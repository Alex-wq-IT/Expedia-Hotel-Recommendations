# Analytical MARTS — Draft v0

## Status

Raw proposal for review.

Nothing in this document should be materialized until the user approves the list and grain.

The goal is to provide a compact business layer over CORE without exposing raw dimensional joins to DataLens.

---

# Design principles

1. MARTS read from CORE only.
2. Every MART has one explicit grain.
3. Every rate has an explicit denominator.
4. Train/test populations are not silently mixed.
5. `COUNT(*)`, `SUM(cnt)`, sessions, users and bookings remain separate concepts.
6. `booking_value_proxy` is a relative business score, not money.
7. Session metrics require `gap_30m_v1`.
8. Date roles remain explicit: event date, check-in date, check-out date.

---

# Tier A — recommended first marts

These are the strongest candidates for the first dashboard.

## A1. `mart_product_daily`

**Priority:** MUST HAVE

**Source:** interaction-complete train population

**Grain:** one row per `event_date`

Purpose:
overall product health and dynamics.

Fields:

### Keys
- `date_key`

### Volume
- `active_users`
- `row_events`
- `weighted_events`
- `bookings`
- `bookers`

### Conversion
- `booking_row_rate = bookings / row_events`
- `booking_weighted_event_rate = SUM(cnt * is_booking) / SUM(cnt)`
- `booker_rate = bookers / active_users`

### Business value
- `booking_value_proxy_total`
- `booking_value_proxy_per_active_user`
- `avg_booking_value_proxy_per_booking`

### Mix
- `mobile_row_share`
- `mobile_booking_share`
- `package_booking_share`

### Trip characteristics
- `avg_valid_lead_days`
- `avg_valid_stay_nights`
- `avg_distance_filled`
- `distance_imputed_share`

Use:
main KPI page and time series.

---

## A2. `mart_session_daily`

**Priority:** MUST HAVE after sessionization

**Source:** `core.fct_session`, rule `gap_30m_v1`

**Grain:** one row per `session_date`

Fields:

- `date_key`
- `active_users`
- `sessions`
- `booking_sessions`
- `session_booking_rate`
- `sessions_per_user`
- `avg_rows_per_session`
- `avg_weighted_events_per_session`
- `median_session_duration_seconds`
- `avg_time_to_first_booking_seconds`
- `multi_destination_session_share`
- `booking_value_proxy_total`
- `booking_value_proxy_per_session`

Use:
behavior / friction / "did a session satisfy travel intent?" analysis.

---

## A3. `mart_travel_calendar_daily`

**Priority:** MUST HAVE

**Grain:** one calendar day

Purpose:
use the role-playing date dimension to compare product activity and actual travel timing.

Fields:

- `date_key`

Event-side:
- `events_on_date`
- `weighted_events_on_date`
- `bookings_made_on_date`

Travel-side:
- `checkins_on_date`
- `checkouts_on_date`
- `booking_value_proxy_for_checkins`
- `package_checkins`
- `avg_stay_nights_for_checkins`
- `avg_lead_days_for_checkins`

Use:
three seasonality curves:
- searches/activity;
- check-ins;
- check-outs.

This mart directly serves the requested seasonality analysis.

---

## A4. `mart_channel_platform`

**Priority:** MUST HAVE

**Source:** train

**Grain:**

`month x channel x platform_id x is_mobile`

Fields:

- `year_month`
- `channel`
- `platform_id`
- `is_mobile`
- `active_users`
- `row_events`
- `weighted_events`
- `bookings`
- `booking_row_rate`
- `booking_weighted_event_rate`
- `booking_value_proxy_total`
- `booking_value_proxy_per_active_user`
- `package_booking_share`
- `avg_valid_lead_days`
- `avg_valid_stay_nights`

Future external extension:
- `cac_proxy`
- `unit_economics_proxy`

Do not fabricate CAC from current data.

---

## A5. `mart_destination_performance`

**Priority:** MUST HAVE

**Source:** train

**Grain:**

`month x destination_id x hotel_market_id`

Fields:

- `year_month`
- `destination_id`
- `hotel_market_id`
- `active_users`
- `row_events`
- `weighted_events`
- `bookings`
- `bookers`
- `booking_row_rate`
- `booking_weighted_event_rate`
- `package_booking_share`
- `booking_value_proxy_total`
- `avg_distance_filled`
- `avg_valid_lead_days`
- `avg_valid_stay_nights`

Add minimum-volume flags for dashboard ranking.

Use:
- top demand destinations;
- top markets;
- high-volume low-conversion areas;
- growth opportunities.

---

## A6. `mart_user_360`

**Priority:** MUST HAVE

**Source:** train events + sessions

**Grain:** one row per user

Fields:

### Lifecycle
- `user_id`
- `first_seen_date`
- `last_seen_date`
- `active_days`
- `active_months`

### Activity
- `row_events`
- `weighted_events`
- `sessions`
- `booking_sessions`

### Booking
- `bookings`
- `first_booking_date`
- `last_booking_date`
- `booking_value_proxy_total`
- `avg_booking_value_proxy`
- `package_bookings`
- `package_booking_share`

