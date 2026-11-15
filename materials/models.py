"""Материалы, вычисляемый низкий остаток и адреса карточек."""

from datetime import date

from django.db import models, transaction
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode


class Material(models.Model):
    MIN_STOCK = 3

    name = models.CharField("Название", max_length=200)
    category = models.CharField("Категория", max_length=100)
    count = models.PositiveIntegerField(
        "Количество",
        help_text="Укажите текущий остаток в штуках, не меньше нуля.",
    )
    added_at = models.DateField("Дата добавления", default=date.today)
    is_low_stock = models.GeneratedField(
        expression=models.Case(
            models.When(count__lte=MIN_STOCK, then=models.Value(True)),
            default=models.Value(False), output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(), db_persist=True,
        verbose_name="Заканчивается",
    )
    slug = models.SlugField(
        "URL-идентификатор", max_length=180, unique=True, editable=False,
    )

    def save(self, *args, **kwargs):
        if self.slug:
            return super().save(*args, **kwargs)
        # Короткий префикс оставляет место для ID и обеспечивает уникальность.
        base_slug = (
            slugify(unidecode(self.name))[:150].strip("-") or "material"
        )
        with transaction.atomic(using=kwargs.get("using")):
            if self._state.adding:
                super().save(*args, **kwargs)
                self.slug = f"{base_slug}-{self.pk}"
                super().save(update_fields=["slug"], using=self._state.db)
            else:
                self.slug = f"{base_slug}-{self.pk}"
                fields = kwargs.get("update_fields")
                if fields is not None:
                    kwargs["update_fields"] = set(fields) | {"slug"}
                super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("materials:detail", kwargs={"slug": self.slug})

    def __str__(self):
        return f"{self.name} ({self.category}) - {self.count} шт."

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
