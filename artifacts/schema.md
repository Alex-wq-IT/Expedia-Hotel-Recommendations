# Текущая схема данных Expedia Analytics

> Сгенерировано `tools/build_schema_artifacts.py` из read-only каталога `data/analytics.duckdb`; состояние на момент генерации отражает зарегистрированные объекты и существующие Parquet-слои.

## Поток

`RAW → STAGING → CORE → MARTS → BI / product analytics`

### Правила интерпретации

- `raw` неизменяем: исходные значения, включая NULL и encoded IDs, сохраняются.
- STAGING сохраняет grain источника и добавляет технические типы, даты, lineage и quality flags.
- CORE делает controlled exact deduplication, dimensions, facts, derived features и validated distance enrichment.
- MARTS агрегируют преимущественно train-популяцию; row-based объёмы используют `COUNT(*)`, weighted-объёмы — `SUM(cnt)`.
- `date_time` — event time; `srch_ci`/`srch_co` — даты запрошенного проживания, их нельзя смешивать.
- `posa_continent`, location, hotel и destination IDs — encoded IDs; реальные географические названия из них не выводятся.

## Обработки по слоям

### RAW

**Назначение:** Immutable source-aligned views over Expedia train, test and destinations data.

**Обработка:** No business cleaning, deduplication, imputation or aggregation. Source semantics are preserved.

**Материализация:** `data/parquet/ and source CSV files; catalog views in analytics.duckdb`

### STAGING

**Назначение:** Source-grain technical normalization and data-quality metadata.

**Обработка:** Type/date normalization, source metadata, duplicate metadata, missing-distance and quality flags; no destructive filtering or business aggregation.

**Материализация:** `data/derived/staging/*.parquet`

### CORE

**Назначение:** Business entities, facts, deterministic derived features and validated distance enrichment.

**Обработка:** Controlled exact deduplication, dimensions, event/booking facts, date and search features, validity flags, and median distance imputation with provenance.

**Материализация:** `data/derived/core/*.parquet`

### MARTS

**Назначение:** Business-ready analytical aggregates for product, session, travel, channel, destination and retention analysis.

**Обработка:** Train-only behavioral aggregation where applicable; row-based and cnt-weighted measures are kept explicitly named.

**Материализация:** `data/derived/marts/*.parquet`

## Lineage

| Откуда | Куда | Обработка |
|---|---|---|
| `raw.train` | `staging.interaction` | type/date normalization + quality flags |
| `raw.test` | `staging.interaction` | same source-grain interaction contract |
| `raw.destinations` | `staging.destinations` | source metadata + column rename |
| `staging.interaction` | `core.fct_event` | deduplicate + keys + derived features |
| `staging.destinations` | `core.dim_destination` | destination dimension + d1…d149 |
| `core.fct_event` | `core.fct_booking` | filter train bookings |
| `core.fct_event` | `core.dim_user` | distinct user IDs |
| `core.fct_event` | `core.dim_user_location` | observed location combinations |
| `core.fct_event` | `core.dim_platform` | site_name × posa_continent |
| `core.fct_event` | `core.dim_destination_type` | distinct type IDs |
| `core.fct_event` | `core.dim_hotel_market` | market attribute combinations |
| `core.fct_event` | `core.dim_hotel_cluster` | distinct cluster IDs |
| `core.fct_event` | `core.dim_search_params` | distinct search feature combinations |
| `core.fct_event` | `core.dim_date` | event/check-in/check-out date roles |
| `core.fct_event` | `core.dim_hour` | event hour role |
| `core.fct_event` | `core.ref_distance_stats` | validated median estimators |
| `core.fct_event` | `core.event_session_map` | gap_30m_v1 session assignment |
| `core.event_session_map` | `core.fct_session` | session aggregation |
| `core.fct_event` | `marts.mart_product_daily` | business aggregation |
| `core.fct_session` | `marts.mart_session_daily` | business aggregation |
| `core.fct_event` | `marts.mart_travel_calendar_daily` | business aggregation |
| `core.fct_event` | `marts.mart_channel_platform` | business aggregation |
| `core.fct_event` | `marts.mart_destination_performance` | business aggregation |
| `core.fct_event` | `marts.mart_user_360` | business aggregation |
| `core.fct_event` | `marts.mart_origin_destination` | business aggregation |
| `core.fct_event` | `marts.mart_trip_profile` | business aggregation |
| `core.fct_session` | `marts.mart_retention_cohort` | business aggregation |
| `core.fct_session` | `marts.mart_booking_frequency` | business aggregation |
| `core.fct_event` | `marts.mart_data_quality_daily` | business aggregation |
| `core.fct_event` | `marts.mart_distance_quality` | business aggregation |

## Таблицы и поля

### RAW

#### `raw.destinations`

Source latent destination features.

