"""Класс Operation и функции работы с историей операций.

Операция - это расход или пополнение материала пользователем.
Она связывает объекты Material и User.
"""

from datetime import date

from .materials import Material
from .users import User


class Operation:
    """Операция с материалом: расход (amount < 0) или пополнение."""

    def __init__(
        self,
        operation_id: int,
        material: Material,
        user: User,
        amount: int,
        created_at: str | None = None,
    ) -> None:
        """Создать объект операции (количество материала не меняется)."""
        self.id = operation_id
        self.material = material
        self.user = user
        self.amount = amount
        self.created_at = created_at or date.today().isoformat()
        self.is_cancelled = False

    @property
    def kind(self) -> str:
        """Тип операции: расход или пополнение."""
        return "Пополнение" if self.amount > 0 else "Расход"

    def cancel(self) -> None:
        """Отменить операцию и вернуть количество материала назад.

        Операция не удаляется, а помечается отменённой.
        """
        if self.is_cancelled:
            raise ValueError("Операция уже отменена.")
        if not self.material.can_change_by(-self.amount):
            raise ValueError(
                "Нельзя отменить: материала осталось меньше, "
                "чем было добавлено."
            )
        self.material.change_by(-self.amount)
        self.is_cancelled = True

    def __str__(self) -> str:
        """Вернуть строковое представление операции."""
        state = " [отменена]" if self.is_cancelled else ""
        return (
            f"#{self.id} {self.created_at} {self.kind}: "
            f"{self.material.name} {self.amount:+d} шт. "
            f"({self.user.name}){state}"
        )


def find_operation_by_id(
    operations: list[Operation],
    operation_id: int
) -> Operation | None:
    """Найти операцию по идентификатору."""
    for operation in operations:
        if operation.id == operation_id:
            return operation
    return None


def create_operation(
    operations: list[Operation],
    material: Material,
    user: User,
    amount: int
) -> Operation | None:
    """Создать операцию, изменить количество материала.

    Возвращает None, если материала недостаточно для расхода.
    ValueError - если amount равен нулю.
    """
    if amount == 0:
        raise ValueError("Количество в операции не может быть нулевым.")
    if not material.can_change_by(amount):
        return None
    material.change_by(amount)
    new_id = max((op.id for op in operations), default=0) + 1
    operation = Operation(new_id, material, user, amount)
    operations.append(operation)
    return operation


def cancel_operation(operations: list[Operation], operation_id: int) -> bool:
    """Найти операцию и отменить её.

    Возвращает False, если операция не найдена.
    ValueError - если отменить нельзя.
    """
    operation = find_operation_by_id(operations, operation_id)
    if operation is None:
        return False
    operation.cancel()
    return True


def get_material_history(
    operations: list[Operation],
    material: Material
) -> list[Operation]:
    """Вернуть операции, связанные с материалом."""
    return [op for op in operations if op.material is material]
