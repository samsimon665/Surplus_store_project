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
            form.save()
            return redirect("adminpanel:promo_list")

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
def promo_edit(request, promo_id):
    promo = PromoCode.objects.get(id=promo_id)

    # Convert paise → rupees before showing in form
    initial_data = {
        "code": promo.code,
        "discount_type": promo.discount_type,
        "discount_value": (
            promo.discount_value / 100
            if promo.discount_type == PromoCode.FLAT
            else promo.discount_value
        ),
        "minimum_cart_value": promo.minimum_cart_value / 100,
        "maximum_discount_amount": (
            promo.maximum_discount_amount / 100
            if promo.maximum_discount_amount
            else None
        ),
        "usage_limit_total": promo.usage_limit_total,
        "valid_from": promo.valid_from,
        "valid_to": promo.valid_to,
        "is_active": promo.is_active,
    }

    if request.method == "POST":
        form = PromoCodeForm(request.POST, instance=promo)

        if form.is_valid():
            form.save()
            return redirect("adminpanel:promo_list")

    else:
        form = PromoCodeForm(initial=initial_data, instance=promo)

    return render(
        request,
        "adminpanel/promo/promo_create.html",  # reuse same template
        {"form": form, "is_edit": True},
    )
