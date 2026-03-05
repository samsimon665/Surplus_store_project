from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "gateway",
        "amount",
        "status",
        "razorpay_order_id",
        "created_at",
    )

    search_fields = (
        "order__uuid",
        "razorpay_order_id",
        "razorpay_payment_id",
    )

    list_filter = (
        "status",
        "gateway",
        "created_at",
    )
