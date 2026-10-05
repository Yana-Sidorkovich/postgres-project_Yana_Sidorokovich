-- ============================================================
-- TASK 2: BoM Explosion - SQL Implementation
-- ============================================================
-- Примечание: для импорта данных Excel был конвертирован в CSV через Pandas:
-- df = pd.read_excel('data/task_2_data_ex.xlsx')
-- df.to_csv('data/task_2_data_ex.csv', index=False, encoding='utf-8')

-- 1. Создаем таблицу для сырых данных
CREATE TABLE IF NOT EXISTS bom_raw (
    year INT,
    month INT,
    produced_material BIGINT,
    produced_material_production_type BIGINT,
    produced_material_release_type VARCHAR(10),
    produced_material_quantity NUMERIC,
    component_material BIGINT,
    component_material_production_type BIGINT,
    component_material_release_type VARCHAR(10),
    component_material_quantity NUMERIC,
    plant_id VARCHAR(20)
);

-- Данные загружаются через Import Data в DBeaver из task_2_data_ex.csv
-- После загрузки: SELECT COUNT(*) FROM bom_raw; -- должно быть 1320

-- 2. Создаем таблицу уникальных структурных связей BoM
-- (без количеств, чтобы избежать дублирования по месяцам)

-- Сначала удаляем VIEW (он зависит от таблицы bom_unique)
DROP VIEW IF EXISTS bom_exploded_view;

-- Теперь можно безопасно удалить таблицу
DROP TABLE IF EXISTS bom_unique;

CREATE TABLE bom_unique AS
SELECT DISTINCT
    plant_id,
    year,
    produced_material,
    produced_material_production_type,
    produced_material_release_type,
    component_material,
    component_material_production_type,
    component_material_release_type
FROM bom_raw;

-- Проверка: SELECT COUNT(*) FROM bom_unique; -- должно быть 110

-- 3. Создаем VIEW с рекурсивным раскрытием BoM
DROP VIEW IF EXISTS bom_exploded_view;

CREATE OR REPLACE VIEW bom_exploded_view AS
WITH RECURSIVE bom_tree AS (
    -- Базовый случай: FIN материалы (корни деревьев)
    SELECT
        plant_id AS plant,
        year,
        produced_material AS fin_material_id,
        produced_material_release_type AS fin_material_release_type,
        produced_material_production_type AS fin_material_production_type,
        produced_material AS current_material_id,
        produced_material_release_type AS current_release_type,
        0 AS depth
    FROM bom_unique
    WHERE produced_material_release_type = 'FIN'

    UNION ALL

    -- Рекурсивный шаг: идем вглубь для FIN и PROD
    SELECT
        bt.plant,
        bt.year,
        bt.fin_material_id,
        bt.fin_material_release_type,
        bt.fin_material_production_type,
        b.component_material AS current_material_id,
        b.component_material_release_type AS current_release_type,
        bt.depth + 1
    FROM bom_tree bt
    JOIN bom_unique b ON bt.current_material_id = b.produced_material
                     AND bt.plant = b.plant_id
                     AND bt.year = b.year
    WHERE bt.current_release_type IN ('FIN', 'PROD')
)
-- Финальный SELECT: для каждого PROD показываем его компоненты
SELECT DISTINCT
    bt.plant,
    bt.year,
    bt.fin_material_id,
    bt.fin_material_release_type,
    bt.fin_material_production_type,
    r1.produced_material_quantity AS fin_production_quantity,
    bt.current_material_id AS prod_material_id,
    bt.current_release_type AS prod_material_release_type,
    bu.produced_material_production_type AS prod_material_production_type,
    r2.produced_material_quantity AS prod_material_production_quantity,
    bu.component_material AS component_id,
    bu.component_material_release_type AS component_material_release_type,
    bu.component_material_production_type AS component_material_production_type,
    r3.component_material_quantity AS component_consumption_quantity
FROM bom_tree bt
JOIN bom_unique bu ON bt.current_material_id = bu.produced_material
                   AND bt.plant = bu.plant_id
                   AND bt.year = bu.year
LEFT JOIN (
    SELECT DISTINCT ON (plant_id, year, produced_material)
           plant_id, year, produced_material, produced_material_quantity
    FROM bom_raw
    ORDER BY plant_id, year, produced_material
) r1 ON bt.plant = r1.plant_id AND bt.year = r1.year AND bt.fin_material_id = r1.produced_material
LEFT JOIN (
    SELECT DISTINCT ON (plant_id, year, produced_material)
           plant_id, year, produced_material, produced_material_quantity
    FROM bom_raw
    ORDER BY plant_id, year, produced_material
) r2 ON bt.plant = r2.plant_id AND bt.year = r2.year AND bt.current_material_id = r2.produced_material
LEFT JOIN (
    SELECT DISTINCT ON (plant_id, year, produced_material, component_material)
           plant_id, year, produced_material, component_material, component_material_quantity
    FROM bom_raw
    ORDER BY plant_id, year, produced_material, component_material
) r3 ON bt.plant = r3.plant_id AND bt.year = r3.year
     AND bt.current_material_id = r3.produced_material AND bu.component_material = r3.component_material
WHERE bt.current_release_type = 'PROD'
  AND bu.component_material IS NOT NULL
ORDER BY bt.plant, bt.year, bt.fin_material_id;

-- 4. Проверки
SELECT COUNT(*) AS total_rows FROM bom_exploded_view;
-- Должно быть: 100

SELECT fin_material_id, COUNT(*) AS row_count
FROM bom_exploded_view
GROUP BY fin_material_id
ORDER BY fin_material_id;
-- Должно быть: по 10 строк на каждый FIN

SELECT * FROM bom_exploded_view
WHERE fin_material_id = 10000
ORDER BY year, plant, fin_material_id;

