# 02. Каталог витрин

| Витрина | Grain | Для чего | Источник | Строк |
|---|---|---|---|---:|
| `mart_product_daily` | event date | Главные product KPI по дням | fct_event + dim_date | 724 |
| `mart_session_daily` | session start date | Сессии, booking sessions, session conversion | fct_session | 724 |
| `mart_travel_calendar_daily` | calendar date | Events/booking date vs check-in/check-out calendar | dim_date + fct_event | 6,908 |
| `mart_channel_platform` | month × channel × platform × mobile | Каналы и платформы | fct_event + dim_platform | 11,720 |
| `mart_destination_performance` | month × destination × hotel market | Направления и hotel markets | fct_event | 502,728 |
| `mart_user_360` | user | Профиль пользователя, частота, recency-like показатели | fct_event + fct_session | 1,198,786 |
| `mart_origin_destination` | month × origin country × hotel country | Географические потоки | fct_event + location dimensions | 151,998 |
| `mart_trip_profile` | month × lead bucket × stay bucket × party | Профиль поездки | fct_event + session map | 2,399 |
| `mart_retention_cohort` | cohort month × month offset | Observed repeat booking retention | booking rows | 300 |
| `mart_booking_frequency` | booking-count bucket | Крупные сегменты по числу booking rows | mart_user_360 | 5 |
| `mart_booking_frequency_exact` | exact bookings | Точное распределение booking frequency | mart_user_360 | 101 |
| `mart_data_quality_daily` | event date | Мониторинг качества данных | fct_event quality flags | 724 |
| `mart_distance_quality` | imputation level × min support | Holdout-валидация distance imputation | distance validation output | 49 |
| `mart_package_profile` | month × package × lead × stay × party × channel × mobile | Package vs non-package поведение | fct_event | 72,280 |

## Базовые формулы

- `booking_row_rate = bookings / row_events` (или `bookings / events` в profile marts).
- `booking_weighted_event_rate = weighted_booking_events / weighted_events`.
- `package_booking_share = package bookings / bookings`.
- `session_booking_rate = booking_sessions / sessions`.
- `booking_retention_rate = returned_bookers / cohort_users`.

## Правило агрегации

Суммируем только аддитивные меры: rows/events/bookings/users в пределах grain, booking value proxy total.
Rate/share нельзя бездумно суммировать. Для общего conversion надо пересчитать ratio из числителя и знаменателя.
Например общий booking conversion: `SUM(bookings) / SUM(row_events)`, а не `AVG(booking_row_rate)` по месяцам.

## Ключи

Результат `analysis/grain_validation.csv`: во всех 14 переданных marts нет повторов по заявленному grain.