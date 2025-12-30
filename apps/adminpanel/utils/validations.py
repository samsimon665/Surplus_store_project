import re
from django import forms


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
