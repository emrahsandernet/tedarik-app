from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import (
    Urun, Tedarikci, SatinAlmaSiparisi, Surec, Adim, 
    SurecDurumu, Departman, UserProfile, GeriGonderme, Dosya,
    Proje, SurecYorum
)
from .serializers import (
    UrunSerializer, TedarikciSerializer, SatinAlmaSiparisiSerializer,
    SurecSerializer, AdimSerializer, SurecDurumuSerializer,
    DepartmanSerializer, UserProfileSerializer, GeriGondermeSerializer,
    DosyaSerializer, ProjeSerializer, SurecYorumSerializer
)
from workflow.engine import WorkflowEngine
from django.shortcuts import get_object_or_404
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.views import APIView

# Create your views here.

class UrunViewSet(viewsets.ModelViewSet):
    queryset = Urun.objects.all()
    serializer_class = UrunSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

class TedarikciViewSet(viewsets.ModelViewSet):
    queryset = Tedarikci.objects.all()
    serializer_class = TedarikciSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

class SurecViewSet(viewsets.ModelViewSet):
    queryset = Surec.objects.all()
    serializer_class = SurecSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

class AdimViewSet(viewsets.ModelViewSet):
    queryset = Adim.objects.all()
    serializer_class = AdimSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Adim.objects.all()
        surec_id = self.request.query_params.get('surec', None)
        
        if surec_id is not None:
            queryset = queryset.filter(surec_id=surec_id)
        
        return queryset.order_by('sira')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['surec_id'] = self.request.query_params.get('surec')
        return context
    
    @action(detail=False, methods=['get'])
    def by_surec(self, request):
        """Belirli bir sürece ait adımları getirir"""
        surec_id = request.query_params.get('surec', None)
        if not surec_id:
            return Response(
                {"error": "Süreç ID'si belirtilmelidir"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        adimlar = self.get_queryset().filter(surec_id=surec_id).order_by('sira')
        serializer = self.get_serializer(adimlar, many=True)
        
        return Response(serializer.data)

class SatinAlmaSiparisiViewSet(viewsets.ModelViewSet):
    queryset = SatinAlmaSiparisi.objects.all()
    serializer_class = SatinAlmaSiparisiSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
   

    def get_queryset(self):
        # Kullanıcıya göre filtreleme
        user = self.request.user
        if user.is_staff:
            return SatinAlmaSiparisi.objects.all()
        return SatinAlmaSiparisi.objects.filter(olusturan=user)
    
    def perform_create(self, serializer):
        # Kullanıcıyı otomatik olarak ekle
        serializer.save(olusturan=self.request.user, son_islem_yapan=self.request.user)

    
    
    @action(detail=True, methods=['get'])
    def detaylar(self, request, pk=None):
        try:
            siparis = self.get_object()
            # tedarik_surec_durumu olarak değiştirildi
            surec_durumu = siparis.tedarik_surec_durumu
            geri_gondermeler = GeriGonderme.objects.filter(surec_durumu=surec_durumu)
            
            return Response({
                'siparis': SatinAlmaSiparisiSerializer(siparis).data,
                'surec_durumu': SurecDurumuSerializer(surec_durumu).data,
                'geri_gondermeler': GeriGondermeSerializer(geri_gondermeler, many=True).data
            })
        except SatinAlmaSiparisi.DoesNotExist:
            return Response(
                {'error': 'Sipariş bulunamadı'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except SurecDurumu.DoesNotExist:
            return Response(
                {'error': 'Süreç durumu bulunamadı'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def onayla(self, request, pk=None):
        """Mevcut adımı onaylar ve bir sonraki adıma geçer"""
        print("onayla fonksiyonu çağrıldı", request.data)
        yorum = request.data.get('yorum', '')
        
        try:
            siparis = self.get_object()
            
            try:
                surec_durumu = siparis.tedarik_surec_durumu
                print(surec_durumu)
            except SurecDurumu.DoesNotExist:
                return Response(
                    {"error": "Bu sipariş için aktif bir süreç durumu bulunamadı."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # WorkflowEngine kullanarak adımı işle
            try:
                # Önce yorumu oluştur
                if yorum:
                    yeni_yorum = SurecYorum.objects.create(
                        surec_durumu=surec_durumu,
                        adim=surec_durumu.mevcut_adim,
                        yazan=request.user,
                        yorum=yorum
                    )
                    
                    # Dosya yükleme işlemi
                    dosyalar = request.FILES.getlist('dosyalar', [])
                    for dosya in dosyalar:
                        dosya_obj = Dosya.objects.create(
                            surec_durumu=surec_durumu,
                            dosya=dosya,
                            yukleyen=request.user
                        )
                        yeni_yorum.dosyalar.add(dosya_obj)
                
                # Sonra adımı işle
                engine = WorkflowEngine(surec_durumu, request.user)
                engine.process_step(request.data)
                
                return Response({"message": "Adım onaylandı"})
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except SatinAlmaSiparisi.DoesNotExist:
            return Response(
                {'error': 'Sipariş bulunamadı'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def reddet(self, request, pk=None):
        """Mevcut adımı reddeder"""
        siparis = self.get_object()
        
        # Eğer sipariş zaten reddedilmişse, hata döndürme
        if siparis.durum == 'reddedildi':
            return Response(
                {"message": "Bu sipariş zaten reddedilmiş"},
                status=status.HTTP_200_OK
            )
        
        # Red nedeni kontrolü
        reason = request.data.get('reason', '')
        if not reason:
            return Response(
                {"error": "Red nedeni belirtilmelidir"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            engine = WorkflowEngine(siparis.tedarik_surec_durumu, request.user)
            engine.reject_step(request.data)
            return Response(
                {"message": "Adım reddedildi"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def dosya_yukle(self, request, pk=None):
        """Siparişe birden fazla dosya yükler"""
        siparis = self.get_object()
        
        # Dosya kontrolü
        dosyalar = request.FILES.getlist('dosyalar')
        if not dosyalar:
            return Response(
                {"error": "En az bir dosya yüklenmelidir."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Her dosyayı kaydet
        for dosya in dosyalar:
            Dosya.objects.create(siparis=siparis, dosya=dosya,yukleyen=request.user)
        
        return Response(
            {"message": "Dosyalar başarıyla yüklendi."},
            status=status.HTTP_200_OK
        )

class SurecDurumuViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SurecDurumu.objects.all()
    serializer_class = SurecDurumuSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SurecDurumu.objects.all()
        
        user_department = getattr(user.profile, 'departman', None)
        
        if user_department:
            return SurecDurumu.objects.filter(
                models.Q(mevcut_adim__onaylayanlar=user) | 
                models.Q(mevcut_adim__departmanlar=user_department),
                is_completed=False
            ).distinct()
        else:
            return SurecDurumu.objects.filter(
                mevcut_adim__onaylayanlar=user,
                is_completed=False
            )
    
    @action(detail=True, methods=['get'])
    def yorumlar(self, request, pk=None):
        """Süreç durumuna ait yorumları adımlara göre gruplandırarak getirir"""
        surec_durumu = self.get_object()
        
        # Sadece bu süreç durumunun mevcut adımına ait yorumları getir
        yorumlar = SurecYorum.objects.filter(
            surec_durumu=surec_durumu,
            adim=surec_durumu.mevcut_adim
        ).order_by('-olusturma_tarihi')
        
        return Response({
            'adim': {
                'id': surec_durumu.mevcut_adim.id,
                'ad': surec_durumu.mevcut_adim.ad,
                'sira': surec_durumu.mevcut_adim.sira
            },
            'yorumlar': SurecYorumSerializer(yorumlar, many=True).data
        })
    
    @action(detail=True, methods=['get'])
    def tum_yorumlar(self, request, pk=None):
        """Süreç durumunun tüm adımlarına ait yorumları gruplandırarak getirir"""
        surec_durumu = self.get_object()
        adimlar = surec_durumu.surec.tedarik_adimlari.all()
        
        sonuc = []
        for adim in adimlar:
            yorumlar = SurecYorum.objects.filter(
                surec_durumu=surec_durumu,
                adim=adim
            ).order_by('-olusturma_tarihi')
            
            if yorumlar.exists():
                sonuc.append({
                    'adim': {
                        'id': adim.id,
                        'ad': adim.ad,
                        'sira': adim.sira
                    },
                    'yorumlar': SurecYorumSerializer(yorumlar, many=True).data
                })
        
        return Response(sonuc)
    
    @action(detail=True, methods=['post'])
    def yorum_ekle(self, request, pk=None):
        """Süreç durumunun mevcut adımına yorum ekler"""
        surec_durumu = self.get_object()
        yorum_metni = request.data.get('yorum')
        
        if not yorum_metni:
            return Response(
                {"error": "Yorum metni boş olamaz"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Yorum oluştur
        yorum = SurecYorum.objects.create(
            surec_durumu=surec_durumu,
            adim=surec_durumu.mevcut_adim,
            yazan=request.user,
            yorum=yorum_metni
        )
        
        # Dosya yükleme işlemi
        dosyalar = request.FILES.getlist('dosyalar', [])
        for dosya in dosyalar:
            dosya_obj = Dosya.objects.create(
                surec_durumu=surec_durumu,
                dosya=dosya,
                yukleyen=request.user
            )
            yorum.dosyalar.add(dosya_obj)
        
        return Response(SurecYorumSerializer(yorum).data)

class SurecYorumViewSet(viewsets.ModelViewSet):
    queryset = SurecYorum.objects.all()
    serializer_class = SurecYorumSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = SurecYorum.objects.all()
        surec_durumu_id = self.request.query_params.get('surec_durumu', None)
        adim_id = self.request.query_params.get('adim', None)
        
        # Kullanıcı yetkisi kontrolü
        user = self.request.user
        if not user.is_staff:
            user_department = getattr(user.profile, 'departman', None)
            if user_department:
                queryset = queryset.filter(
                    models.Q(surec_durumu__mevcut_adim__onaylayanlar=user) |
                    models.Q(surec_durumu__mevcut_adim__departmanlar=user_department) |
                    models.Q(yazan=user)
                ).distinct()
            else:
                queryset = queryset.filter(
                    models.Q(surec_durumu__mevcut_adim__onaylayanlar=user) |
                    models.Q(yazan=user)
                ).distinct()
        
        # Süreç durumu filtresi
        if surec_durumu_id:
            queryset = queryset.filter(surec_durumu_id=surec_durumu_id)
        
        # Adım filtresi
        if adim_id:
            queryset = queryset.filter(adim_id=adim_id)
        
        return queryset.order_by('-olusturma_tarihi')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['surec_durumu_id'] = self.request.query_params.get('surec_durumu')
        return context
    
    def perform_create(self, serializer):
        surec_durumu_id = self.request.data.get('surec_durumu')
        surec_durumu = get_object_or_404(SurecDurumu, id=surec_durumu_id)
        
        serializer.save(
            yazan=self.request.user,
            adim=surec_durumu.mevcut_adim
        )
    
    @action(detail=False, methods=['get'])
    def by_surec_durumu(self, request):
        """Belirli bir süreç durumuna ait yorumları adımlara göre gruplandırarak getirir"""
        surec_durumu_id = request.query_params.get('surec_durumu')
        if not surec_durumu_id:
            return Response(
                {"error": "Süreç durumu ID'si belirtilmelidir"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        surec_durumu = get_object_or_404(SurecDurumu, id=surec_durumu_id)
        adimlar = surec_durumu.surec.tedarik_adimlari.all()
        
        sonuc = []
        for adim in adimlar:
            yorumlar = self.get_queryset().filter(
                surec_durumu_id=surec_durumu_id,
                adim=adim
            )
            
            if yorumlar.exists():
                sonuc.append({
                    'adim': {
                        'id': adim.id,
                        'ad': adim.ad,
                        'sira': adim.sira
                    },
                    'yorumlar': SurecYorumSerializer(yorumlar, many=True).data
                })
        
        return Response(sonuc)
    
    @action(detail=True, methods=['post'])
    def dosya_ekle(self, request, pk=None):
        """Yoruma dosya ekler"""
        yorum = self.get_object()
        
        if yorum.yazan != request.user and not request.user.is_staff:
            return Response(
                {"error": "Bu yoruma dosya ekleme yetkiniz yok."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        dosyalar = request.FILES.getlist('dosyalar', [])
        if not dosyalar:
            return Response(
                {"error": "En az bir dosya yüklemelisiniz."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for dosya in dosyalar:
            dosya_obj = Dosya.objects.create(
                surec_durumu=yorum.surec_durumu,
                dosya=dosya,
                yukleyen=request.user
            )
            yorum.dosyalar.add(dosya_obj)
        
        return Response(SurecYorumSerializer(yorum).data)

class DepartmanViewSet(viewsets.ModelViewSet):
    queryset = Departman.objects.all()
    serializer_class = DepartmanSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

class GeriGondermeViewSet(viewsets.ModelViewSet):
    queryset = GeriGonderme.objects.all()
    serializer_class = GeriGondermeSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(geri_gonderen=self.request.user)

class DosyaViewSet(viewsets.ModelViewSet):
    queryset = Dosya.objects.all()
    serializer_class = DosyaSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(yukleyen=self.request.user)

class MeView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print("\n----Debug Bilgileri (MeView)----")
        print("Headers:", request.headers)
        print("Auth:", request.auth)
        print("User:", request.user)
        print("Is Authenticated:", request.user.is_authenticated)
        print("Method:", request.method)
        print("Path:", request.path)
        print("------------------------\n")

        user = request.user
        try:
            profile = user.profile
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'profile': {
                    'departman': profile.departman.ad if profile.departman else None,
                    'telefon': profile.telefon if hasattr(profile, 'telefon') else None,
                    'unvan': profile.unvan if hasattr(profile, 'unvan') else None,
                }
            })
        except Exception as e:
            print("Hata:", str(e))
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
            })

class ProjeViewSet(viewsets.ModelViewSet):
    queryset = Proje.objects.all()
    serializer_class = ProjeSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]