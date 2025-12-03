from django.shortcuts import render
from django.shortcuts import redirect

from django.http import HttpResponse
from .forms import RegisterForm

# Create your views here.


def login_view(request):
    return render(request, 'accounts/login.html')


def register_view(request):

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            return redirect('catalog:home')

    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})
