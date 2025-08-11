from django.apps import AppConfig

class PerformanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.performance'
    verbose_name = 'Performance Monitoring'
    
    def ready(self):
        import apps.performance.signals