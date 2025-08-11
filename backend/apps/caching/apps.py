from django.apps import AppConfig


class CachingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.caching'
    verbose_name = 'Advanced Caching System'

    def ready(self):
        import apps.caching.signals