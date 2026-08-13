# Project Tickets — Extracted from Sonya's Feedback

This file contains only concrete, actionable implementation work from the chat. Items that still require a product/data decision or clarification are intentionally excluded and placed in `questions.md`.

## EXP-001 — Make `build_core.py` work on a fresh project setup

**Type:** Bug / reproducibility
**Source messages:** 570607–570608

### Problem
`tools/build_core.py` expects the `raw` layer to exist, specifically `raw.test` and `raw.destinations`, but on a fresh setup it creates only `staging`, `core`, and `meta`. As a result, running:

```bash
python3 tools/build_core.py
```

can fail with `schema "raw" does not exist` even when the Parquet files are valid.

### Required change
- Make the RAW prerequisites part of the normal build flow rather than requiring a manual one-off command.
- Ensure the `raw` schema exists.
- Create or refresh:
  - `raw.test` → `data/parquet/test.parquet`
  - `raw.destinations` → `data/parquet/destinations.parquet`
- Preserve the current behavior for train if `build_core.py` intentionally reads `data/parquet/train_full.parquet` directly.
- Update the documented build sequence so a new contributor can build CORE from the documented starting state.

### Acceptance criteria
- With the required Parquet files present and no pre-existing DuckDB RAW schema, `python3 tools/build_core.py` starts successfully without manual SQL/Python bootstrapping.
- `raw.test` and `raw.destinations` are available before they are referenced by the build.
- The documented fresh-start procedure matches the actual code path.

---

## EXP-002 — Fix `temp_directory` path handling in `build_analytics.py`

**Type:** Bug / Python compatibility
**Source messages:** 570609–570612

### Problem
`tools/build_analytics.py` constructs the DuckDB `PRAGMA temp_directory` value using a backslash replacement inside an f-string expression. This can raise:

```text
SyntaxError: f-string expression part cannot include a backslash
```

on affected Python versions.

### Required change
Resolve the path before the f-string and convert it with `Path.as_posix()`, then pass the prepared value into `sql_literal(...)`.

Conceptually:

```text
tmp = temp_dir.resolve().as_posix()
PRAGMA temp_directory = sql_literal(tmp)
```

### Acceptance criteria
- `python3 tools/build_analytics.py` parses and starts successfully on Python 3.11.
- The temp directory path is valid on macOS/Linux-style environments.
- No backslash replacement expression remains inside the affected f-string.

---

## EXP-003 — Install Superset PostgreSQL and ClickHouse drivers inside Superset's virtual environment

**Type:** Infrastructure / dependency bug
**Source messages:** 570613–570616, 570622

### Problem
`make bi-up` can fail during `superset-init` with:

```text
ModuleNotFoundError: No module named 'psycopg2'
```

Installing dependencies with a generic `pip install` does not necessarily install them into the environment used by the current Superset image (`/app/.venv`).

### Required change
Update `infra/Dockerfile` so the Superset image installs both required drivers into `/app/.venv` using the package mechanism available in the image:

- `clickhouse-connect`
- `psycopg2-binary`

The source proposal uses `uv pip install` after activating `/app/.venv`.

### Acceptance criteria
- A clean Docker image build succeeds.
- Inside the built Superset image, both `import psycopg2` and `import clickhouse_connect` succeed using `/app/.venv/bin/python`.
- `make bi-up` completes Superset initialization without the missing-`psycopg2` error.
- `superset-init` exits successfully and the main Superset container starts.

---

## EXP-004 — Remove the Makefile dependency on the `python` executable name

**Type:** Build portability
**Source messages:** 570617–570619, 570622

### Problem
On environments where Python 3 is exposed as `python3` but not `python`, targets such as `make bi-all` fail with:

```text
make: python: No such file or directory
```

### Required change
Update the Makefile commands that currently invoke `python` so the project can run with Python 3 in environments where only `python3` is present. Sonya's concrete fix was to replace the Makefile's `python` calls with `python3` while preserving Makefile tab indentation.

Affected flows include at least:
- `tools/build_analytics.py`
- `tools/publish_bi.py publish`
- `tools/publish_bi.py export`
- `tools/publish_bi.py all`
- unit-test discovery

### Acceptance criteria
- `grep -n "python" Makefile` shows no remaining command that incorrectly requires the unavailable `python` binary.
- `make bi-all` proceeds past the Python executable step on an environment with `python3` but no `python`.
- Unit-test targets still run.

---

## EXP-005 — Fix ClickHouse authentication for host-side BI publication

**Type:** Infrastructure / connectivity
**Source messages:** 570622

### Problem
The BI publisher can receive:

```text
ClickHouse query failed with 403
Authentication failed: password is incorrect
```

