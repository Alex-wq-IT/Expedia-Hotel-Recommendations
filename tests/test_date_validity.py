import unittest
from pathlib import Path

import duckdb

from tools import build_core


ROOT = Path(__file__).resolve().parents[1]


class ProjectDateValidityTest(unittest.TestCase):
    def test_project_date_range_is_inclusive(self):
        values = """
            VALUES
                (DATE '2012-12-31', FALSE),
                (DATE '2013-01-01', TRUE),
                (DATE '2016-12-31', TRUE),
                (DATE '2017-01-01', FALSE),
                (NULL::DATE, FALSE)
        """
        query = f"""
            SELECT test_date, expected,
                   {build_core.project_date_is_valid_sql('test_date')} AS actual
            FROM ({values}) AS boundary_dates(test_date, expected)
        """

        con = duckdb.connect()
        try:
            rows = con.execute(query).fetchall()
        finally:
            con.close()

        self.assertTrue(all(expected == actual for _, expected, actual in rows), rows)

    def test_only_present_out_of_range_dates_are_flagged(self):
        values = """
            VALUES
                (DATE '2012-12-31', TRUE),
                (DATE '2013-01-01', FALSE),
                (DATE '2016-12-31', FALSE),
                (DATE '2017-01-01', TRUE),
                (NULL::DATE, FALSE)
        """
        query = f"""
            SELECT test_date, expected,
                   {build_core.project_date_is_outside_sql('test_date')} AS actual
            FROM ({values}) AS boundary_dates(test_date, expected)
        """

        con = duckdb.connect()
        try:
            rows = con.execute(query).fetchall()
        finally:
            con.close()

        self.assertTrue(all(expected == actual for _, expected, actual in rows), rows)

    def test_active_pipeline_no_longer_uses_broad_date_boundaries(self):
        core_source = (ROOT / "tools" / "build_core.py").read_text(encoding="utf-8")
        analytics_source = (ROOT / "tools" / "build_analytics.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("BETWEEN 1900 AND 2049", core_source)
        self.assertNotIn(">= 2050", core_source)
        self.assertGreaterEqual(analytics_source.count("event_date_key IS NOT NULL"), 4)


if __name__ == "__main__":
    unittest.main()
