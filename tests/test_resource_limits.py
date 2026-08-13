import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.duckdb_runtime import configure_duckdb


ROOT = Path(__file__).resolve().parents[1]


class RecordingConnection:
    def __init__(self):
        self.queries = []

    def execute(self, query):
        self.queries.append(query)


class LaptopResourceLimitsTest(unittest.TestCase):
    def test_duckdb_defaults_to_one_thread_and_one_gigabyte(self):
        connection = RecordingConnection()

        with patch.dict(os.environ, {}, clear=True):
            configure_duckdb(connection, ROOT / "data" / "derived" / "test_tmp")

        self.assertIn("PRAGMA threads=1", connection.queries)
        self.assertIn("PRAGMA memory_limit='1GB'", connection.queries)

    def test_duckdb_limits_can_be_overridden_explicitly(self):
        connection = RecordingConnection()

        with patch.dict(
            os.environ,
            {"EXPEDIA_DUCKDB_THREADS": "2", "EXPEDIA_DUCKDB_MEMORY_LIMIT": "2GB"},
            clear=True,
        ):
            configure_duckdb(connection, ROOT / "data" / "derived" / "test_tmp")

        self.assertIn("PRAGMA threads=2", connection.queries)
        self.assertIn("PRAGMA memory_limit='2GB'", connection.queries)

    def test_compose_caps_every_long_running_service(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")

        for service in ("clickhouse", "superset", "db", "superset-init"):
            match = re.search(
                rf"^  {re.escape(service)}:\n(?P<body>.*?)(?=^  [a-zA-Z]|^volumes:)",
                compose,
                flags=re.MULTILINE | re.DOTALL,
            )
            self.assertIsNotNone(match, service)
            block = match.group("body")
            self.assertIn("mem_limit:", block, service)
            self.assertIn("cpus:", block, service)
        self.assertIn("--workers 1", compose)


if __name__ == "__main__":
    unittest.main()
