from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages

from apps.adminpanel.decorators import admin_required
from apps.adminpanel.forms.variant_forms import ProductVariantForm
from apps.catalog.models import Product, ProductVariant

from django.db.models import F, DecimalField, ExpressionWrapper


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


@admin_required
def variant_list(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    variants = (
        ProductVariant.objects
        .filter(product=product)
        .select_related("product__subcategory")
        .annotate(
            final_price=ExpressionWrapper(
                F("weight_kg") * F("product__subcategory__price_per_kg"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        )
        .order_by("color", "size")
    )

    context = {
        "product": product,
        "variants": variants,
    }

    return render(
        request,
        "adminpanel/variants/variant_list.html",
        context,
    )
