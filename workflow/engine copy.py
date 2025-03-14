from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from core.conditions.engine import ConditionEngine
from django.contrib.auth.models import User
from tedarik.models import SurecDurumu, Adim, GeriGonderme
from .models import Adim, SurecDurumu
import json

class WorkflowEngine:
    def __init__(self, surec_durumu: SurecDurumu, user: User):
        self.surec_durumu = surec_durumu
        self.user = user
        self.siparis = surec_durumu.siparis

    def can_process_step(self) -> bool:
        """
        Kullanıcının mevcut adımı işleyip işleyemeyeceğini kontrol eder
        """
        if not self.surec_durumu.mevcut_adim:
            return False
            
        # Kullanıcı doğrudan onaylayıcı olarak atanmış mı?
        if self.user in self.surec_durumu.mevcut_adim.onaylayanlar.all():
            return True
            
        # Kullanıcının departmanı onaylayıcı olarak atanmış mı?
        user_department = getattr(self.user.profile, 'departman', None)
        if user_department and user_department in self.surec_durumu.mevcut_adim.departmanlar.all():
            return True
            
        return False

    def process_step(self, data: dict) -> None:
        """
        Mevcut adımı işler ve bir sonraki adıma geçer
        """
        if not self.can_process_step():
            raise Exception("Bu adımı onaylama yetkiniz yok.")
            
        # Mevcut adımı tamamlanan adımlara ekle
        self.surec_durumu.tamamlanan_adimlar.add(self.surec_durumu.mevcut_adim)
        
        # Sonraki adımı bul
        next_step = self._get_next_step()
        
        # Son adım mı kontrol et
        if not next_step:
            self.surec_durumu.is_completed = True
            self.surec_durumu.mevcut_adim = None
            self.siparis.durum = 'onaylandi'
        else:
            self.surec_durumu.mevcut_adim = next_step
            
        # Son işlem yapan kullanıcıyı güncelle
        self.surec_durumu.son_islem_yapan = self.user
        self.siparis.son_islem_yapan = self.user
        
        # Değişiklikleri kaydet
        self.surec_durumu.save()
        self.siparis.save()

    def reject_step(self, data: dict) -> None:
        """
        Mevcut adımı reddeder
        """
        if not self.can_process_step():
            raise Exception("Bu adımı reddetme yetkiniz yok.")
            
        # Red nedenini kaydet
        reason = data.get('reason', '')
        if not reason:
            raise Exception("Red nedeni belirtilmelidir.")
            
        # Geri gönderme kaydı oluştur
        GeriGonderme.objects.create(
            surec_durumu=self.surec_durumu,
            red_nedeni=reason,
            geri_gonderen=self.user
        )
        
        # Siparişi güncelle
        self.siparis.durum = 'reddedildi'
        self.siparis.red_nedeni = reason
        self.siparis.son_islem_yapan = self.user
        self.siparis.save()
        
        # Süreç durumunu güncelle
        self.surec_durumu.red_nedeni = reason
        self.surec_durumu.son_islem_yapan = self.user
        self.surec_durumu.save()

    def _get_next_step(self) -> Adim:
        """
        Sıradaki adımı döndürür
        """
        current_step = self.surec_durumu.mevcut_adim
        if not current_step:
            return None
            
        # Sonraki adımı bul
        next_steps = self.surec_durumu.surec.adimlar.filter(
            sira__gt=current_step.sira
        ).order_by('sira')
        
        return next_steps.first() if next_steps.exists() else None

    def _check_approvers(self, step):
        """Kullanıcının bu adımı onaylama yetkisi olup olmadığını kontrol eder"""
        # Kullanıcı doğrudan onaylayıcı olarak atanmış mı?
        if step.onaylayanlar.filter(id=self.user.id).exists():
            return True
        
        # Kullanıcının departmanı onaylayıcı olarak atanmış mı?
        user_department = getattr(getattr(self.user, 'profile', None), 'departman', None)
        if user_department and step.departmanlar.filter(id=user_department.id).exists():
            return True
        
        # Admin kullanıcılar her zaman onaylayabilir
        if self.user.is_staff or self.user.is_superuser:
            return True
        
        return False
    
    def _evaluate_step_conditions(self, step):
        """Adımın koşullarını değerlendirir"""
        if not step.kosul:
            return True  # Koşul yoksa, her zaman True döner
        
        # İlgili modeli belirle
        related_model = self._get_related_model()
        
        # Koşul değerlendirme motoru oluştur
        context = {
            'model': related_model,
            'user': self.user,
            'step': step
        }
        
        condition_engine = ConditionEngine(context)
        return condition_engine.evaluate(step.kosul)
    
    def _get_related_model(self):
        """SurecDurumu ile ilişkili modeli döndürür"""
        # İlişkili modeli bul
        for field in self.surec_durumu._meta.get_fields():
            if field.one_to_one and field.related_model != self.surec_durumu.__class__:
                try:
                    return getattr(self.surec_durumu, field.name)
                except:
                    pass
        return None
    
    def _move_to_next_step(self):
        """Bir sonraki adıma geçer"""
        current_step = self.surec_durumu.mevcut_adim
        
        # Koşullu atama için özel kontrol
        next_step = self._get_conditional_next_step(current_step)
        
        if next_step:
            # Mevcut adımı tamamlanan adımlara ekle
            self.surec_durumu.tamamlanan_adimlar.add(current_step)
            
            # Bir sonraki adıma geç
            self.surec_durumu.mevcut_adim = next_step
            self.surec_durumu.save()
        else:
            # Eğer bir sonraki adım yoksa, süreci tamamla
            self.surec_durumu.is_completed = True
            self.surec_durumu.save()
            
            # İlişkili modelin durumunu güncelle
            related_model = self._get_related_model()
            if related_model and hasattr(related_model, 'durum'):
                related_model.durum = 'onaylandi'
                related_model.save()
    
    def _get_conditional_next_step(self, current_step):
        """Koşullara göre bir sonraki adımı belirler"""
        # Eğer mevcut adımın sonraki adım koşulu yoksa, normal sıradaki adımı döndür
        if not current_step.sonraki_adim_kosulu:
            return self._get_next_step()
        
        # İlişkili modeli belirle
        related_model = self._get_related_model()
        
        # Koşul değerlendirme motoru oluştur
        context = {
            'model': related_model,
            'user': self.user,
            'step': current_step
        }
        
        # Koşulları sırayla kontrol et
        for condition_item in current_step.sonraki_adim_kosulu.get('conditions', []):
            try:
                # Koşulu değerlendir
                condition_engine = ConditionEngine(context)
                condition = {
                    'field': condition_item.get('field'),
                    'operator': condition_item.get('operator'),
                    'value': condition_item.get('value')
                }
                
                # Koşul sağlanıyorsa, belirtilen adıma geç
                if condition_engine.evaluate(condition):
                    next_step_name = condition_item.get('next_step')
                    if next_step_name:
                        # Adı belirtilen adımı bul
                        next_step = Adim.objects.filter(
                            surec=self.surec_durumu.surec,
                            ad=next_step_name
                        ).first()
                        
                        if next_step:
                            return next_step
            except Exception as e:
                print(f"Error evaluating next step condition: {str(e)}")
        
        # Hiçbir koşul sağlanmadıysa, normal sıradaki adımı döndür
        return self._get_next_step()

    def _send_rejection_notification(self, reason, return_step):
        """Siparişi oluşturan kişiye red bildirimi gönderir"""
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        context = {
            'user': self.surec_durumu.olusturan,
            'order': self.surec_durumu,
            'reason': reason,
            'rejector': self.user,
            'return_step': return_step,
            'app_url': settings.APP_URL if hasattr(settings, 'APP_URL') else 'http://localhost:8000'
        }
        
        html_message = render_to_string('workflow/email/rejection_notification.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=f'Sipariş Reddedildi: {self.surec_durumu}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.surec_durumu.olusturan.email],
            html_message=html_message,
            fail_silently=True
        ) 