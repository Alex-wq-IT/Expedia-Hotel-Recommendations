# Expedia Analytics DWH Contract

**Status:** Draft v1
**Scope:** RAW → STAGING → CORE
**Out of scope:** MARTS, dashboard, final sessionization, predictive ML

---

# 1. Purpose

Этот документ является главным архитектурным контрактом для локального DWH Expedia Hotel Recommendations.

Его задача — однозначно определить:

* слои DWH;
* grain таблиц;
* бизнес-сущности;
* правила обработки данных;
* структуру CORE;
* правила работы с датами;
* правила восстановления `orig_destination_distance`;
* границы ответственности последующих аналитических слоёв.

Если реализация агента противоречит этому документу, приоритет имеет этот документ.

Агент не должен самостоятельно перепроектировать описанную модель.

---

# 2. Source datasets

Основные источники:

* `train`
* `test`
* `destinations`

Исходные данные являются денормализованными логами Expedia.

Основной train содержит десятки миллионов агрегированных log rows.

Поле `cnt` означает multiplicity похожих событий внутри контекста одной пользовательской сессии.

Следовательно:

* одна строка исходных данных не обязательно соответствует одному физическому пользовательскому действию;
* `COUNT(*)` означает количество aggregated log rows;
* `SUM(cnt)` является отдельной мерой объёма активности;
* `cnt` не является `session_id`.

Известные проблемы данных:

* большое количество NULL в `orig_destination_distance`;
* логически некорректные даты;
* missing check-in/check-out;
* exact duplicates;
* zero-adult searches;
* zero-room searches;
* zero-traveler searches;
* экстремальные даты;
* подозрительные записи иногда заканчиваются booking event.

Эти проблемы не должны приводить к автоматическому удалению строк на STAGING.

---

# 3. Target architecture

Используется архитектура:

```text
SOURCE
   ↓
RAW
   ↓
STAGING
   ↓
CORE
   ↓
MARTS
   ↓
BI / Product Analytics
```

На текущем этапе реализуются только:

```text
RAW → STAGING → CORE
```

MARTS проектируются отдельным этапом после проверки CORE.

---

# 4. RAW

## Purpose

RAW является immutable source of truth.

## Rules

RAW:

* максимально точно повторяет исходные данные;
* не содержит бизнес-исправлений;
* не содержит imputation;
* не содержит deduplication;
* не содержит нормализации бизнес-сущностей.

Допускаются только технические metadata-поля:

* `source_dataset`;
* `source_file`;
* `source_row_id`;
* `loaded_at`.

Исходные Parquet/CSV никогда не изменяются.

---

# 5. STAGING

## Purpose

STAGING приводит источник к технически пригодному состоянию, сохраняя source grain и source semantics.

## Grain

**Одна строка STAGING = одна строка исходного dataset.**

## STAGING responsibilities

STAGING выполняет:

* type normalization;
* date parsing;
* NULL normalization;
* source metadata;
* data-quality flags.

STAGING не выполняет:

* destructive filtering;
* business aggregation;
* distance imputation;
* sessionization;
* product metrics;
* dimensional modeling.

## Required normalized fields

Минимально:

* `event_ts`;
* `checkin_date`;
* `checkout_date`;
* `distance_is_missing`.

## Required quality flags

Минимально:

* `q_missing_checkin`;
* `q_missing_checkout`;
* `q_checkin_before_event`;
* `q_checkout_before_checkin`;
* `q_same_day_stay`;
* `q_zero_adults`;
* `q_zero_rooms`;
* `q_zero_travelers`;
* `q_extreme_future_date`;
* `q_exact_duplicate`;
* `quality_issue_count`.

Активный допустимый диапазон для `event_ts`, `checkin_date` и
`checkout_date` — от `2013-01-01` до `2016-12-31` включительно. Историческое
имя `q_extreme_future_date` сохраняется для совместимости контракта, но flag
устанавливается для любой присутствующей даты вне этого диапазона. Такие
source rows сохраняются; их невалидные даты не получают CORE date keys и не
участвуют в соответствующих date-derived metrics.

