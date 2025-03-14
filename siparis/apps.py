from django.apps import AppConfig

class SiparisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'siparis'
    verbose_name = 'Satın Alma Siparişleri'

    def ready(self):
        import siparis.signals 