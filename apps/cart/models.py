from django.db import models
from apps.catalog.models import ProductVariant

from decimal import Decimal

from django.conf import settings

User = settings.AUTH_USER_MODEL




class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart({self.user})"

    @property
    def subtotal(self):
        """
        Live subtotal:
        sum of (unit_price × quantity) for all cart items.
        Always correct. Never stored.
        """
        return sum(
            (item.unit_price * item.quantity)
            for item in self.items.all()
        ) or Decimal("0.00")

    @property
    def total(self):
        """
        Final payable amount.
        Currently same as subtotal.
        Keep separate for future:
        - shipping
        - tax
        - discounts
        """
        return self.subtotal



class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    # SKU / batch-based variant
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="cart_items"
    )

    # Quantity user wants
    quantity = models.PositiveIntegerField()

    # -------- SNAPSHOTS (PER UNIT) --------
    product_name = models.CharField(max_length=255)
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=50)

    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        help_text="Snapshot weight per unit in KG"
    )

    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    # -------------------------------------

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "variant")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product_name} ({self.size}) × {self.quantity}"
