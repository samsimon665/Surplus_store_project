from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from apps.cart.models import Cart
from apps.cart.services import can_proceed_to_checkout
from .services import get_shipping_preview
from allauth.account.models import EmailAddress


@login_required(login_url="accounts:login")
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

    # ✅ Verified email (source of truth)
    email_verified = EmailAddress.objects.filter(
        user=request.user,
        verified=True,
        primary=True
    ).exists()

    # 📞 Phone presence (not mandatory)
    phone_present = bool(request.user.profile.phone)

    # 📍 Addresses (default first)
    addresses = request.user.addresses.all().order_by("-is_default", "-created_at")
    default_address = addresses.filter(is_default=True).first()

    # 🚚 Shipping previews
    standard_shipping = get_shipping_preview("standard")
    express_shipping = get_shipping_preview("express")

    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "cart_items": cart.items.select_related("variant"),
            "cart_subtotal": cart.subtotal,
            "email_verified": email_verified,
            "phone_present": phone_present,
            "addresses": addresses,
            "default_address": default_address,
            "standard_shipping": standard_shipping,
            "express_shipping": express_shipping,
        }
    )
