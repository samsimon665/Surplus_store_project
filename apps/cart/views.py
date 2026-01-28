
# Create your views here.
from decimal import Decimal

from django.http import JsonResponse

from .models import Cart, CartItem
from apps.catalog.models import ProductVariant, ProductImage

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .services import get_cart_item_status, CartItemStatus

from django.db.models import Prefetch




@login_required(login_url="accounts:login")
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()

    checkout_allowed = True
    items = []

    if cart:
        for item in (
            cart.items
            .select_related("variant", "variant__product")
        ):
            status = get_cart_item_status(item)

            item.status = status
            item.is_out_of_stock = (status == CartItemStatus.OUT_OF_STOCK)

            # ✅ CORRECT IMAGE RESOLUTION (color-based)
            item.display_image = (
                ProductImage.objects
                .filter(
                    variant__product=item.variant.product,
                    variant__color=item.variant.color,
                )
                .order_by("-is_primary", "created_at")
                .first()
            )

            if status != CartItemStatus.VALID:
                checkout_allowed = False

            items.append(item)



    context = {
        "cart": cart,
        "cart_items": items,
        "checkout_allowed": checkout_allowed,
        "cart_subtotal": cart.subtotal if cart else Decimal("0.00"),
        "cart_total": cart.total if cart else Decimal("0.00"),
        "shipping_cost": "FREE",
        "discount_amount": None,
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

    requested_qty = 1  # ✅ DEFAULT

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

    cart_item = CartItem.objects.filter(cart=cart, variant=variant).first()

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
            quantity=requested_qty,

            product_name=variant.product.name,
            color=variant.color,
            size=variant.size,

            weight_kg=variant.weight_kg,   # ✅ MATCHES MODEL
            price_per_kg=price_per_kg,
            unit_price=unit_price,
        )

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
        "cart_subtotal": str(cart.subtotal),
        "cart_total": str(cart.total),
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
