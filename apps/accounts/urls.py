from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # ✅ Email verification flow
    path("verification/", views.verification_sent, name="verification_sent"),
    path("send-verification/", views.send_verification_email,
         name="send_verification"),
]
