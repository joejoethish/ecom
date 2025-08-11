from django.apps import AppConfig


class SystemSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.system_settings'
    verbose_name = 'System Settings'

    def ready(self):
        # Import signals if any
        pass