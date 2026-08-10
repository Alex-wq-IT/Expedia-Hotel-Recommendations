# HotelsBooking / Expedia Analytics

Аналитический pipeline для Expedia Hotel Recommendations:

```text
Parquet → RAW → STAGING → CORE → MARTS
                              ↓
                         ClickHouse
                              ↓
                  Superset datasets / metrics
                              ↓
                    charts → dashboard
```

## 1. Куда положить данные

Исходные данные не должны попадать в Git. Положите source-aligned Parquet в `data/parquet/` с такими именами:

```text
data/parquet/train_full.parquet
data/parquet/test.parquet
data/parquet/destinations.parquet
```

`train_full.parquet` — полный train. Если train разбит на части, части можно хранить в `data/train_parquet/`, но перед сборкой CORE должен существовать единый `data/parquet/train_full.parquet`.

CSV-источники (`train.csv`, `test.csv`, `destinations.csv`) также можно хранить в `data/`, но pipeline читает Parquet. В текущей рабочей копии необходимые Parquet уже присутствуют.

## 2. Установка

Нужны Python 3.11+, DuckDB и Docker Compose:

```bash
python -m pip install duckdb
```

Проверьте наличие данных:

```bash
ls -lh data/parquet/train_full.parquet \
       data/parquet/test.parquet \
       data/parquet/destinations.parquet
```

## 3. Полная обработка данных

Запустите из корня проекта:

```bash
python tools/build_core.py
```

Команда строит STAGING и CORE в `data/derived/` и обновляет manifests в `artifacts/`. Затем подготавливаются sessionization и MARTS:

```bash
python tools/build_analytics.py
```

После этого MARTS находятся в `data/derived/marts/*.parquet`. Их registry, grain и метрики описаны в [`bi/registry.json`](bi/registry.json).

## 4. Запуск ClickHouse и Superset

Запустите локальные сервисы:

```bash
make bi-up
```

Compose поднимает ClickHouse, PostgreSQL для metadata Superset и Superset с ClickHouse-драйвером.

Задайте учётные данные Superset. Для локального запуска по умолчанию подходят `admin` / `admin`, но лучше переопределить их:

```bash
export SUPERSET_USERNAME=admin
export SUPERSET_PASSWORD='change-this-password'
export SUPERSET_EMAIL='admin@example.com'
```

Затем выполните полный deploy MARTS и BI-объектов:

```bash
make bi-all
```

`make bi-all` выполняет `build_analytics.py`, загружает все 12 MARTS в ClickHouse и через Superset API создаёт или обновляет:

- database connection `Expedia ClickHouse`;
- datasets для каждой MART;
- metrics из registry;
- charts;
- dashboard `Expedia Hotel Analytics`.

Адреса:

- Superset: <http://localhost:8088>
- ClickHouse HTTP: <http://localhost:8123>

Откройте Superset, перейдите в Dashboards и выберите `Expedia Hotel Analytics`.

## 5. Повторная публикация и экспорт

Повторный запуск безопасен для derived-слоёв: таблицы MARTS в ClickHouse пересоздаются из Parquet, а Superset-объекты upsert-ятся по стабильным именам.

```bash
python tools/publish_bi.py publish --dry-run
python tools/publish_bi.py publish
python tools/publish_bi.py all
```

Для публикации без Superset:

```bash
python tools/publish_bi.py all --skip-superset
```

Экспорт появляется в:

```text
exports/latest.yaml
exports/expedia-bi-<timestamp>.zip
artifacts/bi_publish_manifest.json
```

В ZIP лежат registry и manifest фактического deploy. Это воспроизводимый repository bundle; сам Superset продолжает быть источником runtime-состояния объектов.

## 6. Git и безопасность

В текущем workspace корень проекта не является Git-репозиторием. Вложенный `superset/` — отдельный репозиторий Apache Superset fork с remote `git@github.com:Debchik/superset_mod.git`; корневые файлы HotelsBooking туда не попадают.

Корневой `.gitignore` уже исключает:

- весь `data/`, включая CSV, Parquet, DuckDB и временные файлы;
- `.env` и `.env.*`;
- Python cache, notebook checkpoints и IDE-файлы;
- вложенный `superset/`.

`README.md`, `bi/`, `infra/`, `tools/`, `tests/`, `docs/` и `exports/` не исключены и могут быть добавлены в будущий Git-репозиторий проекта. Перед публикацией проверьте:

```bash
git status --short
git check-ignore -v data/parquet/train_full.parquet
git check-ignore -v .env
```

Не коммитьте пароли Superset, данные Expedia и файлы с секретами.

## 7. Остановка

```bash
make bi-down
```

По умолчанию volumes сохраняют данные ClickHouse и metadata Superset между запусками.
