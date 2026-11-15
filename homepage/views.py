"""Главная страница, статистика ORM и собственная страница 404."""

from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.db.models.functions import Round
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from materials.models import Material
from operations.models import Operation, User

LOW_STOCK_LIMIT = Material.MIN_STOCK
BIG_CATEGORY_SIZE = 2


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "homepage/index.html")


def statistics(request: HttpRequest) -> HttpResponse:
    totals = Material.objects.aggregate(
        materials_count=Count("id"), total_count=Sum("count", default=0),
        min_count=Min("count"), max_count=Max("count"),
        avg_count=Round(Avg("count"), precision=1),
    )
    active = Q(operations__status=Operation.Status.ACTIVE)
    operation_totals = Operation.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=Operation.Status.ACTIVE)),
        cancelled=Count("id", filter=Q(status=Operation.Status.CANCELLED)),
        completed=Count("id", filter=Q(status=Operation.Status.COMPLETED)),
    )
    context = {
        "totals": totals,
        "active_operations": operation_totals["active"],
        "operation_totals": operation_totals,
        "low_stock": Material.objects.filter(
            count__lte=LOW_STOCK_LIMIT,
        ).order_by("count", "name", "pk")[:5],
        "by_category": Material.objects.values("category").annotate(
            materials_count=Count("id"), total_count=Sum("count"),
        ).order_by("-total_count", "category"),
        "by_material": Material.objects.annotate(
            material_name=F("name"),
            operations_count=Count("operations", filter=active),
            total_change=Sum("operations__amount", filter=active, default=0),
        ).values(
            "material_name", "operations_count", "total_change",
        ).order_by("-operations_count", "material_name", "pk"),
        "by_user": User.objects.annotate(
            user_name=F("name"),
            operations_count=Count("operations", filter=active),
        ).values("user_name", "operations_count").order_by(
            "-operations_count", "user_name", "pk",
        ),
        "big_categories": Material.objects.values("category").annotate(
            materials_count=Count("id"),
        ).filter(materials_count__gte=BIG_CATEGORY_SIZE).order_by(
            "-materials_count", "category",
        ),
        "big_category_size": BIG_CATEGORY_SIZE,
    }
    return render(request, "homepage/statistics.html", context)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(request, "homepage/404.html", status=404)
