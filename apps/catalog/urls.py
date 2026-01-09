from django.urls import path
from .views import home_view, category_list

app_name = 'catalog'

urlpatterns = [

    path('', home_view, name='home'),

    path("categories/", category_list, name="category_list"),

]
