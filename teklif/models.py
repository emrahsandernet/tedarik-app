from django.db import models
from workflow.models import SurecDurumu

class Teklif(models.Model):
    DURUM_SECENEKLERI = [
        ('beklemede', 'Beklemede'),
        ('degerlendirildi', 'Değerlendirildi'),
        ('kabul_edildi', 'Kabul Edildi'),
        ('reddedildi', 'Reddedildi'),
    ]
    
    talep = models.ForeignKey('talep.MalzemeTalebi', on_delete=models.PROTECT)
    tedarikci = models.ForeignKey('core.Tedarikci', on_delete=models.PROTECT)
    teklif_tarihi = models.DateTimeField(auto_now_add=True)
    gecerlilik_tarihi = models.DateField()
    toplam_tutar = models.DecimalField(max_digits=15, decimal_places=2)
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='beklemede')
    surec_durumu = models.OneToOneField(SurecDurumu, on_delete=models.SET_NULL, null=True)

class TeklifKalemi(models.Model):
    teklif = models.ForeignKey(Teklif, on_delete=models.CASCADE, related_name='kalemler')
    talep_kalemi = models.ForeignKey('talep.TalepKalemi', on_delete=models.PROTECT)
    birim_fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    teslimat_suresi = models.IntegerField(help_text='Gün cinsinden') 