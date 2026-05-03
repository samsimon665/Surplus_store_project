from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate

from apps.orders.models import Order


def admin_analytics(request):

    # -------------------------
    # 1. DATE FILTER
    # -------------------------
    days = int(request.GET.get("days", 30))

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    orders = Order.objects.filter(created_at__gte=start_date)

    # -------------------------
    # 2. PAID ORDERS
    # -------------------------
    paid_orders_qs = orders.filter(payment_status="paid")

    # -------------------------
    # 3. FULL DATE RANGE (IMPORTANT FIX)
    # -------------------------
    date_range = [
        (start_date + timedelta(days=i)).date()
        for i in range(days)
    ]

    # -------------------------
    # 4. AGGREGATED DATA
    # -------------------------
    trend_qs = (
        paid_orders_qs
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(
            revenue=Sum("total_amount"),
            count=Count("id")
        )
    )

    trend_dict = {
        item["date"]: item
        for item in trend_qs
    }

    # -------------------------
    # 5. FINAL CHART DATA
    # -------------------------
    dates = []
    revenue = []
    order_counts = []

    for date in date_range:
        data = trend_dict.get(date)

        dates.append(date.strftime("%d %b"))

        if data:
            revenue.append(float(data["revenue"] or 0))
            order_counts.append(data["count"])
        else:
            revenue.append(0)
            order_counts.append(0)

    # -------------------------
    # 6. STATUS DISTRIBUTION
    # -------------------------
    status_qs = (
        orders
        .values("status")
        .annotate(count=Count("id"))
    )

    status_data = {
        item["status"]: item["count"]
        for item in status_qs
    }

    # -------------------------
    # 7. SUMMARY
    # -------------------------
    total_orders = orders.count()
    paid_orders = orders.filter(payment_status="paid").count()
    delivered_orders = orders.filter(status="delivered").count()
    cancelled_orders = orders.filter(status="cancelled").count()

    # -------------------------
    # 8. REVENUE + REFUNDS
    # -------------------------
    total_revenue = paid_orders_qs.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    refunded_qs = orders.filter(refund_status="processed")

    total_refunded = refunded_qs.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    refund_count = refunded_qs.count()

    refund_rate = (
        (refund_count / total_orders) * 100
        if total_orders > 0 else 0
    )

    # -------------------------
    # 9. TOP CUSTOMERS
    # -------------------------
    top_customers_qs = (
        paid_orders_qs
        .values("user__username", "user__email")
        .annotate(
            order_count=Count("id"),
            total_spent=Sum("total_amount")
        )
        .order_by("-total_spent")[:5]
    )

    top_customers = [
        {
            "name": c["user__username"],
            "email": c["user__email"],
            "order_count": c["order_count"],
            "total_spent": float(c["total_spent"] or 0),
        }
        for c in top_customers_qs
    ]

    # -------------------------
    # 10. INSIGHTS
    # -------------------------
    insights = []

    if total_orders > 0:
        cancel_rate = (cancelled_orders / total_orders) * 100
        if cancel_rate > 20:
            insights.append("High cancellation rate detected")

    if total_refunded > 0:
        insights.append("Refund activity present")

    if total_revenue > 0:
        insights.append("Revenue is being generated")

    if not insights:
        insights.append("No significant activity")

    # -------------------------
    # FINAL CONTEXT
    # -------------------------
    context = {
        "dates": dates,
        "revenue": revenue,
        "order_counts": order_counts,
        "status_data": status_data,

        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,

        "total_revenue": total_revenue,
        "total_refunded": total_refunded,
        "refund_count": refund_count,
        "refund_rate": round(refund_rate, 2),

        "top_customers": top_customers,
        "insights": insights,
    }

    return render(request, "adminpanel/analytics.html", context)
