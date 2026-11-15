"""Главная страница, статистика и собственная страница 404."""

import sqlite3

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import get_connection

# Запрос 9 из sql/queries.sql
TOTALS_SQL = """
    SELECT
        COUNT(*) AS materials_count,
        SUM(count) AS total_count,
        MIN(count) AS min_count,
        MAX(count) AS max_count,
        ROUND(AVG(count), 1) AS avg_count
    FROM materials
"""

# Запрос 10
ACTIVE_OPERATIONS_SQL = """
    SELECT COUNT(*) AS active_operations
    FROM operations
    WHERE is_cancelled = 0
"""

# Запрос 5
LOW_STOCK_SQL = """
    SELECT id, name, category, count
    FROM materials
    WHERE count <= ?
    ORDER BY count, name
    LIMIT 5
"""

# Запрос 11
BY_CATEGORY_SQL = """
    SELECT category, COUNT(*) AS materials_count, SUM(count) AS total_count
    FROM materials
    GROUP BY category
    ORDER BY total_count DESC
"""

# Запрос 12
BY_MATERIAL_SQL = """
    SELECT
        materials.name AS material_name,
        COUNT(operations.id) AS operations_count,
        COALESCE(SUM(operations.amount), 0) AS total_change
    FROM materials
    LEFT JOIN operations
        ON materials.id = operations.material_id
       AND operations.is_cancelled = 0
    GROUP BY materials.id, materials.name
    ORDER BY operations_count DESC, materials.name
"""

# Запрос 13
BY_USER_SQL = """
    SELECT users.name AS user_name, COUNT(operations.id) AS operations_count
    FROM users
    LEFT JOIN operations
        ON users.id = operations.user_id
       AND operations.is_cancelled = 0
    GROUP BY users.id, users.name
    ORDER BY operations_count DESC, users.name
"""

# Запрос 14
BIG_CATEGORIES_SQL = """
    SELECT category, COUNT(*) AS materials_count
    FROM materials
    GROUP BY category
    HAVING COUNT(*) >= ?
    ORDER BY materials_count DESC
"""

LOW_STOCK_LIMIT = 3       # остаток, при котором материал «заканчивается»
BIG_CATEGORY_SIZE = 2     # сколько материалов делает категорию «большой»


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: описание сервиса и переходы в разделы."""
    return render(request, "homepage/index.html")


def statistics(request: HttpRequest) -> HttpResponse:
    """Страница /statistics/: итоги, группировки и материалы на исходе."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    context = {
        "totals": conn.execute(TOTALS_SQL).fetchone(),
        "active_operations": conn.execute(
            ACTIVE_OPERATIONS_SQL
        ).fetchone()["active_operations"],
        "low_stock": conn.execute(
            LOW_STOCK_SQL, [LOW_STOCK_LIMIT]
        ).fetchall(),
        "by_category": conn.execute(BY_CATEGORY_SQL).fetchall(),
        "by_material": conn.execute(BY_MATERIAL_SQL).fetchall(),
        "by_user": conn.execute(BY_USER_SQL).fetchall(),
        "big_categories": conn.execute(
            BIG_CATEGORIES_SQL, [BIG_CATEGORY_SIZE]
        ).fetchall(),
        "big_category_size": BIG_CATEGORY_SIZE,
    }
    conn.close()

    return render(request, "homepage/statistics.html", context)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Собственная страница 404 для адресов без маршрута."""
    return render(request, "homepage/404.html", status=404)
