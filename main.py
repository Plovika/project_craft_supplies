"""Точка запуска сервиса учёта материалов для творчества."""

from collections.abc import Callable

from materials import (
    add_material,
    change_count,
    check_low_stock,
    filter_by_category,
    find_material,
    get_categories,
    get_low_stock_materials,
    get_statistics,
    remove_material,
    sort_materials,
    validate_material,
)
from storage import load_materials, save_materials
from utils import input_int, input_text


def show_material(material: dict) -> None:
    """Вывести карточку материала (функция из ПР1)."""
    print("Карточка материала")
    print(f"ID:         {material['id']}")
    print(f"Название:   {material['name']}")
    print(f"Категория:  {material['category']}")
    print(f"Количество: {material['count']} шт.")
    print(f"Добавлен:   {material['added_at']}")


def show_materials(materials_list: list[dict]) -> None:
    """Вывести список материалов в виде таблицы."""
    if not materials_list:
        print("Материалы не найдены.")
        return
    print(f"{'ID':<4}{'Название':<25}{'Категория':<15}{'Кол-во':>7}")
    print("-" * 51)
    for material in materials_list:
        print(
            f"{material['id']:<4}{material['name']:<25}"
            f"{material['category']:<15}{material['count']:>7}"
        )


def handle_show_all(materials: dict[int, dict]) -> bool:
    """Пункт меню: показать все материалы."""
    show_materials(list(materials.values()))
    return False


def handle_add(materials: dict[int, dict]) -> bool:
    """Пункт меню: добавить материал (сценарий из ПР1)."""
    name = input("Введите название материала: ")
    category = input("Введите категорию: ")
    count = input_int("Введите количество: ")

    status = validate_material(name, category, count)
    if status != "OK":
        print(status)
        return False

    material = add_material(materials, name, category, count)
    show_material(material)
    print(check_low_stock(material))
    return True


def handle_find(materials: dict[int, dict]) -> bool:
    """Пункт меню: поиск материала по названию."""
    query = input_text("Введите часть названия: ")
    show_materials(find_material(materials, query))
    return False


def handle_category(materials: dict[int, dict]) -> bool:
    """Пункт меню: материалы выбранной категории."""
    categories = sorted(get_categories(materials))
    print("Доступные категории:", ", ".join(categories) or "нет")
    category = input_text("Введите категорию: ")
    show_materials(filter_by_category(materials, category))
    return False


def handle_change_count(materials: dict[int, dict]) -> bool:
    """Пункт меню: израсходовать или пополнить материал."""
    material_id = input_int("ID материала: ")
    delta = input_int("Изменение (например, -2 расход или 5 пополнение): ")
    try:
        material = change_count(materials, material_id, delta)
    except (KeyError, ValueError) as error:
        print(f"Ошибка: {error.args[0]}")
        return False
    print(f"Новый остаток: {material['count']} шт.")
    print(check_low_stock(material))
    return True


def handle_remove(materials: dict[int, dict]) -> bool:
    """Пункт меню: удалить материал."""
    material_id = input_int("ID материала для удаления: ")
    try:
        material = remove_material(materials, material_id)
    except KeyError as error:
        print(f"Ошибка: {error.args[0]}")
        return False
    print(f"Материал «{material['name']}» удалён.")
    return True


def handle_low_stock(materials: dict[int, dict]) -> bool:
    """Пункт меню: материалы, которые заканчиваются."""
    show_materials(list(get_low_stock_materials(materials)))
    return False


def handle_sort(materials: dict[int, dict]) -> bool:
    """Пункт меню: сортировка материалов."""
    fields = {"1": "name", "2": "category", "3": "count"}
    print("Сортировать по: 1 - названию, 2 - категории, 3 - количеству")
    choice = input("Ваш выбор: ").strip()
    try:
        show_materials(sort_materials(materials, fields.get(choice, "")))
    except ValueError:
        print("Ошибка: неизвестный вариант сортировки.")
    return False


def handle_statistics(materials: dict[int, dict]) -> bool:
    """Пункт меню: статистика по материалам."""
    stats = get_statistics(materials)
    print(f"Всего позиций: {stats['total_materials']}")
    print(f"Всего единиц:  {stats['total_count']} шт.")
    print(f"Заканчиваются: {stats['low_stock']} позиций")
    print("По категориям:")
    for category, count in stats["by_category"].items():
        print(f"  {category}: {count} шт.")
    return False


MENU: dict[str, tuple[str, Callable[[dict[int, dict]], bool]]] = {
    "1": ("Показать все материалы", handle_show_all),
    "2": ("Добавить материал", handle_add),
    "3": ("Найти материал по названию", handle_find),
    "4": ("Показать материалы категории", handle_category),
    "5": ("Израсходовать / пополнить материал", handle_change_count),
    "6": ("Удалить материал", handle_remove),
    "7": ("Материалы, которые заканчиваются", handle_low_stock),
    "8": ("Отсортировать материалы", handle_sort),
    "9": ("Статистика", handle_statistics),
}


def main() -> None:
    """Точка запуска: цикл меню и вызов функций проекта."""
    materials = load_materials()
    while True:
        print("\n=== Учёт материалов для творчества ===")
        for key, (title, _) in MENU.items():
            print(f"{key}. {title}")
        print("0. Выход")

        choice = input("Выберите действие: ").strip()
        if choice == "0":
            print("До свидания!")
            break
        if choice not in MENU:
            print("Ошибка: такого пункта меню нет.")
            continue

        _, handler = MENU[choice]
        if handler(materials):
            save_materials(materials)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nРабота программы прервана.")
