from django.apps import AppConfig

class CuposConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cupos"

    def ready(self):
        import cupos.signals
