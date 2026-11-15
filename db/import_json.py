"""Перенос данных проекта из JSON-файлов в базу SQLite.

Запуск из корня проекта:  python -m db.import_json
Скрипт можно запускать повторно: таблицы создаются, если их нет,
старые записи удаляются и загружаются заново из JSON.
"""

import json
import sqlite3
from pathlib import Path

from db.database import BASE_DIR, DB_PATH, create_schema, get_connection

DATA_DIR = BASE_DIR / "data"
MATERIALS_FILE = DATA_DIR / "materials.json"
USERS_FILE = DATA_DIR / "users.json"
OPERATIONS_FILE = DATA_DIR / "operations.json"


def load_json(filename: Path) -> list[dict]:
    """Прочитать список записей из JSON-файла."""
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def clear_tables(conn: sqlite3.Connection) -> None:
    """Удалить старые записи: сначала зависимые операции, потом остальное."""
    conn.execute("DELETE FROM operations")
    conn.execute("DELETE FROM users")
    conn.execute("DELETE FROM materials")


def import_materials(conn: sqlite3.Connection) -> None:
    """Перенести материалы."""
    materials = load_json(MATERIALS_FILE)
    conn.executemany(
        """
        INSERT INTO materials (id, name, category, count, added_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (m["id"], m["name"], m["category"], m["count"], m["added_at"])
            for m in materials
        ],
    )


def import_users(conn: sqlite3.Connection) -> None:
    """Перенести пользователей."""
    users = load_json(USERS_FILE)
    conn.executemany(
        """
        INSERT INTO users (id, name, email)
        VALUES (?, ?, ?)
        """,
        [(u["id"], u["name"], u["email"]) for u in users],
    )


def import_operations(conn: sqlite3.Connection) -> None:
    """Перенести операции (ссылаются на материалы и пользователей)."""
    operations = load_json(OPERATIONS_FILE)
    conn.executemany(
        """
        INSERT INTO operations
            (id, material_id, user_id, amount, created_at, is_cancelled)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                op["id"],
                op["material_id"],
                op["user_id"],
                op["amount"],
                op["created_at"],
                int(op["is_cancelled"]),
            )
            for op in operations
        ],
    )


def import_all(conn: sqlite3.Connection) -> None:
    """Перенести все данные. Порядок важен из-за внешних ключей."""
    import_materials(conn)
    import_users(conn)
    import_operations(conn)


def main() -> None:
    """Создать таблицы и перенести в них данные из JSON."""
    conn = get_connection()
    try:
        create_schema(conn)
        clear_tables(conn)
        import_all(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print("Данные перенесены в", DB_PATH.name)


if __name__ == "__main__":
    main()
