# Full-source rerun comparison

Дата прогона: 2026-08-09  
Новый источник: `data/parquet/train_full.parquet`, объединённый из 38 файлов `data/train_parquet/*.parquet`.  
Строк train: **37,670,293**.

## EDA: previous report vs rerun

| Metric | Previous EDA | Full-source rerun | Result |
|---|---:|---:|---|
| train rows | 37,670,293 | 37,670,293 | match |
| distinct users | 1,198,786 | 1,198,786 | match |
| weighted events, `SUM(cnt)` | 55,879,507 | 55,879,507 | match |
| click rows | 34,669,600 | 34,669,600 | match |
| booking rows | 3,000,693 | 3,000,693 | match |
| booking row rate | 7.97% | 7.966% | match |
| booking weighted-event rate | 5.45% | 5.452% | match |
| missing distance | 13,525,001 / 35.90% | 13,525,001 / 35.904% | match |
| missing check-in | 47,083 | 47,083 | match |
| missing check-out | 47,084 | 47,084 | match |
| check-in before event | 8,457 | 8,457 | match |
| check-out before check-in | 798 | 798 | match |
| same-day stay | 144,804 | 144,804 | match |

The rerun confirms that the previous EDA report was based on the complete dataset, while the previous local CORE build had accidentally used the incomplete 243,605-row Parquet.

## Session sensitivity rerun

The experiment uses a reproducible 5% user sample and starts a new reconstructed session when the gap exceeds the threshold. `cnt` remains event multiplicity; it is not used as a session identifier.

| Gap | Sessions | Rows p50 | Weighted events p50 | Duration p50, min | Booking-session rate | Multi-destination |
|---:|---:|---:|---:|---:|---:|---:|
| 15 min | 694,838 | 2 | 2 | 2 | 19.567% | 11.109% |
| 30 min | 614,850 | 2 | 3 | 3 | 21.641% | 14.195% |
| 60 min | 572,427 | 2 | 3 | 3 | 22.947% | 16.256% |
| 120 min | 546,477 | 2 | 3 | 4 | 23.819% | 17.767% |

On this sample, the metrics change materially across all thresholds. The result does not justify freezing a 30-minute session rule in CORE; sessionization remains a separate future-layer decision.

## CORE: previous incomplete run vs full-source rerun

| Metric | Previous incomplete CORE | Full-source CORE |
|---|---:|---:|
| STAGING interaction rows | 2,771,848 | 40,198,536 |
| CORE event rows | 2,771,846 | 40,197,567 |
| controlled duplicates removed | 2 | 969 |
| distinct users | 1,181,694 | 1,198,786 |
| `dim_user_location` rows | 45,155 | 68,576 |
| `dim_destination` rows | 64,887 | 65,781 |
| `dim_hotel_market` rows | 2,185 | 2,225 |
| `dim_search_params` rows | 3,082 | 7,246 |
| `fct_booking` rows | 20,437 | 3,000,689 |
| raw missing distance | 933,811 | 14,371,504 |
| imputed distance rows | 293,803 | 5,238,749 |
| final NULL distance | 640,008 | 9,132,755 |

Full-source CORE validation: PK `PASS`, FK orphan checks `PASS`, fan-out `PASS`.

Mapping checks on the complete combined train+test source found:

- unstable user location: 985,538 users;
- unstable `hotel_market → country/continent`: 57 markets;
- unstable `site_name → posa_continent`: 0;
- unstable `destination_id → destination_type_id`: 0.

The full-source build uses the same fixed model and distance methodology. Country-level distance candidates remain measured but are not applied because their holdout errors are materially worse than city/region backoffs.
