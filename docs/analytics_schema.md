# Analytics extension schema

The base CORE objects are documented in [core_schema.md](core_schema.md). This
extension is built by `tools/build_analytics.py` and reads CORE only.

## Session objects

| Object | Grain | Key |
|---|---|---|
| `core.event_session_map` | one eligible train event assigned to one session-rule version | `event_id, session_rule_version` |
| `core.fct_session` | one reconstructed user session under one rule version | `session_id` |

Current rule: `gap_30m_v1`. Sessions are ordered by `event_ts, event_id` within
user and split only when the gap is strictly greater than 30 minutes. `cnt` is
not used for boundaries.

## Materialized marts

| Mart | Grain |
|---|---|
| `marts.mart_product_daily` | event date |
| `marts.mart_session_daily` | session start date |
| `marts.mart_travel_calendar_daily` | calendar date |
| `marts.mart_channel_platform` | month × channel × platform × mobile flag |
| `marts.mart_destination_performance` | month × destination × hotel market |
| `marts.mart_user_360` | user |
| `marts.mart_origin_destination` | month × user country × hotel country |
| `marts.mart_trip_profile` | month × lead bucket × stay bucket × party segment |
| `marts.mart_retention_cohort` | first booking month × months since first booking |
| `marts.mart_booking_frequency` | booking-count bucket |
| `marts.mart_data_quality_daily` | event date |
| `marts.mart_distance_quality` | imputation level × support threshold |

All behavioral marts use `source_dataset = 'train'`. Row-level volumes use
`COUNT(*)`; weighted volumes use `SUM(cnt)`. Booking rates are named explicitly
as row-based or `cnt`-weighted. `booking_value_proxy` is a relative score, not
money.

## Resource-safe build

Sessionization is exact because users cannot cross hash buckets. The build uses
32 deterministic user-hash buckets, writes Parquet fragments under
`data/derived/core/session_events/`, aggregates each fragment separately, and
limits DuckDB to two threads and 2GB. A cache manifest invalidates fragments
when the CORE build timestamp or eligible event count changes.

See [analytics_build_report.md](analytics_build_report.md) for the latest
counts, sensitivity comparison, and validation results. The machine-readable
manifest is [analytics_manifest.json](../artifacts/analytics_manifest.json).
