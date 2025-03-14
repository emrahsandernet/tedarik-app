from django.apps import AppConfig

class WorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workflow'
    verbose_name = 'İş Akışı Yönetimi'

    def ready(self):
        # Geçici olarak devre dışı bırakıldı
        # import workflow.signals
        pass 