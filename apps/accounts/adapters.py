from allauth.account.adapter import DefaultAccountAdapter
from django.contrib import messages


class CustomAccountAdapter(DefaultAccountAdapter):

    # FIX 1 — auto create username for Google users
    def populate_username(self, request, user):
        if not user.username:
            base = user.email.split("@")[0]
            user.username = self.generate_unique_username([base, "user"])

    # FIX 2 — DO NOT return redirect here

    def confirm_email(self, request, email_address):
        email_address.verified = True
        email_address.save()

        request.session.pop("last_verification_sent", None)

        messages.success(
            request,
            "Email verified successfully.",
            extra_tags="email_verified"
        )
