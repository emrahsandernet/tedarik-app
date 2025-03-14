from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from workflow.models import SurecDurumu

class SatinAlmaSiparisi(models.Model):
    DURUM_SECENEKLERI = [
        ('taslak', 'Taslak'),
        ('onay_bekliyor', 'Onay Bekliyor'),
        ('onaylandi', 'Onaylandı'),
        ('reddedildi', 'Reddedildi'),
        ('revizyon_bekliyor', 'Revizyon Bekliyor'),
    ]
    
    olusturan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='olusturulan_siparisler')
    tedarikci = models.ForeignKey('core.Tedarikci', on_delete=models.CASCADE)
    toplam_tutar = models.DecimalField(max_digits=15, decimal_places=2)
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='taslak')
    onay_sureci = models.ForeignKey('workflow.Surec', on_delete=models.SET_NULL, null=True, blank=True)
    surec_durumu = GenericRelation(SurecDurumu)
    red_nedeni = models.TextField(blank=True, null=True)
    son_islem_yapan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='islem_yapilan_siparisler')
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.olusturan} - {self.tedarikci} - {self.toplam_tutar}"

    class Meta:
        verbose_name = 'Satın Alma Siparişi'
        verbose_name_plural = 'Satın Alma Siparişleri'
        ordering = ['-olusturma_tarihi'] 