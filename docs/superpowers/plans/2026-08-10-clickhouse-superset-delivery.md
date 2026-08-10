# ClickHouse Superset Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the approved MARTS deployable from the repository into ClickHouse and idempotently provisioned in Superset as datasets, metrics, charts, a dashboard, and a Git-tracked export bundle.

**Architecture:** `tools/build_analytics.py` remains the CORE → MARTS producer. A new BI publisher reads only the materialized MART Parquet files, replaces derived ClickHouse tables, then uses Superset REST API upserts keyed by stable names. The same registry drives both provisioning and a deterministic YAML/ZIP export; raw data and DuckDB raw schemas are never written.

**Tech Stack:** Python 3.11+ standard library, ClickHouse HTTP API, Superset REST API, Docker Compose, JSON-compatible YAML registry, ZIP archive.

## Global Constraints

- Raw/source Parquet and `raw` DuckDB objects remain immutable.
- MART grain and metric definitions come from `docs/analytics_schema.md` and `docs/03_marts_draft_v0.md`.
- ClickHouse writes are limited to derived `marts` tables.
- Superset provisioning is idempotent and fails loudly on HTTP/API errors.
- No Python loading of the full train dataset; the publisher reads one MART file at a time as bytes.

### Task 1: Define the delivery registry and local services

**Files:**
- Create: `bi/registry.json`
- Create: `infra/docker-compose.yml`
- Create: `docs/bi_delivery.md`

- [ ] Define all 12 existing marts, their grains, time columns, default dimensions, and explicit metrics in a machine-readable registry.
- [ ] Add ClickHouse and Superset service topology with persistent volumes and health checks; keep Superset’s existing source tree untouched.
- [ ] Document prerequisites, environment variables, commands, idempotency, and artifact locations.

### Task 2: Implement ClickHouse MART publisher

**Files:**
- Create: `tools/publish_bi.py`
- Test: `tests/test_publish_bi.py`

- [ ] Add pure functions for registry loading, ClickHouse type mapping, SQL identifier quoting, and stable names.
- [ ] Implement ClickHouse HTTP requests for database/table replacement and Parquet `INSERT`.
- [ ] Validate source file existence and row count before publishing; write `artifacts/bi_publish_manifest.json`.

### Task 3: Implement Superset API provisioning

**Files:**
- Modify: `tools/publish_bi.py`
- Modify: `bi/registry.json`
- Test: `tests/test_publish_bi.py`

- [ ] Implement login + CSRF handling and name-based upsert of the ClickHouse database connection and datasets.
- [ ] Create/update dataset metrics and stable chart definitions.
- [ ] Create/update one dashboard with a deterministic chart layout and fail if a required API response is malformed.

### Task 4: Implement export and command-line workflow

**Files:**
- Modify: `tools/publish_bi.py`
- Create: `Makefile`
- Create: `exports/.gitkeep`
- Test: `tests/test_publish_bi.py`

- [ ] Add `publish`, `export`, and `all` commands, with `--skip-superset` for ClickHouse-only deployments and `--dry-run` for inspection.
- [ ] Export registry plus provisioned API payloads as readable YAML-compatible JSON and ZIP under `exports/`.
- [ ] Add tests for dry-run behavior, deterministic archive contents, and injection-safe identifiers.

### Task 5: Verify the end-to-end contract

- [ ] Run unit tests and compile checks.
- [ ] Validate registry marts against `data/derived/marts/*.parquet` without scanning raw data.
- [ ] If Docker is available, run ClickHouse health check and a small publisher smoke test; report Superset build-time limitations separately.
- [ ] Update docs with exact verification results.
