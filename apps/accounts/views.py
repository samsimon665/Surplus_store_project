from django.shortcuts import render, redirect
from django.contrib.auth.models import User

from django.contrib import messages
from .forms import RegisterForm


# Create your views here.


def login_view(request):
    return render(request, 'accounts/login.html')


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()

            messages.success(request, "Account created successfully!")
            # ✅ IMPORTANT: REDIRECT AFTER SUCCESS
            return redirect("accounts:login")

    else:
        form = RegisterForm()   # ✅ EMPTY FORM ON GET

    return render(request, "accounts/register.html", {"form": form})
