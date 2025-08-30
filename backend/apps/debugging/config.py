"""
Configuration management for the E2E Workflow Debugging System.
"""
import os
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
from .models import DebugConfiguration


class DebuggingConfig:
    """Centralized configuration management for debugging system"""
    
    _instance = None
    _config_cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from Django settings and database"""
        # Load base configuration from settings
        self._config_cache = {
            'debugging_system': getattr(settings, 'DEBUGGING_SYSTEM', {}),
            'performance_monitoring': getattr(settings, 'PERFORMANCE_MONITORING', {}),
            'workflow_tracing': getattr(settings, 'WORKFLOW_TRACING', {}),
            'error_tracking': getattr(settings, 'ERROR_TRACKING', {}),
            'route_discovery': getattr(settings, 'ROUTE_DISCOVERY', {}),
            'api_validation': getattr(settings, 'API_VALIDATION', {}),
            'database_monitoring': getattr(settings, 'DATABASE_MONITORING', {}),
            'debugging_dashboard': getattr(settings, 'DEBUGGING_DASHBOARD', {}),
            'debugging_alerts': getattr(settings, 'DEBUGGING_ALERTS', {}),
            'debugging_security': getattr(settings, 'DEBUGGING_SECURITY', {}),
        }
        
        # Override with database configuration if available
        try:
            db_configs = DebugConfiguration.objects.filter(enabled=True)
            for config in db_configs:
                self._config_cache[config.name] = config.config_data
        except Exception:
            # Database might not be available during initial setup
            pass
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Get configuration value"""
        cache_key = f"debug_config_{section}_{key}" if key else f"debug_config_{section}"
        
        # Try cache first
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value
        
        # Get from configuration
        section_config = self._config_cache.get(section, {})
        
        if key is None:
            value = section_config
        else:
            value = section_config.get(key, default)
        
        # Cache the value for 5 minutes
        cache.set(cache_key, value, 300)
        return value
    
    def set(self, section: str, key: str, value: Any, persist: bool = False) -> None:
        """Set configuration value"""
        if section not in self._config_cache:
            self._config_cache[section] = {}
        
        self._config_cache[section][key] = value
        
        # Clear cache
        cache_key = f"debug_config_{section}_{key}"
        cache.delete(cache_key)
        
        # Persist to database if requested
        if persist:
            try:
                config_obj, created = DebugConfiguration.objects.get_or_create(
                    name=section,
                    defaults={
                        'config_type': 'runtime_setting',
                        'config_data': self._config_cache[section],
                        'enabled': True
                    }
                )
                if not created:
                    config_obj.config_data = self._config_cache[section]
                    config_obj.save()
            except Exception as e:
                # Log error but don't fail
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to persist configuration: {e}")
    
    def is_enabled(self, feature: str) -> bool:
        """Check if a debugging feature is enabled"""
        return self.get('debugging_system', feature, False)
    
    def get_performance_threshold(self, metric: str, level: str = 'warning') -> Optional[float]:
        """Get performance threshold for a metric"""
        thresholds = self.get('performance_monitoring', 'ALERT_THRESHOLDS', {})
        threshold_key = f"{metric}_{level}"
        return thresholds.get(threshold_key)
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get dashboard configuration"""
        return self.get('debugging_dashboard', default={})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.get('debugging_security', default={})
    
    def reload(self) -> None:
        """Reload configuration from settings and database"""
        self._config_cache.clear()
        cache.clear()
        self._load_configuration()
    
    def get_environment_config(self) -> str:
        """Get current environment configuration"""
        if settings.DEBUG:
            return 'development'
        elif 'test' in os.environ.get('DJANGO_SETTINGS_MODULE', ''):
            return 'testing'
        else:
            return 'production'


# Global configuration instance
config = DebuggingConfig()


class FeatureFlags:
    """Feature flags for debugging system components"""
    
    @staticmethod
    def is_performance_monitoring_enabled() -> bool:
        return config.is_enabled('PERFORMANCE_MONITORING_ENABLED')
    
    @staticmethod
    def is_workflow_tracing_enabled() -> bool:
        return config.is_enabled('WORKFLOW_TRACING_ENABLED')
    
    @staticmethod
    def is_error_tracking_enabled() -> bool:
        return config.is_enabled('ERROR_TRACKING_ENABLED')
    
    @staticmethod
    def is_route_discovery_enabled() -> bool:
        return config.is_enabled('ROUTE_DISCOVERY_ENABLED')
    
    @staticmethod
    def is_api_validation_enabled() -> bool:
        return config.is_enabled('API_VALIDATION_ENABLED')
    
    @staticmethod
    def is_database_monitoring_enabled() -> bool:
        return config.is_enabled('DATABASE_MONITORING_ENABLED')
    
    @staticmethod
    def is_dashboard_enabled() -> bool:
        return config.get('debugging_dashboard', 'ENABLED', False)
    
    @staticmethod
    def is_real_time_updates_enabled() -> bool:
        return config.get('debugging_dashboard', 'REAL_TIME_UPDATES', False)
    
    @staticmethod
    def is_websocket_enabled() -> bool:
        return config.get('debugging_dashboard', 'WEBSOCKET_ENABLED', False)


class ConfigValidator:
    """Validate debugging system configuration"""
    
    @staticmethod
    def validate_configuration() -> Dict[str, Any]:
        """Validate current configuration and return validation results"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check required settings
        required_settings = [
            ('debugging_system', 'ENABLED'),
            ('performance_monitoring', 'ALERT_THRESHOLDS'),
            ('debugging_dashboard', 'ENABLED'),
        ]
        
        for section, key in required_settings:
            value = config.get(section, key)
            if value is None:
                results['errors'].append(f"Missing required setting: {section}.{key}")
                results['valid'] = False
        
        # Check performance thresholds
        thresholds = config.get('performance_monitoring', 'ALERT_THRESHOLDS', {})
        for metric in ['api_response_time', 'database_query_time', 'memory_usage', 'error_rate']:
            warning_key = f"{metric}_warning"
            critical_key = f"{metric}_critical"
            
            warning_threshold = thresholds.get(warning_key)
            critical_threshold = thresholds.get(critical_key)
            
            if warning_threshold is None or critical_threshold is None:
                results['warnings'].append(f"Missing thresholds for {metric}")
            elif warning_threshold >= critical_threshold:
                results['errors'].append(f"Warning threshold for {metric} must be less than critical threshold")
                results['valid'] = False
        
        # Check environment-specific recommendations
        env = config.get_environment_config()
        
        if env == 'production':
            if config.is_enabled('WORKFLOW_TRACING_ENABLED'):
                results['recommendations'].append("Consider disabling workflow tracing in production for better performance")
            
            if config.is_enabled('ROUTE_DISCOVERY_ENABLED'):
                results['recommendations'].append("Consider disabling route discovery in production")
            
            if not config.get('debugging_security', 'API_KEY_REQUIRED', False):
                results['warnings'].append("API key authentication is recommended for production")
        
        elif env == 'development':
            if not config.is_enabled('PERFORMANCE_MONITORING_ENABLED'):
                results['recommendations'].append("Enable performance monitoring in development for better debugging")
        
        return results
    
    @staticmethod
    def get_configuration_summary() -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'environment': config.get_environment_config(),
            'enabled_features': {
                'performance_monitoring': FeatureFlags.is_performance_monitoring_enabled(),
                'workflow_tracing': FeatureFlags.is_workflow_tracing_enabled(),
                'error_tracking': FeatureFlags.is_error_tracking_enabled(),
                'route_discovery': FeatureFlags.is_route_discovery_enabled(),
                'api_validation': FeatureFlags.is_api_validation_enabled(),
                'database_monitoring': FeatureFlags.is_database_monitoring_enabled(),
                'dashboard': FeatureFlags.is_dashboard_enabled(),
                'real_time_updates': FeatureFlags.is_real_time_updates_enabled(),
                'websocket': FeatureFlags.is_websocket_enabled(),
            },
            'performance_thresholds': config.get('performance_monitoring', 'ALERT_THRESHOLDS', {}),
            'dashboard_config': config.get_dashboard_config(),
            'security_config': config.get_security_config(),
        }