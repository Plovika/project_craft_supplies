"""История операций с фильтрацией, сортировкой и пагинацией через ORM."""

from datetime import date

from django.core.paginator import Paginator
from django.db.models import Case, CharField, F, Q, Value, When
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from materials.models import Material
from .models import Operation, User

SORT_FIELDS = {
    "date": "-created_at",
    "material": "material__name",
    "user": "user__name",
}


def operations(request: HttpRequest) -> HttpResponse:
    status = request.GET.get("status", "")
    selected_date = request.GET.get("date", "").strip()
    material_id = request.GET.get("material", "").strip()
    user_id = request.GET.get("user", "").strip()
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "date")
    if sort not in SORT_FIELDS:
        sort = "date"
    error = ""
    operations_list = Operation.objects.all()
    if status == Operation.Status.ACTIVE:
        operations_list = operations_list.active()
    elif status == Operation.Status.CANCELLED:
        operations_list = operations_list.cancelled()
    elif status == Operation.Status.COMPLETED:
        operations_list = operations_list.completed()
    else:
        status = ""
    if selected_date:
        try:
            parsed_date = date.fromisoformat(selected_date)
        except ValueError:
            error = "Укажите корректную дату в формате ГГГГ-ММ-ДД."
        else:
            operations_list = operations_list.for_date(parsed_date)
    for field, value in (("material_id", material_id), ("user_id", user_id)):
        if value:
            try:
                if not value.isascii() or not value.isdecimal():
                    raise ValueError
                number = int(value)
                if not 0 < number <= 9223372036854775807:
                    raise ValueError
            except ValueError:
                error = "Выберите корректный материал и пользователя."
            else:
                operations_list = operations_list.filter(**{field: number})
    if query:
        operations_list = operations_list.filter(
            Q(material__name__icontains=query)
            | Q(user__name__icontains=query),
        )
    if error:
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
        "operations": page_obj, "page_obj": page_obj, "status": status,
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
