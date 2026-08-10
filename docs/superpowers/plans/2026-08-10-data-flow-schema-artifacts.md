# Data Flow Schema Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Document the current RAW → STAGING → CORE → MARTS data flow and publish a self-contained interactive HTML diagram with clickable tables and field hover descriptions.

**Architecture:** Read the actual DuckDB catalog and derived Parquet layer as the source of truth, combine it with the existing DWH contracts and build manifests, then render both Markdown and HTML from one metadata model. The HTML will be dependency-free and contain the table/column metadata plus explicit transformation and lineage edges.

**Tech Stack:** Python, DuckDB read-only introspection, Markdown, standalone HTML/CSS/JavaScript.

## Global Constraints

- Raw data and `raw` schema remain immutable.
- Do not load the full train dataset into pandas or create database writes during introspection.
- Distinguish actual materialized objects from target/contract objects.
- Preserve the existing four-layer terminology `RAW → STAGING → CORE → MARTS`.

### Task 1: Build the metadata and rendering tool

**Files:**
- Create: `tools/build_schema_artifacts.py`

- [ ] Read table/column metadata from `data/analytics.duckdb` with a read-only DuckDB connection.
- [ ] Read current row counts and Parquet paths from manifests/files without scanning raw data into memory.
- [ ] Add curated descriptions for layers, transformations, tables, and field naming patterns (`d1`…`d149`, encoded IDs, quality flags, metrics).
- [ ] Render `artifacts/schema.md` and `artifacts/data_flow.html` from the same metadata structure.
- [ ] Render the HTML as a standalone document with layer columns, lineage arrows, clickable table cards, field lists, and hover tooltips.

### Task 2: Generate the requested artifacts

**Files:**
- Create: `artifacts/schema.md`
- Create: `artifacts/data_flow.html`

- [ ] Run the renderer from the repository root.
- [ ] Include all currently registered RAW, STAGING, CORE, and MARTS objects and explicitly document session objects and materialization paths.
- [ ] Include caveats for `cnt`, event time vs stay dates, encoded IDs, distance imputation, and the missing `tools/query_duckdb.py` helper.

### Task 3: Validate the deliverables

- [ ] Re-run the renderer and confirm it succeeds against the current catalog.
- [ ] Check that every catalog object appears in `artifacts/schema.md` and `artifacts/data_flow.html`.
- [ ] Parse the HTML and verify every table card has a click target and every field has a non-empty tooltip description.
- [ ] Verify that no raw/source file is modified and report the generated artifacts and validation results.
