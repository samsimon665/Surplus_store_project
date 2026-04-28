
from io import BytesIO
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import get_template

from django.conf import settings
import os
from django.templatetags.static import static



# invoice_view.py

import logging
logging.getLogger("xhtml2pdf").setLevel(logging.ERROR)

from xhtml2pdf import pisa

from .models import Order





# 🔹 PREVIEW (HTML page)
@login_required
def invoice_preview(request, uuid):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        uuid=uuid,
        user=request.user
    )

    return render(request, "orders/invoice_preview.html", {"order": order})


def link_callback(uri, rel):
    from django.conf import settings
    import os

    if uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.BASE_DIR, uri.replace(
            settings.STATIC_URL, "static/"))
    else:
        return uri

    if not os.path.isfile(path):
        raise Exception(f"Media URI must exist: {path}")

    return path



# 🔹 DOWNLOAD (PDF)
@login_required
def download_invoice(request, uuid):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        uuid=uuid,
        user=request.user
    )

    # ✅ STEP 1: Get absolute logo path
    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.png")
    logo_path = f"file:///{logo_path.replace('\\', '/')}"

    # ✅ STEP 2: Pass to template
    template = get_template("orders/invoice_pdf.html")
    html = template.render({
        "order": order,
        "logo_path": logo_path
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="invoice.pdf"'

    pisa_status = pisa.CreatePDF(
        html,
        dest=response,
        link_callback=link_callback
    )

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    return response


# FOR EMAIL INVOICE

def generate_invoice_pdf(order):
    template = get_template("orders/invoice_pdf.html")
    html = template.render({"order": order})

    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)

    if pisa_status.err:
        return None

    return result.getvalue()
