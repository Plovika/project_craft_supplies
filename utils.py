"""Вспомогательные функции безопасного ввода данных."""


def input_int(prompt: str) -> int:
    """Запросить у пользователя целое число.

    При некорректном вводе запрос повторяется,
    программа не завершается аварийно.
    """
    while True:
        value = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print("Ошибка: нужно ввести целое число.")


def input_text(prompt: str) -> str:
    """Запросить у пользователя непустую строку.

    Пустой ввод (или ввод из одних пробелов) не принимается.
    """
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Ошибка: значение не может быть пустым.")
