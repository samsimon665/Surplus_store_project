from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.adminpanel.utils import admin_required
from apps.adminpanel.forms.category_forms import ProductCategoryForm

from apps.catalog.models import ProductCategory
from django.core.paginator import Paginator


@admin_required
def category_create(request):

    if request.method == "POST":
        form = ProductCategoryForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect("adminpanel:category_list")

    else:
        form = ProductCategoryForm()

    return render(request, "adminpanel/categories/category_form.html", {"form": form, "title": "Add Category"})


@admin_required
def category_list(request):
    categories = ProductCategory.objects.order_by("-created_at")

    paginator = Paginator(categories, 4)  # 4 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "adminpanel/categories/category_list.html",
        {
            "categories": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
        }
    )


@admin_required
def category_update(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)

    if request.method == "POST":
        form = ProductCategoryForm(
            request.POST, request.FILES, instance=category)

        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            # or wherever your list page is
            return redirect("adminpanel:categories")

    else:
        form = ProductCategoryForm(instance=category)

    return render(
        request,
        "adminpanel/categories/category_form.html",
        {
            "form": form,
            "title": "Edit Category",
            "is_edit": True,
        },
    )
