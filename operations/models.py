"""Пользователи, статусы и согласованный учёт операций с материалами."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import models, router, transaction
from django.db.models import F, Q

from materials.models import Material


class User(models.Model):
    """Участник учёта, не учётная запись входа в Django Admin."""

    name = models.CharField("Имя", max_length=200)
    email = models.EmailField("Электронная почта", unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class OperationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=self.model.Status.ACTIVE)

    def cancelled(self):
        return self.filter(status=self.model.Status.CANCELLED)

    def completed(self):
        return self.filter(status=self.model.Status.COMPLETED)

    def for_date(self, selected_date):
        return self.filter(created_at=selected_date)

    def delete(self):
        """В том числе массовое удаление должно восстановить остатки."""
        total, details = 0, {}
        with transaction.atomic(using=self.db):
            for operation in self.order_by("pk"):
                deleted, by_model = operation.delete(using=self.db)
                total += deleted
                for label, count in by_model.items():
                    details[label] = details.get(label, 0) + count
        return total, details


class OperationManager(models.Manager.from_queryset(OperationQuerySet)):
    pass


class Operation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активна"
        CANCELLED = "cancelled", "Отменена"
        COMPLETED = "completed", "Завершена"

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
    status = models.CharField(
        "Статус", max_length=12, choices=Status.choices, default=Status.ACTIVE,
    )
    objects = OperationManager()

    @property
    def kind(self):
        return "Пополнение" if self.amount > 0 else "Расход"

    def _stock_changes(self, previous, update_fields=None):
        fields = None if update_fields is None else set(update_fields)
        material_id, amount, status = (
            self.material_id, self.amount, self.status,
        )
        if previous is not None and fields is not None:
            if not {"material", "material_id"} & fields:
                material_id = previous.material_id
            if "amount" not in fields:
                amount = previous.amount
            if "status" not in fields:
                status = previous.status
        if (
            not isinstance(amount, int) or isinstance(amount, bool)
            or not amount
        ):
            raise ValidationError({
                "amount": "Укажите ненулевое целое число.",
            })
        if status not in self.Status.values:
            raise ValidationError({"status": "Неизвестный статус операции."})
        changes = {}
        if previous and previous.status != self.Status.CANCELLED:
            changes[previous.material_id] = -previous.amount
        if status != self.Status.CANCELLED and material_id is not None:
            changes[material_id] = changes.get(material_id, 0) + amount
        return changes

    def clean(self):
        super().clean()
        previous = None
        if self.pk:
            previous = Operation.objects.filter(pk=self.pk).first()
        for material_id, delta in self._stock_changes(previous).items():
            count = Material.objects.filter(pk=material_id).values_list(
                "count", flat=True,
            ).first()
            if count is not None and count + delta < 0:
                raise ValidationError({
                    "amount": "Недостаточно материала для этой операции.",
                })

    def save(self, *args, **kwargs):
        """Сохранить историю и изменение остатка в одной транзакции."""
        using = kwargs.get("using") or router.db_for_write(
            type(self), instance=self,
        )
        fields = kwargs.get("update_fields")
        if fields is not None and not fields:
            return
        with transaction.atomic(using=using):
            previous = None
            if self.pk:
                previous = (
                    Operation.objects.using(using).select_for_update()
                    .filter(pk=self.pk).first()
                )
            changes = self._stock_changes(previous, fields)
            for material_id, delta in sorted(changes.items()):
                if not delta:
                    continue
                changed = Material.objects.using(using).filter(
                    pk=material_id, count__gte=max(-delta, 0),
                ).update(count=F("count") + delta)
                if not changed:
                    raise ValidationError({
                        "amount": "Недостаточно материала для этой операции.",
                    })
            super().save(*args, **kwargs)
        self._state.fields_cache.pop("material", None)

    def delete(self, using=None, keep_parents=False):
        using = using or router.db_for_write(type(self), instance=self)
        with transaction.atomic(using=using):
            previous = Operation.objects.using(using).select_for_update().get(
                pk=self.pk,
            )
            if previous.status != self.Status.CANCELLED:
                changed = Material.objects.using(using).filter(
                    pk=previous.material_id,
                    count__gte=max(previous.amount, 0),
                ).update(count=F("count") - previous.amount)
                if not changed:
                    raise ValidationError(
                        "Нельзя удалить операцию: "
                        "остаток стал бы отрицательным."
                    )
            return super().delete(using=using, keep_parents=keep_parents)

    def cancel(self):
        """Отмена сохраняет запись истории и возвращает остаток."""
        current = Operation.objects.get(pk=self.pk)
        if current.status == self.Status.CANCELLED:
            raise ValueError("Операция уже отменена.")
        current.status = self.Status.CANCELLED
        current.save(update_fields=["status"])
        self.status = current.status
        self._state.fields_cache.pop("material", None)

    def restore(self):
        current = Operation.objects.get(pk=self.pk)
        if current.status != self.Status.CANCELLED:
            raise ValueError("Операция не отменена.")
        current.status = self.Status.ACTIVE
        current.save(update_fields=["status"])
        self.status = current.status
        self._state.fields_cache.pop("material", None)

    def __str__(self):
        return (
            f"#{self.pk} {self.created_at} {self.kind}: "
            f"{self.material.name} {self.amount:+d} шт. ({self.user})"
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
