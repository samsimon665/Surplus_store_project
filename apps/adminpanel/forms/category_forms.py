from django import forms
from apps.catalog.models import ProductCategory
from django.utils.text import slugify


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = [
            "name",
            "description",
            "image",
            "is_active",
        ]
