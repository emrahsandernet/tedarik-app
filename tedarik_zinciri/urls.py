"""
URL configuration for tedarik_zinciri project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as token_views
from tedarik.views import (
    SurecViewSet, AdimViewSet, SurecDurumuViewSet,
    GeriGondermeViewSet, DosyaViewSet, MeView, SurecYorumViewSet
)
from talep.views import MalzemeTalebiViewSet, TalepKalemiViewSet
from core.views import UserViewSet, DepartmanViewSet, UrunViewSet, TedarikciViewSet
from tedarik.views import UserProfileViewSet,SatinAlmaSiparisiViewSet,ProjeViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
# Core
router.register(r'users', UserViewSet)
router.register(r'departmanlar', DepartmanViewSet)
router.register(r'urunler', UrunViewSet)
router.register(r'tedarikciler', TedarikciViewSet)

# Workflow
router.register(r'surecler', SurecViewSet)
router.register(r'adimlar', AdimViewSet)
router.register(r'surec-durumlari', SurecDurumuViewSet)
router.register(r'geri-gondermeler', GeriGondermeViewSet)
router.register(r'dosyalar', DosyaViewSet)
router.register(r'surec-yorumlar', SurecYorumViewSet)
# Talep
router.register(r'malzeme-talepleri', MalzemeTalebiViewSet)
router.register(r'talep-kalemleri', TalepKalemiViewSet)


# Sipariş
router.register(r'talepler', SatinAlmaSiparisiViewSet)
router.register(r'projeler', ProjeViewSet)
# Tedarik
router.register(r'user-profiles', UserProfileViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('api-token-auth/', token_views.obtain_auth_token),
    path('api/auth/me/', MeView.as_view(), name='me'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
