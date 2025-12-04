# apps/accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.account.signals import email_confirmed
from .models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(email_confirmed)
def update_profile_email_verified(sender, request, email_address, **kwargs):
    user = email_address.user
    if hasattr(user, 'profile'):
        user.profile.email_verified = True
        user.profile.save()
