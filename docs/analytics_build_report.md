# Sessionization and MARTS build report

Build timestamp: `2026-08-09T15:36:27+00:00`  
Session rule: `gap_30m_v1`  
Source population: `source_dataset = 'train'`, with non-null `user_id`, `event_ts`, and `event_date_key`.
Sessionization is an analytical reconstruction, not the source Expedia session ID.
The build uses 32 deterministic user-hash buckets, DuckDB spill-to-disk, two
threads, and a 2GB memory limit; it never creates one in-memory train table.

## Session rule

Rows are ordered per user by `event_ts, event_id`. A new session starts when the
inactivity gap is strictly greater than 30 minutes. Same-timestamp rows remain
together. `cnt` affects weighted activity metrics only; it never affects session
boundaries. Destination, channel, and search-parameter changes do not split a
session.

## Session snapshot

| metric | value |
|---|---:|
| eligible events | 37,669,324 |
| sessions | 12,242,331 |
| users | 1,198,786 |
| booking sessions | 2,661,774 |
| one-row sessions | 4,467,893 |
| maximum duration, seconds | 26,881 |
| p50 duration, seconds | 159 |
| p90 duration, seconds | 1,636 |
| p99 duration, seconds | 4,279 |

## Sensitivity

The comparison in `artifacts/session_sensitivity.csv` uses a deterministic 5%
user sample (59,948 users and
1,877,090 events). It is diagnostic only; the
materialized version remains `gap_30m_v1`.

## Metric definitions

- Row events are `COUNT(*)`; weighted events are `SUM(cnt)`.
- Booking rates use booking rows or weighted booking events as named in each mart.
- Booking value proxy is 0 for non-bookings, 1 for hotel-only bookings, and 2 for package bookings; it is not money.
- `mart_product_daily`, channel, destination, origin, and trip marts use train interaction rows with a valid project event date only.
- The active project-date range is `2013-01-01` through `2016-12-31` inclusive; events outside it remain in CORE but are excluded from sessions and behavioral marts.
- `mart_travel_calendar_daily` uses valid project event dates and booking rows with valid check-in/check-out date keys.
- `mart_user_360` includes all observed train users; `observation_end_date` is the maximum observed train event date.
- `mart_retention_cohort` is observed repeat-booking behavior from each user's first observed booking, not lifetime retention.
- The destination performance minimum flags are `row_events >= 100` and `bookings >= 10`.
- `mart_trip_profile` excludes rows with invalid lead time, stay length, or party metrics. Buckets are fixed in `tools/build_analytics.py`.

## Validation

```json
{
  "event_session_map_rows": 37669324,
  "eligible_train_events": 37669324,
  "session_rows": 12242331,
  "session_map_duplicate_keys": 0,
  "session_map_orphan_events": 0,
  "session_user_violations": 0,
  "negative_session_durations": 0,
  "session_row_count_mismatch": 0,
  "session_weighted_count_mismatch": 0,
  "session_booking_row_mismatch": 0,
  "session_first_after_last_violations": 0,
  "pass": true
}
```

## Materialized MART row counts

| mart | rows |
|---|---:|
| `mart_booking_frequency` | 5 |
| `mart_channel_platform` | 11,720 |
| `mart_data_quality_daily` | 724 |
| `mart_destination_performance` | 502,728 |
| `mart_distance_quality` | 49 |
| `mart_origin_destination` | 151,998 |
| `mart_product_daily` | 724 |
| `mart_retention_cohort` | 300 |
| `mart_session_daily` | 724 |
| `mart_travel_calendar_daily` | 6,908 |
| `mart_trip_profile` | 2,399 |
| `mart_user_360` | 1,198,786 |
