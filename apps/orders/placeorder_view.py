from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.cart.models import Cart
from .services import create_order_from_checkout


@login_required(login_url="accounts:login")
@require_POST
@transaction.atomic
def place_order(request):

    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        messages.error(request, "Cart is empty.")
        return redirect("cart:cart")

    shipping_method = request.POST.get("shipping_method", "standard")
    address_id = request.POST.get("selected_address")

    if not address_id:
        messages.error(request, "Please select delivery address.")
        return redirect("orders:start_checkout")

    address = get_object_or_404(
        request.user.addresses,
        id=address_id
    )

    # Snapshot address (LOCK TEXT)
    address_text = f"""
{address.full_name}
{address.address_line_1}
{address.address_line_2 or ''}
{address.city}, {address.state} - {address.pincode}
{address.country}
""".strip()

    try:
        order = create_order_from_checkout(
            request=request,
            cart=cart,
            shipping_method=shipping_method,
            address_text=address_text,
        )
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect("orders:start_checkout")

    return redirect("orders:payment_page", uuid=order.uuid)
