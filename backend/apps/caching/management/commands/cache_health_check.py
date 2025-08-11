from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.caching.models import CacheConfiguration, CacheAlert
from apps.caching.optimization import cache_optimizer
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Perform health checks on all active cache configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cache-name',
            type=str,
            help='Check specific cache by name'
        )
        parser.add_argument(
            '--create-alerts',
            action='store_true',
            help='Create alerts for health issues'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        cache_name = options.get('cache_name')
        create_alerts = options.get('create_alerts', False)
        verbose = options.get('verbose', False)
        
        try:
            # Get cache configurations to check
            if cache_name:
                configs = CacheConfiguration.objects.filter(
                    name=cache_name, is_active=True
                )
                if not configs.exists():
                    self.stdout.write(
                        self.style.ERROR(f'Cache configuration "{cache_name}" not found or inactive')
                    )
                    return
            else:
                configs = CacheConfiguration.objects.filter(is_active=True)
            
            if not configs.exists():
                self.stdout.write(
                    self.style.WARNING('No active cache configurations found')
                )
                return
            
            total_checks = 0
            healthy_caches = 0
            issues_found = 0
            
            for config in configs:
                total_checks += 1
                
                if verbose:
                    self.stdout.write(f'Checking cache: {config.name}')
                
                try:
                    # Perform health check
                    health = cache_optimizer.monitor_cache_health(config.name)
                    
                    if 'error' in health:
                        self.stdout.write(
                            self.style.ERROR(f'Health check failed for {config.name}: {health["error"]}')
                        )
                        continue
                    
                    health_score = health.get('health_score', 0)
                    status = health.get('status', 'unknown')
                    alerts = health.get('alerts', [])
                    
                    if health_score >= 75:
                        healthy_caches += 1
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ {config.name}: {status} (score: {health_score})')
                            )
                    else:
                        issues_found += 1
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠ {config.name}: {status} (score: {health_score})')
                        )
                        
                        # Show alerts
                        for alert in alerts:
                            self.stdout.write(f'    - {alert.message}')
                            
                            # Create alert if requested
                            if create_alerts:
                                CacheAlert.objects.get_or_create(
                                    cache_name=config.name,
                                    alert_type=alert.alert_type,
                                    severity=alert.severity,
                                    defaults={
                                        'message': alert.message,
                                        'threshold_value': alert.threshold_value,
                                        'current_value': alert.current_value
                                    }
                                )
                    
                    if verbose:
                        # Show detailed stats
                        stats = health.get('stats', {})
                        self.stdout.write(f'    Hit ratio: {stats.get("hit_ratio", 0):.2%}')
                        self.stdout.write(f'    Avg response time: {stats.get("avg_response_time_ms", 0):.2f}ms')
                        self.stdout.write(f'    Memory usage: {stats.get("memory_usage_percent", 0):.1f}%')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Health check failed for {config.name}: {e}')
                    )
                    logger.error(f'Health check failed for {config.name}: {e}')
            
            # Summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write(f'Health Check Summary:')
            self.stdout.write(f'  Total caches checked: {total_checks}')
            self.stdout.write(
                self.style.SUCCESS(f'  Healthy caches: {healthy_caches}')
            )
            if issues_found > 0:
                self.stdout.write(
                    self.style.WARNING(f'  Caches with issues: {issues_found}')
                )
            
            if create_alerts and issues_found > 0:
                self.stdout.write(f'  Alerts created for issues found')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Health check command failed: {e}')
            )
            logger.error(f'Health check command failed: {e}')