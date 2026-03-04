
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from apps.cart.models import Cart
from apps.cart.services import can_proceed_to_checkout
from apps.promotions.services import validate_promo_for_cart
from .services import get_shipping_preview, calculate_checkout_totals

from allauth.account.models import EmailAddress

from django.utils import timezone

from apps.catalog.models import ProductImage

from decimal import Decimal, ROUND_HALF_UP



@login_required(login_url="accounts:login")
def start_checkout(request):

    # -------------------------------------------------
    # 1️⃣ Load Cart
    # -------------------------------------------------
    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart")

    if not can_proceed_to_checkout(cart):
        messages.error(
            request,
            "Your cart contains unavailable or out-of-stock items."
        )
        return redirect("cart:cart")

    # -------------------------------------------------
    # 2️⃣ Email Verification (Required)
    # -------------------------------------------------
    email_verified = EmailAddress.objects.filter(
        user=request.user,
        verified=True,
        primary=True
    ).exists()

    if not email_verified:
        messages.error(request, "Please verify your email before checkout.")
        return redirect("accounts:profile")

    # -------------------------------------------------
    # 3️⃣ Phone (Optional)
    # -------------------------------------------------
    phone_present = bool(
        hasattr(request.user, "profile") and request.user.profile.phone
    )

    # -------------------------------------------------
    # 4️⃣ Addresses
    # -------------------------------------------------
    addresses = request.user.addresses.all().order_by(
        "-is_default",
        "-created_at"
    )
    default_address = addresses.filter(is_default=True).first()

    # -------------------------------------------------
    # 5️⃣ Shipping
    # -------------------------------------------------
    selected_shipping = request.GET.get("shipping", "standard")

    standard_shipping = get_shipping_preview("standard")
    express_shipping = get_shipping_preview("express")

    if selected_shipping == "express":
        shipping_fee = Decimal(express_shipping["fee"])
    else:
        shipping_fee = Decimal("0.00")

    # -------------------------------------------------
    # 6️⃣ Build Cart Items (LIKE cart_view)
    # -------------------------------------------------
    cart_items = []

    for item in cart.items.select_related(
        "variant",
        "variant__product",
        "variant__product__subcategory",
        "variant__product__subcategory__category",
    ):

        # Attach correct image based on color
        item.display_image = (
            ProductImage.objects
            .filter(
                variant__product=item.variant.product,
                variant__color=item.color,
            )
            .order_by("-is_primary", "created_at")
            .first()
        )

        cart_items.append(item)

    # -------------------------------------------------
    # 7️⃣ Promo Revalidation
    # -------------------------------------------------
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
            promo_error = result.error

    # -------------------------------------------------
    # 8️⃣ Totals Calculation
    # -------------------------------------------------
    subtotal = cart.subtotal
    taxable_amount = subtotal - discount

    tax_rate = Decimal("12.00")

    tax_amount = (
        taxable_amount * tax_rate / Decimal("100")
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    final_total = (
        taxable_amount + tax_amount + shipping_fee
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    # -------------------------------------------------
    # 10 Totals Weight 
    # -------------------------------------------------

    total_weight = sum(
        item.weight_kg * item.quantity
        for item in cart.items.all()
    )


    # -------------------------------------------------
    # 9️⃣ Render
    # -------------------------------------------------
    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "cart_items": cart_items,

            "cart_subtotal": subtotal,
            "discount": discount,
            "applied_promo": applied_promo,
            "promo_error": promo_error,

            "shipping_fee": shipping_fee,
            "selected_shipping": selected_shipping,
            "standard_shipping": standard_shipping,
            "express_shipping": express_shipping,

            "total_weight": round(total_weight, 3),

            "tax_amount": tax_amount,
            "final_total": final_total,

            "email_verified": email_verified,
            "phone_present": phone_present,

            "addresses": addresses,
            "default_address": default_address,
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

        return JsonResponse({
            "success": True
        })

    # ---------------------------
    # APPLY PROMO
    # ---------------------------
    if action == "apply":

        code = request.POST.get("promo_code", "").strip()

        if not code:
            return JsonResponse({
                "success": False,
                "error": "Please enter a promo code."
            }, status=400)

        result = validate_promo_for_cart(
            user=request.user,
            cart=cart,
            code=code
        )

        if result.success:

            # ✅ Store only if valid
            request.session["applied_promo"] = code.upper()

            return JsonResponse({
                "success": True,
                "code": result.promo.code,
                "discount": str(result.discount)
            })

        else:

            # ❌ Remove invalid promo from session
            request.session.pop("applied_promo", None)

            return JsonResponse({
                "success": False,
                "error": result.error
            }, status=400)

    # ---------------------------
    # INVALID ACTION
    # ---------------------------
    return JsonResponse({
        "success": False,
        "error": "Invalid action."
    }, status=400)


@require_POST
@login_required(login_url="accounts:login")
def update_checkout_summary(request):

    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        return JsonResponse({"error": "Cart empty"}, status=400)

    shipping_method = request.POST.get("shipping", "standard")

    # --------------------
    # SHIPPING
    # --------------------
    if shipping_method == "express":
        express = get_shipping_preview("express")
        shipping_fee = Decimal(express["fee"])
    else:
        shipping_fee = Decimal("0.00")

    # --------------------
    # PROMO (from session)
    # --------------------
    applied_code = request.session.get("applied_promo")
    discount = Decimal("0.00")

    if applied_code:
        result = validate_promo_for_cart(
            user=request.user,
            cart=cart,
            code=applied_code
        )
        if result.success:
            discount = result.discount

    # --------------------
    # TOTAL WEIGHT
    # --------------------
    total_weight = sum(
        item.weight_kg * item.quantity
        for item in cart.items.all()
    )

    # --------------------
    # TAX + TOTAL
    # --------------------
    subtotal = cart.subtotal
    taxable_amount = subtotal - discount
    tax_rate = Decimal("12.00")

    tax_amount = (
        taxable_amount * tax_rate / Decimal("100")
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    final_total = (
        taxable_amount + tax_amount + shipping_fee
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    return JsonResponse({
        "subtotal": str(subtotal),
        "discount": str(discount),
        "shipping": str(shipping_fee),
        "tax": str(tax_amount),
        "total": str(final_total),
        "weight": str(round(total_weight, 3)),
    })


