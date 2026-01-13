from django.shortcuts import render
from collections import defaultdict
from .models import FAQ


def faq_view(request):
    faqs = FAQ.objects.filter(is_active=True)

    grouped_faqs = defaultdict(list)
    for faq in faqs:
        grouped_faqs[faq.section].append(faq)

    return render(
        request,
        "support/faq.html",
        {
            "grouped_faqs": grouped_faqs
        }
    )
