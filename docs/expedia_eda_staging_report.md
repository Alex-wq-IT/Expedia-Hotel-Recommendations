# Expedia Hotel Recommendations — EDA synthesis, staging risks and metric implications

## 1. Executive summary

This report combines:

1. the team's uploaded `EDA.ipynb`;
2. public analyses of the same Expedia Hotel Recommendations dataset;
3. additional recommendations specifically for the DWH cleaning/staging pipeline and the product metrics currently being designed.

The most important conclusion is that the dataset grain is **not equal to one raw user action**. The field `cnt` is documented as the number of similar events in the context of the same user session. In the team's EDA, 25.43% of rows have `cnt > 1`; therefore one row may represent several similar events. Any metric based on activity must explicitly choose whether it counts **rows**, **events weighted by `cnt`**, **sessions**, **users**, or **bookings**.

The second major conclusion is that this dataset should not be treated as a clean production event stream. It contains missing distances, malformed or logically inconsistent dates, exact duplicates, zero-party/zero-room searches, and already-aggregated events. The safest DWH design is therefore:

**RAW → STG (typed + quality flags, no destructive edits) → CLEAN/SILVER (dedupe/quarantine/derived fields) → MARTS (sessions, funnel, users/RF, destinations).**

---

## 2. What the team's EDA established

### Scale and event semantics

- Rows: **37,670,293**
- Unique users: **1,198,786**
- Click rows (`is_booking=0`): **34,669,600**
- Booking rows (`is_booking=1`): **3,000,693**
- Booking share by rows: **7.97%**
- Events after expanding by `cnt`: **55,879,507**
- Click events after weighting by `cnt`: **52,833,029**
- Booking events after weighting by `cnt`: **3,046,478**
- Booking share by weighted events: **5.45%**
- Rows with `cnt > 1`: **9,579,178 = 25.43%**
- `cnt=1`: **74.57%** of rows
- Mean `cnt`:
  - click rows: **1.524**
  - booking rows: **1.015**
- Maximum observed `cnt`: **269**

### Interpretation

This is not a cosmetic difference. The same dataset gives a booking rate of 7.97% if every row has weight 1 and 5.45% if each row is expanded by `cnt`.

For product metrics, always name the denominator:

- `booking_row_rate`
- `booking_event_rate`
- `booking_session_rate`
- `bookers / active_users`

Do not call all four simply "conversion".

---

## 3. Data-quality problems found by the team

| Problem | Count / share | Recommended handling |
|---|---:|---|
| Missing `orig_destination_distance` | 13,525,001 / **35.90%** | Preserve NULL; add missingness flag. Do not impute in STG. |
| Missing `srch_ci` | 47,083 / **0.12%** | Preserve row; flag; exclude from lead/stay metrics. |
| Missing `srch_co` | 47,084 / **0.12%** | Preserve row; flag; exclude from stay metrics. |
| `check-in < event date` | 8,457 / **0.0225%** | Flag as invalid for lead-time metrics. |
| `check-out < check-in` | 798 / **0.0021%** | Strong invalid-date flag; quarantine for stay metrics. |
| `check-out == check-in` | 144,804 / **0.3844%** | Ambiguous; flag, do not automatically delete. |
| Exact duplicate rows | 969 / **0.0026%** | Preserve RAW; dedupe in CLEAN after audit. |
| `srch_adults_cnt = 0` | 70,979 / **0.1884%** | Flag; do not hard-delete in STG. |
| `srch_rm_cnt = 0` | 859 / **0.0023%** | Flag as suspicious. |
| adults + children = 0 | 68,634 / **0.1822%** | Flag as suspicious/invalid occupancy. |

A useful warning: suspicious rows sometimes become bookings:

- zero adults: 5,239 booking rows;
- zero rooms: 250 booking rows;
- zero travelers: 5,076 booking rows.

This is exactly why staging should add quality flags instead of destructively deleting records.

### Date anomalies

The event timestamps themselves span:

- `2013-01-07 00:00:02` to `2014-12-31 23:59:59`.

