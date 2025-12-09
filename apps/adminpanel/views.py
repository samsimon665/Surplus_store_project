from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test

# Only superusers can access admin panel


def admin_only(user):
    return user.is_superuser


@user_passes_test(admin_only)
def dashboard(request):
    return render(request, "adminpanel/dashboard.html")


@user_passes_test(admin_only)
def users(request):
    return render(request, "adminpanel/users.html")


@user_passes_test(admin_only)
def shops(request):
    return render(request, "adminpanel/shops.html")


@user_passes_test(admin_only)
def categories(request):
    return render(request, "adminpanel/categories.html")


@user_passes_test(admin_only)
def products(request):
    return render(request, "adminpanel/products.html")


@user_passes_test(admin_only)
def orders(request):
    return render(request, "adminpanel/orders.html")
