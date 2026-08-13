# Setup и запуск BI с чистого окружения

Это канонический runbook проекта: он ведёт от трёх подготовленных Parquet-файлов
до работающего dashboard в Superset. Все команды выполняются из корня
репозитория `HotelsBooking`.

Pipeline, который будет собран:

```text
Parquet → RAW → STAGING → CORE → MARTS → ClickHouse
                                              ↓
                      Superset connection → datasets → metrics
                                                       ↓
                                              charts → dashboard
                                                       ↓
                                                 export bundle
```

## 1. Предварительные требования

Нужны:

- Python 3.11 или новее, доступный как `python3`;
- пакет Python `duckdb`;
- Docker Engine с Compose plugin (`docker compose`);
- `curl` для проверок локальных HTTP endpoints;
- место на диске для исходных данных, derived-слоёв, образов и Docker volumes.

Проверьте инструменты и установите единственную Python-зависимость, если её
ещё нет:

```bash
python3 --version
docker --version
docker compose version
curl --version
python3 -c "import duckdb; print(duckdb.__version__)"
# Только если предыдущая команда завершилась с ModuleNotFoundError:
python3 -m pip install duckdb
```

## 2. Подготовьте входные Parquet-файлы

Положите source-aligned файлы по точным путям:

```text
data/parquet/train_full.parquet
data/parquet/test.parquet
data/parquet/destinations.parquet
```

`train_full.parquet` должен содержать полный train. Если исходный train хранится
частями в `data/train_parquet/`, сначала объедините его утверждённым для вашей
поставки способом в единый `data/parquet/train_full.parquet`: текущий build не
собирает части автоматически. CSV-файлы не заменяют эти три Parquet-входа.

Проверьте входы до запуска долгого build:

```bash
ls -lh data/parquet/train_full.parquet \
       data/parquet/test.parquet \
       data/parquet/destinations.parquet

python3 - <<'PY'
from pathlib import Path

import duckdb

paths = [
    Path("data/parquet/train_full.parquet"),
    Path("data/parquet/test.parquet"),
    Path("data/parquet/destinations.parquet"),
]
con = duckdb.connect(":memory:")
for path in paths:
    assert path.is_file() and path.stat().st_size > 0, f"Missing or empty: {path}"
    rows = con.execute("SELECT count(*) FROM read_parquet(?)", [str(path)]).fetchone()[0]
    assert rows > 0, f"No rows: {path}"
    print(f"OK {path}: {rows:,} rows")
con.close()
PY
```

## 3. Инициализируйте RAW catalog views и соберите STAGING/CORE

```bash
python3 tools/build_core.py
```

Этот шаг сам обеспечивает наличие source-aligned views `raw.test` и
`raw.destinations` над подготовленными Parquet в локальном DuckDB catalog.
Ручной SQL, предварительно созданный catalog и setup-notebook не нужны. Train
читается напрямую из `data/parquet/train_full.parquet`. RAW здесь остаётся
логическим read-only слоем: исходные Parquet не изменяются, а все
материализованные результаты пишутся только в `data/derived/staging/` и
`data/derived/core/`. Catalog хранится в `data/analytics.duckdb`, manifest — в
`artifacts/core_manifest.json`.

Проверьте RAW prerequisites и CORE в read-only режиме:

```bash
python3 - <<'PY'
import json
from pathlib import Path

import duckdb

con = duckdb.connect("data/analytics.duckdb", read_only=True)
required = ["raw.test", "raw.destinations", "core.fct_event", "core.fct_booking"]
for relation in required:
    rows = con.execute(f"SELECT count(*) FROM {relation}").fetchone()[0]
    assert rows > 0, f"Missing or empty: {relation}"
    print(f"OK {relation}: {rows:,} rows")
con.close()

manifest = json.loads(Path("artifacts/core_manifest.json").read_text())
validation = manifest["validation"]
assert validation["all_pk_checks_pass"] is True
assert validation["all_fk_checks_pass"] is True
assert validation["fanout_check"]["pass"] is True
print("OK CORE validation")
PY
```

## 4. Соберите sessions и MARTS

```bash
python3 tools/build_analytics.py
```

Команда читает CORE, строит session objects и 12 MARTS в
`data/derived/marts/`, обновляет DuckDB catalog и
`artifacts/analytics_manifest.json`.

Проверьте session validation и соответствие файлов BI registry:

```bash
python3 - <<'PY'
import json
from pathlib import Path

analytics = json.loads(Path("artifacts/analytics_manifest.json").read_text())
registry = json.loads(Path("bi/registry.json").read_text())
assert analytics["validation"]["pass"] is True

expected = {item["name"] for item in registry["marts"]}
actual = {path.stem for path in Path("data/derived/marts").glob("*.parquet")}
assert len(expected) == 12, f"Expected 12 registered MARTS, got {len(expected)}"
assert expected <= actual, f"Missing MARTS: {sorted(expected - actual)}"
print("OK analytics validation; 12 registered MARTS are materialized")
PY
```

