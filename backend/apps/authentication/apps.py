"""
Authentication app configuration.
"""
from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    Configuration for the authentication app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = 'Authentication'

    def ready(self):
        """
        Import signals when the app is ready.
        """
        import apps.authentication.signals