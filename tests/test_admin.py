"""Админка, права, миграции ПР10 и согласованность остатков."""

from datetime import date
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, connections, models
from django.db.migrations.executor import MigrationExecutor
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from materials.models import Material
from operations.models import Operation, User


@pytest.fixture
def admin_client():
    user = get_user_model().objects.create_user(
        username="test-admin", is_staff=True, is_superuser=True,
    )
    client = Client()
    client.force_login(user)
    return client


def operation_data(**extra):
    data = {
        "material": Material.objects.first().pk,
        "user": User.objects.first().pk, "amount": 3,
        "created_at": "2026-11-15", "status": Operation.Status.ACTIVE,
        "_save": "Сохранить",
    }
    data.update(extra)
    return data


@pytest.mark.parametrize("route", [
    "admin:index", "admin:materials_material_changelist",
    "admin:operations_user_changelist",
    "admin:operations_operation_changelist",
])
def test_admin_pages(admin_client, route):
    assert admin_client.get(reverse(route)).status_code == 200


def test_admin_search_filter_and_inline(admin_client):
    operation = Operation.objects.first()
    response = admin_client.get(
        reverse("admin:operations_operation_changelist"), {
            "q": operation.material.name,
            "status__exact": Operation.Status.ACTIVE,
        },
    )
    assert response.status_code == 200
    assert list(response.context["cl"].result_list) == [operation]
    for model, obj in [("materials_material", operation.material),
                       ("operations_user", operation.user)]:
        response = admin_client.get(reverse(
            f"admin:{model}_change", args=[obj.pk],
        ))
        assert response.status_code == 200
        inline = response.context["inline_admin_formsets"][0]
        assert list(inline.formset.queryset) == [operation]
        assert not inline.opts.can_delete
        assert not inline.opts.has_add_permission(response.wsgi_request, obj)


def test_staff_group_permissions():
    group = Group.objects.create(name="Craftbox Operators")
    group.permissions.set(Permission.objects.filter(
        content_type__app_label="materials", content_type__model="material",
        codename__in=["view_material", "add_material", "change_material"],
    ))
    user = get_user_model().objects.create_user(
        username="operator", is_staff=True,
    )
    user.groups.add(group)
    client = Client()
    client.force_login(user)
    material = Material.objects.first()
    assert client.get(
        reverse("admin:materials_material_changelist"),
    ).status_code == 200
    assert client.get(
        reverse("admin:materials_material_add"),
    ).status_code == 200
    assert client.get(reverse(
        "admin:materials_material_change", args=[material.pk],
    )).status_code == 200
    assert client.get(reverse(
        "admin:materials_material_delete", args=[material.pk],
    )).status_code == 403


def test_admin_create_update_cancel_restore_delete(admin_client):
    material = Material.objects.first()
    before = material.count
    response = admin_client.post(reverse("admin:operations_operation_add"),
                                 operation_data(material=material.pk))
    assert response.status_code == 302
    operation = Operation.objects.order_by("pk").last()
    material.refresh_from_db()
    assert material.count == before + 3
    change_url = reverse(
        "admin:operations_operation_change", args=[operation.pk],
    )
    response = admin_client.post(change_url, operation_data(
        material=material.pk, amount=5,
    ))
    assert response.status_code == 302
    material.refresh_from_db()
    assert material.count == before + 5
    listing = reverse("admin:operations_operation_changelist")
    for action, expected in [("cancel_operations", before),
                             ("restore_operations", before + 5)]:
        response = admin_client.post(listing, {
            "action": action, "_selected_action": [operation.pk],
        })
        assert response.status_code == 302
        material.refresh_from_db()
        assert material.count == expected
    response = admin_client.post(listing, {
        "action": "delete_selected", "_selected_action": [operation.pk],
        "post": "yes",
    })
    assert response.status_code == 302
    material.refresh_from_db()
    assert material.count == before
    assert not Operation.objects.filter(pk=operation.pk).exists()


def test_admin_bad_usage_shows_form_error(admin_client):
    material = Material.objects.first()
    before = material.count
    response = admin_client.post(reverse("admin:operations_operation_add"),
                                 operation_data(amount=-1000))
    assert response.status_code == 200
    assert "Недостаточно материала" in response.content.decode()
    material.refresh_from_db()
    assert material.count == before


