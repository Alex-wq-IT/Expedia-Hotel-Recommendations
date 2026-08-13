# Exploratory data analysis

`eda/` is the canonical repository location for exploratory data-analysis
notebooks and small, hand-maintained files that directly support them.

Run notebooks from the repository root unless a notebook says otherwise. Follow
[`AGENTS.md`](../AGENTS.md): query DuckDB/Parquet with SQL first, state the
analysis grain and metric definitions, and do not load the full train dataset
into pandas.

## Contents

- [`expedia_eda_staging_metrics.ipynb`](expedia_eda_staging_metrics.ipynb) —
  source-grain EDA and staging/product metric checks.
- [`repeat_bookings_analysis.ipynb`](repeat_bookings_analysis.ipynb) —
  exploratory analysis of repeat booking behavior.
- [`extract_expedia_location_ids.ipynb`](extract_expedia_location_ids.ipynb) —
  exploratory extraction of encoded location and channel identifiers.
- [`expedia_eda_staging_report.md`](expedia_eda_staging_report.md) — synthesis
  of EDA findings, staging risks, and metric implications.

Setup and pipeline notebooks remain in [`notebooks/`](../notebooks/); they are
not EDA artifacts.

## What does not belong here

Do not commit raw sources, generated datasets, notebook checkpoints, DuckDB
catalogs, or large intermediate outputs to `eda/`. Keep immutable inputs under
the existing ignored `data/` paths and small generated analysis outputs under
`outputs/` when they need to be retained locally.