Original source columns должны сохраняться.

---

# 6. CORE

## Purpose

CORE представляет бизнес-модель данных.

Именно здесь:

* выполняется controlled exact deduplication;
* создаются normalized dimensions;
* создаются fact tables;
* рассчитываются deterministic derived features;
* добавляются metric validity flags;
* выполняется validated distance enrichment.

CORE является единственным источником данных для будущих MARTS.

---

# 7. CORE tables

Текущий фиксированный набор:

```text
core.dim_date
core.dim_hour

core.dim_user
core.dim_user_location          -- conditional
core.dim_platform

core.dim_destination
core.dim_destination_type

core.dim_hotel_market
core.dim_hotel_cluster

core.dim_search_params

core.fct_event
core.fct_booking

core.ref_distance_stats
```

Дополнительные dimensions не создаются без явной необходимости.

---

# 8. Date model

## 8.1 `core.dim_date`

Используется одна физическая календарная размерность.

### Grain

**Одна строка = один календарный день.**

### Required fields

```text
date_key
full_date

year
quarter
year_quarter

month
month_name
year_month

iso_week

day_of_month
day_of_year

day_of_week
day_name

is_weekend
season
```

`date_key` рекомендуется хранить в формате integer:

```text
YYYYMMDD
```

Например:

```text
20140716
```

## Role-playing usage

Одна `dim_date` используется в нескольких логических ролях:

```text
fct_event.event_date_key
    → dim_date

fct_event.checkin_date_key
    → dim_date

fct_event.checkout_date_key
    → dim_date
```

Это позволяет независимо анализировать:

* seasonality of Expedia activity/searches;
* seasonality of check-ins;
* seasonality of check-outs.

Не создавать отдельные физические таблицы:

```text
dim_event_date
dim_checkin_date
dim_checkout_date
```

Одна таблица используется как role-playing dimension.

## Calendar range

Calendar должен строиться только по допустимому диапазону валидных дат.

Ошибочные экстремальные даты не должны расширять `dim_date`.

---

# 9. Hour dimension

Создать:

```text
core.dim_hour
```

### Grain

**Одна строка = один час суток.**

Всего 24 строки.

### Fields

```text
hour_key
hour
daypart
```

Пример `daypart`:

```text
00–05 → night
06–11 → morning
12–17 → afternoon
18–23 → evening
```

Связь:

```text
fct_event.event_hour_key
    → dim_hour
```

Check-in/check-out hour отсутствует в источнике, поэтому check-in/check-out с `dim_hour` не связываются.

Не создавать физический `dim_datetime` на каждую секунду.

Original `event_ts` сохраняется в fact.

---

# 10. User dimension

## Preferred model

Если выполняется функциональная зависимость:

```text
user_id
    →
user_location_country
user_location_region
user_location_city
```

создаётся:

```text
core.dim_user
```

с полями:

```text
user_id
user_country
user_region
user_city
```

## If location is unstable

Если один `user_id` встречается с несколькими location combinations:

создать:

```text
core.dim_user
---------
user_id
```

и отдельно:

```text
core.dim_user_location
----------------------
user_location_id
user_country
user_region
user_city
```

В таком случае `user_location_id` связывается непосредственно с event.

Нельзя произвольно выбирать одну location для пользователя.

---

# 11. Platform dimension

Создать:

```text
core.dim_platform
```

### Grain

Одна строка = уникальная platform combination.

Основные атрибуты:

```text
platform_id
site_name
posa_continent
```

Перед materialization проверить mapping между `site_name` и `posa_continent`.

При нестабильном mapping surrogate key строится по фактической комбинации атрибутов.

---

# 12. Destination dimensions

## `core.dim_destination`

Основной ключ:

