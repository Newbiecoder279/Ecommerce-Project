from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("create/", views.order_create, name="order_create"),
    path(
        "confirmation/<int:order_id>/",
        views.order_confirmation,
        name="order_confirmation",
    ),
    path("esewa/success/", views.esewa_success, name="esewa_success"),
    path("esewa/failure/", views.esewa_failure, name="esewa_failure"),
]
