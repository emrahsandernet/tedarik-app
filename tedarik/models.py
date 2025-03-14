from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.


class Departman(models.Model):
    ad = models.CharField(max_length=255)
    aciklama = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.ad

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    departman = models.ForeignKey(
        Departman,  # core.Departman yerine kendi Departman modelimizi kullanalım
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tedarik_calisanlar'  # related_name'i güncelleyelim
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.departman}"
    
    class Meta:
        verbose_name = 'Kullanıcı Profili'
        verbose_name_plural = 'Kullanıcı Profilleri'

class Urun(models.Model):
    ad = models.CharField(max_length=255)
    aciklama = models.TextField(blank=True, null=True)
    fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    stok = models.IntegerField()

    def __str__(self):
        return self.ad

class Tedarikci(models.Model):
    ad = models.CharField(max_length=255)
    adres = models.TextField(blank=True, null=True)
    telefon = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.ad

class Surec(models.Model):
    ad = models.CharField(max_length=255)
    aciklama = models.TextField()
    aktif = models.BooleanField(default=True)
    kosullar = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.ad

class Adim(models.Model):
    surec = models.ForeignKey(Surec, on_delete=models.CASCADE, related_name='tedarik_adimlari')
    ad = models.CharField(max_length=255)
    sira = models.IntegerField()
    kosul = models.JSONField(null=True, blank=True)
    onaylayanlar = models.ManyToManyField(
        User, 
        related_name='tedarik_onay_adimlari',
        blank=True
    )
    departmanlar = models.ManyToManyField(
        Departman, 
        related_name='tedarik_onay_adimlari',
        blank=True
    )
    sonraki_adim_kosulu = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.surec.ad} - {self.ad}"

class Proje(models.Model):
    ad = models.CharField(max_length=255)
    aciklama = models.TextField(blank=True, null=True)
    surec = models.ForeignKey(Surec, on_delete=models.CASCADE, related_name='proje_surecler')
    def __str__(self):
        return self.ad
    
class MalzemeTalep(models.Model):
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
        related_name='tedarik_olusturulan_siparisler'
    )
    
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='taslak')
    proje = models.ForeignKey(Proje, on_delete=models.SET_NULL, null=True, blank=True)
    son_islem_yapan = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tedarik_islem_yapilan_siparisler'
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    aciklama = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.olusturan} - {self.proje}"
    
    class Meta:
        verbose_name = 'Satin Alma Siparişi'
        verbose_name_plural = 'Satin Alma Siparişleri'
        ordering = ['-olusturma_tarihi'] 

class MalzemeKategori(models.Model):
    ad = models.CharField(max_length=255)
    aciklama = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.ad

class Malzeme(models.Model):
    ad = models.CharField(max_length=255)
    aciklama = models.TextField(blank=True, null=True)
    birim = models.CharField(max_length=255)
    stok = models.IntegerField(null=True, blank=True)
    kategori = models.ForeignKey(MalzemeKategori, on_delete=models.CASCADE, related_name='malzemeler')
    def __str__(self):
        return f"{self.ad} - {self.kategori} - {self.birim} - {self.stok}"

class MalzemeTalepSatir(models.Model):
    talep = models.ForeignKey(MalzemeTalep, on_delete=models.CASCADE, related_name='satirlar')
    malzeme = models.ForeignKey(Malzeme, on_delete=models.CASCADE, related_name='talep_satirlar')
    miktar = models.DecimalField(max_digits=10, decimal_places=2)
    

    def __str__(self):
        return f"{self.talep} - {self.malzeme} - {self.miktar}"

class SurecDurumu(models.Model):
    siparis = models.OneToOneField(
        MalzemeTalep, 
        on_delete=models.CASCADE, 
        related_name='tedarik_surec_durumu'
    )
    surec = models.ForeignKey(Surec, on_delete=models.CASCADE)
    mevcut_adim = models.ForeignKey(Adim, on_delete=models.SET_NULL, null=True)
    tamamlanan_adimlar = models.ManyToManyField(Adim, related_name='tamamlanan_durumlar')
    is_completed = models.BooleanField(default=False)
    notlar = models.TextField(blank=True, null=True)
    red_nedeni = models.TextField(blank=True, null=True)
    son_islem_yapan = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tedarik_islem_yapilan_durumlar'
    )
    baslangic_tarihi = models.DateTimeField(auto_now_add=True)
    tamamlanma_tarihi = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.siparis} - {self.mevcut_adim}"

class GeriGonderme(models.Model):
    surec_durumu = models.ForeignKey(
        SurecDurumu, 
        on_delete=models.CASCADE, 
        related_name='tedarik_geri_gondermeler'
    )
    red_nedeni = models.TextField()
    geri_gonderen = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='tedarik_geri_gondermeler'
    )
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.red_nedeni} - {self.geri_gonderen.username} - {self.tarih}"
    
    class Meta:
        verbose_name = 'Geri Gönderme'
        verbose_name_plural = 'Geri Göndermeler'

def surec_dosya_yolu(instance, filename):
    # Dosyaları süreç durumuna göre klasörlere ayır
    return f'surec_dosyalar/{instance.surec_durumu.id}/{filename}'

class Dosya(models.Model):
    surec_durumu = models.ForeignKey(
        SurecDurumu, 
        on_delete=models.CASCADE, 
        related_name='tedarik_dosyalar'
    )
    dosya = models.FileField(upload_to=surec_dosya_yolu)
    yukleyen = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='tedarik_dosyalar'
    )
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.dosya.name} - {self.yukleyen.username} - {self.tarih}"
    
    class Meta:
        verbose_name = 'Dosya'
        verbose_name_plural = 'Dosyalar'

class SurecYorum(models.Model):
    surec_durumu = models.ForeignKey(SurecDurumu, on_delete=models.CASCADE, related_name='yorumlar')
    adim = models.ForeignKey(Adim, on_delete=models.CASCADE, related_name='yorumlar')
    yazan = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    yorum = models.TextField()
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    dosyalar = models.ManyToManyField(Dosya, blank=True)
    
    class Meta:
        ordering = ['-olusturma_tarihi']
        verbose_name = 'Süreç Yorumu'
        verbose_name_plural = 'Süreç Yorumları'

    def __str__(self):
        return f"{self.yazan.username} - {self.adim.ad} - {self.olusturma_tarihi}"


