from decimal import Decimal
from django import forms
from apps.promotions.models import PromoCode


from datetime import timezone as dt_timezone
from zoneinfo import ZoneInfo
from django.utils import timezone


IST = ZoneInfo("Asia/Kolkata")


class PromoCodeForm(forms.ModelForm):

    discount_value = forms.DecimalField(
        label="Discount Value (₹)",
        min_value=0,
        decimal_places=2,
        required=True,
    )

    minimum_cart_value = forms.DecimalField(
        label="Minimum Cart Value (₹)",
        min_value=0,
        decimal_places=2,
        required=True,
    )

    maximum_discount_amount = forms.DecimalField(
        label="Maximum Discount Amount (₹)",
        min_value=0,
        decimal_places=2,
        required=False,
    )

    class Meta:
        model = PromoCode
        fields = [
            "code",
            "discount_type",
            "discount_value",
            "minimum_cart_value",
            "maximum_discount_amount",
            "usage_limit_total",
            "valid_from",
            "valid_to",
            "is_active",
        ]

        input_formats = {
            "valid_from": ["%Y-%m-%dT%H:%M"],
            "valid_to": ["%Y-%m-%dT%H:%M"],
        }

    # ------------------------
    # Field-level cleaning
    # ------------------------

    def clean_code(self):
        return self.cleaned_data["code"].upper()

    # ❌ DO NOT CONVERT TO INT HERE
    def clean_discount_value(self):
        return self.cleaned_data["discount_value"]

    def clean_minimum_cart_value(self):
        return self.cleaned_data["minimum_cart_value"]

    def clean_maximum_discount_amount(self):
        return self.cleaned_data.get("maximum_discount_amount")

    def clean_valid_from(self):
        dt = self.cleaned_data.get("valid_from")
        if dt is None:
            return dt

        # User enters IST (naive datetime)
        ist_dt = dt.replace(tzinfo=IST)

        # Convert to UTC for DB
        return ist_dt.astimezone(dt_timezone.utc)

    def clean_valid_to(self):
        dt = self.cleaned_data.get("valid_to")
        if dt is None:
            return dt

        ist_dt = dt.replace(tzinfo=IST)
        return ist_dt.astimezone(dt_timezone.utc)

    # ------------------------
    # Cross-field validation
    # ------------------------

    def clean(self):
        cleaned_data = super().clean()

        discount_type = cleaned_data.get("discount_type")
        discount_value = cleaned_data.get("discount_value")
        max_discount = cleaned_data.get("maximum_discount_amount")

        usage_total = cleaned_data.get("usage_limit_total")

        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")

        # 1️⃣ Date validation
        if valid_from and valid_to and valid_to <= valid_from:
            raise forms.ValidationError(
                "Valid To date must be later than Valid From date."
            )

        # 2️⃣ Discount rules
        if discount_type == PromoCode.PERCENT:
            if discount_value > Decimal("100"):
                raise forms.ValidationError(
                    "Percentage discount cannot exceed 100%."
                )

            if not max_discount:
                raise forms.ValidationError(
                    "Maximum discount amount is required for percentage discounts."
                )

        elif discount_type == PromoCode.FLAT:
            if max_discount:
                raise forms.ValidationError(
                    "Maximum discount amount is not applicable for flat discounts."
                )

        # 3️⃣ BUSINESS RULE (ENFORCED, NOT OPTIONAL)
        # One promo → one use per user → ALWAYS
        cleaned_data["usage_limit_per_user"] = 1

        # 4️⃣ Usage total logic
        if usage_total == 0:
            # 0 means unlimited internally
            cleaned_data["usage_limit_total"] = None

        return cleaned_data
