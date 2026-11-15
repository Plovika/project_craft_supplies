import json
from datetime import date
from unittest.mock import patch

import pytest
from django.db import IntegrityError, connection, transaction
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.test import Client
from django.test.utils import CaptureQueriesContext, setup_test_environment

from db.database import BASE_DIR
from db.import_sqlite_to_orm import import_source
from materials.models import Material
from operations.models import Operation, User

setup_test_environment()
client = Client()


def count_json(name):
    with open(BASE_DIR / "data" / name, encoding="utf-8") as file:
        return len(json.load(file))


@pytest.mark.parametrize("model,filename", [
    (Material, "materials.json"), (User, "users.json"),
    (Operation, "operations.json"),
])
def test_import_counts_and_ids(model, filename):
    assert model.objects.count() == count_json(filename)
    with open(BASE_DIR / "data" / filename, encoding="utf-8") as file:
        expected = {record["id"] for record in json.load(file)}
    assert set(model.objects.values_list("pk", flat=True)) == expected


def test_import_preserves_relations_dates_and_counts(test_db):
    operation = Operation.objects.select_related("material", "user").get(pk=1)
    material = operation.material
    original_count = material.count
    assert operation.material_id == material.pk
    assert operation.user_id == User.objects.get(pk=1).pk
    assert isinstance(operation.created_at, date)
    assert isinstance(material.added_at, date)
    import_source(test_db)
    assert Operation.objects.count() == count_json("operations.json")
    material.refresh_from_db()
    assert material.count == original_count


def test_import_rolls_back_on_error(test_db):
    Material.objects.filter(pk=1).update(name="До импорта")
    with patch.object(
        User.objects, "update_or_create", side_effect=ValueError,
    ):
        with pytest.raises(ValueError):
            import_source(test_db)
    assert Material.objects.get(pk=1).name == "До импорта"


def test_model_crud():
    material = Material.objects.create(name="Тест", category="Тест", count=4)
    material.count = 7
    material.save(update_fields=["count"])
    material.refresh_from_db()
    assert material.count == 7
    identifier = material.pk
    material.delete()
    assert not Material.objects.filter(pk=identifier).exists()


def test_constraints_and_protected_history():
    operation = Operation.objects.get(pk=1)
    with pytest.raises(ProtectedError):
        operation.material.delete()
    with pytest.raises(ProtectedError):
        operation.user.delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        Operation.objects.create(
            material=operation.material, user=operation.user, amount=0,
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        Material.objects.create(name="Минус", category="Тест", count=-1)
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(name="Дубль", email=operation.user.email)


def test_cancel_restores_count_once():
    operation = Operation.objects.select_related("material").get(pk=1)
    before = operation.material.count
    operation.cancel()
    operation.refresh_from_db()
    operation.material.refresh_from_db()
    assert operation.is_cancelled
    assert operation.material.count == before - operation.amount
    with pytest.raises(ValueError):
        operation.cancel()


def test_cannot_cancel_restock_after_consumption():
    material = Material.objects.create(name="Тест", category="Тест", count=1)
    operation = Operation.objects.create(
        material=material, user=User.objects.first(), amount=5,
    )
    with pytest.raises(ValueError):
        operation.cancel()
    material.refresh_from_db()
    operation.refresh_from_db()
    assert material.count == 1
    assert not operation.is_cancelled


def test_forward_and_reverse_relations_without_extra_queries():
    with CaptureQueriesContext(connection) as queries:
        operation = Operation.objects.select_related("material", "user").get(
            pk=1,
        )
        assert operation.material.name
        assert operation.user.name
    assert len(queries) == 1
    assert operation in operation.material.operations.all()
    assert operation in operation.user.operations.all()


def test_search_and_sql_injection():
    response = client.get("/materials/search/", {
        "category": "Краски", "max_count": "3", "q": "Акварель",
    })
    assert [m.pk for m in response.context["materials"]] == [1]
    response = client.get("/materials/search/", {"category": "' OR 1=1 --"})
    assert list(response.context["materials"]) == []


@pytest.mark.parametrize("value", ["-1", "abc", "²", "9" * 100, "1.5"])
def test_invalid_stock(value):
    response = client.get("/materials/search/", {"max_count": value})
    assert response.status_code == 200
    assert response.context["error"]


@pytest.mark.parametrize("parameters", [
    {"date": "не дата"}, {"material": "²"}, {"user": "-1"},
    {"material": "9" * 100},
])
def test_invalid_operation_filters(parameters):
    response = client.get("/operations/", parameters)
    assert response.status_code == 200
    assert response.context["error"]


def test_operations_search_filters_sort_and_pages():
    user = User.objects.first()
    material = Material.objects.get(pk=1)
    Operation.objects.bulk_create([
        Operation(material=material, user=user, amount=-1,
                  created_at=date(2026, 10, 1))
        for _ in range(7)
    ])
    parameters = {
        "status": "active", "date": "2026-10-01", "material": material.pk,
        "user": user.pk, "q": "Акварель", "sort": "user", "page": 2,
    }
    response = client.get("/operations/", parameters)
    page = response.context["page_obj"]
    assert page.number == 2
    assert page.paginator.count == 7
    assert len(page) == 2
    html = response.content.decode()
    assert "page=1" in html
    for parameter in ["status=active", "sort=user", "date=2026-10-01"]:
        assert parameter in html
    for page_value, expected in [("abc", 1), ("9999", 2), ("-1", 2)]:
        parameters["page"] = page_value
        response = client.get("/operations/", parameters)
        assert response.context["page_obj"].number == expected


def test_sort_allowlist_and_cancelled_filter():
    operation = Operation.objects.get(pk=1)
    operation.is_cancelled = True
    operation.save(update_fields=["is_cancelled"])
    active = client.get("/operations/", {"status": "active"})
    assert active.context["page_obj"].paginator.count == 0
    cancelled = client.get("/operations/", {"status": "cancelled"})
    assert cancelled.context["page_obj"].paginator.count == 1
    response = client.get("/operations/", {"sort": "invalid__field"})
    assert response.status_code == 200
    assert response.context["sort"] == "date"


def test_statistics_preserve_objects_without_operations():
    operation = Operation.objects.get(pk=1)
    operation.is_cancelled = True
    operation.save(update_fields=["is_cancelled"])
    response = client.get("/statistics/")
    context = response.context
    assert context["active_operations"] == 0
    assert len(context["by_material"]) == Material.objects.count()
    assert all(row["operations_count"] == 0 for row in context["by_material"])
    assert all(row["total_change"] == 0 for row in context["by_material"])
    assert len(context["by_user"]) == User.objects.count()
    expected = sum(Material.objects.values_list("count", flat=True))
    assert context["totals"]["total_count"] == expected
    assert all(
        row["materials_count"] >= 2 for row in context["big_categories"]
    )
    assert list(Material.objects.values("category").annotate(n=Count("id")))


def test_empty_statistics():
    Operation.objects.all().delete()
    Material.objects.all().delete()
    User.objects.all().delete()
    response = client.get("/statistics/")
    assert response.status_code == 200
    assert response.context["totals"]["materials_count"] == 0
    assert response.context["totals"]["total_count"] == 0


@pytest.mark.parametrize("prefix", ["materials", "operations"])
def test_large_missing_id(prefix):
    assert client.get(f"/{prefix}/9223372036854775808/").status_code == 404
