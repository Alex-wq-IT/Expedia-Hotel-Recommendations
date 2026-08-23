# 04. Выводы по фактическим витринам

Все цифры ниже посчитаны из переданных CSV, без доступа к raw.

## Масштаб

- 37,669,324 event rows.
- 55,878,461 weighted events (`SUM(cnt)`).
- 3,000,689 booking rows.
- Общий booking row conversion: **7.97%**.
- Weighted booking event rate: **5.45%**.
- 1,198,786 пользователей; 813,985 имеют хотя бы одно бронирование
  (**67.9%**).
- 12,242,331 reconstructed sessions; booking-session rate **21.74%**.

## Повторные бронирования

Сегменты booking frequency:
- 0 bookings: 384,801 пользователей (**32.10%**);
- 1 booking: 315,681 (**26.33%**);
- 2 bookings: 168,059 (**14.02%**);
- 3 bookings: 95,501 (**7.97%**);
- 4+ bookings: 234,744 (**19.58%**).

Главный бизнес-смысл: почти треть пользователей ни разу не дошла до booking,
а примерно каждый пятый пользователь — repeat-heavy сегмент 4+ bookings.

## Mobile

- desktop booking row rate: **8.29%**;
- mobile booking row rate: **5.86%**;
- mobile формирует **13.49%** event rows, но только **9.92%** booking rows.

Это диагностический сигнал: mobile funnel заметно слабее desktop.
Причину нельзя установить только по marts; для causal вывода нужна дальнейшая детализация.

## Package

По `mart_package_profile`:
- non-package event conversion: **9.17%**;
- package event conversion: **4.43%**.

При этом package bookings составляют **13.67%** всех bookings.
Это не означает, что package «хуже» как продукт: группы могут различаться по lead time,
trip complexity и channel mix.

## Lead time

Conversion монотонно снижается с горизонтом планирования:
- same/next day: **15.48%**;
- 2–7 days: **11.69%**;
- 8–30: **8.53%**;
- 31–90: **6.23%**;
- 91+: **4.54%**.

## Stay length

- 1 ночь: **12.92%**;
- 2–3 ночи: **7.86%**;
- 4–7: **4.72%**;
- 8–14: **3.24%**;
- 15+: **2.47%**.

Чем длиннее поездка, тем ниже вероятность booking row в текущем event funnel.

## Party segment

По валидному trip-profile:
- solo: **12.40%**;
- family with children: **7.19%**;
- group: **7.06%**;
- couple: **6.91%**.

## Retention

Observed repeat-booking retention:
- month 1: **13.83%**;
- month 3: **11.23%**;
- month 6: **11.21%**.

Это **observed retention внутри конечного окна данных**, а не lifetime retention.
Поздние когорты имеют меньше доступных месяцев наблюдения.

## Destinations

По объёму bookings лидер среди volume-qualified destination IDs — `8250`
(97,637 bookings в сумме переданной витрины).
Названия не присваиваем, потому что `destination_id` закодирован и lookup с названием не предоставлен.

## Data quality

Средневзвешенно по дням:
- missing distance: **35.90%**;
- imputed distance: **13.02%**;
- хотя бы один quality issue: **36.35%**.

Quality issue в основном связан с missing distance; это не значит, что 36% строк надо удалить.
Флаги позволяют использовать строку в тех метриках, для которых она валидна.

## Distance imputation

На holdout лучший MAE среди проверенных комбинаций дает `city_destination`
при низком support threshold; например `min_support=5`:
coverage ~84.25%, MAE ~29.41.
Country-level варианты дают почти полное покрытие, но существенно больший error,
поэтому их не стоит автоматически использовать ради coverage.
