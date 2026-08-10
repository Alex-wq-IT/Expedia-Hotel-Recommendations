# Handoff: Expedia RAW → STAGING → CORE rerun

## Task

Rebuild the Expedia analysis and CORE pipeline after discovering that the previous `data/parquet/train.parquet` contained only 243,605 rows.

## Current canonical source

- The only active train source is `data/parquet/train_full.parquet`.
- Built by combining 38 immutable files from `data/train_parquet/*.parquet`.
- Verified row count: 37,670,293.
- The old incomplete `data/parquet/train.parquet` and source parts are preserved
  as immutable historical/source artifacts and are not active pipeline inputs.
- `raw.train` view points to `train_full.parquet`.

## Completed

- Full EDA rerun completed; comparison is in `docs/full_source_rerun_comparison.md`.
- CORE pipeline rerun completed through `notebooks/02_build_core.ipynb` and `tools/build_core.py`.
- CORE outputs, docs, and manifest were regenerated.
- Latest validation: PK PASS, FK PASS, fan-out PASS.

## Latest CORE snapshot

- STAGING interaction rows: 40,198,536.
- CORE event rows: 40,197,567.
- Controlled exact duplicates removed: 969.
- `fct_booking`: 3,000,689 rows.
- Raw distance missing: 14,371,504.
- Final distance NULL: 9,132,755.
- Distance imputed: 5,238,749; minimum support remains 5.

## Important decisions

- Architecture remains `RAW → STAGING → CORE`; no MARTS, dashboard, or sessionization was built.
- `fct_event` grain is one unique aggregated source log row after exact deduplication.
- `cnt` is multiplicity, not a session identifier.
- Country-level distance backoffs are measured but not applied because holdout p90 errors are too high.
- Session sensitivity was rerun on a 5% user sample for 15/30/60/120 minutes. No stable plateau was observed. If a provisional timeout is needed, 30 minutes is the recommended baseline, versioned as `gap_30m_v1`; 60 minutes is a journey-analysis sensitivity.

## Key artifacts

- `artifacts/core_manifest.json`
- `docs/core_schema.md`
- `docs/distance_imputation_report.md`
- `docs/full_source_rerun_comparison.md`
- `notebooks/02_build_core.ipynb`
- `tools/build_core.py`

## Suggested skills

- `diagnosing-bugs` for investigating any new pipeline/data issue.
- `code-review` when a Git baseline is available.
- `implement` for approved CORE/pipeline changes.
- `research` only if external dataset semantics need verification.
