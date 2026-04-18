from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction

import razorpay

from apps.payments.models import Payment
from apps.orders.models import Order
from apps.cart.models import Cart


@login_required(login_url="accounts:login")
@require_POST
def verify_payment(request):

    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    razorpay_order_id = request.POST.get("razorpay_order_id")
    razorpay_signature = request.POST.get("razorpay_signature")

    # -------------------------------------------------
    # 1️⃣ Validate request data
    # -------------------------------------------------
    if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
        return JsonResponse(
            {"success": False, "error": "Missing payment data"},
            status=400
        )

    # -------------------------------------------------
    # 2️⃣ Verify Razorpay signature
    # -------------------------------------------------
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        client.utility.verify_payment_signature({
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_signature": razorpay_signature
        })

    except razorpay.errors.SignatureVerificationError:
        return JsonResponse(
            {"success": False, "error": "Signature verification failed"},
            status=400
        )

    # -------------------------------------------------
    # 3️⃣ Find payment attempt
    # -------------------------------------------------
    payment = Payment.objects.select_related("order").filter(
        razorpay_order_id=razorpay_order_id,
        order__user=request.user
    ).order_by("-created_at").first()


    if not payment:

        return JsonResponse(
            {"success": False, "error": "Payment record not found"},
            status=404
        )

    order = payment.order


    # -------------------------------------------------
    # 5️⃣ Atomic update
    # -------------------------------------------------
    # Prevent duplicate processing
    if payment.status == "success":
        return JsonResponse({
            "success": True,
            "redirect_url": f"/order/success/{order.uuid}/"
        })
    with transaction.atomic():

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = "success"
        payment.save()
        

        order.status = "processing"
        order.payment_status = "paid"
        order.razorpay_payment_id = razorpay_payment_id
        order.save()

        # -------------------------------------------------
        # 6️⃣ Clear cart after payment success
        # -------------------------------------------------
        cart = Cart.objects.filter(user=request.user).first()

        if cart:
            cart.items.all().delete()

        # -------------------------------------------------
        # 7️⃣ Remove promo from session
        # -------------------------------------------------
        request.session.pop("applied_promo", None)

    # -------------------------------------------------
    # 8️⃣ Return response
    # -------------------------------------------------
    return JsonResponse({
        "success": True,
        "redirect_url": f"/order/success/{order.uuid}/"
    })
