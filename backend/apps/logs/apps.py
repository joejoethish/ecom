"""
Django app configuration for logs application.
"""
from django.apps import AppConfig


class LogsConfig(AppConfig):
    """
    Configuration for the logs application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.logs'
    verbose_name = 'Logging and Monitoring'
    
    def ready(self):
        """
        Initialize the app when Django starts.
        """
        # Import signal handlers
        import apps.logs.signals  # noqa
        
        # Configure logging system
        # from apps.logs.config import configure_logging
        # configure_logging()
        
        # Start system monitoring if enabled
        from django.conf import settings
        if getattr(settings, 'SYSTEM_MONITORING_ENABLED', False):
            from backend.logs.monitoring import system_monitor
            system_monitor.start()
            
        # Start alert manager if enabled
        if getattr(settings, 'ALERT_MONITORING_ENABLED', False):
            from backend.logs.alerts import start_alert_manager
            start_alert_manager()