#!/usr/bin/env python3
"""Build supplementary Expedia analytical marts.

This extension is intentionally separate from tools/build_analytics.py so the
existing 12-mart builder remains stable. The canonical BI build calls both
builders, then validates all 14 marts before publication.

Outputs:
- data/derived/marts/mart_package_profile.parquet
- data/derived/marts/mart_booking_frequency_exact.parquet
- artifacts/extra_marts_manifest.json

RAW/source files are never modified.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

try:
    from tools.duckdb_runtime import configure_duckdb, runtime_settings
except ModuleNotFoundError:  # python3 tools/build_extra_marts.py
    from duckdb_runtime import configure_duckdb, runtime_settings


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "analytics.duckdb"
MARTS_DIR = ROOT / "data" / "derived" / "marts"
ARTIFACTS_DIR = ROOT / "artifacts"
TEMP_DIR = ROOT / "data" / "derived" / "duckdb_tmp" / "extra_marts"
BUILD_TS = datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def output_path(path: Path) -> str:
    return sql_literal(path.resolve().as_posix())


def scalar(con: duckdb.DuckDBPyConnection, query: str):
    return con.execute(query).fetchone()[0]


def relation_exists(con: duckdb.DuckDBPyConnection, relation: str) -> bool:
    schema, table = relation.split(".", 1)
    return bool(
        scalar(
            con,
            f"""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = {sql_literal(schema)}
              AND table_name = {sql_literal(table)}
            """,
        )
    )


def materialize(
    con: duckdb.DuckDBPyConnection,
    name: str,
    query: str,
) -> tuple[Path, int]:
    MARTS_DIR.mkdir(parents=True, exist_ok=True)
    path = MARTS_DIR / f"{name}.parquet"
    if path.exists():
        path.unlink()
    con.execute(
        f"COPY ({query}) TO {output_path(path)} "
        "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 500000)"
    )
    con.execute("CREATE SCHEMA IF NOT EXISTS marts")
    con.execute(
        f"CREATE OR REPLACE VIEW marts.{name} AS "
        f"SELECT * FROM read_parquet({output_path(path)})"
    )
    rows = int(scalar(con, f"SELECT COUNT(*) FROM marts.{name}"))
    return path, rows


def build_package_profile(con: duckdb.DuckDBPyConnection) -> tuple[Path, int]:
    # Grain:
    # one month × package flag × lead bucket × stay bucket × party segment
    # × channel × mobile flag.
    query = """
    WITH enriched AS (
        SELECT
            e.*,
            d.year_month,
            sp.adults_cnt,
            sp.children_cnt,
            CASE
                WHEN e.lead_days BETWEEN 0 AND 1 THEN 'same_next_day'
                WHEN e.lead_days BETWEEN 2 AND 7 THEN '2_7'
                WHEN e.lead_days BETWEEN 8 AND 30 THEN '8_30'
                WHEN e.lead_days BETWEEN 31 AND 90 THEN '31_90'
                WHEN e.lead_days >= 91 THEN '91_plus'
            END AS lead_time_bucket,
            CASE
                WHEN e.stay_nights = 1 THEN '1'
                WHEN e.stay_nights BETWEEN 2 AND 3 THEN '2_3'
                WHEN e.stay_nights BETWEEN 4 AND 7 THEN '4_7'
                WHEN e.stay_nights BETWEEN 8 AND 14 THEN '8_14'
                WHEN e.stay_nights >= 15 THEN '15_plus'
            END AS stay_length_bucket,
            CASE
                WHEN e.party_size = 1 THEN 'solo'
                WHEN sp.adults_cnt = 2 AND COALESCE(sp.children_cnt, 0) = 0 THEN 'couple'
                WHEN COALESCE(sp.children_cnt, 0) > 0 THEN 'family_with_children'
                WHEN e.party_size > 0 THEN 'group'
            END AS party_segment
        FROM core.fct_event e
        LEFT JOIN core.dim_date d
          ON d.date_key = e.event_date_key
        LEFT JOIN core.dim_search_params sp
          ON sp.search_params_id = e.search_params_id
        WHERE e.source_dataset = 'train'
          AND e.user_id IS NOT NULL
          AND e.event_ts IS NOT NULL
          AND e.event_date_key IS NOT NULL
          AND e.valid_for_lead_time
          AND e.valid_for_stay_length
          AND e.valid_for_party_metrics
    )
    SELECT
        year_month,
        is_package,
        lead_time_bucket,
        stay_length_bucket,
        party_segment,
        channel,
        is_mobile,
        COUNT(DISTINCT user_id)::BIGINT AS users,
        COUNT(*)::BIGINT AS events,
        SUM(COALESCE(cnt, 0))::BIGINT AS weighted_events,
        COUNT(*) FILTER (WHERE is_booking = 1)::BIGINT AS bookings,
        SUM(CASE WHEN is_booking = 1 THEN COALESCE(cnt, 0) ELSE 0 END)::BIGINT
            AS weighted_bookings,
        1.0 * COUNT(*) FILTER (WHERE is_booking = 1)
            / NULLIF(COUNT(*), 0) AS booking_row_rate,
        1.0 * SUM(CASE WHEN is_booking = 1 THEN COALESCE(cnt, 0) ELSE 0 END)
            / NULLIF(SUM(COALESCE(cnt, 0)), 0) AS booking_weighted_event_rate,
        SUM(
            CASE WHEN is_booking = 1
                 THEN COALESCE(booking_value_proxy, 0)
                 ELSE 0 END
        )::BIGINT AS booking_value_proxy_total
    FROM enriched
    GROUP BY
        year_month,
        is_package,
        lead_time_bucket,
        stay_length_bucket,
        party_segment,
        channel,
        is_mobile
    """
    return materialize(con, "mart_package_profile", query)


def build_booking_frequency_exact(
    con: duckdb.DuckDBPyConnection,
) -> tuple[Path, int]:
    # Grain: one exact observed booking-row count.
    query = """
    SELECT
        bookings,
        COUNT(*)::BIGINT AS users,
        1.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS user_share
    FROM marts.mart_user_360
    GROUP BY bookings
    ORDER BY bookings
    """
    return materialize(con, "mart_booking_frequency_exact", query)


def main() -> None:
    for directory in (MARTS_DIR, ARTIFACTS_DIR, TEMP_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DB_PATH))
    try:
        configure_duckdb(con, TEMP_DIR)
        required = [
            "core.fct_event",
            "core.dim_date",
            "core.dim_search_params",
            "marts.mart_user_360",
        ]
        missing = [name for name in required if not relation_exists(con, name)]
        if missing:
            raise RuntimeError(
                "Required upstream objects are missing: " + ", ".join(missing)
                + ". Run `python3 tools/build_core.py` and "
                  "`python3 tools/build_analytics.py` first."
            )

        package_path, package_rows = build_package_profile(con)
        exact_path, exact_rows = build_booking_frequency_exact(con)

        threads, memory_limit = runtime_settings()
        manifest = {
            "manifest_version": 1,
            "build_timestamp": BUILD_TS,
            "runtime": {
                "duckdb_threads": threads,
                "duckdb_memory_limit": memory_limit,
            },
            "marts": [
                {
                    "table_name": "marts.mart_package_profile",
                    "grain": (
                        "month x package x lead bucket x stay bucket x party "
                        "segment x channel x mobile"
                    ),
                    "row_count": package_rows,
                    "parquet_path": str(package_path.relative_to(ROOT)),
                },
                {
                    "table_name": "marts.mart_booking_frequency_exact",
                    "grain": "exact observed booking-row count",
                    "row_count": exact_rows,
                    "parquet_path": str(exact_path.relative_to(ROOT)),
                },
            ],
        }
        (ARTIFACTS_DIR / "extra_marts_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            "Built supplementary marts: "
            f"mart_package_profile={package_rows:,}, "
            f"mart_booking_frequency_exact={exact_rows:,}"
        )
    finally:
        con.close()


if __name__ == "__main__":
    main()
