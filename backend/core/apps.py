"""
Core app configuration
"""
import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'
    
    def ready(self):
        """Initialize core services when Django starts"""
        # Import signal handlers
        try:
            from . import signals  # noqa
        except ImportError:
            pass
        
        # Start replica monitoring if enabled
        if getattr(settings, 'REPLICA_MONITORING_ENABLED', True):
            self._start_replica_monitoring()
        
        # Initialize connection pool monitoring if enabled
        if getattr(settings, 'CONNECTION_MONITORING_ENABLED', False):
            self._start_connection_monitoring()
    
    def _start_replica_monitoring(self):
        """Start replica health monitoring"""
        try:
            from .replica_health_monitor import start_replica_monitoring
            start_replica_monitoring()
            logger.info("Replica health monitoring started")
        except Exception as e:
            logger.error(f"Failed to start replica monitoring: {e}")
    
    def _start_connection_monitoring(self):
        """Start connection pool monitoring"""
        try:
            from .connection_pool_manager import start_connection_monitoring
            start_connection_monitoring()
            logger.info("Connection pool monitoring started")
        except Exception as e:
            logger.error(f"Failed to start connection monitoring: {e}")