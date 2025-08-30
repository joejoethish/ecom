"""
Management command to set up error handling configurations
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from apps.debugging.models import DebugConfiguration, PerformanceThreshold


class Command(BaseCommand):
    help = 'Set up error handling and recovery system configurations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all configurations to defaults',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Default email for notifications',
        )
        parser.add_argument(
            '--webhook-url',
            type=str,
            help='Default webhook URL for notifications',
        )
        parser.add_argument(
            '--slack-webhook',
            type=str,
            help='Slack webhook URL for notifications',
        )
    
    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting error handling configurations...')
            DebugConfiguration.objects.filter(
                config_type__in=['alert_settings', 'performance_threshold']
            ).delete()
            PerformanceThreshold.objects.all().delete()
        
        self.setup_notification_configurations(options)
        self.setup_performance_thresholds()
        self.setup_error_handling_configurations()
        
        self.stdout.write(
            self.style.SUCCESS('Error handling system configured successfully!')
        )
    
    def setup_notification_configurations(self, options):
        """Set up notification configurations"""
        self.stdout.write('Setting up notification configurations...')
        
        # Default email configuration
        default_email = options.get('email') or getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@example.com')
        
        # Email notifications for different escalation levels
        email_configs = {
            'email_notifications_critical': {
                'enabled': True,
                'recipients': [default_email],
                'throttle_minutes': 5,
                'max_notifications_per_window': 3
            },
            'email_notifications_high': {
                'enabled': True,
                'recipients': [default_email],
                'throttle_minutes': 10,
                'max_notifications_per_window': 5
            },
            'email_notifications_medium': {
                'enabled': True,
                'recipients': [default_email],
                'throttle_minutes': 15,
                'max_notifications_per_window': 5
            },
            'email_notifications_low': {
                'enabled': False,
                'recipients': [default_email],
                'throttle_minutes': 30,
                'max_notifications_per_window': 10
            },
            'email_notifications_default': {
                'enabled': True,
                'recipients': [default_email],
                'throttle_minutes': 15,
                'max_notifications_per_window': 5
            }
        }
        
        for name, config in email_configs.items():
            DebugConfiguration.objects.update_or_create(
                name=name,
                defaults={
                    'config_type': 'alert_settings',
                    'enabled': True,
                    'config_data': config,
                    'description': f'Email notification configuration for {name.split("_")[-1]} escalation level'
                }
            )
        
        # Webhook notifications
        webhook_url = options.get('webhook_url')
        webhook_configs = {
            'webhook_notifications_critical': {
                'enabled': bool(webhook_url),
                'webhooks': [
                    {
                        'url': webhook_url or 'https://example.com/webhook',
                        'headers': {'Content-Type': 'application/json'},
                        'timeout': 30
                    }
                ] if webhook_url else [],
                'throttle_minutes': 5,
                'max_notifications_per_window': 5
            },
            'webhook_notifications_high': {
                'enabled': bool(webhook_url),
                'webhooks': [
                    {
                        'url': webhook_url or 'https://example.com/webhook',
                        'headers': {'Content-Type': 'application/json'},
                        'timeout': 30
                    }
                ] if webhook_url else [],
                'throttle_minutes': 10,
                'max_notifications_per_window': 10
            },
            'webhook_notifications_default': {
                'enabled': False,
                'webhooks': [],
                'throttle_minutes': 15,
                'max_notifications_per_window': 10
            }
        }
        
        for name, config in webhook_configs.items():
            DebugConfiguration.objects.update_or_create(
                name=name,
                defaults={
                    'config_type': 'alert_settings',
                    'enabled': True,
                    'config_data': config,
                    'description': f'Webhook notification configuration for {name.split("_")[-1]} escalation level'
                }
            )
        
        # Slack notifications
        slack_webhook = options.get('slack_webhook')
        slack_configs = {
            'slack_notifications_critical': {
                'enabled': bool(slack_webhook),
                'webhook_url': slack_webhook or '',
                'channel': '#alerts',
                'username': 'E2E Debug Bot',
                'throttle_minutes': 5,
                'max_notifications_per_window': 3
            },
            'slack_notifications_high': {
                'enabled': bool(slack_webhook),
                'webhook_url': slack_webhook or '',
                'channel': '#alerts',
                'username': 'E2E Debug Bot',
                'throttle_minutes': 10,
                'max_notifications_per_window': 5
            },
            'slack_notifications_default': {
                'enabled': False,
                'webhook_url': '',
                'channel': '#alerts',
                'username': 'E2E Debug Bot',
                'throttle_minutes': 15,
                'max_notifications_per_window': 10
            }
        }
        
        for name, config in slack_configs.items():
            DebugConfiguration.objects.update_or_create(
                name=name,
                defaults={
                    'config_type': 'alert_settings',
                    'enabled': True,
                    'config_data': config,
                    'description': f'Slack notification configuration for {name.split("_")[-1]} escalation level'
                }
            )
        
        # Notification routing configurations
        notification_routing = {
            'notifications_critical': {
                'email': {'enabled': True},
                'webhook': {'enabled': bool(webhook_url)},
                'slack': {'enabled': bool(slack_webhook)},
                'dashboard': {'enabled': True}
            },
            'notifications_high': {
                'email': {'enabled': True},
                'webhook': {'enabled': bool(webhook_url)},
                'slack': {'enabled': bool(slack_webhook)},
                'dashboard': {'enabled': True}
            },
            'notifications_medium': {
                'email': {'enabled': True},
                'webhook': {'enabled': False},
                'slack': {'enabled': False},
                'dashboard': {'enabled': True}
            },
            'notifications_low': {
                'email': {'enabled': False},
                'webhook': {'enabled': False},
                'slack': {'enabled': False},
                'dashboard': {'enabled': True}
            }
        }
        
        for name, config in notification_routing.items():
            DebugConfiguration.objects.update_or_create(
                name=name,
                defaults={
                    'config_type': 'alert_settings',
                    'enabled': True,
                    'config_data': config,
                    'description': f'Notification routing for {name.split("_")[-1]} escalation level'
                }
            )
    
    def setup_performance_thresholds(self):
        """Set up performance thresholds"""
        self.stdout.write('Setting up performance thresholds...')
        
        # Performance thresholds for different layers and metrics
        thresholds = [
            # Frontend thresholds
            {
                'metric_name': 'response_time',
                'layer': 'frontend',
                'component': None,
                'warning_threshold': 2000.0,  # 2 seconds
                'critical_threshold': 5000.0,  # 5 seconds
                'enabled': True
            },
            
            # API thresholds
            {
                'metric_name': 'response_time',
                'layer': 'api',
                'component': None,
                'warning_threshold': 1000.0,  # 1 second
                'critical_threshold': 3000.0,  # 3 seconds
                'enabled': True
            },
            {
                'metric_name': 'error_rate',
                'layer': 'api',
                'component': None,
                'warning_threshold': 5.0,  # 5%
                'critical_threshold': 10.0,  # 10%
                'enabled': True
            },
            
            # Database thresholds
            {
                'metric_name': 'response_time',
                'layer': 'database',
                'component': None,
                'warning_threshold': 500.0,  # 500ms
                'critical_threshold': 1000.0,  # 1 second
                'enabled': True
            },
            {
                'metric_name': 'query_count',
                'layer': 'database',
                'component': None,
                'warning_threshold': 50.0,  # 50 queries per request
                'critical_threshold': 100.0,  # 100 queries per request
                'enabled': True
            },
            {
                'metric_name': 'connection_pool',
                'layer': 'database',
                'component': None,
                'warning_threshold': 80.0,  # 80% pool usage
                'critical_threshold': 95.0,  # 95% pool usage
                'enabled': True
            },
            
            # Cache thresholds
            {
                'metric_name': 'cache_hit_rate',
                'layer': 'cache',
                'component': None,
                'warning_threshold': 70.0,  # 70% hit rate (warning if below)
                'critical_threshold': 50.0,  # 50% hit rate (critical if below)
                'enabled': True
            },
            {
                'metric_name': 'response_time',
                'layer': 'cache',
                'component': None,
                'warning_threshold': 100.0,  # 100ms
                'critical_threshold': 500.0,  # 500ms
                'enabled': True
            },
            
            # System thresholds
            {
                'metric_name': 'memory_usage',
                'layer': 'system',
                'component': None,
                'warning_threshold': 80.0,  # 80% memory usage
                'critical_threshold': 95.0,  # 95% memory usage
                'enabled': True
            },
            {
                'metric_name': 'cpu_usage',
                'layer': 'system',
                'component': None,
                'warning_threshold': 80.0,  # 80% CPU usage
                'critical_threshold': 95.0,  # 95% CPU usage
                'enabled': True
            }
        ]
        
        for threshold_data in thresholds:
            PerformanceThreshold.objects.update_or_create(
                metric_name=threshold_data['metric_name'],
                layer=threshold_data['layer'],
                component=threshold_data['component'],
                defaults={
                    'warning_threshold': threshold_data['warning_threshold'],
                    'critical_threshold': threshold_data['critical_threshold'],
                    'enabled': threshold_data['enabled'],
                    'alert_on_warning': True,
                    'alert_on_critical': True
                }
            )
    
    def setup_error_handling_configurations(self):
        """Set up error handling configurations"""
        self.stdout.write('Setting up error handling configurations...')
        
        # Circuit breaker configurations
        circuit_breaker_config = {
            'database_connections': {
                'failure_threshold': 5,
                'timeout_seconds': 60,
                'recovery_timeout': 30
            },
            'external_apis': {
                'failure_threshold': 3,
                'timeout_seconds': 30,
                'recovery_timeout': 15
            },
            'cache_operations': {
                'failure_threshold': 10,
                'timeout_seconds': 30,
                'recovery_timeout': 10
            }
        }
        
        DebugConfiguration.objects.update_or_create(
            name='circuit_breaker_settings',
            defaults={
                'config_type': 'alert_settings',
                'enabled': True,
                'config_data': circuit_breaker_config,
                'description': 'Circuit breaker configuration for different components'
            }
        )
        
        # Retry configurations
        retry_config = {
            'network_errors': {
                'max_retries': 3,
                'base_delay_seconds': 1.0,
                'backoff_multiplier': 2.0,
                'max_delay_seconds': 30.0
            },
            'database_errors': {
                'max_retries': 2,
                'base_delay_seconds': 0.5,
                'backoff_multiplier': 2.0,
                'max_delay_seconds': 10.0
            },
            'external_service_errors': {
                'max_retries': 3,
                'base_delay_seconds': 2.0,
                'backoff_multiplier': 2.0,
                'max_delay_seconds': 60.0
            }
        }
        
        DebugConfiguration.objects.update_or_create(
            name='retry_settings',
            defaults={
                'config_type': 'alert_settings',
                'enabled': True,
                'config_data': retry_config,
                'description': 'Retry configuration for different error types'
            }
        )
        
        # Error escalation rules
        escalation_config = {
            'critical_errors': {
                'immediate_escalation': True,
                'notification_channels': ['email', 'slack', 'webhook'],
                'escalation_delay_minutes': 0
            },
            'high_errors': {
                'immediate_escalation': True,
                'notification_channels': ['email', 'slack'],
                'escalation_delay_minutes': 5
            },
            'medium_errors': {
                'immediate_escalation': False,
                'notification_channels': ['email'],
                'escalation_delay_minutes': 15
            },
            'low_errors': {
                'immediate_escalation': False,
                'notification_channels': ['dashboard'],
                'escalation_delay_minutes': 60
            }
        }
        
        DebugConfiguration.objects.update_or_create(
            name='escalation_rules',
            defaults={
                'config_type': 'alert_settings',
                'enabled': True,
                'config_data': escalation_config,
                'description': 'Error escalation rules for different severity levels'
            }
        )
        
        # Fallback configurations
        fallback_config = {
            'database_fallbacks': {
                'read_operations': 'use_cache',
                'write_operations': 'queue_for_retry'
            },
            'external_service_fallbacks': {
                'payment_gateway': 'use_backup_gateway',
                'email_service': 'use_backup_service',
                'sms_service': 'disable_feature'
            },
            'cache_fallbacks': {
                'read_operations': 'fetch_from_database',
                'write_operations': 'skip_caching'
            }
        }
        
        DebugConfiguration.objects.update_or_create(
            name='fallback_settings',
            defaults={
                'config_type': 'alert_settings',
                'enabled': True,
                'config_data': fallback_config,
                'description': 'Fallback configuration for different system components'
            }
        )
        
        self.stdout.write('Error handling configurations created successfully!')