```text
destination_id
```

Поля:

```text
destination_id
destination_type_id

d1
...
d149
```

Latent destination features сохраняются без PCA.

PCA и другие ML transformations находятся вне scope CORE.

## `core.dim_destination_type`

```text
destination_type_id
```

Это допустимая структурная dimension даже при отсутствии дополнительных descriptive attributes.

---

# 13. Hotel dimensions

В исходном dataset отсутствует ID конкретного отеля.

`hotel_cluster` не является hotel ID.

Поэтому `dim_hotel` не создаётся.

Используются две отдельные сущности.

## `core.dim_hotel_market`

Атрибуты:

```text
hotel_market_id
hotel_continent
hotel_country
hotel_market
```

Перед созданием проверить mapping:

```text
hotel_market
    →
hotel_country
hotel_continent
```

При нестабильном mapping surrogate key формируется по комбинации атрибутов.

## `core.dim_hotel_cluster`

```text
hotel_cluster_id
```

`hotel_cluster` означает группу похожих отелей.

---

# 14. Search parameters dimension

Создать:

```text
core.dim_search_params
```

### Grain

Одна строка = уникальная комбинация параметров поиска.

Поля:

```text
search_params_id

adults_cnt
children_cnt
room_cnt

stay_nights
party_size
has_children
```

Критически важно:

`search_params_id` НЕ является:

* search ID;
* session ID;
* request ID.

Он является только surrogate key для комбинации параметров.

Разные пользователи и разные реальные searches могут иметь одинаковый `search_params_id`.

---

# 15. Deterministic derived features

На CORE рассчитываются:

## `lead_days`

```text
checkin_date - event_date
```

Используется только при валидной temporal ordering.

## `stay_nights`

```text
checkout_date - checkin_date
```

Используется только при валидных stay dates.

## `party_size`

```text
adults_cnt + children_cnt
```

## `has_children`

Boolean flag:

```text
children_cnt > 0
```

---

# 16. Metric validity flags

Подозрительные events сохраняются в CORE.

Для аналитических метрик создаются flags:

```text
valid_for_lead_time
valid_for_stay_length
valid_for_party_metrics
```

Таким образом:

* факт события сохраняется;
* некорректное поле не участвует в соответствующей метрике.

---

# 17. Booking Value Proxy

Используется business-value approximation.

Определение:

```text
non-booking event      → 0
hotel-only booking     → 1
package booking        → 2
```

Поле:

```text
booking_value_proxy
```

Это не реальные деньги и не revenue.

Это относительный proxy ценности booking event.

В дальнейших MARTS он может использоваться для построения:

```text
total booking value proxy
average booking value proxy
booking value proxy per user
LTV proxy
```

---

# 18. `core.fct_event`

## Grain

**Одна строка = одна уникальная aggregated Expedia log row после controlled exact deduplication.**

Это НЕ:

* один физический click;
* один search;
* одна session;
* одна поездка.

`cnt` хранится как отдельная multiplicity исходной aggregated row.

## Required fields

### Technical

```text
event_id
source_row_id
source_dataset
```

### Time

```text
event_ts

event_date_key
event_hour_key

checkin_date_key
checkout_date_key
```

### Dimension foreign keys

```text
user_id
user_location_id        -- conditional

platform_id
destination_id

hotel_market_id
hotel_cluster_id

search_params_id
```

### Event attributes

```text
channel

is_mobile
is_package

is_booking
cnt
```

Отсутствующие source attributes не должны выдумываться.

### Derived

```text
lead_days
stay_nights

party_size
has_children

booking_value_proxy
```

### Distance

```text
distance_raw
distance_filled

distance_was_missing
distance_is_imputed

distance_imputation_level
distance_imputation_support
distance_imputation_mae
```

### Quality

```text
valid_for_lead_time
valid_for_stay_length
valid_for_party_metrics

quality_issue_count
```

---

# 19. `cnt` semantics

