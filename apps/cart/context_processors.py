from .models import WishlistItem


def wishlist_count(request):
    if not request.user.is_authenticated:
        return {"wishlist_count": 0}

    count = WishlistItem.objects.filter(
        wishlist__user=request.user
    ).count()

    return {
        "wishlist_count": count
    }