**Зерно:** one destination ID with latent d1…d149 features.

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `srch_destination_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `d1` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d2` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d3` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d4` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d5` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d6` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d7` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d8` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d9` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d10` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d11` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d12` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d13` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d14` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d15` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d16` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d17` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d18` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d19` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d20` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d21` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d22` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d23` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d24` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d25` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d26` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d27` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d28` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d29` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d30` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d31` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d32` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d33` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d34` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d35` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d36` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d37` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d38` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d39` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d40` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d41` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d42` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d43` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d44` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d45` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d46` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d47` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d48` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d49` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d50` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d51` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d52` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d53` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d54` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d55` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d56` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d57` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d58` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d59` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d60` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d61` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d62` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d63` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d64` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d65` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d66` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d67` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d68` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d69` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d70` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d71` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d72` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d73` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d74` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d75` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d76` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d77` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d78` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d79` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d80` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d81` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d82` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d83` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d84` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d85` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d86` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d87` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d88` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d89` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d90` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d91` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d92` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d93` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d94` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d95` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d96` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d97` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d98` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d99` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d100` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d101` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d102` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d103` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d104` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d105` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d106` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d107` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d108` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d109` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d110` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d111` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d112` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d113` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d114` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d115` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d116` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d117` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d118` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d119` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d120` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d121` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d122` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d123` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d124` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d125` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d126` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d127` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d128` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d129` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d130` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d131` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d132` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d133` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d134` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d135` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d136` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d137` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d138` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d139` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d140` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d141` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d142` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d143` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d144` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d145` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d146` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d147` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d148` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d149` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |

#### `raw.test`

Source test interaction log.

**Зерно:** one source test log row; no booking outcome fields.

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `id` | `BIGINT` | да | Field in the raw.test object; physical type BIGINT. |
| `date_time` | `TIMESTAMP` | да | Source event timestamp; distinct from requested check-in and check-out dates. |
| `site_name` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `posa_continent` | `BIGINT` | да | Encoded point-of-sale continent associated with site_name, not necessarily user geography. |
| `user_location_country` | `BIGINT` | да | Field in the raw.test object; physical type BIGINT. |
| `user_location_region` | `BIGINT` | да | Field in the raw.test object; physical type BIGINT. |
| `user_location_city` | `BIGINT` | да | Field in the raw.test object; physical type BIGINT. |
| `orig_destination_distance` | `DOUBLE` | да | Source physical distance from user origin to destination when available. |
| `user_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `is_mobile` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `is_package` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `channel` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `srch_ci` | `VARCHAR` | да | Source requested check-in date; source-aligned value may be text. |
| `srch_co` | `DATE` | да | Source requested check-out date; source-aligned value may be text/date. |
| `srch_adults_cnt` | `BIGINT` | да | Field in the raw.test object; physical type BIGINT. |
| `srch_children_cnt` | `BIGINT` | да | Field in the raw.test object; physical type BIGINT. |
| `srch_rm_cnt` | `BIGINT` | да | Field in the raw.test object; physical type BIGINT. |
| `srch_destination_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `srch_destination_type_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `hotel_continent` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_country` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_market` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |

#### `raw.train`

Source train interaction log.

**Зерно:** one source train log row; train-only booking fields are present.

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `date_time` | `VARCHAR` | да | Source event timestamp; distinct from requested check-in and check-out dates. |
| `site_name` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `posa_continent` | `BIGINT` | да | Encoded point-of-sale continent associated with site_name, not necessarily user geography. |
| `user_location_country` | `BIGINT` | да | Field in the raw.train object; physical type BIGINT. |
| `user_location_region` | `BIGINT` | да | Field in the raw.train object; physical type BIGINT. |
| `user_location_city` | `BIGINT` | да | Field in the raw.train object; physical type BIGINT. |
| `orig_destination_distance` | `DOUBLE` | да | Source physical distance from user origin to destination when available. |
| `user_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `is_mobile` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `is_package` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `channel` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `srch_ci` | `VARCHAR` | да | Source requested check-in date; source-aligned value may be text. |
| `srch_co` | `VARCHAR` | да | Source requested check-out date; source-aligned value may be text/date. |
| `srch_adults_cnt` | `BIGINT` | да | Field in the raw.train object; physical type BIGINT. |
| `srch_children_cnt` | `BIGINT` | да | Field in the raw.train object; physical type BIGINT. |
| `srch_rm_cnt` | `BIGINT` | да | Field in the raw.train object; physical type BIGINT. |
| `srch_destination_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `srch_destination_type_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `is_booking` | `BIGINT` | да | Train outcome flag: 1 means booking, 0 means click/non-booking interaction. |
| `cnt` | `BIGINT` | да | Multiplicity of similar events represented by the source log row; not a session ID. |
| `hotel_continent` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_country` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_market` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_cluster` | `BIGINT` | да | Field in the raw.train object; physical type BIGINT. |

### STAGING

#### `staging.destinations`

Normalized destinations reference.

