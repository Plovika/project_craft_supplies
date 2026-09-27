import pytest

from materials import (
    add_material,
    change_count,
    check_low_stock,
    find_material,
    get_low_stock_materials,
    remove_material,
    sort_materials,
    validate_material,
)


def test_validate_material_empty_name():
    assert validate_material("  ", "Краски", 5) != "OK"


def test_add_material():
    materials = {}
    add_material(materials, "Акварель", "Краски", 3)
    assert len(materials) == 1


def test_add_same_material_increases_count():
    materials = {}
    add_material(materials, "Акварель", "Краски", 3)
    add_material(materials, "акварель", "краски", 2)
    assert len(materials) == 1
    assert materials[1]["count"] == 5


def test_find_material():
    materials = {}
    add_material(materials, "Пряжа мохер", "Пряжа", 4)
    assert find_material(materials, "МОХЕР")


def test_sort_materials_by_count():
    materials = {}
    add_material(materials, "Кисть", "Кисти", 10)
    add_material(materials, "Бисер", "Фурнитура", 1)
    result = sort_materials(materials, "count")
    assert [m["count"] for m in result] == [1, 10]


def test_low_stock_generator():
    materials = {}
    add_material(materials, "Кисть", "Кисти", 10)
    add_material(materials, "Бисер", "Фурнитура", 1)
    low = list(get_low_stock_materials(materials))
    assert [m["name"] for m in low] == ["Бисер"]


def test_change_count_negative_forbidden():
    materials = {}
    add_material(materials, "Бисер", "Фурнитура", 1)
    with pytest.raises(ValueError):
        change_count(materials, 1, -5)


def test_remove_missing_material():
    with pytest.raises(KeyError):
        remove_material({}, 42)


def test_check_low_stock():
    material = {"name": "Бисер", "count": 1}
    assert "заканчивается" in check_low_stock(material)
