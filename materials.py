"""Функции для работы с материалами для творчества."""

import datetime
from collections.abc import Iterator

MIN_STOCK = 3  # минимальный остаток

SORT_KEYS = {
    "name": lambda material: material["name"].lower(),
    "category": lambda material: material["category"].lower(),
    "count": lambda material: material["count"],
}


def validate_material(name: str, category: str, count: int) -> str:
    """Проверить корректность введённых данных (функция из ПР1).

    Возвращает "OK" или текст ошибки.
    """
    if not name.strip():
        return "Ошибка: название материала не может быть пустым."
    if not category.strip():
        return "Ошибка: категория не может быть пустой."
    if count <= 0:
        return "Ошибка: количество должно быть больше нуля."
    return "OK"


def get_next_id(materials: dict[int, dict]) -> int:
    """Вернуть следующий свободный идентификатор материала."""
    return max(materials, default=0) + 1


def find_same_material(
    materials: dict[int, dict],
    name: str,
    category: str
) -> dict | None:
    """Найти материал с тем же названием и категорией.

    Сравнение выполняется без учёта регистра.
    """
    for material in materials.values():
        if (material["name"].lower() == name.strip().lower()
                and material["category"].lower()
                == category.strip().lower()):
            return material
    return None


def add_material(
    materials: dict[int, dict],
    name: str,
    category: str,
    count: int
) -> dict:
    """Добавить материал в учёт и вернуть карточку материала.

    Если такой материал уже есть, его количество увеличивается,
    а новая запись не создаётся.
    """
    existing = find_same_material(materials, name, category)
    if existing is not None:
        existing["count"] += count
        return existing

    material_id = get_next_id(materials)
    material = {
        "id": material_id,
        "name": name.strip(),
        "category": category.strip(),
        "count": count,
        "added_at": datetime.date.today().isoformat(),
    }
    materials[material_id] = material
    return material


def find_material(materials: dict[int, dict], query: str) -> list[dict]:
    """Найти материалы по подстроке названия (без учёта регистра)."""
    query = query.strip().lower()
    return [
        material for material in materials.values()
        if query in material["name"].lower()
    ]


def filter_by_category(
    materials: dict[int, dict],
    category: str
) -> list[dict]:
    """Отобрать материалы указанной категории."""
    category = category.strip().lower()
    return [
        material for material in materials.values()
        if material["category"].lower() == category
    ]


def get_categories(materials: dict[int, dict]) -> set[str]:
    """Вернуть множество категорий, которые есть в учёте."""
    return {material["category"] for material in materials.values()}


def get_low_stock_materials(materials: dict[int, dict]) -> Iterator[dict]:
    """Генератор материалов, остаток которых не больше MIN_STOCK."""
    for material in materials.values():
        if material["count"] <= MIN_STOCK:
            yield material


def sort_materials(
    materials: dict[int, dict],
    by: str = "name"
) -> list[dict]:
    """Отсортировать материалы по названию, категории или количеству.

    Ключ сортировки задаётся lambda-функцией из словаря SORT_KEYS.
    При неизвестном поле возбуждается ValueError.
    """
    if by not in SORT_KEYS:
        raise ValueError(f"Нельзя отсортировать по полю «{by}».")
    return sorted(materials.values(), key=SORT_KEYS[by])


def change_count(
    materials: dict[int, dict],
    material_id: int,
    delta: int
) -> dict:
    """Изменить количество материала на delta.

    Положительное delta - пополнение, отрицательное - расход.
    KeyError - если материала нет, ValueError - если остаток
    станет отрицательным.
    """
    if material_id not in materials:
        raise KeyError(f"Материал с id {material_id} не найден.")
    material = materials[material_id]
    new_count = material["count"] + delta
    if new_count < 0:
        raise ValueError(
            f"Недостаточно материала: в наличии {material['count']} шт."
        )
    material["count"] = new_count
    return material


def remove_material(materials: dict[int, dict], material_id: int) -> dict:
    """Удалить материал из учёта и вернуть его карточку."""
    if material_id not in materials:
        raise KeyError(f"Материал с id {material_id} не найден.")
    return materials.pop(material_id)


def get_statistics(materials: dict[int, dict]) -> dict:
    """Собрать статистику по учёту материалов."""
    by_category: dict[str, int] = {}
    for material in materials.values():
        category = material["category"]
        by_category[category] = (
            by_category.get(category, 0) + material["count"]
        )
    return {
        "total_materials": len(materials),
        "total_count": sum(m["count"] for m in materials.values()),
        "by_category": by_category,
        "low_stock": len(list(get_low_stock_materials(materials))),
    }


def check_low_stock(material: dict) -> str:
    """Проверить остаток материала (функция из ПР1)."""
    if material["count"] <= MIN_STOCK:
        return f"Внимание: материал «{material['name']}» заканчивается!"
    return f"Материал «{material['name']}» в достаточном количестве."
