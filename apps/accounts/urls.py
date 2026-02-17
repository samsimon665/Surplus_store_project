from django.urls import path
from . import views
from .profile_views import profile_view, update_details, update_image, update_phone, add_address, set_default_address, delete_address

app_name = "accounts"

urlpatterns = [

    # Auth

    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    path("disabled/", views.account_disabled, name="account_disabled"),


    # Profile

    path("profile/", profile_view, name="profile"),
    path("profile/update-details/", update_details, name="update_details"),
    path("profile/update-phone/", update_phone, name="update_phone"),
    path("profile/update-image/", update_image, name="update_image"),
    path("profile/address/add/", add_address, name="add_address"),
    path("profile/address/<int:pk>/set-default/", set_default_address, name="set_default_address"),
    path("profile/address/<int:pk>/delete/", delete_address, name="delete_address"),



]
