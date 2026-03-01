from decimal import Decimal
from apps.promotions.models import PromoCode, PromoUsage


class PromoValidationResult:
    def __init__(self, success, promo=None, error=None, discount=Decimal("0.00")):
        self.success = success
        self.promo = promo
        self.error = error
        self.discount = discount


def validate_promo_for_cart(user, cart, code):
    if not code:
        return PromoValidationResult(False, error="Enter promo code.")

    code = code.strip().upper()

    try:
        promo = PromoCode.objects.get(code=code)
    except PromoCode.DoesNotExist:
        return PromoValidationResult(False, error="Invalid promo code.")

    # 1️⃣ Must be active RIGHT NOW
    if promo.status != "active":
        return PromoValidationResult(False, error="Promo is not currently active.")

    # 2️⃣ Cart total in paise (assumes cart.subtotal is Decimal rupees)
    cart_total_paise = int(cart.subtotal * 100)

    # 3️⃣ Minimum cart value
    if cart_total_paise < promo.minimum_cart_value:
        min_rupees = promo.minimum_cart_value / 100
        return PromoValidationResult(
            False,
            error=f"Minimum cart value is ₹{min_rupees:.2f}"
        )

    # 4️⃣ Global usage limit
    if promo.usages.count() >= promo.usage_limit_total:
        return PromoValidationResult(False, error="Promo usage limit reached.")

    # 5️⃣ Already used by this user
    if PromoUsage.objects.filter(promo=promo, user=user).exists():
        return PromoValidationResult(False, error="You already used this promo.")

    # 6️⃣ Calculate discount (in paise)
    if promo.discount_type == PromoCode.FLAT:
        discount_paise = min(promo.discount_value, cart_total_paise)

    else:  # PERCENT
        percent_discount = cart_total_paise * promo.discount_value // 100

        if promo.maximum_discount_amount:
            discount_paise = min(
                percent_discount, promo.maximum_discount_amount)
        else:
            discount_paise = percent_discount

    # Convert to rupees Decimal for frontend
    discount = Decimal(discount_paise) / 100

    return PromoValidationResult(
        True,
        promo=promo,
        discount=discount
    )
