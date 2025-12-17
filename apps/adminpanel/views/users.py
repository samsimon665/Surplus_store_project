from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from apps.adminpanel.decorators import admin_required


@admin_required
def customers(request):
    users = User.objects.filter(is_superuser=False).select_related(
        "profile").order_by("-id")
    return render(request, "adminpanel/customers.html", {'users': users})


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
