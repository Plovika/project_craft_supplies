"""Класс Material и функции работы с коллекцией материалов."""

from collections.abc import Iterator
from datetime import date


class Material:
    """Материал для творчества."""

    MIN_STOCK = 3  # атрибут класса: общий порог для всех материалов

    def __init__(
        self,
        material_id: int,
        name: str,
        category: str,
        count: int,
        added_at: str | None = None,
    ) -> None:
        """Создать объект материала."""
        self.id = material_id
        self.name = name
        self.category = category
        self.count = count  # проверяется через сеттер свойства
        self.added_at = added_at or date.today().isoformat()

    @property
    def count(self) -> int:
        """Количество материала в наличии."""
        return self._count

    @count.setter
    def count(self, value: int) -> None:
        """Установить количество, не допуская отрицательных значений."""
        if not Material.validate_count(value):
            raise ValueError("Количество не может быть отрицательным.")
        self._count = value

    @staticmethod
    def validate_count(count: int) -> bool:
        """Проверить, что количество - целое неотрицательное число."""
        return isinstance(count, int) and count >= 0

    @staticmethod
    def validate(name: str, category: str, count: int) -> str:
        """Проверить данные нового материала (validate_material из ПР1).

        Возвращает "OK" или текст ошибки.
        """
        if not name.strip():
            return "Ошибка: название материала не может быть пустым."
        if not category.strip():
            return "Ошибка: категория не может быть пустой."
        if count <= 0:
            return "Ошибка: количество должно быть больше нуля."
        return "OK"

    @classmethod
    def from_data(cls, data: dict) -> "Material":
        """Создать материал из словаря, прочитанного из JSON."""
        return cls(
            material_id=data["id"],
            name=data["name"],
            category=data["category"],
            count=data["count"],
            added_at=data["added_at"],
        )

    def is_same(self, name: str, category: str) -> bool:
        """Проверить, тот же ли это материал (без учёта регистра)."""
        return (self.name.lower() == name.strip().lower()
                and self.category.lower() == category.strip().lower())

    def can_change_by(self, delta: int) -> bool:
        """Проверить, можно ли изменить количество на delta."""
        return self.count + delta >= 0

    def change_by(self, delta: int) -> None:
        """Изменить количество: delta > 0 - пополнение, < 0 - расход."""
        if not self.can_change_by(delta):
            raise ValueError(
                f"Недостаточно материала: в наличии {self.count} шт."
            )
        self.count += delta

    def is_low_stock(self) -> bool:
        """Проверить, заканчивается ли материал."""
        return self.count <= Material.MIN_STOCK

    def check_low_stock(self) -> str:
        """Вернуть сообщение об остатке (функция из ПР1)."""
        if self.is_low_stock():
            return f"Внимание: материал «{self.name}» заканчивается!"
        return f"Материал «{self.name}» в достаточном количестве."

    def __str__(self) -> str:
        """Вернуть строковое представление материала."""
        return f"{self.name} ({self.category}) - {self.count} шт."


SORT_KEYS = {
    "name": lambda material: material.name.lower(),
    "category": lambda material: material.category.lower(),
    "count": lambda material: material.count,
}


def find_material_by_id(
    materials: list[Material],
    material_id: int
) -> Material | None:
    """Найти материал по идентификатору."""
    for material in materials:
        if material.id == material_id:
            return material
    return None


def add_material(
    materials: list[Material],
    name: str,
    category: str,
    count: int
) -> Material:
    """Добавить материал в коллекцию и вернуть его.

    Если такой материал уже есть, увеличивается его количество.
    """
    for material in materials:
        if material.is_same(name, category):
            material.change_by(count)
            return material

    new_id = max((m.id for m in materials), default=0) + 1
    material = Material(new_id, name.strip(), category.strip(), count)
    materials.append(material)
    return material


def find_material(materials: list[Material], query: str) -> list[Material]:
    """Найти материалы по подстроке названия."""
    query = query.strip().lower()
    return [m for m in materials if query in m.name.lower()]


def filter_by_category(
    materials: list[Material],
    category: str
) -> list[Material]:
    """Отобрать материалы указанной категории."""
    category = category.strip().lower()
    return [m for m in materials if m.category.lower() == category]


def get_categories(materials: list[Material]) -> set[str]:
    """Вернуть множество категорий."""
    return {material.category for material in materials}


def get_low_stock_materials(materials: list[Material]) -> Iterator[Material]:
    """Генератор материалов, которые заканчиваются."""
    for material in materials:
        if material.is_low_stock():
            yield material


def sort_materials(
    materials: list[Material],
    by: str = "name"
) -> list[Material]:
    """Отсортировать материалы по названию, категории или количеству."""
    if by not in SORT_KEYS:
        raise ValueError(f"Нельзя отсортировать по полю «{by}».")
    return sorted(materials, key=SORT_KEYS[by])


def remove_material(materials: list[Material], material_id: int) -> Material:
    """Удалить материал из коллекции и вернуть его."""
    material = find_material_by_id(materials, material_id)
    if material is None:
        raise KeyError(f"Материал с id {material_id} не найден.")
    materials.remove(material)
    return material


def get_statistics(materials: list[Material]) -> dict:
    """Собрать статистику по материалам."""
    by_category: dict[str, int] = {}
    for material in materials:
        by_category[material.category] = (
            by_category.get(material.category, 0) + material.count
        )
    return {
        "total_materials": len(materials),
        "total_count": sum(m.count for m in materials),
        "by_category": by_category,
        "low_stock": len(list(get_low_stock_materials(materials))),
    }
