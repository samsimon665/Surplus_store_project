from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid

User = settings.AUTH_USER_MODEL


class Order(models.Model):

    ORDER_STATUS_CHOICES = (
        ("created", "Created"),
        ("pending_payment", "Pending Payment"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
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
        default="created"
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

    promo_code = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"
