"""Загрузка и сохранение объектов в JSON-файлы.

В JSON хранятся обычные данные, в программе - объекты.
Преобразование в обе стороны выполняется здесь.
"""

import json
from pathlib import Path

from models import Material, Operation, User
from models.materials import find_material_by_id
from models.users import find_user_by_id

DATA_DIR = Path(__file__).parent / "data"
MATERIALS_FILE = DATA_DIR / "materials.json"
USERS_FILE = DATA_DIR / "users.json"
OPERATIONS_FILE = DATA_DIR / "operations.json"


def read_json(filename: str | Path) -> list[dict]:
    """Прочитать список записей из JSON-файла.

    При отсутствии файла или ошибке формата возвращается пустой список.
    """
    try:
        with open(filename, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Файл {filename} не найден, начинаем с пустого списка.")
        return []
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён (некорректный JSON).")
        return []
    if not isinstance(data, list):
        print(f"Файл {filename} содержит данные неверного формата.")
        return []
    return data


def write_json(filename: str | Path, data: list[dict]) -> bool:
    """Записать список записей в JSON-файл."""
    path = Path(filename)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return True
    except OSError as error:
        print(f"Не удалось сохранить {path.name}: {error}")
        return False


def load_materials(filename: str | Path = MATERIALS_FILE) -> list[Material]:
    """Загрузить материалы и создать объекты Material."""
    materials = []
    for data in read_json(filename):
        try:
            materials.append(Material.from_data(data))
        except (KeyError, TypeError, ValueError):
            print(f"Пропущена некорректная запись материала: {data}")
    return materials


def save_materials(
    materials: list[Material],
    filename: str | Path = MATERIALS_FILE
) -> bool:
    """Сохранить объекты Material в JSON."""
    data = [
        {
            "id": m.id,
            "name": m.name,
            "category": m.category,
            "count": m.count,
            "added_at": m.added_at,
        }
        for m in materials
    ]
    return write_json(filename, data)


def load_users(filename: str | Path = USERS_FILE) -> list[User]:
    """Загрузить пользователей и создать объекты User."""
    users = []
    for data in read_json(filename):
        try:
            users.append(User.from_data(data))
        except (KeyError, TypeError):
            print(f"Пропущена некорректная запись пользователя: {data}")
    return users


def save_users(users: list[User], filename: str | Path = USERS_FILE) -> bool:
    """Сохранить объекты User в JSON."""
    data = [{"id": u.id, "name": u.name, "email": u.email} for u in users]
    return write_json(filename, data)


def load_operations(
    materials: list[Material],
    users: list[User],
    filename: str | Path = OPERATIONS_FILE
) -> list[Operation]:
    """Загрузить операции и восстановить связи с Material и User.

    Операции, ссылающиеся на несуществующий материал
    или пользователя, пропускаются.
    """
    operations = []
    for data in read_json(filename):
        try:
            material = find_material_by_id(materials, data["material_id"])
            user = find_user_by_id(users, data["user_id"])
            if material is None or user is None:
                print(f"Пропущена операция #{data['id']}: "
                      "материал или пользователь не найден.")
                continue
            operation = Operation(
                operation_id=data["id"],
                material=material,
                user=user,
                amount=data["amount"],
                created_at=data["created_at"],
            )
            operation.is_cancelled = data["is_cancelled"]
            operations.append(operation)
        except (KeyError, TypeError):
            print(f"Пропущена некорректная запись операции: {data}")
    return operations


def save_operations(
    operations: list[Operation],
    filename: str | Path = OPERATIONS_FILE
) -> bool:
    """Сохранить операции, заменяя объекты их идентификаторами."""
    data = [
        {
            "id": op.id,
            "material_id": op.material.id,
            "user_id": op.user.id,
            "amount": op.amount,
            "created_at": op.created_at,
            "is_cancelled": op.is_cancelled,
        }
        for op in operations
    ]
    return write_json(filename, data)


def save_all(
    materials: list[Material],
    users: list[User],
    operations: list[Operation]
) -> None:
    """Сохранить все данные приложения."""
    save_materials(materials)
    save_users(users)
    save_operations(operations)