**Зерно:** one source destination row.
**Parquet:** `data/derived/staging/destinations.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `destination_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `source_dataset` | `VARCHAR` | да | Source population label, such as train, test or destinations. |
| `source_file` | `VARCHAR` | да | Field in the staging.destinations object; physical type VARCHAR. |
| `source_row_id` | `BIGINT` | да | Deterministic source row identifier used for lineage and duplicate selection. |
| `loaded_at` | `TIMESTAMP` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |
| `d1` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d2` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d3` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d4` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d5` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d6` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d7` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d8` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d9` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d10` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d11` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d12` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d13` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d14` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d15` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d16` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d17` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d18` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d19` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d20` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d21` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d22` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d23` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d24` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d25` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d26` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d27` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d28` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d29` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d30` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d31` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d32` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d33` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d34` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d35` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d36` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d37` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d38` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d39` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d40` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d41` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d42` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d43` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d44` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d45` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d46` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d47` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d48` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d49` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d50` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d51` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d52` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d53` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d54` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d55` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d56` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d57` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d58` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d59` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d60` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d61` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d62` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d63` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d64` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d65` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d66` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d67` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d68` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d69` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d70` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d71` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d72` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d73` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d74` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d75` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d76` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d77` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d78` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d79` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d80` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d81` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d82` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d83` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d84` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d85` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d86` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d87` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d88` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d89` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d90` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d91` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d92` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d93` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d94` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d95` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d96` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d97` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d98` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d99` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d100` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d101` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d102` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d103` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d104` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d105` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d106` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d107` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d108` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d109` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d110` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d111` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d112` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d113` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d114` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d115` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d116` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d117` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d118` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d119` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d120` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d121` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d122` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d123` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d124` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d125` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d126` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d127` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d128` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d129` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d130` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d131` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d132` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d133` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d134` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d135` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d136` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d137` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d138` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d139` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d140` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d141` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d142` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d143` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d144` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d145` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d146` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d147` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d148` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d149` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |

#### `staging.interaction`

Normalized interaction stream.

**Зерно:** one source interaction row, preserving source grain.
**Parquet:** `data/derived/staging/interaction.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `source_dataset` | `VARCHAR` | да | Source population label, such as train, test or destinations. |
| `source_file` | `VARCHAR` | да | Field in the staging.interaction object; physical type VARCHAR. |
| `source_row_id` | `BIGINT` | да | Deterministic source row identifier used for lineage and duplicate selection. |
| `source_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `date_time` | `TIMESTAMP` | да | Source event timestamp; distinct from requested check-in and check-out dates. |
| `raw_srch_ci` | `VARCHAR` | да | Field in the staging.interaction object; physical type VARCHAR. |
| `raw_srch_co` | `VARCHAR` | да | Field in the staging.interaction object; physical type VARCHAR. |
| `site_name` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `posa_continent` | `BIGINT` | да | Encoded point-of-sale continent associated with site_name, not necessarily user geography. |
| `user_location_country` | `BIGINT` | да | Field in the staging.interaction object; physical type BIGINT. |
| `user_location_region` | `BIGINT` | да | Field in the staging.interaction object; physical type BIGINT. |
| `user_location_city` | `BIGINT` | да | Field in the staging.interaction object; physical type BIGINT. |
| `orig_destination_distance` | `DOUBLE` | да | Source physical distance from user origin to destination when available. |
| `user_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `is_mobile` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `is_package` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `channel` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `srch_adults_cnt` | `BIGINT` | да | Field in the staging.interaction object; physical type BIGINT. |
| `srch_children_cnt` | `BIGINT` | да | Field in the staging.interaction object; physical type BIGINT. |
| `srch_rm_cnt` | `BIGINT` | да | Field in the staging.interaction object; physical type BIGINT. |
| `srch_destination_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `srch_destination_type_id` | `BIGINT` | да | Encoded source identifier; no real-world name is inferred from this value. |
| `is_booking` | `BIGINT` | да | Train outcome flag: 1 means booking, 0 means click/non-booking interaction. |
| `cnt` | `BIGINT` | да | Multiplicity of similar events represented by the source log row; not a session ID. |
| `hotel_continent` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_country` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_market` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_cluster` | `BIGINT` | да | Field in the staging.interaction object; physical type BIGINT. |
| `event_ts` | `TIMESTAMP` | да | Normalized event timestamp derived from date_time. |
| `checkin_date` | `DATE` | да | Normalized requested check-in date. |
| `checkout_date` | `DATE` | да | Normalized requested check-out date. |
| `duplicate_rank` | `BIGINT` | да | Field in the staging.interaction object; physical type BIGINT. |
| `duplicate_group_size` | `BIGINT` | да | Field in the staging.interaction object; physical type BIGINT. |
| `distance_is_missing` | `BOOLEAN` | да | Field in the staging.interaction object; physical type BOOLEAN. |
| `q_missing_checkin` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `q_missing_checkout` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `q_checkin_before_event` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `q_checkout_before_checkin` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `q_same_day_stay` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `q_zero_adults` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `q_zero_rooms` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `q_zero_travelers` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `q_extreme_future_date` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `q_exact_duplicate` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `loaded_at` | `TIMESTAMP` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |
| `quality_issue_count` | `BIGINT` | да | Count of quality flags raised for the row. |

### CORE

#### `core.dim_date`

Calendar dimension.

**Зерно:** one row per valid calendar day.
**Parquet:** `data/derived/core/dim_date.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `full_date` | `DATE` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |
| `year` | `INTEGER` | да | Calendar or clock attribute. |
| `quarter` | `INTEGER` | да | Calendar or clock attribute. |
| `year_quarter` | `VARCHAR` | да | Field in the core.dim_date object; physical type VARCHAR. |
| `month` | `INTEGER` | да | Calendar or clock attribute. |
| `month_name` | `VARCHAR` | да | Field in the core.dim_date object; physical type VARCHAR. |
| `year_month` | `VARCHAR` | да | Field in the core.dim_date object; physical type VARCHAR. |
| `iso_week` | `INTEGER` | да | Calendar or clock attribute. |
| `day_of_month` | `INTEGER` | да | Calendar or clock attribute. |
| `day_of_year` | `INTEGER` | да | Calendar or clock attribute. |
| `day_of_week` | `INTEGER` | да | Calendar or clock attribute. |
| `day_name` | `VARCHAR` | да | Field in the core.dim_date object; physical type VARCHAR. |
| `is_weekend` | `BOOLEAN` | да | Boolean or encoded indicator retained for segmentation. |
| `season` | `VARCHAR` | да | Field in the core.dim_date object; physical type VARCHAR. |

