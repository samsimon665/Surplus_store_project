from decimal import Decimal

from django.urls import reverse

from django.http import JsonResponse

from .models import Cart, CartItem, Wishlist, WishlistItem

from apps.catalog.models import Product, ProductVariant, ProductImage

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .services import get_cart_item_status, CartItemStatus

from django.db.models import Prefetch

from .services import can_proceed_to_checkout

from .services import is_cart_valid


def get_nav_counts(user):
    wishlist_count = WishlistItem.objects.filter(
        wishlist__user=user
    ).count()

    cart_count = CartItem.objects.filter(
        cart__user=user
    ).count()

    return {
        "wishlist_count": min(wishlist_count, 10),
        "cart_count": min(cart_count, 10),
    }


@login_required(login_url="accounts:login")
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    items = []

    if cart:
        for item in cart.items.select_related(
            "variant",
            "variant__product",
            "variant__product__subcategory",
            "variant__product__subcategory__category",
        ):

            status = get_cart_item_status(item)
            item.status = status
            item.is_out_of_stock = (status == CartItemStatus.OUT_OF_STOCK)

            # Generate product URL
            base_url = reverse(
                "catalog:product_detail",
                args=[
                    item.variant.product.subcategory.category.slug,
                    item.variant.product.subcategory.slug,
                    item.variant.product.slug,
                ],
            )

            # 🔥 Attach variant query param
            item.product_url = f"{base_url}?variant={item.variant.id}"

            # Image resolution
            item.display_image = (
                ProductImage.objects
                .filter(
                    variant__product=item.variant.product,
                    variant__color=item.color,
                )
                .order_by("-is_primary", "created_at")
                .first()
            )

            items.append(item)

    context = {
        "cart": cart,
        "cart_items": items,
        "checkout_allowed": can_proceed_to_checkout(cart),
        "cart_subtotal": cart.subtotal if cart else Decimal("0.00"),
        "cart_total": cart.total if cart else Decimal("0.00"),
        "shipping_cost": "FREE",
    }

    return render(request, "cart/cart_summary.html", context)




@login_required(login_url='accounts:login')
def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        variant_id = int(request.POST.get("variant_id"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid variant"}, status=400)

    variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
        is_active=True
    )

    if variant.stock < 1:
        return JsonResponse(
            {"error": "This item is out of stock"},
            status=409
        )

    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_item = CartItem.objects.filter(
        cart=cart,
        variant=variant
    ).first()

    if cart_item:
        if cart_item.quantity + 1 > variant.stock:
            return JsonResponse(
                {"error": f"Only {variant.stock} pieces available"},
                status=409
            )

        cart_item.quantity += 1
        cart_item.save(update_fields=["quantity"])

    else:
        price_per_kg = variant.product.subcategory.price_per_kg
        unit_price = Decimal(variant.weight_kg) * price_per_kg

        CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=1,

            product_name=variant.product.name,
            color=variant.color,
            size=variant.size,

            weight_kg=variant.weight_kg,
            price_per_kg=price_per_kg,
            unit_price=unit_price,
        )

    # -------------------------------------------------
    # ✅ WISHLIST → CART (SESSION-BASED, PRODUCT-LEVEL)
    # -------------------------------------------------
    move_product_id = request.session.get("move_to_cart_product_id")

    if move_product_id == variant.product.id:
        WishlistItem.objects.filter(
            wishlist__user=request.user,
            product_id=move_product_id
        ).delete()

        # 🔒 Clear intent after successful move
        del request.session["move_to_cart_product_id"]

    return JsonResponse({"success": True})


@login_required(login_url='accounts:login')
def update_cart_item(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    item_id = request.POST.get("item_id")
    action = request.POST.get("action")

    if not item_id or action not in ("increase", "decrease"):
        return JsonResponse({"error": "Invalid input"}, status=400)

    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    if action == "decrease":
        if item.quantity <= 1:
            return JsonResponse({"error": "Minimum quantity is 1"}, status=400)
        item.quantity -= 1

    elif action == "increase":
        if item.quantity + 1 > item.variant.stock:
            return JsonResponse(
                {"error": f"Only {item.variant.stock} pieces available"},
                status=409
            )
        item.quantity += 1

    item.save(update_fields=["quantity"])

    return JsonResponse({
        "success": True,
        "quantity": item.quantity,
        "status": get_cart_item_status(item),

        # ✅ CORRECT
        "item_line_total": str(item.display_line_total),

        "cart_subtotal": str(cart.subtotal),
        "cart_total": str(cart.total),
        "checkout_allowed": is_cart_valid(cart),
    })






@login_required
def remove_cart_item(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        item_id = int(request.POST.get("item_id"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid input"}, status=400)

    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    item.delete()

    return JsonResponse({"success": True})


@login_required
def remove_invalid_items(request):
    cart = get_object_or_404(Cart, user=request.user)

    removed = False

    for item in cart.items.select_related("variant"):
        if get_cart_item_status(item) != CartItemStatus.VALID:
            item.delete()
            removed = True

    return JsonResponse({
        "success": True,
        "removed": removed,
        "cart_subtotal": str(cart.subtotal),
        "cart_total": str(cart.total),
        "checkout_allowed": is_cart_valid(cart),
    })





# ----- WISHLIST -----


@login_required(login_url="accounts:login")
def wishlist_view(request):
    
    wishlist = Wishlist.objects.filter(user=request.user).first()

    wishlist_items = []
    if wishlist:
        wishlist_items = wishlist.items.select_related("product")

    context = {
        "wishlist": wishlist,
        "wishlist_items": wishlist_items,
    }

    return render(request, "cart/wishlist.html", context)


@login_required(login_url="accounts:login")
def toggle_wishlist(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    product_id = request.POST.get("product_id")
    if not product_id:
        return JsonResponse({"error": "Invalid product"}, status=400)

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    wishlist_item = WishlistItem.objects.filter(
        wishlist=wishlist,
        product=product
    ).first()

    if wishlist_item:
        wishlist_item.delete()
        return JsonResponse({
            "success": True,
            "action": "removed"
        })

    WishlistItem.objects.create(
        wishlist=wishlist,
        product=product
    )

    return JsonResponse({
        "success": True,
        "action": "added"
    })


@login_required(login_url="accounts:login")
def remove_from_wishlist(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    item_id = request.POST.get("item_id")
    if not item_id:
        return JsonResponse({"error": "Invalid item"}, status=400)

    WishlistItem.objects.filter(
        id=item_id,
        wishlist__user=request.user
    ).delete()

    return JsonResponse({"success": True})
