# 05. Проверки качества витрин

## Grain

Для каждой mart задан составной ключ. В `analysis/grain_validation.csv`:
- duplicate_grain_rows = 0 для всех 14 marts;
- null_grain_rows = 0 для всех 14 marts.

## Reconciliation

В `analysis/reconciliation_checks.csv` все проверки проходят:
- product totals = channel totals;
- product totals = destination totals;
- product totals = origin-destination totals;
- product totals = travel-calendar event totals;
- product totals = daily quality totals;
- user_360 users = booking-frequency users;
- user_360 bookings = product bookings.

Это сильная проверка: независимые агрегации разных grains сходятся к одному total.

## Rate domain

При приемке production build дополнительно проверять:
- все share/rate ∈ [0,1];
- counts >= 0;
- `returned_bookers <= cohort_users`;
- `booking_sessions <= sessions`;
- `bookings <= row_events/events`;
- `covered_rows <= holdout_rows`.

## Почему NULL не всегда ошибка

NULL в measure может быть ожидаем:
- у пользователя без bookings нет package booking share;
- в календарные даты без check-ins нет average stay/lead;
- у low-volume destination может отсутствовать среднее distance.

Критично отличать `NULL in grain key` от `NULL in optional measure`.
