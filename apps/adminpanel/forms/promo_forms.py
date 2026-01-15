from django import forms
from apps.promotions.models import PromoCode


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
            "usage_limit_per_user",
            "valid_from",
            "valid_to",
            "is_active",
        ]

    def clean_code(self):
        return self.cleaned_data["code"].upper()

    def clean_discount_value(self):
        return int(self.cleaned_data["discount_value"] * 100)

    def clean_minimum_cart_value(self):
        return int(self.cleaned_data["minimum_cart_value"] * 100)

    def clean_maximum_discount_amount(self):
        value = self.cleaned_data.get("maximum_discount_amount")
        return int(value * 100) if value else None
