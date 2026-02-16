from django.shortcuts import render, redirect

from .forms import ProfileDetailsForm, PhoneUpdateForm, ProfileImageForm

from allauth.account.models import EmailAddress

from django.contrib.auth.decorators import login_required

from .forms import AddressForm


@login_required(login_url='accounts:login')
def profile_view(request):
    profile = request.user.profile

    details_form = ProfileDetailsForm(
        instance=profile,
        initial={"full_name": request.user.first_name}
    )

    phone_form = PhoneUpdateForm(instance=profile)
    image_form = ProfileImageForm(instance=profile)

    email_verified = EmailAddress.objects.filter(
        user=request.user,
        verified=True
    ).exists()

    addresses = request.user.addresses.all()

    context = {
        "profile": profile,
        "details_form": details_form,
        "phone_form": phone_form,
        "image_form": image_form,
        "email_verified": email_verified,
        "phone_verified": False,
        "addresses": addresses,
    }

    return render(request, "accounts/profile.html", context)


@login_required(login_url='accounts:login')
def update_details(request):
    if request.method == "POST":

        form = ProfileDetailsForm(request.POST, instance=request.user.profile)

        if form.is_valid():

            # ✅ Update USER fields directly from POST
            request.user.first_name = request.POST.get("first_name", "").strip()
            request.user.last_name = request.POST.get("last_name", "").strip()
            request.user.save()

            # ✅ Update PROFILE fields (gender, dob)
            form.save()

    return redirect("accounts:profile")



@login_required(login_url='accounts:login')
def update_phone(request):
    if request.method == "POST":
        form = PhoneUpdateForm(request.POST, instance=request.user.profile)

        if form.is_valid():
            profile = form.save()

    return redirect("accounts:profile")


@login_required(login_url='accounts:login')
def update_image(request):
    if request.method == "POST":
        form = ProfileImageForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )

        if form.is_valid():
            profile = form.save()

    return redirect("accounts:profile")


@login_required(login_url="accounts:login")
def add_address(request):
    if request.method != "POST":
        return redirect("accounts:profile")

    form = AddressForm(request.POST)

    if form.is_valid():
        address = form.save(commit=False)
        address.user = request.user

        # If this is the user's first address → force default
        if not request.user.addresses.exists():
            address.is_default = True

        address.save()

    return redirect("accounts:profile")
