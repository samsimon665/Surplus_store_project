from django import forms
from apps.catalog.models import ProductVariant


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = [
            "color",
            "size",
            "weight_kg",
            "stock",
            "is_active",
        ]
