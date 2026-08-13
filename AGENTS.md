# AGENTS.md — Expedia Hotel Recommendations analytics

## Mission

Act as a data/product analyst for this repository. Use SQL-first analysis over
the local DuckDB catalog and Parquet layers. Prefer reproducible queries and
explicit metric definitions over one-off Python data loading.

Primary topics: users, searches, clicks, bookings, destinations, channels,
devices, hotel markets/clusters, seasonality, sessions, retention and repeat
behavior.

Respond in the language used by the user, usually Russian.

## Current architecture

The current local pipeline is materialized and follows:

```text
RAW → STAGING → CORE → MARTS → BI / product analytics
```

The detailed catalog, field descriptions and lineage are in
[`artifacts/schema.md`](artifacts/schema.md). The interactive view is
[`artifacts/data_flow.html`](artifacts/data_flow.html).

DuckDB catalog objects currently registered in `data/analytics.duckdb`:

### RAW — immutable source-aligned views

- `raw.train` — one source train log row; includes `is_booking`, `cnt` and `hotel_cluster`.
- `raw.test` — one source test log row; includes `id`, but no train outcomes.
- `raw.destinations` — one destination row with `srch_destination_id` and latent `d1` … `d149` features.

Raw source files are under `data/parquet/`, `data/train_parquet/` and the
corresponding source CSV paths. Raw is read-only and contains no business
deduplication, imputation or aggregation.

### STAGING — source-grain technical normalization

- `staging.interaction` — one source interaction row. Preserves source columns and adds normalized timestamps/dates, lineage metadata, duplicate metadata, missing-distance flag and quality flags.
- `staging.destinations` — one source destination row. Adds lineage metadata and exposes the destination ID as `destination_id`.

STAGING does not destructively filter suspicious records, perform business
aggregation, sessionize users or impute distance.

### CORE — business entities and facts

Dimensions:

- `core.dim_date` — one calendar day; used for event, check-in and check-out roles.
- `core.dim_hour` — one hour of day.
- `core.dim_user` — one user.
- `core.dim_user_location` — one observed user country/region/city combination.
- `core.dim_platform` — one `site_name × posa_continent` combination.
- `core.dim_destination` — one destination ID plus latent `d1` … `d149` features when available.
- `core.dim_destination_type` — one destination type ID.
- `core.dim_hotel_market` — one observed `hotel_market × hotel_country × hotel_continent` combination.
- `core.dim_hotel_cluster` — one hotel cluster ID; this is not a physical hotel ID.
- `core.dim_search_params` — one adults/children/rooms/stay/party feature combination.

Facts and references:

- `core.fct_event` — one unique aggregated source log row after controlled exact deduplication. It retains `cnt`, source dataset, date keys, dimensions, derived trip features, quality flags and distance provenance.
- `core.fct_booking` — one train booking log event, filtered to `is_booking = 1`.
- `core.ref_distance_stats` — one median distance estimator per hierarchy group, with support and holdout validation metrics.
- `core.event_session_map` — one eligible train event assigned to one session under `gap_30m_v1`.
- `core.fct_session` — one reconstructed user session under `gap_30m_v1`; session boundaries use event-time gaps greater than 30 minutes and do not use `cnt`.

Sessionization also writes deterministic working fragments under
`data/derived/core/session_events/` and `data/derived/core/session_summaries/`.
These fragment directories support the build and are not additional business
tables in the DuckDB contract.

CORE processing includes controlled exact deduplication, deterministic
dimension keys, derived lead/stay/party features, metric-validity flags and
validated distance enrichment. It does not remove rows merely because their
quality flags are suspicious.

### MARTS — business-ready aggregates

- `marts.mart_product_daily` — one event date.
- `marts.mart_session_daily` — one session start date.
- `marts.mart_travel_calendar_daily` — one calendar date, combining event-date and stay-date roles.
- `marts.mart_channel_platform` — one month × channel × platform × mobile flag.
- `marts.mart_destination_performance` — one month × destination × hotel market.
- `marts.mart_user_360` — one user.
- `marts.mart_origin_destination` — one month × user country × hotel country.
- `marts.mart_trip_profile` — one month × lead-time bucket × stay-length bucket × party segment.
- `marts.mart_retention_cohort` — one first-booking month × months since first booking.
- `marts.mart_booking_frequency` — one booking-count bucket.
- `marts.mart_data_quality_daily` — one event date.
- `marts.mart_distance_quality` — one imputation level × support threshold.

