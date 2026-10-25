from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.urls import reverse
import pytest

from models import Material, Operation, User
import homepage.views

client = Client()


@pytest.mark.parametrize("url", [
    "/", "/materials/", "/materials/1/", "/operations/", "/operations/1/",
])
def test_pages_open(url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("url", [
    "/materials/9999/", "/operations/9999/", "/materials/abc/",
])
def test_not_found(url):
    assert client.get(url).status_code == 404


def test_missing_material_message():
    html = client.get("/materials/9999/").content.decode()
    assert "Материал не найден" in html


def test_material_page_shows_data():
    html = client.get("/materials/1/").content.decode()
    assert "Акварель Белые ночи" in html


def test_base_template_and_static_files():
    html = client.get("/").content.decode()
    assert "/static/homepage/css/style.css" in html
    assert "/static/homepage/js/main.js" in html
    assert "/static/homepage/img/logo.png" in html
    assert 'id="current-year"' in html


def test_named_urls_with_namespaces():
    assert reverse("homepage:index") == "/"
    assert reverse("materials:list") == "/materials/"
    assert reverse("materials:detail", args=[3]) == "/materials/3/"
    assert reverse("operations:list") == "/operations/"
    assert reverse("operations:detail", args=[2]) == "/operations/2/"


def test_page_function_removed():
    assert not hasattr(homepage.views, "page")


def test_empty_materials_list():
    html = render_to_string("materials/material_list.html", {"materials": []})
    assert "Материалы не найдены." in html
    assert "Всего материалов: 0" in html


def test_empty_operations_list():
    html = render_to_string(
        "operations/operation_list.html", {"operations": []}
    )
    assert "Операции не найдены." in html


def test_operation_status_include():
    material = Material(1, "Кисть", "Кисти", 5)
    user = User(1, "Анна", "anna@example.com")
    operation = Operation(1, material, user, -1)
    context = {"operation": operation}
    template = "operations/includes/operation_status.html"

    assert "Активна" in render_to_string(template, context)
    operation.is_cancelled = True
    assert "Отменена" in render_to_string(template, context)


def test_default_filter_for_empty_name():
    material = Material(1, "", "Кисти", 5)
    html = render_to_string(
        "materials/includes/material_card.html", {"material": material}
    )
    assert "Без названия" in html


@override_settings(DEBUG=False)
def test_custom_404_page():
    response = client.get("/nonexistent/")
    assert response.status_code == 404
    assert "404 – страница не найдена" in response.content.decode()
