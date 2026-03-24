import razorpay
from django.conf import settings


client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def create_razorpay_order(order):

    amount = int(order.total_amount * 100)

    data = {
        "amount": amount,
        "currency": "INR",
        "receipt": str(order.uuid),
        "notes": {
            "order_uuid": str(order.uuid)
        }
    }

    try:

        razorpay_order = client.order.create(data=data)

        return razorpay_order

    except Exception as e:

        print("RAZORPAY ORDER CREATION FAILED:", e)

        return None
