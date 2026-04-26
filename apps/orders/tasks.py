from celery import shared_task
import razorpay
from django.conf import settings
from .models import Order


@shared_task(bind=True, max_retries=3)
def process_refund(self, order_id):

    order = None

    try:
        order = Order.objects.get(id=order_id)

        print("------ REFUND DEBUG START ------")
        print("ORDER ID:", order.id)
        print("PAYMENT STATUS:", order.payment_status)
        print("REFUND STATUS:", order.refund_status)
        print("RAZORPAY PAYMENT ID:", order.razorpay_payment_id)

        # ✅ Payment must be completed
        if order.payment_status not in ["paid", "success"]:
            print("BLOCKED: Payment not completed")
            return

        # ✅ Prevent duplicate refund
        if order.razorpay_refund_id:
            print("BLOCKED: Already refunded")
            return

        # ✅ Only process initiated/failed
        if order.refund_status not in ["initiated", "failed"]:
            print("BLOCKED: Invalid refund status")
            return

        # ❌ No payment id → cannot refund
        if not order.razorpay_payment_id:
            print("ERROR: Missing Razorpay payment ID")
            order.refund_status = "failed"
            order.save()
            return

        print("Calling Razorpay refund API...")

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        refund = client.payment.refund(
            order.razorpay_payment_id,
            {
                "amount": int(order.total_amount * 100)
            }
        )

        print("Refund response:", refund)

        # ❌ DO NOT update DB here
        # Webhook will handle:
        # - razorpay_refund_id
        # - refund_status

        print("REFUND INITIATED (waiting for webhook)")

    except Exception as e:
        print("Refund error:", str(e))

        if order:
            order.refund_status = "failed"
            order.save()

        raise self.retry(exc=e, countdown=10)
