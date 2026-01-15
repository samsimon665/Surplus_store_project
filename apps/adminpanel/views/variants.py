from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django import forms

from django.db import transaction
from django.db.models import F, DecimalField, ExpressionWrapper

from apps.adminpanel.decorators import admin_required
from apps.catalog.models import Product, ProductVariant, ProductImage
from apps.adminpanel.utils.validations import validate_variant_data


@admin_required
def variant_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        color = request.POST.get("color")
        sizes = request.POST.getlist("sizes")
        images = request.FILES.getlist("images")

        weights = {}
        stocks = {}

        for size in sizes:
            weights[size] = request.POST.get(f"weight[{size}]")
            stocks[size] = request.POST.get(f"stock[{size}]")

        # ✅ PRE-DB VALIDATION (CRITICAL)
        try:
            validate_variant_data(
                product=product,
                color=color,
                sizes=sizes,
                weights=weights,
                stocks=stocks,
                images=images,
            )

        except forms.ValidationError as e:
            messages.error(request, e.message)
            return render(
                request,
                "adminpanel/variants/variant_form.html",
                {
                    "product": product,
                    "posted_data": request.POST,
                    "posted_sizes": sizes,
                },
            )

        # ✅ SAFE DB OPERATIONS
        with transaction.atomic():
            created_variants = []

            for size in sizes:
                created_variants.append(
                    ProductVariant.objects.create(
                        product=product,
                        color=color.strip(),
                        size=size,
                        weight_kg=float(weights[size]),
                        stock=int(stocks[size]),
                        is_active=True,
                    )
                )

            # Images belong to the COLOR (first variant)
            image_owner = created_variants[0]

            for index, image in enumerate(images):
                ProductImage.objects.create(
                    variant=image_owner,
                    image=image,
                    is_primary=(index == 0),
                )

        messages.success(request, "Variant created successfully.")
        return redirect(
            "adminpanel:variant_list",
            product_id=product.id,
        )

    return render(
        request,
        "adminpanel/variants/variant_form.html",
        {"product": product},
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
                output_field=DecimalField(max_digits=12, decimal_places=4),
            )
        )
        .order_by("color", "size")
    )

    return render(
        request,
        "adminpanel/variants/variant_list.html",
        {
            "product": product,
            "variants": variants,
        },
    )
