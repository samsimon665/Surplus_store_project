from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Order


@login_required(login_url="accounts:login")
def invoice_preview(request, uuid):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        uuid=uuid,
        user=request.user
    )
    return render(request, "orders/invoice.html", {"order": order})
