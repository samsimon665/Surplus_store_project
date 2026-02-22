from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from apps.cart.models import Cart
from apps.cart.services import can_proceed_to_checkout

from allauth.account.models import EmailAddress   # ✅ add this


@login_required
def start_checkout(request):
    cart = Cart.objects.filter(user=request.user).first()

    # 🚫 No cart or empty cart
    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart")

    # 🔒 HARD RE-VALIDATION
    if not can_proceed_to_checkout(cart):
        messages.error(
            request,
            "Your cart contains out-of-stock or unavailable items."
        )
        return redirect("cart:cart")

    # ✅ Check verified email using allauth (REAL SOURCE OF TRUTH)
    email_verified = EmailAddress.objects.filter(
        user=request.user,
        verified=True,
        primary=True
    ).exists()

    # Address

    addresses = request.user.addresses.all()
    default_address = addresses.filter(is_default=True).first()

    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "cart_items": cart.items.select_related("variant"),
            "subtotal": cart.subtotal,
            "total": cart.total,
            "email_verified": email_verified,   # ✅ pass this
            "addresses": addresses,
            "default_address": default_address,
        }
    )
