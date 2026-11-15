-- ==========================================
-- Мастерская: SQL-запросы проекта
-- Проверка: sqlite3 data/craftbox.sqlite
-- В приложении конкретные значения (3, 'Краски', 1 ...)
-- передаются параметрами ?, а не вписываются в текст запроса.
-- ==========================================


-- 1. [Список] Все материалы по алфавиту (страница /materials/)
SELECT
    id,
    name,
    category,
    count,
    count <= 3 AS is_low_stock
FROM materials
ORDER BY name;


-- 2. [Список] Категории без повторов (выпадающий список на /materials/search/)
SELECT DISTINCT category
FROM materials
ORDER BY category;


-- 3. [WHERE] Один материал по номеру (страница /materials/1/)
SELECT
    id,
    name,
    category,
    count,
    added_at,
    count <= 3 AS is_low_stock
FROM materials
WHERE id = 1;


-- 4. [WHERE, несколько условий] Поиск: категория + остаток не больше N
--    (страница /materials/search/?category=Краски&max_count=3)
--    Если категория не выбрана (''), первое условие истинно для всех строк;
--    если остаток не задан (NULL), второе условие тоже.
SELECT
    id,
    name,
    category,
    count,
    count <= 3 AS is_low_stock
FROM materials
WHERE ('Краски' = '' OR category = 'Краски')
  AND (3 IS NULL OR count <= 3)
ORDER BY count, name;


-- 5. [WHERE] Материалы, которые заканчиваются (остаток 3 и меньше)
--    (блок «Заканчиваются» на /statistics/)
SELECT
    id,
    name,
    category,
    count
FROM materials
WHERE count <= 3
ORDER BY count, name
LIMIT 5;


-- 6. [JOIN + WHERE по состоянию] История операций с названием материала
--    и именем пользователя (страница /operations/).
--    Фильтр ?status=active -> is_cancelled = 0, cancelled -> 1, без фильтра -> NULL.
SELECT
    operations.id,
    operations.created_at,
    operations.amount,
    operations.is_cancelled,
    CASE WHEN operations.amount > 0 THEN 'Пополнение' ELSE 'Расход' END AS kind,
    materials.id AS material_id,
    materials.name AS material_name,
    users.name AS user_name
FROM operations
JOIN materials ON operations.material_id = materials.id
JOIN users ON operations.user_id = users.id
WHERE (0 IS NULL OR operations.is_cancelled = 0)
ORDER BY operations.created_at DESC, operations.id DESC;


-- 7. [JOIN + WHERE] Одна операция со всеми связанными данными
--    (страница /operations/1/)
SELECT
    operations.id,
    operations.created_at,
    operations.amount,
    operations.is_cancelled,
    CASE WHEN operations.amount > 0 THEN 'Пополнение' ELSE 'Расход' END AS kind,
    materials.id AS material_id,
    materials.name AS material_name,
    users.name AS user_name,
    users.email AS user_email
FROM operations
JOIN materials ON operations.material_id = materials.id
JOIN users ON operations.user_id = users.id
WHERE operations.id = 1;


-- 8. [JOIN + WHERE] История операций одного материала
--    (блок «История операций» на /materials/2/)
SELECT
    operations.id,
    operations.created_at,
    operations.amount,
    operations.is_cancelled,
    CASE WHEN operations.amount > 0 THEN 'Пополнение' ELSE 'Расход' END AS kind,
    users.name AS user_name
FROM operations
JOIN users ON operations.user_id = users.id
WHERE operations.material_id = 2
ORDER BY operations.created_at DESC, operations.id DESC;


-- 9. [Агрегатные функции] Общие показатели по материалам (/statistics/)
SELECT
    COUNT(*) AS materials_count,
    SUM(count) AS total_count,
    MIN(count) AS min_count,
    MAX(count) AS max_count,
    ROUND(AVG(count), 1) AS avg_count
FROM materials;


-- 10. [Агрегатная функция + WHERE] Количество активных операций (/statistics/)
SELECT COUNT(*) AS active_operations
FROM operations
WHERE is_cancelled = 0;


-- 11. [GROUP BY] Материалы по категориям: сколько позиций и единиц
--     (таблица «По категориям» на /statistics/)
SELECT
    category,
    COUNT(*) AS materials_count,
    SUM(count) AS total_count
FROM materials
GROUP BY category
ORDER BY total_count DESC;


-- 12. [LEFT JOIN + GROUP BY] Активные операции по каждому материалу,
--     включая материалы без операций (таблица на /statistics/)
SELECT
    materials.name AS material_name,
    COUNT(operations.id) AS operations_count,
    COALESCE(SUM(operations.amount), 0) AS total_change
FROM materials
LEFT JOIN operations
    ON materials.id = operations.material_id
   AND operations.is_cancelled = 0
GROUP BY materials.id, materials.name
ORDER BY operations_count DESC, materials.name;


-- 13. [LEFT JOIN + GROUP BY] Активность пользователей (/statistics/)
SELECT
    users.name AS user_name,
    COUNT(operations.id) AS operations_count
FROM users
LEFT JOIN operations
    ON users.id = operations.user_id
   AND operations.is_cancelled = 0
GROUP BY users.id, users.name
ORDER BY operations_count DESC, users.name;


-- 14. [GROUP BY + HAVING] Категории, в которых не меньше 2 материалов
--     (блок «Самые большие категории» на /statistics/)
SELECT
    category,
    COUNT(*) AS materials_count
FROM materials
GROUP BY category
HAVING COUNT(*) >= 2
ORDER BY materials_count DESC;
