from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=10)
    last_name = forms.CharField(max_length=10)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]

    # EMAIL
    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")

        return email

    # FIRST NAME
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name').strip()

        if len(first_name) < 3:
            raise ValidationError(
                "First name must be at least 3 characters long.")

        if not re.match(r"^[A-Za-z]+$", first_name):
            raise ValidationError("First name must contain only letters.")

        return first_name

    # LAST NAME
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name').strip()

        if not re.match(r"^[A-Za-z]+$", last_name):
            raise ValidationError("Last name must contain only letters.")

        return last_name

    # USERNAME
    def clean_username(self):
        username = self.cleaned_data.get('username').strip()

        if len(username) < 4:
            raise ValidationError(
                "Username must be at least 4 characters long.")

        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValidationError(
                "Username can contain only letters, numbers, and underscores.")

        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")

        return username
