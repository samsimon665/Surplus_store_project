from django.shortcuts import render, redirect
from django.db import transaction

from apps.adminpanel.decorators import admin_required
from apps.adminpanel.forms.product_forms import ProductForm


@admin_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                product = form.save()

            # TEMP: stay on product page until variant exists
            return redirect("adminpanel:product_create")

    else:
        form = ProductForm()

    return render(
        request,
        "adminpanel/products/product_form.html",
        {"form": form}
    )
