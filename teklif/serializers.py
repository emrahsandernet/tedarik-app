from rest_framework import serializers
from .models import Teklif, TeklifKalemi
from talep.serializers import MalzemeTalebiSerializer, TalepKalemiSerializer
from core.serializers import TedarikciSerializer
from workflow.serializers import SurecDurumuSerializer

class TeklifKalemiSerializer(serializers.ModelSerializer):
    talep_kalemi = TalepKalemiSerializer(read_only=True)
    
    class Meta:
        model = TeklifKalemi
        fields = '__all__'

class TeklifSerializer(serializers.ModelSerializer):
    talep = MalzemeTalebiSerializer(read_only=True)
    tedarikci = TedarikciSerializer(read_only=True)
    kalemler = TeklifKalemiSerializer(many=True, read_only=True)
    surec_durumu = SurecDurumuSerializer(read_only=True)
    
    class Meta:
        model = Teklif
        fields = '__all__'
        read_only_fields = ('durum',) 