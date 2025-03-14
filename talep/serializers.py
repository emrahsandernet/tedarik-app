from rest_framework import serializers
from .models import MalzemeTalebi, TalepKalemi
from core.serializers import UserSerializer, DepartmanSerializer, UrunSerializer
from workflow.serializers import SurecDurumuSerializer

class TalepKalemiSerializer(serializers.ModelSerializer):
    urun = UrunSerializer(read_only=True)
    
    class Meta:
        model = TalepKalemi
        fields = '__all__'

class MalzemeTalebiSerializer(serializers.ModelSerializer):
    talep_eden = UserSerializer(read_only=True)
    departman = DepartmanSerializer(read_only=True)
    kalemler = TalepKalemiSerializer(many=True, read_only=True)
    surec_durumu = SurecDurumuSerializer(read_only=True)
    
    class Meta:
        model = MalzemeTalebi
        fields = '__all__'
        read_only_fields = ('durum',)
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['talep_eden'] = user
        return super().create(validated_data) 