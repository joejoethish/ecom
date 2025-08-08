from django.apps import AppConfig


class CustomerAnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.customer_analytics'
    verbose_name = 'Customer Analytics'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import apps.customer_analytics.signals
        except ImportError:
            pass