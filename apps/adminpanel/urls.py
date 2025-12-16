from django.urls import path

from apps.adminpanel.views.auth import admin_login, admin_logout
from apps.adminpanel.views.dashboard import dashboard
from apps.adminpanel.views.users import customers, block_user, unblock_user
from apps.adminpanel.views.categories import category_create, category_list, category_update

app_name = "adminpanel"

urlpatterns = [

    # Default admin homepage
    path("", dashboard, name="dashboard"),

    path("login/", admin_login, name="login"),
    path("logout/", admin_logout, name="logout"),


    path("customers/", customers, name="customers"),
    path("block/<int:user_id>/", block_user, name="block_user"),
    path("unblock/<int:user_id>/", unblock_user, name="unblock_user"),

    path("categories/", category_list, name="category_list"),
    path("categories/add/", category_create, name="category_create"),
    path("categories/<int:pk>/edit/", category_update, name="category_edit"),

]
