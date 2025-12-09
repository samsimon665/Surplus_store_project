from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as auth_logout

from .forms import RegisterForm
from django.contrib.auth.models import User


def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("email")  # email or username
        password = request.POST.get("password")

        # 1️⃣ Check if identifier is email
        if "@" in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                messages.error(
                    request, "No account found with this email.", extra_tags="email_error")
                return render(request, "accounts/login.html")

            # Check password
            user = authenticate(
                request, username=user_obj.username, password=password)
            if user is None:
                messages.error(request, "Incorrect password.",
                               extra_tags="password_error")
                return render(request, "accounts/login.html")

            login(request, user)
            return redirect("catalog:home")

        else:
            # 2️⃣ Identifier is username
            try:
                user_obj = User.objects.get(username__iexact=identifier)
            except User.DoesNotExist:
                messages.error(
                    request, "No account found with this username.", extra_tags="username_error")
                return render(request, "accounts/login.html")

            # Check password
            user = authenticate(
                request, username=user_obj.username, password=password)
            if user is None:
                messages.error(request, "Incorrect password.",
                               extra_tags="password_error")
                return render(request, "accounts/login.html")

            login(request, user)
            return redirect("catalog:home")

    return render(request, "accounts/login.html")




def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()

            messages.success(
                request, "Account created successfully. You can now login.")
            return redirect("catalog:home")
        else:
            # Form has errors → they will show under fields
            return render(request, "accounts/register.html", {"form": form})

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("accounts:login")
