"""
Management command to start production monitoring and alerting system.
"""

import signal
import sys
import time
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.debugging.production_monitoring import (
    production_logger, alerting_system, health_check_service
)
from apps.debugging.performance_monitoring import MetricsCollector, ThresholdManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start production monitoring and alerting system'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = False
        self.metrics_collector = None
        self.threshold_manager = None
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--no-alerts',
            action='store_true',
            help='Disable alerting system',
        )
        parser.add_argument(
            '--no-metrics',
            action='store_true',
            help='Disable metrics collection',
        )
        parser.add_argument(
            '--initialize-thresholds',
            action='store_true',
            help='Initialize default performance thresholds',
        )
        parser.add_argument(
            '--log-level',
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Set logging level',
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        
        # Set logging level
        log_level = getattr(logging, options['log_level'])
        logging.getLogger().setLevel(log_level)
        
        self.stdout.write(
            self.style.SUCCESS('Starting Production Monitoring System...')
        )
        
        # Check if production monitoring is enabled
        if not getattr(settings, 'PRODUCTION_MONITORING', {}).get('ENABLED', False):
            self.stdout.write(
                self.style.WARNING(
                    'Production monitoring is disabled in settings. '
                    'Set PRODUCTION_MONITORING_ENABLED=True to enable.'
                )
            )
            return
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Initialize components
            self._initialize_components(options)
            
            # Start monitoring services
            self._start_services(options)
            
            # Main monitoring loop
            self._run_monitoring_loop()
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nReceived interrupt signal. Shutting down...')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error in production monitoring: {e}')
            )
            logger.error(f'Production monitoring error: {e}', exc_info=True)
        finally:
            self._shutdown_services()
    
    def _initialize_components(self, options):
        """Initialize monitoring components"""
        
        self.stdout.write('Initializing monitoring components...')
        
        # Initialize production logger
        try:
            production_logger.setup_production_logging()
            self.stdout.write('✓ Production logging initialized')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to initialize logging: {e}')
            )
            raise
        
        # Initialize threshold manager
        try:
            self.threshold_manager = ThresholdManager()
            if options['initialize_thresholds']:
                self.threshold_manager.initialize_default_thresholds()
                self.stdout.write('✓ Default performance thresholds initialized')
            self.stdout.write('✓ Threshold manager initialized')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to initialize threshold manager: {e}')
            )
            raise
        
        # Initialize metrics collector
        if not options['no_metrics']:
            try:
                self.metrics_collector = MetricsCollector()
                self.stdout.write('✓ Metrics collector initialized')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to initialize metrics collector: {e}')
                )
                raise
        
        self.stdout.write(
            self.style.SUCCESS('All components initialized successfully')
        )
    
    def _start_services(self, options):
        """Start monitoring services"""
        
        self.stdout.write('Starting monitoring services...')
        
        # Start metrics collection
        if not options['no_metrics'] and self.metrics_collector:
            try:
                self.metrics_collector.start_collection()
                self.stdout.write('✓ Metrics collection started')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to start metrics collection: {e}')
                )
                raise
        
        # Start alerting system
        if not options['no_alerts']:
            try:
                alerting_system.start_monitoring()
                self.stdout.write('✓ Alerting system started')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to start alerting system: {e}')
                )
                raise
        
        self.running = True
        self.stdout.write(
            self.style.SUCCESS('All monitoring services started successfully')
        )
        
        # Display status information
        self._display_status_info(options)
    
    def _display_status_info(self, options):
        """Display current status information"""
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('PRODUCTION MONITORING STATUS'))
        self.stdout.write('='*60)
        
        # System status
        try:
            system_status = health_check_service.run_all_health_checks()
            status_color = self.style.SUCCESS if system_status.status == 'healthy' else self.style.WARNING
            self.stdout.write(f'System Status: {status_color(system_status.status.upper())}')
            
            # Health check details
            for check in system_status.health_checks:
                status_symbol = '✓' if check.status == 'healthy' else '⚠' if check.status == 'degraded' else '✗'
                self.stdout.write(f'  {status_symbol} {check.service}: {check.status} ({check.response_time_ms:.1f}ms)')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to get system status: {e}')
            )
        
        # Active alerts
        try:
            active_alerts = alerting_system.get_active_alerts()
            if active_alerts:
                self.stdout.write(f'\nActive Alerts: {len(active_alerts)}')
                for alert in active_alerts[:5]:  # Show first 5 alerts
                    severity_color = self.style.ERROR if alert['severity'] == 'critical' else self.style.WARNING
                    self.stdout.write(f'  • {severity_color(alert["severity"].upper())}: {alert["title"]}')
                if len(active_alerts) > 5:
                    self.stdout.write(f'  ... and {len(active_alerts) - 5} more')
            else:
                self.stdout.write(f'\nActive Alerts: {self.style.SUCCESS("None")}')
        except Exception as e:
            self.stdout.write(f'\nFailed to get alerts: {e}')
        
        # Configuration
        self.stdout.write('\nConfiguration:')
        self.stdout.write(f'  Metrics Collection: {"Enabled" if not options["no_metrics"] else "Disabled"}')
        self.stdout.write(f'  Alerting System: {"Enabled" if not options["no_alerts"] else "Disabled"}')
        self.stdout.write(f'  Log Level: {options["log_level"]}')
        
        # Endpoints
        self.stdout.write('\nMonitoring Endpoints:')
        self.stdout.write('  Health Check: /api/v1/debugging/health/')
        self.stdout.write('  Detailed Health: /api/v1/debugging/health/detailed/')
        self.stdout.write('  Metrics: /api/v1/debugging/metrics/')
        self.stdout.write('  Alerts: /api/v1/debugging/alerts/')
        self.stdout.write('  Dashboard: /api/v1/debugging/production/')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Press Ctrl+C to stop monitoring')
        self.stdout.write('='*60 + '\n')
    
    def _run_monitoring_loop(self):
        """Main monitoring loop"""
        
        loop_interval = 60  # Check every minute
        last_status_display = 0
        status_display_interval = 300  # Display status every 5 minutes
        
        while self.running:
            try:
                current_time = time.time()
                
                # Periodic status display
                if current_time - last_status_display > status_display_interval:
                    self._display_periodic_status()
                    last_status_display = current_time
                
                # Sleep for the loop interval
                time.sleep(loop_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f'Error in monitoring loop: {e}', exc_info=True)
                time.sleep(30)  # Wait before retrying
    
    def _display_periodic_status(self):
        """Display periodic status update"""
        
        try:
            # Get current system status
            system_status = health_check_service.run_all_health_checks()
            active_alerts = alerting_system.get_active_alerts()
            
            # Display brief status
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            status_color = self.style.SUCCESS if system_status.status == 'healthy' else self.style.WARNING
            
            self.stdout.write(
                f'[{timestamp}] System: {status_color(system_status.status.upper())} | '
                f'Alerts: {len(active_alerts)} | '
                f'Uptime: {system_status.uptime_seconds:.0f}s'
            )
            
            # Show any new critical alerts
            critical_alerts = [a for a in active_alerts if a['severity'] == 'critical']
            if critical_alerts:
                for alert in critical_alerts[:3]:  # Show first 3 critical alerts
                    self.stdout.write(
                        f'  🚨 CRITICAL: {alert["title"]}'
                    )
            
        except Exception as e:
            logger.error(f'Error displaying periodic status: {e}')
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write(f'\nReceived signal {signum}. Initiating graceful shutdown...')
        self.running = False
    
    def _shutdown_services(self):
        """Shutdown monitoring services"""
        
        self.stdout.write('Shutting down monitoring services...')
        
        # Stop alerting system
        try:
            alerting_system.stop_monitoring()
            self.stdout.write('✓ Alerting system stopped')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error stopping alerting system: {e}')
            )
        
        # Stop metrics collection
        if self.metrics_collector:
            try:
                self.metrics_collector.stop_collection()
                self.stdout.write('✓ Metrics collection stopped')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error stopping metrics collection: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Production monitoring system stopped')
        )