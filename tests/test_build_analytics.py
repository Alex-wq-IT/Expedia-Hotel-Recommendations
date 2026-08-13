import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_analytics


BUILD_ANALYTICS = Path(__file__).resolve().parents[1] / "tools" / "build_analytics.py"
PYTHON_311 = sys.executable if sys.version_info[:2] == (3, 11) else shutil.which("python3.11")


class TempDirectoryConfigured(Exception):
    pass


class RecordingConnection:
    def __init__(self):
        self.queries = []
        self.closed = False

    def execute(self, query):
        self.queries.append(query)
        if query.startswith("PRAGMA temp_directory="):
            raise TempDirectoryConfigured

    def close(self):
        self.closed = True


class BuildAnalyticsCompatibilityTest(unittest.TestCase):
    def test_temp_directory_path_is_prepared_outside_fstring(self):
        source = (
            BUILD_ANALYTICS.parents[0] / "duckdb_runtime.py"
        ).read_text(encoding="utf-8")

        self.assertIn("temp_directory.resolve().as_posix()", source)
        self.assertIn('connection.execute(f"PRAGMA temp_directory=', source)
        self.assertNotIn("replace('\\\\', '/')", source)

    def test_main_configures_posix_temp_directory_before_building(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project's root"
            connection = RecordingConnection()
            paths = {
                "ROOT": root,
                "DB_PATH": root / "data" / "analytics.duckdb",
                "CORE_DIR": root / "data" / "derived" / "core",
                "MARTS_DIR": root / "data" / "derived" / "marts",
                "ARTIFACTS_DIR": root / "artifacts",
                "DOCS_DIR": root / "docs",
            }
            with mock.patch.multiple(build_analytics, **paths), mock.patch.object(
                build_analytics.duckdb, "connect", return_value=connection
            ):
                with self.assertRaises(TempDirectoryConfigured):
                    build_analytics.main()

            temp_directory = (
                root / "data" / "derived" / "duckdb_tmp" / "analytics"
            ).resolve().as_posix()
            expected_pragma = (
                "PRAGMA temp_directory='" + temp_directory.replace("'", "''") + "'"
            )
            self.assertEqual(connection.queries[-1], expected_pragma)
            self.assertTrue(connection.closed)

    @unittest.skipUnless(PYTHON_311, "Python 3.11 is not installed")
    def test_script_parses_on_python_311(self):
        subprocess.run(
            [
                PYTHON_311,
                "-c",
                "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), "
                "sys.argv[1], 'exec')",
                str(BUILD_ANALYTICS),
            ],
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
