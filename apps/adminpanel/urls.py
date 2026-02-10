from django.urls import path


from apps.adminpanel.views.auth import admin_login, admin_logout

from apps.adminpanel.views.dashboard import dashboard

from apps.adminpanel.views.users import customers, block_user, unblock_user

from apps.adminpanel.views.categories import category_create, category_list, category_update

from apps.adminpanel.views.subcategories import subcategory_list, subcategory_create, subcategory_edit, ajax_load_subcategories

from apps.adminpanel.views.products import product_list, product_create, product_edit

from apps.adminpanel.views.variants import variant_list, variant_create, variant_edit

from apps.adminpanel.views.faq import faq_list, faq_create

from apps.adminpanel.views.promotions import promo_list, promo_create


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


    path("subcategories/", subcategory_list, name="subcategory_list"),
    path("subcategories/add/", subcategory_create, name="subcategory_create"),
    path("subcategories/<int:pk>/edit/", subcategory_edit, name="subcategory_edit"),


    path("products/", product_list, name="product_list"),
    path("products/create/", product_create, name="product_create"),
    path("products/<int:pk>/edit/", product_edit, name="product_edit"),
    path("ajax/load-subcategories/", ajax_load_subcategories, name="adminpanel_ajax_load_subcategories"),


    path("products/<int:product_id>/variants/", variant_list, name="variant_list"),
    path("products/<int:product_id>/variants/create/", variant_create, name="variant_create"),
    path("products/<int:product_id>/variants/<int:variant_id>/edit/", variant_edit, name="variant_edit",),
    

    path("faqs/", faq_list, name="faq_list"),
    path("faqs/add/", faq_create, name="faq_add"),


    path("promos/", promo_list, name="promo_list"),
    path("promos/add/", promo_create, name="promo_create"),




]
