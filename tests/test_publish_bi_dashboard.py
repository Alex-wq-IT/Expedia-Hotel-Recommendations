import json
import unittest

from tools.publish_bi import (
    ClickHouseClient,
    chart_params,
    dashboard_position,
    load_registry,
    provision_superset,
)


class StatefulSupersetClient:
    """Small name-keyed API double that exposes create/update behavior."""

    def __init__(self):
        self.objects = {}
        self.operations = []
        self.next_id = 1

    def upsert(self, resource, name, payload):
        key = (resource, name)
        if key in self.objects:
            operation = "update"
            object_id = self.objects[key]["id"]
        else:
            operation = "create"
            object_id = self.next_id
            self.next_id += 1
        self.objects[key] = {"id": object_id, "payload": payload.copy()}
        self.operations.append((operation, resource, name, payload.copy()))
        return {"id": object_id}

    def add_missing_metrics(self, dataset_id, metrics):
        self.operations.append(("metrics", "dataset", dataset_id, metrics))
        return {"id": dataset_id}


class DashboardPublicationTest(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "clickhouse": {"database": "expedia"},
            "superset": {
                "database_name": "Expedia ClickHouse",
                "dashboard_title": "Expedia Hotel Analytics",
                "slug": "expedia-hotel-analytics",
            },
            "marts": [
                {
                    "name": "mart_product_daily",
                    "time_column": "date_key",
                    "metrics": [],
                }
            ],
            "dashboard_charts": [
                {
                    "name": "Product bookings by day",
                    "mart": "mart_product_daily",
                    "viz_type": "echarts_timeseries_line",
                    "groupby": ["date_key"],
                    "metrics": ["sum__bookings"],
                }
            ],
        }
        self.clickhouse = ClickHouseClient(
            "http://localhost:8123", "bi_publisher", "secret"
        )

    def test_dashboard_layout_has_complete_render_hierarchy(self):
        layout = dashboard_position({"Chart one": 11, "Chart two": 12})

        self.assertEqual(layout["DASHBOARD_VERSION_KEY"], "v2")
        self.assertEqual(layout["ROOT_ID"]["children"], ["GRID_ID"])
        self.assertEqual(layout["GRID_ID"]["children"], ["ROW-1"])
        self.assertEqual(layout["ROW-1"]["children"], ["CHART-11", "CHART-12"])
        self.assertEqual(
            layout["CHART-11"]["parents"], ["ROOT_ID", "GRID_ID", "ROW-1"]
        )
        self.assertEqual(layout["CHART-11"]["meta"]["sliceName"], "Chart one")

    def test_chart_params_contain_renderable_datasource_and_time_axis(self):
        params = chart_params(
            self.registry["dashboard_charts"][0], self.registry["marts"][0], 27
        )

        self.assertEqual(params["datasource"], "27__table")
        self.assertEqual(params["x_axis"], "date_key")
        self.assertTrue(params["x_axis_force_categorical"])
        self.assertNotIn("granularity_sqla", params)
        self.assertEqual(params["metrics"], ["sum__bookings"])
        self.assertEqual(params["groupby"], [])

    def test_publication_creates_then_reuses_dashboard_and_attaches_charts(self):
        client = StatefulSupersetClient()

        first = provision_superset(self.registry, client, self.clickhouse)
        second = provision_superset(self.registry, client, self.clickhouse)

        self.assertEqual(first["dashboard_id"], second["dashboard_id"])
        dashboards = [key for key in client.objects if key[0] == "dashboard"]
        charts = [key for key in client.objects if key[0] == "chart"]
        self.assertEqual(dashboards, [("dashboard", "Expedia Hotel Analytics")])
        self.assertEqual(charts, [("chart", "Product bookings by day")])

        chart_payload = client.objects[charts[0]]["payload"]
        self.assertEqual(chart_payload["dashboards"], [first["dashboard_id"]])
        self.assertNotIn("query_context", chart_payload)
        self.assertEqual(json.loads(chart_payload["params"])["datasource"], "2__table")

        dashboard_payload = client.objects[dashboards[0]]["payload"]
        position = json.loads(dashboard_payload["position_json"])
        chart_id = first["charts"]["Product bookings by day"]
        self.assertEqual(position[f"CHART-{chart_id}"]["meta"]["chartId"], chart_id)

        dashboard_operations = [
            operation
            for operation in client.operations
            if operation[1] == "dashboard"
        ]
        self.assertEqual(dashboard_operations[0][0], "create")
        self.assertTrue(all(item[0] == "update" for item in dashboard_operations[1:]))

    def test_registry_charts_are_all_attached_and_have_render_configuration(self):
        registry = load_registry()
        client = StatefulSupersetClient()

        result = provision_superset(registry, client, self.clickhouse)

        expected_names = [chart["name"] for chart in registry["dashboard_charts"]]
        self.assertEqual(list(result["charts"]), expected_names)
        layout = json.loads(
            client.objects[("dashboard", "Expedia Hotel Analytics")]["payload"][
                "position_json"
            ]
        )
        for chart in registry["dashboard_charts"]:
            chart_payload = client.objects[("chart", chart["name"])]["payload"]
            params = json.loads(chart_payload["params"])
            dataset_id = result["datasets"][chart["mart"]]
            chart_id = result["charts"][chart["name"]]
            self.assertEqual(chart_payload["dashboards"], [result["dashboard_id"]])
            self.assertEqual(params["datasource"], f"{dataset_id}__table")
            self.assertEqual(params["metrics"], chart["metrics"])
            self.assertIn(f"CHART-{chart_id}", layout)

        top_destinations = next(
            chart
            for chart in registry["dashboard_charts"]
            if chart["name"] == "Top destinations by bookings"
        )
        self.assertEqual(top_destinations["viz_type"], "echarts_timeseries_bar")
        self.assertEqual(top_destinations["x_axis"], "destination_id")


if __name__ == "__main__":
    unittest.main()
