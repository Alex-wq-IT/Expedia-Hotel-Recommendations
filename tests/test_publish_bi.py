import json
import tempfile
import unittest
from pathlib import Path

from tools.publish_bi import clickhouse_type, export_bundle, load_registry, quote_identifier


class PublishBiTest(unittest.TestCase):
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

    def test_export_is_readable_bundle(self):
        registry = {"version": 1, "marts": []}
        with tempfile.TemporaryDirectory() as directory:
            bundle = export_bundle(registry, {"dashboard_id": 1}, [], Path(directory))
            self.assertTrue(bundle.is_file())
            import zipfile
            with zipfile.ZipFile(bundle) as archive:
                self.assertEqual(sorted(archive.namelist()), ["provision_manifest.yaml", "registry.yaml"])
                self.assertEqual(json.loads(archive.read("registry.yaml"))["version"], 1)


if __name__ == "__main__":
    unittest.main()
