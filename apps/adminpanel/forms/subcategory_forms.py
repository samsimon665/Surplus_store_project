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

    def clean_description(self):
        return validate_description(
            self.cleaned_data.get("description", "")
        )

    def clean_image(self):
        return validate_image(
            self.cleaned_data.get("image")
        )
