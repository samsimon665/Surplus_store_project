from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid

from django.db.models import Q

User = settings.AUTH_USER_MODEL


class Order(models.Model):

    ORDER_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    )


    # 🔹 Razorpay
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_refund_id = models.CharField(max_length=255, null=True, blank=True)

    # 🔹 Refund tracking
    REFUND_STATUS_CHOICES = (
        ("none", "None"),
        ("initiated", "Initiated"),
        ("processed", "Processed"),
        ("failed", "Failed"),
    )

    refund_status = models.CharField(
        max_length=20,
        choices=REFUND_STATUS_CHOICES,
        default="none"
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="orders"
    )

    # Snapshot address (DO NOT FK)
    address_text = models.TextField(
        help_text="Snapshot of delivery address at order time"
    )

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="pending"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    total_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=3
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Tax rate applied at order time (e.g., 12.00)"
    )


    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    promo_code = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    shipping_method = models.CharField(
        max_length=20,
        choices=(
            ("standard", "Standard"),
            ("express", "Express"),
        ),
        default="standard"
    )

    shipping_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    delivery_start = models.DateField(
        null=True,
        blank=True
    )

    delivery_end = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="pending_payment"),
                name="unique_pending_order_per_user"
            )
        ]

    def __str__(self):
        return f"Order {self.uuid} | {self.user}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product_name = models.CharField(max_length=255)
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=20)

    quantity = models.PositiveIntegerField()

    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=3
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    variant_id = models.IntegerField(
        help_text="Original variant ID for reference"
    )

    product_url = models.URLField(blank=True, null=True)
    
    image_url = models.URLField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"
