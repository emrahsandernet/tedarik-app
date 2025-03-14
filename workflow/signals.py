# Geçici olarak devre dışı bırakıldı
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from tedarik.models import OnayDurumu, SatinAlmaSiparisi
# 
# @receiver(post_save, sender=OnayDurumu)
# def update_siparis_status(sender, instance, created, **kwargs):
#     # Signal işlemleri...
#     pass

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from workflow.models import SurecDurumu

# Sistem içi bildirim fonksiyonu (isteğe bağlı)
def send_system_notification(approval_instance, user):
    """
    Belirtilen kullanıcıya sistem içi bildirim gönderir.
    """
    # Burada sistem içi bildirim mantığınızı uygulayabilirsiniz
    # Örneğin, bir Notification modeli oluşturup kaydetme
    pass 

@receiver(post_save, sender=SurecDurumu)
def update_related_model_status(sender, instance, created, **kwargs):
    # İlişkili modeli bul
    related_model = None
    for field in instance._meta.get_fields():
        if field.one_to_one and field.related_model != instance.__class__:
            try:
                related_model = getattr(instance, field.name)
                if related_model and hasattr(related_model, 'durum'):
                    if instance.is_completed:
                        related_model.durum = 'onaylandi'
                    else:
                        related_model.durum = 'onay_bekliyor'
                    related_model.save()
                    break
            except:
                pass 