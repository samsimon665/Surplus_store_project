from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    path("login/", views.admin_login, name="login"),
    path("logout/", views.admin_logout, name="logout"),

    # Default admin homepage = dashboard
    path("", views.dashboard, name="dashboard"),

    path("customers/", views.customers, name="customers"),
    path("block/<int:user_id>/", views.block_user, name="block_user"),
    path("unblock/<int:user_id>/", views.unblock_user, name="unblock_user"),
]
