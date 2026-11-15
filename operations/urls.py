from django.urls import path

from . import views

app_name = "operations"

urlpatterns = [
    path("", views.operations, name="list"),
    path("create/", views.operation_create, name="create"),
    path("<int:operation_id>/edit/", views.operation_update, name="update"),
    path("<int:operation_id>/cancel/", views.operation_cancel, name="cancel"),
    path("<int:operation_id>/", views.operation_detail, name="detail"),
]
