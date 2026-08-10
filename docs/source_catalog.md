# Source catalog

## Canonical active train source

`data/parquet/train_full.parquet`

- 37,670,293 rows;
- used by `raw.train`;
- used by `tools/build_core.py`;
- one logical full Expedia train dataset.

## Preserved non-active artifacts

- `data/parquet/train.parquet` — older incomplete Parquet artifact with 243,605 rows;
- `data/train_parquet/part_*.parquet` — 38 immutable source parts used to build the canonical file;
- `data/train.csv` — original immutable CSV source.

These files are not alternative active inputs. The pipeline deliberately fails
if `train_full.parquet` is missing instead of silently falling back to an
incomplete or differently shaped source.