MARTS are materialized under `data/derived/marts/`. Behavioral marts use
`source_dataset = 'train'` where applicable. Measures are named so that
row-based volumes (`COUNT(*)`) are distinguishable from weighted volumes
(`SUM(cnt)`).

### Supporting schemas

- `meta.core_build_manifest` and `meta.analytics_build_manifest` — build and validation metadata.
- `scratch` — temporary exploratory objects only; not a contract layer.

## Analysis source priority

1. Use an appropriate `marts.*` object when its grain and population fit the question.
2. Otherwise use `core.*` facts/dimensions.
3. Otherwise use `staging.*` for source-grain quality or normalization questions.
4. Otherwise query `raw.*` directly.
5. Do not invent tables or claim that a target/contract object is materialized.
6. Do not create a permanent mart silently. First propose its grain, key, dimensions, measures, source logic and quality checks.

## Absolute safety rules

Raw data is read-only. Never modify, overwrite, truncate, rename, move,
delete or reformat:

- `data/train.csv`, `data/test.csv`, `data/destinations.csv`;
- anything under `data/parquet/` or `data/train_parquet/`;
- `raw.*` views;
- any other file explicitly identified as an immutable source dataset.

During ordinary analysis:

- connect to `data/analytics.duckdb` in read-only mode;
- use analytical SQL only;
- do not execute `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `TRUNCATE`, `COPY`, `EXPORT`, `IMPORT` or other filesystem/database writes;
- do not install packages, extensions or system dependencies unless needed and requested.

If the user explicitly asks to build or rebuild derived data, writes are
allowed only to the relevant `data/derived/staging/`, `data/derived/core/`,
`data/derived/marts/` or scratch locations. Raw files and `raw` remain
immutable.

## Dataset and field semantics

The base data is the Kaggle **Expedia Hotel Recommendations** dataset. Treat
the actual local schema as the source of truth; inspect `DESCRIBE` before
relying on a field. In particular, source-aligned raw types are not always
normalized: `raw.train.date_time`, `raw.train.srch_ci` and
`raw.train.srch_co` are source strings, while `raw.test` has some normalized
date types.

### Event and stay time

- `date_time` / `event_ts` — event timestamp.
- `srch_ci` / `checkin_date` — requested check-in date.
- `srch_co` / `checkout_date` — requested check-out date.

Never confuse event time with stay time. `event_date_key` and
`checkin_date_key` answer different business questions.

### User, point of sale and acquisition

- `user_id` — encoded user identifier.
- `site_name` — encoded Expedia point-of-sale/site identifier.
- `posa_continent` — encoded continent associated with the point of sale, not necessarily the user's physical continent.
- `user_location_country`, `user_location_region`, `user_location_city` — encoded user-origin IDs.
- `channel` — encoded marketing channel.
- `is_mobile` — mobile indicator.
- `is_package` — whether the interaction/booking is part of a package.
- `orig_destination_distance` / `distance_raw` — source physical distance when available.

Encoded IDs are not real-world labels. Do not invent country, city, hotel or
destination names from them. A mapping requires an external validated mapping
or an explicitly approved inference methodology.

### Search party and destination

- `srch_adults_cnt`, `srch_children_cnt`, `srch_rm_cnt` — requested adults, children and rooms.
- `srch_destination_id` / `destination_id` — encoded destination key.
- `srch_destination_type_id` / `destination_type_id` — encoded destination type.
- `d1` … `d149` — latent destination/search-region numeric features, not human-readable geography.
- `hotel_continent`, `hotel_country`, `hotel_market`, `hotel_cluster` — encoded hotel-side IDs; `hotel_cluster` is the competition target, not a hotel ID.

Some train/test destination IDs have no row in the destinations reference. Do
not use an inner join unless intentionally accepting that row loss; check join
uniqueness and fan-out first.

### Interaction and booking

- `is_booking = 1` identifies a booking in train; `0` identifies a non-booking interaction/click.
- `cnt` is the multiplicity of similar events represented by one aggregated source row. It is not a session ID and does not define session boundaries.
- `booking_value_proxy` is a relative score: 0 for non-booking, 1 for hotel-only booking and 2 for package booking. It is not money or revenue.

Row count and event volume are different measures. Whenever reporting
events, clicks or bookings, state whether the numerator uses row count or
`SUM(cnt)`. If ambiguous, calculate both or explicitly record the chosen
definition.

## Grain and joins

Never aggregate before identifying the grain. For every reusable query/model,
state the intended grain in a SQL comment or analysis note, for example:

- one raw/staging interaction row;
- one CORE event;
- one booking event;
- one user;
- one user per calendar month;
- one destination;
- one hotel market per month;
- one reconstructed session.

Before joining, check whether the right-side key is unique. Report possible
fan-out and preserve unmatched rows when the business question requires it.

## SQL-first workflow

1. Inspect actual schemas, tables/views and relevant columns.
2. Define population, grain, numerator, denominator and time basis.
3. Query DuckDB directly in read-only mode.
4. Filter and project early; aggregate inside DuckDB.
5. Pull only small aggregated results into Python.
6. Validate row counts, denominators, nulls, duplicates and join fan-out.
7. Report assumptions, edge cases and whether `cnt` weighting was used.

The repository currently does not contain `tools/query_duckdb.py`. Use the
following equivalent read-only pattern from the repository root:

```bash
python - <<'PY'
import duckdb

