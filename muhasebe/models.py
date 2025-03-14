from django.db import models
from workflow.models import SurecDurumu

class Fatura(models.Model):
    DURUM_SECENEKLERI = [
        ('taslak', 'Taslak'),
        ('onay_bekliyor', 'Onay Bekliyor'),
        ('onaylandi', 'Onaylandı'),
        ('odendi', 'Ödendi'),
    ]
    
    siparis = models.ForeignKey('siparis.SatinAlmaSiparisi', on_delete=models.PROTECT)
    fatura_no = models.CharField(max_length=50)
    fatura_tarihi = models.DateField()
    vade_tarihi = models.DateField()
    toplam_tutar = models.DecimalField(max_digits=15, decimal_places=2)
    kdv_tutari = models.DecimalField(max_digits=15, decimal_places=2)
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='taslak')
    surec_durumu = models.OneToOneField(SurecDurumu, on_delete=models.SET_NULL, null=True) 