"""Страницы материалов: данные берутся из базы SQLite."""

import sqlite3

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import get_connection

# Запрос 1 из sql/queries.sql
MATERIALS_SQL = """
    SELECT id, name, category, count, count <= 3 AS is_low_stock
    FROM materials
    ORDER BY name
"""

# Запрос 2
CATEGORIES_SQL = """
    SELECT DISTINCT category
    FROM materials
    ORDER BY category
"""

# Запрос 3
MATERIAL_SQL = """
    SELECT id, name, category, count, added_at, count <= 3 AS is_low_stock
    FROM materials
    WHERE id = ?
"""

# Запрос 4
SEARCH_SQL = """
    SELECT id, name, category, count, count <= 3 AS is_low_stock
    FROM materials
    WHERE (? = '' OR category = ?)
      AND (? IS NULL OR count <= ?)
    ORDER BY count, name
"""

# Запрос 8
HISTORY_SQL = """
    SELECT
        operations.id,
        operations.created_at,
        operations.amount,
        operations.is_cancelled,
        CASE WHEN operations.amount > 0 THEN 'Пополнение'
             ELSE 'Расход' END AS kind,
        users.name AS user_name
    FROM operations
    JOIN users ON operations.user_id = users.id
    WHERE operations.material_id = ?
    ORDER BY operations.created_at DESC, operations.id DESC
"""


def materials(request: HttpRequest) -> HttpResponse:
    """Страница /materials/: список всех материалов."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    materials_list = conn.execute(MATERIALS_SQL).fetchall()
    conn.close()

    context = {
        "materials": materials_list,
    }

    return render(request, "materials/material_list.html", context)


def material_search(request: HttpRequest) -> HttpResponse:
    """Страница /materials/search/: поиск по категории и остатку."""
    category = request.GET.get("category", "").strip()
    max_count_text = request.GET.get("max_count", "").strip()
    searched = "category" in request.GET or "max_count" in request.GET

    error = ""
    max_count = None
    if max_count_text:
        if max_count_text.isdigit():
            max_count = int(max_count_text)
        else:
            error = "Остаток должен быть целым неотрицательным числом."

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    categories = conn.execute(CATEGORIES_SQL).fetchall()
    results = []
    if searched and not error:
        results = conn.execute(
            SEARCH_SQL,
            [category, category, max_count, max_count],
        ).fetchall()
    conn.close()

    context = {
        "categories": categories,
        "category": category,
        "max_count": max_count_text,
        "searched": searched,
        "error": error,
        "materials": results,
    }

    return render(request, "materials/material_search.html", context)


def material_detail(request: HttpRequest, material_id: int) -> HttpResponse:
    """Страница /materials/<id>/: карточка материала и его история."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    material = conn.execute(MATERIAL_SQL, [material_id]).fetchone()
    history = []
    if material is not None:
        history = conn.execute(HISTORY_SQL, [material_id]).fetchall()
    conn.close()

    context = {
        "material": material,
        "history": history,
    }

    return render(
        request,
        "materials/material_detail.html",
        context,
        status=404 if material is None else 200,
    )
