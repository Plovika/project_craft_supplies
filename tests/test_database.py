import json
import sqlite3

import pytest

from db.database import BASE_DIR, get_connection
from homepage.views import BIG_CATEGORIES_SQL, BY_CATEGORY_SQL
from materials.views import SEARCH_SQL
from operations.views import OPERATIONS_SQL


def count_json(name):
    with open(BASE_DIR / "data" / name, encoding="utf-8") as file:
        return len(json.load(file))


def test_tables_created():
    conn = get_connection()
    names = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    conn.close()
    assert {"materials", "users", "operations"} <= names


@pytest.mark.parametrize("sql, json_file", [
    ("SELECT COUNT(*) FROM materials", "materials.json"),
    ("SELECT COUNT(*) FROM users", "users.json"),
    ("SELECT COUNT(*) FROM operations", "operations.json"),
])
def test_import_counts_match_json(sql, json_file):
    conn = get_connection()
    count = conn.execute(sql).fetchone()[0]
    conn.close()
    assert count == count_json(json_file)


def test_foreign_keys_are_checked():
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO operations"
            " (material_id, user_id, amount, created_at)"
            " VALUES (?, ?, ?, ?)",
            [9999, 1, 1, "2026-10-01"],
        )
    conn.close()


def test_search_with_parameters():
    conn = get_connection()
    rows = conn.execute(SEARCH_SQL, ["Краски", "Краски", 3, 3]).fetchall()
    every = conn.execute(SEARCH_SQL, ["", "", None, None]).fetchall()
    conn.close()
    assert [row[1] for row in rows] == ["Акварель Белые ночи"]
    assert len(every) == count_json("materials.json")


def test_search_is_safe_from_sql_injection():
    conn = get_connection()
    rows = conn.execute(
        SEARCH_SQL, ["' OR 1=1 --", "' OR 1=1 --", None, None]
    ).fetchall()
    conn.close()
    assert rows == []


def test_operations_status_filter():
    conn = get_connection()
    cancelled = conn.execute(OPERATIONS_SQL, [1, 1]).fetchall()
    every = conn.execute(OPERATIONS_SQL, [None, None]).fetchall()
    conn.close()
    assert all(row[3] == 1 for row in cancelled)
    assert len(every) == count_json("operations.json")


def test_group_by_and_having():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    groups = conn.execute(BY_CATEGORY_SQL).fetchall()
    big = conn.execute(BIG_CATEGORIES_SQL, [2]).fetchall()
    conn.close()
    total = sum(row["materials_count"] for row in groups)
    assert total == count_json("materials.json")
    assert all(row["materials_count"] >= 2 for row in big)
