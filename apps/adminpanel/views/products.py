from django.shortcuts import render
from apps.adminpanel.utils import admin_required


@admin_required
def products(request):
    return render(request, "adminpanel/products.html")
