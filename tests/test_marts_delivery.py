import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class MartsDeliveryContractTest(unittest.TestCase):
    def test_registry_contains_complete_14_mart_contract(self):
        registry = json.loads((ROOT/"bi"/"registry.json").read_text(encoding="utf-8"))
        names = [item["name"] for item in registry["marts"]]
        self.assertEqual(len(names), 14)
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("mart_package_profile", names)
        self.assertIn("mart_booking_frequency_exact", names)

    def test_registry_metrics_have_supported_prefix(self):
        registry = json.loads((ROOT/"bi"/"registry.json").read_text(encoding="utf-8"))
        supported = {"sum","avg","min","max","count"}
        for mart in registry["marts"]:
            for metric in mart.get("metrics", []):
                function, separator, column = metric.partition("__")
                self.assertEqual(separator, "__", metric)
                self.assertIn(function, supported, metric)
                self.assertTrue(column, metric)

    def test_makefile_builds_and_validates_all_marts_before_publish(self):
        makefile = (ROOT/"Makefile").read_text(encoding="utf-8")
        build = makefile.split("bi-build:",1)[1].split("\n\n",1)[0]
        self.assertIn("tools/build_analytics.py", build)
        self.assertIn("tools/build_extra_marts.py", build)
        self.assertIn("tools/validate_marts.py", build)
        all_target = makefile.split("bi-all:",1)[1].split("\n\n",1)[0]
        self.assertLess(all_target.index("tools/validate_marts.py"),
                        all_target.index("tools/publish_bi.py"))


    def test_registry_preserves_existing_dashboard_chart_contract(self):
        registry = json.loads((ROOT/"bi"/"registry.json").read_text(encoding="utf-8"))
        names = [chart["name"] for chart in registry["dashboard_charts"]]
        self.assertEqual(
            names,
            [
                "Product bookings by day",
                "Product conversion by day",
                "Bookings by channel and platform",
                "Top destinations by bookings",
            ],
        )
        top = registry["dashboard_charts"][-1]
        self.assertEqual(top["viz_type"], "echarts_timeseries_bar")
        self.assertEqual(top["x_axis"], "destination_id")

    def test_supplementary_builder_declares_expected_outputs(self):
        source=(ROOT/"tools"/"build_extra_marts.py").read_text(encoding="utf-8")
        self.assertIn("mart_package_profile", source)
        self.assertIn("mart_booking_frequency_exact", source)
        self.assertIn("extra_marts_manifest.json", source)

    def test_validator_declares_same_14_marts_as_registry(self):
        source=(ROOT/"tools"/"validate_marts.py").read_text(encoding="utf-8")
        registry=json.loads((ROOT/"bi"/"registry.json").read_text(encoding="utf-8"))
        for item in registry["marts"]:
            self.assertIn(f'"{item["name"]}"', source)

if __name__ == "__main__":
    unittest.main()
