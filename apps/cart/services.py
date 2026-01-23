class CartItemStatus:
    
    VALID = "valid"
    OUT_OF_STOCK = "out_of_stock"
    INSUFFICIENT_STOCK = "insufficient_stock"
    DISABLED = "disabled"


def get_cart_item_status(cart_item):
    
    variant = cart_item.variant

    # Variant disabled or deleted logically
    if not variant.is_active:
        return CartItemStatus.DISABLED

    # Completely out of stock
    if variant.stock == 0:
        return CartItemStatus.OUT_OF_STOCK

    # User wants more than available
    if cart_item.quantity > variant.stock:
        return CartItemStatus.INSUFFICIENT_STOCK

    return CartItemStatus.VALID


def is_cart_valid(cart):
   
    for item in cart.items.select_related("variant"):
        if get_cart_item_status(item) != CartItemStatus.VALID:
            return False
    return True


