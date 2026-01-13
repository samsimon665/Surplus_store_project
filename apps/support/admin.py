from django.contrib import admin
from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "section", "is_active", "display_order")
    list_filter = ("section", "is_active")
    search_fields = ("question",)
    ordering = ("section", "display_order")
