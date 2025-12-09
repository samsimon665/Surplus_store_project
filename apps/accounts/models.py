from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )

    phone = models.BigIntegerField(null=True, blank=True)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )

    profile_pic = models.ImageField(
        upload_to="profiles/", null=True, blank=True
    )

    # ✅ Keep this — default False, no verification logic needed now
    email_verified = models.BooleanField(default=False)

    is_blocked = models.BooleanField(default=False)

    dob = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
