from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.cart.services import can_proceed_to_checkout
from apps.orders.models import Order, OrderItem
from apps.cart.services import get_cart_item_status, CartItemStatus
from apps.cart.services import round_money


@transaction.atomic
def create_order_from_cart(cart, address_text, shipping_method, promo_code=None):
    """
    Converts a cart into a locked Order.
    This is the ONLY place where an Order is created.
    """

    if not cart or not cart.items.exists():
        raise ValidationError("Cart is empty.")

    # 🔒 HARD RE-VALIDATION
    if not can_proceed_to_checkout(cart):
        raise ValidationError(
            "Cart contains out-of-stock or unavailable items."
        )

    subtotal = Decimal("0.00")
    total_weight = Decimal("0.000")

    # 🚚 Shipping Calculation (NEVER trust frontend)
    if shipping_method == "express":
        shipping_fee = Decimal("99.00")
        min_days = 4
        max_days = 5
    else:
        shipping_fee = Decimal("0.00")
        min_days = 7
        max_days = 8
        shipping_method = "standard"

    today = date.today()
    delivery_start = today + timedelta(days=min_days)
    delivery_end = today + timedelta(days=max_days)

    # Create order (temporary values first)
    order = Order.objects.create(
        user=cart.user,
        address_text=address_text,
        promo_code=promo_code or "",
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
        total_weight_kg=Decimal("0.000"),
        shipping_method=shipping_method,
        shipping_fee=shipping_fee,
        delivery_start=delivery_start,
        delivery_end=delivery_end,
        status="created",
        payment_status="pending",
    )

    # Create Order Items
    for item in cart.items.select_related("variant"):
        status = get_cart_item_status(item)

        if status != CartItemStatus.VALID:
            raise ValidationError(
                f"{item.product_name} is no longer available."
            )

        unit_price = round_money(item.unit_price)
        line_total = round_money(unit_price * item.quantity)

        OrderItem.objects.create(
            order=order,
            product_name=item.product_name,
            color=item.color,
            size=item.size,
            quantity=item.quantity,
            weight_kg=item.weight_kg,
            unit_price=unit_price,
            total_price=line_total,
            variant_id=item.variant.id,
        )

        subtotal += line_total
        total_weight += item.weight_kg * item.quantity

    subtotal = round_money(subtotal)

    # 🚀 Final total calculation
    total_amount = subtotal + shipping_fee
    total_amount = round_money(total_amount)

    # 🔒 Final lock
    order.subtotal = subtotal
    order.total_amount = total_amount
    order.total_weight_kg = total_weight

    order.save(update_fields=[
        "subtotal",
        "total_amount",
        "total_weight_kg"
    ])

    # 🧹 Clear cart AFTER order is safely created
    cart.items.all().delete()

    return order


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
