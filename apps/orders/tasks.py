from celery import shared_task
import razorpay
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction

from .models import Order
from .invoice_view import generate_invoice_pdf


# -------------------------------------------------
# 🔹 REFUND PROCESS TASK
# -------------------------------------------------
@shared_task(bind=True, max_retries=0)  # ❌ no retry for bad requests
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

        # ✅ Only valid states
        if order.refund_status not in ["initiated", "failed"]:
            print("BLOCKED: Invalid refund status")
            return

        # ❌ Missing payment id
        if not order.razorpay_payment_id:
            print("ERROR: Missing Razorpay payment ID")
            order.refund_status = "failed"
            order.save()
            return

        amount = int(order.total_amount * 100)

        print("Refund amount:", amount)
        print("Calling Razorpay refund API...")

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        refund = client.payment.refund(
            order.razorpay_payment_id,
            {
                "amount": amount
            }
        )

        print("Refund response:", refund)

        # ❌ DO NOT update DB here
        # webhook will update:
        # - refund_status
        # - razorpay_refund_id

        print("REFUND INITIATED (waiting for webhook)")

    except Exception as e:
        print("❌ REFUND ERROR FULL:", repr(e))

        if order:
            order.refund_status = "failed"
            order.save()

        print("❌ FINAL FAILURE — NOT RETRYING")


# -------------------------------------------------
# 🔹 REFUND EMAIL TASK (WITH PDF)
# -------------------------------------------------
@shared_task(bind=True, max_retries=3)
def send_refund_email(self, order_id):
    try:
        order = Order.objects.select_related("user").get(id=order_id)

        pdf_bytes = generate_invoice_pdf(order)

        subject = "Refund Processed Successfully"

        message = f"""
Hi {order.user.username},

Your refund has been successfully processed.

Order ID: {order.uuid}
Amount: ₹{order.total_amount}

The amount will reflect in your account within 5–7 business days.

Please find your invoice attached.

Thank you,
Surplus Store
"""

        email = EmailMessage(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [order.user.email],
        )

        # ✅ Attach PDF
        if pdf_bytes:
            email.attach(
                f"invoice_{order.id}.pdf",
                pdf_bytes,
                "application/pdf"
            )
        else:
            print(
                f"[EMAIL WARNING] PDF generation failed for order {order.id}")

        email.send()

        print(f"[EMAIL SUCCESS] Refund email sent for order {order.id}")

    except Exception as e:
        print(f"[EMAIL ERROR] Order {order_id}: {repr(e)}")

        raise self.retry(exc=e, countdown=10)
