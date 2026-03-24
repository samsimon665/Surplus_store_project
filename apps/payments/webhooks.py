import json
import hmac
import hashlib

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from apps.payments.models import Payment
from apps.orders.models import Order

from apps.cart.models import Cart

from apps.catalog.models import ProductVariant


@csrf_exempt
def razorpay_webhook(request):

    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body
    received_signature = request.headers.get("X-Razorpay-Signature")

    secret = settings.RAZORPAY_WEBHOOK_SECRET

    # -------------------------------------------------
    # 1️⃣ Verify webhook signature
    # -------------------------------------------------
    generated_signature = hmac.new(
        bytes(secret, "utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(generated_signature, received_signature):
        print("Webhook signature verification failed")
        return HttpResponse(status=400)

    print("Webhook verified successfully")

    # -------------------------------------------------
    # 2️⃣ Parse event
    # -------------------------------------------------
    event = json.loads(payload)

    event_type = event.get("event")
    print("Webhook event:", event_type)

    # Razorpay payment data
    payment_entity = event["payload"]["payment"]["entity"]

    razorpay_payment_id = payment_entity["id"]
    razorpay_order_id = payment_entity["order_id"]

    # -------------------------------------------------
    # 3️⃣ Handle payment.captured
    # -------------------------------------------------
    if event_type == "payment.captured":

        try:
            payment = Payment.objects.select_related("order").get(
                razorpay_order_id=razorpay_order_id
            )
        except Payment.DoesNotExist:
            print("Webhook: Payment record not found")
            return HttpResponse(status=200)

        order = payment.order

        # Prevent duplicate processing
        if payment.status == "success":
            print("Webhook: payment already processed")
            return HttpResponse(status=200)

        with transaction.atomic():

            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = "success"
            payment.save()

            order.status = "paid"
            order.payment_status = "success"
            order.save()

            # -------------------------------------------------
            # Deduct inventory (safe deduction with DB lock)
            # -------------------------------------------------
            for item in order.items.all():

                try:
                    variant = ProductVariant.objects.select_for_update().get(
                        id=item.variant_id
                    )

                except ProductVariant.DoesNotExist:
                    print(f"Webhook: Variant {item.variant_id} not found")
                    continue

                # Prevent negative stock
                if variant.stock < item.quantity:
                    print(
                        f"Webhook: Stock already insufficient for variant {variant.id}"
                    )
                    continue

                variant.stock -= item.quantity
                variant.save()

            # -------------------------------------------------
            # Clear user's cart
            # -------------------------------------------------
            cart = Cart.objects.filter(user=order.user).first()

            if cart:
                cart.items.all().delete()

            print(
                f"Webhook: Order {order.uuid} marked as PAID, inventory updated, and cart cleared")

    # -------------------------------------------------
    # 4️⃣ Handle payment.failed
    # -------------------------------------------------
    elif event_type == "payment.failed":

        try:
            payment = Payment.objects.get(
                razorpay_order_id=razorpay_order_id
            )
        except Payment.DoesNotExist:
            print("Webhook: Failed payment record not found")
            return HttpResponse(status=200)

        if payment.status != "success":

            payment.status = "failed"
            payment.save()

            print(f"Webhook: Payment failed for order {payment.order.uuid}")

    # -------------------------------------------------
    # 5️⃣ Return success to Razorpay
    # -------------------------------------------------
    return HttpResponse(status=200)
