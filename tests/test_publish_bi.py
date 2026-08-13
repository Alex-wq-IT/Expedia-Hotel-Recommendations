import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

from tools.publish_bi import (
    ClickHouseClient,
    SupersetClient,
    clickhouse_client_from_env,
    clickhouse_type,
    export_bundle,
    load_registry,
    provision_superset,
    quote_identifier,
)


class _SupersetCookieHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _write_json(self, payload, *, set_cookie=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/v1/security/csrf_token/":
            if "session=login-session" not in self.headers.get("Cookie", ""):
                self.send_error(403, "login session cookie missing")
                return
            self._write_json(
                {"result": "csrf-token"},
                set_cookie="csrf_session=csrf-session; Path=/",
            )
            return
        self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(content_length)
        if self.path == "/api/v1/security/login":
            self._write_json(
                {"access_token": "access-token"},
                set_cookie="session=login-session; Path=/",
            )
            return
        if self.path == "/api/v1/protected":
            cookies = self.headers.get("Cookie", "")
            has_session_cookies = all(
                cookie in cookies
                for cookie in ("session=login-session", "csrf_session=csrf-session")
            )
            if not has_session_cookies or self.headers.get("X-CSRFToken") != "csrf-token":
                self.send_error(403, "CSRF session token is missing")
                return
            self._write_json({"result": "published"})
            return
        self.send_error(404)


class RecordingSupersetClient:
    def __init__(self):
        self.upserts = []
        self.ids = {}

    def upsert(self, resource, name, payload):
        self.upserts.append((resource, name, payload))
        object_key = (resource, name)
        if object_key not in self.ids:
            self.ids[object_key] = len(self.ids) + 1
        return {"id": self.ids[object_key]}


def empty_registry():
    return {
        "clickhouse": {"database": "expedia"},
        "superset": {
            "database_name": "Expedia Analytics",
            "dashboard_title": "Expedia Dashboard",
            "slug": "expedia-dashboard",
        },
        "marts": [],
        "dashboard_charts": [],
    }


class PublishBiTest(unittest.TestCase):
    def test_superset_client_preserves_cookies_for_csrf_protected_requests(self):
        server = HTTPServer(("127.0.0.1", 0), _SupersetCookieHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{server.server_port}"
            client = SupersetClient(base_url, "admin", "password")

            response = client.request("/api/v1/protected", "POST", {"name": "dataset"})

            self.assertEqual(response, {"result": "published"})
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_clickhouse_requests_keep_using_urlopen(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.side_effect = [b"query-result", b""]
        client = ClickHouseClient(
            "http://clickhouse.example:8123",
            "publisher",
            "secret",
            timeout=37,
        )

        with patch("tools.publish_bi.urllib.request.urlopen", return_value=response) as urlopen:
            query_result = client.query("SELECT 1")
            client.insert_parquet("expedia.mart_product_daily", b"PAR1")

        self.assertEqual(query_result, "query-result")
        self.assertEqual(urlopen.call_count, 2)
        query_call, insert_call = urlopen.call_args_list
        self.assertEqual(query_call.kwargs, {"timeout": 37})
        self.assertEqual(insert_call.kwargs, {"timeout": 37})
        query_request = query_call.args[0]
        insert_request = insert_call.args[0]
        self.assertEqual(query_request.full_url, "http://clickhouse.example:8123/")
        self.assertEqual(query_request.data, b"SELECT 1")
        self.assertEqual(query_request.get_method(), "POST")
        self.assertEqual(
            insert_request.full_url,
            "http://clickhouse.example:8123/?query=INSERT%20INTO%20expedia.mart_product_daily%20FORMAT%20Parquet",
        )
        self.assertEqual(insert_request.data, b"PAR1")
        self.assertEqual(insert_request.get_method(), "POST")

    def test_superset_uses_docker_clickhouse_defaults_without_changing_host_publisher(self):
        registry = empty_registry()
        superset = RecordingSupersetClient()

        with patch.dict(os.environ, {"CLICKHOUSE_PASSWORD": "secret"}, clear=True):
            publisher = clickhouse_client_from_env()
            provision_superset(registry, superset, publisher)

        database_payload = superset.upserts[0][2]
        self.assertEqual(
            database_payload["sqlalchemy_uri"],
            "clickhousedb://expedia_bi:secret@clickhouse:8123/expedia",
        )
        self.assertEqual(publisher.url, "http://localhost:8123")

    def test_superset_clickhouse_host_and_port_can_be_configured_independently(self):
        registry = empty_registry()
        superset = RecordingSupersetClient()
        publisher = ClickHouseClient("http://localhost:18123", "publisher", "secret")

        with patch.dict(
            os.environ,
            {
                "SUPERSET_CLICKHOUSE_HOST": "analytics-clickhouse",
                "SUPERSET_CLICKHOUSE_PORT": "28123",
            },
            clear=True,
        ):
            provision_superset(registry, superset, publisher)

        database_payload = superset.upserts[0][2]
        self.assertEqual(
            database_payload["sqlalchemy_uri"],
            "clickhousedb://publisher:secret@analytics-clickhouse:28123/expedia",
        )
        self.assertEqual(publisher.url, "http://localhost:18123")

    def test_superset_clickhouse_uri_escapes_credentials(self):
        registry = empty_registry()
        superset = RecordingSupersetClient()
        publisher = ClickHouseClient(
            "http://localhost:8123", "publisher/name", "secret@with/slash"
        )

        provision_superset(registry, superset, publisher)

        self.assertEqual(
            superset.upserts[0][2]["sqlalchemy_uri"],
            "clickhousedb://publisher%2Fname:secret%40with%2Fslash@clickhouse:8123/expedia",
        )

    def test_registry_contains_existing_marts(self):
        registry = load_registry()
        self.assertEqual(len(registry["marts"]), 12)
        for item in registry["marts"]:
            self.assertTrue((Path("data/derived/marts") / f"{item['name']}.parquet").is_file())

    def test_identifier_is_quoted_and_rejects_sql(self):
        self.assertEqual(quote_identifier("mart_product_daily"), "`mart_product_daily`")
        with self.assertRaises(ValueError):
            quote_identifier("mart; DROP TABLE users")

    def test_type_mapping(self):
        self.assertEqual(clickhouse_type("BIGINT"), "Int64")
        self.assertEqual(clickhouse_type("DOUBLE"), "Float64")
        self.assertEqual(clickhouse_type("VARCHAR"), "String")

    def test_dataset_create_posts_current_api_payload(self):
        client = object.__new__(SupersetClient)
        client.find_by_name = Mock(return_value=None)

        def api_response(path, method="GET", payload=None):
            return {"id": 20 if path == "/api/v1/dataset/" else 10}

        client.request = Mock(side_effect=api_response)
        registry = {
            "clickhouse": {"database": "expedia"},
            "superset": {
                "database_name": "Expedia ClickHouse",
                "dashboard_title": "Expedia Hotel Analytics",
                "slug": "expedia-hotel-analytics",
            },
            "marts": [{"name": "mart_product_daily"}],
            "dashboard_charts": [],
        }
        clickhouse = ClickHouseClient(
            "http://localhost:8123", "bi_publisher", "secret"
        )

        provision_superset(registry, client, clickhouse)

        expected_payload = {
            "database": 10,
            "schema": "expedia",
            "table_name": "mart_product_daily",
            "owners": [],
        }
        self.assertIn(
            call("/api/v1/dataset/", "POST", expected_payload),
            client.request.call_args_list,
        )

    def test_dataset_update_puts_payload_without_database(self):
        client = object.__new__(SupersetClient)
        client.find_by_name = Mock(return_value={"id": 20})
        client.request = Mock(return_value={"id": 20})
        create_payload = {
            "database": 10,
            "schema": "expedia",
            "table_name": "mart_product_daily",
            "owners": [],
        }

        client.upsert("dataset", "mart_product_daily", create_payload)

        client.request.assert_called_once_with(
            "/api/v1/dataset/20",
            "PUT",
            {
                "schema": "expedia",
                "table_name": "mart_product_daily",
                "owners": [],
            },
        )
        self.assertEqual(create_payload["database"], 10)

    def test_export_is_readable_bundle(self):
        registry = {"version": 1, "marts": []}
        with tempfile.TemporaryDirectory() as directory:
            bundle = export_bundle(registry, {"dashboard_id": 1}, [], Path(directory))
            self.assertTrue(bundle.is_file())
            import zipfile
            with zipfile.ZipFile(bundle) as archive:
                self.assertEqual(sorted(archive.namelist()), ["provision_manifest.yaml", "registry.yaml"])
                self.assertEqual(json.loads(archive.read("registry.yaml"))["version"], 1)

    def test_dataset_metrics_use_details_and_put_only_missing_metrics(self):
        client = object.__new__(SupersetClient)
        client.request = Mock(side_effect=[
            {"result": {"metrics": [{"metric_name": "sum__event_rows"}]}},
            {"id": 42},
        ])
        metrics = [
            {"metric_name": "sum__event_rows", "expression": "SUM(`event_rows`)"},
            {"metric_name": "sum__booking_rows", "expression": "SUM(`booking_rows`)"},
        ]

        client.add_missing_metrics(42, metrics)

        self.assertEqual(
            client.request.call_args_list,
            [
                call("/api/v1/dataset/42"),
                call(
                    "/api/v1/dataset/42",
                    "PUT",
                    {"metrics": [metrics[1]]},
                ),
            ],
        )

    def test_provisioning_creates_dataset_before_adding_metrics(self):
        class RecordingMetricClient:
            def __init__(self):
                self.events = []

            def upsert(self, resource, name, payload):
                self.events.append((resource, payload))
                return {"id": {"database": 7, "dataset": 42, "dashboard": 99}[resource]}

            def add_missing_metrics(self, dataset_id, metrics):
                self.events.append(("metrics", {"dataset_id": dataset_id, "metrics": metrics}))
                return {"id": dataset_id}

        registry = {
            "clickhouse": {"database": "expedia"},
            "superset": {
                "database_name": "Expedia Analytics",
                "dashboard_title": "Expedia Dashboard",
                "slug": "expedia-dashboard",
            },
            "marts": [{"name": "mart_product_daily", "metrics": ["sum__event_rows"]}],
            "dashboard_charts": [],
        }
        client = RecordingMetricClient()

        provision_superset(
            registry,
            client,
            ClickHouseClient("http://localhost:8123", "publisher", "secret"),
        )

        dataset_event = client.events[1]
        metric_event = client.events[2]
        self.assertEqual(dataset_event[0], "dataset")
        self.assertNotIn("metrics", dataset_event[1])
        self.assertEqual(metric_event[0], "metrics")
        self.assertEqual(metric_event[1]["dataset_id"], 42)
        self.assertEqual(
            metric_event[1]["metrics"],
            [{
                "metric_name": "sum__event_rows",
                "expression": "SUM(`event_rows`)",
                "metric_type": "numeric",
                "verbose_name": "sum event_rows",
            }],
        )

    def test_dataset_metrics_rerun_is_idempotent(self):
        client = object.__new__(SupersetClient)
        existing_metrics = []

        def dataset_api(_path, method="GET", payload=None):
            if method == "PUT":
                existing_metrics.extend(payload["metrics"])
                return {"id": 42}
            return {"result": {"metrics": list(existing_metrics)}}

        client.request = Mock(side_effect=dataset_api)
        metrics = [
            {"metric_name": "sum__event_rows", "expression": "SUM(`event_rows`)"},
            {"metric_name": "sum__booking_rows", "expression": "SUM(`booking_rows`)"},
        ]

        client.add_missing_metrics(42, metrics)
        client.add_missing_metrics(42, metrics)

        self.assertEqual(
            client.request.call_args_list,
            [
                call("/api/v1/dataset/42"),
                call("/api/v1/dataset/42", "PUT", {"metrics": metrics}),
                call("/api/v1/dataset/42"),
            ],
        )
        self.assertEqual(
            [metric["metric_name"] for metric in existing_metrics],
            ["sum__event_rows", "sum__booking_rows"],
        )


if __name__ == "__main__":
    unittest.main()
