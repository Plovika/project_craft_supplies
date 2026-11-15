from django.urls import path

from . import views

app_name = "materials"

urlpatterns = [
    path("", views.materials, name="list"),
    path("search/", views.material_search, name="search"),
    path(
        "<int:material_id>/", views.material_legacy_detail,
        name="legacy_detail",
    ),
    path("<slug:slug>/", views.material_detail, name="detail"),
]
