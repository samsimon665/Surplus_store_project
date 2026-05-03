from django.http import JsonResponse
from apps.catalog.models import ProductImage, ProductVariant
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q

from apps.adminpanel.decorators import admin_required
from apps.orders.models import Order


# ================================
# ORDER LIST
# ================================
@admin_required
def orders(request):

    qs = Order.objects.select_related("user").order_by("-created_at")

    status = request.GET.get("status")

    if status:
        qs = qs.filter(status=status)

    if status == "unpaid":
        qs = qs.filter(payment_status="pending")

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "adminpanel/orders/order_list.html", {
        "orders": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "current_status": status,
    })


# ================================
# ORDER DETAIL + STATUS UPDATE
# ================================


@admin_required
def order_detail(request, order_id):

    order = get_object_or_404(Order, id=order_id)

    # 🔥 Attach product + image (cart-style)
    items = order.items.all()

    for item in items:
        variant = (
            ProductVariant.objects
            .select_related("product")
            .filter(id=item.variant_id)
            .first()
        )

        if variant:
            # ✅ Needed for URL
            item.product_id = variant.product.id

            # ✅ Image (cart style)
            image = (
                ProductImage.objects
                .filter(
                    variant__product=variant.product,
                    variant__color=item.color
                )
                .order_by("-is_primary", "created_at")
                .first()
            )

            item.display_image = image
        else:
            item.display_image = None
            item.product_id = None

    # =========================
    # STATUS UPDATE LOGIC
    # =========================
    if request.method == "POST":
        new_status = request.POST.get("status")

        # ❌ Block cancelled
        if order.status == "cancelled":
            messages.error(request, "Cancelled orders cannot be modified")
            return redirect("adminpanel:admin_order_detail", order_id=order.id)

        VALID_TRANSITIONS = {
            "pending": ["processing", "cancelled"],
            "processing": ["shipped", "cancelled"],
            "shipped": ["out_for_delivery"],
            "out_for_delivery": ["delivered"],
            "delivered": [],
        }

        current_status = order.status

        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            messages.error(
                request,
                f"Invalid status change: {current_status} → {new_status}"
            )
            return redirect("adminpanel:admin_order_detail", order_id=order.id)

        # ❌ Prevent cancel without refund
        if new_status == "cancelled" and order.payment_status == "paid":
            if order.refund_status != "processed":
                messages.error(
                    request,
                    "Cannot cancel a paid order without refund"
                )
                return redirect("adminpanel:admin_order_detail", order_id=order.id)

        order.status = new_status
        order.save(update_fields=["status"])

        messages.success(request, "Order status updated successfully")

        return redirect("adminpanel:admin_order_detail", order_id=order.id)

    return render(request, "adminpanel/orders/order_detail.html", {
        "order": order,
        "items": items,   # 🔥 IMPORTANT
    })


@admin_required
def update_order_status_ajax(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        new_status = request.POST.get("status")

        order = get_object_or_404(Order, id=order_id)

        # 🚫 BLOCK FINAL STATES
        if order.status in ["cancelled", "delivered"]:
            return JsonResponse({
                "success": False,
                "message": "This order cannot be modified."
            })

        # ✅ VALID TRANSITIONS (basic safe version)
        VALID_TRANSITIONS = {
            "pending": ["processing", "cancelled"],
            "processing": ["shipped", "cancelled"],
            "shipped": ["out_for_delivery"],
            "out_for_delivery": ["delivered"],
        }

        if new_status not in VALID_TRANSITIONS.get(order.status, []):
            return JsonResponse({
                "success": False,
                "message": "Invalid status transition."
            })

        order.status = new_status
        order.save()

        return JsonResponse({
            "success": True,
            "new_status": order.status
        })

    return JsonResponse({"success": False})
