from rest_framework import serializers
from .models import SatinAlmaSiparisi
from core.serializers import TedarikciSerializer
from workflow.serializers import SurecSerializer, SurecDurumuSerializer
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class SatinAlmaSiparisiCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SatinAlmaSiparisi
        fields = ('tedarikci', 'toplam_tutar', 'onay_sureci')

    def create(self, validated_data):
        # Kullanıcıyı request'ten al
        user = self.context['request'].user
        validated_data['olusturan'] = user
        return super().create(validated_data)

class SatinAlmaSiparisiSerializer(serializers.ModelSerializer):
    tedarikci = TedarikciSerializer(read_only=True)
    onay_sureci = SurecSerializer(read_only=True)
    surec_durumu = SurecDurumuSerializer(read_only=True)
    olusturan = UserSerializer(read_only=True)
    son_islem_yapan = UserSerializer(read_only=True)
    
    class Meta:
        model = SatinAlmaSiparisi
        fields = '__all__'
        read_only_fields = ('durum', 'red_nedeni', 'son_islem_yapan')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['olusturan'] = user
        return super().create(validated_data) 