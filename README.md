# HotelsBooking / Expedia Analytics

Аналитический pipeline для **Kaggle Expedia Hotel Recommendations**.

> Важно: ссылка `customer-personality-analysis`, которая ранее фигурировала в
> обсуждении, относится к другому датасету. Этот репозиторий, EDA и все MARTS
> относятся к Expedia Hotel Recommendations.

```text
Source Parquet
      ↓
     RAW
      ↓
   STAGING
      ↓
     CORE
      ↓
12 base MARTS + 2 supplementary MARTS
      ↓
 validation
      ↓
 ClickHouse
      ↓
 Superset datasets / metrics / charts
      ↓
 Expedia Hotel Analytics dashboard
```

Канонический runbook BI: [`docs/setup_bi_runbook.md`](docs/setup_bi_runbook.md).
Описание обработанного слоя и витрин:
[`MARTS_HANDOFF.md`](MARTS_HANDOFF.md).

## 1. Исходные данные

Raw/source-файлы не коммитятся в Git. Pipeline ожидает:

```text
data/parquet/train_full.parquet
data/parquet/test.parquet
data/parquet/destinations.parquet
```

`train_full.parquet` — полный Expedia train. Raw остаётся immutable.

## 2. Требования

- Python 3.11+
- DuckDB
- Docker / Docker Compose для ClickHouse + Superset

Минимально:

```bash
python3 -m pip install duckdb
```

DuckDB builder использует resource-safe настройки и spill-to-disk через
`tools/duckdb_runtime.py`.

## 3. Полная обработка данных

### CORE

```bash
python3 tools/build_core.py
```

Сборка создаёт/обновляет производные STAGING/CORE Parquet и manifests, не
изменяя source Parquet.

### Все 14 MARTS

```bash
make bi-build
```

`make bi-build` последовательно выполняет:

```text
python3 tools/build_analytics.py
python3 tools/build_extra_marts.py
python3 tools/validate_marts.py
```

Первый builder создаёт sessionization и 12 базовых marts. Второй создаёт:

- `mart_package_profile`
- `mart_booking_frequency_exact`

После этого validator проверяет все 14 marts относительно
[`bi/registry.json`](bi/registry.json).

Материализованные таблицы лежат в:

```text
data/derived/marts/*.parquet
```

## 4. MART catalog

| Mart | Grain |
|---|---|
| `mart_product_daily` | event date |
| `mart_session_daily` | session start date |
| `mart_travel_calendar_daily` | calendar date |
| `mart_channel_platform` | month × channel × platform × mobile |
| `mart_destination_performance` | month × destination × hotel market |
| `mart_user_360` | user |
| `mart_origin_destination` | month × user country × hotel country |
| `mart_trip_profile` | month × lead bucket × stay bucket × party segment |
| `mart_package_profile` | month × package × lead × stay × party × channel × mobile |
| `mart_retention_cohort` | cohort month × months since first booking |
| `mart_booking_frequency` | booking-count bucket |
| `mart_booking_frequency_exact` | exact observed booking count |
| `mart_data_quality_daily` | event date |
| `mart_distance_quality` | imputation level × support threshold |

Полный каталог: [`docs/marts_catalog.md`](docs/marts_catalog.md).

## 5. Metric semantics

`cnt` — multiplicity исходной агрегированной строки. Поэтому проект всегда
различает:

```text
row_events      = COUNT(*)
weighted_events = SUM(cnt)
```

`booking_value_proxy` — относительный score (0/1/2), **не деньги и не revenue**.

Для aggregate conversion нельзя суммировать rates. Правильно:

```text
SUM(bookings) / SUM(row_events)
```

Подробно: [`docs/marts_architecture.md`](docs/marts_architecture.md).

## 6. Validation

Повторная проверка без rebuild:

```bash
make bi-validate
```

Проверяется:

- физическое наличие всех 14 marts;
- соответствие registry реальным колонкам;
- уникальность и non-null grain;
- rate/share в допустимом диапазоне;
- логические ограничения;
- reconciliation totals между независимыми grains.

Acceptance snapshot переданных marts находится в
`artifacts/marts_handoff/`.

## 7. ClickHouse + Superset

Создайте локальный `.env` из `.env.example` и задайте непустой пароль
ClickHouse. Реальные credentials не коммитить.

Пример:

```bash
cp .env.example .env
set -a
. ./.env
set +a

export SUPERSET_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export SUPERSET_USERNAME=admin
export SUPERSET_PASSWORD='change-this-password'
export SUPERSET_EMAIL='admin@example.com'
```

Запуск:

```bash
make bi-up
```

Полная сборка + validation + публикация:

```bash
make bi-all
```

`make bi-all` строит все 14 marts, валидирует их, загружает в ClickHouse и
публикует Superset datasets/metrics/charts/dashboard.

Локальные адреса:

- Superset: `http://localhost:8088`
- ClickHouse HTTP: `http://localhost:8123`

Dashboard: **Expedia Hotel Analytics**.

## 8. Portable demo без Superset

Для защиты проекта можно использовать отдельный Streamlit snapshot-dashboard.
Он читает переданные CSV-marts и не является production BI-слоем.

```bash
python3 -m pip install -r requirements_marts_demo.txt
streamlit run dashboard/streamlit_app.py
```

Укажите каталог с 14 CSV в sidebar.

## 9. Документы для защиты

Рекомендуемый порядок:

1. [`docs/marts_architecture.md`](docs/marts_architecture.md)
2. [`docs/marts_catalog.md`](docs/marts_catalog.md)
3. [`docs/marts_dashboard_logic.md`](docs/marts_dashboard_logic.md)
4. [`docs/marts_findings.md`](docs/marts_findings.md)
5. [`docs/marts_quality_checks.md`](docs/marts_quality_checks.md)
6. [`docs/marts_defense_script.md`](docs/marts_defense_script.md)

## 10. Git и безопасность

Не коммитьте:

- `data/` с raw/derived datasets;
- `.env` и secrets;
- локальные DuckDB temp/cache;
- credentials ClickHouse/Superset.

Коммитить следует:

- `tools/`
- `bi/`
- `docs/`
- `tests/`
- `dashboard/` (portable demo)
- небольшие audit artifacts

## 11. Тесты

```bash
make bi-test
```

## 12. Остановка BI

```bash
make bi-down
```

Volumes ClickHouse и Superset metadata сохраняются между обычными restart.