The reported configuration used the `default` ClickHouse user with an empty password. In that setup the container may restrict the user to local connections, while `tools/publish_bi.py` is executed from the host.

### Required change
- Configure a non-empty ClickHouse credential for the BI environment.
- Ensure `tools/publish_bi.py` receives the same credentials through `CLICKHOUSE_USER` and `CLICKHOUSE_PASSWORD`.
- Do not commit a production-strength secret directly into the repository; document/configure it through the environment for real use.
- Recreate the ClickHouse service when authentication configuration changes.

### Acceptance criteria
- A host-side request to ClickHouse on port `8123` authenticates successfully with the configured credentials.
- `tools/publish_bi.py` can connect from the host without a 403 authentication error.
- The same credentials are consistently used by the Docker configuration and publishing process.
- The repository does not require committing a real secret for normal deployment.

---

## EXP-006 — Preserve the Superset HTTP session for CSRF-protected API calls

**Type:** BI publishing bug
**Source messages:** 570622–570623

### Problem
Superset API publication can fail with:

```text
The CSRF session token is missing
```

The script retrieves a CSRF token but separate `urllib.request.urlopen()` calls do not preserve the related session cookie.

### Required change
In `tools/publish_bi.py`:
- add cookie handling with `http.cookiejar`;
- create a persistent opener using `HTTPCookieProcessor(CookieJar())`;
- use that opener for Superset JSON/API requests so cookies are retained across login/token/API calls;
- keep ClickHouse-specific `urlopen()` calls unchanged unless they need session handling for another reason.

### Acceptance criteria
- Superset API calls made after CSRF-token retrieval reuse the associated session cookie.
- Publication no longer fails with `The CSRF session token is missing`.
- ClickHouse client behavior is unchanged by the Superset session fix.

---

## EXP-007 — Use the Docker service hostname for Superset-to-ClickHouse connections

**Type:** Docker networking / BI integration
**Source messages:** 570623

### Problem
Superset can fail to connect to:

```text
localhost:8123
```

because inside the Superset container, `localhost` refers to the Superset container itself, not ClickHouse.

### Required change
Separate the two connection contexts:
- host-side publisher → `localhost:8123`;
- Superset container → `clickhouse:8123`.

In `provision_superset()`, build the Superset database URI using configurable values such as:
- `SUPERSET_CLICKHOUSE_HOST` with default `clickhouse`;
- `SUPERSET_CLICKHOUSE_PORT` with default `8123`.

### Acceptance criteria
- Host-side publication still reaches ClickHouse through `localhost:8123`.
- The Superset-created database connection points to the ClickHouse Docker service rather than container-local `localhost`.
- Superset can test/query the ClickHouse connection successfully.

---

## EXP-008 — Update Superset dataset create/update payloads for the current API

**Type:** API compatibility
**Source messages:** 570623

### Problem
Dataset provisioning uses fields that the current Superset API rejects. Reported errors include:

```text
database: Missing data for required field
database_id: Unknown field
is_sqllab_view: Unknown field
```

and, on update:

```text
database: Unknown field
```

The API expects different payloads for dataset creation and update.

### Required change
- For dataset creation (`POST`), use the current API shape with `database`, schema, table name, and valid supported fields.
- Do not send legacy/unsupported `database_id` or `is_sqllab_view` fields.
- For dataset update (`PUT`), remove `database` from the update payload before sending it.
- Make the generic `upsert()` path aware of this dataset-specific difference.

### Acceptance criteria
- New datasets can be created without `database_id` / `is_sqllab_view` validation errors.
- Existing datasets can be updated without the `database: Unknown field` error.
- Re-running dataset provisioning updates existing datasets instead of failing due to payload shape.

---

## EXP-009 — Publish Superset metrics through the supported dataset API and make the operation idempotent

**Type:** API compatibility / idempotency
**Source messages:** 570623–570624

### Problem
The publisher uses a metric endpoint that returns 404 in the current Superset version:

```text
GET /api/v1/dataset/{id}/metrics/
404 Not Found
```

Additionally, repeated runs can fail with:

```text
One or more metrics already exist
```

### Required change
- Do not rely on the removed `/dataset/{id}/metrics/` endpoint.
- Create/update the dataset first and obtain its `dataset_id`.
- Add metrics in a separate `PUT /api/v1/dataset/{id}` request rather than including them in the initial dataset `POST`.
- Before adding metrics, fetch the current dataset details and compare existing metric names.
- Send only missing metrics so repeated publication is idempotent.

### Acceptance criteria
- Metrics are added successfully using the supported dataset API.
- Initial dataset creation does not fail because `metrics` was included in the wrong request.
- Running the BI publication twice does not fail because previously created metrics already exist.
- Existing metrics are not duplicated.

---

## EXP-010 — Rewrite the project setup and BI deployment instructions around the actual working sequence

