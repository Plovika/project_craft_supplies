from django.template.loader import render_to_string
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
import pytest

from models import Material, Operation, User
from materials.models import Material as OrmMaterial
import homepage.views

client = Client()


@pytest.mark.parametrize("url", [
    "/", "/materials/", "/materials/1/", "/operations/", "/operations/1/",
    "/materials/search/", "/materials/search/?category=Краски&max_count=3",
    "/operations/?status=active", "/operations/?status=cancelled",
    "/statistics/",
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
    assert reverse("materials:search") == "/materials/search/"
    assert reverse("homepage:statistics") == "/statistics/"


def test_page_function_removed():
    assert not hasattr(homepage.views, "page")


def test_empty_materials_list():
    html = render_to_string("materials/material_list.html", {"materials": []})
    assert "Материалы не найдены." in html
    assert "Всего материалов: 0" in html


def test_empty_operations_list():
    html = render_to_string(
        "operations/operation_list.html", {"operations": []},
        request=RequestFactory().get("/operations/"),
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


def test_page_shows_data_from_database(test_db):
    OrmMaterial.objects.filter(pk=1).update(name="Акварель НОВАЯ")
    assert "Акварель НОВАЯ" in client.get("/materials/").content.decode()


def test_search_page_results():
    html = client.get(
        "/materials/search/?category=Краски&max_count=3"
    ).content.decode()
    assert "Найдено материалов: 1" in html
    assert "Акварель Белые ночи" in html


def test_search_page_bad_number():
    html = client.get("/materials/search/?max_count=abc").content.decode()
    assert "целым неотрицательным числом" in html


def test_search_page_empty_result():
    html = client.get("/materials/search/?max_count=0").content.decode()
    assert "По этим условиям материалов нет." in html


def test_cancelled_filter_empty():
    html = client.get("/operations/?status=cancelled").content.decode()
    assert "Операции не найдены." in html


def test_statistics_page():
    html = client.get("/statistics/").content.decode()
    assert "По категориям" in html
    assert "Краски" in html
