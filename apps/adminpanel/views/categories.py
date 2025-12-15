from django.shortcuts import render, redirect
from django.contrib import messages

from apps.adminpanel.utils import admin_required
from apps.adminpanel.forms.category_forms import ProductCategoryForm


@admin_required
def category_create(request):

    if request.method == "POST":
        form = ProductCategoryForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect("adminpanel:dashboard")

    else:
        form = ProductCategoryForm()
    
    return render(request, "adminpanel/categories/category_form.html", {"form":form, "title" : "Add Category"})