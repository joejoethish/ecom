from django.apps import AppConfig


class DocumentationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documentation'
    verbose_name = 'Documentation System'

    def ready(self):
        import apps.documentation.signals