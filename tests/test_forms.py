"""ПР11: валидация, пользовательские операции, остатки и CSRF."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from materials.models import Material
from operations.forms import OperationFilterForm, OperationForm
from operations.models import Operation, User


def data(**changes):
    values = {
        "material": Material.objects.first().pk,
        "user": User.objects.first().pk, "amount": -1,
        "created_at": timezone.localdate().isoformat(),
    }
    values.update(changes)
    return values


def test_filter_unbound_and_typed_values():
    assert not OperationFilterForm().is_bound
    values = data()
    form = OperationFilterForm({
        "date": values["created_at"], "material": values["material"],
        "user": values["user"], "sort": "material", "status": "active",
    })
    assert form.is_valid()
    assert form.cleaned_data["date"] == timezone.localdate()
    assert isinstance(form.cleaned_data["material"], Material)
    assert isinstance(form.cleaned_data["user"], User)


@pytest.mark.parametrize("values,field", [
    ({"date": "2026-02-30"}, "date"),
    ({"material": "999999"}, "material"),
    ({"user": "999999"}, "user"),
    ({"material": "9" * 100}, "material"),
    ({"status": "unknown"}, "status"),
    ({"sort": "material__count"}, "sort"),
])
def test_filter_rejects_invalid_values(values, field):
    response = Client().get(reverse("operations:list"), values)
    assert response.status_code == 200
    assert field in response.context["form"].errors
    assert response.context["page_obj"].paginator.count == 0


def test_filter_preserves_bound_values_and_errors():
    response = Client().get(reverse("operations:list"), {
        "q": "Акварель", "date": "2026-02-30", "sort": "user",
    })
    form = response.context["form"]
    assert form.is_bound
    assert form["q"].value() == "Акварель"
    assert form["date"].value() == "2026-02-30"
    html = response.content.decode()
    assert 'value="Акварель"' in html
    assert "Укажите корректную дату" in html


def test_create_get_does_not_write_and_uses_default_date():
    before = Operation.objects.count()
    response = Client().get(reverse("operations:create"))
    form = response.context["form"]
    assert response.status_code == 200
    assert not form.is_bound
    assert form["created_at"].value() == timezone.localdate()
    assert set(form.fields) == {"material", "user", "amount", "created_at"}
    assert Operation.objects.count() == before


@pytest.mark.parametrize("offset,amount", [(0, -1), (1, 5)])
def test_create_saves_once_and_ignores_injected_status(offset, amount):
    material = Material.objects.first()
    before_count, before_rows = material.count, Operation.objects.count()
    response = Client().post(reverse("operations:create"), data(
        material=material.pk, amount=amount, status="cancelled", id=999999,
        created_at=(timezone.localdate() + timedelta(days=offset)).isoformat(),
    ))
    assert response.status_code == 302
    assert response.url == reverse("operations:list")
    assert Operation.objects.count() == before_rows + 1
    operation = Operation.objects.order_by("pk").last()
    assert operation.status == Operation.Status.ACTIVE
    assert operation.pk != 999999
    material.refresh_from_db()
    assert material.count == before_count + amount


@pytest.mark.parametrize("changes,field", [
    ({"amount": 0}, "amount"), ({"amount": "1.5"}, "amount"),
    ({"amount": "не число"}, "amount"),
    ({"amount": "9" * 100}, "amount"),
    ({"material": ""}, "material"), ({"user": 999999}, "user"),
    ({"created_at": "2026-02-30"}, "created_at"),
    ({"created_at": ""}, "created_at"),
])
def test_invalid_create_does_not_change_database(changes, field):
    before = list(Material.objects.values_list("pk", "count"))
    rows = Operation.objects.count()
    response = Client().post(reverse("operations:create"), data(**changes))
    assert response.status_code == 200
    assert field in response.context["form"].errors
    assert Operation.objects.count() == rows
    assert list(Material.objects.values_list("pk", "count")) == before


def test_past_date_is_rejected_without_saving():
    form = OperationForm(data(created_at=(
        timezone.localdate() - timedelta(days=1)
    ).isoformat()))
    assert not form.is_valid()
    assert "created_at" in form.errors


def test_stock_availability_and_cancelled_history():
    material = Material.objects.create(name="Запас", category="Тест", count=2)
    client = Client()
    values = data(material=material.pk, amount=-2)
    assert client.post(reverse("operations:create"), values).status_code == 302
    first = Operation.objects.order_by("pk").last()
    response = client.post(reverse("operations:create"), values)
    assert "amount" in response.context["form"].errors
    material.refresh_from_db()
    assert material.count == 0
    cancel_url = reverse("operations:cancel", args=[first.pk])
    assert client.post(cancel_url).status_code == 302
    material.refresh_from_db()
    assert material.count == 2
    assert client.post(reverse("operations:create"), values).status_code == 302
    first.refresh_from_db()
    assert first.status == Operation.Status.CANCELLED


def test_edit_preserves_identity_original_date_and_own_effect():
    operation = Operation.objects.first()
    material = operation.material
    before_count, before_rows = material.count, Operation.objects.count()
    client = Client()
    url = reverse("operations:update", args=[operation.pk])
    response = client.get(url)
    assert response.context["form"].instance.pk == operation.pk
    values = data(
        material=material.pk, user=operation.user_id, amount=operation.amount,
        created_at=operation.created_at.isoformat(),
    )
    assert client.post(url, values).status_code == 302
    material.refresh_from_db()
    assert material.count == before_count
    values["amount"] = operation.amount + 2
    assert client.post(url, values).status_code == 302
    material.refresh_from_db()
    operation.refresh_from_db()
    assert material.count == before_count + 2
    assert operation.amount == values["amount"]
    assert Operation.objects.count() == before_rows


def test_edit_can_use_entire_original_stock_and_rejects_conflict():
    material = Material.objects.create(name="Запас", category="Тест", count=3)
    operation = Operation.objects.create(
        material=material, user=User.objects.first(), amount=-3,
    )
    url = reverse("operations:update", args=[operation.pk])
    values = data(material=material.pk, amount=-3)
    client = Client()
    assert client.post(url, values).status_code == 302
    values["amount"] = -4
    response = client.post(url, values)
    assert "amount" in response.context["form"].errors
    operation.refresh_from_db()
    material.refresh_from_db()
    assert operation.amount == -3
    assert material.count == 0


def test_edit_moves_effect_to_other_material():
    original = Material.objects.create(name="Первый", category="Тест", count=5)
    target = Material.objects.create(name="Второй", category="Тест", count=3)
    operation = Operation.objects.create(
        material=original, user=User.objects.first(), amount=-2,
    )
    response = Client().post(reverse("operations:update", args=[operation.pk]),
                             data(material=target.pk, amount=-3))
    assert response.status_code == 302
    original.refresh_from_db()
    target.refresh_from_db()
    assert (original.count, target.count) == (5, 0)


def test_edit_rejects_different_past_date():
    operation = Operation.objects.first()
    changed_date = min(
        operation.created_at, timezone.localdate(),
    ) - timedelta(days=1)
    response = Client().post(reverse("operations:update", args=[operation.pk]),
                             data(created_at=changed_date.isoformat()))
    assert "created_at" in response.context["form"].errors


@pytest.mark.parametrize("status", ["cancelled", "completed"])
def test_inactive_operations_cannot_be_edited_or_cancelled(status):
    operation = Operation.objects.create(
        material=Material.objects.first(), user=User.objects.first(),
        amount=1, status=status,
    )
    client = Client()
    url = reverse("operations:update", args=[operation.pk])
    assert client.get(url).status_code == 404
    assert client.post(url, data()).status_code == 404
    cancel_url = reverse("operations:cancel", args=[operation.pk])
    assert client.post(cancel_url).status_code == 404


def test_cancel_only_post_and_exactly_once():
    operation = Operation.objects.first()
    before, amount = operation.material.count, operation.amount
    url = reverse("operations:cancel", args=[operation.pk])
    client = Client()
    assert client.get(url).status_code == 405
    operation.refresh_from_db()
    assert operation.status == Operation.Status.ACTIVE
    assert client.post(url).status_code == 302
    operation.refresh_from_db()
    operation.material.refresh_from_db()
    assert operation.status == Operation.Status.CANCELLED
    assert operation.material.count == before - amount
    assert client.post(url).status_code == 404


def test_cancel_insufficient_restock_is_shown_without_partial_change():
    material = Material.objects.create(name="Запас", category="Тест", count=0)
    restock = Operation.objects.create(
        material=material, user=User.objects.first(), amount=2,
    )
    Operation.objects.create(
        material=material, user=User.objects.first(), amount=-2,
    )
    response = Client().post(reverse("operations:cancel", args=[restock.pk]))
    assert response.status_code == 400
    assert "Недостаточно материала" in response.content.decode()
    restock.refresh_from_db()
    material.refresh_from_db()
    assert restock.status == Operation.Status.ACTIVE
    assert material.count == 0


@pytest.mark.parametrize("route,method", [
    ("detail", "get"), ("update", "get"),
    ("update", "post"), ("cancel", "post"),
])
def test_missing_object(route, method):
    url = reverse(f"operations:{route}", args=[999999])
    response = getattr(Client(), method)(url)
    assert response.status_code == 404


@pytest.mark.parametrize("action", ["create", "update", "cancel"])
def test_csrf_rejects_missing_token_and_accepts_real_form(action):
    client = Client(enforce_csrf_checks=True)
    operation = Operation.objects.first()
    args = [] if action == "create" else [operation.pk]
    url = reverse(f"operations:{action}", args=args)
    values = data()
    assert client.post(url, values).status_code == 403
    page = (
        reverse("operations:detail", args=args) if action == "cancel" else url
    )
    assert client.get(page).status_code == 200
    values["csrfmiddlewaretoken"] = client.cookies["csrftoken"].value
    assert client.post(url, values).status_code == 302


@pytest.mark.parametrize("failure", [ValidationError("Остаток изменился."),
                                     IntegrityError("hidden database detail")])
def test_save_error_is_displayed_as_non_field_error(failure):
    before = list(Material.objects.values_list("pk", "count"))
    rows = Operation.objects.count()
    with patch("operations.forms.OperationForm.save", side_effect=failure):
        response = Client().post(reverse("operations:create"), data())
    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
    assert "hidden database detail" not in response.content.decode()
    assert Operation.objects.count() == rows
    assert list(Material.objects.values_list("pk", "count")) == before
