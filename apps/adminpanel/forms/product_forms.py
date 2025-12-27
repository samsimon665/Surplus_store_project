from django import forms

from apps.catalog.models import (Product, ProductCategory, SubCategory,)

from apps.adminpanel.utils.validations import (
    validate_name, validate_description,)


class ProductForm(forms.ModelForm):
    # UI-only field (NOT saved in Product)
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.filter(is_active=True),
        required=True,
        empty_label="Select Category"
    )

    class Meta:
        model = Product
        fields = [
            "category",        # UI-only
            "subcategory",     # saved
            "name",
            "description",
            "price_per_kg",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initially, show NO subcategories
        self.fields["subcategory"].queryset = SubCategory.objects.none()

        # If editing existing product
        if self.instance.pk:
            self.fields["category"].initial = self.instance.subcategory.category
            self.fields["subcategory"].queryset = SubCategory.objects.filter(
                category=self.instance.subcategory.category
            )

        # If category selected (POST request)
        elif "category" in self.data:
            try:
                category_id = int(self.data.get("category"))
                self.fields["subcategory"].queryset = SubCategory.objects.filter(
                    category_id=category_id
                )
            except (ValueError, TypeError):
                pass

    def clean_name(self):
        return validate_name(
            self.cleaned_data.get("name", ""),
            field_label="Product name"
        )

    def clean_description(self):
        return validate_description(
            self.cleaned_data.get("description", "")
        )

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        subcategory = cleaned_data.get("subcategory")

        if not name or not subcategory:
            return cleaned_data

        qs = Product.objects.filter(
            name__iexact=name,
            subcategory=subcategory
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A product with this name already exists in the selected subcategory."
            )

        return cleaned_data
