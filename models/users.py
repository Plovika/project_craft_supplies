"""Класс User и функции работы с коллекцией пользователей."""


class User:
    """Пользователь сервиса."""

    def __init__(self, user_id: int, name: str, email: str) -> None:
        """Создать объект пользователя."""
        self.id = user_id
        self.name = name
        self.email = email

    @staticmethod
    def validate_email(email: str) -> bool:
        """Простая проверка адреса электронной почты."""
        email = email.strip()
        return "@" in email and "." in email.split("@")[-1]

    @classmethod
    def from_data(cls, data: dict) -> "User":
        """Создать пользователя из словаря, прочитанного из JSON."""
        return cls(
            user_id=data["id"],
            name=data["name"],
            email=data["email"],
        )

    def __str__(self) -> str:
        """Вернуть строковое представление пользователя."""
        return f"{self.name} <{self.email}>"


def find_user_by_id(users: list[User], user_id: int) -> User | None:
    """Найти пользователя по идентификатору."""
    for user in users:
        if user.id == user_id:
            return user
    return None


def add_user(users: list[User], name: str, email: str) -> User:
    """Создать пользователя, добавить его в коллекцию и вернуть.

    ValueError - если email некорректен или уже занят.
    """
    if not User.validate_email(email):
        raise ValueError("Некорректный адрес электронной почты.")
    email = email.strip().lower()
    if any(user.email.lower() == email for user in users):
        raise ValueError("Пользователь с таким email уже есть.")
    new_id = max((u.id for u in users), default=0) + 1
    user = User(new_id, name.strip(), email)
    users.append(user)
    return user


def find_user(users: list[User], query: str) -> list[User]:
    """Найти пользователей по части имени или email."""
    query = query.strip().lower()
    return [
        user for user in users
        if query in user.name.lower() or query in user.email.lower()
    ]