def test_admin_handles_database_error_and_rolls_back(admin_client):
    material = Material.objects.first()
    before = material.count
    with patch.object(
        models.Model, "save", side_effect=IntegrityError("test"),
    ):
        response = admin_client.post(reverse("admin:operations_operation_add"),
                                     operation_data(material=material.pk))
    assert response.status_code == 302
    material.refresh_from_db()
    assert material.count == before
    response = admin_client.get(response.url)
    assert "Не удалось сохранить данные" in response.content.decode()


def test_orm_operation_updates_and_moves_stock():
    first = Material.objects.get(pk=1)
    second = Material.objects.get(pk=2)
    before_first, before_second = first.count, second.count
    operation = Operation.objects.create(
        material=first, user=User.objects.first(), amount=4,
    )
    first.refresh_from_db()
    assert first.count == before_first + 4
    operation.amount = 7
    operation.save(update_fields=["amount"])
    first.refresh_from_db()
    assert first.count == before_first + 7
    operation.material = second
    operation.save(update_fields=["material"])
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.count == before_first
    assert second.count == before_second + 7
    operation.status = Operation.Status.COMPLETED
    operation.save(update_fields=["status"])
    second.refresh_from_db()
    assert second.count == before_second + 7
    operation.cancel()
    second.refresh_from_db()
    assert second.count == before_second
    operation.restore()
    second.refresh_from_db()
    assert second.count == before_second + 7
    Operation.objects.filter(pk=operation.pk).delete()
    second.refresh_from_db()
    assert second.count == before_second


def test_partial_save_does_not_apply_unsaved_amount():
    operation = Operation.objects.first()
    material = operation.material
    before = material.count
    old_amount = operation.amount
    operation.amount = 100
    operation.created_at = date(2026, 11, 1)
    operation.save(update_fields=["created_at"])
    operation.refresh_from_db()
    material.refresh_from_db()
    assert material.count == before
    assert operation.amount == old_amount


def test_failed_operation_change_rolls_back():
    operation = Operation.objects.first()
    material = operation.material
    before = material.count
    operation.amount = -1000
    with pytest.raises(ValidationError):
        operation.save()
    material.refresh_from_db()
    assert material.count == before
    operation.refresh_from_db()
    assert operation.amount != -1000


def test_bulk_action_failure_is_atomic(admin_client):
    material = Material.objects.first()
    first = Operation.objects.create(
        material=material, user=User.objects.first(), amount=4,
    )
    second = Operation.objects.create(
        material=material, user=User.objects.first(), amount=100,
    )
    Material.objects.filter(pk=material.pk).update(count=10)
    response = admin_client.post(
        reverse("admin:operations_operation_changelist"), {
            "action": "cancel_operations",
            "_selected_action": [first.pk, second.pk],
        },
    )
    assert response.status_code == 302
    first.refresh_from_db()
    second.refresh_from_db()
    material.refresh_from_db()
    assert first.status == second.status == Operation.Status.ACTIVE
    assert material.count == 10


def test_slug_generated_field_and_old_url():
    material = Material.objects.create(
        name="Акварель тест", category="Тест", count=3,
    )
    assert material.slug.isascii()
    assert material.slug.endswith(f"-{material.pk}")
    assert material.is_low_stock
    old_slug = material.slug
    material.name = "Другое название"
    material.count = 4
    material.save()
    material.refresh_from_db()
    assert not material.is_low_stock
    assert material.slug == old_slug
    client = Client()
    response = client.get(f"/materials/{material.pk}/")
    assert response.status_code == 301
    assert response.url == material.get_absolute_url()
    assert client.get(response.url).status_code == 200
    assert client.get("/materials/missing-material/").status_code == 404


@pytest.mark.parametrize("path", ["/", "/materials/", "/operations/"])
def test_context_processor_is_live(path):
    client = Client()
    before = client.get(path)
    expected = Material.objects.count()
    assert before.context["site_materials_count"] == expected
    assert before.context["site_name"] == "Мастерская"
    Material.objects.create(name="Новый", category="Тест", count=0)
    after = client.get(path)
    assert after.context["site_materials_count"] == expected + 1
    assert f"Материалы ({expected + 1})" in after.content.decode()


def test_status_manager_statistics_and_filters():
    user = User.objects.first()
    material = Material.objects.first()
    completed = Operation.objects.create(
        material=material, user=user, amount=1,
        status=Operation.Status.COMPLETED, created_at=date(2026, 11, 15),
    )
    cancelled = Operation.objects.create(
        material=material, user=user, amount=2,
        status=Operation.Status.CANCELLED,
    )
    assert completed in Operation.objects.completed().for_date(
        date(2026, 11, 15),
    )
    assert cancelled in Operation.objects.cancelled()
    client = Client()
    response = client.get("/operations/", {"status": "completed"})
    assert [
        row["id"] for row in response.context["operations"]
    ] == [completed.pk]
    stats = client.get("/statistics/").context["operation_totals"]
    assert stats == {"total": 3, "active": 1, "cancelled": 1, "completed": 1}


