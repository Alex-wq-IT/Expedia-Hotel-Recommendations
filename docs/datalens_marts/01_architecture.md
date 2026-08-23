# Обработанные данные и витрины — архитектура

## Scope

Этот пакет закрывает только пункт:

**«Обработанные данные и витрины: структура витрин и логика их сборки; сами витрины под капотом дашборда и выводов».**

Новый BI-инструмент не строится. Существующий Yandex DataLens остаётся визуальным слоем.

## Поток данных

```text
Expedia Parquet
  train_full.parquet
  test.parquet
  destinations.parquet
        |
        v
RAW (источник не изменяется)
        |
        v
STAGING
  - приведение типов
  - парсинг date_time / srch_ci / srch_co
  - quality flags
  - фиксация exact duplicates
        |
        v
CORE
  - fct_event
  - calendar / platform / destination dimensions
  - reconstructed sessions
        |
        v
7 DATALENS MARTS
  - mart_product_daily
  - mart_session_daily
  - mart_channel_platform
  - mart_trip_profile
  - mart_retention_cohort
  - mart_travel_calendar_daily
  - mart_destination_performance
        |
        v
Yandex DataLens
```

## Главные семантические правила

1. `COUNT(*)` — число строк событий (`row_events`).
2. `SUM(cnt)` — объём событий с учётом агрегирующего поля источника (`weighted_events`).
3. Эти две семантики нельзя смешивать.
4. Row conversion = `SUM(bookings) / SUM(row_events)`.
5. Weighted conversion использует `cnt` и хранится как `booking_weighted_event_rate`.
6. Rate/share нельзя суммировать и обычно нельзя усреднять без весов: общий rate пересчитывается из числителя и знаменателя.
7. Сессия реконструируется внутри пользователя: новая сессия при gap **строго > 30 минут**.
8. `destination_id`, `hotel_market_id`, `channel` — кодированные ID; им нельзя придумывать реальные названия без mapping-справочника.
9. `booking_value_proxy` — не деньги и не revenue.

## Почему именно 7 витрин

По предоставленным 5 листам DataLens все KPI и графики покрываются этими семью mart. Дополнительные marts исходного проекта не являются обязательными для этого дашборда.
