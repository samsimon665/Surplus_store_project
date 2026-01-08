from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages

from apps.adminpanel.decorators import admin_required
from apps.adminpanel.forms.variant_forms import ProductVariantForm
from apps.catalog.models import Product


@admin_required
def variant_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductVariantForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                variant = form.save(commit=False)
                variant.product = product
                variant.save()

            messages.success(
                request,
                "Variant created successfully."
            )

            # TEMP redirect (we’ll change later)
            return redirect("adminpanel:product_list")

    else:
        form = ProductVariantForm()

    return render(
        request,
        "adminpanel/variants/variant_form.html",
        {
            "form": form,
            "product": product,
        }
    )
