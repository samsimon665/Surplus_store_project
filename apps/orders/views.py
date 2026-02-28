
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from apps.cart.models import Cart
from apps.cart.services import can_proceed_to_checkout
from apps.promotions.services import validate_promo_for_cart
from .services import get_shipping_preview, calculate_checkout_totals

from allauth.account.models import EmailAddress




@login_required(login_url="accounts:login")
def start_checkout(request):

    cart = Cart.objects.filter(user=request.user).first()

    # -----------------------------------
    # 1️⃣ Cart existence check
    # -----------------------------------
    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart")

    # -----------------------------------
    # 2️⃣ Hard cart validation
    # -----------------------------------
    if not can_proceed_to_checkout(cart):
        messages.error(
            request,
            "Your cart contains unavailable or out-of-stock items."
        )
        return redirect("cart:cart")

    # -----------------------------------
    # 3️⃣ Email verification (required)
    # -----------------------------------
    email_verified = EmailAddress.objects.filter(
        user=request.user,
        verified=True,
        primary=True
    ).exists()

    if not email_verified:
        messages.error(request, "Please verify your email before checkout.")
        return redirect("accounts:profile")

    # -----------------------------------
    # 4️⃣ Phone (optional)
    # -----------------------------------
    phone_present = bool(
        hasattr(request.user, "profile") and request.user.profile.phone
    )

    # -----------------------------------
    # 5️⃣ Address loading
    # -----------------------------------
    addresses = request.user.addresses.all().order_by(
        "-is_default",
        "-created_at"
    )
    default_address = addresses.filter(is_default=True).first()

    # -----------------------------------
    # 6️⃣ Shipping preview
    # -----------------------------------
    selected_shipping = request.GET.get("shipping", "standard")

    standard_shipping = get_shipping_preview("standard")
    express_shipping = get_shipping_preview("express")

    if selected_shipping == "express":
        shipping_fee = Decimal(express_shipping.fee)
        shipping_data = express_shipping
    else:
        shipping_fee = Decimal("0.00")
        shipping_data = standard_shipping

    # -----------------------------------
    # 7️⃣ Promo Revalidation (Optional)
    # -----------------------------------
    applied_code = request.session.get("applied_promo")

    discount = Decimal("0.00")
    applied_promo = None
    promo_error = None

    if applied_code:

        result = validate_promo_for_cart(
            user=request.user,
            cart=cart,
            code=applied_code
        )

        if result.success:
            discount = result.discount
            applied_promo = result.promo
        else:
            # Remove invalid promo
            request.session.pop("applied_promo", None)
            promo_error = result.error

    # -----------------------------------
    # 8️⃣ Tax calculation (12% GST example)
    # -----------------------------------
    taxable_amount = cart.subtotal - discount
    tax_rate = Decimal("0.12")
    tax_amount = taxable_amount * tax_rate

    # -----------------------------------
    # 9️⃣ Final total
    # -----------------------------------
    final_total = taxable_amount + tax_amount + shipping_fee

    # -----------------------------------
    # 10️⃣ Render
    # -----------------------------------
    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "cart_items": cart.items.select_related("variant"),
            "cart_subtotal": cart.subtotal,
            "discount": discount,
            "applied_promo": applied_promo,
            "promo_error": promo_error,
            "shipping_fee": shipping_fee,
            "selected_shipping": selected_shipping,
            "tax_amount": tax_amount,
            "final_total": final_total,
            "email_verified": email_verified,
            "phone_present": phone_present,
            "addresses": addresses,
            "default_address": default_address,
            "standard_shipping": standard_shipping,
            "express_shipping": express_shipping,
            "shipping_data": shipping_data,
        }
    )




@require_POST
@login_required(login_url="accounts:login")
def update_promo_ajax(request):

    action = request.POST.get("action")
    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        return JsonResponse({
            "success": False,
            "error": "Your cart is empty."
        }, status=400)

    # ---------------------------
    # REMOVE PROMO
    # ---------------------------
    if action == "remove":

        request.session.pop("applied_promo", None)

        totals = calculate_checkout_totals(
            cart=cart,
            discount_amount=Decimal("0.00"),
            shipping_fee=Decimal("0.00"),
            tax_rate=Decimal("0.12"),
        )

        return JsonResponse({
            "success": True,
            "discount": "0.00",
            "tax": str(totals["tax"]),
            "total": str(totals["total"]),
            "discounted_subtotal": str(totals["discounted_subtotal"]),
        })

    # ---------------------------
    # APPLY PROMO
    # ---------------------------
    if action == "apply":

        code = request.POST.get("promo_code", "").strip()

        result = validate_promo_for_cart(
            user=request.user,
            cart=cart,
            code=code
        )

        if not result.success:
            return JsonResponse({
                "success": False,
                "error": result.error
            }, status=400)

        request.session["applied_promo"] = result.promo.code

        totals = calculate_checkout_totals(
            cart=cart,
            discount_amount=result.discount,
            shipping_fee=Decimal("0.00"),
            tax_rate=Decimal("0.12"),
        )

        return JsonResponse({
            "success": True,
            "code": result.promo.code,
            "discount": str(totals["discount"]),
            "tax": str(totals["tax"]),
            "total": str(totals["total"]),
            "discounted_subtotal": str(totals["discounted_subtotal"]),
        })

    # ---------------------------
    # INVALID ACTION
    # ---------------------------
    return JsonResponse({
        "success": False,
        "error": "Invalid action."
    }, status=400)
