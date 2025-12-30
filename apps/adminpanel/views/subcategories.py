from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.adminpanel.decorators import admin_required
from apps.catalog.models import SubCategory
from apps.adminpanel.forms.subcategory_forms import SubCategoryForm


@admin_required
def subcategory_list(request):
    subcategories = (
        SubCategory.objects
        .select_related("category")
        .order_by("name")
    )

    context = {
        "subcategories": subcategories
    }

    return render(
        request,
        "adminpanel/subcategories/subcategory_list.html",
        context
    )


@admin_required
def subcategory_create(request):
    if request.method == "POST":
        form = SubCategoryForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Subcategory created successfully."
            )
            return redirect("adminpanel:subcategory_list")
    else:
        form = SubCategoryForm()

    context = {
        "form": form,
        "is_edit": False,
    }

    return render(
        request,
        "adminpanel/subcategories/subcategory_form.html",
        context
    )


@admin_required
def subcategory_edit(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)

    if request.method == "POST":
        form = SubCategoryForm(
            request.POST,
            request.FILES,
            instance=subcategory
        )

        # Handle image delete
        if request.POST.get("remove_image"):
            subcategory.image.delete(save=False)
            subcategory.image = None

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Subcategory updated successfully."
            )
            return redirect("adminpanel:subcategory_list")
    else:
        form = SubCategoryForm(instance=subcategory)

    context = {
        "form": form,
        "subcategory": subcategory,
        "is_edit": True,
    }

    return render(
        request,
        "adminpanel/subcategories/subcategory_form.html",
        context
    )


# AJAX for product Subcategory


def ajax_load_subcategories(request):
    category_id = request.GET.get("category_id")

    if not category_id:
        return JsonResponse([], safe=False)

    subcategories = SubCategory.objects.filter(
        category_id=category_id,
        is_active=True
    ).values("id", "name")

    return JsonResponse(list(subcategories), safe=False)
