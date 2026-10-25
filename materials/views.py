"""Страницы материалов: список и карточка материала."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.materials import find_material_by_id
from models.operations import get_material_history
from storage import load_materials, load_operations, load_users


def materials(request: HttpRequest) -> HttpResponse:
    """Страница /materials/: список всех материалов."""
    materials_list = load_materials()

    context = {
        "materials": materials_list,
    }

    return render(request, "materials/material_list.html", context)


def material_detail(request: HttpRequest, material_id: int) -> HttpResponse:
    """Страница /materials/<id>/: карточка материала и его история."""
    materials_list = load_materials()
    material = find_material_by_id(materials_list, material_id)

    history = []
    if material is not None:
        operations_list = load_operations(materials_list, load_users())
        history = get_material_history(operations_list, material)

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