#### `core.dim_destination`

Destination dimension.

**Зерно:** one row per destination ID, with latent features when available.
**Parquet:** `data/derived/core/dim_destination.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `destination_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `destination_type_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `d1` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d2` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d3` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d4` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d5` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d6` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d7` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d8` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d9` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d10` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d11` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d12` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d13` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d14` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d15` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d16` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d17` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d18` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d19` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d20` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d21` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d22` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d23` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d24` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d25` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d26` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d27` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d28` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d29` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d30` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d31` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d32` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d33` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d34` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d35` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d36` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d37` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d38` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d39` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d40` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d41` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d42` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d43` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d44` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d45` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d46` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d47` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d48` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d49` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d50` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d51` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d52` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d53` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d54` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d55` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d56` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d57` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d58` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d59` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d60` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d61` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d62` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d63` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d64` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d65` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d66` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d67` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d68` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d69` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d70` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d71` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d72` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d73` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d74` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d75` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d76` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d77` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d78` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d79` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d80` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d81` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d82` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d83` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d84` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d85` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d86` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d87` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d88` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d89` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d90` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d91` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d92` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d93` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d94` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d95` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d96` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d97` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d98` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d99` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d100` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d101` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d102` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d103` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d104` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d105` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d106` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d107` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d108` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d109` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d110` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d111` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d112` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d113` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d114` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d115` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d116` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d117` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d118` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d119` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d120` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d121` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d122` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d123` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d124` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d125` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d126` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d127` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d128` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d129` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d130` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d131` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d132` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d133` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d134` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d135` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d136` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d137` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d138` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d139` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d140` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d141` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d142` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d143` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d144` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d145` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d146` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d147` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d148` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |
| `d149` | `DOUBLE` | да | Latent destination/search-region feature; encoded numeric signal, not human-readable geography. |

#### `core.dim_destination_type`

Destination type dimension.

**Зерно:** one row per destination type ID.
**Parquet:** `data/derived/core/dim_destination_type.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `destination_type_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |

#### `core.dim_hotel_cluster`

Hotel cluster dimension.

**Зерно:** one row per hotel cluster ID.
**Parquet:** `data/derived/core/dim_hotel_cluster.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `hotel_cluster_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |

#### `core.dim_hotel_market`

Hotel market dimension.

**Зерно:** one row per observed market × country × continent combination.
**Parquet:** `data/derived/core/dim_hotel_market.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `hotel_market_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `hotel_continent` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_country` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_market` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |

#### `core.dim_hour`

Hour-of-day dimension.

