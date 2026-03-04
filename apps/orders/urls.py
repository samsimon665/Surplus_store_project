from django.urls import path
from . import views
from .placeorder_view import place_order

app_name = "orders"

urlpatterns = [
    path("checkout/", views.start_checkout, name="start_checkout"),
    path("checkout/promo/", views.update_promo_ajax, name="update_promo_ajax"),
    path("update-summary/", views.update_checkout_summary, name="update_checkout_summary"),
    path("place-order/", place_order, name="place_order"),

    # path("payment/<uuid:uuid>/", views.payment_page, name="payment_page"),
    
]
