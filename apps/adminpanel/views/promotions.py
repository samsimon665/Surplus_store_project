from django.shortcuts import render, redirect

from apps.promotions.models import PromoCode

from apps.adminpanel.forms.promo_forms import PromoCodeForm

from apps.adminpanel.decorators import admin_required


@admin_required
def promo_create(request):
    if request.method == "POST":
        form = PromoCodeForm(request.POST)

        if form.is_valid():
            promo = form.save(commit=False)
            promo.code = promo.code.upper()
            promo.save()

            return redirect("adminpanel:promo_list")

    else:
        form = PromoCodeForm()

    return render(
        request,
        "adminpanel/promo/promo_create.html",
        {
            "form": form
        }
    )


@admin_required
def promo_list(request):
    promos = PromoCode.objects.all().order_by("-created_at")

    return render(
        request,
        "adminpanel/promo/promo_list.html",
        {
            "promos": promos
        }
    )
