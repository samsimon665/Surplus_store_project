"""
URL configuration for surplus_store_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # path('', include('apps.pages.urls')),   # intentionally disabled
    # path('accounts/', include('apps.accounts.urls')),  # old test route

    path('catalog/', include('apps.catalog.urls')),

    # ✅ ENABLE ONLY AUTH SYSTEM PROPERLY
    path('', include('apps.accounts.urls')),
    path('accounts/', include('allauth.urls')),
]
