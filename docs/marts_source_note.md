# 07. Source note

В исходном сообщении было несовпадение источников.

## Фактический источник проекта

Текущий GitHub `Debchik/HotelExpedia`, EDA и все 14 marts относятся к
**Kaggle Expedia Hotel Recommendations**:

`https://www.kaggle.com/competitions/expedia-hotel-recommendations/data`

Этот источник содержит `train.csv`, `test.csv`, `destinations.csv` и
`sample_submission.csv`; train включает click/booking events и поле `cnt`.

## Неверная ссылка из исходного сообщения

`https://www.kaggle.com/datasets/imakash3011/customer-personality-analysis`

ведёт на **Customer Personality Analysis** — отдельный customer-segmentation
dataset, не связанный с Expedia Hotel Recommendations.

## Что использовано в handoff

1. загруженные 14 Expedia MART CSV;
2. загруженный EDA notebook;
3. текущая структура и contracts GitHub `Debchik/HotelExpedia`;
4. официальный Kaggle competition page — только для верификации source identity.

В презентации, README и ссылках на источник используйте Expedia Hotel
Recommendations, а не Customer Personality Analysis.
