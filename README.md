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

Канонический путь для чистого развёртывания —
**[`docs/setup_bi_runbook.md`](docs/setup_bi_runbook.md)**. Он задаёт точный
порядок credentials, data builds, запуска сервисов, публикации и проверок;
для первого запуска следуйте ему от начала до конца.

## Готовые MARTS без локальной пересборки

[Скачать готовые (prebuilt) MARTS](https://disk.360.yandex.ru/d/5bgzCaQ-IuH7rw) — вариант для участников, которые хотят сразу анализировать данные или работать с BI, не запуская полный pipeline.

Это отдельный путь от локальной пересборки: чтобы собрать MARTS из исходных Parquet-файлов самостоятельно, выполните шаги из раздела [«Полная обработка данных»](#3-полная-обработка-данных).

## Exploratory data analysis

Exploratory-ноутбуки и небольшие EDA-specific материалы находятся в
каноническом корневом каталоге [`eda/`](eda/); правила размещения описаны в
[`eda/README.md`](eda/README.md). Generated datasets и большие raw/intermediate
файлы в `eda/` не добавляются.

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
python3 -m pip install duckdb
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
python3 tools/build_core.py
```

Команда сама обеспечивает наличие source-aligned `raw.test` и
`raw.destinations` над соответствующими immutable Parquet, затем строит STAGING
и CORE в `data/derived/` и обновляет manifests в `artifacts/`.
`train_full.parquet` при этом читается напрямую, поэтому отдельный ручной шаг
инициализации DuckDB или setup-notebook не нужен. Затем подготавливаются
sessionization и MARTS:

```bash
python3 tools/build_analytics.py
```

После этого MARTS находятся в `data/derived/marts/*.parquet`. Их registry, grain и метрики описаны в [`bi/registry.json`](bi/registry.json).

## 4. Запуск ClickHouse и Superset

Сначала задайте непустой пароль ClickHouse. Один и тот же
`CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD` используется Docker Compose и
запускаемым с хоста publisher; настоящий пароль храните только в окружении или
локальном `.env` (он исключён из Git):

```bash
cp .env.example .env
# Замените placeholder CLICKHOUSE_PASSWORD в .env.
set -a
. ./.env
set +a
export SUPERSET_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export SUPERSET_USERNAME=admin
export SUPERSET_PASSWORD='change-this-password'
export SUPERSET_EMAIL='admin@example.com'
```

Superset admin создаётся при первой инициализации, поэтому его credentials
также должны быть заданы до запуска. Затем запустите локальные сервисы:

```bash
make bi-up
```

Если ClickHouse уже был создан с другими учётными данными, пересоздайте его
контейнер после экспорта новых переменных (именованные volumes с данными при
этом сохраняются):

```bash
docker compose -f infra/docker-compose.yml up -d --force-recreate clickhouse
```

Проверьте аутентификацию именно с хоста перед публикацией:

```bash
curl --fail --user "$CLICKHOUSE_USER:$CLICKHOUSE_PASSWORD" \
  http://localhost:8123/ --data-binary 'SELECT 1'
```

Compose поднимает ClickHouse, PostgreSQL для metadata Superset и Superset с ClickHouse-драйвером.

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
python3 tools/publish_bi.py publish --dry-run
python3 tools/publish_bi.py publish
python3 tools/publish_bi.py all
```

Для публикации без Superset:

```bash
python3 tools/publish_bi.py all --skip-superset
```

Экспорт появляется в:

```text
exports/latest.yaml
exports/expedia-bi-<timestamp>.zip
artifacts/bi_publish_manifest.json
```

В ZIP лежат registry и manifest фактического deploy. Это воспроизводимый repository bundle; сам Superset продолжает быть источником runtime-состояния объектов.

## 6. Git и безопасность

Корень `HotelsBooking` является основным Git-репозиторием проекта. Каталог
`superset/` содержит отдельный вложенный checkout Apache Superset и исключён из
корневого репозитория; не смешивайте изменения этих двух рабочих деревьев.

Корневой `.gitignore` уже исключает:

- весь `data/`, включая CSV, Parquet, DuckDB и временные файлы;
- `.env` и `.env.*`;
- Python cache, notebook checkpoints и IDE-файлы;
- вложенный `superset/`.

`README.md`, `bi/`, `infra/`, `tools/`, `tests/`, `docs/` и `eda/` относятся к
корневому репозиторию. Generated BI exports добавляйте только намеренно. Перед
публикацией проверьте:

```bash
git status --short
git check-ignore -v data/parquet/train_full.parquet
git check-ignore -v .env
```

Не коммитьте пароли ClickHouse/Superset, данные Expedia и файлы с секретами.

## 7. Остановка

```bash
make bi-down
```

По умолчанию volumes сохраняют данные ClickHouse и metadata Superset между запусками.
