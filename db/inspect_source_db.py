"""Показать таблицы, столбцы и количество записей исходной базы ПР7."""

import sqlite3
from pathlib import Path

SOURCE_DB = Path(__file__).resolve().parent.parent / "data" / "craftbox.sqlite"


def main():
    if not SOURCE_DB.is_file():
        raise FileNotFoundError(f"Исходная база не найдена: {SOURCE_DB}")
    connection = sqlite3.connect(SOURCE_DB.as_uri() + "?mode=ro", uri=True)
    try:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        for (table,) in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            print(f"\nТаблица: {table}")
            for column in connection.execute(f"PRAGMA table_info({quoted})"):
                print(
                    f" имя={column[1]}, тип={column[2]}, "
                    f"NOT NULL={column[3]}, PRIMARY KEY={column[5]}"
                )
            count = connection.execute(
                f"SELECT COUNT(*) FROM {quoted}"
            ).fetchone()[0]
            print(f"Количество записей: {count}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
