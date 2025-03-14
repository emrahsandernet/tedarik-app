from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import  Surec, Adim, SurecDurumu, GeriGonderme, Dosya
from .serializers import (
     SurecSerializer, AdimSerializer, 
    SurecDurumuSerializer, GeriGondermeSerializer, DosyaSerializer
)
from django.db import models



class SurecViewSet(viewsets.ModelViewSet):
    queryset = Surec.objects.all()
    serializer_class = SurecSerializer
    permission_classes = [permissions.IsAuthenticated]

class AdimViewSet(viewsets.ModelViewSet):
    queryset = Adim.objects.all()
    serializer_class = AdimSerializer
    permission_classes = [permissions.IsAuthenticated]

class SurecDurumuViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SurecDurumu.objects.all()
    serializer_class = SurecDurumuSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Kullanıcıya göre filtreleme
        user = self.request.user
        if user.is_staff:
            return SurecDurumu.objects.all()
        
        # Kullanıcının onaylayabileceği adımları içeren süreç durumlarını getir
        user_department = getattr(user.profile, 'departman', None)
        
        if user_department:
            # Kullanıcının departmanına atanmış adımları içeren süreç durumları
            return SurecDurumu.objects.filter(
                models.Q(mevcut_adim__onaylayanlar=user) | 
                models.Q(mevcut_adim__departmanlar=user_department),
                is_completed=False
            ).distinct()
        else:
            # Sadece kullanıcıya atanmış adımları içeren süreç durumları
            return SurecDurumu.objects.filter(
                mevcut_adim__onaylayanlar=user,
                is_completed=False
            )

class GeriGondermeViewSet(viewsets.ModelViewSet):
    queryset = GeriGonderme.objects.all()
    serializer_class = GeriGondermeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(geri_gonderen=self.request.user)

class DosyaViewSet(viewsets.ModelViewSet):
    queryset = Dosya.objects.all()
    serializer_class = DosyaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(yukleyen=self.request.user) 