from django.core.management.base import BaseCommand
from apps.debugging.models import DebugConfiguration, PerformanceThreshold


class Command(BaseCommand):
    help = 'Set up default debugging system configuration and thresholds'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up debugging system defaults...')
        
        # Create default debug configurations
        default_configs = [
            {
                'name': 'tracing_enabled',
                'config_type': 'tracing_enabled',
                'enabled': True,
                'config_data': {
                    'trace_all_requests': True,
                    'trace_database_queries': True,
                    'trace_api_calls': True,
                    'max_trace_duration_hours': 24
                },
                'description': 'Enable request tracing across all system layers'
            },
            {
                'name': 'performance_monitoring',
                'config_type': 'performance_threshold',
                'enabled': True,
                'config_data': {
                    'collect_metrics': True,
                    'alert_on_threshold_breach': True,
                    'metric_retention_days': 30
                },
                'description': 'Performance monitoring configuration'
            },
            {
                'name': 'error_logging',
                'config_type': 'logging_level',
                'enabled': True,
                'config_data': {
                    'log_level': 'error',
                    'include_stack_traces': True,
                    'auto_resolve_after_days': 7
                },
                'description': 'Error logging configuration'
            },
            {
                'name': 'dashboard_settings',
                'config_type': 'dashboard_settings',
                'enabled': True,
                'config_data': {
                    'refresh_interval_seconds': 30,
                    'max_displayed_errors': 100,
                    'max_displayed_workflows': 50
                },
                'description': 'Dashboard display settings'
            }
        ]
        
        for config_data in default_configs:
            config, created = DebugConfiguration.objects.get_or_create(
                name=config_data['name'],
                defaults=config_data
            )
            if created:
                self.stdout.write(f'Created configuration: {config.name}')
            else:
                self.stdout.write(f'Configuration already exists: {config.name}')
        
        # Create default performance thresholds
        default_thresholds = [
            # API Response Time Thresholds
            {
                'metric_name': 'response_time',
                'layer': 'api',
                'component': None,
                'warning_threshold': 500.0,  # 500ms
                'critical_threshold': 2000.0,  # 2 seconds
            },
            # Database Query Time Thresholds
            {
                'metric_name': 'response_time',
                'layer': 'database',
                'component': None,
                'warning_threshold': 100.0,  # 100ms
                'critical_threshold': 500.0,  # 500ms
            },
            # Frontend Response Time Thresholds
            {
                'metric_name': 'response_time',
                'layer': 'frontend',
                'component': None,
                'warning_threshold': 200.0,  # 200ms
                'critical_threshold': 1000.0,  # 1 second
            },
            # Memory Usage Thresholds
            {
                'metric_name': 'memory_usage',
                'layer': 'system',
                'component': None,
                'warning_threshold': 80.0,  # 80%
                'critical_threshold': 95.0,  # 95%
            },
            # CPU Usage Thresholds
            {
                'metric_name': 'cpu_usage',
                'layer': 'system',
                'component': None,
                'warning_threshold': 70.0,  # 70%
                'critical_threshold': 90.0,  # 90%
            },
            # Error Rate Thresholds
            {
                'metric_name': 'error_rate',
                'layer': 'api',
                'component': None,
                'warning_threshold': 5.0,  # 5%
                'critical_threshold': 10.0,  # 10%
            },
            # Cache Hit Rate Thresholds (lower is worse for cache)
            {
                'metric_name': 'cache_hit_rate',
                'layer': 'cache',
                'component': None,
                'warning_threshold': 80.0,  # 80%
                'critical_threshold': 60.0,  # 60%
            }
        ]
        
        for threshold_data in default_thresholds:
            threshold, created = PerformanceThreshold.objects.get_or_create(
                metric_name=threshold_data['metric_name'],
                layer=threshold_data['layer'],
                component=threshold_data['component'] or '',
                defaults=threshold_data
            )
            if created:
                self.stdout.write(
                    f'Created threshold: {threshold.layer}.{threshold.metric_name}'
                )
            else:
                self.stdout.write(
                    f'Threshold already exists: {threshold.layer}.{threshold.metric_name}'
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up debugging system defaults!')
        )