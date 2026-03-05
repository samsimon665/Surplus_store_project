from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from apps.orders.models import Order


@login_required(login_url="accounts:login")
def payment_page(request, uuid):

    order = get_object_or_404(
        Order,
        uuid=uuid,
        user=request.user
    )

    return render(
        request,
        "payments/payment.html",
        {
            "order": order
        }
    )
