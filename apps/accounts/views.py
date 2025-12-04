from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm
from allauth.account.models import EmailAddress


def login_view(request):
    return render(request, "accounts/login.html")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()

            # ✅ DO NOT SEND EMAIL HERE
            messages.success(
                request, "Account created. Please verify your email.")
            return redirect("accounts:verification_sent")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def verification_sent(request):
    return render(request, "accounts/verification_sent.html")


@login_required
def send_verification_email(request):
    email_obj, created = EmailAddress.objects.get_or_create(
        user=request.user,
        email=request.user.email,
        defaults={"primary": True, "verified": False},
    )

    if not email_obj.verified:
        # ✅ THIS is the correct resend API
        email_obj.send_confirmation(request)
        messages.success(request, "Verification email sent successfully.")
    else:
        messages.info(request, "Your email is already verified.")

    return redirect("accounts:verification_sent")




def logout_view(request):
    auth_logout(request)
    return redirect("accounts:login")
