from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Order, OrderItem

from apps.catalog.models import ProductVariant, ProductImage


# -------------------------------------------------------
# Order Item Inline (inside Order page)
# -------------------------------------------------------

class OrderItemInline(admin.TabularInline):

    model = OrderItem
    extra = 0

    can_delete = False
    show_change_link = False

    readonly_fields = (
        "product_name",
        "color",
        "size",
        "quantity",
        "weight_kg",
        "unit_price",
        "total_price",
        "variant_id",
        "created_at",
    )

    fields = (
        "product_name",
        "color",
        "size",
        "quantity",
        "unit_price",
        "total_price",
        "weight_kg",
        "variant_id",
    )

    def has_add_permission(self, request, obj=None):
        return False


# -------------------------------------------------------
# Order Admin
# -------------------------------------------------------

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "uuid",
        "status_badge",
        "payment_status_badge",
        "refund_status",            # ✅ ADD
        "razorpay_payment_id",
        "razorpay_refund_id",       # ✅ ADD
        "shipping_method",
        "subtotal",
        "discount_amount",
        "tax_amount",
        "shipping_fee",
        "total_amount",
        "promo_code",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "shipping_method",
        "created_at",
    )

    search_fields = (
        "uuid",
        "user__email",
        "user__username",
        "promo_code",
        "address_text",
    )

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    list_per_page = 25

    # prevents N+1 queries
    list_select_related = ("user",)

    readonly_fields = (
        "uuid",
        "user",
        "created_at",
        "updated_at",
        "subtotal",
        "total_amount",
        "tax_amount",
        "total_weight_kg",

        "razorpay_payment_id",     # ✅ ADD
        "razorpay_refund_id",      # ✅ ADD
    )

    fieldsets = (

        ("Order Info", {
            "fields": (
                "uuid",
                "user",
                "status",
                "payment_status",
                "refund_status",            # ✅ ADD
                "razorpay_payment_id",
                "razorpay_refund_id",       # ✅ ADD
                "created_at",
                "updated_at",
            )
        }),

        ("Delivery", {
            "fields": (
                "address_text",
                "shipping_method",
                "shipping_fee",
                "delivery_start",
                "delivery_end",
                "total_weight_kg",
            )
        }),

        ("Pricing", {
            "fields": (
                "subtotal",
                "promo_code",
                "discount_amount",
                "tax_rate",
                "tax_amount",
                "total_amount",
            )
        }),

    )

    inlines = [OrderItemInline]

    # ---------------------------------------------------
    # Status badge
    # ---------------------------------------------------

    @admin.display(description="Order Status")
    def status_badge(self, obj):

        colors = {
            "pending": "#f59e0b",
            "processing": "#3b82f6",
            "shipped": "#6366f1",
            "out_for_delivery": "#8b5cf6",
            "delivered": "#10b981",
            "cancelled": "#ef4444",
        }

        color = colors.get(obj.status, "#6b7280")

        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    # ---------------------------------------------------
    # Payment badge
    # ---------------------------------------------------

    @admin.display(description="Payment Status")
    def payment_status_badge(self, obj):

        colors = {
            "pending": "#f59e0b",
            "paid": "#10b981",
            "failed": "#ef4444",
        }

        color = colors.get(obj.payment_status, "#6b7280")

        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color,
            obj.get_payment_status_display(),
        )


# -------------------------------------------------------
# Order Item Admin
# -------------------------------------------------------

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "product_name",
        "image_preview",
        "color",
        "size",
        "quantity",
        "unit_price",
        "total_price",
        "weight_kg",
        "order_link",
        "created_at",
    )

    list_filter = (
        "color",
        "size",
    )

    search_fields = (
        "product_name",
        "order__uuid",
        "order__user__email",
        "variant_id",
    )

    ordering = ("-created_at",)

    list_per_page = 50

    readonly_fields = (
        "image_preview",
        "order",
        "variant_id",
        "created_at",
        "total_price",
    )

    fieldsets = (

        ("Item Details", {
            "fields": (
                "image_preview",
                "order",
                "product_name",
                "color",
                "size",
                "variant_id",
            )
        }),

        ("Quantity & Pricing", {
            "fields": (
                "quantity",
                "unit_price",
                "total_price",
                "weight_kg",
            )
        }),

        ("Meta", {
            "fields": (
                "created_at",
            )
        }),

    )

    # ---------------------------------------------------
    # Link to Order
    # ---------------------------------------------------

    @admin.display(description="Order")
    def order_link(self, obj):

        url = reverse(
            "admin:orders_order_change",
            args=[obj.order.pk]
        )

        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.order.uuid
        )
    
    @admin.display(description="Image")
    def image_preview(self, obj):

        try:
            variant = ProductVariant.objects.select_related(
                "product").get(id=obj.variant_id)
        except ProductVariant.DoesNotExist:
            return "—"

        image = (
            ProductImage.objects
            .filter(variant__product=variant.product, is_primary=True)
            .first()
        )

        if image and image.image:
            return format_html(
                '<img src="{}" style="width:50px;height:60px;object-fit:cover;border-radius:4px;" />',
                image.image.url
            )

        return "—"
