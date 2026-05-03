from django.shortcuts import render
from django.contrib.auth.models import User
from apps.adminpanel.decorators import admin_required
from apps.orders.models import Order
from django.db.models import Sum


@admin_required
def dashboard(request):

    # Active users
    active_users = User.objects.filter(
        is_active=True, is_superuser=False
    ).count()

    # Total orders
    total_orders = Order.objects.count()

    # Total revenue (ONLY PAID)
    total_revenue = (
        Order.objects.filter(payment_status="paid")
        .aggregate(total=Sum("total_amount"))["total"] or 0
    )

    # Replace "Returns Pending" → Pending Orders
    pending_orders = Order.objects.filter(status="pending").count()

    # Latest 10 orders
    recent_orders = (
        Order.objects.select_related("user")
        .order_by("-created_at")[:10]
    )

    context = {
        "active_users": active_users,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
        "recent_orders": recent_orders,
    }

    return render(request, "adminpanel/dashboard.html", context)
