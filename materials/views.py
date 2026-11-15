"""Список, поиск и карточки материалов через Django ORM."""

from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Material


def materials(request: HttpRequest) -> HttpResponse:
    materials_list = Material.objects.order_by("name", "pk")
    return render(
        request, "materials/material_list.html", {"materials": materials_list},
    )


def material_search(request: HttpRequest) -> HttpResponse:
    category = request.GET.get("category", "").strip()
    max_count_text = request.GET.get("max_count", "").strip()
    query = request.GET.get("q", "").strip()
    searched = any(
        key in request.GET for key in ("category", "max_count", "q")
    )
    error = ""
    max_count = None
    if max_count_text:
        try:
            if not max_count_text.isascii() or not max_count_text.isdecimal():
                raise ValueError
            max_count = int(max_count_text)
            if max_count > 9223372036854775807:
                raise ValueError
        except ValueError:
            error = (
                "Остаток должен быть целым неотрицательным числом до 2⁶³−1."
            )
    categories = Material.objects.order_by("category").values(
        "category",
    ).distinct()
    results = Material.objects.none()
    if searched and not error:
        results = Material.objects.all()
        if category:
            results = results.filter(category=category)
        if max_count is not None:
            results = results.filter(count__lte=max_count)
        if query:
            results = results.filter(
                Q(name__icontains=query) | Q(category__icontains=query),
            )
        results = results.order_by("count", "name", "pk")
    return render(request, "materials/material_search.html", {
        "categories": categories, "category": category,
        "max_count": max_count_text, "q": query, "searched": searched,
        "error": error, "materials": results,
    })


def material_detail(request: HttpRequest, slug: str) -> HttpResponse:
    try:
        material = get_object_or_404(Material, slug=slug)
    except Http404:
        # Сохраняем существующее оформление отсутствующего материала.
        return render(
            request, "materials/material_detail.html",
            {"material": None}, status=404,
        )
    history = material.operations.select_related("user").all()
    return render(request, "materials/material_detail.html", {
        "material": material, "history": history,
    })


def material_legacy_detail(
    request: HttpRequest, material_id: int,
) -> HttpResponse:
    try:
        material = get_object_or_404(Material, pk=material_id)
    except Http404:
        return render(
            request, "materials/material_detail.html",
            {"material": None}, status=404,
        )
    return redirect(material.get_absolute_url(), permanent=True)
