from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile


# ✅ Custom User Admin (is_active locked)
class CustomUserAdmin(BaseUserAdmin):
    readonly_fields = ('is_active',)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ✅ Profile Admin (is_blocked locked)
class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ('is_blocked',)


admin.site.register(Profile, ProfileAdmin)
