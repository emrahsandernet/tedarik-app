from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType



class Surec(models.Model):
    ad = models.CharField(max_length=255)
    aciklama = models.TextField(blank=True, null=True)
    aktif = models.BooleanField(default=True)
    kosullar = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.tip.ad} - {self.ad}"
    
    class Meta:
        verbose_name = 'Süreç'
        verbose_name_plural = 'Süreçler'

class Adim(models.Model):
    surec = models.ForeignKey(Surec, on_delete=models.CASCADE, related_name='adimlar')
    ad = models.CharField(max_length=255)
    sira = models.IntegerField()
    kosul = models.JSONField(null=True, blank=True)
    onaylayanlar = models.ManyToManyField(User, related_name='onay_adimlari', blank=True)
    departmanlar = models.ManyToManyField('core.Departman', related_name='onay_adimlari', blank=True)
    sonraki_adim_kosulu = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.surec.ad} - {self.ad}"
    
    class Meta:
        verbose_name = 'Adım'
        verbose_name_plural = 'Adımlar'
        ordering = ['surec', 'sira']

class SurecDurumu(models.Model):
    surec = models.ForeignKey(Surec, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    ilgili_nesne = GenericForeignKey('content_type', 'object_id')
    mevcut_adim = models.ForeignKey(Adim, on_delete=models.SET_NULL, null=True)
    tamamlanan_adimlar = models.ManyToManyField(Adim, related_name='tamamlanan_durumlar')
    is_completed = models.BooleanField(default=False)
    notlar = models.TextField(blank=True, null=True)
    red_nedeni = models.TextField(blank=True, null=True)
    son_islem_yapan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='islem_yapilan_durumlar')
    baslangic_tarihi = models.DateTimeField(auto_now_add=True)
    tamamlanma_tarihi = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.surec} - {self.mevcut_adim}"
    
    class Meta:
        verbose_name = 'Süreç Durumu'
        verbose_name_plural = 'Süreç Durumları'

class GeriGonderme(models.Model):
    surec_durumu = models.ForeignKey(SurecDurumu, on_delete=models.CASCADE, related_name='geri_gondermeler')
    red_nedeni = models.TextField()
    geri_gonderen = models.ForeignKey(User, on_delete=models.CASCADE)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.red_nedeni} - {self.geri_gonderen.username} - {self.tarih}"
    
    class Meta:
        verbose_name = 'Geri Gönderme'
        verbose_name_plural = 'Geri Göndermeler'

class Dosya(models.Model):
    surec_durumu = models.ForeignKey(SurecDurumu, on_delete=models.CASCADE, related_name='dosyalar')
    dosya = models.FileField(upload_to='surec_dosyalar/')
    yukleyen = models.ForeignKey(User, on_delete=models.CASCADE)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.dosya.name} - {self.yukleyen.username} - {self.tarih}"
    
    class Meta:
        verbose_name = 'Dosya'
        verbose_name_plural = 'Dosyalar' 