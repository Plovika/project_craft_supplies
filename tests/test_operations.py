import pytest

from models import Material, Operation, User
from models.operations import (
    cancel_operation,
    create_operation,
    get_material_history,
)


@pytest.fixture
def material():
    return Material(1, "Акварель", "Краски", 5)


@pytest.fixture
def user():
    return User(1, "Анна", "anna@example.com")


def test_operation_creation(material, user):
    operation = Operation(1, material, user, -2, "2026-09-27")
    assert operation.material is material
    assert operation.user is user
    assert operation.kind == "Расход"
    assert not operation.is_cancelled
    assert material.count == 5  # конструктор не меняет количество


def test_create_usage_decreases_count(material, user):
    operations = []
    operation = create_operation(operations, material, user, -2)
    assert operation in operations
    assert material.count == 3


def test_create_restock_increases_count(material, user):
    operation = create_operation([], material, user, 4)
    assert operation.kind == "Пополнение"
    assert material.count == 9


def test_usage_more_than_available_forbidden(material, user):
    operations = []
    assert create_operation(operations, material, user, -10) is None
    assert operations == []
    assert material.count == 5


def test_cancel_restores_count(material, user):
    operations = []
    operation = create_operation(operations, material, user, -2)
    operation.cancel()
    assert operation.is_cancelled
    assert material.count == 5
    assert operation in operations  # операция не удаляется


def test_cancel_twice_forbidden(material, user):
    operation = create_operation([], material, user, -1)
    operation.cancel()
    with pytest.raises(ValueError):
        operation.cancel()


def test_cancel_operation_not_found():
    assert cancel_operation([], 99) is False


def test_operation_str(material, user):
    operation = create_operation([], material, user, -2)
    operation.cancel()
    assert "Расход" in str(operation)
    assert "[отменена]" in str(operation)


def test_material_history(material, user):
    operations = []
    create_operation(operations, material, user, -1)
    other = Material(2, "Кисть", "Кисти", 3)
    create_operation(operations, other, user, 1)
    assert len(get_material_history(operations, material)) == 1
