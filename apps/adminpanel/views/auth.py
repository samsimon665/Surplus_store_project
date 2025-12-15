from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.shortcuts import render, redirect

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
