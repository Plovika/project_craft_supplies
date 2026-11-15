"""Подключение к базе данных SQLite проекта."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "craftbox.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Открыть соединение с базой и включить проверку внешних ключей."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Создать таблицы по командам из sql/schema.sql."""
    with open(SCHEMA_PATH, encoding="utf-8") as file:
        conn.executescript(file.read())
