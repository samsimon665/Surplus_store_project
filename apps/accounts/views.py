from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout as auth_logout

from .forms import RegisterForm, EmailUpdateForm, PhoneUpdateForm
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress

from django.utils import timezone
from datetime import timedelta

from django.db import transaction

from .models import PhoneOTP

from django.contrib.auth.decorators import login_required

def login_view(request):

    #  If user already logged in → do NOT show login page
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
            messages.error(request, "Incorrect password.", extra_tags="password_error")
            return render(request, "accounts/login.html")

        # Login
        login(request, user)

        # session
        request.session['username'] = user.username
        request.session['email'] = user.email
        request.session['logged_in'] = True

        return redirect("catalog:home")

    return render(request, "accounts/login.html")


def register_view(request):

    if request.user.is_authenticated:
        return redirect("catalog:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()

            EmailAddress.objects.create(
                user=user,
                email=user.email,
                primary=True,
                verified=False
            )


            if not user.is_active:
                return redirect("accounts:account_disabled")

            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend"
            )

            messages.success(request, "Account created successfully.")
            return redirect("catalog:home")

        return render(request, "accounts/register.html", {"form": form})

    form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})



# def logout_view(request):
#     if request.method == "POST":
#         auth_logout(request)
#         return redirect("accounts:login")
#     return redirect("accounts:login")

def logout_view(request):
    auth_logout(request)
    return redirect("accounts:login")


def account_disabled(request):
    return render(request, "accounts/account_disabled.html")




# EMAIL VERIFICATION


@login_required(login_url="accounts:login")
def send_verification_email(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    try:
        email_address = EmailAddress.objects.get(
            user=request.user, primary=True)
    except EmailAddress.DoesNotExist:
        messages.error(request, "No email address found.")
        return redirect("accounts:profile")

    if email_address.verified:
        messages.info(request, "Email already verified.")
        return redirect("accounts:profile")

    # 🔥 2 minute throttle
    last_sent = request.session.get("last_verification_sent")

    if last_sent:
        last_sent_time = timezone.datetime.fromisoformat(last_sent)
        if timezone.now() < last_sent_time + timedelta(minutes=2):
            messages.warning(
                request, "Please wait before resending verification email.")
            return redirect("accounts:profile")

    # Send email
    email_address.send_confirmation(request)

    # Save send time in session
    request.session["last_verification_sent"] = timezone.now().isoformat()

    messages.success(
        request,
        "Verification email sent successfully.",
        extra_tags="email_sent"
    )


    return redirect("accounts:profile")



@login_required(login_url="accounts:login")
def update_email(request):

    if request.method != "POST":
        return redirect("accounts:profile")

    form = EmailUpdateForm(request.POST, instance=request.user)

    if form.is_valid():

        new_email = form.cleaned_data["email"]

        EmailAddress.objects.filter(user=request.user).delete()

        request.user.email = new_email
        request.user.save()

        EmailAddress.objects.create(
            user=request.user,
            email=new_email,
            primary=True,
            verified=False
        )

        messages.success(request, "Email updated. Please verify it.")

    else:
        # Save error message
        messages.error(
            request, form.errors["email"][0], extra_tags="email_error")

    return redirect("accounts:profile")


# PHONE VERIFICATION


@login_required(login_url="accounts:login")
def send_phone_otp(request):

    profile = request.user.profile

    # 🚫 No phone number
    if not profile.phone:
        messages.error(
            request,
            "Add phone number first.",
            extra_tags="phone_otp_error"
        )
        return redirect("accounts:profile")

    existing = PhoneOTP.objects.filter(user=request.user).first()

    if existing:

        # 🔥 If expired → clean up first
        if existing.is_expired():
            existing.delete()

        else:
            # 🔥 Cooldown (60 seconds from creation)
            cooldown_time = existing.created_at + timedelta(seconds=60)

            if timezone.now() < cooldown_time:
                messages.warning(
                    request,
                    "Please wait before requesting another OTP.",
                    extra_tags="phone_otp_error"
                )
                return redirect("accounts:profile")

            # 🔥 If phone changed → invalidate old OTP
            if existing.phone != profile.phone:
                existing.delete()

    # ✅ Generate new OTP
    code = PhoneOTP.generate_code()
    hashed_code = PhoneOTP.hash_code(code)

    expires_at = timezone.now() + timedelta(minutes=2)

    # 🔒 Atomic save
    with transaction.atomic():
        PhoneOTP.objects.update_or_create(
            user=request.user,
            defaults={
                "phone": profile.phone,
                "otp_hash": hashed_code,
                "expires_at": expires_at,
                "attempts": 0,
            }
        )

    # 🔥 TEMPORARY (Replace with SMS API later)
    print("PHONE OTP:", code)

    messages.success(
        request,
        "OTP sent successfully.",
        extra_tags="phone_sent"
    )

    return redirect("accounts:profile")

@login_required(login_url="accounts:login")
def verify_phone_otp(request):

    if request.method != "POST":
        return redirect("accounts:profile")

    entered_otp = request.POST.get("otp", "").strip()

    try:
        otp_obj = PhoneOTP.objects.get(user=request.user)
    except PhoneOTP.DoesNotExist:
        messages.error(request, "OTP expired.", extra_tags="phone_otp_error")
        return redirect("accounts:profile")

    # 🔥 Expiry check
    if otp_obj.is_expired():
        otp_obj.delete()
        messages.error(request, "OTP expired. Request new one.",
                       extra_tags="phone_otp_error")
        return redirect("accounts:profile")

    # 🔥 Phone consistency check
    if otp_obj.phone != request.user.profile.phone:
        otp_obj.delete()
        messages.error(request, "Phone changed. Request new OTP.",
                       extra_tags="phone_otp_error")
        return redirect("accounts:profile")

    # 🔥 Attempt limit
    if otp_obj.attempts >= 3:
        otp_obj.delete()
        messages.error(
            request, "Too many attempts. Request new OTP.", extra_tags="phone_otp_error")
        return redirect("accounts:profile")

    # 🔥 Hash compare
    if PhoneOTP.hash_code(entered_otp) != otp_obj.otp_hash:
        otp_obj.attempts += 1
        otp_obj.save(update_fields=["attempts"])

        remaining = 3 - otp_obj.attempts

        messages.error(
            request,
            f"Invalid OTP. {remaining} attempts left.",
            extra_tags="phone_otp_error"
        )
        return redirect("accounts:profile")

    # ✅ SUCCESS
    with transaction.atomic():
        profile = request.user.profile
        profile.phone_verified = True
        profile.save(update_fields=["phone_verified"])

        otp_obj.delete()

    request.session.pop("phone_last_verification_sent", None)

    messages.success(request, "Phone verified successfully.",
                     extra_tags="phone_verified")

    return redirect("accounts:profile")


@login_required
def update_phone(request):

    if request.method != "POST":
        return redirect("accounts:profile")

    form = PhoneUpdateForm(
        request.POST,
        instance=request.user.profile
    )

    if form.is_valid():

        profile = form.save(commit=False)

        # Reset verification if number changed
        if profile.phone != request.user.profile.phone:
            profile.phone_verified = False

        profile.save()

        messages.success(request, "Phone number updated successfully.")

    else:
        messages.error(
            request,
            form.errors["phone"][0],
            extra_tags="phone_update_error"
        )
    return redirect("accounts:profile")
