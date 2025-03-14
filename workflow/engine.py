from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from core.conditions.engine import ConditionEngine
from django.contrib.auth.models import User
from tedarik.models import SurecDurumu, Adim, GeriGonderme
from .models import Adim, SurecDurumu
import json
from django.utils import timezone

class WorkflowEngine:
    def __init__(self, surec_durumu, user):
        self.surec_durumu = surec_durumu
        self.user = user
        self.surec = surec_durumu.surec

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

    def process_step(self, data=None):
        """Mevcut adımı işler ve bir sonraki adıma geçer"""
        # Süreç durumu tamamlanmış mı kontrol et
        if self.surec_durumu.is_completed:
            raise Exception("Bu süreç zaten tamamlanmış")
        
        # Mevcut adım var mı kontrol et
        if not self.surec_durumu.mevcut_adim:
            # Eğer mevcut adım yoksa, ilk adımı ata
            try:
                # Önce tedarik_adimlari'nı dene
                if hasattr(self.surec, 'tedarik_adimlari'):
                    ilk_adim = self.surec.tedarik_adimlari.order_by('sira').first()
                # Sonra adimlar'ı dene
                elif hasattr(self.surec, 'adimlar'):
                    ilk_adim = self.surec.adimlar.order_by('sira').first()
                else:
                    raise Exception("Süreçte hiç adım bulunamadı")
                
                if ilk_adim:
                    self.surec_durumu.mevcut_adim = ilk_adim
                    self.surec_durumu.save()
                else:
                    raise Exception("Süreçte hiç adım bulunamadı")
            except Exception as e:
                raise Exception(f"İlk adım atanamadı: {str(e)}")
        
        # Kullanıcının yetkisi var mı kontrol et
        self._check_user_permission()
        
        # Adım koşullarını kontrol et
        if data:
            self._validate_step_conditions(data)
        
        # Mevcut adımı tamamlanan adımlara ekle
        mevcut_adim = self.surec_durumu.mevcut_adim
        self.surec_durumu.tamamlanan_adimlar.add(mevcut_adim)
        
        # Koşullu sonraki adımı kontrol et
        sonraki_adim = None
        
        # Eğer mevcut adımın sonraki adım koşulu varsa, koşullu yönlendirme yap
        if hasattr(mevcut_adim, 'sonraki_adim_kosulu') and mevcut_adim.sonraki_adim_kosulu:
            print(f"Sonraki adım koşulu bulundu: {mevcut_adim.sonraki_adim_kosulu}")
            sonraki_adim = self._get_conditional_next_step(mevcut_adim)
        
        # Koşullu yönlendirme yoksa veya başarısız olduysa, normal sıradaki adımı bul
        if not sonraki_adim:
            try:
                # Önce tedarik_adimlari'nı dene
                if hasattr(self.surec, 'tedarik_adimlari'):
                    sonraki_adim = self.surec.tedarik_adimlari.filter(
                        sira__gt=mevcut_adim.sira
                    ).order_by('sira').first()
                # Sonra adimlar'ı dene
                elif hasattr(self.surec, 'adimlar'):
                    sonraki_adim = self.surec.adimlar.filter(
                        sira__gt=mevcut_adim.sira
                    ).order_by('sira').first()
                else:
                    sonraki_adim = None
            except Exception as e:
                raise Exception(f"Sonraki adım bulunamadı: {str(e)}")
        
        if sonraki_adim:
            self.surec_durumu.mevcut_adim = sonraki_adim
            self.surec_durumu.son_islem_yapan = self.user
            self.surec_durumu.save()
            print(f"Sonraki adıma geçildi: {sonraki_adim.ad}")
        else:
            # Süreç tamamlandı
            self.surec_durumu.is_completed = True
            self.surec_durumu.mevcut_adim = None
            self.surec_durumu.son_islem_yapan = self.user
            self.surec_durumu.tamamlanma_tarihi = timezone.now()
            self.surec_durumu.save()
            print("Süreç tamamlandı")
            
            # Siparişi onayla
            siparis = self.surec_durumu.siparis
            siparis.durum = 'onaylandi'
            siparis.son_islem_yapan = self.user
            siparis.save()

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
        # Eğer mevcut adımın sonraki adım koşulu yoksa, None döndür
        if not current_step.sonraki_adim_kosulu:
            print("Sonraki adım koşulu bulunamadı")
            return None
        
        print(f"Sonraki adım koşulu değerlendiriliyor: {current_step.sonraki_adim_kosulu}")
        
        # Koşulları sırayla kontrol et
        for condition_item in current_step.sonraki_adim_kosulu.get('conditions', []):
            try:
                # Koşul değerlendirme motoru oluştur
                from core.conditions.engine import ConditionEngine
                
                context = {
                    'model': self.surec_durumu.siparis,
                    'user': self.user,
                    'step': current_step
                }
                
                condition_engine = ConditionEngine(context)
                condition = {
                    'field': condition_item.get('field'),
                    'operator': condition_item.get('operator'),
                    'value': condition_item.get('value')
                }
                
                # Koşul sağlanıyorsa, belirtilen adıma geç
                if condition_engine.evaluate(condition):
                    next_step_name = condition_item.get('next_step')
                    print(f"Koşul sağlandı, sonraki adım: {next_step_name}")
                    
                    if next_step_name:
                        # Adı belirtilen adımı bul
                        if hasattr(self.surec, 'tedarik_adimlari'):
                            next_step = self.surec.tedarik_adimlari.filter(ad=next_step_name).first()
                        else:
                            next_step = self.surec.adimlar.filter(ad=next_step_name).first()
                        
                        if next_step:
                            return next_step
            except Exception as e:
                print(f"Koşul değerlendirme hatası: {str(e)}")
        
        # Varsayılan sonraki adımı kontrol et
        default_next_step = current_step.sonraki_adim_kosulu.get('default_next_step')
        if default_next_step:
            print(f"Varsayılan sonraki adım: {default_next_step}")
            if hasattr(self.surec, 'tedarik_adimlari'):
                return self.surec.tedarik_adimlari.filter(ad=default_next_step).first()
            else:
                return self.surec.adimlar.filter(ad=default_next_step).first()
        
        print("Koşullu sonraki adım bulunamadı")
        return None

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

    def _check_user_permission(self):
        """Kullanıcının mevcut adımı işleme yetkisi olup olmadığını kontrol eder"""
        if not self.surec_durumu.mevcut_adim:
            raise Exception("İşlenecek adım bulunamadı")
        
        # Kullanıcı doğrudan onaylayıcı olarak atanmış mı?
        if self.surec_durumu.mevcut_adim.onaylayanlar.filter(id=self.user.id).exists():
            return True
        
        # Kullanıcının departmanı onaylayıcı olarak atanmış mı?
        try:
            user_department = getattr(self.user.profile, 'departman', None)
            if user_department and self.surec_durumu.mevcut_adim.departmanlar.filter(id=user_department.id).exists():
                return True
        except:
            pass
        
        # Admin kullanıcılar her zaman onaylayabilir
        if self.user.is_staff or self.user.is_superuser:
            return True
        
        raise Exception("Bu adımı onaylama yetkiniz yok")

    def _validate_step_conditions(self, data):
        """Adım koşullarını kontrol eder"""
        if not self.surec_durumu.mevcut_adim.kosul:
            return True  # Koşul yoksa, her zaman True döner
        
        try:
            # Koşul değerlendirme motoru oluştur
            from core.conditions.engine import ConditionEngine
            
            context = {
                'model': self.surec_durumu.siparis,
                'user': self.user,
                'data': data,
                'step': self.surec_durumu.mevcut_adim
            }
            
            condition_engine = ConditionEngine(context)
            result = condition_engine.evaluate(self.surec_durumu.mevcut_adim.kosul)
            
            if not result:
                raise Exception("Adım koşulları sağlanmıyor")
            
            return True
        except Exception as e:
            raise Exception(f"Koşul değerlendirme hatası: {str(e)}") 