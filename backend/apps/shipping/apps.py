from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ShippingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shipping'
    verbose_name = _('Shipping')
    
    def ready(self):
        import apps.shipping.signals