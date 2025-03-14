from django.db import models
from django.contrib.auth.models import User
from tedarik.models import Proje, Surec, Urun

class MalzemeTalebi(models.Model):
    DURUM_SECENEKLERI = [
        ('taslak', 'Taslak'),
        ('onay_bekliyor', 'Onay Bekliyor'),
        ('onaylandi', 'Onaylandı'),
        ('reddedildi', 'Reddedildi'),
        ('revizyon_bekliyor', 'Revizyon Bekliyor'),
    ]
    
    olusturan = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='olusturulan_talepler'
    )
    proje = models.ForeignKey(
        Proje,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='malzeme_talepleri'
    )
    toplam_tutar = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='taslak')
    onay_sureci = models.ForeignKey(
        Surec,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='malzeme_talepleri'
    )
    son_islem_yapan = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='islem_yapilan_talepler'
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.olusturan} - {self.proje} - {self.toplam_tutar}"
    
    class Meta:
        verbose_name = 'Malzeme Talebi'
        verbose_name_plural = 'Malzeme Talepleri'
        ordering = ['-olusturma_tarihi']

class TalepKalemi(models.Model):
    talep = models.ForeignKey(
        MalzemeTalebi,
        on_delete=models.CASCADE,
        related_name='talep_kalemleri'
    )
    urun = models.ForeignKey(
        Urun,
        on_delete=models.CASCADE,
        related_name='talep_kalemleri'
    )
    miktar = models.IntegerField()
    birim_fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    toplam_fiyat = models.DecimalField(max_digits=15, decimal_places=2, blank=True)

    def save(self, *args, **kwargs):
        # Toplam fiyatı hesapla
        self.toplam_fiyat = self.miktar * self.birim_fiyat
        super().save(*args, **kwargs)
        
        # Talebin toplam tutarını güncelle
        talep = self.talep
        talep.toplam_tutar = talep.talep_kalemleri.aggregate(
            toplam=models.Sum('toplam_fiyat')
        )['toplam'] or 0
        talep.save()

    def __str__(self):
        return f"{self.urun.ad} - {self.miktar} adet"
    
    class Meta:
        verbose_name = 'Talep Kalemi'
        verbose_name_plural = 'Talep Kalemleri' 