`cnt` является количеством похожих событий в контексте user session.

Поэтому обязательно сохраняются две разные концепции активности:

```text
row activity
=
COUNT(*)
```

и:

```text
weighted event activity
=
SUM(cnt)
```

Ни одна из них не должна автоматически называться "sessions".

Session count появляется только после отдельного sessionization layer.

---

# 20. `core.fct_booking`

## Grain

**Одна строка = один подтверждённый booking log event.**

Строится из `fct_event`.

Минимально:

```text
booking_id
event_id

user_id
platform_id

destination_id

hotel_market_id
hotel_cluster_id

event_date_key
checkin_date_key
checkout_date_key

is_package

lead_days
stay_nights

distance_filled

booking_value_proxy
```

Booking fact используется как удобный booking-centric interface для последующих analytical marts.

---

# 21. Distance enrichment

## Source semantics

`orig_destination_distance = NULL` означает отсутствие рассчитанного source distance.

NULL:

* не равен 0;
* не заменяется на 0;
* не impute-ится в STAGING.

Original value всегда сохраняется.

## Goal

Цель CORE enrichment:

**максимизировать полезное coverage distance при контролируемой ошибке восстановления.**

Не ставится цель заполнить 100% пропусков любой ценой.

---

# 22. Distance hierarchy

Основной estimator:

```text
median observed distance
```

Candidate levels:

```text
1. user city × destination
2. user city × hotel market

3. user region × destination
4. user region × hotel market

5. user country × destination
6. user country × hotel market

7. user country × hotel country
```

Каждый следующий уровень является backoff при отсутствии достаточной статистики предыдущего.

Дополнительные уровни могут исследоваться только при наличии явной причины.

`hotel_cluster` не рассматривается как географический ID.

---

# 23. Distance validation

Перед применением imputation обязательно проводится pseudo-missing experiment.

На подвыборке rows с observed distance:

1. часть известных distance скрывается;
2. значения восстанавливаются каждым hierarchy level;
3. сравниваются predictions с observed values.

Для каждого уровня измеряются:

```text
coverage
MAE
median_absolute_error
p90_absolute_error
relative_error
support
```

Также тестируются minimum-support thresholds.

Иерархия выбирается по measured quality.

Если уровень имеет неприемлемую ошибку, он не используется.

Допускается оставлять часть значений NULL.

---

# 24. `core.ref_distance_stats`

Создать reusable reference table для distance enrichment.

Минимальная логика:

```text
imputation_level

origin keys
destination/hotel keys

median_distance

observations

validation_error
```

Точная физическая схема зависит от технической реализации hierarchy.

---

# 25. Distance provenance in fact

Для каждого event хранить:

```text
distance_raw
distance_filled

distance_was_missing
distance_is_imputed

distance_imputation_level
distance_imputation_support
distance_imputation_mae
```

Если original distance присутствует:

```text
distance_filled = distance_raw
distance_is_imputed = false
```

Если distance восстановлен:

```text
distance_raw = NULL
distance_filled = estimated distance
distance_is_imputed = true
```

Если надёжно восстановить distance нельзя:

```text
distance_raw = NULL
distance_filled = NULL
distance_is_imputed = false
```

---

# 26. Exact duplicates

RAW сохраняет все exact duplicates.

STAGING только помечает их.

В CORE допускается controlled exact deduplication.

Количество удалённых duplicates обязательно логируется.

Deduplication rule должен быть deterministic и reproducible.

---

# 27. Train and test compatibility

CORE должен позволять хранить train и test в совместимой структуре.

Обязательное поле:

```text
source_dataset
```

Например:

```text
train
test
```

Нельзя автоматически предполагать одинаковую outcome semantics всех source datasets.

Если конкретное поле отсутствует в source:

* сохранять NULL;
* либо использовать подтверждённую dataset semantics;
* но не выдумывать значение.