## 5. Задайте credentials до первого запуска BI

Credentials ClickHouse (`CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`) и Superset
admin (`SUPERSET_USERNAME`, `SUPERSET_PASSWORD`) потребляются и Docker Compose,
и host-side publisher. `SUPERSET_SECRET_KEY` и `SUPERSET_EMAIL` нужны Compose
при инициализации Superset; `CLICKHOUSE_URL` и `SUPERSET_URL` нужны publisher с
хоста. Экспортируйте весь набор **до** сборки/старта сервисов. Не коммитьте
значения в Git.

```bash
export SUPERSET_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export SUPERSET_USERNAME=admin
export SUPERSET_PASSWORD='replace-with-a-local-admin-password'
export SUPERSET_EMAIL='admin@example.com'

export CLICKHOUSE_USER=expedia_bi
export CLICKHOUSE_PASSWORD='replace-with-a-local-clickhouse-password'
export CLICKHOUSE_URL='http://localhost:8123'
export SUPERSET_URL='http://localhost:8088'
```

`CLICKHOUSE_PASSWORD` обязан быть непустым. `CLICKHOUSE_USER` и
`CLICKHOUSE_PASSWORD` должны быть одинаковыми для ClickHouse container и
publisher. Publisher с хоста использует `CLICKHOUSE_URL=localhost:8123`, а
созданное им Superset connection внутри Compose network использует service
hostname `clickhouse:8123`. При нестандартной сети это можно переопределить
через `SUPERSET_CLICKHOUSE_HOST` и `SUPERSET_CLICKHOUSE_PORT`.

Superset admin создаётся сервисом `superset-init` только при первой
инициализации metadata volume. Изменение `SUPERSET_PASSWORD` после первого
запуска не меняет пароль уже существующего пользователя. Для существующего
окружения используйте текущие credentials или штатно смените пароль в
Superset; не удаляйте volumes с данными ради обычного повторного запуска.

## 6. Соберите образы и запустите ClickHouse/Superset

Сначала получите pinned images ClickHouse/PostgreSQL и явно соберите локальный
Superset image с PostgreSQL- и ClickHouse-драйверами, затем запустите stack:

```bash
docker compose -f infra/docker-compose.yml pull clickhouse db
docker compose -f infra/docker-compose.yml build superset superset-init
make bi-up
```

`make bi-up` поднимает ClickHouse, PostgreSQL metadata database,
одноразовый `superset-init` и основной Superset container. Дождитесь завершения
инициализации и проверьте каждый уровень:

```bash
docker compose -f infra/docker-compose.yml ps -a
docker inspect --format '{{.State.ExitCode}}' expedia_superset_init
curl --fail --silent --show-error http://localhost:8123/ping
curl --fail --silent --show-error \
  --user "${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}" \
  --data-binary 'SELECT 1' \
  http://localhost:8123/
curl --fail --silent --show-error http://localhost:8088/health

docker exec -i \
  -e CLICKHOUSE_USER="${CLICKHOUSE_USER}" \
  -e CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD}" \
  expedia_superset /app/.venv/bin/python - <<'PY'
import os

import clickhouse_connect
import psycopg2

client = clickhouse_connect.get_client(
    host="clickhouse",
    port=8123,
    username=os.environ["CLICKHOUSE_USER"],
    password=os.environ["CLICKHOUSE_PASSWORD"],
)
assert client.query("SELECT 1").result_rows == [(1,)]
client.close()
print("OK Superset image drivers and Superset-container-to-ClickHouse connectivity")
PY
```

Ожидается:

- `clickhouse`, `db` и `superset` имеют status `Up`/`healthy`;
- `expedia_superset_init` имеет exit code `0`;
- ClickHouse `/ping` отвечает `Ok.`, authenticated query — `1`;
- Superset `/health` отвечает `OK`;
- оба BI-драйвера импортируются в `/app/.venv`, а Superset container достигает
  ClickHouse по `clickhouse:8123` с credentials publisher.

Если проверка не прошла, сначала смотрите логи, не запускайте publisher поверх
неисправного stack:

```bash
docker compose -f infra/docker-compose.yml logs --tail=200 clickhouse
docker compose -f infra/docker-compose.yml logs --tail=200 superset-init
docker compose -f infra/docker-compose.yml logs --tail=200 superset
```

Superset будет доступен по <http://localhost:8088>, ClickHouse HTTP — по
<http://localhost:8123>.

## 7. Опубликуйте MARTS и все BI-объекты

После успешных проверок сервисов выполните полный deploy:

```bash
make bi-all
```

