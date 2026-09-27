"""Точка запуска сервиса учёта материалов для творчества."""

from collections.abc import Callable

from models import Material, Operation, User
from models.materials import (
    add_material,
    filter_by_category,
    find_material,
    find_material_by_id,
    get_categories,
    get_low_stock_materials,
    get_statistics,
    remove_material,
    sort_materials,
)
from models.operations import (
    cancel_operation,
    create_operation,
    get_material_history,
)
from models.users import add_user, find_user, find_user_by_id
from storage import load_materials, load_operations, load_users, save_all
from utils import input_int, input_text

Handler = Callable[[list[Material], list[User], list[Operation]], bool]


def show_material(material: Material) -> None:
    """Вывести карточку материала (функция из ПР1)."""
    print("Карточка материала")
    print(f"ID:         {material.id}")
    print(f"Название:   {material.name}")
    print(f"Категория:  {material.category}")
    print(f"Количество: {material.count} шт.")
    print(f"Добавлен:   {material.added_at}")


def show_materials(materials: list[Material]) -> None:
    """Вывести список материалов в виде таблицы."""
    if not materials:
        print("Материалы не найдены.")
        return
    print(f"{'ID':<4}{'Название':<25}{'Категория':<15}{'Кол-во':>7}")
    print("-" * 51)
    for m in materials:
        print(f"{m.id:<4}{m.name:<25}{m.category:<15}{m.count:>7}")


def show_users(users: list[User]) -> None:
    """Вывести список пользователей."""
    if not users:
        print("Пользователи не найдены.")
    for user in users:
        print(f"{user.id}. {user}")


def show_operations(operations: list[Operation]) -> None:
    """Вывести историю операций."""
    if not operations:
        print("Операций пока нет.")
    for operation in operations:
        print(operation)


