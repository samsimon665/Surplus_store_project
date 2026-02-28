from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


alphanumeric_validator = RegexValidator(
    regex=r'^[A-Za-z0-9]+$',
    message="Promo code must contain only letters and numbers.",
)

class PromoCode(TimeStampedModel):
    PERCENT = "PERCENT"
    FLAT = "FLAT"

    DISCOUNT_TYPE_CHOICES = (
        (PERCENT, "Percent"),
        (FLAT, "Flat"),
    )

    code = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        validators=[alphanumeric_validator],
    )

    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
    )

    # Stored in paise for FLAT
    # Stored as integer percent for PERCENT (e.g., 25 means 25%)
    discount_value = models.PositiveIntegerField()

    # Only used for PERCENT type (stored in paise)
    maximum_discount_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # Stored in paise
    minimum_cart_value = models.PositiveIntegerField(default=0)

    
    usage_limit_total = models.PositiveIntegerField()

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    # -------------------------
    # Model-Level Validation
    # -------------------------
    def clean(self):

        # -------------------------
        # Promo Code validation
        # -------------------------
        if not self.code:
            raise ValidationError({"code": "Promo code is required."})

        code_length = len(self.code)

        if code_length < 5:
            raise ValidationError({
                "code": "Promo code must be at least 5 characters long."
            })

        if code_length > 15:
            raise ValidationError({
                "code": "Promo code cannot exceed 15 characters."
            })

        if self.code.isdigit():
            raise ValidationError({
                "code": "Promo code cannot contain only numbers."
            })

        # -------------------------
        # Date validation
        # -------------------------
        if not self.valid_from:
            raise ValidationError({"valid_from": "Valid from is required."})


        if not self.valid_to:
            raise ValidationError({"valid_to": "Valid to is required."})


        if self.valid_to <= self.valid_from:
            raise ValidationError({
                "valid_to": "Valid To must be later than Valid From."
            })
        if self.valid_to < timezone.now():
            raise ValidationError({
                "valid_to": "Valid To cannot be in the past."
            })

        # -------------------------
        # Discount must exist and be > 0
        # -------------------------
        if self.discount_value is None or self.discount_value <= 0:
            raise ValidationError({
                "discount_value": "Discount value must be greater than zero."
            })

        # -------------------------
        # Discount rules by type
        # -------------------------
        if self.discount_type == self.PERCENT:

            # Max 25%
            if self.discount_value > 25:
                raise ValidationError({
                    "discount_value": "Percentage discount cannot exceed 25%."
                })
            

            # Cap required
            if self.maximum_discount_amount is None:
                raise ValidationError({
                    "maximum_discount_amount":
                    "Maximum discount amount is required for percentage discounts."
                })

            # Cap must not exceed ₹500 (50000 paise)
            if self.maximum_discount_amount > 50000:
                raise ValidationError({
                    "maximum_discount_amount":
                    "Maximum discount cap cannot exceed ₹500."
                })

        elif self.discount_type == self.FLAT:

            # Flat discount stored in paise
            if self.discount_value > 50000:
                raise ValidationError({
                    "discount_value":
                    "Flat discount cannot exceed ₹500."
                })

            # Flat should not have cap
            if self.maximum_discount_amount is not None:
                raise ValidationError({
                    "maximum_discount_amount":
                    "Maximum discount amount should not be set for flat discounts."
                })
            
        # -------------------------
        # Minimum Cart Value Validation
        # -------------------------
        if self.minimum_cart_value is None:
            raise ValidationError({
                "minimum_cart_value": "Minimum cart value is required."
            })

        if self.minimum_cart_value < 50000:
            raise ValidationError({
                "minimum_cart_value":
                "Minimum cart value must be at least ₹500."
            })

        if self.minimum_cart_value > 250000:
            raise ValidationError({
                "minimum_cart_value":
                "Minimum cart value cannot exceed ₹2500."
            })

       # -------------------------
        # Usage limit validation
        # -------------------------
        if self.usage_limit_total is None:
            raise ValidationError({
                "usage_limit_total":
                "Usage limit is required."
            })

        if self.usage_limit_total < 1:
            raise ValidationError({
                "usage_limit_total":
                "Usage limit must be at least 1."
            })

        if self.usage_limit_total > 100:
            raise ValidationError({
                "usage_limit_total":
                "Usage limit cannot exceed 100 users."
            })
            
    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    # -------------------------
    # Status Helper
    # -------------------------
    def get_status(self):
        now = timezone.now()

        if not self.is_active:
            return "inactive"

        if now < self.valid_from:
            return "upcoming"

        if now > self.valid_to:
            return "expired"

        return "active"


class PromoUsage(models.Model):
    promo = models.ForeignKey(
        "promotions.PromoCode",
        on_delete=models.PROTECT,
        related_name="usages",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="promo_usages",
    )

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="promo_usage",
    )

    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["promo", "user"],
                name="unique_user_per_promo"
            )
        ]
        indexes = [
            models.Index(fields=["promo"]),
            models.Index(fields=["promo", "user"]),
        ]

    def __str__(self):
        return f"{self.promo.code} → {self.user_id}"
