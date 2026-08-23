"""Validate only the seven marts required by the supplied Yandex DataLens dashboard."""
from __future__ import annotations

import sys
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
MARTS_DIR = ROOT / "data" / "derived" / "marts"

MARTS = {
    "mart_product_daily": ["date_key"],
    "mart_session_daily": ["date_key"],
    "mart_channel_platform": ["year_month", "channel", "platform_id", "is_mobile"],
    "mart_trip_profile": ["year_month", "lead_time_bucket", "stay_length_bucket", "party_segment"],
    "mart_retention_cohort": ["cohort_month", "months_since_first_booking"],
    "mart_travel_calendar_daily": ["date_key"],
    "mart_destination_performance": ["year_month", "destination_id", "hotel_market_id"],
}

RATE_COLUMNS = {
    "mart_product_daily": ["booking_row_rate", "booking_weighted_event_rate", "booker_rate", "mobile_row_share", "mobile_booking_share", "package_booking_share", "distance_imputed_share"],
    "mart_session_daily": ["session_booking_rate", "multi_destination_session_share"],
    "mart_channel_platform": ["booking_row_rate", "booking_weighted_event_rate", "package_booking_share"],
    "mart_trip_profile": ["booking_row_rate", "booking_weighted_event_rate", "package_share", "mobile_share", "session_booking_rate"],
    "mart_retention_cohort": ["booking_retention_rate"],
    "mart_destination_performance": ["booking_row_rate", "booking_weighted_event_rate", "package_booking_share"],
}

def ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def source(path: Path) -> str:
    p = str(path.resolve()).replace("\\", "/").replace("'", "''")
    return f"read_parquet('{p}')"

def scalar(con, sql):
    return con.execute(sql).fetchone()[0]

def main() -> int:
    con = duckdb.connect()
    failures = []
    rows = {}

    for mart, grain in MARTS.items():
        path = MARTS_DIR / f"{mart}.parquet"
        if not path.is_file():
            failures.append(f"{mart}: missing {path}")
            continue
        rel = source(path)
        rows[mart] = int(scalar(con, f"SELECT COUNT(*) FROM {rel}"))
        if rows[mart] <= 0:
            failures.append(f"{mart}: empty")
        grain_sql = ", ".join(ident(c) for c in grain)
        null_pred = " OR ".join(f"{ident(c)} IS NULL" for c in grain)
        nulls = int(scalar(con, f"SELECT COUNT(*) FROM {rel} WHERE {null_pred}"))
        dups = int(scalar(con, f"""
            SELECT COALESCE(SUM(n), 0)
            FROM (
                SELECT COUNT(*) AS n
                FROM {rel}
                GROUP BY {grain_sql}
                HAVING COUNT(*) > 1
            )
        """))
        if nulls:
            failures.append(f"{mart}: {nulls} rows with NULL grain")
        if dups:
            failures.append(f"{mart}: {dups} rows in duplicate grain groups")

        cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {rel}").fetchall()}
        for col in RATE_COLUMNS.get(mart, []):
            if col in cols:
                bad = int(scalar(con, f"""
                    SELECT COUNT(*) FROM {rel}
                    WHERE {ident(col)} IS NOT NULL
                      AND ({ident(col)} < 0 OR {ident(col)} > 1)
                """))
                if bad:
                    failures.append(f"{mart}.{col}: {bad} values outside [0,1]")

    required = {"mart_product_daily", "mart_channel_platform", "mart_destination_performance", "mart_travel_calendar_daily"}
    if required.issubset(rows):
        def sums(mart, fields):
            rel = source(MARTS_DIR / f"{mart}.parquet")
            return tuple(con.execute(
                "SELECT " + ", ".join(f"SUM({ident(f)})" for f in fields) + f" FROM {rel}"
            ).fetchone())

        product = sums("mart_product_daily", ["row_events", "weighted_events", "bookings"])
        channel = sums("mart_channel_platform", ["row_events", "weighted_events", "bookings"])
        destination = sums("mart_destination_performance", ["row_events", "weighted_events", "bookings"])
        calendar = sums("mart_travel_calendar_daily", ["events_on_date", "weighted_events_on_date", "bookings_made_on_date"])
        if not (product == channel == destination == calendar):
            failures.append(f"reconciliation mismatch: product={product}, channel={channel}, destination={destination}, calendar={calendar}")

    if "mart_session_daily" in rows:
        rel = source(MARTS_DIR / "mart_session_daily.parquet")
        bad = int(scalar(con, f"SELECT COUNT(*) FROM {rel} WHERE booking_sessions > sessions"))
        if bad:
            failures.append(f"mart_session_daily: {bad} rows with booking_sessions > sessions")

    if "mart_retention_cohort" in rows:
        rel = source(MARTS_DIR / "mart_retention_cohort.parquet")
        bad = int(scalar(con, f"SELECT COUNT(*) FROM {rel} WHERE returned_bookers > cohort_users"))
        if bad:
            failures.append(f"mart_retention_cohort: {bad} rows with returned_bookers > cohort_users")

    print("DataLens marts validation")
    for mart in MARTS:
        if mart in rows:
            print(f"  PASS {mart}: {rows[mart]:,} rows")

    if failures:
        print("\nFAIL")
        for item in failures:
            print(" -", item)
        return 1

    print("\nPASS: 7/7 DataLens marts are valid and reconciled.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
