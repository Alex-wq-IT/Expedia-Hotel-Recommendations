"""Publish approved MARTS to ClickHouse and provision Superset.

The publisher is intentionally independent from the raw/CORE builders. It reads
only materialized files under data/derived/marts and talks to ClickHouse and
Superset over their HTTP APIs. All object names are stable, so rerunning the
command updates the existing BI objects instead of creating duplicates.
"""

from __future__ import annotations

import argparse
import base64
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
                  headers: dict[str, str] | None = None, timeout: int = 60) -> Any:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
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


class SupersetClient:
    def __init__(self, base_url: str, username: str, password: str, provider: str = "db") -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.headers: dict[str, str] = {"Accept": "application/json"}
        login = _json_request(
            self.base_url + "/api/v1/security/login", "POST",
            {"username": username, "password": password, "provider": provider, "refresh": True},
        )
        self.headers["Authorization"] = f"Bearer {login['access_token']}"
        csrf = _json_request(self.base_url + "/api/v1/security/csrf_token/", headers=self.headers)
        self.headers["X-CSRFToken"] = csrf["result"]

    def request(self, path: str, method: str = "GET", payload: Any | None = None) -> Any:
        return _json_request(self.base_url + path, method, payload, self.headers)

    def find_by_name(self, resource: str, name: str) -> dict[str, Any] | None:
        query = urllib.parse.quote(json.dumps({"filters": [{"col": "database_name" if resource == "database" else "table_name" if resource == "dataset" else "slice_name" if resource == "chart" else "dashboard_title", "opr": "eq", "value": name}]}))
        response = self.request(f"/api/v1/{resource}/?q={query}")
        results = response.get("result", [])
        return results[0] if results else None

    def upsert(self, resource: str, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.find_by_name(resource, name)
        if existing:
            object_id = existing.get("id")
            return self.request(f"/api/v1/{resource}/{object_id}", "PUT", payload)
        return self.request(f"/api/v1/{resource}/", "POST", payload)

    def upsert_metric(self, dataset_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.request(f"/api/v1/dataset/{dataset_id}/metrics/")
        existing = next((item for item in response.get("result", []) if item.get("metric_name") == payload["metric_name"]), None)
        if existing:
            return self.request(f"/api/v1/dataset/{dataset_id}/metrics/{existing['id']}", "PUT", payload)
        return self.request(f"/api/v1/dataset/{dataset_id}/metrics/", "POST", payload)


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


def provision_superset(registry: dict[str, Any], client: SupersetClient, clickhouse: ClickHouseClient, dry_run: bool = False) -> dict[str, Any]:
    db_name = registry["superset"]["database_name"]
    parsed = urllib.parse.urlparse(clickhouse.url)
    uri = f"clickhousedb://{urllib.parse.quote(clickhouse.user)}:{urllib.parse.quote(clickhouse.password)}@{parsed.hostname or 'clickhouse'}:{parsed.port or 8123}/{registry['clickhouse']['database']}"
    database = client.upsert("database", db_name, {"database_name": db_name, "sqlalchemy_uri": uri, "expose_in_sqllab": True}) if not dry_run else {"id": 0}
    database_id = database.get("id", 0)
    datasets: dict[str, int] = {}
    for item in registry["marts"]:
        payload = {"database_id": database_id, "schema": registry["clickhouse"]["database"], "table_name": item["name"], "is_sqllab_view": False, "owners": []}
        dataset = client.upsert("dataset", item["name"], payload) if not dry_run else {"id": 0}
        dataset_id = dataset.get("id", 0)
        datasets[item["name"]] = dataset_id
        for metric in metric_payloads(item):
            if not dry_run:
                client.upsert_metric(dataset_id, metric)
    charts: dict[str, int] = {}
    for chart in registry["dashboard_charts"]:
        dataset_id = datasets[chart["mart"]]
        params = {"viz_type": chart["viz_type"], "metrics": chart["metrics"], "groupby": chart["groupby"], "adhoc_filters": [], "row_limit": 100}
        payload = {"slice_name": chart["name"], "datasource_id": dataset_id, "datasource_type": "table", "viz_type": chart["viz_type"], "params": json.dumps(params), "query_context": json.dumps({"datasource": {"id": dataset_id, "type": "table"}, "force": False, "queries": []})}
        result = client.upsert("chart", chart["name"], payload) if not dry_run else {"id": 0}
        charts[chart["name"]] = result.get("id", 0)
    dashboard_payload = {"dashboard_title": registry["superset"]["dashboard_title"], "slug": registry["superset"]["slug"], "published": True, "position_json": json.dumps({"CHART-%d" % chart_id: {"type": "CHART", "meta": {"chartId": chart_id, "width": 6, "height": 4}} for chart_id in charts.values()})}
    dashboard = client.upsert("dashboard", registry["superset"]["dashboard_title"], dashboard_payload) if not dry_run else {"id": 0}
    return {"database_id": database_id, "datasets": datasets, "charts": charts, "dashboard_id": dashboard.get("id", 0)}


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
    clickhouse = ClickHouseClient(os.getenv("CLICKHOUSE_URL", "http://localhost:8123"), os.getenv("CLICKHOUSE_USER", "default"), os.getenv("CLICKHOUSE_PASSWORD", ""))
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
