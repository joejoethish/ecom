"""
App configuration for the search app.
"""
from django.apps import AppConfig


class SearchConfig(AppConfig):
    """
    Configuration for the search app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.search'
    
    def ready(self):
        """
        Initialize app when Django starts.
        """
        # Import signals to register them
        import apps.search.signals