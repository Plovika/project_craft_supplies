import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "craftbox.settings")
django.setup()

from db import database  # noqa: E402
from db.import_json import import_all  # noqa: E402
from db.import_sqlite_to_orm import import_source  # noqa: E402
from django.db import transaction  # noqa: E402
from django.conf import settings  # noqa: E402
from django.test import override_settings  # noqa: E402
from django.test.utils import setup_databases, teardown_databases  # noqa: E402


@pytest.fixture(scope="session")
def orm_database():
    """Миграции применяются к отдельной тестовой базе Django в памяти."""
    configuration = setup_databases(verbosity=0, interactive=False)
    middleware = [
        item for item in settings.MIDDLEWARE
        if item != "debug_toolbar.middleware.DebugToolbarMiddleware"
    ]
    with override_settings(MIDDLEWARE=middleware):
        yield
    teardown_databases(configuration, verbosity=0)


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch, orm_database):
    """Каждый тест работает с временной копией базы, собранной из JSON.

    Настоящий файл data/craftbox.sqlite тесты не трогают.
    """
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    conn = database.get_connection()
    database.create_schema(conn)
    import_all(conn)
    conn.commit()
    conn.close()
    with transaction.atomic():
        import_source(tmp_path / "test.sqlite")
        yield tmp_path / "test.sqlite"
        transaction.set_rollback(True)
