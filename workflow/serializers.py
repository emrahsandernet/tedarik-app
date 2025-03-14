from rest_framework import serializers
from tedarik.models import  Surec, Adim, SurecDurumu, GeriGonderme, Dosya
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class AdimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adim
        fields = '__all__'

class SurecSerializer(serializers.ModelSerializer):
    adimlar = AdimSerializer(many=True, read_only=True)
    
    class Meta:
        model = Surec
        fields = '__all__'

class SurecDurumuSerializer(serializers.ModelSerializer):
    surec = SurecSerializer(read_only=True)
    mevcut_adim = AdimSerializer(read_only=True)
    tamamlanan_adimlar = AdimSerializer(many=True, read_only=True)
    son_islem_yapan = UserSerializer(read_only=True)
    
    class Meta:
        model = SurecDurumu
        fields = '__all__'

class GeriGondermeSerializer(serializers.ModelSerializer):
    geri_gonderen = UserSerializer(read_only=True)
    
    class Meta:
        model = GeriGonderme
        fields = '__all__'
        read_only_fields = ('tarih',)

class DosyaSerializer(serializers.ModelSerializer):
    yukleyen = UserSerializer(read_only=True)
    
    class Meta:
        model = Dosya
        fields = '__all__'
        read_only_fields = ('tarih',) 