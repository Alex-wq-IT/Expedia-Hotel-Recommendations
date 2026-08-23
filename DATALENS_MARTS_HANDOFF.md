# DATALENS_MARTS_FINAL

Это финальный пакет ровно для части **«Обработанные данные и витрины»** существующего Expedia Hotel Recommendations dashboard в Yandex DataLens.

## Что внутри

- `marts_csv/` — 7 фактических витрин, которые покрывают предоставленный DataLens.
- `docs/01_architecture.md` — архитектура обработанного слоя.
- `docs/02_marts_catalog.md` — grain и поля каждой mart.
- `docs/03_dashboard_mapping.md` — каждый KPI/график → конкретная mart.
- `docs/04_build_logic.md` — логика сборки и формулы.
- `docs/05_validation_report.md` — фактическая валидация.
- `docs/06_defense_script.md` — готовое объяснение на защиту.
- `dashboard_mapping.csv` — машинно-читаемое соответствие графиков и marts.
- `manifest.json` — состав, grain, row counts, headline metrics.
- `tools/validate_datalens_marts.py` — проверка локально построенных Parquet.
- `tools/build_datalens_layer.py` — единая команда для CORE → MARTS → validation.

## Что НЕ нужно для этой части

Не требуется строить новый Streamlit/Superset dashboard. Визуальный слой уже существует в Yandex DataLens.

## Локальная репродукция

Из корня вашего репозитория, где уже лежат:
`data/parquet/train_full.parquet`,
`data/parquet/test.parquet`,
`data/parquet/destinations.parquet`:

```powershell
python .\tools\build_datalens_layer.py
```

Скрипт вызывает существующие `build_core.py` и `build_analytics.py`, а затем валидирует семь DataLens marts.

Фактические CSV в этом ZIP — готовый снимок витрин для проверки/защиты. Большие source Parquet в пакет не входят.
