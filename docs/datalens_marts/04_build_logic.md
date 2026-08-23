# Логика сборки и формулы

## Репродукция

На полном Expedia источнике:

```powershell
python .\tools\build_core.py
python .\tools\build_analytics.py
python .\tools\validate_datalens_marts.py
```

`build_core.py` создаёт обработанный CORE. `build_analytics.py` создаёт аналитические marts. Для DataLens из набора выбираются семь mart из этого пакета.

## Формулы

### Product
- `booking_row_rate = bookings / row_events`
- общий KPI: `SUM(bookings) / SUM(row_events)`
- `booking_weighted_event_rate = weighted_booking_events / weighted_events`
- `mobile_row_share = mobile row events / row_events`
- `mobile_booking_share = mobile booking rows / bookings`

### Sessions
- `session_booking_rate = booking_sessions / sessions`
- KPI: `SUM(booking_sessions) / SUM(sessions)`

Sessionization:
1. события группируются по `user_id`;
2. сортировка `event_ts, event_id`;
3. первая строка пользователя открывает сессию;
4. новая сессия, если `event_ts - previous_event_ts > 30 minutes`;
5. `cnt` не влияет на границы сессии.

### Channel / platform
Grain: month × channel × platform × mobile.
- `weighted_events = SUM(cnt)`
- conversion с учетом cnt → `booking_weighted_event_rate`

### Trip profile
Категориальные buckets:
- lead time;
- stay length;
- party segment.
Все графики DataLens с подписью «с учетом cnt» используют weighted conversion.

### Retention
- cohort = месяц первого booking пользователя;
- offset = число месяцев после первого booking;
- `booking_retention_rate = returned_bookers / cohort_users`.

### Travel calendar
События разделяются по:
- дате действия;
- дате check-in;
- дате check-out.

### Destination
Grain: month × destination × hotel market.
Conversion ranking допустим только после фильтра минимального объёма.
