# 06. Сценарий защиты проекта

## 1. Что была за задача

«Нужно было построить обработанный аналитический слой и витрины, которые являются
единственным источником метрик для dashboard и выводов».

## 2. Почему нельзя строить dashboard прямо на train

Train содержит десятки миллионов строк, `cnt` агрегирует несколько событий,
а часть дат/расстояний имеет проблемы качества. Если каждый график будет писать
свою логику, метрики начнут расходиться.

## 3. Архитектура

Показываю схему:

`Parquet → RAW → STAGING → CORE → MARTS → ClickHouse → Superset`.

RAW immutable. STAGING парсит и флагирует. CORE фиксирует факты/измерения и семантику.
MARTS отвечают на конкретные бизнес-вопросы.

## 4. Самая важная семантика

«Я различаю COUNT(*) и SUM(cnt). Поэтому у проекта есть row events и weighted events.
Booking conversion тоже имеет row-based и weighted версию».

Это хороший вопрос на защите: если спросили, зачем два вида событий — объяснить `cnt`.

## 5. Сессии

«В исходнике нет надежного session id, поэтому мы реконструируем сессии:
для одного user сортируем события, gap > 30 минут открывает новую сессию.
Это аналитическое допущение, версия правила хранится явно».

## 6. Витрины

Не перечислять 14 таблиц без смысла. Группировать:
- product/session/calendar;
- channel/destination/geography;
- customer/retention/frequency;
- trip/package;
- data quality.

Для каждой назвать grain и ответ на бизнес-вопрос.

## 7. Контроль

«Я проверяю не только schema, но и reconciliation:
общие bookings из product mart должны совпадать с суммой bookings по channels,
destinations и user_360».

Это доказывает отсутствие потерь/fan-out в агрегациях.

## 8. Главные фактические выводы

1. Общий booking row conversion ≈ 7.97%.
2. Mobile conversion ≈ 5.86% против desktop ≈ 8.29%.
3. 32.1% пользователей не имеют bookings, 19.6% имеют 4+.
4. Чем дальше lead time, тем ниже conversion.
5. Чем длиннее stay, тем ниже conversion.
6. Month-1 observed repeat-booking retention ≈ 13.8%.
7. Missing distance велик, поэтому distance анализ сопровождается imputation-quality mart.

## 9. Ограничения

- `booking_value_proxy` — не деньги/revenue.
- encoded destination/channel IDs нельзя называть реальными объектами без mapping.
- cohort retention ограничен окном наблюдения.
- dashboard correlations не доказывают causal effect.

## 10. Что конкретно сделал я

«Я зафиксировал grain, формулы, собрал/проверил marts, сделал BI registry,
reconciliation checks и связал каждый dashboard chart с конкретной mart.
Таким образом выводы можно воспроизвести вне dashboard».
