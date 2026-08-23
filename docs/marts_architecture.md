# 01. Архитектура обработанных данных

## Цель слоя

Слой `processed/CORE → MARTS` превращает сырые event-логи Expedia в стабильные аналитические сущности,
которые можно напрямую подключать к dashboard. В репозитории принята схема:

`source Parquet → RAW → STAGING → CORE → MARTS → ClickHouse → Superset`.

Главный принцип: **не считать бизнес-метрики напрямую из raw в каждом графике**.
Семантика фиксируется один раз в CORE/MARTS, после чего BI только агрегирует готовые поля.

## Зерно исходных данных

Одна строка train — агрегированное взаимодействие пользователя. Поле `cnt` означает кратность,
поэтому:
- `row_events = COUNT(*)` — число строк/логов;
- `weighted_events = SUM(cnt)` — число событий с учетом кратности;
- `bookings = COUNT(*) WHERE is_booking = 1` — booking rows.

По фактическим витринам:
- row events: **37,669,324**
- weighted events: **55,878,461**
- bookings: **3,000,689**
- пользователей: **1,198,786**

## STAGING

STAGING сохраняет источник и добавляет техническую обработку:
- парсинг `date_time`, `srch_ci`, `srch_co`;
- quality flags;
- признаки валидности lead time / stay length;
- обнаружение exact duplicates;
- сохранение исходного distance.

Логически неверная дата не заставляет удалять всю строку: строка остается пригодной для channel/mobile анализа,
но исключается из метрик, где нужна корректная дата.

## CORE

CORE задает звездообразную модель:
- `fct_event` — основной факт;
- `fct_booking` — booking rows;
- `dim_date`, `dim_user`, `dim_user_location`, `dim_platform`,
  `dim_destination`, `dim_destination_type`, `dim_hotel_market`,
  `dim_hotel_cluster`, `dim_search_params`;
- `event_session_map`, `fct_session` — reconstructed sessions.

Сессия: события одного пользователя, новая сессия начинается после gap > 30 минут.
Это аналитическая реконструкция, а не исходный Expedia session id.

## MARTS

MARTS уже имеют фиксированное зерно и предназначены для конкретных аналитических вопросов.
В BI нельзя join-ить две витрины «по удобному полю», если их grain различается.
Лучше выбирать одну витрину на один визуальный объект.

## Почему такая схема хороша

1. Воспроизводимость: metric logic хранится в коде, а не только в dashboard.
2. Производительность: dashboard читает агрегаты вместо десятков миллионов event rows.
3. Аудит: каждая цифра сверяется между независимыми marts.
4. Защита от fan-out: фиксирован grain и ключ каждой витрины.
5. Разделение event-time и travel-time: product trend и travel calendar не смешиваются.
