from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, Address, PhoneOTP


from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        # "is_staff",
        "is_superuser",
        # "last_login",
        # "date_joined",
    )


# Unregister default admin
admin.site.unregister(User)

# Register customized admin
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'phone',
        'phone_verified',
        'gender',
        'dob',
        'completion_percentage',
        'profile_pic_preview',
    )

    list_filter = ('gender',)
    search_fields = ('user__username', 'user__email', 'phone')

    def profile_pic_preview(self, obj):
        if obj.profile_pic:
            return format_html(
                '<img src="{}" width="40" height="40" style="object-fit:cover; border-radius:6px;" />',
                obj.profile_pic.url
            )
        return "—"

    profile_pic_preview.short_description = "Profile Pic"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "full_name",
        "city",
        "district",
        "state",
        "pincode",
        "is_default",
        "created_at",
    )

    list_filter = (
        "is_default",
        "state",
        "city",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "full_name",
        "city",
        "state",
        "pincode",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)


    fieldsets = (
        ("User Info", {
            "fields": ("user", "full_name")
        }),
        ("Address Details", {
            "fields": (
                "address_line_1",
                "address_line_2",
                "landmark",
                "city",
                "district",
                "state",
                "pincode",
                "country",
            )
        }),
        ("Settings", {
            "fields": ("is_default",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "created_at", "expires_at", "attempts")
