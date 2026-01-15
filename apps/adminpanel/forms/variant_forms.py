from django import forms
from django.core.exceptions import ValidationError
from catalog.models import ProductVariant


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

    def __init__(self, *args, **kwargs):
        """
        Expect `product` to be passed from the view.
        """
        self.product = kwargs.pop("product", None)
        super().__init__(*args, **kwargs)

    def clean_color(self):
        color = self.cleaned_data.get("color")

        if not self.product:
            # Safety guard — form must know the product
            return color

        qs = ProductVariant.objects.filter(
            product=self.product,
            color__iexact=color.strip(),
        )

        # 🔒 EDIT SAFE: exclude current instance
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(
                "This color already exists for this product."
            )

        return color
