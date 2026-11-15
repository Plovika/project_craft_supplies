"""Перенос базы ПР7 в db.sqlite3 с сохранением идентификаторов и связей."""

import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "craftbox.sqlite"
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "craftbox.settings")

import django  # noqa: E402

django.setup()

from django.db import transaction  # noqa: E402

from materials.models import Material  # noqa: E402
from operations.models import Operation, User  # noqa: E402


def import_source(source=SOURCE_DB):
    """Прочитать источник без записи; повторный перенос не создаёт дублей."""
    source = Path(source).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Исходная база не найдена: {source}")
    conn = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        materials = conn.execute(
            "SELECT * FROM materials ORDER BY id"
        ).fetchall()
        users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        operations = conn.execute(
            "SELECT * FROM operations ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    with transaction.atomic():
        for row in materials:
            Material.objects.update_or_create(
                pk=row["id"], defaults={
                    "name": row["name"], "category": row["category"],
                    "count": row["count"],
                    "added_at": date.fromisoformat(row["added_at"]),
                },
            )
        for row in users:
            User.objects.update_or_create(
                pk=row["id"],
                defaults={"name": row["name"], "email": row["email"]},
            )
        for row in operations:
            if row["is_cancelled"] not in (0, 1):
                raise ValueError("Некорректный признак отмены операции.")
            # Остатки уже перенесены из снимка ПР7. Здесь сохраняем историю
            # без повторного применения её количества к этим остаткам.
            values = {
                "material_id": row["material_id"],
                "user_id": row["user_id"], "amount": row["amount"],
                "created_at": date.fromisoformat(row["created_at"]),
                "status": (
                    Operation.Status.CANCELLED if row["is_cancelled"]
                    else Operation.Status.ACTIVE
                ),
            }
            if not Operation.objects.filter(pk=row["id"]).update(**values):
                Operation.objects.bulk_create([
                    Operation(pk=row["id"], **values),
                ])


def main():
    import_source()
    print("Перенос завершён.")
    print("Материалов:", Material.objects.count())
    print("Пользователей:", User.objects.count())
    print("Операций:", Operation.objects.count())


if __name__ == "__main__":
    main()