### Behavior
- `mobile_event_share`
- `distinct_destinations`
- `distinct_hotel_markets`
- `avg_valid_lead_days`
- `avg_valid_stay_nights`
- `avg_distance_filled`

### RF-style
- `days_since_last_booking`
- `booking_frequency`
- `session_frequency`

Use:
user segmentation, repeat behavior and future RFM-like analysis.

---

# Tier B — likely useful marts

## B1. `mart_origin_destination`

**Priority:** HIGH

**Grain:**

`month x user_location_id x destination_id`

Potentially too granular for BI.

For dashboard use, consider an aggregate view:

`month x user_country x hotel_country`

Fields:

- users
- row events
- weighted events
- bookings
- booking rate
- booking value proxy
- avg distance
- package share
- avg stay
- avg lead time

Use:
travel flows and geographic demand.

---

## B2. `mart_trip_profile`

**Priority:** HIGH

**Grain:**

`month x lead_time_bucket x stay_length_bucket x party_segment`

Recommended buckets should be fixed in a separate metric contract.

Example dimensions:

### Lead time
- same/next day
- 2-7
- 8-30
- 31-90
- 91+

### Stay
- 1 night
- 2-3
- 4-7
- 8-14
- 15+

### Party
- solo
- couple
- family_with_children
- group
- invalid/unknown excluded from party metrics

Fields:
- users
- events
- bookings
- booking rates
- package share
- mobile share
- BVP
- sessions
- session booking rate

Use:
product hypotheses about travel intent.

---

## B3. `mart_retention_cohort`

**Priority:** HIGH

**Source:** train bookings

**Grain:**

`first_booking_month x months_since_first_booking`

Fields:

- `cohort_month`
- `months_since_first_booking`
- `cohort_users`
- `returned_bookers`
- `booking_retention_rate`
- `bookings`
- `booking_value_proxy_total`

Important:
the competition sample is not a full lifetime observation window, so label this as observed cohort repeat-booking behavior, not true lifetime retention.

---

## B4. `mart_booking_frequency`

**Priority:** MEDIUM

**Grain:**

`booking_count_bucket`

Fields:
- users
- user_share
- avg sessions
- avg active_months
- avg BVP
- package share

Suggested buckets:
- 0
- 1
- 2
- 3
- 4+

This is the clean version of the proposed:
"visited but never booked -> booked once -> twice -> three times..."

It is a frequency distribution, not a funnel.

---

# Tier C — optional / QA marts

## C1. `mart_data_quality_daily`

**Priority:** OPTIONAL

**Grain:** event date

Fields:
- rows
- missing distance share
- imputed distance share
- invalid lead-time share
- invalid stay share
- zero-party share
- duplicate share

Useful internally, not necessarily for final dashboard.

---

## C2. `mart_distance_quality`

**Priority:** OPTIONAL

**Grain:** imputation level

Fields:
- imputed rows
- support statistics
- holdout coverage
- MAE
- median AE
- p90 AE

Use only for technical appendix / curator discussion.

---

# Potential 2015 mart — blocked decision

## `mart_booking_2015_profile`

Current CORE treats `fct_booking` as train-only.

If the DWH contract explicitly confirms that every test row is a booking observation, a separate booking-only 2015 profile can be built.

Possible grain:
- month;
- user geography;
- destination;
- channel/platform.

It may compare the **structure of bookings** between 2014 and 2015.

It must NOT be used to calculate:
- 2015 booking conversion;
- 2015 session conversion;
- 2015 click/event traffic;
- 2015 DAU of the full product population.

Do not materialize this mart until test semantics are formally approved.

---

# Proposed first implementation order

After approval:

1. `mart_product_daily`
2. `mart_travel_calendar_daily`
3. sessionization
4. `mart_session_daily`
5. `mart_channel_platform`
6. `mart_destination_performance`
7. `mart_user_360`
8. `mart_origin_destination`
9. `mart_trip_profile`
10. `mart_retention_cohort`
11. optional marts

---

# Recommended dashboard mapping

## Page 1 — Product overview
- `mart_product_daily`
- `mart_session_daily`

## Page 2 — Seasonality
- `mart_travel_calendar_daily`

## Page 3 — Channel & platform
- `mart_channel_platform`

## Page 4 — Geography & demand
- `mart_destination_performance`
- `mart_origin_destination`

## Page 5 — Customer behavior
- `mart_user_360`
- `mart_retention_cohort`
- `mart_booking_frequency`

## Page 6 — Search / trip behavior
- `mart_trip_profile`

---

# Questions to review before materialization

1. Keep both row and `cnt`-weighted booking rates in the dashboard, or choose one canonical headline metric?
2. Is `Bookings per Active User` still a secondary KPI next to Booking Value Proxy?
3. Should channel/platform grain be daily or monthly?
4. Is destination x hotel-market too granular for the final BI layer?
5. Which geography is the main origin view: country, region or city?
6. Do we want booking cohorts by first-ever observed booking or first booking in each calendar year?
7. Which trip-profile buckets should be canonical?
8. Do we formally accept test rows as booking-only 2015 observations for a separate profile mart?
