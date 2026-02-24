from django.shortcuts import render, redirect

from django.core.paginator import Paginator

from apps.adminpanel.decorators import admin_required

from django.db.models import Q

from apps.promotions.models import PromoCode
from apps.adminpanel.forms.promo_forms import PromoCodeForm


from django.shortcuts import render, redirect

from django.core.paginator import Paginator

from apps.adminpanel.decorators import admin_required

from django.db.models import Q

from apps.promotions.models import PromoCode
from apps.adminpanel.forms.promo_forms import PromoCodeForm


@admin_required
def promo_create(request):
    if request.method == "POST":
        form = PromoCodeForm(request.POST)

        if form.is_valid():
            promo = form.save(commit=False)

            # -----------------------------
            # Convert money fields properly
            # -----------------------------

            # Percent → store as integer (no *100)
            if promo.discount_type == PromoCode.PERCENT:
                promo.discount_value = int(promo.discount_value)

            # Flat → convert rupees → paise
            elif promo.discount_type == PromoCode.FLAT:
                promo.discount_value = int(promo.discount_value * 100)

            # Minimum cart value → always rupees → paise
            promo.minimum_cart_value = int(promo.minimum_cart_value * 100)

            # Max cap → rupees → paise (only if provided)
            if promo.maximum_discount_amount:
                promo.maximum_discount_amount = int(
                    promo.maximum_discount_amount * 100
                )

            promo.save()

            return redirect("adminpanel:promo_list")

        # If invalid → fall through and render with errors

    else:
        form = PromoCodeForm()

    return render(
        request,
        "adminpanel/promo/promo_create.html",
        {"form": form},
    )

@admin_required
def promo_list(request):
    status = request.GET.get("status", "all")
    query = request.GET.get("q", "").strip()

    promos_qs = PromoCode.objects.all().order_by("-created_at")

    # 🔎 SEARCH
    if query:
        promos_qs = promos_qs.filter(
            Q(code__icontains=query) |
            Q(discount_type__icontains=query)
        )

    # 🔘 STATUS FILTER (business logic)
    promos = []
    for promo in promos_qs:
        promo_status = promo.get_status()
        if status == "all" or promo_status == status:
            promos.append(promo)

    paginator = Paginator(promos, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "adminpanel/promo/promo_list.html",
        {
            "promos": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "current_status": status,
        },
    )


@admin_required
def promo_list(request):
    status = request.GET.get("status", "all")
    query = request.GET.get("q", "").strip()

    promos_qs = PromoCode.objects.all().order_by("-created_at")

    # 🔎 SEARCH
    if query:
        promos_qs = promos_qs.filter(
            Q(code__icontains=query) |
            Q(discount_type__icontains=query)
        )

    # 🔘 STATUS FILTER (business logic)
    promos = []
    for promo in promos_qs:
        promo_status = promo.get_status()
        if status == "all" or promo_status == status:
            promos.append(promo)

    paginator = Paginator(promos, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "adminpanel/promo/promo_list.html",
        {
            "promos": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "current_status": status,
        },
    )
