from django.db import models
from workflow.models import SurecDurumu

class Odeme(models.Model):
    DURUM_SECENEKLERI = [
        ('beklemede', 'Beklemede'),
        ('onay_bekliyor', 'Onay Bekliyor'),
        ('onaylandi', 'Onaylandı'),
        ('tamamlandi', 'Tamamlandı'),
    ]
    
    fatura = models.ForeignKey('muhasebe.Fatura', on_delete=models.PROTECT)
    odeme_tarihi = models.DateField()
    odeme_tutari = models.DecimalField(max_digits=15, decimal_places=2)
    odeme_yontemi = models.CharField(max_length=50)
    aciklama = models.TextField(null=True, blank=True)
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='beklemede')
    surec_durumu = models.OneToOneField(SurecDurumu, on_delete=models.SET_NULL, null=True) 