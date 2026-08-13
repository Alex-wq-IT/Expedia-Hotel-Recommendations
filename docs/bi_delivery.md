# CORE/MARTS → ClickHouse → Superset delivery

The repository now has a repeatable BI delivery boundary:

```text
CORE / MARTS
    ↓ tools/build_analytics.py
data/derived/marts/*.parquet
    ↓ tools/publish_bi.py
ClickHouse expedia.mart_*
    ↓ Superset REST API
datasets → metrics → charts → dashboard
    ↓
exports/expedia-bi-*.zip + exports/latest.yaml
```

The registry is [`bi/registry.json`](../bi/registry.json). It lists the 12
approved marts and their grains, time columns, and metrics. The publisher never
reads raw Parquet and never writes to DuckDB.

## Local start

The complete clean-setup sequence and stage-by-stage checks are maintained in
[`setup_bi_runbook.md`](setup_bi_runbook.md). The commands below are only a
short reference for an already prepared local environment.

```bash
cp .env.example .env
# Replace the CLICKHOUSE_PASSWORD placeholder, then export the same values for
# Docker Compose and the host-side publisher.
set -a
. ./.env
set +a
export SUPERSET_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export SUPERSET_USERNAME=admin
export SUPERSET_PASSWORD='replace-with-a-local-admin-password'
export SUPERSET_EMAIL='admin@example.com'
make bi-up
make bi-all
```

`CLICKHOUSE_PASSWORD` is required and must be non-empty. Keep the real value in
the environment or the ignored local `.env`, never in tracked configuration.
The default local username is `expedia_bi`; override `CLICKHOUSE_USER` in the
same environment when needed. After changing either credential, recreate the
ClickHouse service while preserving its named data volume:

```bash
docker compose -f infra/docker-compose.yml up -d --force-recreate clickhouse
curl --fail --user "$CLICKHOUSE_USER:$CLICKHOUSE_PASSWORD" \
  http://localhost:8123/ --data-binary 'SELECT 1'
```

`bi-all` first rebuilds the existing CORE-derived MARTS with
`tools/build_analytics.py`, then publishes them and provisions Superset.

ClickHouse is available at `http://localhost:8123`; Superset is at
`http://localhost:8088`. Override `CLICKHOUSE_URL`, `CLICKHOUSE_USER`,
`CLICKHOUSE_PASSWORD`, and `SUPERSET_URL` when using a non-local deployment.
The publisher uses `CLICKHOUSE_URL` from the host, while the database URI stored
in Superset uses `SUPERSET_CLICKHOUSE_HOST=clickhouse` and
`SUPERSET_CLICKHOUSE_PORT=8123` by default so it resolves over the Docker
network. Override those two variables independently when Superset connects by a
different internal address.
The publisher reads the ClickHouse username and password directly from those
two environment variables, so run it from the shell where they were exported.

Useful commands:

```bash
python3 tools/publish_bi.py publish --dry-run
python3 tools/publish_bi.py publish
python3 tools/publish_bi.py all --skip-superset
make bi-test
```

`publish` replaces only derived ClickHouse MART tables, so a rerun is safe and
does not duplicate rows. Superset objects are upserted by stable names. The
publisher writes `artifacts/bi_publish_manifest.json`; `all` additionally
writes a readable YAML-compatible export and a ZIP bundle under `exports/`.

The current export is a repository delivery bundle, not a native Superset
import archive. It contains the registry and the exact provisioning manifest;
the source of truth remains the registry plus the idempotent publisher.

## Verification

The delivery layer was verified locally with:

```text
python -m py_compile tools/publish_bi.py infra/superset_config.py  PASS
python -m unittest discover -s tests -v                         4 tests PASS
docker compose -f infra/docker-compose.yml config              PASS
registry ↔ data/derived/marts/*.parquet                          12 ↔ 12
```

The ClickHouse container smoke test requires a successful Docker Hub image
pull; in the current environment that pull ended with an external TLS timeout.
