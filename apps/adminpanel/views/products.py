from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction

from apps.adminpanel.decorators import admin_required
from apps.adminpanel.forms.product_forms import ProductForm

from django.contrib import messages

from apps.catalog.models import Product


@admin_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                product = form.save()

            # TEMP: stay on product page until variant exists
            return redirect("adminpanel:product_list")

    else:
        form = ProductForm()

    return render(
        request,
        "adminpanel/products/product_form.html",
        {"form": form}
    )


@admin_required
def product_list(request):
    products = (
        Product.objects
        .select_related("subcategory", "subcategory__category")
        .order_by("name")
    )

    context = {
        "products": products
    }

    return render(
        request,
        "adminpanel/products/product_list.html",
        context
    )


@admin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        # Handle main image delete
        if request.POST.get("remove_main_image"):
            product.main_image.delete(save=False)
            product.main_image = None

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Product updated successfully."
            )
            return redirect("adminpanel:product_list")
    else:
        form = ProductForm(instance=product)

    context = {
        "form": form,
        "product": product,
        "is_edit": True,
    }

    return render(
        request,
        "adminpanel/products/product_form.html",
        context
    )