**Зерно:** one row per hour of day.
**Parquet:** `data/derived/core/dim_hour.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `hour_key` | `BIGINT` | да | Integer key for the hour-of-day dimension. |
| `hour` | `INTEGER` | да | Calendar or clock attribute. |
| `daypart` | `VARCHAR` | да | Field in the core.dim_hour object; physical type VARCHAR. |

#### `core.dim_platform`

Point-of-sale platform dimension.

**Зерно:** one row per site_name × posa_continent combination.
**Parquet:** `data/derived/core/dim_platform.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `platform_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `site_name` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `posa_continent` | `BIGINT` | да | Encoded point-of-sale continent associated with site_name, not necessarily user geography. |

#### `core.dim_search_params`

Search parameters dimension.

**Зерно:** one row per adults × children × rooms × stay/party feature combination.
**Parquet:** `data/derived/core/dim_search_params.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `search_params_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `adults_cnt` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `children_cnt` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `room_cnt` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `stay_nights` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `party_size` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `has_children` | `BOOLEAN` | да | Boolean or encoded indicator retained for segmentation. |

#### `core.dim_user`

User dimension.

**Зерно:** one row per observed user.
**Parquet:** `data/derived/core/dim_user.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `user_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |

#### `core.dim_user_location`

Observed user location dimension.

**Зерно:** one row per observed country/region/city combination.
**Parquet:** `data/derived/core/dim_user_location.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `user_location_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `user_country` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `user_region` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `user_city` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |

#### `core.event_session_map`

Event-to-session bridge.

**Зерно:** one eligible train event assigned to one session-rule version.
**Parquet:** `data/derived/core/event_session_map.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `event_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `session_id` | `VARCHAR` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `session_rule_version` | `VARCHAR` | да | Field in the core.event_session_map object; physical type VARCHAR. |

#### `core.fct_booking`

Booking fact.

**Зерно:** one train booking log event, filtered to is_booking = 1.
**Parquet:** `data/derived/core/fct_booking.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `booking_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `event_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `user_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `user_location_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `platform_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `destination_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `hotel_market_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `hotel_cluster_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `event_date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `checkin_date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `checkout_date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `is_package` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `lead_days` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `stay_nights` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `distance_filled` | `DOUBLE` | да | Distance used for analysis: source distance or validated CORE estimate. |
| `booking_value_proxy` | `BIGINT` | да | Relative package/value proxy: 0 non-booking, 1 hotel-only booking, 2 package booking; not revenue. |

#### `core.fct_event`

Deduplicated event fact.

**Зерно:** one unique aggregated source log row after controlled exact deduplication.
**Parquet:** `data/derived/core/fct_event.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `event_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `source_row_id` | `BIGINT` | да | Deterministic source row identifier used for lineage and duplicate selection. |
| `source_dataset` | `VARCHAR` | да | Source population label, such as train, test or destinations. |
| `event_ts` | `TIMESTAMP` | да | Normalized event timestamp derived from date_time. |
| `event_date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `event_hour_key` | `BIGINT` | да | Integer key for the hour-of-day dimension. |
| `checkin_date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `checkout_date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `user_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `user_location_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `platform_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `destination_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `hotel_market_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `hotel_cluster_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `search_params_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `channel` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `is_mobile` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `is_package` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `is_booking` | `BIGINT` | да | Train outcome flag: 1 means booking, 0 means click/non-booking interaction. |
| `cnt` | `BIGINT` | да | Multiplicity of similar events represented by the source log row; not a session ID. |
| `lead_days` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `stay_nights` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `party_size` | `BIGINT` | да | Derived or requested trip/search characteristic. |
| `has_children` | `BOOLEAN` | да | Boolean or encoded indicator retained for segmentation. |
| `booking_value_proxy` | `BIGINT` | да | Relative package/value proxy: 0 non-booking, 1 hotel-only booking, 2 package booking; not revenue. |
| `distance_raw` | `DOUBLE` | да | Immutable source distance before any enrichment. |
| `distance_filled` | `DOUBLE` | да | Distance used for analysis: source distance or validated CORE estimate. |
| `distance_was_missing` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `distance_is_imputed` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `distance_imputation_level` | `VARCHAR` | да | Hierarchy level used to fill a missing distance, if any. |
| `distance_imputation_support` | `BIGINT` | да | Field in the core.fct_event object; physical type BIGINT. |
| `distance_imputation_mae` | `DOUBLE` | да | Field in the core.fct_event object; physical type DOUBLE. |
| `valid_for_lead_time` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `valid_for_stay_length` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `valid_for_party_metrics` | `BOOLEAN` | да | Boolean data-quality or metric-validity flag produced by the pipeline. |
| `quality_issue_count` | `BIGINT` | да | Count of quality flags raised for the row. |

#### `core.fct_session`

Reconstructed session fact.

**Зерно:** one reconstructed user session under gap_30m_v1.
**Parquet:** `data/derived/core/fct_session.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `session_id` | `VARCHAR` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `session_rule_version` | `VARCHAR` | да | Field in the core.fct_session object; physical type VARCHAR. |
| `user_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `source_dataset` | `VARCHAR` | да | Source population label, such as train, test or destinations. |
| `session_start_ts` | `TIMESTAMP` | да | Field in the core.fct_session object; physical type TIMESTAMP. |
| `session_end_ts` | `TIMESTAMP` | да | Field in the core.fct_session object; physical type TIMESTAMP. |
| `session_date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `session_start_hour_key` | `BIGINT` | да | Integer key for the hour-of-day dimension. |
| `session_duration_seconds` | `BIGINT` | да | Field in the core.fct_session object; physical type BIGINT. |
| `row_count` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `weighted_event_count` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `distinct_destination_count` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `distinct_hotel_market_count` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `distinct_search_params_count` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `has_booking` | `BOOLEAN` | да | Field in the core.fct_session object; physical type BOOLEAN. |
| `booking_row_count` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `first_booking_ts` | `TIMESTAMP` | да | Field in the core.fct_session object; physical type TIMESTAMP. |
| `time_to_first_booking_seconds` | `BIGINT` | да | Field in the core.fct_session object; physical type BIGINT. |
| `booking_value_proxy_total` | `BIGINT` | да | Field in the core.fct_session object; physical type BIGINT. |
| `package_booking_count` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `first_channel` | `BIGINT` | да | Field in the core.fct_session object; physical type BIGINT. |
| `last_channel` | `BIGINT` | да | Field in the core.fct_session object; physical type BIGINT. |
| `first_platform_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `last_platform_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `first_destination_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `last_destination_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `first_is_mobile` | `BIGINT` | да | Field in the core.fct_session object; physical type BIGINT. |
| `last_is_mobile` | `BIGINT` | да | Field in the core.fct_session object; physical type BIGINT. |

