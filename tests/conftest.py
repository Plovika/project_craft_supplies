import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "craftbox.settings")
django.setup()

from db import database  # noqa: E402
from db.import_json import import_all  # noqa: E402


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    """Каждый тест работает с временной копией базы, собранной из JSON.

    Настоящий файл data/craftbox.sqlite тесты не трогают.
    """
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    conn = database.get_connection()
    database.create_schema(conn)
    import_all(conn)
    conn.commit()
    conn.close()
    return tmp_path / "test.sqlite"
