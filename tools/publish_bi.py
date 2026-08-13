"""Publish approved MARTS to ClickHouse and provision Superset.

The publisher is intentionally independent from the raw/CORE builders. It reads
only materialized files under data/derived/marts and talks to ClickHouse and
Superset over their HTTP APIs. All object names are stable, so rerunning the
command updates the existing BI objects instead of creating duplicates.
"""

from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "bi" / "registry.json"
MARTS_DIR = ROOT / "data" / "derived" / "marts"
EXPORT_DIR = ROOT / "exports"
ARTIFACTS_DIR = ROOT / "artifacts"


class ApiError(RuntimeError):
    """An external API returned a non-success response."""


def quote_identifier(identifier: str) -> str:
    """Quote a simple ClickHouse identifier and reject qualified injection."""
    if not identifier or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for ch in identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier!r}")
    return f"`{identifier}`"


def clickhouse_type(duck_type: str) -> str:
    normalized = duck_type.upper().split("(")[0].strip()
    mapping = {
        "BIGINT": "Int64", "INTEGER": "Int64", "INT": "Int64", "SMALLINT": "Int64",
        "UBIGINT": "UInt64", "DOUBLE": "Float64", "FLOAT": "Float64", "REAL": "Float64",
        "BOOLEAN": "Bool", "VARCHAR": "String", "DATE": "Date", "TIMESTAMP": "DateTime64(6)",
    }
    return mapping.get(normalized, "String")


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    names = [item["name"] for item in registry["marts"]]
    if len(names) != len(set(names)):
        raise ValueError("Registry contains duplicate mart names")
    for name in names:
        quote_identifier(name)
    return registry


def mart_path(name: str) -> Path:
    path = MARTS_DIR / f"{name}.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"Approved MART file is missing: {path}")
    return path


def parquet_schema(path: Path) -> list[tuple[str, str]]:
    con = duckdb.connect(":memory:")
    try:
        rows = con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]).fetchall()
        return [(row[0], row[1]) for row in rows]
    finally:
        con.close()


