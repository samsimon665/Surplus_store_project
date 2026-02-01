from django.contrib import admin

from .models import Cart, CartItem, Wishlist, WishlistItem

# Register your models here.


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ( "user", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "cart",
        "product_name",
        "color",
        "size",
        "quantity",
        "unit_price",
        "created_at",
    )

    list_filter = ("created_at", "color", "size")
    search_fields = ("product_name",)  # SAFE
    readonly_fields = (
        "cart",
        "variant",
        "product_name",
        "color",
        "size",
        "weight_kg",
        "price_per_kg",
        "unit_price",
        "created_at",
    )

    ordering = ("-created_at",)


admin.site.register(Wishlist)
admin.site.register(WishlistItem)