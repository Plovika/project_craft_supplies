"""Администрирование участников и операций с сохранением остатков."""

from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.urls import reverse

from .models import Operation, User


class StockAdmin(admin.ModelAdmin):
    """При ошибке сохранения откатываем форму и показываем сообщение."""

    def changeform_view(self, request, object_id=None, form_url="",
                        extra_context=None):
        try:
            return super().changeform_view(
                request, object_id, form_url, extra_context,
            )
        except (ValidationError, IntegrityError) as error:
            text = "; ".join(error.messages) if isinstance(
                error, ValidationError,
            ) else "Не удалось сохранить данные. Проверьте значения и связи."
            self.message_user(request, text, messages.ERROR)
            return redirect(request.path)


class OperationInline(admin.TabularInline):
    model = Operation
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("material", "user")


class UserOperationInline(OperationInline):
    fields = ("material", "amount", "created_at", "status")
    autocomplete_fields = ("material",)


@admin.register(User)
class UserAdmin(StockAdmin):
    list_display = ("id", "name", "email")
    list_display_links = ("name",)
    search_fields = ("name", "email")
    ordering = ("name", "pk")
    list_per_page = 20
    readonly_fields = ("id",)
    inlines = (UserOperationInline,)


@admin.register(Operation)
class OperationAdmin(StockAdmin):
    list_display = (
        "id", "material", "user", "material_count", "amount", "created_at",
        "status",
    )
    list_display_links = ("id",)
    search_fields = ("material__name", "user__name")
    list_filter = ("created_at", "status")
    ordering = ("-created_at", "-pk")
    list_per_page = 20
    readonly_fields = ("id",)
    list_select_related = ("material", "user")
    date_hierarchy = "created_at"
    autocomplete_fields = ("material", "user")
    actions = ("cancel_operations", "restore_operations", "delete_selected")

    @admin.display(description="Остаток", ordering="material__count")
    def material_count(self, obj):
        return obj.material.count

    def _change_status(self, request, queryset, target):
        count = 0
        try:
            with transaction.atomic():
                for operation in queryset.order_by("pk"):
                    if target == Operation.Status.CANCELLED:
                        if operation.status == target:
                            continue
                        operation.cancel()
                    else:
                        if operation.status != Operation.Status.CANCELLED:
                            continue
                        operation.restore()
                    count += 1
        except (ValidationError, ValueError) as error:
            text = "; ".join(error.messages) if isinstance(
                error, ValidationError,
            ) else str(error)
            self.message_user(request, text, messages.ERROR)
        else:
            self.message_user(
                request, f"Обработано операций: {count}.", messages.SUCCESS,
            )

    @admin.action(
        description="Отменить выбранные операции", permissions=["change"],
    )
    def cancel_operations(self, request, queryset):
        self._change_status(request, queryset, Operation.Status.CANCELLED)

    @admin.action(description="Вернуть в активные", permissions=["change"])
    def restore_operations(self, request, queryset):
        self._change_status(request, queryset, Operation.Status.ACTIVE)

    @admin.action(
        description="Удалить выбранные операции", permissions=["delete"],
    )
    def delete_selected(self, request, queryset):
        try:
            return delete_selected(self, request, queryset)
        except ValidationError as error:
            self.message_user(
                request, "; ".join(error.messages), messages.ERROR,
            )

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context)
        except ValidationError as error:
            self.message_user(
                request, "; ".join(error.messages), messages.ERROR,
            )
            return redirect(reverse("admin:operations_operation_changelist"))


admin.site.site_header = "Мастерская — администрирование"
admin.site.site_title = "Мастерская"
admin.site.index_title = "Управление материалами и операциями"
