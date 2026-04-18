from django.urls import path
from . import views
from .placeorder_view import place_order, order_list, order_success, order_detail

app_name = "orders"

urlpatterns = [
    path("checkout/", views.start_checkout, name="start_checkout"),
    path("checkout/promo/", views.update_promo_ajax, name="update_promo_ajax"),
    path("update-summary/", views.update_checkout_summary, name="update_checkout_summary"),
    path("place-order/", place_order, name="place_order"),

    path("", order_list, name="order_list"),
    path("success/<uuid:uuid>/", order_success, name="order_success"),
    path("<uuid:uuid>/", order_detail, name="order_detail"),

    path("order/<uuid:uuid>/cancel/", views.cancel_order, name="cancel_order"),
    
]
