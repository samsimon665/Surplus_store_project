from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_view, name="cart"),
    path("add/", views.add_to_cart, name="cart_add"),
    path("update/", views.update_cart_item, name="cart_update"),
    path("remove/", views.remove_cart_item, name="cart_remove"),

]
