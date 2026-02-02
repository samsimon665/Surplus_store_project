from .models import WishlistItem, CartItem


def nav_counts(request):
    if not request.user.is_authenticated:
        return {
            "wishlist_count": 0,
            "cart_count": 0,
        }

    wishlist_count = WishlistItem.objects.filter(
        wishlist__user=request.user
    ).count()

    cart_count = CartItem.objects.filter(
        cart__user=request.user
    ).count()

    return {
        "wishlist_count": min(wishlist_count, 10),
        "cart_count": min(cart_count, 10),
    }
