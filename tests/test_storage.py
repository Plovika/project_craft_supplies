from storage import load_materials, save_materials


def test_save_and_load(tmp_path):
    filename = tmp_path / "materials.json"
    materials = {
        1: {"id": 1, "name": "Кисть", "category": "Кисти",
            "count": 2, "added_at": "2026-09-27"}
    }
    assert save_materials(materials, filename)
    assert load_materials(filename) == materials


def test_load_missing_file(tmp_path):
    assert load_materials(tmp_path / "nope.json") == {}


def test_load_broken_json(tmp_path):
    filename = tmp_path / "broken.json"
    filename.write_text("{ это не json", encoding="utf-8")
    assert load_materials(filename) == {}
