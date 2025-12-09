from django.contrib import admin
from django.utils.html import format_html
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'phone',
        'gender',
        'email_verified',
        'is_blocked',
        'profile_pic_preview',
        
    )

    # Only allow editing "is_blocked"
    list_editable = ('is_blocked',)

    list_filter = ('email_verified', 'is_blocked', 'gender')
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