`make bi-all` повторно запускает analytics build, затем
`python3 tools/publish_bi.py all`: загружает 12 MARTS в database `expedia` в
ClickHouse, создаёт/обновляет Superset connection `Expedia ClickHouse`,
datasets и metrics из `bi/registry.json`, charts и dashboard
`Expedia Hotel Analytics`, после чего создаёт export bundle. Команда должна
завершиться с exit code `0`. Имена объектов стабильны, поэтому повторный
`make bi-all` обновляет/переиспользует их.

Отдельные команды для диагностики или частичного прогона:

```bash
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD}" python3 tools/publish_bi.py publish --dry-run
make bi-publish
make bi-export
python3 tools/publish_bi.py all --skip-superset
```

`publish` работает только с ClickHouse. `export` provision-ит Superset и пишет
bundle, но не перезагружает ClickHouse. Для обычного полного развёртывания
используйте `make bi-all`.

## 8. Проверьте финальный результат

### ClickHouse

Следующая команда должна вернуть 12 таблиц `mart_*`:

```bash
curl --fail --silent --show-error \
  --user "${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}" \
  --data-binary "SELECT name FROM system.tables WHERE database = 'expedia' AND name LIKE 'mart_%' ORDER BY name FORMAT TSV" \
  http://localhost:8123/
```

### Superset publication и dashboard

Publisher записывает фактические IDs созданных объектов. Проверьте, что
опубликованы все datasets/charts и dashboard:

```bash
python3 - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path("artifacts/bi_publish_manifest.json").read_text())
superset = manifest["superset"]
assert manifest["dry_run"] is False
assert len(manifest["clickhouse"]) == 12
assert superset["database_id"] > 0
assert len(superset["datasets"]) == 12 and all(superset["datasets"].values())
assert len(superset["charts"]) == 4 and all(superset["charts"].values())
assert superset["dashboard_id"] > 0
print("OK ClickHouse publication, Superset connection, 12 datasets, 4 charts, dashboard")
PY
```

Проверьте через read-only Superset API, что registry metrics действительно
присутствуют в каждом dataset:

```bash
python3 - <<'PY'
import json
import os
from pathlib import Path

from tools.publish_bi import SupersetClient

registry = json.loads(Path("bi/registry.json").read_text())
manifest = json.loads(Path("artifacts/bi_publish_manifest.json").read_text())
client = SupersetClient(
    os.environ["SUPERSET_URL"],
    os.environ["SUPERSET_USERNAME"],
    os.environ["SUPERSET_PASSWORD"],
)
for mart in registry["marts"]:
    dataset_id = manifest["superset"]["datasets"][mart["name"]]
    details = client.request(f"/api/v1/dataset/{dataset_id}")["result"]
    actual = {metric["metric_name"] for metric in details.get("metrics", [])}
    expected = set(mart.get("metrics", []))
    assert expected <= actual, f"Missing metrics in {mart['name']}: {expected - actual}"
print("OK all registry metrics are present in Superset datasets")
PY
```

Успешное завершение `make bi-all` означает, что metrics были добавлены до
charts: при ошибке API publisher останавливается с ненулевым exit code и не
записывает успешные chart/dashboard IDs. Для визуальной проверки войдите в
Superset с `SUPERSET_USERNAME` / `SUPERSET_PASSWORD`, откройте **Dashboards →
Expedia Hotel Analytics** и убедитесь, что четыре charts отображаются без
ошибки connection/query. В **Data → Datasets** должны быть 12 `mart_*`
datasets; их metrics определены registry `bi/registry.json`.

### Export bundle

Ожидаются:

```text
artifacts/bi_publish_manifest.json
exports/latest.yaml
exports/expedia-bi-<UTC timestamp>.zip
```

Проверьте последний bundle:

```bash
python3 - <<'PY'
import json
import zipfile
from pathlib import Path

latest = json.loads(Path("exports/latest.yaml").read_text())
assert latest["superset"]["dashboard_id"] > 0
bundles = sorted(Path("exports").glob("expedia-bi-*.zip"))
assert bundles, "No BI export bundle"
with zipfile.ZipFile(bundles[-1]) as archive:
    assert set(archive.namelist()) == {"registry.yaml", "provision_manifest.yaml"}
print(f"OK export: {bundles[-1]}")
PY
```

`latest.yaml` имеет JSON-совместимое содержимое; ZIP — repository BI bundle с
registry и provisioning manifest, а не native Superset import archive.

## 9. Остановка и повторный запуск

```bash
make bi-down
```

Команда останавливает stack, но сохраняет ClickHouse и Superset metadata в
Docker volumes. Для повторного запуска экспортируйте те же credentials,
выполните `make bi-up`, дождитесь health checks и при необходимости повторите
`make bi-all`.