**Type:** Documentation / developer experience
**Source messages:** 570608, 570615–570616, 570625

### Problem
The current README/setup path does not fully describe prerequisites discovered during a clean setup. Examples from the chat include the missing RAW-layer prerequisite and multiple required BI environment/dependency steps.

### Required change
Create a single reproducible setup/runbook covering at least:
1. required Parquet inputs;
2. RAW initialization / CORE build;
3. analytics build;
4. Superset/ClickHouse image build and startup;
5. Superset credentials that must be provided before first initialization;
6. ClickHouse credentials required by the publisher;
7. `make bi-up` / `make bi-all` (or their corrected equivalents);
8. verification commands for containers and connectivity;
9. expected final outputs: marts in ClickHouse, Superset connection, datasets, metrics, charts, dashboard, and exported BI bundle.

### Acceptance criteria
- A new contributor can follow one documented path from prepared input files to a running BI environment.
- The documentation contains no hidden manual prerequisite such as pre-created `raw.test` / `raw.destinations` views.
- Required environment variables are described before the step at which they are consumed.
- Verification steps make it clear whether CORE, analytics, ClickHouse, Superset init, publication, and dashboard creation succeeded.

---

## EXP-011 — Investigate and fix dashboard creation after the BI publication flow

**Type:** Bug / BI end-to-end
**Source message:** 570627

### Problem
After the earlier ClickHouse/Superset/publishing fixes, Sonya reported that the dashboards still were not being built.

### Required change
Trace the final dashboard-generation phase of the BI publisher and identify the remaining failure after dataset/metric/chart provisioning. Fix the publication path so the expected dashboard is actually created or updated.

### Acceptance criteria
- The end-to-end BI publication completes without an unhandled dashboard-creation error.
- `Expedia Hotel Analytics` exists in Superset after publication.
- Expected charts are attached to the dashboard and render against the registered datasets.
- Re-running publication updates/reuses the dashboard rather than producing duplicates or failing.


---

## EXP-012 — Restrict valid project dates to 2013–2016

**Type:** Data quality / validation
**Source:** Team decision based on Sonya's date-range feedback

### Problem
The current date-validation logic allows a much wider year range than is useful for the project. This keeps isolated outlier dates that fall outside the period we want to analyze and display.

### Required change
- Update the project's date-validity rules so the accepted year range is **2013 through 2016 inclusive**.
- Apply the same range consistently wherever date validity is enforced in the data pipeline.
- Ensure records outside this interval are treated according to the existing invalid-date handling policy rather than silently entering downstream marts.
- Update any documentation or data-quality notes that still describe the previous date boundaries.

### Acceptance criteria
- Dates with year `< 2013` are not considered valid.
- Dates with year `> 2016` are not considered valid.
- Dates from `2013-01-01` through `2016-12-31` remain eligible, subject to the project's other date-validity checks.
- CORE/analytics outputs use the same 2013–2016 rule consistently.
- Documentation no longer references the previous broad year range as the active validation rule.

---

## EXP-013 — Add a dedicated root-level `eda/` folder

**Type:** Repository structure / developer experience
**Source:** Team decision based on Sonya's repository-organization suggestion

### Problem
EDA materials do not currently have an explicit, standardized location in the repository, which makes exploratory notebooks and related analysis harder to discover and organize.

### Required change
- Create an explicit `eda/` directory at the **root of the repository**.
- Move or place exploratory data-analysis notebooks and EDA-specific supporting files there.
- Keep generated datasets and large raw/intermediate data files out of this folder unless they are intentionally tracked.
- Update relevant repository documentation so contributors know where EDA work belongs.

### Acceptance criteria
- The repository root contains an `eda/` directory.
- Existing tracked EDA notebooks/files are organized under `eda/` where applicable.
- New contributors can identify `eda/` as the canonical location for exploratory analysis.
- Repository paths/documentation referencing EDA are updated if moving files changes them.

---

## EXP-014 — Add the ready marts download link to README

**Type:** Documentation / data access
**Source:** Team request

### Problem
A contributor currently has to rebuild the marts locally or obtain them separately, even though a ready-to-use copy is already available for the team.

### Required change
Add a clearly visible section to the repository README with a link to the prepared marts:

`https://disk.360.yandex.ru/d/5bgzCaQ-IuH7rw`

The README entry should explain that these are **ready/prebuilt marts** for contributors who want to analyze the data or work with BI without rebuilding the full pipeline first.

### Acceptance criteria
- The README contains the marts link exactly as provided.
- The link is labeled clearly as the location of the ready/prebuilt marts.
- The README distinguishes downloading ready marts from rebuilding marts locally.
- A new contributor can find the link without reading implementation-specific documentation.
