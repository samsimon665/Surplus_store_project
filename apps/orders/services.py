from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.cart.services import can_proceed_to_checkout
from apps.orders.models import Order, OrderItem
from apps.cart.models import Cart
from apps.cart.services import get_cart_item_status, CartItemStatus
from apps.cart.services import round_money


@transaction.atomic
def create_order_from_cart(cart, address_text, promo_code=None):
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

    order = Order.objects.create(
        user=cart.user,
        address_text=address_text,
        promo_code=promo_code or "",
        subtotal=Decimal("0.00"),        # temp
        discount_amount=Decimal("0.00"),  # promo later
        total_amount=Decimal("0.00"),    # temp
        total_weight_kg=Decimal("0.000"),
        status="created",
        payment_status="pending",
    )

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

    # 🔒 Final lock
    order.subtotal = subtotal
    order.total_amount = subtotal  # promo comes later
    order.total_weight_kg = total_weight
    order.save(update_fields=[
        "subtotal",
        "total_amount",
        "total_weight_kg"
    ])

    # 🧹 Clear cart AFTER order is created
    cart.items.all().delete()

    return order
