from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.start_checkout, name="start_checkout"),
]
