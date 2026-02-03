from django import forms
from apps.catalog.models import ProductCategory
from apps.adminpanel.utils.validations import (
    validate_name,
    validate_description,
    validate_image,
)


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = [
            "name",
            "description",
            "image",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "e.g. Men, Women, Kids",
                "class": "w-full rounded-lg border border-slate-300 px-4 py-2.5 text-sm"
            }),
            "description": forms.Textarea(attrs={
                "placeholder": "Short description for this category",
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
        name = validate_name(
            self.cleaned_data.get("name", ""),
            field_label="Category name"
        )

        # Case-insensitive uniqueness (category-specific logic stays HERE)
        qs = ProductCategory.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A category with this name already exists."
            )

        return name

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
        image = cleaned_data.get("image")

        # IMAGE IS REQUIRED FOR BOTH CREATE & EDIT
        if not image:
            raise forms.ValidationError(
                "Category image is required. Please upload an image."
            )

        return cleaned_data
