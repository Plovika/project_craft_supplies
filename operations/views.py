"""Страницы операций: данные берутся из базы SQLite."""

import sqlite3

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import get_connection

# Запрос 6 из sql/queries.sql
OPERATIONS_SQL = """
    SELECT
        operations.id,
        operations.created_at,
        operations.amount,
        operations.is_cancelled,
        CASE WHEN operations.amount > 0 THEN 'Пополнение'
             ELSE 'Расход' END AS kind,
        materials.id AS material_id,
        materials.name AS material_name,
        users.name AS user_name
    FROM operations
    JOIN materials ON operations.material_id = materials.id
    JOIN users ON operations.user_id = users.id
    WHERE (? IS NULL OR operations.is_cancelled = ?)
    ORDER BY operations.created_at DESC, operations.id DESC
"""

# Запрос 7
OPERATION_SQL = """
    SELECT
        operations.id,
        operations.created_at,
        operations.amount,
        operations.is_cancelled,
        CASE WHEN operations.amount > 0 THEN 'Пополнение'
             ELSE 'Расход' END AS kind,
        materials.id AS material_id,
        materials.name AS material_name,
        users.name AS user_name,
        users.email AS user_email
    FROM operations
    JOIN materials ON operations.material_id = materials.id
    JOIN users ON operations.user_id = users.id
    WHERE operations.id = ?
"""

# Значение фильтра в адресе -> значение is_cancelled в базе
STATUS_FILTERS = {
    "active": 0,
    "cancelled": 1,
}


def operations(request: HttpRequest) -> HttpResponse:
    """Страница /operations/: история операций с фильтром по статусу."""
    status = request.GET.get("status", "")
    is_cancelled = STATUS_FILTERS.get(status)

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    operations_list = conn.execute(
        OPERATIONS_SQL,
        [is_cancelled, is_cancelled],
    ).fetchall()
    conn.close()

    context = {
        "operations": operations_list,
        "status": status if status in STATUS_FILTERS else "",
    }

    return render(request, "operations/operation_list.html", context)


def operation_detail(request: HttpRequest, operation_id: int) -> HttpResponse:
    """Страница /operations/<id>/: карточка операции."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    operation = conn.execute(OPERATION_SQL, [operation_id]).fetchone()
    conn.close()

    context = {
        "operation": operation,
    }

    return render(
        request,
        "operations/operation_detail.html",
        context,
        status=404 if operation is None else 200,
    )
