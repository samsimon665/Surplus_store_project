from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_view, name="cart"),
    path("add/", views.add_to_cart, name="add_to_cart"),
    path("update/", views.update_cart_item, name="update_cart"),
    path("remove/", views.remove_cart_item, name="cart_remove"),

    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/toggle/", views.toggle_wishlist, name="toggle_wishlist"),
    path("wishlist/remove/", views.remove_from_wishlist, name="remove_wishlist"),
]
