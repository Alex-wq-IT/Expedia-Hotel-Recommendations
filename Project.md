# Project map: HotelsBooking

## Назначение

Проект посвящён аналитике датасета **Expedia Hotel Recommendations**: поискам отелей, кликам и бронированиям, пользователям, направлениям, каналам, устройствам, сезонности и повторному поведению. Основной рабочий слой — локальные Parquet-файлы и каталог DuckDB; визуализация и dashboard-прототип собраны на базе вложенного Apache Superset.

Это навигационный файл для агентов. Подробные правила работы с данными находятся в [`AGENTS.md`](AGENTS.md).

## Карта верхнего уровня

| Путь | Роль |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Обязательные инструкции: SQL-first анализ, зерно данных, метрики, ограничения на запись и работу с raw. Читать перед аналитическими изменениями. |
| [`data/`](data/) | Данные, DuckDB-каталог и производные Parquet-слои. Raw-источники неизменяемы. |
| [`docs/`](docs/) | Контракты, схемы, проверки CORE, sessionization и marts. |
| [`eda/`](eda/) | Каноническое место для exploratory-ноутбуков и небольших EDA-specific материалов. Generated datasets и большие raw/intermediate-файлы сюда не добавляются. |
| [`notebooks/`](notebooks/) | Воспроизводимые setup/build pipeline-ноутбуки. Не использовать для загрузки всего train в pandas. |
| [`tools/`](tools/) | Python-скрипты построения CORE, сессий и MARTS. |
| [`artifacts/`](artifacts/) | Manifest-файлы сборок, handoff и небольшие результаты проверок. |
| [`design/`](design/) | Expedia-брендинг, иконки, брендбук и тема для dashboard. |
| [`superset/`](superset/) | Вложенный исходный репозиторий Apache Superset; это отдельный Git-репозиторий и инфраструктура BI-прототипа. |
| [`project_tree.txt`](project_tree.txt) | Снимок дерева проекта; может отставать от фактического состояния. |
| [`test_location_ids.csv`](test_location_ids.csv), [`test_location_ids_unique.csv`](test_location_ids_unique.csv) | Небольшие вспомогательные выборки location ID, извлечённые для исследования. |

## Поток данных

```text
CSV / исходные Parquet
        │
        ▼
RAW views в data/analytics.duckdb
        │
        ▼
data/derived/staging/*.parquet
        │
        ▼
data/derived/core/*.parquet
        │
        ▼
data/derived/marts/*.parquet и session-объекты
        │
        ▼
Superset / dashboard-прототип
```

Логическая архитектура описана как `RAW → STAGING → CORE → MARTS`. Фактическое состояние слоёв и их контракты нужно сверять с [`docs/dwh_contract.md`](docs/dwh_contract.md), [`docs/core_schema.md`](docs/core_schema.md) и [`docs/analytics_schema.md`](docs/analytics_schema.md), а не только с именами каталогов.

## `data/`: что где лежит

### Неизменяемые источники

- `train.csv`, `test.csv`, `destinations.csv` — исходные CSV.
- `parquet/train.parquet`, `parquet/test.parquet`, `parquet/destinations.parquet` — source-aligned Parquet.
- `parquet/train_full.parquet` — полный train-источник, собранный из частей.
- `train_parquet/part_*.parquet` — 38 частей полного train.
- `sample_submission.csv` — файл формата соревнования.

`data/quarantine/` содержит malformed-строки, исключённые при подготовке данных. Не считать их основным источником без явной задачи.

### Каталог и производные слои

- `analytics.duckdb` — локальный каталог DuckDB с представлениями над raw и производными слоями.
- `derived/staging/` — очищенные `interaction` и `destinations`.
- `derived/core/` — факты и измерения: `fct_event`, `fct_booking`, `dim_*`, справочники и результаты валидации расстояния.
- `derived/marts/` — аналитические витрины, созданные pipeline аналитики.
- `derived/duckdb_tmp/` и `analytics.duckdb.tmp/` — временные файлы DuckDB; не являются бизнес-артефактами.
- `query_duckdb.py` — локальный helper для выполнения SQL; перед использованием сверить его с правилами в `AGENTS.md`.

