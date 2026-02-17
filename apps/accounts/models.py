from django.db import models
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress

from django.db import transaction

from django.db.models import Q


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
            score += 25

        # 2️⃣ Personal details complete
        if (
            (self.user.first_name or self.user.last_name) and
            self.gender and
            self.dob
        ):
            score += 25

        # 3️⃣ At least one address added
        if self.user.addresses.exists():
            score += 25

        # 4️⃣ Contact info verified (email + phone)
        email_verified = EmailAddress.objects.filter(
            user=self.user,
            verified=True
        ).exists()

        if email_verified and self.phone_verified:
            score += 25

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
