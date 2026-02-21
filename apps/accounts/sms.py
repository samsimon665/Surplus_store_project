import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_sms(phone, otp):
    """
    Development-safe SMS sender.
    Switch behavior based on SMS_BACKEND setting.
    """

    if settings.SMS_BACKEND == "console":
        logger.info(f"[DEV OTP] Phone: {phone} | OTP: {otp}")
        print(f"\n🔥 DEV OTP for {phone}: {otp}\n")
        return True

    # Future: production backends
    elif settings.SMS_BACKEND == "twilio":
        raise NotImplementedError("Twilio not configured yet.")

    elif settings.SMS_BACKEND == "msg91":
        raise NotImplementedError("MSG91 not configured yet.")

    else:
        raise ValueError("Invalid SMS_BACKEND setting.")
