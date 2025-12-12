from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as auth_logout

from .forms import RegisterForm
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required


# @login_required(login_url="accounts:login")


def login_view(request):

    # 🔥 If user already logged in → do NOT show login page
    if request.user.is_authenticated:
        return redirect("catalog:home")

    if request.method == "POST":
        identifier = request.POST.get("email")
        password = request.POST.get("password")

        # If user entered email
        if "@" in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                messages.error(
                    request, "No account found with this email.", extra_tags="email_error")
                return render(request, "accounts/login.html")

        # If user entered username
        else:
            try:
                user_obj = User.objects.get(username__iexact=identifier)
            except User.DoesNotExist:
                messages.error(
                    request, "No account found with this username.", extra_tags="username_error")
                return render(request, "accounts/login.html")

        # Check active status
        if not user_obj.is_active:
            return redirect("accounts:account_disabled")

        # Authenticate
        user = authenticate(
            request, username=user_obj.username, password=password)
        if user is None:
            messages.error(request, "Incorrect password.",
                           extra_tags="password_error")
            return render(request, "accounts/login.html")

        # Login
        login(request, user)

        # Optional session data
        request.session['username'] = user.username
        request.session['email'] = user.email
        request.session['logged_in'] = True

        return redirect("catalog:home")

    return render(request, "accounts/login.html")


def register_view(request):

    # 🔥 If user already logged in → do not show register page
    if request.user.is_authenticated:
        return redirect("catalog:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()

            if not user.is_active:
                return redirect("accounts:account_disabled")

            # Auto login after register
            login(request, user)

            messages.success(request, "Account created successfully.")
            return redirect("catalog:home")

        return render(request, "accounts/register.html", {"form": form})

    form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
        return redirect("accounts:login")
    return redirect("accounts:login")


def account_disabled(request):
    return render(request, "accounts/account_disabled.html")
