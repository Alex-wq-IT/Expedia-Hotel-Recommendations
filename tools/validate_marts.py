#!/usr/bin/env python3
"""Validate the complete Expedia MART layer against the BI registry.

The validator is SQL-first and reads Parquet by default, so it can run on the
canonical production artifacts without loading the 1.2M-row user mart into
pandas.

Usage:
    python3 tools/validate_marts.py
    python3 tools/validate_marts.py --dir /path/to/csvs --extension csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "data" / "derived" / "marts"
DEFAULT_REGISTRY = ROOT / "bi" / "registry.json"

GRAINS: dict[str, list[str]] = {
    "mart_product_daily": ["date_key"],
    "mart_session_daily": ["date_key"],
    "mart_travel_calendar_daily": ["date_key"],
    "mart_channel_platform": ["year_month", "channel", "platform_id", "is_mobile"],
    "mart_destination_performance": [
        "year_month", "destination_id", "hotel_market_id"
    ],
    "mart_user_360": ["user_id"],
    "mart_origin_destination": ["year_month", "user_country", "hotel_country"],
    "mart_trip_profile": [
        "year_month", "lead_time_bucket", "stay_length_bucket", "party_segment"
    ],
    "mart_package_profile": [
        "year_month", "is_package", "lead_time_bucket", "stay_length_bucket",
        "party_segment", "channel", "is_mobile"
    ],
    "mart_retention_cohort": ["cohort_month", "months_since_first_booking"],
    "mart_booking_frequency": ["booking_count_bucket"],
    "mart_booking_frequency_exact": ["bookings"],
    "mart_data_quality_daily": ["date_key"],
    "mart_distance_quality": ["imputation_level", "min_support"],
}

RATE_COLUMNS = {
    "booking_row_rate", "booking_weighted_event_rate", "booker_rate",
    "mobile_row_share", "mobile_booking_share", "package_booking_share",
    "session_booking_rate", "multi_destination_session_share", "user_share",
    "booking_retention_rate", "missing_distance_share", "imputed_distance_share",
    "invalid_lead_time_share", "invalid_stay_share", "zero_party_share",
    "quality_issue_share", "package_share", "mobile_share",
}

COUNT_COLUMNS = {
    "active_users", "row_events", "weighted_events", "bookings", "bookers",
    "sessions", "booking_sessions", "events", "weighted_bookings", "users",
    "cohort_users", "returned_bookers", "rows", "events_on_date",
    "weighted_events_on_date", "bookings_made_on_date", "checkins_on_date",
    "checkouts_on_date", "holdout_rows", "covered_rows",
}


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def relation_expr(path: Path, extension: str) -> str:
    fn = "read_parquet" if extension == "parquet" else "read_csv_auto"
    return f"{fn}({quote(path.resolve().as_posix())})"


def scalar(con: duckdb.DuckDBPyConnection, sql: str):
    return con.execute(sql).fetchone()[0]


def columns(con: duckdb.DuckDBPyConnection, relation: str) -> set[str]:
    rows = con.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall()
    return {row[0] for row in rows}


def load_registry(path: Path) -> dict:
    registry = json.loads(path.read_text(encoding="utf-8"))
    names = [item["name"] for item in registry.get("marts", [])]
    if len(names) != len(set(names)):
        raise ValueError("Registry contains duplicate mart names")
    return registry


def check_registry(con, registry, relations, failures):
    registry_names = [item["name"] for item in registry["marts"]]
    expected = set(GRAINS)
    if set(registry_names) != expected:
        failures.append(
            "registry mart set mismatch: expected "
            f"{sorted(expected)}, got {sorted(registry_names)}"
        )

    for item in registry["marts"]:
        name = item["name"]
        if name not in relations:
            continue
        cols = columns(con, relations[name])
        time_column = item.get("time_column")
        if time_column and time_column not in cols:
            failures.append(f"{name}: missing time column {time_column!r}")

        for metric in item.get("metrics", []):
            if "__" not in metric:
                failures.append(f"{name}: malformed metric {metric!r}")
                continue
            function, column = metric.split("__", 1)
            if function not in {"sum", "avg", "min", "max", "count"}:
                failures.append(f"{name}: unsupported metric function {metric!r}")
            if column not in cols:
                failures.append(
                    f"{name}: registry metric references missing column {column!r}"
                )


def check_grain_and_domains(con, name, relation, failures):
    cols = columns(con, relation)
    keys = GRAINS[name]
    missing_keys = [key for key in keys if key not in cols]
    if missing_keys:
        failures.append(f"{name}: missing grain keys {missing_keys}")
        return

    key_sql = ", ".join(f'"{key}"' for key in keys)
    null_pred = " OR ".join(f'"{key}" IS NULL' for key in keys)
    duplicate_groups = int(
        scalar(
            con,
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT {key_sql}
                FROM {relation}
                GROUP BY {key_sql}
                HAVING COUNT(*) > 1
            )
            """,
        )
    )
    null_grain_rows = int(
        scalar(con, f"SELECT COUNT(*) FROM {relation} WHERE {null_pred}")
    )
    row_count = int(scalar(con, f"SELECT COUNT(*) FROM {relation}"))

    print(
        f"{name:34s} rows={row_count:9,d} "
        f"duplicate_grain_groups={duplicate_groups:4d} "
        f"null_grain_rows={null_grain_rows:4d}"
    )
    if duplicate_groups:
        failures.append(f"{name}: duplicate grain groups={duplicate_groups}")
    if null_grain_rows:
        failures.append(f"{name}: null grain rows={null_grain_rows}")

    for column in RATE_COLUMNS.intersection(cols):
        bad = int(
            scalar(
                con,
                f"""
                SELECT COUNT(*)
                FROM {relation}
                WHERE "{column}" IS NOT NULL
                  AND ("{column}" < 0 OR "{column}" > 1)
                """,
            )
        )
        if bad:
            failures.append(f"{name}.{column}: {bad} values outside [0,1]")

    for column in COUNT_COLUMNS.intersection(cols):
        bad = int(
            scalar(
                con,
                f"""
                SELECT COUNT(*)
                FROM {relation}
                WHERE "{column}" IS NOT NULL AND "{column}" < 0
                """,
            )
        )
        if bad:
            failures.append(f"{name}.{column}: {bad} negative values")


