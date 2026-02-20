from django.db import models
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress

from django.db import transaction

from django.db.models import Q

import random
import hashlib

from django.utils import timezone
from datetime import timedelta

from django.conf import settings



class Profile(models.Model):

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    phone_verified = models.BooleanField(
        default=False
    )

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )

    profile_pic = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True
    )

    dob = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ===============================
    # COMPLETION LOGIC (DYNAMIC)
    # ===============================
    @property
    def completion_percentage(self):
        score = 0

        # 1️⃣ Profile picture uploaded
        if self.profile_pic:
            score += 20

        # 2️⃣ Personal details complete
        if (
            self.user.first_name and
            self.gender and
            self.dob
        ):
            score += 20

        # 3️⃣ Email verified
        email_verified = EmailAddress.objects.filter(
            user=self.user,
            verified=True
        ).exists()

        if email_verified:
            score += 20

        # 4️⃣ Phone verified
        if self.phone_verified:
            score += 20

        # 5️⃣ At least one address added
        if self.user.addresses.exists():
            score += 20

        return score

    def __str__(self):
        return self.user.username


class Address(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    # Receiver name (can differ from account name)
    full_name = models.CharField(max_length=150)

    # Address fields
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)

    landmark = models.CharField(max_length=255, blank=True)

    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    country = models.CharField(max_length=100, default="India")

    # Default selection
    is_default = models.BooleanField(default=False, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_default=True),
                name="unique_default_address_per_user"
            )
        ]

    def save(self, *args, **kwargs):
        
        with transaction.atomic():
            if self.is_default:
                Address.objects.filter(
                    user=self.user,
                    is_default=True
                ).exclude(pk=self.pk).update(is_default=False)

            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}"


class PhoneOTP(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="phone_otp"
    )

    phone = models.CharField(max_length=20)

    otp_hash = models.CharField(max_length=64)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    attempts = models.PositiveIntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.expires_at

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

    @staticmethod
    def hash_code(code):
        return hashlib.sha256(code.encode()).hexdigest()
