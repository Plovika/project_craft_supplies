"""Страницы материалов: список и карточка материала."""

from django.http import HttpRequest, HttpResponse

from homepage.views import page
from models.materials import find_material_by_id
from models.operations import get_material_history
from storage import load_materials, load_operations, load_users


def materials(request: HttpRequest) -> HttpResponse:
    """Страница /materials/: таблица всех материалов."""
    rows = ""
    for material in load_materials():
        badge = "bg-danger" if material.is_low_stock() else "bg-success"
        rows += f"""
        <tr>
            <td>{material.id}</td>
            <td><a href="/materials/{material.id}/">{material.name}</a></td>
            <td>{material.category}</td>
            <td><span class="badge {badge}">{material.count} шт.</span></td>
        </tr>
        """
    content = f"""
    <h1>Материалы</h1>
    <table class="table table-hover bg-white">
        <thead>
            <tr><th>ID</th><th>Название</th><th>Категория</th>
            <th>Остаток</th></tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """
    return HttpResponse(page("Материалы", content))


def material_detail(request: HttpRequest, material_id: int) -> HttpResponse:
    """Страница /materials/<id>/: карточка материала и его история."""
    materials_list = load_materials()
    material = find_material_by_id(materials_list, material_id)
    if material is None:
        content = """
        <h1 class="text-danger">Материал не найден</h1>
        <a href="/materials/" class="btn btn-outline-secondary">
            ← к списку материалов
        </a>
        """
        return HttpResponse(page("Материал не найден", content), status=404)

    operations_list = load_operations(materials_list, load_users())
    history = ""
    for operation in get_material_history(operations_list, material):
        history += f'<li class="list-group-item">{operation}</li>'
    history = history or '<li class="list-group-item">Операций нет</li>'

    badge = "bg-danger" if material.is_low_stock() else "bg-success"
    content = f"""
    <div class="card mb-4">
        <div class="card-body">
            <h5 class="card-title">{material.name}</h5>
            <p class="card-text"><strong>ID:</strong> {material.id}</p>
            <p class="card-text">
                <strong>Категория:</strong> {material.category}
            </p>
            <p class="card-text">
                <strong>Количество:</strong>
                <span class="badge {badge}">{material.count} шт.</span>
            </p>
            <p class="card-text">
                <strong>Добавлен:</strong> {material.added_at}
            </p>
            <p class="card-text">{material.check_low_stock()}</p>
            <a href="/materials/" class="btn btn-outline-secondary">
                ← к списку материалов
            </a>
        </div>
    </div>
    <h2 class="h5">История операций</h2>
    <ul class="list-group">{history}</ul>
    """
    return HttpResponse(page(material.name, content), status=200)
