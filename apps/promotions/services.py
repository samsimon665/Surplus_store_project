from decimal import Decimal
from django.utils import timezone
from apps.promotions.models import PromoCode, PromoUsage


class PromoValidationResult:
    def __init__(self, success, promo=None, error=None, discount=Decimal("0.00")):
        self.success = success
        self.promo = promo
        self.error = error
        self.discount = discount


def validate_promo_for_cart(user, cart, code):
    """
    Validates promo against:
    - existence
    - active status
    - date validity
    - usage limit
    - user usage
    - minimum cart value

    Returns PromoValidationResult
    """

    if not code:
        return PromoValidationResult(False, error="Enter promo code.")

    code = code.strip().upper()

    try:
        promo = PromoCode.objects.get(code=code)
    except PromoCode.DoesNotExist:
        return PromoValidationResult(False, error="Invalid promo code.")

    now = timezone.now()

    if not promo.is_active:
        return PromoValidationResult(False, error="Promo inactive.")

    if now < promo.valid_from:
        return PromoValidationResult(False, error="Promo not started yet.")

    if now > promo.valid_to:
        return PromoValidationResult(False, error="Promo expired.")

    if PromoUsage.objects.filter(promo=promo, user=user).exists():
        return PromoValidationResult(False, error="You already used this promo.")

    if promo.usages.count() >= promo.usage_limit_total:
        return PromoValidationResult(False, error="Promo usage limit reached.")

    cart_total_paise = int(cart.subtotal * 100)

    if cart_total_paise < promo.minimum_cart_value:
        return PromoValidationResult(
            False,
            error=f"Minimum cart value is ₹{promo.minimum_cart_value / 100}"
        )

    # ----- Discount Calculation -----
    if promo.discount_type == PromoCode.FLAT:
        discount_paise = promo.discount_value

    else:  # PERCENT
        raw_discount = cart_total_paise * promo.discount_value // 100
        discount_paise = min(raw_discount, promo.maximum_discount_amount)

    discount = Decimal(discount_paise) / 100

    return PromoValidationResult(
        True,
        promo=promo,
        discount=discount
    )
