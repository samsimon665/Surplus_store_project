from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django import forms

from django.db import transaction
from django.db.models import F, DecimalField, ExpressionWrapper, Sum

from apps.adminpanel.decorators import admin_required
from apps.catalog.models import Product, ProductVariant, ProductImage

from apps.adminpanel.utils.validations import validate_variant_data
from collections import defaultdict
from django.core.exceptions import ValidationError

from decimal import Decimal




@admin_required
def variant_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        color = request.POST.get("color")
        sizes = request.POST.getlist("sizes")

        sizes = [s.strip().upper() for s in sizes]
        
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

    # Fetch variants with correct size order and pricing
    variants = (
        ProductVariant.objects
        .filter(product=product)
        .select_related("product__subcategory")
        .prefetch_related("images")
        .annotate(
            final_price=ExpressionWrapper(
                F("weight_kg") * F("product__subcategory__price_per_kg"),
                output_field=DecimalField(max_digits=12, decimal_places=4),
            )
        )
        .order_by("color", "size_order")
    )

    # ✅ SIMPLE TOTAL STOCK (ALL VARIANTS)
    total_stock = variants.aggregate(total=Sum("stock"))["total"] or 0

    return render(
        request,
        "adminpanel/variants/variant_list.html",
        {
            "product": product,
            "variants": variants,
            "total_stock": total_stock,
        },
    )


@admin_required
def variant_edit(request, product_id, variant_id):
    """
    Edit a COLOR VARIANT (all sizes under the same color).
    """

    # =====================================================
    # 1️⃣ Base variant (anchor)
    # =====================================================
    base_variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
        product_id=product_id
    )

    product = base_variant.product
    original_color = base_variant.color

    # =====================================================
    # 2️⃣ Fetch ALL variants in this color group
    # =====================================================
    variants = (
        ProductVariant.objects
        .filter(product=product, color=original_color)
        .order_by("size_order")
    )

    # =====================================================
    # 3️⃣ Image owner (images attached to ONE variant)
    # =====================================================
    image_owner = variants.first()

    existing_images = list(
        image_owner.images.values("id", "image", "is_primary")
    )

    # =====================================================
    # 4️⃣ Prepare restore data
    # =====================================================
    posted_sizes = []
    weights = {}
    stocks = {}

    for v in variants:
        posted_sizes.append(v.size)
        weights[v.size] = str(v.weight_kg)
        stocks[v.size] = v.stock

    posted_data = {
        "color": original_color,
        "weights": weights,
        "stocks": stocks,
    }

    # =====================================================
    # ===================== POST ==========================
    # =====================================================
    if request.method == "POST":
        try:
            with transaction.atomic():

                # -----------------------------
                # COLOR VALIDATION
                # -----------------------------
                new_color = request.POST.get("color", "").strip()

                if not new_color:
                    raise ValidationError({"color": "Color is required."})

                if new_color.lower() != original_color.lower():
                    conflict = ProductVariant.objects.filter(
                        product=product,
                        color__iexact=new_color
                    ).exists()

                    if conflict:
                        raise ValidationError({
                            "color": "This color already exists for this product."
                        })

                # -----------------------------
                # UPDATE SIZE VARIANTS
                # -----------------------------
                for v in variants:
                    size = v.size

                    v.color = new_color
                    v.weight_kg = Decimal(
                        request.POST.get(f"weight[{size}]", "0")
                    )
                    v.stock = int(
                        request.POST.get(f"stock[{size}]", "0")
                    )

                    v.full_clean()
                    v.save()

                # ===============================
                # IMAGE VALIDATION
                # ===============================
                deleted_ids = [
                    int(i) for i in
                    request.POST.get("deleted_images", "").split(",")
                    if i.isdigit()
                ]

                uploaded_images = request.FILES.getlist("images")

                existing_count = ProductImage.objects.filter(
                    variant=image_owner
                ).count()

                final_count = existing_count - len(deleted_ids) + len(uploaded_images)

                if final_count < 2:
                    raise ValidationError(
                        "At least 2 images are required for a variant."
                    )

                if final_count > 4:
                    raise ValidationError(
                        "You can have a maximum of 4 images per variant."
                    )

                # ===============================
                # DELETE (SINGLE SOURCE OF TRUTH)
                # ===============================
                if deleted_ids:
                    ProductImage.objects.filter(
                        id__in=deleted_ids,
                        variant=image_owner
                    ).delete()

                # ===============================
                # ADD NEW IMAGES
                # ===============================
                has_primary = ProductImage.objects.filter(
                    variant=image_owner,
                    is_primary=True
                ).exists()

                for idx, img in enumerate(uploaded_images):
                    ProductImage.objects.create(
                        variant=image_owner,
                        image=img,
                        is_primary=(not has_primary and idx == 0)
                    )

               
                print("DELETED IMAGES RAW:", request.POST.get("deleted_images"))


                print("POST KEYS:", request.POST.keys())




                messages.success(request, "Variant updated successfully.")

                return redirect(
                    "adminpanel:variant_list",
                    product_id=product.id
                )

        except ValidationError as e:
            posted_data["color"] = new_color

            if hasattr(e, "message_dict"):
                # field-based validation errors
                for msgs in e.message_dict.values():
                    for msg in msgs:
                        messages.error(request, msg)
            else:
                # non-field (string) validation errors
                for msg in e.messages:
                    messages.error(request, msg)


    # =====================================================
    # ===================== GET ===========================
    # =====================================================
    return render(
        request,
        "adminpanel/variants/variant_form.html",
        {
            "product": product,
            "is_edit": True,

            "posted_sizes": posted_sizes,
            "posted_data": posted_data,
            "existing_images": existing_images,
        },
    )
