from allauth.account.adapter import DefaultAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect


class CustomAccountAdapter(DefaultAccountAdapter):

    def confirm_email(self, request, email_address):

        email_address.verified = True
        email_address.save()

        request.session.pop("last_verification_sent", None)

        # 🔥 add extra tag here
        messages.success(request, "Email verified successfully.",
                         extra_tags="email_verified")

        return redirect("accounts:profile")
