# Короткий сценарий защиты

## Что было сделано

«Моя часть — обработанные данные и аналитические витрины под существующим Yandex DataLens. Я не перестраивал dashboard: я зафиксировал единый слой данных, из которого воспроизводятся его KPI, графики и выводы».

## Архитектура

`Expedia Parquet → RAW → STAGING → CORE → 7 MARTS → Yandex DataLens`

RAW не меняется. В STAGING приводятся типы и ставятся quality flags. В CORE фиксируется семантика событий и реконструированных сессий. MARTS агрегируют данные ровно до grain, необходимого конкретным листам DataLens.

## Почему нельзя считать всё прямо из train

Train содержит десятки миллионов строк и поле `cnt`. Если каждый график сам реализует свои формулы, легко смешать `COUNT(*)` и `SUM(cnt)` и получить расходящиеся KPI.

## Семь витрин

- Product → `mart_product_daily`
- Sessions → `mart_session_daily`
- Channels/devices → `mart_channel_platform`
- Trip scenarios → `mart_trip_profile`
- Retention → `mart_retention_cohort`
- Calendar → `mart_travel_calendar_daily`
- Hotel markets → `mart_destination_performance`

## Главные проверки

«У каждой mart зафиксирован grain. В фактических снимках нет дублей и NULL по grain. Общие event rows, weighted events и bookings независимо совпадают в product, channel, destination и calendar marts».

## KPI

- 3,000,689 bookings.
- Row booking conversion ≈ 7.97%.
- 12,242,331 reconstructed sessions.
- Session booking rate ≈ 21.74%.
- Среднее active users/day ≈ 13,707.

## Важные ограничения

- `cnt` — multiplicity, поэтому row и weighted metrics различаются.
- session id реконструирован аналитическим правилом gap > 30 минут.
- encoded IDs нельзя называть реальными географическими объектами без mapping.
- retention ограничен окном наблюдения.
- `booking_value_proxy` — не revenue.
