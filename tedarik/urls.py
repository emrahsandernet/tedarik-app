from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet, SatinAlmaSiparisiViewSet, SurecViewSet, 
    AdimViewSet, SurecDurumuViewSet, GeriGondermeViewSet, DosyaViewSet, 
    MeView, SurecYorumViewSet
)

router = DefaultRouter()
router.register(r'siparisler', SatinAlmaSiparisiViewSet)
router.register(r'surecler', SurecViewSet)
router.register(r'adimlar', AdimViewSet)
router.register(r'surec-durumlari', SurecDurumuViewSet)
router.register(r'geri-gondermeler', GeriGondermeViewSet)
router.register(r'dosyalar', DosyaViewSet)
router.register(r'user-profiles', UserProfileViewSet)
router.register(r'surec-yorumlar', SurecYorumViewSet)

urlpatterns = [
    path('api/', include([
        path('', include(router.urls)),
        path('auth/me/', MeView.as_view(), name='me'),
    ])),
] 