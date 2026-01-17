from django.urls import path
from .views import home_view, category_list, subcategory_list


app_name = 'catalog'

urlpatterns = [

    path('', home_view, name='home'),

    path("categories/", category_list, name="category_list"),

    path("subcategories/", subcategory_list, name="all_subcategory_list"),
    path("categories/<slug:category_slug>/", subcategory_list, name="subcategory_list",),

]