def relation_sum(con, relation, column):
    value = scalar(con, f'SELECT SUM("{column}") FROM {relation}')
    return int(value or 0)


def reconcile(con, relations, failures):
    p = relations["mart_product_daily"]
    checks = [
        ("product vs channel row_events",
         relation_sum(con, p, "row_events"),
         relation_sum(con, relations["mart_channel_platform"], "row_events")),
        ("product vs channel bookings",
         relation_sum(con, p, "bookings"),
         relation_sum(con, relations["mart_channel_platform"], "bookings")),
        ("product vs destination row_events",
         relation_sum(con, p, "row_events"),
         relation_sum(con, relations["mart_destination_performance"], "row_events")),
        ("product vs destination bookings",
         relation_sum(con, p, "bookings"),
         relation_sum(con, relations["mart_destination_performance"], "bookings")),
        ("product vs origin row_events",
         relation_sum(con, p, "row_events"),
         relation_sum(con, relations["mart_origin_destination"], "row_events")),
        ("product vs origin bookings",
         relation_sum(con, p, "bookings"),
         relation_sum(con, relations["mart_origin_destination"], "bookings")),
        ("product vs calendar events",
         relation_sum(con, p, "row_events"),
         relation_sum(con, relations["mart_travel_calendar_daily"], "events_on_date")),
        ("product vs calendar bookings",
         relation_sum(con, p, "bookings"),
         relation_sum(con, relations["mart_travel_calendar_daily"], "bookings_made_on_date")),
        ("product vs data-quality rows",
         relation_sum(con, p, "row_events"),
         relation_sum(con, relations["mart_data_quality_daily"], "rows")),
        ("user360 bookings vs product bookings",
         relation_sum(con, relations["mart_user_360"], "bookings"),
         relation_sum(con, p, "bookings")),
        ("user360 users vs frequency users",
         int(scalar(con, f'SELECT COUNT(*) FROM {relations["mart_user_360"]}')),
         relation_sum(con, relations["mart_booking_frequency"], "users")),
        ("user360 users vs exact-frequency users",
         int(scalar(con, f'SELECT COUNT(*) FROM {relations["mart_user_360"]}')),
         relation_sum(con, relations["mart_booking_frequency_exact"], "users")),
    ]

    print("\nReconciliation:")
    for label, left, right in checks:
        ok = left == right
        print(f"{'PASS' if ok else 'FAIL'} {label}: {left:,} vs {right:,}")
        if not ok:
            failures.append(f"{label}: {left} != {right}")


def logical_constraints(con, relations, failures):
    checks = [
        ("retention returned_bookers <= cohort_users",
         f"""SELECT COUNT(*) FROM {relations["mart_retention_cohort"]}
             WHERE returned_bookers > cohort_users"""),
        ("session booking_sessions <= sessions",
         f"""SELECT COUNT(*) FROM {relations["mart_session_daily"]}
             WHERE booking_sessions > sessions"""),
        ("distance covered_rows <= holdout_rows",
         f"""SELECT COUNT(*) FROM {relations["mart_distance_quality"]}
             WHERE covered_rows > holdout_rows"""),
        ("product bookings <= row_events",
         f"""SELECT COUNT(*) FROM {relations["mart_product_daily"]}
             WHERE bookings > row_events"""),
        ("package bookings <= events",
         f"""SELECT COUNT(*) FROM {relations["mart_package_profile"]}
             WHERE bookings > events"""),
    ]
    for label, sql in checks:
        bad = int(scalar(con, sql))
        if bad:
            failures.append(f"{label}: violating rows={bad}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--extension", choices=("parquet", "csv"), default="parquet")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()

    registry = load_registry(args.registry)
    failures = []
    relations = {}

    for name in GRAINS:
        path = args.dir / f"{name}.{args.extension}"
        if not path.is_file():
            failures.append(f"missing mart file: {path}")
            continue
        relations[name] = relation_expr(path, args.extension)

    con = duckdb.connect(":memory:")
    try:
        if len(relations) == len(GRAINS):
            check_registry(con, registry, relations, failures)
            print("Grain/schema checks:")
            for name in GRAINS:
                check_grain_and_domains(con, name, relations[name], failures)
            logical_constraints(con, relations, failures)
            reconcile(con, relations, failures)

        if failures:
            print("\nFAILED:")
            for failure in failures:
                print("-", failure)
            raise SystemExit(1)

        print("\nALL 14 MART CHECKS PASSED")
    finally:
        con.close()


if __name__ == "__main__":
    main()
