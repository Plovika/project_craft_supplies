"""История операций с фильтрацией, сортировкой и пагинацией через ORM."""

from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Case, CharField, F, Q, Value, When
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from materials.models import Material
from .forms import OperationFilterForm, OperationForm
from .models import Operation, User

SORT_FIELDS = {
    "date": "-created_at",
    "material": "material__name",
    "user": "user__name",
}


def operations(request: HttpRequest) -> HttpResponse:
    form = OperationFilterForm(request.GET or None)
    status, selected_date, material_id, user_id, query = "", "", "", "", ""
    sort = "date"
    error = ""
    operations_list = Operation.objects.all()
    if form.is_bound:
        if form.is_valid():
            data = form.cleaned_data
            status, query = data["status"], data["q"]
            selected_date = data["date"]
            material, user = data["material"], data["user"]
            material_id = str(material.pk) if material else ""
            user_id = str(user.pk) if user else ""
            sort = data["sort"] or "date"
            if status == Operation.Status.ACTIVE:
                operations_list = operations_list.active()
            elif status == Operation.Status.CANCELLED:
                operations_list = operations_list.cancelled()
            elif status == Operation.Status.COMPLETED:
                operations_list = operations_list.completed()
            if selected_date:
                operations_list = operations_list.for_date(selected_date)
            if material:
                operations_list = operations_list.filter(material=material)
            if user:
                operations_list = operations_list.filter(user=user)
            if query:
                operations_list = operations_list.filter(
                    Q(material__name__icontains=query)
                    | Q(user__name__icontains=query),
                )
        else:
            error = "Проверьте корректность параметров фильтрации."
            operations_list = operations_list.none()
    operations_list = operations_list.annotate(
        material_name=F("material__name"), user_name=F("user__name"),
        material_slug=F("material__slug"),
        kind=Case(
            When(amount__gt=0, then=Value("Пополнение")),
            default=Value("Расход"), output_field=CharField(),
        ),
    ).values(
        "id", "created_at", "amount", "status", "kind",
        "material_id", "material_slug", "material_name", "user_name",
    ).order_by(SORT_FIELDS[sort], "-id")
    page_obj = Paginator(operations_list, 5).get_page(request.GET.get("page"))
    return render(request, "operations/operation_list.html", {
        "operations": page_obj, "page_obj": page_obj, "form": form,
        "status": status,
        "selected_date": selected_date, "selected_material": material_id,
        "selected_user": user_id, "q": query, "sort": sort, "error": error,
        "materials": Material.objects.order_by("name", "pk"),
        "users": User.objects.order_by("name", "pk"),
    })


def operation_detail(request: HttpRequest, operation_id: int) -> HttpResponse:
    try:
        operation = get_object_or_404(
            Operation.objects.select_related("material", "user"),
            pk=operation_id,
        )
    except Http404:
        return render(
            request, "operations/operation_detail.html",
            {"operation": None}, status=404,
        )
    return render(request, "operations/operation_detail.html", {
        "operation": operation,
    })


@require_http_methods(["GET", "POST"])
def operation_create(request: HttpRequest) -> HttpResponse:
    form = OperationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except ValidationError as error:
            form.add_error(None, error.messages)
        except IntegrityError:
            form.add_error(None, "Не удалось сохранить операцию. "
                           "Обновите страницу и проверьте данные.")
        else:
            return redirect("operations:list")
    return render(request, "operations/operation_form.html", {"form": form})


@require_http_methods(["GET", "POST"])
def operation_update(request: HttpRequest, operation_id: int) -> HttpResponse:
    try:
        operation = get_object_or_404(
            Operation.objects.active(), pk=operation_id,
        )
    except Http404:
        return render(request, "operations/operation_detail.html", {
            "operation": None,
        }, status=404)
    form = OperationForm(
        request.POST if request.method == "POST" else None, instance=operation,
    )
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except ValidationError as error:
            form.add_error(None, error.messages)
        except IntegrityError:
            form.add_error(None, "Не удалось сохранить изменения. "
                           "Обновите страницу и проверьте данные.")
        else:
            return redirect("operations:list")
    return render(request, "operations/operation_form.html", {
        "form": form, "operation": operation,
    })


@require_POST
def operation_cancel(request: HttpRequest, operation_id: int) -> HttpResponse:
    try:
        operation = get_object_or_404(
            Operation.objects.active().select_related("material", "user"),
            pk=operation_id,
        )
    except Http404:
        return render(request, "operations/operation_detail.html", {
            "operation": None,
        }, status=404)
    try:
        operation.cancel()
    except (ValidationError, ValueError) as error:
        message = (
            " ".join(error.messages)
            if isinstance(error, ValidationError) else str(error)
        )
    except IntegrityError:
        message = "Не удалось отменить операцию. Обновите страницу."
    else:
        return redirect("operations:list")
    return render(request, "operations/operation_detail.html", {
        "operation": operation, "cancel_error": message,
    }, status=400)
