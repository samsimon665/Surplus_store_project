from django.shortcuts import render, get_object_or_404

from .models import ProductCategory, SubCategory

from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required(login_url='accounts:login')
def home_view(request):
    print("HOME VIEW EXECUTED")
    return render(request, "catalog/home.html")


def category_list(request):
    q = request.GET.get("q", "").strip()

    categories = ProductCategory.objects.filter(is_active=True)

    if q:
        categories = categories.filter(name__icontains=q)

    categories = categories.order_by("name")

    return render(
        request,
        "catalog/categories.html",
        {
            "categories": categories
        }
    )


def subcategory_list(request, category_slug=None):
    category = None

    subcategories = SubCategory.objects.filter(
        is_active=True,
        category__is_active=True
    ).select_related("category")

    if category_slug:
        category = get_object_or_404(
            ProductCategory,
            slug=category_slug,
            is_active=True
        )
        subcategories = subcategories.filter(category=category)

    subcategories = subcategories.order_by("category__name", "name")

    return render(
        request,
        "catalog/subcategories.html",
        {
            "category": category,          # None if global
            "subcategories": subcategories,
        }
    )
