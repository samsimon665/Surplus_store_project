from django import forms

from apps.catalog.models import (
    Product,
    ProductCategory,
    SubCategory,
)

from apps.adminpanel.utils.validations import (
    validate_name,
    validate_description,
)


class ProductForm(forms.ModelForm):
    """
    Product creation / edit form

    - category: UI-only (used to filter subcategory)
    - subcategory: saved to DB
    - size_type: controls variant size system (TOP / WAIST)
    """

    # 🔹 UI-only field (NOT in Product model)
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.filter(is_active=True),
        required=True,
        empty_label="Select Category",
        widget=forms.Select(attrs={
            "class": (
                "block w-full rounded-lg border-0 py-2.5 pl-3 pr-10 "
                "text-slate-900 dark:text-white "
                "shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 "
                "focus:ring-2 focus:ring-inset focus:ring-primary "
                "dark:bg-slate-800/50 sm:text-sm sm:leading-6 appearance-none"
            )
        })
    )

    class Meta:
        model = Product
        fields = [
            "category",        # UI-only
            "subcategory",
            "size_type",       # ✅ NEW (TOP / WAIST)
            "name",
            "description",
            "main_image",
            "is_active",
        ]
        widgets = {
            "subcategory": forms.Select(attrs={
                "class": (
                    "block w-full rounded-lg border-0 py-2.5 pl-3 pr-10 "
                    "text-slate-900 dark:text-white "
                    "shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 "
                    "focus:ring-2 focus:ring-inset focus:ring-primary "
                    "dark:bg-slate-800/50 sm:text-sm sm:leading-6 appearance-none"
                )
            }),
            "size_type": forms.Select(attrs={
                "class": (
                    "block w-full rounded-lg border-0 py-2.5 pl-3 pr-10 "
                    "text-slate-900 dark:text-white "
                    "shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 "
                    "focus:ring-2 focus:ring-inset focus:ring-primary "
                    "dark:bg-slate-800/50 sm:text-sm sm:leading-6 appearance-none"
                )
            }),
            "name": forms.TextInput(attrs={
                "class": (
                    "block w-full rounded-lg border-0 py-2.5 "
                    "text-slate-900 dark:text-white "
                    "shadow-sm ring-1 ring-inset ring-slate-300 dark:ring-slate-700 "
                    "placeholder:text-slate-400 "
                    "focus:ring-2 focus:ring-inset focus:ring-primary "
                    "dark:bg-slate-800/50 sm:text-sm sm:leading-6"
                ),
                "placeholder": "e.g. Polo T-Shirt",
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
                "rows": 3,
            }),
            "main_image": forms.ClearableFileInput(attrs={
                "class": "hidden",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "sr-only peer",
                "id": "toggleA",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔒 Subcategory always controlled manually
        self.fields["subcategory"].queryset = SubCategory.objects.none()

        # 🔴 POST data has first priority
        if "category" in self.data:
            try:
                category_id = int(self.data.get("category"))
                self.fields["subcategory"].queryset = SubCategory.objects.filter(
                    category_id=category_id
                )
            except (TypeError, ValueError):
                pass

        # 🟢 Edit mode fallback
        elif self.instance.pk:
            category = self.instance.subcategory.category
            self.fields["category"].initial = category
            self.fields["subcategory"].queryset = SubCategory.objects.filter(
                category=category
            )

    # =========================
    # VALIDATIONS
    # =========================

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
