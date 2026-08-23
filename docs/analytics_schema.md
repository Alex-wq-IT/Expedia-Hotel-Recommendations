# Analytics extension schema

The base CORE objects are documented in [core_schema.md](core_schema.md).

The analytical layer is built in two steps:

```text
tools/build_analytics.py      -> 12 base marts + session objects
tools/build_extra_marts.py    -> 2 supplementary marts
tools/validate_marts.py       -> schema/grain/reconciliation validation
```

The production Makefile runs all three steps through `make bi-build`.

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
| `marts.mart_package_profile` | month × package × lead bucket × stay bucket × party segment × channel × mobile flag |
| `marts.mart_retention_cohort` | first booking month × months since first booking |
| `marts.mart_booking_frequency` | booking-count bucket |
| `marts.mart_booking_frequency_exact` | exact observed booking count |
| `marts.mart_data_quality_daily` | event date |
| `marts.mart_distance_quality` | imputation level × support threshold |

All behavioral marts use `source_dataset = 'train'` where applicable.
Row-level volumes use `COUNT(*)`; weighted volumes use `SUM(cnt)`.
`booking_value_proxy` is a relative score, not money/revenue.

## Supplementary marts

`mart_package_profile` and `mart_booking_frequency_exact` are built by
`tools/build_extra_marts.py` after the base analytical build. The script reads
CORE/base MARTS only, writes Parquet under `data/derived/marts/`, refreshes
DuckDB views, and records `artifacts/extra_marts_manifest.json`.

## Validation contract

`tools/validate_marts.py` verifies all 14 physical marts against
`bi/registry.json`, including schema, grain, domains, logical constraints and
reconciliation of global totals.

Run:

```bash
make bi-build
# or only validation:
make bi-validate
```

See [marts_architecture.md](marts_architecture.md),
[marts_catalog.md](marts_catalog.md) and
[marts_dashboard_logic.md](marts_dashboard_logic.md).
