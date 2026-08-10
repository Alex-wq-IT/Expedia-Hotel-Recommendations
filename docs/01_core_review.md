# CORE v1 Review

## Verdict

**Status: PASS WITH TWO REQUIRED CHECKS BEFORE FINAL MART BUILD.**

The structural DWH work is good enough to continue with sessionization and mart prototyping.

The current implementation correctly follows the intended architecture:

`RAW -> STAGING -> CORE`

and does not prematurely materialize marts.

---

## What is correct

### 1. Grain and entity semantics

`core.fct_event` has the correct grain:

> one unique aggregated Expedia source log row after exact deduplication.

This is explicitly not treated as:
- one physical click;
- one search;
- one session;
- one booking journey.

`cnt` is preserved as multiplicity.

`search_params_id` is correctly treated only as a surrogate key for a parameter combination.

`hotel_cluster_id` is correctly treated as a cluster, not a hotel ID.

### 2. Dimensional modelling

The implementation handled non-stable mappings correctly.

Observed:
- `295,201` users have multiple user-location combinations;
- therefore `dim_user_location` was created separately.
- `39` hotel-market IDs violate a simple market -> country/continent mapping;
- therefore `dim_hotel_market` is keyed by the actual attribute combination.

This is preferable to silently forcing invalid functional dependencies.

### 3. Date model

The following are correctly present:
- `dim_date`;
- `dim_hour`;
- event date FK;
- check-in date FK;
- check-out date FK;
- event hour FK.

This supports independent analysis of:
- interaction/search seasonality;
- check-in seasonality;
- check-out seasonality.

### 4. Quality handling

STAGING preserves suspicious records and source values.

CORE performs deterministic exact deduplication only.

Current accounting:
- RAW rows: `2,771,848`
- STAGING rows: `2,771,848`
- duplicate rows flagged: `4`
- CORE events: `2,771,846`
- rows removed: `2`

This accounting is internally consistent.

### 5. PK / FK / fan-out validation

All recorded PK checks pass.

All recorded FK orphan counts are zero.

`fct_event` fan-out validation passes:

- core base rows: `2,771,846`
- fct_event rows: `2,771,846`

This is a strong signal that dimensions are not multiplying facts.

### 6. Distance enrichment

The distance design follows the agreed principles:
- raw distance is preserved;
- NULL is never replaced with zero;
- imputation occurs only in CORE;
- estimator is median;
- provenance is stored;
- low-quality country-level fallback is not applied.

Current result:
- source missing: `933,811` / `33.689%`
- imputed: `293,803` / `10.600%` of all events
- final NULL: `640,008` / `23.090%`
- final available distance: `76.910%`

Applied levels:
- city x destination
- city x hotel market
- region x destination
- region x hotel market

The rejected country-level candidates have MAE roughly 468-543 and p90 error roughly 1,271-1,409, so rejecting them is correct.

---

# Missing CORE object to add now

Sessionization was intentionally not part of CORE v1.

For the next iteration add:

- `core.fct_session`
- `core.event_session_map`

Do not overwrite the grain of `fct_event`.

Sessionization must remain a derived, versioned reconstruction.

See `sessionization_contract_v1.md`.

---

# Recommendation

Proceed in this order:

1. verify train source scope;
2. verify strict holdout isolation for distance;
3. implement versioned sessionization;
4. create draft marts;
5. inspect marts before dashboard work;
6. rebuild the same pipeline on the full intended source before final reporting if current train is only a sample.
