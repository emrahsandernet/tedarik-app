from rest_framework import serializers
from .models import MalzemeTalebi, TalepKalemi
from tedarik.serializers import ProjeSerializer, SurecSerializer, UrunSerializer
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class TalepKalemiSerializer(serializers.ModelSerializer):
    urun = UrunSerializer(read_only=True)
    urun_id = serializers.PrimaryKeyRelatedField(
        queryset=Urun.objects.all(),
        write_only=True,
        source='urun'
    )
    
    class Meta:
        model = TalepKalemi
        fields = ['id', 'urun', 'urun_id', 'miktar', 'birim_fiyat', 'toplam_fiyat']

class BasitMalzemeTalepSerializer(serializers.ModelSerializer):
    olusturan = UserSerializer(read_only=True)
    proje = ProjeSerializer(read_only=True)
    onay_sureci = SurecSerializer(read_only=True)
    son_islem_yapan = UserSerializer(read_only=True)
    malzemeler = TalepKalemiSerializer(source='talep_kalemleri', many=True, read_only=True)
    
    class Meta:
        model = MalzemeTalebi
        fields = [
            'id', 'olusturan', 'proje', 'toplam_tutar', 'durum',
            'onay_sureci', 'son_islem_yapan', 'malzemeler',
            'olusturma_tarihi', 'guncelleme_tarihi'
        ]

class DetayliMalzemeTalepSerializer(BasitMalzemeTalepSerializer):
    malzemeler = TalepKalemiSerializer(source='talep_kalemleri', many=True)
    
    def create(self, validated_data):
        malzemeler_data = validated_data.pop('talep_kalemleri', [])
        talep = MalzemeTalebi.objects.create(**validated_data)
        
        for malzeme_data in malzemeler_data:
            TalepKalemi.objects.create(talep=talep, **malzeme_data)
        
        return talep
    
    def update(self, instance, validated_data):
        malzemeler_data = validated_data.pop('talep_kalemleri', [])
        
        # Mevcut talep bilgilerini güncelle
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mevcut malzemeleri temizle
        instance.talep_kalemleri.all().delete()
        
        # Yeni malzemeleri ekle
        for malzeme_data in malzemeler_data:
            TalepKalemi.objects.create(talep=instance, **malzeme_data)
        
        return instance 