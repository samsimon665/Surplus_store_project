from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.db import transaction
from .services import create_order_from_checkout
from apps.cart.models import Cart


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

    address = get_object_or_404(request.user.addresses, id=address_id)

    # Snapshot address
    address_text = f"""
    {address.full_name}
    {address.address_line_1}
    {address.address_line_2 or ''}
    {address.city}, {address.state} - {address.pincode}
    {address.country}
    """

    # 🔥 CREATE ORDER
    order = create_order_from_checkout(
        request=request,
        cart=cart,
        shipping_method=shipping_method,
        address_text=address_text,
    )

    # Clear cart AFTER order created
    cart.items.all().delete()
    request.session.pop("applied_promo", None)

    return redirect("orders:payment_page", uuid=order.uuid)
