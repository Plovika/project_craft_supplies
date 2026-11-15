"""Список материалов и встроенная история операций."""

from django.contrib import admin
from django.db.models import Count, Q

from operations.admin import OperationInline, StockAdmin
from operations.models import Operation
from .models import Material


class MaterialOperationInline(OperationInline):
    fields = ("user", "amount", "created_at", "status")
    autocomplete_fields = ("user",)


class LowStockFilter(admin.SimpleListFilter):
    title = "Запас материала"
    parameter_name = "low_stock"

    def lookups(self, request, model_admin):
        return [("yes", "Заканчивается"), ("no", "Достаточно")]

    def queryset(self, request, queryset):
        if self.value() in ("yes", "no"):
            return queryset.filter(is_low_stock=self.value() == "yes")
        return queryset


@admin.register(Material)
class MaterialAdmin(StockAdmin):
    list_display = (
        "id", "name", "category", "count", "low_stock_indicator",
        "active_operations_count",
    )
    list_display_links = ("name",)
    list_editable = ("count",)
    search_fields = ("name", "category")
    list_filter = ("category", LowStockFilter)
    ordering = ("name", "pk")
    list_per_page = 20
    readonly_fields = ("id", "slug", "low_stock_indicator")
    inlines = (MaterialOperationInline,)
    view_on_site = True

    @admin.display(
        boolean=True, description="Заканчивается", ordering="is_low_stock",
    )
    def low_stock_indicator(self, obj):
        return obj.is_low_stock

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            active_operations=Count(
                "operations", filter=Q(
                    operations__status=Operation.Status.ACTIVE,
                ),
            ),
        )

    @admin.display(
        description="Активных операций", ordering="active_operations",
    )
    def active_operations_count(self, obj):
        return obj.active_operations
