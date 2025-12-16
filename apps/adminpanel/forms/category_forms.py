from django import forms
from apps.catalog.models import ProductCategory
from django.utils.text import slugify
import re


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
            "image": forms.ClearableFileInput(attrs={
                "class": "absolute inset-0 cursor-pointer opacity-0"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "sr-only peer"
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()

        # Required
        if not name:
            raise forms.ValidationError("Category name is required.")

        # Length check
        if len(name) < 2:
            raise forms.ValidationError(
                "Category name must be at least 2 characters long.")

        if len(name) > 100:
            raise forms.ValidationError(
                "Category name cannot exceed 100 characters.")

        # Must contain at least one letter
        if not re.search(r"[A-Za-z]", name):
            raise forms.ValidationError(
                "Category name must contain at least one letter."
            )

        # Block only special characters
        if re.fullmatch(r"[^A-Za-z0-9\s]+", name):
            raise forms.ValidationError(
                "Category name cannot contain only special characters."
            )

        # Case-insensitive uniqueness
        qs = ProductCategory.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A category with this name already exists.")

        return name

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()

        if description:

            if not re.search(r"[A-Za-z]", description):
                raise forms.ValidationError(
                    "Description must contain letters (not only numbers or symbols).")

            if re.fullmatch(r"[^A-Za-z0-9\s]+", description):
                raise forms.ValidationError(
                    "Description cannot contain only special characters.")

            if description.isdigit():
                raise forms.ValidationError(
                    "Description cannot contain only numbers.")

            if len(description) > 500:
                raise forms.ValidationError(
                    "Description cannot exceed 500 characters."
                )

        return description

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            raise forms.ValidationError("Category image is required.")

        # Max size: 10 MB
        max_size = 10 * 1024 * 1024  # 10 MB
        if image.size > max_size:
            raise forms.ValidationError(
                "Image size must be less than or equal to 10 MB."
            )

        # Allowed formats
        valid_types = ["image/jpeg", "image/png", "image/webp"]
        if image.content_type not in valid_types:
            raise forms.ValidationError(
                "Only JPG, PNG, and WEBP images are allowed."
            )

        return image
