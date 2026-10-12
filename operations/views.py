"""Страницы операций: история и карточка операции."""

from django.http import HttpRequest, HttpResponse

from homepage.views import page
from models import Operation
from models.operations import find_operation_by_id
from storage import load_materials, load_operations, load_users


def load_all_operations() -> list[Operation]:
    """Загрузить операции со связанными материалами и пользователями."""
    return load_operations(load_materials(), load_users())


def operations(request: HttpRequest) -> HttpResponse:
    """Страница /operations/: история всех операций."""
    items = ""
    for operation in load_all_operations():
        status = "отменена" if operation.is_cancelled else "активна"
        badge = "bg-secondary" if operation.is_cancelled else "bg-success"
        items += f"""
        <li class="list-group-item d-flex justify-content-between">
            <a href="/operations/{operation.id}/">
                {operation.created_at} · {operation.kind}:
                {operation.material.name} {operation.amount:+d} шт.
            </a>
            <span class="badge {badge}">{status}</span>
        </li>
        """
    items = items or '<li class="list-group-item">Операций пока нет</li>'
    content = f"""
    <h1>История операций</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("История операций", content))


def operation_detail(request: HttpRequest, operation_id: int) -> HttpResponse:
    """Страница /operations/<id>/: карточка операции."""
    operation = find_operation_by_id(load_all_operations(), operation_id)
    if operation is None:
        content = """
        <h1 class="text-danger">Операция не найдена</h1>
        <a href="/operations/" class="btn btn-outline-secondary">
            ← к истории операций
        </a>
        """
        return HttpResponse(page("Операция не найдена", content), status=404)

    status = "отменена" if operation.is_cancelled else "активна"
    badge = "bg-secondary" if operation.is_cancelled else "bg-success"
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">Операция №{operation.id}</h5>
            <p class="card-text"><strong>Тип:</strong> {operation.kind}</p>
            <p class="card-text">
                <strong>Материал:</strong>
                <a href="/materials/{operation.material.id}/">
                    {operation.material.name}
                </a>
            </p>
            <p class="card-text">
                <strong>Количество:</strong> {operation.amount:+d} шт.
            </p>
            <p class="card-text">
                <strong>Пользователь:</strong> {operation.user}
            </p>
            <p class="card-text">
                <strong>Дата:</strong> {operation.created_at}
            </p>
            <p class="card-text">
                <strong>Статус:</strong>
                <span class="badge {badge}">{status}</span>
            </p>
            <a href="/operations/" class="btn btn-outline-secondary">
                ← к истории операций
            </a>
        </div>
    </div>
    """
    return HttpResponse(
        page(f"Операция №{operation.id}", content),
        status=200,
    )
