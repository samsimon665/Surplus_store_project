  
from django.shortcuts import render, get_object_or_404

# Create your views here.
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Cart, CartItem
from apps.catalog.models import ProductVariant

from .services import get_cart_item_status, CartItemStatus


@login_required(login_url='accounts:login')
def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        variant_id = int(request.POST.get("variant_id"))
        requested_qty = int(request.POST.get("quantity"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid input"}, status=400)

    if requested_qty <= 0:
        return JsonResponse({"error": "Quantity must be at least 1"}, status=400)

    variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
        is_active=True
    )

    # Stock check (first gate)
    if requested_qty > variant.stock:
        return JsonResponse(
            {"error": f"Only {variant.stock} pieces available"},
            status=409
        )

    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_item = CartItem.objects.filter(cart=cart, variant=variant).first()

    if cart_item:
        new_qty = cart_item.quantity + requested_qty

        # Stock check (merge gate)
        if new_qty > variant.stock:
            return JsonResponse(
                {"error": f"Only {variant.stock} pieces available"},
                status=409
            )

        cart_item.quantity = new_qty
        cart_item.save(update_fields=["quantity"])
    else:
        # ---- SNAPSHOT ON CREATE ----
        price_per_kg = variant.product.subcategory.price_per_kg
        unit_price = (Decimal(variant.weight_grams) /
                      Decimal(1000)) * price_per_kg

        CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=requested_qty,
            product_name=variant.product.name,
            color=variant.color,
            size=variant.size,
            weight_grams=variant.weight_grams,
            price_per_kg=price_per_kg,
            unit_price=unit_price,
        )

    return JsonResponse({"success": True})


@login_required
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()

    cart_items = []
    checkout_allowed = True

    if cart:
        for item in cart.items.select_related("variant"):
            status = get_cart_item_status(item)

            # flags for template (DTL-safe)
            item.is_out_of_stock = (status == CartItemStatus.OUT_OF_STOCK)
            item.is_min_quantity = (item.quantity <= 1)
            item.status = status  # expose status safely

            if status != CartItemStatus.VALID:
                checkout_allowed = False

            cart_items.append(item)

    context = {
        "cart_items": cart_items,
        "checkout_allowed": checkout_allowed,
    }

    return render(request, "cart/cart_summary.html", context)



@login_required
def update_cart_item(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        item_id = int(request.POST.get("item_id"))
        new_qty = int(request.POST.get("quantity"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid input"}, status=400)

    if new_qty < 1:
        return JsonResponse({"error": "Quantity must be at least 1"}, status=400)

    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    variant = item.variant

    # Stock validation
    if new_qty > variant.stock:
        return JsonResponse(
            {"error": f"Only {variant.stock} pieces available"},
            status=409
        )

    item.quantity = new_qty
    item.save(update_fields=["quantity"])

    status = get_cart_item_status(item)

    return JsonResponse({
        "success": True,
        "status": status,
        "quantity": item.quantity
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
