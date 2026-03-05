from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [

    path("<uuid:uuid>/", views.payment_page, name="payment_page"),

]
