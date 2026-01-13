from django.urls import path
from .views import faq_view

app_name = "support"

urlpatterns = [

    path("faq/", faq_view, name="faq"),

]