con = duckdb.connect("data/analytics.duckdb", read_only=True)
print(con.sql("SELECT COUNT(*) FROM raw.train").fetchall())
con.close()
PY
```

For complex investigations, save important SQL under `sql/checks/` or an
appropriately named analysis file rather than hiding business logic in a
notebook. Do not load the full train Parquet/CSV into pandas.

## Metric discipline

Every metric answer should make explicit when relevant:

- numerator and denominator;
- population/cohort and time window;
- event-time versus check-in-time basis;
- row-based versus `cnt`-weighted measure;
- null handling;
- whether clicks and bookings are mixed;
- whether the metric is user-, event-, session- or booking-level.

For booking metrics, normally filter `is_booking = 1` unless the metric
explicitly includes clicks. For repeat-booker metrics, distinguish:

- all observed users;
- users with at least one booking;
- users with more than one booking.

Do not call a user active or retained without declaring the activity definition
and time window. `marts.mart_retention_cohort` is booking-based and should not
be described as generic product retention without qualification.

## Time, leakage and distance rules

The public train/test split is temporal. Preserve time ordering when
evaluating predictive or behavioral hypotheses. Do not use future information
to define historical cohorts or timestamped features unless the task is
explicitly retrospective.

Distance imputation is a CORE-only operation. `distance_raw` is immutable;
missing values may be filled into `distance_filled` using validated median
estimators with minimum support and recorded `distance_imputation_level`,
support and validation fields. Do not silently replace raw distance values.

## Quality checks and performance

Before conclusions, consider row count, distinct users, date range, null
rates, duplicate/grain issues, unexpected `is_booking` values, join fan-out,
denominator consistency and session validation checks.

The raw train data is large. Query Parquet rather than CSV, select only needed
columns, filter early, aggregate in DuckDB and avoid full-data pandas loads.
Use approximate distinct counts only for exploration; use exact counts for
final KPIs unless clearly labeled approximate. Materialize/cache only genuinely
reusable transformations in derived layers.

## Artifact and change rules

Analysis may create SQL under `sql/`, small outputs under `outputs/`,
exploratory notebooks and their small supporting files under the canonical
root-level `eda/`, operational setup/build notebooks under `notebooks/`, and
explicitly requested derived models. Do not place generated datasets or large
raw/intermediate data in `eda/`. Do not edit unrelated project files.

If a new mart is created, document its purpose, grain, primary/unique key
expectation, sources, dimensions, measures, filters, refresh logic and data
quality checks. When changing the pipeline, update the relevant build
manifest and schema documentation.
