from .models import Product
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ProductCategory,
    SubCategory,
    Product,
    ProductVariant,
    ProductImage,
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
        "created_at",
        "image_preview",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )

    readonly_fields = (
        "image_preview",
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px; height:50px; object-fit:cover; border-radius:4px;" />',
                obj.image.url
            )
        return "—"

    image_preview.short_description = "Image"


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "slug",
        "price_per_kg",
        "is_active",
        "created_at",
        "image_preview",
    )

    list_filter = (
        "category",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )

    readonly_fields = (
        "image_preview",
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px; height:50px; object-fit:cover; border-radius:4px;" />',
                obj.image.url
            )
        return "—"

    image_preview.short_description = "Image"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "id",
        "subcategory",
        "is_active",
        "created_at",
        "image_preview",   # new column
    )

    list_filter = (
        "subcategory",
        "is_active",
        "created_at",
    )

    search_fields = ("name",)
    ordering = ("name",)

    readonly_fields = ("image_preview",)  # optional, for detail view

    def image_preview(self, obj):
        if getattr(obj, "main_image", None):          # use your actual field name
            return format_html(
                '<img src="{}" style="width:50px; height:50px; '
                'object-fit:cover; border-radius:4px;" />',
                obj.main_image.url,                   # same field here
            )
        return "—"

    image_preview.short_description = "Image"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "color",
        "size",
        "weight_kg",
        "stock",
        "is_active",
        "created_at",
    )

    list_filter = (
        "product",
        "is_active",
        "created_at",
    )

    search_fields = (
        "product__name",
        "color",
        "size",
    )

    ordering = (
        "-created_at",
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "is_primary",
        "created_at",
        "image_preview",
    )

    list_filter = (
        "is_primary",
        "created_at",
    )

    ordering = (
        "created_at",
    )

    readonly_fields = (
        "image_preview",
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px; height:50px; object-fit:cover; border-radius:4px;" />',
                obj.image.url
            )
        return "—"

    image_preview.short_description = "Image"
