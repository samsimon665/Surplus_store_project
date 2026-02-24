from django.contrib import admin
from django.db.models import Count
from .models import PromoCode, PromoUsage
from django.utils import timezone


# ==========================================
# PromoUsage Admin
# ==========================================
@admin.register(PromoUsage)
class PromoUsageAdmin(admin.ModelAdmin):
    list_display = (
        "promo",
        "user",
        "order",
        "used_at",
    )

    list_filter = (
        "promo",
        "used_at",
    )

    search_fields = (
        "promo__code",
        "user__email",
        "user__username",
        "order__id",
    )

    readonly_fields = ("used_at",)

    ordering = ("-used_at",)


# ==========================================
# PromoCode Admin
# ==========================================
@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "discount_type",
        "display_discount_value",
        "display_minimum_cart_value",
        "display_max_discount_amount",
        "usage_limit_total",
        "display_used_count",
        "display_remaining",
        "display_usage_percent",
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
            "fields": ("usage_limit_total",)
        }),
        ("Validity Period", {
            "fields": ("valid_from", "valid_to")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    # ==========================================
    # Custom Display Helpers
    # ==========================================

    def display_discount_value(self, obj):
        if obj.discount_type == PromoCode.PERCENT:
            return f"{obj.discount_value}%"
        return f"₹{obj.discount_value / 100:.2f}"
    display_discount_value.short_description = "Discount"

    def display_minimum_cart_value(self, obj):
        return f"₹{obj.minimum_cart_value / 100:.2f}"
    display_minimum_cart_value.short_description = "Min Cart"

    def display_max_discount_amount(self, obj):
        if obj.maximum_discount_amount is None:
            return "—"
        return f"₹{obj.maximum_discount_amount / 100:.2f}"
    display_max_discount_amount.short_description = "Max Cap"

    # ---- Usage Derived from PromoUsage ----

    def display_used_count(self, obj):
        return obj.usages.count()
    display_used_count.short_description = "Used"

    def display_remaining(self, obj):
        if obj.usage_limit_total == 0:
            return "Unlimited"
        used = obj.usages.count()
        return max(obj.usage_limit_total - used, 0)
    display_remaining.short_description = "Remaining"

    def display_usage_percent(self, obj):
        if obj.usage_limit_total == 0:
            return "—"
        used = obj.usages.count()
        percent = (used / obj.usage_limit_total) * 100
        return f"{percent:.0f}%"
    display_usage_percent.short_description = "Usage %"

    def is_currently_valid(self, obj):
        return obj.get_status() == "active"
    is_currently_valid.boolean = True
    is_currently_valid.short_description = "Valid Now?"
