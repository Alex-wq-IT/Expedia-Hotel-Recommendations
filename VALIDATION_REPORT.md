# Validation report

Дата handoff: 2026-08-23.

## Что проверено фактически

### 14 загруженных MART CSV

Acceptance validator завершился:

`ALL MART CHECKS PASSED`

Проверено:
- 14/14 файлов присутствуют;
- duplicate grain = 0 во всех marts;
- NULL grain = 0 во всех marts;
- product/channel/destination/origin/calendar/data-quality totals согласованы;
- `mart_user_360` согласован с обеими booking-frequency витринами;
- user-level bookings согласованы с product bookings.

Ключевые reconciliation totals:
- event rows: `37,669,324`;
- bookings: `3,000,689`;
- users: `1,198,786`.

Полный stdout: `artifacts/marts_handoff/validation_output.txt`.

### Patch contract

`python3 -m unittest discover -s tests -v`:

- 6 tests;
- 6 passed;
- 0 failed.

Проверяется:
- 14 marts в registry;
- отсутствие duplicate registry names;
- допустимый синтаксис metric names;
- `make bi-build` строит base + supplementary marts и запускает validation;
- `make bi-all` валидирует до publication;
- существующий Superset chart-name contract сохранён;
- два supplementary marts объявлены builder'ом;
- validator и registry согласованы по mart names.

### Python syntax

Успешно скомпилированы:
- `tools/build_extra_marts.py`;
- `tools/validate_marts.py`;
- `dashboard/streamlit_app.py`;
- `install_into_repo.py`.

## Что нельзя было выполнить в этой среде

1. Автоматический GitHub push: подключённый GitHub token имеет `push=false`.
2. Полный rebuild `build_core.py → build_analytics.py → build_extra_marts.py`:
   source Parquet/DuckDB catalog репозитория не смонтированы в текущую среду.
3. Production Parquet validator локально: системный Python текущей среды не
   содержит `duckdb`. В самом HotelExpedia DuckDB уже является обязательной
   зависимостью pipeline.

Поэтому handoff включает:
- one-command installer;
- production DuckDB validator;
- фактический CSV acceptance snapshot;
- unit/static contract tests;
- prebuilt full delivery для демонстрации.
