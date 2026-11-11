# Databricks Data Engineering Internship Task

## Описание
Данный проект представляет собой реализацию ETL-пайплайна (Medallion Architecture: Bronze, Silver, Gold) для обработки данных о поездках такси, пользователях и водителях.

## Особенности реализации
- **Тестовые данные**: Вместо загрузки внешних файлов Parquet/Avro, данные были сгенерированы программно с использованием библиотеки `Faker` (для drivers) и вручную созданных DataFrame (для taxi и users). Это обеспечило контролируемый набор данных с "плохими" записями для тестирования фильтрации.
- **Окружение**: Проект разработан и протестирован в **Databricks Community Edition (Serverless)** из-за ограничений доступа к Premium-функциям.

## Что было реализовано ✅
- [x] Создание схем (баз данных) Bronze, Silver, Gold.
- [x] Batch Ingestion: генерация и загрузка тестовых данных в слой Bronze (Delta format).
- [x] Delta Lake Features: Schema Evolution (добавление колонки phone), Time Travel (`VERSION AS OF`) и `RESTORE TABLE`.
- [x] Data Cleansing (Silver): фильтрация null/нулевых значений, маппинг payment_type через CASE, добавление `ingest_time`, дедупликация.
- [x] Aggregations (Gold): группировка по локациям и experience level, агрегатные функции (COUNT, SUM, AVG), округление.
- [x] Data Enrichment: создание справочника водителей и LEFT JOIN с данными о поездках через синтетический driver_id.
- [x] Maintenance: финальный `OPTIMIZE` (Z-Order) и `VACUUM` для всех Gold-таблиц.
- [x] Генерация JSON-отчета о количестве строк на каждом этапе пайплайна.

## Что не было запущено (и почему) ⚠️
Следующие части задания требуют лицензии Databricks Premium/Enterprise (Unity Catalog, DLT):
- **Delta Live Tables (DLT)** 
- **Security & Governance**
- **Streaming с Faker** Эмулирован через batch-запись с `mergeSchema`, так как длительные стриминговые джобы ограничены в Serverless окружении.

## Структура проекта

```
bronze/ # Сырые данные
├── taxi # Данные о поездках
├── users # Данные о пользователях
└── drivers # Данные о водителях
silver/ # Очищенные данные
├── taxi_dedup
├── users
└── drivers_dedup
gold/ # Агрегированные данные
├── taxi_metrics # Статистика поездок по локациям
├── driver_metrics # Статистика водителей по опыту
├── user_metrics # Статистика пользователей по датам
└── enriched_trips # Объединённые данные (trips + drivers)
```

## Как запустить
1. Открыть ноутбук `Internship_Task` в Databricks Workspace.
2. Последовательно выполнить ячейки (или использовать Run All).
3. Убедиться, что в выводе последней ячейки сгенерирован JSON-отчёт со статистикой по всем таблицам.

## Технологии
- Apache Spark (PySpark)
- Delta Lake
- Databricks
- Python (Faker для генерации данных)