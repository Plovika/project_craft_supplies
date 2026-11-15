"""Фильтрация и пользовательский ввод операций средствами Django Forms."""

from django import forms
from django.utils import timezone

from materials.models import Material
from .models import Operation, User


class OperationFilterForm(forms.Form):
    status = forms.ChoiceField(
        required=False, label="Статус", widget=forms.HiddenInput,
        choices=[("", "Все")] + list(Operation.Status.choices),
    )
    q = forms.CharField(
        required=False, label="Материал или пользователь", max_length=200,
        widget=forms.TextInput(attrs={
            "type": "search", "class": "form-control",
        }),
    )
    date = forms.DateField(
        required=False, label="Дата операции", input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "form-control"},
        ),
        error_messages={"invalid": "Укажите корректную дату: ГГГГ-ММ-ДД."},
    )
    material = forms.ModelChoiceField(
        required=False, label="Материал",
        queryset=Material.objects.order_by("name", "pk"),
        empty_label="Все материалы",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    user = forms.ModelChoiceField(
        required=False, label="Пользователь",
        queryset=User.objects.order_by("name", "pk"),
        empty_label="Все пользователи",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    sort = forms.ChoiceField(
        required=False, label="Сортировать по", initial="date",
        choices=[("date", "Дате"), ("material", "Материалу"),
                 ("user", "Пользователю")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ["material", "user", "amount", "created_at"]
        labels = {"amount": "Количество со знаком"}
        help_texts = {
            "amount": "Положительное число — пополнение, "
                      "отрицательное — расход. "
                      "Ноль недопустим.",
            "created_at": "Новая операция — сегодня или позже. "
                          "У старой записи можно сохранить исходную дату.",
        }
        widgets = {
            "material": forms.Select(attrs={"class": "form-select"}),
            "user": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={
                "class": "form-control", "placeholder": "Например: -2 или 5",
            }),
            "created_at": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_date = (
            self.instance.created_at if self.instance.pk else None
        )
        self.fields["created_at"].input_formats = ["%Y-%m-%d"]

    def clean_created_at(self):
        value = self.cleaned_data["created_at"]
        if value < timezone.localdate() and value != self.original_date:
            raise forms.ValidationError(
                "Нельзя указать новую прошедшую дату операции."
            )
        return value
