# Yandex Summer School Project

Аналитическая система на данных Kaggle о поиске и бронировании отелей. Проект объединяет SQL-first обработку данных, контроль качества, продуктовую аналитику и публикацию витрин в ClickHouse/Superset.

## Результат

| Показатель | Значение |
|---|---:|
| Строк событий | 37 669 324 |
| Бронирования | 3 000 689 |
| Пользователи | 1 198 786 |
| Восстановленные сессии | 12 242 331 |
| Аналитические витрины | 14 |

Период событий в сохранённом отчёте: 7 января 2013 — 31 декабря 2014 года.

## Что я сделал

- Построил pipeline `RAW → STAGING → CORE → MARTS` в DuckDB; исходные Parquet остаются неизменяемыми, производные слои создаются повторяемыми скриптами.
- Подготовил 14 витрин для продуктовых, пользовательских, когортных и географических срезов; реализовал сессионализацию и согласование итогов между независимыми grain.
- Добавил проверки наличия витрин, схем, уникальности и заполненности ключей, допустимых диапазонов rates/shares и межвитринных totals.
- Настроил выгрузку в ClickHouse и публикацию datasets, metrics, charts и dashboard в Superset; добавил переносимый Streamlit-demo.
- Проверил восстановление пропущенного расстояния групповыми медианами на детерминированном holdout 10% известных значений. Для уровня `city_destination` при `min_support=5`: coverage 84,25%, MAE 29,41 в единицах исходного признака.

## Выводы из витрин

- Booking row rate: **8,29% desktop** против **5,86% mobile**.
- 67,9% пользователей имеют хотя бы одно бронирование; 19,58% относятся к наблюдаемому сегменту `4+ bookings`.
- Наблюдаемая repeat-booking retention: 13,83% через месяц, 11,23% через три месяца и 11,21% через шесть месяцев.
- В 35,90% строк отсутствует исходное расстояние; сохранены raw-значение, уровень восстановления и флаг качества.

Эти сравнения описательные. Они не доказывают причинное влияние устройства, пакета или горизонта планирования на бронирование.

## Архитектура

```text
Source Parquet
      ↓
RAW → STAGING → CORE
      ↓
14 MARTS → validation
      ↓
ClickHouse → Superset dashboard
```

Подробности:

- [архитектура витрин](docs/marts_architecture.md);
- [каталог витрин](docs/marts_catalog.md);
- [выводы по фактическим витринам](docs/marts_findings.md);
- [проверки качества](docs/marts_quality_checks.md);
- [отчёт о валидации](VALIDATION_REPORT.md).

## Воспроизведение

Нужны Python 3.11+, DuckDB и Docker Compose. Исходные файлы не входят в репозиторий; ожидаются:

```text
data/parquet/train_full.parquet
data/parquet/test.parquet
data/parquet/destinations.parquet
```

```bash
python -m pip install duckdb
python tools/build_core.py
make bi-build
make bi-validate
```

Для ClickHouse и Superset:

```bash
cp .env.example .env
make bi-up
make bi-all
```

Для demo без Superset:

```bash
python -m pip install -r requirements_marts_demo.txt
streamlit run dashboard/streamlit_app.py
```

## Границы проекта

Репозиторий подтверждает подготовку данных, аналитику и BI. В нём пока нет опубликованной predictive ranking-модели с Recall@K/NDCG@K; поэтому такие метрики не заявляются. Следующее логичное расширение — time-aware baseline для `hotel_cluster` с отдельным временным тестом.
