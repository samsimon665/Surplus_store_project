from django import forms
from apps.catalog.models import SubCategory
from apps.adminpanel.utils.validations import (
    validate_name,
    validate_description,
    validate_image,
)


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = [
            "category",
            "name",
            "price_per_kg",
            "description",
            "image",
            "is_active",
        ]

        widgets = {
            "category": forms.Select(attrs={
                "class": "w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm"
            }),

            "name": forms.TextInput(attrs={
                "placeholder": "e.g. T-Shirts, Hoodies",
                "class": "w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm"
            }),

            "price_per_kg": forms.NumberInput(attrs={
                "class": "w-full rounded-lg border border-slate-300 py-2.5 text-sm pl-7 pr-12",
                "step": "0.01",
                "placeholder": "Price per KG (e.g. 1100)",
            }),

            "description": forms.Textarea(attrs={
                "placeholder": "Short description for this subcategory",
                "rows": 4,
                "class": "w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm"
            }),

            "image": forms.FileInput(attrs={
                "class": "absolute inset-0 cursor-pointer opacity-0",
                "accept": "image/*"
            }),

            "is_active": forms.CheckboxInput(attrs={
                "class": "sr-only peer"
            }),
        }

    def clean_name(self):
        return validate_name(
            self.cleaned_data.get("name", ""),
            field_label="Subcategory name"
        )

    def clean_price_per_kg(self):
        price = self.cleaned_data.get("price_per_kg")

        if price is None or price <= 0:
            raise forms.ValidationError(
                "Price per KG must be greater than zero."
            )

        return price

    def clean_description(self):
        return validate_description(
            self.cleaned_data.get("description", "")
        )

    def clean_image(self):
        return validate_image(
            self.cleaned_data.get("image")
        )

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        category = cleaned_data.get("category")

        # If either field is missing, skip uniqueness check
        if not name or not category:
            return cleaned_data

        # Check uniqueness PER CATEGORY (case-insensitive)
        qs = SubCategory.objects.filter(
            name__iexact=name,
            category=category,
        )

        # Exclude current instance when editing
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "Sub Category with this name already exists in the selected category."
            )

        return cleaned_data
