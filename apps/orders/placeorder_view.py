from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from apps.cart.models import Cart
from .services import create_order_from_checkout


@login_required(login_url="accounts:login")
@require_POST
@transaction.atomic
def place_order(request):

    # -------------------------------------------------
    # 1️⃣ Load Cart
    # -------------------------------------------------
    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart:cart")

    # -------------------------------------------------
    # 2️⃣ Get Shipping + Address
    # -------------------------------------------------
    shipping_method = request.POST.get("shipping_method", "standard")
    address_id = request.POST.get("selected_address")

    if not address_id:
        messages.error(request, "Please select delivery address.")
        return redirect("orders:start_checkout")

    address = get_object_or_404(
        request.user.addresses,
        id=address_id
    )

    # -------------------------------------------------
    # 3️⃣ Create Address Snapshot
    # -------------------------------------------------
    address_text = f"""
{address.full_name}
{address.address_line_1}
{address.address_line_2 or ""}
{address.city}, {address.state} - {address.pincode}
{address.country}
"""

    # -------------------------------------------------
    # 4️⃣ Create Order
    # -------------------------------------------------
    try:

        order = create_order_from_checkout(
            request=request,
            cart=cart,
            shipping_method=shipping_method,
            address_text=address_text,
        )

    except Exception as e:

        messages.error(request, str(e))
        return redirect("orders:start_checkout")

    # -------------------------------------------------
    # 5️⃣ Redirect to Payment Page (Next Step)
    # -------------------------------------------------
    return redirect(
        "orders:payment_page",
        uuid=order.uuid
    )
