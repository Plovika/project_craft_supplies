"""Пользователи предметной области и операции с материалами."""

from datetime import date

from django.db import models, transaction
from django.db.models import F, Q

from materials.models import Material


class User(models.Model):
    """Участник учёта материалов, не пользователь аутентификации Django."""

    name = models.CharField("Имя", max_length=200)
    email = models.EmailField("Электронная почта", unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Operation(models.Model):
    """Расход или пополнение, связанное с материалом и пользователем."""

    material = models.ForeignKey(
        Material, on_delete=models.PROTECT, related_name="operations",
        verbose_name="Материал",
    )
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="operations",
        verbose_name="Пользователь",
    )
    amount = models.IntegerField("Изменение количества")
    created_at = models.DateField("Дата операции", default=date.today)
    is_cancelled = models.BooleanField("Отменена", default=False)

    @property
    def kind(self):
        return "Пополнение" if self.amount > 0 else "Расход"

    def cancel(self):
        """Отменить операцию и восстановить остаток одной транзакцией."""
        with transaction.atomic():
            operation = Operation.objects.select_for_update().get(pk=self.pk)
            if operation.is_cancelled:
                raise ValueError("Операция уже отменена.")
            changed = Material.objects.filter(
                pk=operation.material_id,
                count__gte=max(operation.amount, 0),
            ).update(count=F("count") - operation.amount)
            if not changed:
                raise ValueError(
                    "Нельзя отменить: материала осталось меньше, "
                    "чем было добавлено."
                )
            operation.is_cancelled = True
            operation.save(update_fields=["is_cancelled"])
        self.is_cancelled = True
        self.material.refresh_from_db()

    def __str__(self):
        return (
            f"#{self.pk} {self.created_at} {self.kind}: "
            f"{self.material} {self.amount:+d} шт. ({self.user})"
        )

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = "Операция"
        verbose_name_plural = "Операции"
        constraints = [
            models.CheckConstraint(
                condition=~Q(amount=0), name="operation_amount_not_zero",
            ),
        ]
