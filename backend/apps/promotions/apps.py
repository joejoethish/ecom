"""
Promotions app configuration
"""
from django.apps import AppConfig


class PromotionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.promotions'
    verbose_name = 'Promotions and Coupons'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import apps.promotions.signals
        except ImportError:
            pass