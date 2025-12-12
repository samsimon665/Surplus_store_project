from .utils import admin_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect




@admin_required
def dashboard(request):
    active_users = User.objects.filter(
        is_active=True, is_superuser=False).count()
    return render(request, "adminpanel/dashboard.html", {"active_users": active_users})


@admin_required
def customers(request):
    users = User.objects.filter(is_superuser=False).select_related(
        "profile").order_by("-id")
    return render(request, "adminpanel/customers.html", {'users': users})


@admin_required
def categories(request):
    return render(request, "adminpanel/categories.html")


@admin_required
def products(request):
    return render(request, "adminpanel/products.html")


@admin_required
def orders(request):
    return render(request, "adminpanel/orders.html")


@admin_required
def block_user(request, user_id):
    user = User.objects.get(id=user_id, is_superuser=False)
    user.is_active = False
    user.save()
    return redirect('adminpanel:customers')


@admin_required
def unblock_user(request, user_id):
    user = User.objects.get(id=user_id, is_superuser=False)
    user.is_active = True
    user.save()
    return redirect('adminpanel:customers')


def admin_login(request):

    # If admin already logged in:
    if request.user.is_authenticated and request.user.is_superuser and request.session.get("is_admin"):
        return redirect("adminpanel:dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password")
            return render(request, "adminpanel/login.html")

        if not user.is_superuser:
            messages.error(
                request, "You are not allowed to access admin panel")
            return render(request, "adminpanel/login.html")

        # Login admin with correct backend
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # ⭐ ADMIN SESSION FLAG
        request.session['is_admin'] = True

        return redirect("adminpanel:dashboard")

    return render(request, "adminpanel/login.html")


def admin_logout(request):
    if request.method == 'POST':
        logout(request)
        request.session.flush()  # clear everything including is_admin
        return redirect("adminpanel:login")
