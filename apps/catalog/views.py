from django.shortcuts import render

from .models import ProductCategory

from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required(login_url='accounts:login')
def home_view(request):
    print("HOME VIEW EXECUTED")
    return render(request, "catalog/home.html")


def category_list(request):
    categories = (
        ProductCategory.objects
        .filter(is_active=True)
        .order_by("name")
    )

    return render(
        request,
        "catalog/categories.html",
        {
            "categories": categories
        }
    )
