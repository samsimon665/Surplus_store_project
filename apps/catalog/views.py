from django.shortcuts import render

from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required(login_url='accounts:login')
def home_view(request):
    print("HOME VIEW EXECUTED")
    return render(request, "catalog/home.html")
