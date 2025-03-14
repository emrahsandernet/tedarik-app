from rest_framework import serializers
from .models import Odeme
from muhasebe.serializers import FaturaSerializer
from workflow.serializers import SurecDurumuSerializer

class OdemeSerializer(serializers.ModelSerializer):
    fatura = FaturaSerializer(read_only=True)
    surec_durumu = SurecDurumuSerializer(read_only=True)
    
    class Meta:
        model = Odeme
        fields = '__all__'
        read_only_fields = ('durum',) 