from django.db import models
from django.contrib.auth.models import User
from workflow.models import SurecDurumu

class MalzemeTalebi(models.Model):
    DURUM_SECENEKLERI = [
        ('taslak', 'Taslak'),
        ('onay_bekliyor', 'Onay Bekliyor'),
        ('onaylandi', 'Onaylandı'),
        ('reddedildi', 'Reddedildi'),
    ]
    
    talep_eden = models.ForeignKey(User, on_delete=models.PROTECT)
    departman = models.ForeignKey('core.Departman', on_delete=models.PROTECT)
    talep_tarihi = models.DateTimeField(auto_now_add=True)
    teslim_tarihi = models.DateField()
    aciklama = models.TextField()
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='taslak')
    surec_durumu = models.OneToOneField(SurecDurumu, on_delete=models.SET_NULL, null=True)

class TalepKalemi(models.Model):
    talep = models.ForeignKey(MalzemeTalebi, on_delete=models.CASCADE, related_name='kalemler')
    urun = models.ForeignKey('core.Urun', on_delete=models.PROTECT)
    miktar = models.DecimalField(max_digits=10, decimal_places=2)
    birim = models.CharField(max_length=50)
    aciklama = models.TextField(null=True, blank=True) 