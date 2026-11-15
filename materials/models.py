"""Модель материалов для веб-версии проекта."""

from datetime import date

from django.db import models


class Material(models.Model):
    """Материал и его текущий остаток."""

    MIN_STOCK = 3

    name = models.CharField("Название", max_length=200)
    category = models.CharField("Категория", max_length=100)
    count = models.PositiveIntegerField("Количество")
    added_at = models.DateField("Дата добавления", default=date.today)

    def is_low_stock(self):
        return self.count <= self.MIN_STOCK

    def __str__(self):
        return f"{self.name} ({self.category}) - {self.count} шт."

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
