from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress

from .models import Profile, Address


# ---------- HELPER ----------

def update_profile_completion(user):
    """
    Safely update profile completion if profile exists.
    Never crash if profile missing.
    """
    profile = Profile.objects.filter(user=user).first()
    if profile:
        profile.calculate_completion()


# ---------- AUTO CREATE PROFILE ----------

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


# ---------- ADDRESS CHANGES ----------

@receiver(post_save, sender=Address)
def update_completion_on_address_save(sender, instance, **kwargs):
    update_profile_completion(instance.user)


@receiver(post_delete, sender=Address)
def update_completion_on_address_delete(sender, instance, **kwargs):
    update_profile_completion(instance.user)


# ---------- EMAIL VERIFIED ----------

@receiver(post_save, sender=EmailAddress)
def update_completion_on_email_change(sender, instance, **kwargs):
    if instance.verified:
        update_profile_completion(instance.user)
