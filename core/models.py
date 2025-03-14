from django.db import models
from django.contrib.auth.models import User

class Departman(models.Model):
    ad = models.CharField(max_length=255)
    aciklama = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.ad

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='core_profile')
    departman = models.ForeignKey(Departman, on_delete=models.SET_NULL, null=True, blank=True, related_name='core_calisanlar')
    
    def __str__(self):
        return f"{self.user.username} - {self.departman}"

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