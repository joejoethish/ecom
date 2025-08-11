from django.apps import AppConfig


class MlAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ml_ai'
    verbose_name = 'Machine Learning and AI'

    def ready(self):
        import apps.ml_ai.signals