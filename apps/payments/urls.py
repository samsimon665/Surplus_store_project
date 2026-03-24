from django.urls import path
from . import views

from .webhooks import razorpay_webhook

app_name = "payments"

urlpatterns = [
    
    path("verify/", views.verify_payment, name="verify_payment"),
    path("webhook/", razorpay_webhook, name="razorpay_webhook"),

]
