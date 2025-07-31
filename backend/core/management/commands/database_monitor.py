"""
Django management command for database monitoring system

This command provides CLI interface for:
- Starting/stopping database monitoring
- Viewing current metrics and alerts
- Testing alert channels
- Managing monitoring configuration
"""

import json
import time
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from core.database_monitor import get_database_monitor, initialize_database_monitoring
from core.database_alerting import get_database_alerting, initialize_database_alerting


class Command(BaseCommand):
    help = 'Database monitoring system management'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status', 'metrics', 'alerts', 'test-alerts', 'config'],
            help='Action to perform'
        )
        
        parser.add_argument(
            '--database',
            type=str,
            help='Database alias to filter results'
        )
        
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Monitoring interval in seconds (default: 30)'
        )
        
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='Hours of history to display (default: 1)'
        )
        
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Continuously watch metrics (use with status/metrics)'
        )
        
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'start':
                self.start_monitoring(options)
            elif action == 'stop':
                self.stop_monitoring(options)
            elif action == 'status':
                self.show_status(options)
            elif action == 'metrics':
                self.show_metrics(options)
            elif action == 'alerts':
                self.show_alerts(options)
            elif action == 'test-alerts':
                self.test_alerts(options)
            elif action == 'config':
                self.show_config(options)
                
        except KeyboardInterrupt:
            self.stdout.write('\nOperation cancelled by user')
        except Exception as e:
            raise CommandError(f'Error executing {action}: {e}')

    def start_monitoring(self, options):
        """Start the database monitoring system"""
        interval = options['interval']
        
        self.stdout.write(f'Starting database monitoring (interval: {interval}s)...')
        
        # Initialize monitoring
        monitor = initialize_database_monitoring(interval)
        alerting = initialize_database_alerting()
        
        # Add alerting callback to monitor
        monitor.add_alert_callback(alerting.send_alert)
        
        self.stdout.write(
            self.style.SUCCESS(f'Database monitoring started successfully')
        )
        
        if options['watch']:
            self.stdout.write('Watching metrics (Press Ctrl+C to stop)...\n')
            try:
                while True:
                    self._display_current_status(options)
                    time.sleep(10)
            except KeyboardInterrupt:
                self.stdout.write('\nStopping watch mode...')

    def stop_monitoring(self, options):
        """Stop the database monitoring system"""
        self.stdout.write('Stopping database monitoring...')
        
        monitor = get_database_monitor()
        monitor.stop_monitoring()
        
        self.stdout.write(
            self.style.SUCCESS('Database monitoring stopped successfully')
        )

    def show_status(self, options):
        """Show monitoring system status"""
        if options['watch']:
            self.stdout.write('Watching status (Press Ctrl+C to stop)...\n')
            try:
                while True:
                    self._display_current_status(options)
                    time.sleep(5)
            except KeyboardInterrupt:
                self.stdout.write('\nStopping watch mode...')
        else:
            self._display_current_status(options)

    def _display_current_status(self, options):
        """Display current monitoring status"""
        monitor = get_database_monitor()
        
        # Clear screen for watch mode
        if options['watch']:
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
        
        # Get health summary
        health_summary = monitor.get_health_summary()
        
        if options['json']:
            self.stdout.write(json.dumps(health_summary, indent=2))
            return
        
        # Display header
        self.stdout.write('=' * 80)
        self.stdout.write(f'Database Monitoring Status - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('=' * 80)
        
        # Overall status
        overall_status = health_summary.get('overall_status', 'unknown')
        status_color = {
            'healthy': self.style.SUCCESS,
            'warning': self.style.WARNING,
            'critical': self.style.ERROR,
            'unknown': self.style.NOTICE
        }.get(overall_status, self.style.NOTICE)
        
        self.stdout.write(f'Overall Status: {status_color(overall_status.upper())}')
        self.stdout.write(f'Active Alerts: {health_summary.get("active_alerts", 0)}')
        self.stdout.write(f'Total Slow Queries: {health_summary.get("total_slow_queries", 0)}')
        self.stdout.write('')
        
        # Database details
        databases = health_summary.get('databases', {})
        if databases:
            self.stdout.write('Database Details:')
            self.stdout.write('-' * 80)
            
            for db_alias, db_data in databases.items():
                db_status = db_data.get('status', 'unknown')
                db_color = {
                    'healthy': self.style.SUCCESS,
                    'warning': self.style.WARNING,
                    'critical': self.style.ERROR,
                    'unknown': self.style.NOTICE
                }.get(db_status, self.style.NOTICE)
                
                status_text = db_color(db_status.upper().ljust(8))
                self.stdout.write(f'{db_alias:15} | {status_text} | '
                                f'Health: {db_data.get("health_score", 0):5.1f} | '
                                f'Conn: {db_data.get("active_connections", 0):3d} '
                                f'({db_data.get("connection_usage_percent", 0):5.1f}%) | '
                                f'QPS: {db_data.get("queries_per_second", 0):6.1f} | '
                                f'AvgTime: {db_data.get("average_query_time", 0):6.3f}s | '
                                f'RepLag: {db_data.get("replication_lag", 0):5.1f}s')
        
        self.stdout.write('')

    def show_metrics(self, options):
        """Show detailed metrics"""
        monitor = get_database_monitor()
        database = options.get('database')
        hours = options['hours']
        
        if database:
            # Show history for specific database
            history = monitor.get_metrics_history(database, hours)
            
            if options['json']:
                self.stdout.write(json.dumps(history, indent=2))
                return
            
            self.stdout.write(f'Metrics History for {database} (last {hours} hours):')
            self.stdout.write('-' * 80)
            
            if not history:
                self.stdout.write('No metrics data available')
                return
            
            # Display recent metrics
            for metrics in history[-10:]:  # Last 10 entries
                timestamp = metrics.get('timestamp', '')
                self.stdout.write(f'{timestamp} | '
                                f'Health: {metrics.get("health_score", 0):5.1f} | '
                                f'Conn: {metrics.get("active_connections", 0):3d} | '
                                f'QPS: {metrics.get("queries_per_second", 0):6.1f} | '
                                f'AvgTime: {metrics.get("average_query_time", 0):6.3f}s')
        else:
            # Show current metrics for all databases
            current_metrics = monitor.get_current_metrics()
            
            if options['json']:
                self.stdout.write(json.dumps(current_metrics, indent=2))
                return
            
            self.stdout.write('Current Database Metrics:')
            self.stdout.write('-' * 80)
            
            for db_alias, metrics in current_metrics.items():
                if not metrics:
                    continue
                
                self.stdout.write(f'\n{db_alias}:')
                self.stdout.write(f'  Health Score: {metrics.get("health_score", 0):.1f}/100')
                self.stdout.write(f'  Connections: {metrics.get("active_connections", 0)}/{metrics.get("max_connections", 0)} '
                                f'({metrics.get("connection_usage_percent", 0):.1f}%)')
                self.stdout.write(f'  Queries/sec: {metrics.get("queries_per_second", 0):.1f}')
                self.stdout.write(f'  Avg Query Time: {metrics.get("average_query_time", 0):.3f}s')
                self.stdout.write(f'  Slow Queries: {metrics.get("slow_queries", 0)} '
                                f'({metrics.get("slow_query_rate", 0):.1f}%)')
                self.stdout.write(f'  Replication Lag: {metrics.get("replication_lag", 0):.1f}s')
                self.stdout.write(f'  CPU Usage: {metrics.get("cpu_usage", 0):.1f}%')
                self.stdout.write(f'  Memory Usage: {metrics.get("memory_usage", 0):.1f}%')
                self.stdout.write(f'  Disk Usage: {metrics.get("disk_usage", 0):.1f}%')

    def show_alerts(self, options):
        """Show active alerts and recent history"""
        monitor = get_database_monitor()
        database = options.get('database')
        hours = options['hours']
        
        # Get active alerts
        active_alerts = monitor.get_active_alerts(database)
        
        # Get alert history
        alert_history = monitor.get_alert_history(hours)
        
        if options['json']:
            data = {
                'active_alerts': active_alerts,
                'alert_history': alert_history
            }
            self.stdout.write(json.dumps(data, indent=2))
            return
        
        # Display active alerts
        self.stdout.write(f'Active Alerts ({len(active_alerts)}):')
        self.stdout.write('-' * 80)
        
        if not active_alerts:
            self.stdout.write('No active alerts')
        else:
            for alert in active_alerts:
                severity_color = {
                    'warning': self.style.WARNING,
                    'critical': self.style.ERROR
                }.get(alert.get('severity', 'warning'), self.style.WARNING)
                
                severity_text = severity_color(alert.get("severity", "").upper().ljust(8))
                self.stdout.write(f'{severity_text} | '
                                f'{alert.get("database_alias", ""):10} | '
                                f'{alert.get("metric_name", ""):20} | '
                                f'{alert.get("current_value", 0):8.1f} | '
                                f'{alert.get("message", "")}')
        
        # Display recent alert history
        self.stdout.write(f'\nAlert History (last {hours} hours, {len(alert_history)} alerts):')
        self.stdout.write('-' * 80)
        
        if not alert_history:
            self.stdout.write('No recent alerts')
        else:
            for alert in alert_history[-20:]:  # Last 20 alerts
                timestamp = alert.get('timestamp', '')[:19]  # Remove microseconds
                resolved = ' [RESOLVED]' if alert.get('resolved', False) else ''
                
                severity_color = {
                    'warning': self.style.WARNING,
                    'critical': self.style.ERROR
                }.get(alert.get('severity', 'warning'), self.style.WARNING)
                
                severity_text = severity_color(alert.get("severity", "").upper().ljust(8))
                self.stdout.write(f'{timestamp} | {severity_text} | '
                                f'{alert.get("database_alias", ""):10} | '
                                f'{alert.get("metric_name", ""):20} | '
                                f'{alert.get("message", "")}{resolved}')

    def test_alerts(self, options):
        """Test alert channels"""
        self.stdout.write('Testing alert channels...')
        
        alerting = get_database_alerting()
        results = alerting.test_channels()
        
        if options['json']:
            self.stdout.write(json.dumps(results, indent=2))
            return
        
        self.stdout.write('\nAlert Channel Test Results:')
        self.stdout.write('-' * 40)
        
        for channel_name, success in results.items():
            status_color = self.style.SUCCESS if success else self.style.ERROR
            status_text = 'PASS' if success else 'FAIL'
            self.stdout.write(f'{channel_name:15} | {status_color(status_text)}')
        
        total_channels = len(results)
        successful_channels = sum(1 for success in results.values() if success)
        
        self.stdout.write(f'\nSummary: {successful_channels}/{total_channels} channels successful')

    def show_config(self, options):
        """Show monitoring configuration"""
        monitor = get_database_monitor()
        alerting = get_database_alerting()
        
        config = {
            'monitoring': {
                'enabled': monitor.monitoring_enabled,
                'interval_seconds': monitor.monitoring_interval,
                'recovery_enabled': monitor.recovery_enabled,
                'alerting_enabled': monitor.alerting_enabled
            },
            'thresholds': {
                name: {
                    'warning_threshold': threshold.warning_threshold,
                    'critical_threshold': threshold.critical_threshold,
                    'enabled': threshold.enabled,
                    'duration_seconds': threshold.duration_seconds
                }
                for name, threshold in monitor.alert_thresholds.items()
            },
            'alert_channels': [
                {
                    'name': channel.name,
                    'type': channel.type,
                    'enabled': channel.enabled,
                    'severity_filter': channel.severity_filter
                }
                for channel in alerting.channels
            ]
        }
        
        if options['json']:
            self.stdout.write(json.dumps(config, indent=2))
            return
        
        self.stdout.write('Database Monitoring Configuration:')
        self.stdout.write('=' * 50)
        
        # Monitoring settings
        self.stdout.write('\nMonitoring Settings:')
        self.stdout.write(f'  Enabled: {config["monitoring"]["enabled"]}')
        self.stdout.write(f'  Interval: {config["monitoring"]["interval_seconds"]}s')
        self.stdout.write(f'  Recovery Enabled: {config["monitoring"]["recovery_enabled"]}')
        self.stdout.write(f'  Alerting Enabled: {config["monitoring"]["alerting_enabled"]}')
        
        # Alert thresholds
        self.stdout.write('\nAlert Thresholds:')
        for name, threshold in config['thresholds'].items():
            enabled_text = 'ENABLED' if threshold['enabled'] else 'DISABLED'
            self.stdout.write(f'  {name:20} | {enabled_text:8} | '
                            f'Warning: {threshold["warning_threshold"]:6.1f} | '
                            f'Critical: {threshold["critical_threshold"]:6.1f}')
        
        # Alert channels
        self.stdout.write('\nAlert Channels:')
        for channel in config['alert_channels']:
            enabled_text = 'ENABLED' if channel['enabled'] else 'DISABLED'
            severity_filter = ', '.join(channel['severity_filter'])
            self.stdout.write(f'  {channel["name"]:15} | {channel["type"]:10} | '
                            f'{enabled_text:8} | Severity: {severity_filter}')