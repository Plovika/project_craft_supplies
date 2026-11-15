"""Корневая маршрутизация проекта: распределяет адреса по приложениям."""

from django.contrib import admin
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("materials/", include("materials.urls")),
    path("operations/", include("operations.urls")),
]

handler404 = "homepage.views.page_not_found"

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
