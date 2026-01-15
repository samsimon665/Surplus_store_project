from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PromoCode(TimeStampedModel):
    PERCENT = "PERCENT"
    FLAT = "FLAT"

    DISCOUNT_TYPE_CHOICES = (
        (PERCENT, "Percent"),
        (FLAT, "Flat"),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
    )

    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
    )

    discount_value = models.PositiveIntegerField(
        help_text="Stored in paise"
    )

    minimum_cart_value = models.PositiveIntegerField(
        help_text="Stored in paise"
    )

    maximum_discount_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Stored in paise"
    )

    usage_limit_total = models.PositiveIntegerField()
    usage_limit_per_user = models.PositiveIntegerField()

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code


# class PromoUsage(TimeStampedModel):
#     promo_code = models.ForeignKey(
#         PromoCode,
#         on_delete=models.CASCADE,
#         related_name="usages",
#     )

#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="promo_usages",
#     )

#     order = models.OneToOneField(
#         "orders.Order",
#         on_delete=models.CASCADE,
#         related_name="promo_usage",
#     )

#     used_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ("promo_code", "order")
#         indexes = [
#             models.Index(fields=["promo_code", "user"]),
#         ]

#     def __str__(self):
#         return f"{self.promo_code.code} → {self.user_id}"
