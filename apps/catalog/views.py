from django.shortcuts import render, get_object_or_404

from .models import ProductCategory, SubCategory, Product, ProductVariant, ProductImage

from django.db.models import Q

from django.db.models import Prefetch

from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required(login_url='accounts:login')
def home_view(request):
    categories = ProductCategory.objects.filter(is_active=True)

    return render(
        request,
        "catalog/home.html",
        {
            "categories": categories,
            "navbar_mode": "home",
        }
    )


@login_required(login_url='accounts:login')
def category_list(request):
    q = request.GET.get("q", "").strip()

    # ⬅️ DO NOT FILTER is_active here
    categories = ProductCategory.objects.all()

    if q:
        categories = categories.filter(name__icontains=q)

    categories = categories.order_by("name")

    has_active_categories = categories.filter(is_active=True).exists()

    return render(
        request,
        "catalog/categories.html",
        {
            "categories": categories,
            "has_active_categories": has_active_categories,
            "navbar_show": "categories",
        }
    )


@login_required(login_url='accounts:login')
def subcategory_list(request, category_slug=None):
    category = None

    # Base queryset: only valid, active subcategories
    subcategories = SubCategory.objects.filter(
        is_active=True,
        category__is_active=True
    ).select_related("category")

    if category_slug:
        # ✅ DO NOT raise 404
        category = ProductCategory.objects.filter(
            slug=category_slug
        ).first()

        if category and category.is_active:
            subcategories = subcategories.filter(category=category)
        else:
            # category inactive OR does not exist
            subcategories = SubCategory.objects.none()

    subcategories = subcategories.order_by("category__name", "name")

    return render(
        request,
        "catalog/subcategories.html",
        {
            # Pass category only if active
            "category": category if category and category.is_active else None,
            "subcategories": subcategories,
            "navbar_show": "subcategories",
        }
    )


@login_required(login_url='accounts:login')
def product_list(request, subcategory_slug=None):
    subcategory = None

    products = Product.objects.filter(
        is_active=True,
        subcategory__is_active=True,
        subcategory__category__is_active=True,
        variants__is_active=True,   # ✅ ONLY SELLABLE PRODUCTS
    ).select_related(
        "subcategory",
        "subcategory__category"
    ).distinct()

    # 1️⃣ Filter by subcategory
    if subcategory_slug:
        subcategory = get_object_or_404(
            SubCategory,
            slug=subcategory_slug,
            is_active=True,
            category__is_active=True,
        )
        products = products.filter(subcategory=subcategory)

    # 2️⃣ Search
    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(subcategory__name__icontains=q)
        )

    products = products.order_by("name")

    return render(
        request,
        "catalog/product_list.html",
        {
            "products": products,
            "subcategory": subcategory,
            "search_query": q,
            "navbar_show": "products",
        }
    )


@login_required(login_url='accounts:login')
def product_detail(request, category_slug, subcategory_slug, product_slug):
    product = get_object_or_404(
        Product.objects.select_related(
            "subcategory",
            "subcategory__category"
        ),
        slug=product_slug,
        subcategory__slug=subcategory_slug,
        subcategory__category__slug=category_slug,
        is_active=True,
    )

    variants = (
        ProductVariant.objects
        .filter(product=product, is_active=True)
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by(
                    "-is_primary", "created_at"
                )
            )
        )
    )

    variant_map = {}

    for variant in variants:
        color = variant.color

        if color not in variant_map:
            variant_map[color] = {
                "color": color,
                "sizes": [],
                "images": []
            }

        variant_map[color]["sizes"].append({
            "size": variant.size,
            "weight_kg": variant.weight_kg,
            "stock": variant.stock,
            "variant_id": variant.id,
            "variant_id": variant.id,

        })

        for img in variant.images.all():
            if img.image.url not in variant_map[color]["images"]:
                variant_map[color]["images"].append(img.image.url)

    recommended_products = (
        Product.objects.filter(
            subcategory=product.subcategory,
            is_active=True
        )
        .exclude(id=product.id)
        .select_related("subcategory")
        .prefetch_related(
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True).prefetch_related(
                    Prefetch(
                        "images",
                        queryset=ProductImage.objects.order_by(
                            "-is_primary", "created_at")
                    )
                )
            )
        )
        .order_by("-created_at")[:4]
    )

    context = {
        "product": product,
        "subcategory": product.subcategory,
        "price_per_kg": product.subcategory.price_per_kg,
        "variants": variant_map,
        "recommended_products": recommended_products,
    }

    return render(request, "catalog/product_details.html", context)


@login_required(login_url='accounts:login')
def product_detail(request, category_slug, subcategory_slug, product_slug):

    product = get_object_or_404(
        Product.objects
        .filter(
            is_active=True,
            variants__is_active=True,   # 🔒 CRITICAL FIX
        )
        .select_related(
            "subcategory",
            "subcategory__category"
        )
        .distinct(),
        slug=product_slug,
        subcategory__slug=subcategory_slug,
        subcategory__category__slug=category_slug,
    )

    variants = (
        ProductVariant.objects
        .filter(
            product=product,
            is_active=True
        )
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by(
                    "-is_primary",
                    "created_at"
                )
            )
        )
    )

    variant_map = {}

    for variant in variants:
        color = variant.color

        if color not in variant_map:
            variant_map[color] = {
                "color": color,
                "sizes": [],
                "images": []
            }

        variant_map[color]["sizes"].append({
            "size": variant.size,
            "weight_kg": variant.weight_kg,
            "stock": variant.stock,
            "variant_id": variant.id,
        })

        for img in variant.images.all():
            if img.image.url not in variant_map[color]["images"]:
                variant_map[color]["images"].append(img.image.url)


    # 🔒 RECOMMENDED PRODUCTS — SAFE VERSION
    recommended_products = (
        Product.objects
        .filter(
            subcategory=product.subcategory,
            is_active=True,
            variants__is_active=True,   # 🔒 CRITICAL FIX
        )
        .exclude(id=product.id)
        .distinct()
        .select_related("subcategory")
        .prefetch_related(
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(
                    is_active=True
                ).prefetch_related(
                    Prefetch(
                        "images",
                        queryset=ProductImage.objects.order_by(
                            "-is_primary",
                            "created_at"
                        )
                    )
                )
            )
        )
        .order_by("-created_at")[:4]
    )

    context = {
        "product": product,
        "subcategory": product.subcategory,
        "price_per_kg": product.subcategory.price_per_kg,
        "variants": variant_map,
        "recommended_products": recommended_products,
    }

    return render(
        request,
        "catalog/product_details.html",
        context
    )
