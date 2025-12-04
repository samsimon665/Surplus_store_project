from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


# ✅ THIS CONTROLS MANUAL EMAIL SENDING
class CustomAccountAdapter(DefaultAccountAdapter):
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        # ❌ Blocks auto email sending on signup
        return


# ✅ THIS CONTROLS GOOGLE AUTO VERIFICATION
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # ✅ Auto-verify Google users
        if hasattr(user, 'profile'):
            user.profile.email_verified = True
            user.profile.save()

        return user
