from models import Material, Operation, User
from storage import (
    load_materials,
    load_operations,
    load_users,
    save_materials,
    save_operations,
    save_users,
)


def test_save_and_load_materials(tmp_path):
    filename = tmp_path / "materials.json"
    save_materials([Material(1, "Кисть", "Кисти", 2, "2026-09-27")],
                   filename)
    loaded = load_materials(filename)
    assert isinstance(loaded[0], Material)
    assert loaded[0].name == "Кисть"
    assert loaded[0].count == 2


def test_save_and_load_users(tmp_path):
    filename = tmp_path / "users.json"
    save_users([User(1, "Анна", "anna@example.com")], filename)
    loaded = load_users(filename)
    assert isinstance(loaded[0], User)
    assert loaded[0].email == "anna@example.com"


def test_operations_links_restored(tmp_path):
    filename = tmp_path / "operations.json"
    material = Material(1, "Кисть", "Кисти", 2)
    user = User(1, "Анна", "anna@example.com")
    operation = Operation(1, material, user, -1, "2026-09-27")
    operation.is_cancelled = True
    save_operations([operation], filename)

    loaded = load_operations([material], [user], filename)
    assert loaded[0].material is material
    assert loaded[0].user is user
    assert loaded[0].is_cancelled


def test_operation_with_unknown_material_skipped(tmp_path):
    filename = tmp_path / "operations.json"
    material = Material(1, "Кисть", "Кисти", 2)
    user = User(1, "Анна", "anna@example.com")
    save_operations([Operation(1, material, user, -1)], filename)
    assert load_operations([], [user], filename) == []


def test_load_missing_file(tmp_path):
    assert load_materials(tmp_path / "nope.json") == []


def test_load_broken_json(tmp_path):
    filename = tmp_path / "broken.json"
    filename.write_text("{ это не json", encoding="utf-8")
    assert load_users(filename) == []
