from django.shortcuts import render, redirect

from apps.support.models import FAQ

from apps.adminpanel.forms.faq_forms import FAQForm


def faq_list(request):
    faqs = FAQ.objects.all().order_by("section", "display_order")

    return render(
        request,
        "adminpanel/faq/faq_list.html",
        {"faqs": faqs}
    )


def faq_create(request):        
    if request.method == "POST":
        form = FAQForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("adminpanel:faq_list")
    else:
        form = FAQForm()

    return render(
        request,
        "adminpanel/faq/faq_form.html",
        {"form": form}
    )
