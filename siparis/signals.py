from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SatinAlmaSiparisi
from workflow.models import SurecDurumu

@receiver(post_save, sender=SatinAlmaSiparisi)
def create_workflow(sender, instance, created, **kwargs):
    """
    Yeni bir sipariş oluşturulduğunda otomatik olarak iş akışı başlatır.
    """
    if created and instance.onay_sureci and not instance.surec_durumu:
        # Yeni süreç durumu oluştur
        surec_durumu = SurecDurumu.objects.create(
            surec=instance.onay_sureci,
            mevcut_adim=instance.onay_sureci.adimlar.order_by('sira').first()
        )
        
        # Siparişe bağla
        instance.surec_durumu = surec_durumu
        instance.durum = 'onay_bekliyor'
        instance.save() 