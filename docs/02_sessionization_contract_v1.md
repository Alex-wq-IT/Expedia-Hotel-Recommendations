# Sessionization Contract v1

## Status

Draft implementation contract.

The session layer is a reconstructed analytical approximation because the source does not contain a true `session_id`.

`cnt` represents multiplicity of similar events in session context but is **not** itself a session identifier.

---

# 1. Scope

For v1, reconstruct sessions only on the source population that contains interaction history and booking outcomes suitable for behavioral analysis.

Current default scope:

`source_dataset = 'train'`

Do not use booking-only / outcome-incomplete test data to estimate:
- session count;
- session conversion;
- time to booking;
- clicks/events before booking.

---

# 2. Session rule v1

Use a deterministic inactivity-gap rule.

**Version name:**

`gap_30m_v1`

For each user:

1. filter to the valid sessionization source population;
2. order rows by:
   - `event_ts`;
   - `event_id` as deterministic tie-break;
3. compute previous event timestamp;
4. start a new session if:
   - this is the first row for the user; or
   - time gap from previous row is strictly greater than 30 minutes.

Same-timestamp rows remain in the same session.

`cnt` does not affect session boundaries.

Destination changes do not automatically split a session.

Channel changes do not automatically split a session.

Search-parameter changes do not automatically split a session.

This is intentional: a user may compare multiple destinations/options in one real browsing session.

---

# 3. Sensitivity report

Although v1 is fixed at 30 minutes, produce a non-materialized comparison for:

- 15 min;
- 30 min;
- 60 min;
- 120 min.

For each threshold report:

- session count;
- sessions per active user;
- median rows per session;
- median `SUM(cnt)` per session;
- median and p90 session duration;
- share of one-row sessions;
- booking-session rate;
- share of sessions with multiple destinations;
- share of sessions with multiple booking rows.

Do **not** automatically change `gap_30m_v1` based on this report.

If 30-minute behavior looks pathological, record an open question for v2.

This keeps the implementation deterministic and prevents the local agent from redesigning the rule.

---

# 4. Persistence model

Do not add a physical `session_id` directly into the existing `fct_event` file.

Create two new CORE objects.

## `core.event_session_map`

Grain:

**one event = one session assignment under one session-rule version**

Fields:

- `event_id`
- `session_id`
- `session_rule_version`

Primary key:

`(event_id, session_rule_version)`

This allows future `gap_60m_v2` or another rule without rebuilding or mutating the event fact.

## `core.fct_session`

Grain:

**one reconstructed user session under one session-rule version**

Primary key:

`session_id`

---

# 5. Deterministic session ID

Recommended session ID input:

- `session_rule_version`
- `source_dataset`
- `user_id`
- first `event_id` in the session

Example conceptual key:

`hash('gap_30m_v1', source_dataset, user_id, first_event_id)`

The exact hash implementation may follow existing project conventions.

The ID must be reproducible across repeated builds of the same event data.

---

# 6. Required `fct_session` fields

## Identity

- `session_id`
- `session_rule_version`
- `user_id`
- `source_dataset`

## Time

- `session_start_ts`
- `session_end_ts`
- `session_date_key`
- `session_start_hour_key`
- `session_duration_seconds`

`session_date_key` is the date of `session_start_ts`.

## Activity

- `row_count`
- `weighted_event_count = SUM(cnt)`
- `distinct_destination_count`
- `distinct_hotel_market_count`
- `distinct_search_params_count`

## Booking

- `has_booking`
- `booking_row_count`
- `first_booking_ts`
- `time_to_first_booking_seconds`
- `booking_value_proxy_total`
- `package_booking_count`

For sessions without booking:
- `has_booking = false`
- booking time fields are NULL
- BVP total = 0

## Entry / exit context

- `first_channel`
- `last_channel`
- `first_platform_id`
- `last_platform_id`
- `first_destination_id`
- `last_destination_id`
- `first_is_mobile`
- `last_is_mobile`

These are descriptive session attributes, not causal attribution.

---

# 7. Session metrics

Canonical definitions for the future MART layer:

## Session booking rate

`sessions with has_booking = 1 / all reconstructed sessions`

Do not call row booking rate or weighted-event booking rate the same metric.

## Events per session

Keep both:

- `row_count`
- `weighted_event_count`

because the source aggregates similar events through `cnt`.

## Time to booking

`first_booking_ts - session_start_ts`

Only for sessions with a valid booking timestamp.

## Multi-intent session

Optional descriptive flag:

`distinct_destination_count > 1`

Do not split such sessions automatically.

---

# 8. Validation

Required checks:

- every train `fct_event.event_id` has exactly one mapping for `gap_30m_v1`;
- no event maps to multiple v1 sessions;
- session start <= session end;
- session duration >= 0;
- session row counts sum to the number of eligible events;
- session weighted-event counts sum to `SUM(cnt)` of eligible events;
- booking-row counts sum to eligible booking rows;
- no session contains multiple users;
- no session crosses source datasets;
- first/last event IDs actually belong to the mapped session.

Report:
- number of eligible events;
- number of sessions;
- number of users;
- booking sessions;
- one-row sessions;
- max session duration;
- p50/p90/p99 duration.

---

# 9. What sessionization does NOT mean

A reconstructed session is not guaranteed to equal Expedia's original internal session.

It is an analytical approximation.

Do not interpret:
- `session_id` as source truth;
- a 30-minute boundary as a business fact;
- multiple destinations as separate sessions;
- `search_params_id` as session identity.

---

# 10. Out of scope

Not part of v1:

- intent/session sub-segmentation;
- ML-based session boundary detection;
- cross-device identity resolution;
- attribution modelling;
- journey stitching across users;
- merging train and test into one behavioral timeline.