def test_admin_list_has_no_n_plus_one(admin_client):
    route = reverse("admin:operations_operation_changelist")
    with CaptureQueriesContext(connection) as baseline:
        assert admin_client.get(route).status_code == 200
    for _ in range(5):
        Operation.objects.create(
            material=Material.objects.first(), user=User.objects.first(),
            amount=1,
        )
    with CaptureQueriesContext(connection) as expanded:
        assert admin_client.get(route).status_code == 200
    assert len(expanded) == len(baseline)


def test_status_data_migration_with_historical_models(tmp_path):
    from copy import deepcopy
    from importlib import import_module

    executor = MigrationExecutor(connection)
    apps = executor.loader.project_state([
        ("operations", "0002_operation_status"),
    ]).apps
    migration = import_module(
        "operations.migrations.0003_migrate_operation_statuses",
    )
    alias = "migration_audit"
    settings = deepcopy(connection.settings_dict)
    settings["NAME"] = str(tmp_path / "historical.sqlite3")
    connections.databases[alias] = settings
    historical_connection = connections[alias]
    material = apps.get_model("materials", "Material")
    user = apps.get_model("operations", "User")
    operation = apps.get_model("operations", "Operation")
    try:
        with historical_connection.schema_editor() as editor:
            editor.create_model(material)
            editor.create_model(user)
            editor.create_model(operation)
        material.objects.using(alias).create(
            pk=1, name="Материал", category="Тест", count=9,
        )
        user.objects.using(alias).create(
            pk=1, name="Тест", email="t@example.com",
        )
        for flag in [False, True]:
            operation.objects.using(alias).create(
                material_id=1, user_id=1, amount=2, is_cancelled=flag,
            )
        with historical_connection.schema_editor() as editor:
            migration.forwards(apps, editor)
        assert list(operation.objects.using(alias).order_by("pk").values_list(
            "is_cancelled", "status",
        )) == [(False, "active"), (True, "cancelled")]
        assert material.objects.using(alias).get(pk=1).count == 9
        with historical_connection.schema_editor() as editor:
            migration.backwards(apps, editor)
        assert list(operation.objects.using(alias).order_by("pk").values_list(
            "is_cancelled", flat=True,
        )) == [False, True]
    finally:
        historical_connection.close()
        del connections[alias]
        del connections.databases[alias]


def test_inline_edit_updates_stock(admin_client):
    operation = Operation.objects.first()
    material = operation.material
    before, amount = material.count, operation.amount
    response = admin_client.post(reverse(
        "admin:materials_material_change", args=[material.pk],
    ), {
        "name": material.name, "category": material.category,
        "count": before, "added_at": material.added_at.isoformat(),
        "operations-TOTAL_FORMS": 1, "operations-INITIAL_FORMS": 1,
        "operations-MIN_NUM_FORMS": 0, "operations-MAX_NUM_FORMS": 0,
        "operations-0-id": operation.pk,
        "operations-0-material": material.pk,
        "operations-0-user": operation.user_id,
        "operations-0-amount": amount + 2,
        "operations-0-created_at": operation.created_at.isoformat(),
        "operations-0-status": operation.status, "_save": "Сохранить",
    })
    assert response.status_code == 302
    material.refresh_from_db()
    operation.refresh_from_db()
    assert material.count == before + 2
    assert operation.amount == amount + 2


def test_available_stock_follows_agreed_status_rules():
    material = Material.objects.create(name="Запас", category="Тест", count=3)
    operation = Operation.objects.create(
        material=material, user=User.objects.first(), amount=-3,
    )

    def available():
        return Material.objects.filter(pk=material.pk, count__gt=0).exists()

    assert not available()
    operation.status = Operation.Status.COMPLETED
    operation.save(update_fields=["status"])
    assert not available()
    operation.cancel()
    assert available()
    operation.restore()
    assert not available()


def test_admin_cannot_delete_material_with_history(admin_client):
    material = Operation.objects.first().material
    response = admin_client.get(reverse(
        "admin:materials_material_delete", args=[material.pk],
    ))
    assert response.status_code == 200
    assert response.context["protected"]
    assert Material.objects.filter(pk=material.pk).exists()