#### `core.ref_distance_stats`

Distance estimator reference.

**Зерно:** one median estimator per imputation hierarchy group.
**Parquet:** `data/derived/core/ref_distance_stats.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `imputation_level` | `VARCHAR` | да | Field in the core.ref_distance_stats object; physical type VARCHAR. |
| `origin_city` | `BIGINT` | да | Field in the core.ref_distance_stats object; physical type BIGINT. |
| `origin_region` | `BIGINT` | да | Field in the core.ref_distance_stats object; physical type BIGINT. |
| `origin_country` | `BIGINT` | да | Field in the core.ref_distance_stats object; physical type BIGINT. |
| `destination_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `hotel_market` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_country` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `median_distance` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `observations` | `BIGINT` | да | Field in the core.ref_distance_stats object; physical type BIGINT. |
| `minimum_support` | `BIGINT` | да | Field in the core.ref_distance_stats object; physical type BIGINT. |
| `validation_coverage_pct` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `validation_mae` | `DOUBLE` | да | Field in the core.ref_distance_stats object; physical type DOUBLE. |
| `validation_median_absolute_error` | `DOUBLE` | да | Field in the core.ref_distance_stats object; physical type DOUBLE. |
| `validation_p90_absolute_error` | `DOUBLE` | да | Field in the core.ref_distance_stats object; physical type DOUBLE. |

### MARTS

#### `marts.mart_booking_frequency`

Booking frequency mart.

**Зерно:** one booking-count bucket.
**Parquet:** `data/derived/marts/mart_booking_frequency.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `booking_count_bucket` | `VARCHAR` | да | Field in the marts.mart_booking_frequency object; physical type VARCHAR. |
| `booking_count_bucket_order` | `INTEGER` | да | Field in the marts.mart_booking_frequency object; physical type INTEGER. |
| `users` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `user_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `avg_sessions` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_active_months` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_booking_value_proxy` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_package_booking_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |

#### `marts.mart_channel_platform`

Channel/platform performance mart.

**Зерно:** one month × channel × platform × mobile flag.
**Parquet:** `data/derived/marts/mart_channel_platform.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `year_month` | `VARCHAR` | да | Field in the marts.mart_channel_platform object; physical type VARCHAR. |
| `channel` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `platform_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `is_mobile` | `BIGINT` | да | Boolean or encoded indicator retained for segmentation. |
| `active_users` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `row_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `weighted_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `bookings` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `booking_row_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_weighted_event_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_value_proxy_total` | `BIGINT` | да | Field in the marts.mart_channel_platform object; physical type BIGINT. |
| `booking_value_proxy_per_active_user` | `DOUBLE` | да | Field in the marts.mart_channel_platform object; physical type DOUBLE. |
| `package_booking_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `avg_valid_lead_days` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_valid_stay_nights` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |

#### `marts.mart_data_quality_daily`

Daily data-quality mart.

**Зерно:** one event date.
**Parquet:** `data/derived/marts/mart_data_quality_daily.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `rows` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `weighted_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `missing_distance_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `imputed_distance_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `invalid_lead_time_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `invalid_stay_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `zero_party_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `quality_issue_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |

#### `marts.mart_destination_performance`

Destination performance mart.

**Зерно:** one month × destination × hotel market.
**Parquet:** `data/derived/marts/mart_destination_performance.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `year_month` | `VARCHAR` | да | Field in the marts.mart_destination_performance object; physical type VARCHAR. |
| `destination_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `hotel_market_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `active_users` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `row_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `weighted_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `bookings` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `bookers` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `booking_row_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_weighted_event_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `package_booking_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_value_proxy_total` | `BIGINT` | да | Field in the marts.mart_destination_performance object; physical type BIGINT. |
| `avg_distance_filled` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_valid_lead_days` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_valid_stay_nights` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `meets_min_volume_flag` | `BOOLEAN` | да | Boolean or encoded indicator retained for segmentation. |
| `meets_booking_min_volume_flag` | `BOOLEAN` | да | Boolean or encoded indicator retained for segmentation. |

#### `marts.mart_distance_quality`

Distance quality mart.

**Зерно:** one imputation level × support threshold.
**Parquet:** `data/derived/marts/mart_distance_quality.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `imputation_level` | `VARCHAR` | да | Field in the marts.mart_distance_quality object; physical type VARCHAR. |
| `min_support` | `INTEGER` | да | Field in the marts.mart_distance_quality object; physical type INTEGER. |
| `holdout_rows` | `BIGINT` | да | Field in the marts.mart_distance_quality object; physical type BIGINT. |
| `covered_rows` | `BIGINT` | да | Field in the marts.mart_distance_quality object; physical type BIGINT. |
| `coverage_pct` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `mae` | `DOUBLE` | да | Field in the marts.mart_distance_quality object; physical type DOUBLE. |
| `median_absolute_error` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `p90_absolute_error` | `DOUBLE` | да | Field in the marts.mart_distance_quality object; physical type DOUBLE. |
| `average_support` | `DOUBLE` | да | Field in the marts.mart_distance_quality object; physical type DOUBLE. |

