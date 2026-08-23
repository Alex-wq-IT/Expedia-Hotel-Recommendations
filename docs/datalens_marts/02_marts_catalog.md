# Каталог 7 витрин DataLens

| Витрина | Grain | Строк | Лист DataLens |
|---|---|---:|---|
| `mart_product_daily` | date_key | 724 | Обзор продукта |
| `mart_session_daily` | date_key | 724 | Обзор продукта |
| `mart_channel_platform` | year_month × channel × platform_id × is_mobile | 11,720 | Каналы и устройства |
| `mart_trip_profile` | year_month × lead_time_bucket × stay_length_bucket × party_segment | 2,399 | Сценарии поездок |
| `mart_retention_cohort` | cohort_month × months_since_first_booking | 300 | Удержание |
| `mart_travel_calendar_daily` | date_key | 6,908 | География и календарь |
| `mart_destination_performance` | year_month × destination_id × hotel_market_id | 502,728 | География и календарь |

## Поля

### `mart_product_daily`

**Grain:** `date_key`

Поля:
- `date_key`
- `active_users`
- `row_events`
- `weighted_events`
- `bookings`
- `bookers`
- `booking_row_rate`
- `booking_weighted_event_rate`
- `booker_rate`
- `booking_value_proxy_total`
- `booking_value_proxy_per_active_user`
- `avg_booking_value_proxy_per_booking`
- `mobile_row_share`
- `mobile_booking_share`
- `package_booking_share`
- `avg_valid_lead_days`
- `avg_valid_stay_nights`
- `avg_distance_filled`
- `distance_imputed_share`

### `mart_session_daily`

**Grain:** `date_key`

Поля:
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

### `mart_channel_platform`

**Grain:** `year_month × channel × platform_id × is_mobile`

Поля:
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

### `mart_trip_profile`

**Grain:** `year_month × lead_time_bucket × stay_length_bucket × party_segment`

Поля:
- `year_month`
- `lead_time_bucket`
- `stay_length_bucket`
- `party_segment`
- `users`
- `events`
- `weighted_events`
- `bookings`
- `booking_row_rate`
- `booking_weighted_event_rate`
- `package_share`
- `mobile_share`
- `booking_value_proxy_total`
- `sessions`
- `booking_sessions`
- `session_booking_rate`

### `mart_retention_cohort`

**Grain:** `cohort_month × months_since_first_booking`

Поля:
- `cohort_month`
- `months_since_first_booking`
- `cohort_users`
- `returned_bookers`
- `booking_retention_rate`
- `bookings`
- `booking_value_proxy_total`

### `mart_travel_calendar_daily`

**Grain:** `date_key`

Поля:
- `date_key`
- `full_date`
- `year`
- `month`
- `year_month`
- `events_on_date`
- `weighted_events_on_date`
- `bookings_made_on_date`
- `checkins_on_date`
- `checkouts_on_date`
- `booking_value_proxy_for_checkins`
- `package_checkins`
- `avg_stay_nights_for_checkins`
- `avg_lead_days_for_checkins`

### `mart_destination_performance`

**Grain:** `year_month × destination_id × hotel_market_id`

Поля:
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
- `meets_min_volume_flag`
- `meets_booking_min_volume_flag`
