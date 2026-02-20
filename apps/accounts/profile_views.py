from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ProfileDetailsForm, PhoneUpdateForm, ProfileImageForm, AddressForm

from allauth.account.models import EmailAddress

from django.contrib.auth.decorators import login_required

from .models import Address 


@login_required(login_url='accounts:login')
def profile_view(request):
    profile = request.user.profile

    # -----------------------------------
    # ADDRESS MODE CONTROL
    # -----------------------------------

    edit_id = request.GET.get("edit")
    address_instance = None

    if edit_id:
        address_instance = get_object_or_404(
            Address,
            id=edit_id,
            user=request.user
        )

    # If editing → instance form
    # Else → blank form
    address_form = AddressForm(instance=address_instance)

    # -----------------------------------
    # ORDER ADDRESSES (Default on top)
    # -----------------------------------

    addresses = request.user.addresses.order_by("-is_default", "-id")

    # -----------------------------------
    # OTHER PROFILE FORMS
    # -----------------------------------

    details_form = ProfileDetailsForm(instance=profile)
    phone_form = PhoneUpdateForm(instance=profile)
    image_form = ProfileImageForm(instance=profile)

    # -----------------------------------
    # EMAIL STATUS
    # -----------------------------------


    email_obj = EmailAddress.objects.filter(
        user=request.user,
        primary=True
    ).first()

    email_verified = False

    if email_obj:
        email_verified = email_obj.verified

        # 🔥 If email is verified → remove resend timer session
        if email_obj.verified:
            request.session.pop("last_verification_sent", None)


    # -----------------------------------
    # CONTEXT
    # -----------------------------------

    context = {
        "profile": profile,
        "details_form": details_form,
        "phone_form": phone_form,
        "image_form": image_form,

        "email_verified": email_verified,
        "email_obj": email_obj,
        
        "phone_verified": False,

        "addresses": addresses,

        # Address control
        "address_form": address_form,
        "editing_address_id": edit_id,
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

    profile = request.user.profile
    addresses = request.user.addresses.all()
    address_id = request.POST.get("address_id")

    # 🔥 EDIT MODE
    if address_id:
        address_instance = get_object_or_404(
            Address,
            id=address_id,
            user=request.user
        )
        form = AddressForm(request.POST, instance=address_instance)

    # 🔥 ADD MODE
    else:
        form = AddressForm(request.POST)

    # =============================
    # IF VALID → SAVE
    # =============================
    if form.is_valid():
        address = form.save(commit=False)
        address.user = request.user

        # First address → auto default
        if not request.user.addresses.exists():
            address.is_default = True

        address.save()

        return redirect("accounts:profile")

    # =============================
    # IF INVALID → RE-RENDER PROFILE
    # =============================
    details_form = ProfileDetailsForm(instance=profile)
    phone_form = PhoneUpdateForm(instance=profile)
    image_form = ProfileImageForm(instance=profile)

    email_verified = EmailAddress.objects.filter(
        user=request.user,
        verified=True
    ).exists()

    context = {
        "profile": profile,
        "details_form": details_form,
        "phone_form": phone_form,
        "image_form": image_form,
        "email_verified": email_verified,
        "phone_verified": False,
        "addresses": addresses,

        # 🔥 IMPORTANT
        "address_form": form,
        "editing_address_id": address_id,
    }

    return render(request, "accounts/profile.html", context)


@login_required(login_url="accounts:login")
def set_default_address(request, pk):

    if request.method != "POST":
        return redirect("accounts:profile")

    address = get_object_or_404(
        Address,
        id=pk,
        user=request.user
    )

    # Just mark this one default
    address.is_default = True
    address.save()

    return redirect("accounts:profile")


@login_required(login_url="accounts:login")
def delete_address(request, pk):

    if request.method != "POST":
        return redirect("accounts:profile")

    address = get_object_or_404(
        Address,
        id=pk,
        user=request.user
    )

    was_default = address.is_default

    address.delete()

    # 🔥 If deleted address was default
    if was_default:
        next_address = request.user.addresses.first()
        if next_address:
            next_address.is_default = True
            next_address.save()

    return redirect("accounts:profile")