#### `marts.mart_origin_destination`

Origin-destination mart.

**Зерно:** one month × user country × hotel country.
**Parquet:** `data/derived/marts/mart_origin_destination.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `year_month` | `VARCHAR` | да | Field in the marts.mart_origin_destination object; physical type VARCHAR. |
| `user_country` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `hotel_country` | `BIGINT` | да | Encoded categorical identifier; treat as an ID rather than a real-world label. |
| `active_users` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `row_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `weighted_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `bookings` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `booking_row_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_value_proxy_total` | `BIGINT` | да | Field in the marts.mart_origin_destination object; physical type BIGINT. |
| `avg_distance_filled` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `package_booking_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `avg_valid_stay_nights` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_valid_lead_days` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |

#### `marts.mart_product_daily`

Daily product KPI mart.

**Зерно:** one event date.
**Parquet:** `data/derived/marts/mart_product_daily.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `active_users` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `row_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `weighted_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `bookings` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `bookers` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `booking_row_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_weighted_event_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booker_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_value_proxy_total` | `BIGINT` | да | Field in the marts.mart_product_daily object; physical type BIGINT. |
| `booking_value_proxy_per_active_user` | `DOUBLE` | да | Field in the marts.mart_product_daily object; physical type DOUBLE. |
| `avg_booking_value_proxy_per_booking` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `mobile_row_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `mobile_booking_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `package_booking_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `avg_valid_lead_days` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_valid_stay_nights` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_distance_filled` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `distance_imputed_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |

#### `marts.mart_retention_cohort`

Booking retention mart.

**Зерно:** one first-booking month × months since first booking.
**Parquet:** `data/derived/marts/mart_retention_cohort.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `cohort_month` | `DATE` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |
| `months_since_first_booking` | `BIGINT` | да | Field in the marts.mart_retention_cohort object; physical type BIGINT. |
| `cohort_users` | `BIGINT` | да | Field in the marts.mart_retention_cohort object; physical type BIGINT. |
| `returned_bookers` | `BIGINT` | да | Field in the marts.mart_retention_cohort object; physical type BIGINT. |
| `booking_retention_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `bookings` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `booking_value_proxy_total` | `BIGINT` | да | Field in the marts.mart_retention_cohort object; physical type BIGINT. |

#### `marts.mart_session_daily`

Daily session KPI mart.

**Зерно:** one session start date.
**Parquet:** `data/derived/marts/mart_session_daily.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `active_users` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `sessions` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `booking_sessions` | `BIGINT` | да | Field in the marts.mart_session_daily object; physical type BIGINT. |
| `session_booking_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `sessions_per_user` | `DOUBLE` | да | Field in the marts.mart_session_daily object; physical type DOUBLE. |
| `avg_rows_per_session` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_weighted_events_per_session` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `median_session_duration_seconds` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_time_to_first_booking_seconds` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `multi_destination_session_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_value_proxy_total` | `BIGINT` | да | Field in the marts.mart_session_daily object; physical type BIGINT. |
| `booking_value_proxy_per_session` | `DOUBLE` | да | Field in the marts.mart_session_daily object; physical type DOUBLE. |

#### `marts.mart_travel_calendar_daily`

Travel calendar mart.

