from django.shortcuts import render
from apps.adminpanel.utils import admin_required


@admin_required
def orders(request):
    return render(request, "adminpanel/orders.html")
