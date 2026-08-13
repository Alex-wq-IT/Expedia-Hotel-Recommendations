import re
import unittest
from pathlib import Path


class InfraDockerfileTest(unittest.TestCase):
    def test_superset_drivers_are_installed_in_application_venv(self):
        dockerfile = Path("infra/Dockerfile").read_text(encoding="utf-8")
        install_command = re.search(
            r"RUN uv pip install --python /app/\.venv/bin/python(?P<packages>(?: \\\n|[^\n])*)",
            dockerfile,
        )

        self.assertIsNotNone(install_command)
        packages = install_command.group("packages")
        self.assertIn('"clickhouse-connect>=0.5.14,<1.0"', packages)
        self.assertIn('"psycopg2-binary"', packages)


if __name__ == "__main__":
    unittest.main()
