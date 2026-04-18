from django.utils import timezone
from apps.cart.services import can_proceed_to_checkout
from apps.orders.models import Order, OrderItem
from apps.cart.services import get_cart_item_status, CartItemStatus
from apps.cart.services import round_money

from apps.promotions.services import validate_promo_for_cart
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.payments.models import Payment
from apps.payments.services import create_razorpay_order

from apps.cart.services import (
    can_proceed_to_checkout,
    get_cart_item_status,
    CartItemStatus,
    round_money,
)


@transaction.atomic
def create_order_from_checkout(request, cart, shipping_method, address_text):

    # -------------------------------------------------
    # 0️⃣ HARD VALIDATION (FINAL GATE)
    # -------------------------------------------------
    if not cart or not cart.items.exists():
        raise ValidationError("Cart is empty.")

    if not can_proceed_to_checkout(cart):
        raise ValidationError(
            "Cart contains out-of-stock or unavailable items."
        )

    # -------------------------------------------------
    # 1️⃣ SHIPPING (Backend Controlled Only)
    # -------------------------------------------------
    if shipping_method == "express":
        shipping_fee = Decimal("99.00")
        min_days = 4
        max_days = 5
    else:
        shipping_method = "standard"
        shipping_fee = Decimal("0.00")
        min_days = 7
        max_days = 8

    today = date.today()
    delivery_start = today + timedelta(days=min_days)
    delivery_end = today + timedelta(days=max_days)

    # -------------------------------------------------
    # 2️⃣ SUBTOTAL + ITEM VALIDATION + PRICE RECHECK
    # -------------------------------------------------
    subtotal = Decimal("0.00")
    total_weight = Decimal("0.000")

    order_items_data = []

    for item in cart.items.select_related(
        "variant",
        "variant__product",
        "variant__product__subcategory"
    ):

        # 🔒 Validate item status again
        status = get_cart_item_status(item)
        if status != CartItemStatus.VALID:
            raise ValidationError(
                f"{item.product_name} is no longer available."
            )

        # 🔒 Price revalidation from source
        current_price_per_kg = (
            item.variant.product.subcategory.price_per_kg
        )

        recalculated_unit_price = (
            item.variant.weight_kg * current_price_per_kg
        )
        recalculated_unit_price = round_money(recalculated_unit_price)

        line_total = round_money(
            recalculated_unit_price * item.quantity
        )

        subtotal += line_total
        total_weight += item.weight_kg * item.quantity

        product = item.variant.product
        
        image = None
        if product and product.main_image:
            image = request.build_absolute_uri(product.main_image.url)


        order_items_data.append({
            "product_name": product.name,
            "color": item.color,
            "size": item.size,
            "quantity": item.quantity,
            "weight_kg": item.weight_kg,
            "unit_price": recalculated_unit_price,
            "total_price": line_total,
            "variant_id": item.variant.id,
            "image_url": image,

            "product_url": request.build_absolute_uri(product.get_absolute_url()) if product else None,
        })

    subtotal = round_money(subtotal)

    # -------------------------------------------------
    # 3️⃣ PROMO (Revalidate From Session)
    # -------------------------------------------------
    discount = Decimal("0.00")
    promo_code = request.session.get("applied_promo")

    if promo_code:
        result = validate_promo_for_cart(
            user=request.user,
            cart=cart,
            code=promo_code
        )

        if result.success:
            discount = round_money(result.discount)
        else:
            promo_code = None

    taxable_amount = subtotal - discount

    if taxable_amount < Decimal("0.00"):
        taxable_amount = Decimal("0.00")

    # -------------------------------------------------
    # 4️⃣ TAX (12% — Whole Rupee Rounding Intentional)
    # -------------------------------------------------
    tax_rate = Decimal("12.00")

    tax_amount = (
        taxable_amount * tax_rate / Decimal("100")
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    # -------------------------------------------------
    # 5️⃣ FINAL TOTAL
    # -------------------------------------------------
    total_amount = (
        taxable_amount + tax_amount + shipping_fee
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    # -------------------------------------------------
    # 6️⃣ CREATE ORDER (LOCKED SNAPSHOT)
    # -------------------------------------------------
    order = Order.objects.create(
        user=request.user,
        address_text=address_text,

        subtotal=subtotal,
        discount_amount=discount,

        tax_rate=tax_rate,
        tax_amount=tax_amount,

        shipping_method=shipping_method,
        shipping_fee=shipping_fee,

        total_amount=total_amount,
        total_weight_kg=total_weight,

        promo_code=promo_code if promo_code else None,

        delivery_start=delivery_start,
        delivery_end=delivery_end,

        status="pending",
        payment_status="pending",
    )

    # Create Razorpay Order
    
    razorpay_order = create_razorpay_order(order)


    if not razorpay_order:
        raise ValidationError(
            "Payment gateway unavailable. Please try again."
        )

    # Save Payment record
    Payment.objects.create(
        order=order,
        gateway="razorpay",
        razorpay_order_id=razorpay_order["id"],
        amount=order.total_amount,
        status="created"
    )

    # -------------------------------------------------
    # 7️⃣ CREATE ORDER ITEMS
    # -------------------------------------------------
    for data in order_items_data:
        OrderItem.objects.create(order=order, **data)


    return order, razorpay_order


def get_shipping_preview(shipping_method: str):
    if shipping_method == "express":
        fee = Decimal("99.00")
        min_days = 4
        max_days = 5
    else:
        fee = Decimal("0.00")
        min_days = 7
        max_days = 8
        shipping_method = "standard"

    today = date.today()
    start = today + timedelta(days=min_days)
    end = today + timedelta(days=max_days)

    return {
        "method": shipping_method,
        "fee": fee,
        "min_days": min_days,
        "max_days": max_days,
        "start_date": start,
        "end_date": end,
    }


def calculate_checkout_totals(
    cart,
    discount_amount=Decimal("0.00"),
    shipping_fee=Decimal("0.00"),
    tax_rate=Decimal("0.00")  # Example: Decimal("0.12") for 12%
):
    """
    Centralized total calculation.
    All checkout math must happen here.
    """

    subtotal = cart.subtotal

    discounted_subtotal = subtotal - discount_amount

    # Safety: never allow negative
    if discounted_subtotal < Decimal("0.00"):
        discounted_subtotal = Decimal("0.00")

    tax_amount = discounted_subtotal * tax_rate

    total = discounted_subtotal + shipping_fee + tax_amount

    return {
        "subtotal": subtotal,
        "discount": discount_amount,
        "discounted_subtotal": discounted_subtotal,
        "tax": tax_amount,
        "shipping": shipping_fee,
        "total": total,
    }


def cart_matches_order(cart, order):

    cart_items = list(
        cart.items.values_list(
            "variant_id",
            "size",
            "color",
            "quantity"
        )
    )

    order_items = list(
        order.items.values_list(
            "variant_id",
            "size",
            "color",
            "quantity"
        )
    )

    return sorted(cart_items) == sorted(order_items)

