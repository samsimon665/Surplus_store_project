from django.contrib import admin
from django.utils.html import format_html
from .models import Profile


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
        'gender',
        'email_verified',
        'profile_pic_preview',

    )

    list_filter = ('email_verified', 'gender')
    search_fields = ('user__username', 'user__email', 'phone')

    # Email should be READ-ONLY
    readonly_fields = ('email_verified',)

    def profile_pic_preview(self, obj):
        if obj.profile_pic:
            return format_html(
                '<img src="{}" width="40" height="40" style="object-fit:cover; border-radius:6px;" />',
                obj.profile_pic.url
            )
        return "—"

    profile_pic_preview.short_description = "Profile Pic"