**Зерно:** one calendar date, combining event and stay-date roles.
**Parquet:** `data/derived/marts/mart_travel_calendar_daily.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `date_key` | `BIGINT` | да | Integer YYYYMMDD key for a calendar-date role. |
| `full_date` | `DATE` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |
| `year` | `INTEGER` | да | Calendar or clock attribute. |
| `month` | `INTEGER` | да | Calendar or clock attribute. |
| `year_month` | `VARCHAR` | да | Field in the marts.mart_travel_calendar_daily object; physical type VARCHAR. |
| `events_on_date` | `BIGINT` | да | Field in the marts.mart_travel_calendar_daily object; physical type BIGINT. |
| `weighted_events_on_date` | `BIGINT` | да | Field in the marts.mart_travel_calendar_daily object; physical type BIGINT. |
| `bookings_made_on_date` | `BIGINT` | да | Field in the marts.mart_travel_calendar_daily object; physical type BIGINT. |
| `checkins_on_date` | `BIGINT` | да | Field in the marts.mart_travel_calendar_daily object; physical type BIGINT. |
| `checkouts_on_date` | `BIGINT` | да | Field in the marts.mart_travel_calendar_daily object; physical type BIGINT. |
| `booking_value_proxy_for_checkins` | `BIGINT` | да | Field in the marts.mart_travel_calendar_daily object; physical type BIGINT. |
| `package_checkins` | `BIGINT` | да | Field in the marts.mart_travel_calendar_daily object; physical type BIGINT. |
| `avg_stay_nights_for_checkins` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_lead_days_for_checkins` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |

#### `marts.mart_trip_profile`

Trip profile mart.

**Зерно:** one month × lead bucket × stay bucket × party segment.
**Parquet:** `data/derived/marts/mart_trip_profile.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `year_month` | `VARCHAR` | да | Field in the marts.mart_trip_profile object; physical type VARCHAR. |
| `lead_time_bucket` | `VARCHAR` | да | Derived or requested trip/search characteristic. |
| `stay_length_bucket` | `VARCHAR` | да | Derived or requested trip/search characteristic. |
| `party_segment` | `VARCHAR` | да | Field in the marts.mart_trip_profile object; physical type VARCHAR. |
| `users` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `weighted_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `bookings` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `booking_row_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_weighted_event_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `package_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `mobile_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `booking_value_proxy_total` | `BIGINT` | да | Field in the marts.mart_trip_profile object; physical type BIGINT. |
| `sessions` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `booking_sessions` | `BIGINT` | да | Field in the marts.mart_trip_profile object; physical type BIGINT. |
| `session_booking_rate` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |

#### `marts.mart_user_360`

User 360 mart.

**Зерно:** one user.
**Parquet:** `data/derived/marts/mart_user_360.parquet`

| Поле | Тип | Nullable | Описание |
|---|---|:---:|---|
| `user_id` | `BIGINT` | да | Surrogate or encoded identifier used to join this entity in the analytical model. |
| `first_seen_date` | `DATE` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |
| `last_seen_date` | `DATE` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |
| `active_days` | `BIGINT` | да | Field in the marts.mart_user_360 object; physical type BIGINT. |
| `active_months` | `BIGINT` | да | Field in the marts.mart_user_360 object; physical type BIGINT. |
| `row_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `weighted_events` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `bookings` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `first_booking_date` | `DATE` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |
| `last_booking_date` | `DATE` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |
| `booking_value_proxy_total` | `BIGINT` | да | Field in the marts.mart_user_360 object; physical type BIGINT. |
| `avg_booking_value_proxy` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `package_bookings` | `BIGINT` | да | Field in the marts.mart_user_360 object; physical type BIGINT. |
| `package_booking_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `mobile_event_share` | `DOUBLE` | да | Ratio metric; numerator and denominator are defined by the mart build logic. |
| `distinct_destinations` | `BIGINT` | да | Field in the marts.mart_user_360 object; physical type BIGINT. |
| `distinct_hotel_markets` | `BIGINT` | да | Field in the marts.mart_user_360 object; physical type BIGINT. |
| `avg_valid_lead_days` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_valid_stay_nights` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `avg_distance_filled` | `DOUBLE` | да | Aggregated average or median measure at the table grain. |
| `sessions` | `BIGINT` | да | Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named. |
| `booking_sessions` | `BIGINT` | да | Field in the marts.mart_user_360 object; physical type BIGINT. |
| `days_since_last_booking` | `BIGINT` | да | Field in the marts.mart_user_360 object; physical type BIGINT. |
| `booking_frequency` | `DOUBLE` | да | Field in the marts.mart_user_360 object; physical type DOUBLE. |
| `session_frequency` | `DOUBLE` | да | Field in the marts.mart_user_360 object; physical type DOUBLE. |
| `observation_end_date` | `DATE` | да | Date or timestamp used for lineage, cohorting or calendar analysis. |

## HTML-диаграмма

Интерактивная версия: [`data_flow.html`](data_flow.html). Нажмите на таблицу, чтобы раскрыть поля; наведите курсор на поле, чтобы увидеть описание.
