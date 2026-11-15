"""Общие данные шапки и навигации сайта."""

from .models import Material


def material_context(request):
    return {
        "site_name": "Мастерская",
        "site_materials_count": Material.objects.count(),
    }
