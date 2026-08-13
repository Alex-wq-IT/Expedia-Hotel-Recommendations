import tempfile
import unittest
from pathlib import Path
from unittest import mock

import duckdb

from tools import build_core


class StopAfterRawCheck(Exception):
    pass


class BuildCoreTest(unittest.TestCase):
    def test_main_registers_raw_prerequisites_on_fresh_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parquet_dir = root / "data" / "parquet"
            parquet_dir.mkdir(parents=True)
            for name in ("train_full", "test", "destinations"):
                con = duckdb.connect()
                try:
                    con.execute(
                        f"COPY (SELECT 1 AS value) TO '{parquet_dir / (name + '.parquet')}' "
                        "(FORMAT PARQUET)"
                    )
                finally:
                    con.close()

            paths = {
                "ROOT": root,
                "DB_PATH": root / "data" / "analytics.duckdb",
                "DERIVED": root / "data" / "derived",
                "STAGING_DIR": root / "data" / "derived" / "staging",
                "CORE_DIR": root / "data" / "derived" / "core",
                "ARTIFACTS_DIR": root / "artifacts",
                "DOCS_DIR": root / "docs",
            }
            with mock.patch.multiple(build_core, **paths), mock.patch.object(
                build_core, "materialize", side_effect=StopAfterRawCheck
            ):
                with self.assertRaises(StopAfterRawCheck):
                    build_core.main()

            con = duckdb.connect(str(paths["DB_PATH"]), read_only=True)
            try:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM raw.test").fetchone()[0], 1)
                self.assertEqual(
                    con.execute("SELECT COUNT(*) FROM raw.destinations").fetchone()[0], 1
                )
            finally:
                con.close()


if __name__ == "__main__":
    unittest.main()
