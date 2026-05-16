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

from django.conf import settings
from django.conf.urls.static import static


# SEO - SITEMAP

from django.contrib.sitemaps.views import sitemap
from apps.catalog.sitemaps import (StaticViewSitemap, CategorySitemap, ProductSitemap)


sitemaps = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
}


urlpatterns = [

    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),

    
    path('admin/', admin.site.urls),

    path('adminpanel/', include("apps.adminpanel.urls")),

    path('', include('apps.pages.urls')),

    path('accounts/', include('apps.accounts.urls')),

    path('accounts/', include('allauth.urls')),

    path('catalog/', include('apps.catalog.urls')),

    path('support/', include("apps.support.urls")),

    path("cart/", include("apps.cart.urls")),

    path("order/", include("apps.orders.urls")),

    path("payments/", include("apps.payments.urls")),


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
