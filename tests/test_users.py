import pytest

from models import User
from models.users import add_user, find_user, find_user_by_id


def test_user_creation():
    user = User(1, "Анна Смирнова", "anna@example.com")
    assert user.id == 1
    assert user.name == "Анна Смирнова"
    assert user.email == "anna@example.com"


def test_user_str():
    user = User(1, "Анна", "anna@example.com")
    assert str(user) == "Анна <anna@example.com>"


def test_user_from_data():
    user = User.from_data({"id": 2, "name": "Иван", "email": "i@ex.ru"})
    assert user.id == 2
    assert user.name == "Иван"


def test_add_and_find_user():
    users = []
    user = add_user(users, "Анна", "anna@example.com")
    assert find_user(users, "ANNA") == [user]
    assert find_user_by_id(users, 1) is user


def test_add_user_invalid_email():
    with pytest.raises(ValueError):
        add_user([], "Анна", "не-почта")


def test_add_user_duplicate_email():
    users = []
    add_user(users, "Анна", "anna@example.com")
    with pytest.raises(ValueError):
        add_user(users, "Другая Анна", "ANNA@example.com")
