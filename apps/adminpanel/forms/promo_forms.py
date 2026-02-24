from decimal import Decimal
from django import forms
from apps.promotions.models import PromoCode
from datetime import timezone as dt_timezone
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


class PromoCodeForm(forms.ModelForm):

    discount_value = forms.DecimalField(
        label="Discount Value",
        min_value=Decimal("0.01"),
        decimal_places=2,
        required=True,
    )

    minimum_cart_value = forms.DecimalField(
        label="Minimum Cart Value",
        min_value=Decimal("0.00"),
        decimal_places=2,
        required=True,
    )

    maximum_discount_amount = forms.DecimalField(
        label="Maximum Discount Amount",
        min_value=Decimal("0.01"),
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
    # Field-Level Cleaning
    # ------------------------

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()

    def clean_valid_from(self):
        dt = self.cleaned_data.get("valid_from")
        if dt:
            ist_dt = dt.replace(tzinfo=IST)
            return ist_dt.astimezone(dt_timezone.utc)
        return dt

    def clean_valid_to(self):
        dt = self.cleaned_data.get("valid_to")
        if dt:
            ist_dt = dt.replace(tzinfo=IST)
            return ist_dt.astimezone(dt_timezone.utc)
        return dt

    # ------------------------
    # Cross-Field Validation
    # ------------------------

    def clean(self):
        cleaned_data = super().clean()

        discount_type = cleaned_data.get("discount_type")
        discount_value = cleaned_data.get("discount_value")
        max_discount = cleaned_data.get("maximum_discount_amount")
        usage_total = cleaned_data.get("usage_limit_total")
        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")

        # Date validation
        if valid_from and valid_to and valid_to <= valid_from:
            self.add_error(
                "valid_to", "Valid To must be later than Valid From.")

        # Percentage rules
        if discount_type == PromoCode.PERCENT and discount_value is not None:

            if discount_value > Decimal("25"):
                self.add_error(
                    "discount_value",
                    "Percentage discount cannot exceed 25%."
                )

            if max_discount is None:
                self.add_error(
                    "maximum_discount_amount",
                    "Maximum discount amount is required for percentage discounts."
                )

            elif max_discount > Decimal("500"):
                self.add_error(
                    "maximum_discount_amount",
                    "Maximum discount cap cannot exceed ₹500."
                )

        # Flat rules
        if discount_type == PromoCode.FLAT and discount_value is not None:

            if discount_value > Decimal("500"):
                self.add_error(
                    "discount_value",
                    "Flat discount cannot exceed ₹500."
                )

            if max_discount:
                self.add_error(
                    "maximum_discount_amount",
                    "Not applicable for flat discount."
                )

        # Usage limit rule
        if usage_total is not None:
            if usage_total < 1:
                self.add_error(
                    "usage_limit_total",
                    "Usage limit must be at least 1."
                )
            if usage_total > 100:
                self.add_error(
                    "usage_limit_total",
                    "Usage limit cannot exceed 100 users."
                )

        return cleaned_data