Most check-in/check-out dates fall in 2013–2015, but isolated values appear far in the future, including 2057 and 2557/2558. These are obvious anomalies. A simple hard rule such as `year <= 2015` is nevertheless too aggressive because legitimate searches for 2016 exist. Logical checks relative to `date_time` are preferable.

---

## 4. Cardinality and dimensional structure

Team EDA:

| Field | Unique values |
|---|---:|
| `site_name` | 45 |
| `posa_continent` | 5 |
| `user_location_country` | 237 |
| `user_location_region` | 1,008 |
| `user_location_city` | 50,447 |
| `channel` | 11 |
| `srch_destination_id` | 59,455 |
| `srch_destination_type_id` | 10 |
| `hotel_continent` | 7 |
| `hotel_country` | 213 |
| `hotel_market` | 2,118 |
| `hotel_cluster` | 100 |

Implications:

- low-cardinality fields are suitable for direct group comparisons;
- high-cardinality IDs should be analyzed through top-N, coverage, concentration, repeat rates and entity-level marts;
- full one-hot encoding of city/destination IDs is not a good generic analytical approach.

---

## 5. Important findings from external analyses

### 5.1 `cnt` already aggregates activity inside sessions

The competition field description says:

> `cnt`: number of similar events in the context of the same user session.

This is the most important external fact for our metric design. It tells us that the raw file has already lost some event-level granularity. `cnt` is an event multiplicity, **not a session identifier**.

Therefore:

- `SUM(cnt)` is closer to event volume than `COUNT(*)`;
- `COUNT(*)` is a count of aggregated records;
- neither directly gives the number of sessions;
- sessionization must be reconstructed from user timelines, with an explicit rule.

### 5.2 Date inconsistencies are a known property of the dataset

Other analyses independently found check-out dates earlier than check-in dates. One public notebook found 2,184 such cases in the competition test data as well. Another project explicitly removed spurious `check-out < check-in` rows before feature engineering.

This supports treating date inconsistency as a genuine source-data quality issue rather than an error introduced by our team's conversion to Parquet.

### 5.3 Derived temporal features repeatedly appear as useful

Public notebooks repeatedly derive:

- stay length: `srch_co - srch_ci`;
- booking/search lead time: `srch_ci - date_time`;
- event month;
- check-in month;
- day of week;
- hour of day;
- season / quarter;
- weekend indicators.

For analytics these are more useful than raw date strings and should be standardized once in CLEAN/SILVER rather than recalculated differently in every mart.

### 5.4 Destination and hotel geography are central

Several solutions build strong simple baselines from the most frequent hotel clusters **conditioned on `srch_destination_id`**, often weighting bookings more strongly than clicks.

That suggests the most useful analytical entity hierarchy is not only user-centric. We also need:

- destination-level demand;
- hotel market/country/continent demand;
- user-origin → destination flows;
- repeat destination behavior;
- destination-specific booking rate;
- top-cluster concentration within destination.

### 5.5 Hotel clusters are imbalanced

Public analyses show that the 100 `hotel_cluster` classes are not uniformly distributed. For business analytics, this means:

- raw cluster counts should be accompanied by shares/concentration;
- "top cluster" comparisons can be dominated by base rate;
- cluster-level conversion should have a minimum-volume threshold.

### 5.6 Simple linear correlation is not enough

Public work notes weak simple linear correlations with `hotel_cluster`; useful signal tends to come from categorical combinations and historical frequencies such as destination × cluster, user-location × destination, hotel market and temporal features.

For our EDA this means a correlation heatmap is secondary. Grouped rates, concentration, repeat behavior and conditional distributions are more informative.

### 5.7 `orig_destination_distance` missingness is semantic

The dataset description says NULL distance means the distance could not be calculated. This is not equivalent to zero distance.

Therefore:

- keep `NULL`;
- create `distance_is_missing`;
- do not replace with zero;
- any imputation belongs downstream and should be explicit.

Some public projects impute the distance using origin-region/hotel-market or origin-country/hotel-country aggregates. That can be useful for modeling, but it should **not** happen in staging because it destroys the distinction between observed and inferred distance.

### 5.8 Destination latent features