Будущие conversion metrics обязаны явно определять допустимый source population.

---

# 28. Sessionization

Sessionization НЕ входит в CORE v1.

Не создавать:

```text
session_id
```

на основе `search_params_id`.

Не фиксировать 30-minute rule.

Будущий session layer будет построен отдельно после анализа sensitivity:

```text
15 min
30 min
60 min
120 min
```

Возможный будущий объект:

```text
fct_session
```

но он находится вне текущего scope.

---

# 29. CORE validation requirements

После materialization должны выполняться проверки.

## Row accounting

Сравнить:

```text
RAW rows
STAGING rows
CORE rows
duplicates removed
```

## Dimensions

Для каждой dimension:

```text
PK uniqueness
NULL PK
row count
```

## Fact relationships

Проверить:

```text
FK orphan counts
```

и:

```text
dimension joins do not increase fct_event row count
```

Ни один dimension join не должен создавать fan-out.

## Dates

Проверить:

* orphan `date_key`;
* invalid temporal records;
* calendar range.

## Distance

Показать:

```text
raw missing %
final missing %

imputed %

coverage by level

validation MAE
median absolute error
p90 error
```

---

# 30. Persistence

Рекомендуемая структура:

```text
data/
├── raw/
│
└── derived/
    ├── staging/
    └── core/
```

Derived tables сохраняются в Parquet.

Рабочая DWH база может дополнительно materialize те же таблицы в локальном ClickHouse/DuckDB.

---

# 31. Repository contract

В Git должны храниться:

```text
eda/
notebooks/
sql/
docs/
checks/
schemas/
artifacts/core_manifest.json
```

Большие generated Parquet по умолчанию не коммитятся в обычный Git.

---

# 32. Core manifest

Создать:

```text
artifacts/core_manifest.json
```

Для каждой таблицы:

```text
table_name
layer
grain
primary_key
foreign_keys
row_count
source_tables
build_timestamp
description
```

Manifest нужен для reproducibility и последующего handoff на MART layer.

---

# 33. Explicitly out of scope for CORE v1

На текущем этапе запрещено самостоятельно создавать:

* analytical marts;
* dashboard tables;
* DAU/MAU marts;
* LTV marts;
* retention marts;
* RFM segments;
* session facts;
* funnel tables;
* final booking-rate definition;
* ML features;
* PCA;
* predictive models.

Эти решения принимаются после просмотра готового CORE.

---

# 34. Open questions

Следующие вопросы остаются открытыми до реального прогона данных:

1. Является ли user location стабильным атрибутом `user_id`?
2. Стабилен ли `site_name → posa_continent`?
3. Стабилен ли `hotel_market → hotel_country/hotel_continent`?
4. Стабилен ли `destination_id → destination_type_id`?
5. Какой minimum support требуется для distance imputation?
6. Какие hierarchy levels distance дают приемлемую ошибку?
7. Какой процент missing distance останется после trustworthy enrichment?
8. Как будет определена sessionization v1?
9. Какая booking-rate definition станет canonical для dashboard?
10. Какие MARTS будут утверждены после CORE validation?

Все остальные архитектурные решения данного документа считаются зафиксированными для v1.

---

# 35. Definition of Done for CORE stage

Этап считается завершённым, если:

* RAW остаётся неизменным;
* STAGING воспроизводимо материализован;
* quality flags рассчитаны;
* dimensions построены;
* `dim_date` используется для event/check-in/check-out;
* `dim_hour` построена;
* `fct_event` материализован без join fan-out;
* `fct_booking` материализован;
* exact duplicates обработаны и залогированы;
* distance enrichment провалидирован на holdout;
* provenance imputed distance сохранён;
* PK/FK checks пройдены;
* derived Parquet сохранён локально;
* `core_schema.md` создан;
* `distance_imputation_report.md` создан;
* `core_manifest.json` создан;
* CORE готов выступать единственным source для следующего MART layer.
