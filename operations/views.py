"""Страницы операций: история и карточка операции."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models import Operation
from models.operations import find_operation_by_id
from storage import load_materials, load_operations, load_users


def load_all_operations() -> list[Operation]:
    """Загрузить операции со связанными материалами и пользователями."""
    return load_operations(load_materials(), load_users())


def operations(request: HttpRequest) -> HttpResponse:
    """Страница /operations/: история всех операций."""
    operations_list = load_all_operations()

    context = {
        "operations": operations_list,
    }

    return render(request, "operations/operation_list.html", context)


def operation_detail(request: HttpRequest, operation_id: int) -> HttpResponse:
    """Страница /operations/<id>/: карточка операции."""
    operation = find_operation_by_id(load_all_operations(), operation_id)

    context = {
        "operation": operation,
    }

    return render(
        request,
        "operations/operation_detail.html",
        context,
        status=404 if operation is None else 200,
    )