`destinations.csv` contains 149 latent features (`d1`…`d149`). One public notebook found that 3 PCA components retained about 61.6% of their variance.

This is relevant for ML and destination similarity, but not for staging. Staging should only validate key coverage and data types; dimensionality reduction belongs in a feature layer.

### 5.9 Dataset is not a production population census

The public project description explicitly notes that the released data are a random selection and are not representative of Expedia's overall statistics.

Therefore the dataset is excellent for:

- internal comparisons;
- metric prototyping;
- pipeline validation;
- behavioral hypotheses.

But values such as "mobile share = X%" or "Expedia conversion = Y%" should not be presented as present-day Expedia business KPIs.

---

## 6. What matters for the metrics we have been discussing

### 6.1 Sessions

Recommended definition for the first iteration:

A new reconstructed session starts for a user when the time gap from the previous logged row exceeds a threshold.

Do **not** freeze 30 minutes without testing. Run a sensitivity table for:

- 15 min
- 30 min
- 60 min
- 120 min

Compare:

- number of sessions;
- median rows per session;
- median weighted events (`SUM(cnt)`) per session;
- share of sessions with booking;
- share of sessions spanning multiple destinations;
- session duration distribution.

If 30→60 minutes causes little change while 15→30 changes a lot, 30 minutes is a reasonable plateau. If the metrics continue changing strongly, a simple timeout definition is unstable and should be refined with search-intent fields.

Important: because `cnt` is already session-context aggregation, reconstructed sessions are an approximation to the original Expedia sessions, not exact recovery.

### 6.2 Funnel / conversion

Keep at least three separate rates:

1. **Row booking rate**  
   `booking rows / all rows`

2. **Weighted-event booking rate**  
   `SUM(cnt * is_booking) / SUM(cnt)`

3. **Session booking rate**  
   `sessions containing booking / all reconstructed sessions`

Potentially also:

4. **Booker rate**  
   `users with ≥1 booking / active users`

These answer different questions.

### 6.3 Active users and frequency

Because hotel trips are infrequent, a short 30/90-day active-user window can be misleading. For this dataset the notebook should profile activity over longer windows and show:

- active users by month;
- active months per user;
- events per user;
- sessions per user;
- booking sessions per user;
- time between booking sessions.

Do not infer a production annual travel frequency from this sampled competition dataset.

### 6.4 RFM

Classic RFM is not fully available because the dataset has no booking price/revenue.

Use an **RF-style segmentation** first:

- **R**: days since last booking (and separately last event);
- **F**: booking sessions or bookings in the observation window;
- optional behavioral dimensions:
  - search sessions;
  - number of distinct destinations;
  - booking/session conversion;
  - mobile/package usage.

Do not fabricate `M` from `cnt`, stay length or distance: none is monetary value.

### 6.5 Useful product cuts

For each rate, include sufficient volume and compare:

- mobile vs desktop;
- package vs standalone;
- channel;
- point-of-sale / POS continent;
- user country / hotel country;
- domestic-ish vs cross-country/continent proxy;
- destination type;
- hotel continent/country/market;
- lead-time bucket;
- stay-length bucket;
- party composition;
- month / weekday.

---

## 7. Recommended staging/cleaning contract

### RAW — immutable

Keep original Parquet/CSV untouched.

### STG — type normalization + quality flags

Recommended columns to add:

- `event_ts`
- `checkin_date`
- `checkout_date`
- `distance_is_missing`
- `q_missing_checkin`
- `q_missing_checkout`
- `q_checkin_before_event`
- `q_checkout_before_checkin`
- `q_same_day_stay`
- `q_zero_adults`
- `q_zero_rooms`
- `q_zero_travelers`
- `q_extreme_future_date`
- `q_exact_duplicate` or duplicate group metadata
- `quality_issue_count`

Rules:

- no replacement of NULL distance with 0;
- no global mean imputation;
- no deletion of suspicious records;
- preserve original fields alongside normalized fields.

### CLEAN / SILVER

Here it is appropriate to:

- deduplicate exact source duplicates after audit;
- produce metric-valid flags such as:
  - `valid_for_lead_time`
  - `valid_for_stay_length`
  - `valid_for_party_metrics`;
