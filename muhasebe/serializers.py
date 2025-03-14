from rest_framework import serializers
from .models import Fatura
from siparis.serializers import SatinAlmaSiparisiSerializer
from workflow.serializers import SurecDurumuSerializer

class FaturaSerializer(serializers.ModelSerializer):
    siparis = SatinAlmaSiparisiSerializer(read_only=True)
    surec_durumu = SurecDurumuSerializer(read_only=True)
    
    class Meta:
        model = Fatura
        fields = '__all__'
        read_only_fields = ('durum',) 