from django.apps import AppConfig


class DebuggingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.debugging"
    verbose_name = "E2E Workflow Debugging System"
    
    def ready(self):
        """Initialize debugging system when Django starts"""
        try:
            from . import signals  # Import signals when app is ready
            from . import websocket_signals  # Import WebSocket signals
        except ImportError:
            pass
