
from apps.adminpanel.decorators import admin_required
from django.shortcuts import render, redirect

from django.db import transaction

from apps.adminpanel.forms.product_forms import (
    ProductForm,
    ProductImageFormSet,
)


@admin_required
def product_create(request):
    if request.method == "POST":
        product_form = ProductForm(request.POST)
        image_formset = ProductImageFormSet(
            request.POST,
            request.FILES,
        )

        if product_form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                # 1️⃣ Save Product first
                product = product_form.save(commit=False)
                product.save()

                # 2️⃣ Attach product to image formset
                image_formset.instance = product
                image_formset.save()

            return redirect("adminpanel:product_create")

    else:
        product_form = ProductForm()
        image_formset = ProductImageFormSet()

    context = {
        "form": product_form,
        "image_formset": image_formset,
    }

    return render(request, "adminpanel/products/product_form.html", context)
