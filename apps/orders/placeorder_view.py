from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone

from datetime import timedelta

from apps.cart.models import Cart
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.services import create_razorpay_order

from .services import create_order_from_checkout

from .services import cart_matches_order



@login_required(login_url="accounts:login")
@require_POST
@transaction.atomic
def place_order(request):

    print("PLACE ORDER CALLED")

    # -------------------------------------------------
    # 1️⃣ Load Cart
    # -------------------------------------------------
    cart = Cart.objects.filter(user=request.user).first()

    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return JsonResponse({
            "success": False,
            "error": "Cart empty"
        })

    # -------------------------------------------------
    # 2️⃣ Check Pending Order
    # -------------------------------------------------

    pending_order = (
        Order.objects
        .select_for_update()
        .filter(
            user=request.user,
            status="pending_payment"
        )
        .first()
    )

    if pending_order:
        

        # -------------------------------
        # Expire order after 30 minutes
        # -------------------------------
        if pending_order.created_at < timezone.now() - timedelta(minutes=30):

            pending_order.status = "cancelled"
            pending_order.payment_status = "failed"
            pending_order.save()

            pending_order = None

        # -------------------------------
        # Detect cart changes
        # -------------------------------
        elif not cart_matches_order(cart, pending_order):

            pending_order.status = "cancelled"
            pending_order.payment_status = "failed"
            pending_order.save()

            pending_order = None

        # -------------------------------
        # Reuse order if still valid
        # -------------------------------
        if pending_order:


            # Reset order payment status for retry
            pending_order.payment_status = "pending"
            pending_order.save(update_fields=["payment_status"])

            Payment.objects.filter(order=pending_order).exclude(status="success").update(status="failed")

            # Create new Razorpay order
            razorpay_order = create_razorpay_order(pending_order)


            if not razorpay_order:

                return JsonResponse({
                    "success": False,
                    "error": "Payment gateway unavailable. Please retry."
                })

            # Create new payment attempt
            Payment.objects.create(
                order=pending_order,
                gateway="razorpay",
                razorpay_order_id=razorpay_order["id"],
                amount=pending_order.total_amount,
                status="created"
            )

            return JsonResponse({
                "success": True,
                "order_uuid": str(pending_order.uuid),
                "razorpay_order_id": razorpay_order["id"],
                "amount": int(pending_order.total_amount * 100),
                "key": settings.RAZORPAY_KEY_ID
            })                                                                                                                                      

    # -------------------------------------------------
    # 3️⃣ Get Shipping + Address
    # -------------------------------------------------
    shipping_method = request.POST.get("shipping_method", "standard")
    address_id = request.POST.get("selected_address")

    if not address_id:
        messages.error(request, "Please select delivery address.")
        return JsonResponse({
            "success": False,
            "error": "Address not selected"
        })

    address = get_object_or_404(
        request.user.addresses,
        id=address_id
    )

    # -------------------------------------------------
    # 4️⃣ Create Address Snapshot
    # -------------------------------------------------
    address_text = f"""
        {address.full_name}
        {address.address_line_1}
        {address.address_line_2 or ""}
        {address.city}, {address.state} - {address.pincode}
        {address.country}
    """

    # -------------------------------------------------
    # 5️⃣ Create Order
    # -------------------------------------------------

    try:

        order, razorpay_order = create_order_from_checkout(
            request=request,
            cart=cart,
            shipping_method=shipping_method,
            address_text=address_text,
        )


    except Exception as e:

        print("PLACE ORDER ERROR:", e)

        return JsonResponse({
            "success": False,
            "error": "Unable to create order. Please try again."
        })

    # -------------------------------------------------
    # 6️⃣ Return Razorpay Data
    # -------------------------------------------------
    return JsonResponse({
        "success": True,
        "order_uuid": str(order.uuid),
        "razorpay_order_id": razorpay_order["id"],
        "amount": int(order.total_amount * 100),
        "key": settings.RAZORPAY_KEY_ID
    })


@login_required(login_url="accounts:login")
def order_list(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "orders/order_list.html",
        {
            "orders": orders
        }
    )

@login_required(login_url="accounts:login")
def order_success(request, uuid):

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        uuid=uuid,
        user=request.user
    )

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order
        }
    )


@login_required(login_url="accounts:login")
def order_detail(request, uuid):

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        uuid=uuid,
        user=request.user
    )

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order
        }
    )
