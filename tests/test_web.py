from django.test import Client
import pytest

client = Client()


@pytest.mark.parametrize("url", [
    "/", "/materials/", "/materials/1/", "/operations/", "/operations/1/",
])
def test_pages_open(url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("url", [
    "/materials/999/", "/operations/999/", "/materials/abc/",
])
def test_not_found(url):
    assert client.get(url).status_code == 404


def test_material_page_shows_data():
    html = client.get("/materials/1/").content.decode()
    assert "Акварель Белые ночи" in html
    assert "bootstrap" in html