- derive:
  - `lead_days`
  - `stay_nights`
  - `event_month`
  - `event_dow`
  - `event_hour`
  - `checkin_month`
  - `party_size`;
- reconstruct session IDs under a versioned rule, e.g. `session_rule_version = 'gap_30m_v1'`.

### MARTS

At minimum:

1. `mart_sessions`
2. `mart_user_activity`
3. `mart_user_rf`
4. `mart_funnel`
5. `mart_destination`
6. `mart_origin_destination`
7. `mart_data_quality_daily`

---

## 8. Additional checks worth adding beyond the team's current EDA

1. **Cross-field geography consistency**
   - site ↔ POS continent;
   - hotel country ↔ hotel continent;
   - user country/region/city nesting stability.

2. **Entity mapping stability**
   - whether the same `site_name` maps to more than one `posa_continent`;
   - whether the same hotel market maps to multiple hotel countries/continents;
   - whether the same user city appears under multiple region/country combinations.

3. **Time ordering per user**
   - negative gaps;
   - bursts with identical timestamps;
   - very long gaps;
   - session-threshold sensitivity.

4. **Distribution drift**
   - 2013 vs 2014 monthly changes;
   - channel/mobile/package shares;
   - destination and market concentration;
   - booking rate by month.

5. **`cnt` behavior**
   - high-`cnt` tail;
   - `cnt` by booking/click;
   - `cnt` by channel/mobile/package;
   - whether high `cnt` values cluster in specific IDs or periods.

6. **Booking consistency**
   - booking rows without any earlier click in the same reconstructed session;
   - sessions containing multiple booking rows;
   - multiple booked clusters/destinations in one session.

7. **User behavior**
   - users with only one active day;
   - active months;
   - repeat destination rate;
   - repeat hotel cluster rate;
   - booking frequency;
   - inter-booking time.

8. **Destination coverage**
   - train IDs missing from `destinations.csv`;
   - latent-feature nulls / duplicates;
   - coverage weighted by events and bookings.

9. **Concentration**
   - top-N share / HHI for destination, hotel market, hotel cluster and channels.

10. **Potential leakage / analytical validity**
    - distinguish event-time attributes from outcomes;
    - do not use future events when constructing historical user features;
    - use time-based splits for any predictive validation.

---

## 9. Recommended first cleaning decisions

### Safe to do early

- normalize types;
- parse dates;
- preserve raw columns;
- add quality flags;
- create semantic NULL flags;
- audit exact duplicates;
- calculate deterministic date features only when valid.

### Do not do in staging

- mean-impute `orig_destination_distance`;
- replace NULL with zero;
- delete all zero-adult rows;
- delete same-day stays;
- cap `cnt` without investigation;
- encode high-cardinality IDs;
- PCA of destination features;
- hard-code a session threshold without sensitivity analysis.

---

## 10. Sources

Team source:
- Uploaded `EDA.ipynb` supplied by the project team.

External sources reviewed:
- Expedia Hotel Recommendations competition: https://www.kaggle.com/c/expedia-hotel-recommendations
- Peeter Piksarv / Notebook Community: https://notebook.community/ppik/playdata/Kaggle-Expedia/Expedia%20Hotel%20Recommendations
- Muatik Expedia notebook: https://notebook.community/muatik/prp/expedia
- ProjectPro Expedia Hotel Recommendations: https://www.projectpro.io/project-use-case/expedia-hotel-recommendations
- Robert Zacchigna, Create Optimal Hotel Recommendations: https://robert-zacchigna.github.io/assets/notebooks/Create%20Optimal%20Hotel%20Recommendations.html
- Simone Antonelli, Expedia recommender project: https://siantonelli.github.io/projects/BigData/
- Shenoy, Wagle, Shaikh, “Kaggle Competition: Expedia Hotel Recommendations”: https://arxiv.org/abs/1703.02915

### Source-quality note

External notebooks use different subsets and sometimes booking-only samples. Their numerical distributions should not be merged with the full-data statistics from the team's notebook. I use them mainly to confirm data semantics, recurring quality problems, and useful analytical directions.
