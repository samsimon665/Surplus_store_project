from django.shortcuts import render
from django.contrib.auth.models import User
from apps.adminpanel.decorators import admin_required



@admin_required
def dashboard(request):
    active_users = User.objects.filter(
        is_active=True, is_superuser=False).count()
    return render(request, "adminpanel/dashboard.html", {"active_users": active_users})
