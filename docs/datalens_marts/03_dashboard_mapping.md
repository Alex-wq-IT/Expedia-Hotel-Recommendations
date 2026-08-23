# DataLens → marts: что лежит под каждым графиком

## 1. Обзор продукта

**`mart_product_daily`**
- KPI «Среднее число пользователей в день» → `AVG(active_users)`.
- KPI «Бронирования» → `SUM(bookings)`.
- KPI «Конверсия в бронирование» → `SUM(bookings) / SUM(row_events)`.
- «Динамика аудитории и бронирований» → `active_users`, `bookings` по времени.
- «Доля mobile в трафике и бронированиях» → `mobile_row_share`, `mobile_booking_share`.
- «Динамика конверсии» → ratio из `bookings` и `row_events`.

**`mart_session_daily`**
- KPI «Сессии» → `SUM(sessions)`.
- KPI «Доля сессий с бронированием» → `SUM(booking_sessions) / SUM(sessions)`.
- «Динамика всех сессий и сессий с бронированием» → `sessions`, `booking_sessions`.

## 2. Каналы и устройства

**`mart_channel_platform`**

Grain: `year_month × channel × platform_id × is_mobile`.

Используется для:
- конверсии по каналам;
- объёма активности по каналам;
- Desktop vs Mobile;
- динамики Desktop/Mobile;
- фильтров по периоду, каналу и типу устройства.

На графиках с подписью «с учетом cnt» используются `weighted_events` и `booking_weighted_event_rate`.

## 3. Сценарии поездок

**`mart_trip_profile`**

Grain: `year_month × lead_time_bucket × stay_length_bucket × party_segment`.

Используется для:
- conversion по сроку планирования;
- conversion по длительности проживания;
- heatmap lead time × stay length;
- объёма активности по lead-time;
- conversion по составу путешественников;
- временной динамики party segment.

## 4. Удержание

**`mart_retention_cohort`**

Grain: `cohort_month × months_since_first_booking`.

- `cohort_users` — размер когорты пользователей по месяцу первого booking.
- `returned_bookers` — пользователи когорты, сделавшие booking на заданном offset.
- `booking_retention_rate = returned_bookers / cohort_users`.

Питает:
- новых пользователей с первым бронированием;
- линии 1/3/6 месяцев;
- cohort heatmap;
- retention по месяцу жизни когорты;
- выбранные когортные линии.

Это **observed repeat-booking retention**, ограниченный окном наблюдения.

## 5. География и календарь

**`mart_travel_calendar_daily`**
- среднее число check-ins в день по месяцам;
- bookings и check-ins по дням недели;
- день недели можно вычислять из `full_date`.

**`mart_destination_performance`**
- scatter «объём × conversion» по гостиничным рынкам;
- таблица крупных рынков с низкой conversion;
- для conversion-ranking нужно применять volume filter (`meets_min_volume_flag` / `meets_booking_min_volume_flag`).

`hotel_market_id` и `destination_id` — encoded IDs.
