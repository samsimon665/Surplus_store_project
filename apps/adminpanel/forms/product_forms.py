from django import forms
from django.forms import inlineformset_factory


from apps.catalog.models import (
    Product, ProductCategory, SubCategory, ProductImage,)

from apps.adminpanel.utils.validations import (
    validate_name, validate_description,)


class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.filter(is_active=True),
        required=True,
        empty_label="Select Category",
        widget=forms.Select(attrs={
            "class": "block w-full rounded-lg border-0 py-2.5 pl-3 pr-10 text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-slate-800/50 sm:text-sm sm:leading-6 appearance-none"
        })
    )

    class Meta:
        model = Product
        fields = [
            "category",
            "subcategory",
            "name",
            "description",
            "price_per_kg",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "block w-full rounded-lg border-0 py-2.5 text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-slate-800/50 sm:text-sm sm:leading-6",
                "placeholder": "e.g. Vintage Denim Jacket",
            }),
            "subcategory": forms.Select(attrs={
                "class": "block w-full rounded-lg border-0 py-2.5 pl-3 pr-10 text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-slate-800/50 sm:text-sm sm:leading-6 appearance-none"
            }),
            "price_per_kg": forms.NumberInput(attrs={
                "class": "block w-full rounded-lg border-0 py-2.5 pl-8 pr-14 text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-slate-800/50 sm:text-sm sm:leading-6",
                "step": "0.01",
            }),
            "description": forms.Textarea(attrs={
                "class": "block w-full rounded-lg border-0 py-2.5 text-slate-900 dark:text-white shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-primary dark:bg-slate-800/50 sm:text-sm sm:leading-6",
                "rows": 4,
                "placeholder": "Detailed information about the batch, condition, and origin...",
            }),
            "description": forms.Textarea(attrs={
                "class": (
                    "block w-full rounded-lg border-0 py-2.5 "
                    "text-slate-900 dark:text-white "
                    "shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 "
                    "placeholder:text-slate-400 "
                    "focus:ring-2 focus:ring-inset focus:ring-primary "
                    "dark:bg-slate-800/50 sm:text-sm sm:leading-6"
                ),
                "placeholder": "Detailed information about the batch, condition, and origin...",
                "rows": 3,
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "sr-only peer",
                "id": "toggleA",
            })


        }

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


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={
                "class": "hidden",
            })
        }


    def clean_image(self):
        image = self.cleaned_data.get("image")
        return image


ProductImageFormSet = inlineformset_factory(
    parent_model=Product,
    model=ProductImage,
    form=ProductImageForm,
    extra=3,          # show 3 image fields initially
    can_delete=True,  # allow removing images on edit
)
