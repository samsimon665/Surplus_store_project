# apps/orders/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.cart.models import Cart
from apps.cart.services import can_proceed_to_checkout


@login_required
def start_checkout(request):
    cart = Cart.objects.filter(user=request.user).first()

    # 🚫 No cart or empty cart
    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart")

    # 🔒 HARD RE-VALIDATION (MANDATORY)
    if not can_proceed_to_checkout(cart):
        messages.error(
            request,
            "Your cart contains out-of-stock or unavailable items. Please fix them before checkout."
        )
        return redirect("cart:cart")

    # ✅ SAFE TO ENTER CHECKOUT
    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "cart_items": cart.items.select_related("variant"),
            "subtotal": cart.subtotal,
            "total": cart.total,
        }
    )
