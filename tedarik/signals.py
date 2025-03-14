from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, SatinAlmaSiparisi, SurecDurumu,Surec,Adim

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Yeni bir kullanıcı oluşturulduğunda otomatik olarak profil oluşturur.
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Kullanıcı güncellendiğinde profilini de günceller.
    """
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=SatinAlmaSiparisi)
def baslat_surec(sender, instance, created, **kwargs):
    """
    Yeni bir sipariş oluşturulduğunda otomatik olarak iş akışı başlatır.
    """
    # Eğer zaten bir süreç durumu varsa, işlem yapma
    try:
        surec_durumu = instance.tedarik_surec_durumu
        return
    except (SurecDurumu.DoesNotExist, AttributeError):
        pass

    # Eğer yeni oluşturulmuş bir sipariş ve onay süreci atanmışsa
    if created and instance.onay_sureci:
        try:
            # İlk adımı bul
            ilk_adim = instance.proje.surec.tedarik_adimlari.order_by('sira').first()
            
            if ilk_adim:
                # Yeni süreç durumu oluştur
                surec_durumu = SurecDurumu.objects.create(
                    siparis=instance,
                    surec=instance.onay_sureci,
                    mevcut_adim=ilk_adim
                )
                
                # Siparişin durumunu güncelle
                SatinAlmaSiparisi.objects.filter(id=instance.id).update(durum='onay_bekliyor')
        except Exception as e:
            print(f"Süreç başlatma hatası: {e}") 