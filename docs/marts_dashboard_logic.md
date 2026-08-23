# 03. Что должно быть под dashboard

## Страница 1 — Executive / Product

Источник: `mart_product_daily`, `mart_session_daily`.

KPI:
- row events;
- bookings;
- booking row conversion;
- active users;
- sessions;
- session booking conversion;
- mobile booking share;
- package booking share.

Charts:
- bookings по `date_key`;
- conversion по `date_key`;
- sessions и booking sessions;
- mobile/package shares.

Важно: conversion на KPI рассчитывать как `SUM(bookings)/SUM(row_events)`,
а не среднее дневных conversion.

## Страница 2 — Acquisition / Channel

Источник: `mart_channel_platform`.

Filters: `year_month`, `channel`, `platform_id`, `is_mobile`.

Charts:
- bookings по channel;
- conversion по channel;
- booking value proxy per active user;
- mobile vs desktop.

## Страница 3 — Destination

Источник: `mart_destination_performance`, опционально `mart_origin_destination`.

Обязательно использовать `meets_min_volume_flag` и `meets_booking_min_volume_flag`
для ranking по conversion, иначе наверх попадут tiny-sample направления.

Charts:
- top destinations by bookings;
- top destinations by conversion после volume filter;
- origin country → hotel country;
- distance / lead / stay profiles.

Encoded IDs нельзя превращать в выдуманные географические названия.

## Страница 4 — Customer / Retention

Источники:
- `mart_user_360`;
- `mart_booking_frequency`;
- `mart_booking_frequency_exact`;
- `mart_retention_cohort`.

Charts:
- booking-frequency distribution;
- 0/1/2/3/4+ segments;
- cohort retention heatmap;
- frequency vs sessions/active months.

`mart_user_360` тяжёлая (1.2M rows), поэтому для dashboard лучше использовать
агрегированные booking-frequency/cohort marts, а user_360 оставлять для drill-through.

## Страница 5 — Trip & Package

Источники:
- `mart_trip_profile`;
- `mart_package_profile`;
- `mart_travel_calendar_daily`.

Charts:
- conversion по lead-time bucket;
- conversion по stay-length bucket;
- conversion по party segment;
- package vs non-package;
- check-ins/check-outs по travel calendar.

## Страница 6 — Data Quality

Источники:
- `mart_data_quality_daily`;
- `mart_distance_quality`.

Charts:
- missing distance share;
- imputed distance share;
- invalid lead/stay;
- quality issue share;
- coverage vs MAE для вариантов distance imputation.

Эта страница нужна, чтобы показать: аналитические выводы сопровождаются контролем качества,
а не считаются на «чистом по умолчанию» источнике.
