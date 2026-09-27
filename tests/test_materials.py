import pytest

from models import Material
from models.materials import (
    add_material,
    filter_by_category,
    find_material,
    get_categories,
    get_low_stock_materials,
    remove_material,
    sort_materials,
)


def test_material_creation():
    material = Material(1, "Акварель", "Краски", 5)
    assert material.id == 1
    assert material.name == "Акварель"
    assert material.category == "Краски"
    assert material.count == 5


def test_material_str():
    material = Material(1, "Акварель", "Краски", 5)
    assert str(material) == "Акварель (Краски) - 5 шт."


def test_negative_count_forbidden():
    with pytest.raises(ValueError):
        Material(1, "Акварель", "Краски", -1)


def test_validate_empty_name():
    assert Material.validate("  ", "Краски", 5) != "OK"


def test_from_data():
    data = {"id": 7, "name": "Бисер", "category": "Фурнитура",
            "count": 2, "added_at": "2026-09-20"}
    material = Material.from_data(data)
    assert material.id == 7
    assert material.added_at == "2026-09-20"


def test_check_low_stock():
    material = Material(1, "Бисер", "Фурнитура", 1)
    assert material.is_low_stock()
    assert "заканчивается" in material.check_low_stock()


def test_change_by_not_below_zero():
    material = Material(1, "Бисер", "Фурнитура", 1)
    with pytest.raises(ValueError):
        material.change_by(-5)
    assert material.count == 1


def test_add_material():
    materials = []
    material = add_material(materials, "Акварель", "Краски", 3)
    assert materials == [material]
    assert isinstance(material, Material)


def test_add_same_material_increases_count():
    materials = []
    add_material(materials, "Акварель", "Краски", 3)
    add_material(materials, "акварель", "краски", 2)
    assert len(materials) == 1
    assert materials[0].count == 5


def test_find_material():
    materials = []
    add_material(materials, "Пряжа мохер", "Пряжа", 4)
    assert find_material(materials, "МОХЕР")


def test_filter_and_categories():
    materials = []
    add_material(materials, "Кисть", "Кисти", 10)
    add_material(materials, "Акрил", "Краски", 2)
    assert len(filter_by_category(materials, "краски")) == 1
    assert get_categories(materials) == {"Кисти", "Краски"}


def test_sort_materials_by_count():
    materials = []
    add_material(materials, "Кисть", "Кисти", 10)
    add_material(materials, "Бисер", "Фурнитура", 1)
    result = sort_materials(materials, "count")
    assert [m.count for m in result] == [1, 10]


def test_low_stock_generator():
    materials = []
    add_material(materials, "Кисть", "Кисти", 10)
    add_material(materials, "Бисер", "Фурнитура", 1)
    low = list(get_low_stock_materials(materials))
    assert [m.name for m in low] == ["Бисер"]


def test_remove_missing_material():
    with pytest.raises(KeyError):
        remove_material([], 42)