Для анализа предпочтителен Parquet и агрегация внутри DuckDB. Не загружать весь `train` в pandas и не писать в `raw` или исходные файлы.

## Документация и порядок чтения

1. [`AGENTS.md`](AGENTS.md) — рабочие ограничения и семантика полей.
2. [`docs/dwh_contract.md`](docs/dwh_contract.md) — целевая модель слоёв и правила источников.
3. [`docs/core_schema.md`](docs/core_schema.md) — зерно и состав CORE.
4. [`docs/analytics_schema.md`](docs/analytics_schema.md) — session-объекты и marts.
5. [`eda/README.md`](eda/README.md) — exploratory-анализы и правила размещения EDA-материалов.
6. [`docs/full_source_rerun_comparison.md`](docs/full_source_rerun_comparison.md) — результаты полного rerun после обнаружения неполного train.
7. [`artifacts/core_manifest.json`](artifacts/core_manifest.json) и [`artifacts/analytics_manifest.json`](artifacts/analytics_manifest.json) — машинно-читаемые результаты последних сборок.

Тематические документы:

- `01_core_review.md` — ревью CORE.
- `02_sessionization_contract_v1.md` — контракт сессий.
- `03_marts_draft_v0.md` — черновик витрин.
- [`eda/expedia_eda_staging_report.md`](eda/expedia_eda_staging_report.md) — EDA, риски staging и интерпретация метрик.
- `distance_imputation_report.md` — валидация заполнения расстояния.
- `analytics_build_report.md` — отчёт о сборке sessionization и marts.

## Скрипты, pipeline-ноутбуки и EDA

Основные скрипты:

- `tools/build_core.py` — регистрирует обязательные source-aligned RAW views и строит производные STAGING/CORE, не изменяя исходные Parquet.
- `tools/build_analytics.py` — строит сессии и первые аналитические MARTS на основе CORE.

Setup/build ноутбуки:

- `notebooks/setup_local_analytics.ipynb` — локальная настройка аналитического окружения.
- `notebooks/02_build_core.ipynb` — сборка CORE.

Exploratory-материалы находятся в каноническом корневом каталоге `eda/`:

- `eda/expedia_eda_staging_metrics.ipynb` — EDA и staging-метрики.
- `eda/repeat_bookings_analysis.ipynb` — анализ повторных бронирований.
- `eda/extract_expedia_location_ids.ipynb` — извлечение location ID.
- `eda/expedia_eda_staging_report.md` — EDA-отчёт, риски staging и интерпретация метрик.

## `design/` и `superset/`

`design/` — самостоятельный asset pack для Expedia dashboard: логотипы, торговые марки, Font Awesome icons, брендбук и [`superset-expedia-theme/`](design/superset-expedia-theme/). Канонический файл темы — `expedia-theme.json`; CSS dashboard — `expedia-dashboard.css`.

`superset/` — большой внешний исходный код Apache Superset, а не доменная логика Expedia. При изменении dashboard-темы сначала смотреть `design/superset-expedia-theme/` и конфигурацию Superset, а при изменении самого BI-продукта учитывать границу вложенного репозитория.

## Практические правила для агента

- Работать из корня `/home/neukluzhiy/Desktop/Projects/HotelsBooking`.
- Сначала проверять реальные таблицы и колонки DuckDB; имена каталогов не заменяют проверку схемы.
- Перед агрегацией явно определять grain и трактовку `cnt`: строки или взвешенные события `SUM(cnt)`.
- Различать event time (`date_time`) и даты проживания (`srch_ci`, `srch_co`).
- Не придумывать географические названия по encoded ID.
- Не создавать постоянные marts без явного запроса; повторно используемую логику сначала описывать в документации.
- Для изменений pipeline обновлять соответствующие manifest/документы и выполнять проверки PK/FK/fan-out.
- Корень `HotelsBooking` — основной Git-репозиторий; `superset/` является отдельным вложенным checkout и исключён из корневого tracking.

## Текущее состояние по именам артефактов

Последние manifest-файлы указывают на полный train, собранный из 38 частей, построенные STAGING/CORE и sessionization с правилом `gap_30m_v1`. Эти сведения являются снимком последней сборки; перед новым анализом проверять timestamp и validation-поля manifest-файлов.
