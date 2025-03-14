from django.apps import AppConfig


class TedarikConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tedarik"
    verbose_name = "Tedarik Yönetimi"

    def ready(self):
        import tedarik.signals
