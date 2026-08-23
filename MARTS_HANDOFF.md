# MARTS handoff — Expedia Hotel Recommendations

Этот файл — короткая точка входа в часть проекта **«обработанные данные и витрины»**.

## Что реализовано

```text
RAW → STAGING → CORE
                 ↓
       tools/build_analytics.py
                 ↓
            12 base MARTS
                 ↓
       tools/build_extra_marts.py
                 ↓
         2 supplementary MARTS
                 ↓
       tools/validate_marts.py
                 ↓
         ClickHouse → Superset
```

Всего в BI registry: **14 витрин**.

## Команды

После того как canonical Expedia Parquet лежат в `data/parquet/`:

```bash
python3 tools/build_core.py
make bi-build
```

`make bi-build` строит 12 базовых + 2 дополнительные витрины и валидирует их.

После проверки:

```bash
make bi-up
make bi-all
```

## Что читать перед защитой

1. `docs/marts_architecture.md`
2. `docs/marts_catalog.md`
3. `docs/marts_dashboard_logic.md`
4. `docs/marts_findings.md`
5. `docs/marts_quality_checks.md`
6. `docs/marts_defense_script.md`

## Portable demo

```bash
python3 -m pip install -r requirements_marts_demo.txt
streamlit run dashboard/streamlit_app.py
```

В sidebar укажите каталог, где лежат 14 CSV-витрин.

## Источник

Проект относится к **Kaggle Expedia Hotel Recommendations**. Ссылка
`customer-personality-analysis`, переданная ранее, относится к другому датасету
и не должна использоваться как source reference этого проекта.