def _json_request(url: str, method: str = "GET", payload: Any | None = None,
                  headers: dict[str, str] | None = None, timeout: int = 60,
                  opener: urllib.request.OpenerDirector | None = None) -> Any:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        open_request = opener.open if opener is not None else urllib.request.urlopen
        with open_request(request, timeout=timeout) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ApiError(f"{method} {url} failed with {exc.code}: {detail[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"{method} {url} failed: {exc.reason}") from exc


@dataclass
class ClickHouseClient:
    url: str
    user: str = "default"
    password: str = ""
    timeout: int = 120

    def query(self, sql: str) -> str:
        endpoint = self.url.rstrip("/") + "/"
        request = urllib.request.Request(endpoint, data=sql.encode("utf-8"), method="POST")
        token = f"{self.user}:{self.password}"
        request.add_header("Authorization", "Basic " + base64.b64encode(token.encode()).decode())
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise ApiError(f"ClickHouse query failed with {exc.code}: {exc.read().decode(errors='replace')[:1000]}") from exc

    def insert_parquet(self, table: str, data: bytes) -> None:
        endpoint = self.url.rstrip("/") + "/?query=" + urllib.parse.quote(
            f"INSERT INTO {table} FORMAT Parquet"
        )
        request = urllib.request.Request(endpoint, data=data, method="POST")
        token = f"{self.user}:{self.password}"
        request.add_header("Authorization", "Basic " + base64.b64encode(token.encode()).decode())
        request.add_header("Content-Type", "application/octet-stream")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            raise ApiError(f"ClickHouse insert failed with {exc.code}: {exc.read().decode(errors='replace')[:1000]}") from exc


def clickhouse_client_from_env() -> ClickHouseClient:
    """Build the host-side client from the credentials shared with Compose."""
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    if not password:
        raise ValueError(
            "CLICKHOUSE_PASSWORD must be set to a non-empty value before BI publication"
        )
    return ClickHouseClient(
        os.getenv("CLICKHOUSE_URL", "http://localhost:8123"),
        os.getenv("CLICKHOUSE_USER") or "expedia_bi",
        password,
    )


class SupersetClient:
    def __init__(self, base_url: str, username: str, password: str, provider: str = "db") -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.headers: dict[str, str] = {"Accept": "application/json"}
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        login = _json_request(
            self.base_url + "/api/v1/security/login", "POST",
            {"username": username, "password": password, "provider": provider, "refresh": True},
            opener=self.opener,
        )
        self.headers["Authorization"] = f"Bearer {login['access_token']}"
        csrf = _json_request(
            self.base_url + "/api/v1/security/csrf_token/",
            headers=self.headers,
            opener=self.opener,
        )
        self.headers["X-CSRFToken"] = csrf["result"]

    def request(self, path: str, method: str = "GET", payload: Any | None = None) -> Any:
        return _json_request(
            self.base_url + path,
            method,
            payload,
            self.headers,
            opener=self.opener,
        )

    def find_by_name(self, resource: str, name: str) -> dict[str, Any] | None:
        query = urllib.parse.quote(json.dumps({"filters": [{"col": "database_name" if resource == "database" else "table_name" if resource == "dataset" else "slice_name" if resource == "chart" else "dashboard_title", "opr": "eq", "value": name}]}))
        response = self.request(f"/api/v1/{resource}/?q={query}")
        results = response.get("result", [])
        return results[0] if results else None

    def upsert(self, resource: str, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.find_by_name(resource, name)
        if existing:
            object_id = existing.get("id")
            update_payload = payload.copy()
            if resource == "dataset":
                update_payload.pop("database", None)
            return self.request(f"/api/v1/{resource}/{object_id}", "PUT", update_payload)
        return self.request(f"/api/v1/{resource}/", "POST", payload)

    def add_missing_metrics(self, dataset_id: int, metrics: list[dict[str, Any]]) -> dict[str, Any]:
        path = f"/api/v1/dataset/{dataset_id}"
        details = self.request(path)
        existing_metrics = details.get("result", {}).get("metrics", [])
        existing_names = {metric.get("metric_name") for metric in existing_metrics}
        missing_metrics = [
            metric for metric in metrics
            if metric.get("metric_name") not in existing_names
        ]
        if not missing_metrics:
            return details
        # Superset's dataset PUT treats `metrics` as the complete replacement
        # collection. Preserve every existing metric (and its id) while adding
        # only the registry metrics that are actually missing.
        accepted_fields = {
            "id", "expression", "description", "extra", "metric_name",
            "metric_type", "d3format", "currency", "verbose_name",
            "warning_text", "uuid",
        }
        preserved_metrics = [
            {key: value for key, value in metric.items() if key in accepted_fields}
            for metric in existing_metrics
        ]
        return self.request(
            path,
            "PUT",
            {"metrics": [*preserved_metrics, *missing_metrics]},
        )


def publish_clickhouse(registry: dict[str, Any], client: ClickHouseClient, dry_run: bool = False) -> list[dict[str, Any]]:
    database = quote_identifier(registry["clickhouse"]["database"])
    results: list[dict[str, Any]] = []
    if not dry_run:
        client.query(f"CREATE DATABASE IF NOT EXISTS {database}")
    for item in registry["marts"]:
        name = item["name"]
        path = mart_path(name)
        schema = parquet_schema(path)
        table = f"{database}.{quote_identifier(name)}"
        columns = ", ".join(f"{quote_identifier(col)} Nullable({clickhouse_type(dtype)})" for col, dtype in schema)
        if not dry_run:
            client.query(f"DROP TABLE IF EXISTS {table}")
            client.query(f"CREATE TABLE {table} ({columns}) ENGINE = MergeTree ORDER BY tuple()")
            client.insert_parquet(table, path.read_bytes())
        results.append({"name": name, "path": str(path.relative_to(ROOT)), "columns": len(schema), "bytes": path.stat().st_size})
    return results


def metric_payloads(item: dict[str, Any]) -> list[dict[str, Any]]:
    payloads = []
    for metric in item.get("metrics", []):
        function, column = metric.split("__", 1)
        expression = f"{function.upper()}({quote_identifier(column)})"
        payloads.append({"metric_name": metric, "expression": expression, "metric_type": "numeric", "verbose_name": metric.replace("__", " ")})
    return payloads


def chart_params(chart: dict[str, Any], mart: dict[str, Any], dataset_id: int) -> dict[str, Any]:
    """Build the Explore form data Superset uses to render a stored chart."""
    groupby = list(chart.get("groupby", []))
    params: dict[str, Any] = {
        "datasource": f"{dataset_id}__table",
        "viz_type": chart["viz_type"],
        "metrics": list(chart.get("metrics", [])),
        "groupby": groupby,
        "adhoc_filters": [],
        "row_limit": 100,
    }
    x_axis = chart.get("x_axis") or mart.get("time_column")
    if chart["viz_type"].startswith("echarts_timeseries") and x_axis:
        params.update(
            {
                "x_axis": x_axis,
                # MART time keys are encoded BIGINT/VARCHAR columns rather than
                # physical Date columns, so Superset must not coerce them to epoch.
                "x_axis_force_categorical": True,
                "time_range": "No filter",
            }
        )
        params["groupby"] = [column for column in groupby if column != x_axis]
    if "order_desc" in chart:
        params["order_desc"] = bool(chart["order_desc"])
    return params


def dashboard_position(charts: dict[str, int]) -> dict[str, Any]:
    """Return a deterministic Superset v2 grid with two charts per row."""
    layout: dict[str, Any] = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
        "GRID_ID": {
            "id": "GRID_ID",
            "type": "GRID",
            "children": [],
            "parents": ["ROOT_ID"],
        },
    }
    for index, (chart_name, chart_id) in enumerate(charts.items()):
        if not chart_id:
            raise ApiError(f"Chart {chart_name!r} has no API id")
        row_id = f"ROW-{index // 2 + 1}"
        if row_id not in layout:
            layout["GRID_ID"]["children"].append(row_id)
            layout[row_id] = {
                "id": row_id,
                "type": "ROW",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID"],
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
            }
        component_id = f"CHART-{chart_id}"
        layout[row_id]["children"].append(component_id)
        layout[component_id] = {
            "id": component_id,
            "type": "CHART",
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", row_id],
            "meta": {
                "chartId": chart_id,
                "sliceName": chart_name,
                "width": 6,
                "height": 50,
            },
        }
    return layout


def _api_object_id(response: dict[str, Any], resource: str) -> int:
    object_id = response.get("id")
    if object_id is None and isinstance(response.get("result"), dict):
        object_id = response["result"].get("id")
    if not isinstance(object_id, int) or object_id <= 0:
        raise ApiError(f"Superset {resource} response has no valid id: {response!r}")
    return object_id


def provision_superset(registry: dict[str, Any], client: SupersetClient, clickhouse: ClickHouseClient, dry_run: bool = False) -> dict[str, Any]:
    db_name = registry["superset"]["database_name"]
    superset_clickhouse_host = os.getenv("SUPERSET_CLICKHOUSE_HOST", "clickhouse")
    superset_clickhouse_port = os.getenv("SUPERSET_CLICKHOUSE_PORT", "8123")
    uri = (
        "clickhousedb://"
        f"{urllib.parse.quote(clickhouse.user, safe='')}:"
        f"{urllib.parse.quote(clickhouse.password, safe='')}@"
        f"{superset_clickhouse_host}:{superset_clickhouse_port}/"
        f"{registry['clickhouse']['database']}"
    )
    database = client.upsert("database", db_name, {"database_name": db_name, "sqlalchemy_uri": uri, "expose_in_sqllab": True}) if not dry_run else {"id": 0}
    database_id = database.get("id", 0)
    datasets: dict[str, int] = {}
    for item in registry["marts"]:
        payload = {"database": database_id, "schema": registry["clickhouse"]["database"], "table_name": item["name"], "owners": []}
        dataset = client.upsert("dataset", item["name"], payload) if not dry_run else {"id": 0}
        dataset_id = dataset.get("id", 0)
        datasets[item["name"]] = dataset_id
        metrics = metric_payloads(item)
        if not dry_run and metrics:
            client.add_missing_metrics(dataset_id, metrics)
    dashboard_base_payload = {
        "dashboard_title": registry["superset"]["dashboard_title"],
        "slug": registry["superset"]["slug"],
        "published": True,
    }
    if not dry_run:
        dashboard = client.upsert(
            "dashboard",
            registry["superset"]["dashboard_title"],
            dashboard_base_payload,
        )
        dashboard_id = _api_object_id(dashboard, "dashboard")
    else:
        dashboard_id = 0

    marts_by_name = {item["name"]: item for item in registry["marts"]}
    charts: dict[str, int] = {}
    for chart in registry["dashboard_charts"]:
        dataset_id = datasets[chart["mart"]]
        payload = {
            "slice_name": chart["name"],
            "datasource_id": dataset_id,
            "datasource_type": "table",
            "viz_type": chart["viz_type"],
            "params": json.dumps(
                chart_params(chart, marts_by_name[chart["mart"]], dataset_id)
            ),
            "dashboards": [dashboard_id] if not dry_run else [],
        }
        result = client.upsert("chart", chart["name"], payload) if not dry_run else {"id": 0}
        charts[chart["name"]] = _api_object_id(result, "chart") if not dry_run else 0

    if not dry_run:
        dashboard_payload = {
            **dashboard_base_payload,
            "position_json": json.dumps(dashboard_position(charts)),
        }
        updated_dashboard = client.upsert(
            "dashboard",
            registry["superset"]["dashboard_title"],
            dashboard_payload,
        )
        updated_dashboard_id = _api_object_id(updated_dashboard, "dashboard")
        if updated_dashboard_id != dashboard_id:
            raise ApiError(
                "Superset dashboard update targeted a different object: "
                f"created/reused {dashboard_id}, updated {updated_dashboard_id}"
            )
    return {"database_id": database_id, "datasets": datasets, "charts": charts, "dashboard_id": dashboard_id}


def export_bundle(registry: dict[str, Any], superset_result: dict[str, Any], publish_result: list[dict[str, Any]], output_dir: Path = EXPORT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle = output_dir / f"expedia-bi-{stamp}.zip"
    manifest = {"registry": registry, "clickhouse": publish_result, "superset": superset_result, "exported_at": stamp}
    yaml_compatible = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("registry.yaml", json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
        archive.writestr("provision_manifest.yaml", yaml_compatible)
    (output_dir / "latest.yaml").write_text(yaml_compatible, encoding="utf-8")
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["publish", "export", "all"])
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-superset", action="store_true")
    args = parser.parse_args()
    registry = load_registry(args.registry)
    clickhouse = clickhouse_client_from_env()
    publish_result = publish_clickhouse(registry, clickhouse, dry_run=args.dry_run) if args.command in {"publish", "all"} else []
    superset_result: dict[str, Any] = {}
    if args.command in {"export", "all"} and not args.skip_superset and not args.dry_run:
        superset = SupersetClient(os.getenv("SUPERSET_URL", "http://localhost:8088"), os.getenv("SUPERSET_USERNAME", "admin"), os.getenv("SUPERSET_PASSWORD", "admin"))
        superset_result = provision_superset(registry, superset, clickhouse)
    elif args.command in {"export", "all"}:
        superset_result = provision_superset(registry, None, clickhouse, dry_run=True)  # type: ignore[arg-type]
    if args.command in {"export", "all"}:
        bundle = export_bundle(registry, superset_result, publish_result)
        print(bundle)
    manifest = {"published_at": datetime.now(timezone.utc).isoformat(), "dry_run": args.dry_run, "clickhouse": publish_result, "superset": superset_result}
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    (ARTIFACTS_DIR / "bi_publish_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
