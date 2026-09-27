"""Функции сохранения и загрузки данных в JSON-файл."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "materials.json"


def load_materials(filename: str | Path = DATA_FILE) -> dict[int, dict]:
    """Загрузить материалы из JSON-файла.

    В файле материалы хранятся списком словарей, в программе -
    словарём, где ключ - id материала.
    При отсутствии файла или некорректных данных
    возвращается пустой словарь.
    """
    try:
        with open(filename, encoding="utf-8") as file:
            data = json.load(file)
        return {item["id"]: item for item in data}
    except FileNotFoundError:
        print(f"Файл {filename} не найден, начинаем с пустого списка.")
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён (некорректный JSON).")
    except (KeyError, TypeError):
        print(f"Файл {filename} содержит данные неверного формата.")
    return {}


def save_materials(
    materials: dict[int, dict],
    filename: str | Path = DATA_FILE
) -> bool:
    """Сохранить материалы в JSON-файл.

    Возвращает True при успешной записи, False при ошибке.
    """
    path = Path(filename)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                list(materials.values()), file,
                ensure_ascii=False, indent=4
            )
        return True
    except OSError as error:
        print(f"Не удалось сохранить данные: {error}")
        return False
