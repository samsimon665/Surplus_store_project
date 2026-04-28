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

# For CELERY REFUND-EMAIL
from apps.orders.tasks import send_refund_email


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

    payload_data = event.get("payload", {})

    # -------------------------------------------------
    # 3️⃣ Handle payment.captured
    # -------------------------------------------------
    if event_type == "payment.captured":

        payment_entity = payload_data.get("payment", {}).get("entity", {})

        razorpay_payment_id = payment_entity.get("id")
        razorpay_order_id = payment_entity.get("order_id")

        if not razorpay_order_id:
            print("Webhook: Missing order_id in payment")
            return HttpResponse(status=200)

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

            order.status = "processing"
            order.payment_status = "paid"

            order.razorpay_payment_id = razorpay_payment_id

            order.save()

            # Inventory update
            for item in order.items.all():
                try:
                    variant = ProductVariant.objects.select_for_update().get(
                        id=item.variant_id
                    )
                except ProductVariant.DoesNotExist:
                    continue

                if variant.stock >= item.quantity:
                    variant.stock -= item.quantity
                    variant.save()

            # Clear cart
            cart = Cart.objects.filter(user=order.user).first()
            if cart:
                cart.items.all().delete()

            print(f"Webhook: Order {order.uuid} marked as PAID")

    # -------------------------------------------------
    # 4️⃣ Handle payment.failed
    # -------------------------------------------------
    elif event_type == "payment.failed":

        payment_entity = payload_data.get("payment", {}).get("entity", {})
        razorpay_order_id = payment_entity.get("order_id")

        if not razorpay_order_id:
            return HttpResponse(status=200)

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
    # 5️⃣ Handle refund.processed
    # -------------------------------------------------
    elif event_type == "refund.processed":

        print("Webhook: Refund received from Razorpay")

        refund_entity = payload_data.get("refund", {}).get("entity", {})

        razorpay_payment_id = refund_entity.get("payment_id")
        razorpay_refund_id = refund_entity.get("id")

        if not razorpay_payment_id:
            print("Webhook: Missing payment_id in refund")
            return HttpResponse(status=200)

        # ✅ SAFE lookup via Payment
        payment = Payment.objects.filter(
            razorpay_payment_id=razorpay_payment_id
        ).select_related("order").first()

        if not payment:
            print("Webhook: Payment not found for refund")
            return HttpResponse(status=200)

        order = payment.order

        # ✅ Strong duplicate protection
        if order.razorpay_refund_id == razorpay_refund_id:
            print("Webhook: Refund already recorded")
            return HttpResponse(status=200)

        order.razorpay_refund_id = razorpay_refund_id
        order.refund_status = "processed"
        order.save()

        print(f"Webhook: Refund SUCCESS for order {order.uuid}")

        # CELERY REFUND EMAIL
        send_refund_email.delay(order.id)

    # -------------------------------------------------
    # 6️⃣ Handle refund.failed
    # -------------------------------------------------
    elif event_type == "refund.failed":

        print("Webhook: Refund FAILED event received")

        refund_entity = payload_data.get("refund", {}).get("entity", {})

        razorpay_payment_id = refund_entity.get("payment_id")

        if not razorpay_payment_id:
            return HttpResponse(status=200)

        payment = Payment.objects.filter(
            razorpay_payment_id=razorpay_payment_id
        ).select_related("order").first()

        if not payment:
            return HttpResponse(status=200)

        order = payment.order

        order.refund_status = "failed"
        order.save()

        print(f"Webhook: Refund FAILED for order {order.uuid}")

    # -------------------------------------------------
    # FINAL RESPONSE
    # -------------------------------------------------
    return HttpResponse(status=200)
