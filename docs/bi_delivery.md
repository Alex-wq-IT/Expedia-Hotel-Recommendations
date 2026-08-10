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

Requirements: Docker Compose, Python with `duckdb` (already used by the local
pipeline), and a running Superset admin account.

```bash
make bi-up
export SUPERSET_USERNAME=admin SUPERSET_PASSWORD=admin
make bi-all
```

`bi-all` first rebuilds the existing CORE-derived MARTS with
`tools/build_analytics.py`, then publishes them and provisions Superset.

ClickHouse is available at `http://localhost:8123`; Superset is at
`http://localhost:8088`. Override `CLICKHOUSE_URL`, `CLICKHOUSE_USER`,
`CLICKHOUSE_PASSWORD`, and `SUPERSET_URL` when using a non-local deployment.

Useful commands:

```bash
python tools/publish_bi.py publish --dry-run
python tools/publish_bi.py publish
python tools/publish_bi.py all --skip-superset
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
