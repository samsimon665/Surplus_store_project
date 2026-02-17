import re
from django.core.exceptions import ValidationError


def validate_full_name(value):
    value = value.strip()

    if len(value) < 3:
        raise ValidationError("Full name must be at least 3 characters long.")

    if not re.match(r"^[A-Za-z\s]+$", value):
        raise ValidationError(
            "Full name must contain only letters and spaces.")

    return value


def validate_pincode(value):
    value = value.strip()

    if not re.match(r"^\d{6}$", value):
        raise ValidationError("Enter a valid 6-digit pincode.")

    return value


def validate_city(value):
    value = value.strip()

    if not re.match(r"^[A-Za-z\s]+$", value):
        raise ValidationError("City must contain only letters.")

    return value


def validate_state(value):
    value = value.strip()

    if not re.match(r"^[A-Za-z\s]+$", value):
        raise ValidationError("State must contain only letters.")

    return value


def validate_district(value):
    value = value.strip()

    if not re.match(r"^[A-Za-z\s]+$", value):
        raise ValidationError("District must contain only letters.")

    return value