def handle_show_all(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: показать все материалы."""
    show_materials(materials)
    return False


def handle_add(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: добавить материал (сценарий из ПР1)."""
    name = input("Введите название материала: ")
    category = input("Введите категорию: ")
    count = input_int("Введите количество: ")

    status = Material.validate(name, category, count)
    if status != "OK":
        print(status)
        return False

    material = add_material(materials, name, category, count)
    show_material(material)
    print(material.check_low_stock())
    return True


def handle_find(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: поиск материала по названию."""
    query = input_text("Введите часть названия: ")
    show_materials(find_material(materials, query))
    return False


def handle_category(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: материалы выбранной категории."""
    categories = sorted(get_categories(materials))
    print("Доступные категории:", ", ".join(categories) or "нет")
    category = input_text("Введите категорию: ")
    show_materials(filter_by_category(materials, category))
    return False


def handle_low_stock(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: материалы, которые заканчиваются."""
    show_materials(list(get_low_stock_materials(materials)))
    return False


def handle_sort(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: сортировка материалов."""
    fields = {"1": "name", "2": "category", "3": "count"}
    print("Сортировать по: 1 - названию, 2 - категории, 3 - количеству")
    choice = input("Ваш выбор: ").strip()
    try:
        show_materials(sort_materials(materials, fields.get(choice, "")))
    except ValueError:
        print("Ошибка: неизвестный вариант сортировки.")
    return False


def handle_remove(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: удалить материал без истории операций."""
    material_id = input_int("ID материала для удаления: ")
    material = find_material_by_id(materials, material_id)
    if material is not None and get_material_history(operations, material):
        print("Нельзя удалить: по материалу есть история операций.")
        return False
    try:
        removed = remove_material(materials, material_id)
    except KeyError as error:
        print(f"Ошибка: {error.args[0]}")
        return False
    print(f"Материал «{removed.name}» удалён.")
    return True


def create_new_operation(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
    sign: int,
) -> bool:
    """Сценарий расхода (sign = -1) или пополнения (sign = 1)."""
    if not users:
        print("Сначала добавьте пользователя.")
        return False
    show_users(users)
    user = find_user_by_id(users, input_int("ID пользователя: "))
    if user is None:
        print("Ошибка: пользователь не найден.")
        return False

    material = find_material_by_id(materials, input_int("ID материала: "))
    if material is None:
        print("Ошибка: материал не найден.")
        return False

    amount = input_int("Количество: ")
    if amount <= 0:
        print("Ошибка: количество должно быть больше нуля.")
        return False

    operation = create_operation(operations, material, user, sign * amount)
    if operation is None:
        print(f"Недостаточно материала: в наличии {material.count} шт.")
        return False
    print(f"Операция создана: {operation}")
    print(material.check_low_stock())
    return True


def handle_use(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: израсходовать материал."""
    return create_new_operation(materials, users, operations, -1)


def handle_restock(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: пополнить материал."""
    return create_new_operation(materials, users, operations, 1)


def handle_history(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: история операций."""
    show_operations(operations)
    return False


def handle_cancel(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: отменить операцию."""
    operation_id = input_int("ID операции: ")
    try:
        if not cancel_operation(operations, operation_id):
            print("Ошибка: операция не найдена.")
            return False
    except ValueError as error:
        print(f"Ошибка: {error}")
        return False
    print("Операция отменена, количество материала восстановлено.")
    return True


def handle_show_users(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: показать пользователей."""
    show_users(users)
    return False


def handle_add_user(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: добавить пользователя."""
    name = input_text("Имя: ")
    email = input_text("Email: ")
    try:
        user = add_user(users, name, email)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return False
    print(f"Пользователь добавлен: {user}")
    return True


def handle_find_user(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: найти пользователя."""
    show_users(find_user(users, input_text("Имя или email: ")))
    return False


def handle_statistics(
    materials: list[Material],
    users: list[User],
    operations: list[Operation],
) -> bool:
    """Пункт меню: статистика."""
    stats = get_statistics(materials)
    active = [op for op in operations if not op.is_cancelled]
    print(f"Всего позиций: {stats['total_materials']}")
    print(f"Всего единиц:  {stats['total_count']} шт.")
    print(f"Заканчиваются: {stats['low_stock']} позиций")
    print(f"Пользователей: {len(users)}")
    print(f"Операций (активных): {len(active)}")
    print("По категориям:")
    for category, count in stats["by_category"].items():
        print(f"  {category}: {count} шт.")
    return False


MENU: dict[str, tuple[str, Handler]] = {
    "1": ("Показать все материалы", handle_show_all),
    "2": ("Добавить материал", handle_add),
    "3": ("Найти материал по названию", handle_find),
    "4": ("Показать материалы категории", handle_category),
    "5": ("Материалы, которые заканчиваются", handle_low_stock),
    "6": ("Отсортировать материалы", handle_sort),
    "7": ("Удалить материал", handle_remove),
    "8": ("Израсходовать материал", handle_use),
    "9": ("Пополнить материал", handle_restock),
    "10": ("История операций", handle_history),
    "11": ("Отменить операцию", handle_cancel),
    "12": ("Показать пользователей", handle_show_users),
    "13": ("Добавить пользователя", handle_add_user),
    "14": ("Найти пользователя", handle_find_user),
    "15": ("Статистика", handle_statistics),
}


def main() -> None:
    """Точка запуска: загрузка данных и цикл меню."""
    materials = load_materials()
    users = load_users()
    operations = load_operations(materials, users)

    while True:
        print("\n=== Учёт материалов для творчества ===")
        for key, (title, _) in MENU.items():
            print(f"{key:>2}. {title}")
        print(" 0. Выход")

        choice = input("Выберите действие: ").strip()
        if choice == "0":
            save_all(materials, users, operations)
            print("Данные сохранены. До свидания!")
            break
        if choice not in MENU:
            print("Ошибка: такого пункта меню нет.")
            continue

        _, handler = MENU[choice]
        if handler(materials, users, operations):
            save_all(materials, users, operations)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nРабота программы прервана.")
