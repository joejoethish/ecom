from django.apps import AppConfig


class ComplianceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.compliance'
    verbose_name = 'Compliance Management'
    
    def ready(self):
        # Import signals to ensure they are registered
        import backend.apps.compliance.signals