-- ==========================================
-- Мастерская: структура базы данных
-- ==========================================

-- Материалы: то, что лежит на полке
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    count INTEGER NOT NULL CHECK (count >= 0),
    added_at TEXT NOT NULL
);

-- Пользователи: кто берёт и докупает материалы
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

-- Операции: расход (amount < 0) или пополнение (amount > 0)
CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY,
    material_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount <> 0),
    created_at TEXT NOT NULL,
    is_cancelled INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
