from django.contrib import admin

from .models import PromoCode

from django.utils import timezone


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "display_discount_value",
        "display_minimum_cart_value",
        "display_max_discount_amount",
        "usage_limit_total",
        "usage_limit_per_user",
        "valid_from",
        "valid_to",
        "is_active",
        "is_currently_valid",
        "created_at",
    )

    list_filter = (
        "discount_type",
        "is_active",
        "valid_from",
        "valid_to",
        "created_at",
    )

    search_fields = ("code",)

    readonly_fields = ("created_at", "updated_at")

    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Info", {
            "fields": ("code", "discount_type", "is_active")
        }),
        ("Discount Rules", {
            "fields": (
                "discount_value",
                "minimum_cart_value",
                "maximum_discount_amount",
            )
        }),
        ("Usage Limits", {
            "fields": (
                "usage_limit_total",
                "usage_limit_per_user",
            )
        }),
        ("Validity Period", {
            "fields": ("valid_from", "valid_to")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    # -----------------------------
    # Custom display helpers
    # -----------------------------
    def display_discount_value(self, obj):
        if obj.discount_type == PromoCode.PERCENT:
            return f"{obj.discount_value}%"
        return f"₹{obj.discount_value / 100:.2f}"

    display_discount_value.short_description = "Discount"

    def display_minimum_cart_value(self, obj):
        return f"₹{obj.minimum_cart_value / 100:.2f}"

    display_minimum_cart_value.short_description = "Min Cart Value"

    def display_max_discount_amount(self, obj):
        if obj.maximum_discount_amount is None:
            return "—"
        return f"₹{obj.maximum_discount_amount / 100:.2f}"

    display_max_discount_amount.short_description = "Max Discount"

    def is_currently_valid(self, obj):
        return obj.get_status() == "active"

    is_currently_valid.boolean = True
    is_currently_valid.short_description = "Valid Now?"
