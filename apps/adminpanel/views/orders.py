from django.shortcuts import render
from apps.adminpanel.decorators import admin_required
from apps.orders.models import Order

from django.core.paginator import Paginator

from django.db.models import Q



@admin_required
def orders(request):

    qs = Order.objects.select_related("user").order_by("-created_at")

    status = request.GET.get("status")

    if status:
        qs = qs.filter(status=status)

    # Optional: quick filter for "unpaid"
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