from django.urls import path
from .views import home_view
from .views import category_list, subcategory_list, product_list, product_detail


app_name = 'catalog'

urlpatterns = [

    path('', home_view, name='home'),


    path("categories/", category_list, name="category_list"),


    path("subcategories/", subcategory_list, name="all_subcategory_list"),
    path("categories/<slug:category_slug>/", subcategory_list, name="subcategory_list",),


    path("products/", product_list, name="product_list"),

    # Product listing (from subcategory)
    path("subcategories/<slug:subcategory_slug>/products/", product_list, name="subcategory_product_list"),

    path("categories/<slug:category_slug>/<slug:subcategory_slug>/<slug:product_slug>/", product_detail, name="product_detail")



]
