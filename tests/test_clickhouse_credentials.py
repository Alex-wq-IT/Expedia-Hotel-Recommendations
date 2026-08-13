import os
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.publish_bi import clickhouse_client_from_env


class ClickHouseCredentialsTest(unittest.TestCase):
    def test_publisher_uses_clickhouse_credentials_from_environment(self):
        environment = {
            "CLICKHOUSE_URL": "http://localhost:8123",
            "CLICKHOUSE_USER": "expedia_bi",
            "CLICKHOUSE_PASSWORD": "test-only-password",
        }

        with patch.dict(os.environ, environment, clear=True):
            client = clickhouse_client_from_env()

        self.assertEqual(client.url, "http://localhost:8123")
        self.assertEqual(client.user, "expedia_bi")
        self.assertEqual(client.password, "test-only-password")

    def test_publisher_rejects_an_empty_clickhouse_password(self):
        with patch.dict(os.environ, {"CLICKHOUSE_PASSWORD": ""}, clear=True):
            with self.assertRaisesRegex(ValueError, "CLICKHOUSE_PASSWORD must be set"):
                clickhouse_client_from_env()

    def test_publisher_and_compose_share_the_default_username(self):
        environment = {
            "CLICKHOUSE_USER": "",
            "CLICKHOUSE_PASSWORD": "test-only-password",
        }

        with patch.dict(os.environ, environment, clear=True):
            client = clickhouse_client_from_env()

        self.assertEqual(client.user, "expedia_bi")

    def test_compose_requires_the_same_non_empty_password(self):
        compose = Path("infra/docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn('CLICKHOUSE_USER: "${CLICKHOUSE_USER:-expedia_bi}"', compose)
        self.assertIn('CLICKHOUSE_PASSWORD: "${CLICKHOUSE_PASSWORD:?', compose)
        self.assertNotIn('CLICKHOUSE_PASSWORD: ""', compose)


if __name__ == "__main__":
    unittest.main()
