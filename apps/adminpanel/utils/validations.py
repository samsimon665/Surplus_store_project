from apps.catalog.models import ProductVariant
import re
from django import forms


TOP_SIZES = {"XS", "S", "M", "L", "XL", "XXL"}
WAIST_SIZES = {"28", "30", "32", "34", "36"}


def validate_name(
    value,
    *,
    field_label="Name",
    min_length=3,
    max_length=100,
):
    value = value.strip()

    if not value:
        raise forms.ValidationError(f"{field_label} is required.")

    if len(value) < min_length:
        raise forms.ValidationError(
            f"{field_label} must be at least {min_length} characters long."
        )

    if len(value) > max_length:
        raise forms.ValidationError(
            f"{field_label} cannot exceed {max_length} characters."
        )

    if not re.search(r"[A-Za-z]", value):
        raise forms.ValidationError(
            f"{field_label} must contain at least one letter."
        )

    if re.fullmatch(r"[^A-Za-z0-9\s]+", value):
        raise forms.ValidationError(
            f"{field_label} cannot contain only special characters."
        )

    return value


def validate_description(value, *, max_length=500):
    value = value.strip()

    if not value:
        return value

    if not re.search(r"[A-Za-z]", value):
        raise forms.ValidationError(
            "Description must contain letters (not only numbers or symbols)."
        )

    if re.fullmatch(r"[^A-Za-z0-9\s]+", value):
        raise forms.ValidationError(
            "Description cannot contain only special characters."
        )

    if value.isdigit():
        raise forms.ValidationError(
            "Description cannot contain only numbers."
        )

    if len(value) > max_length:
        raise forms.ValidationError(
            f"Description cannot exceed {max_length} characters."
        )

    return value


def validate_image(image, *, max_size_mb=10):
    # Editing without changing image
    if not image:
        return image

    # Existing ImageFieldFile from DB
    if hasattr(image, "instance"):
        return image

    valid_mime_types = ["image/jpeg", "image/png", "image/webp"]
    if image.content_type not in valid_mime_types:
        raise forms.ValidationError(
            "Only JPG, PNG, and WEBP images are allowed."
        )

    if image.size > max_size_mb * 1024 * 1024:
        raise forms.ValidationError(
            f"Image size must not exceed {max_size_mb} MB."
        )

    return image
   

def validate_variant_data(
    *,
    product,
    color,
    sizes,
    weights,
    stocks,
    images,
):
    """
    Backend validation for Variant creation.
    One color can be created ONLY ONCE per product.
    """

    # ---------- COLOR ----------
    if not color:
        raise forms.ValidationError("Color is required.")

    color = color.strip()

    # 🚨 HARD BUSINESS RULE (THIS IS THE FIX)
    if ProductVariant.objects.filter(
        product=product,
        color__iexact=color
    ).exists():
        raise forms.ValidationError(
            f"A variant with color '{color}' already exists for this product. "
            "Edit the existing color instead of creating it again."
        )

    # ---------- SIZES ----------
    if not sizes:
        raise forms.ValidationError("At least one size must be selected.")

        # ---------- IMAGES ----------
    if not images or len(images) < 2:
        raise forms.ValidationError(
            "At least 2 images are required for a variant."
        )

    if len(images) > 4:
        raise forms.ValidationError(
            "You can upload a maximum of 4 images."
        )

    # ---------- SIZE TYPE ENFORCEMENT ----------
    if product.size_type == "TOP":
        invalid_sizes = set(sizes) - TOP_SIZES
        if invalid_sizes:
            raise forms.ValidationError(
                "Invalid size selected for this product. "
                "Allowed sizes: XS, S, M, L, XL, XXL."
            )

    if product.size_type == "WAIST":
        invalid_sizes = set(sizes) - WAIST_SIZES
        if invalid_sizes:
            raise forms.ValidationError(
                "Invalid size selected for this product. "
                "Allowed sizes: 28, 30, 32, 34, 36."
            )



    # ---------- SIZE DATA ----------
    for size in sizes:
        weight = weights.get(size)
        stock = stocks.get(size)

        if weight in (None, ""):
            raise forms.ValidationError(
                f"Weight is required for size {size}."
            )

        try:
            weight = float(weight)
        except ValueError:
            raise forms.ValidationError(
                f"Weight must be a number for size {size}."
            )

        if weight <= 0:
            raise forms.ValidationError(
                f"Weight must be greater than 0 for size {size}."
            )

        if stock in (None, ""):
            raise forms.ValidationError(
                f"Stock is required for size {size}."
            )

        try:
            stock = int(stock)
        except ValueError:
            raise forms.ValidationError(
                f"Stock must be an integer for size {size}."
            )

        if stock < 1:
            raise forms.ValidationError(
                f"Stock must be at least 1 for size {size}."
            )
        
        
def validate_variant_images_edit(
    *,
    existing_count,
    deleted_ids,
    uploaded_images,
    min_images=2,
    max_images=4,
):
    deleted_count = len(deleted_ids)
    uploaded_count = len(uploaded_images)

    final_count = existing_count - deleted_count + uploaded_count

    if final_count < min_images:
        raise forms.ValidationError(
            f"At least {min_images} images are required for a variant."
        )

    if final_count > max_images:
        raise forms.ValidationError(
            f"You can have a maximum of {max_images} images per variant."
        )
