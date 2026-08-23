# Валидация фактических 7 витрин

Проверка выполнена на приложенных CSV-снимках.

## Grain

| Mart | Rows | Duplicate grain rows | Null grain rows |
|---|---:|---:|---:|
| `mart_product_daily` | 724 | 0 | 0 |
| `mart_session_daily` | 724 | 0 | 0 |
| `mart_channel_platform` | 11,720 | 0 | 0 |
| `mart_trip_profile` | 2,399 | 0 | 0 |
| `mart_retention_cohort` | 300 | 0 | 0 |
| `mart_travel_calendar_daily` | 6,908 | 0 | 0 |
| `mart_destination_performance` | 502,728 | 0 | 0 |

Результат: **7/7 marts проходят grain-check**.

## Reconciliation

Суммы из независимых marts:

- event rows: **37,669,324**
- weighted events (`SUM(cnt)`): **55,878,461**
- bookings: **3,000,689**

Эти три итога совпадают между:
- `mart_product_daily`;
- `mart_channel_platform`;
- `mart_destination_performance`;
- `mart_travel_calendar_daily`.

Это главный контроль отсутствия потерь и fan-out при агрегациях.

## KPI, воспроизводящие обзор DataLens

- Среднее active users/day: **13,707**
- Bookings: **3,000,689**
- Row booking conversion: **7.97%**
- Sessions: **12,242,331**
- Booking sessions: **2,661,774**
- Session booking rate: **21.74%**

## Device diagnostic

- Desktop: row conversion **8.29%**, weighted conversion **5.69%**.
- Mobile: row conversion **5.86%**, weighted conversion **3.95%**.

## Trip profile — weighted conversion

Lead time:
- `2_7`: **8.29%**
- `31_90`: **4.19%**
- `8_30`: **5.95%**
- `91_plus`: **3.01%**
- `same_next_day`: **10.98%**

Stay length:
- `1`: **9.43%**
- `15_plus`: **1.72%**
- `2_3`: **5.46%**
- `4_7`: **3.05%**
- `8_14`: **2.07%**

Party:
- `couple`: **4.73%**
- `family_with_children`: **4.75%**
- `group`: **4.74%**
- `solo`: **8.87%**

## Observed repeat-booking retention

- Month 1: **13.83%**
- Month 3: **11.23%**
- Month 6: **11.21%**

Важно: это наблюдаемый repeat-booking retention внутри доступного временного окна, а не lifetime retention.
