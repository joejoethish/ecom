"""
Django management command for production monitoring operations
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

from apps.debugging.production_monitoring import (
    start_production_monitoring,
    stop_production_monitoring,
    cleanup_old_data,
    monitoring_dashboard,
    alerting_system,
    health_service
)


class Command(BaseCommand):
    help = 'Manage production monitoring system'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Available actions')
        
        # Start monitoring
        start_parser = subparsers.add_parser('start', help='Start production monitoring')
        
        # Stop monitoring
        stop_parser = subparsers.add_parser('stop', help='Stop production monitoring')
        
        # Status check
        status_parser = subparsers.add_parser('status', help='Check monitoring status')
        
        # Health check
        health_parser = subparsers.add_parser('health', help='Run health checks')
        
        # Cleanup data
        cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old monitoring data')
        cleanup_parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of data to keep (default: 30)'
        )
        
        # Generate report
        report_parser = subparsers.add_parser('report', help='Generate monitoring report')
        report_parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Number of hours to include in report (default: 24)'
        )
        
        # List alerts
        alerts_parser = subparsers.add_parser('alerts', help='List active alerts')
        alerts_parser.add_argument(
            '--history',
            type=int,
            default=24,
            help='Hours of alert history to show (default: 24)'
        )
        
        # Resolve alert
        resolve_parser = subparsers.add_parser('resolve', help='Resolve an alert')
        resolve_parser.add_argument('alert_id', help='Alert ID to resolve')
        resolve_parser.add_argument(
            '--resolved-by',
            default='management_command',
            help='Who resolved the alert'
        )

    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.print_help('manage.py', 'production_monitoring')
            return
        
        try:
            if action == 'start':
                self.handle_start()
            elif action == 'stop':
                self.handle_stop()
            elif action == 'status':
                self.handle_status()
            elif action == 'health':
                self.handle_health()
            elif action == 'cleanup':
                self.handle_cleanup(options['days'])
            elif action == 'report':
                self.handle_report(options['hours'])
            elif action == 'alerts':
                self.handle_alerts(options['history'])
            elif action == 'resolve':
                self.handle_resolve(options['alert_id'], options['resolved_by'])
            else:
                raise CommandError(f"Unknown action: {action}")
                
        except Exception as e:
            raise CommandError(f"Error executing {action}: {e}")

    def handle_start(self):
        """Start production monitoring"""
        self.stdout.write("Starting production monitoring...")
        
        success = start_production_monitoring()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("Production monitoring started successfully")
            )
        else:
            raise CommandError("Failed to start production monitoring")

    def handle_stop(self):
        """Stop production monitoring"""
        self.stdout.write("Stopping production monitoring...")
        
        success = stop_production_monitoring()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("Production monitoring stopped successfully")
            )
        else:
            raise CommandError("Failed to stop production monitoring")

    def handle_status(self):
        """Check monitoring status"""
        self.stdout.write("Checking system status...")
        
        system_status = monitoring_dashboard.get_system_status()
        
        # Display overall status
        status_color = self.style.SUCCESS if system_status.status == 'healthy' else \
                      self.style.WARNING if system_status.status == 'degraded' else \
                      self.style.ERROR
        
        self.stdout.write(f"Overall Status: {status_color(system_status.status.upper())}")
        self.stdout.write(f"Timestamp: {system_status.timestamp}")
        self.stdout.write(f"Uptime: {timedelta(seconds=int(system_status.uptime_seconds))}")
        
        # Display health checks
        self.stdout.write("\nHealth Checks:")
        for hc in system_status.health_checks:
            status_symbol = "✓" if hc.status == 'healthy' else \
                           "⚠" if hc.status == 'degraded' else "✗"
            
            self.stdout.write(f"  {status_symbol} {hc.service}: {hc.status} "
                            f"({hc.response_time_ms:.1f}ms)")
            
            if hc.error_message:
                self.stdout.write(f"    Error: {hc.error_message}")
        
        # Display active alerts
        if system_status.active_alerts:
            self.stdout.write(f"\nActive Alerts ({len(system_status.active_alerts)}):")
            for alert in system_status.active_alerts:
                severity_color = self.style.ERROR if alert.severity == 'critical' else \
                               self.style.WARNING if alert.severity == 'high' else \
                               self.style.NOTICE
                
                self.stdout.write(f"  {severity_color(alert.severity.upper())}: {alert.title}")
                self.stdout.write(f"    Component: {alert.layer}.{alert.component}")
                self.stdout.write(f"    Time: {alert.timestamp}")
        else:
            self.stdout.write(f"\n{self.style.SUCCESS('No active alerts')}")

    def handle_health(self):
        """Run health checks"""
        self.stdout.write("Running health checks...")
        
        health_results = health_service.run_all_health_checks()
        
        for result in health_results:
            status_color = self.style.SUCCESS if result.status == 'healthy' else \
                          self.style.WARNING if result.status == 'degraded' else \
                          self.style.ERROR
            
            self.stdout.write(f"{result.service}: {status_color(result.status)} "
                            f"({result.response_time_ms:.1f}ms)")
            
            if result.error_message:
                self.stdout.write(f"  Error: {result.error_message}")
            
            if result.details:
                for key, value in result.details.items():
                    self.stdout.write(f"  {key}: {value}")

    def handle_cleanup(self, days_to_keep):
        """Clean up old monitoring data"""
        self.stdout.write(f"Cleaning up monitoring data older than {days_to_keep} days...")
        
        result = cleanup_old_data(days_to_keep)
        
        if 'error' in result:
            raise CommandError(f"Cleanup failed: {result['error']}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Cleanup completed:\n"
                f"  - Deleted {result['deleted_snapshots']} performance snapshots\n"
                f"  - Deleted {result['deleted_errors']} error logs\n"
                f"  - Deleted {result['deleted_sessions']} workflow sessions\n"
                f"  - Cleaned {result['cleaned_log_files']} log files"
            )
        )

    def handle_report(self, hours):
        """Generate monitoring report"""
        self.stdout.write(f"Generating monitoring report for last {hours} hours...")
        
        from apps.debugging.tasks import generate_performance_report
        
        # Run the task synchronously
        result = generate_performance_report.apply(args=[hours]).get()
        
        if 'error' in result:
            raise CommandError(f"Report generation failed: {result['error']}")
        
        self.stdout.write(f"\nPerformance Report ({hours} hours)")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Generated at: {result['generated_at']}")
        self.stdout.write(f"Total metrics collected: {result['total_metrics_collected']}")
        self.stdout.write(f"Total errors: {result['total_errors']}")
        
        # Workflow summary
        ws = result['workflow_summary']
        self.stdout.write(f"\nWorkflow Sessions:")
        self.stdout.write(f"  Total: {ws['total_sessions']}")
        self.stdout.write(f"  Completed: {ws['completed_sessions']}")
        self.stdout.write(f"  Failed: {ws['failed_sessions']}")
        if ws['avg_duration']:
            self.stdout.write(f"  Average duration: {ws['avg_duration']:.2f}s")
        
        # Top errors
        if result['error_summary']:
            self.stdout.write(f"\nTop Errors:")
            for error in result['error_summary'][:5]:
                self.stdout.write(f"  {error['layer']}.{error['component']}: "
                                f"{error['error_count']} {error['error_type']} errors")

    def handle_alerts(self, history_hours):
        """List alerts"""
        self.stdout.write(f"Listing alerts (last {history_hours} hours)...")
        
        active_alerts = alerting_system.get_active_alerts()
        alert_history = alerting_system.get_alert_history(hours=history_hours)
        
        # Active alerts
        if active_alerts:
            self.stdout.write(f"\nActive Alerts ({len(active_alerts)}):")
            for alert in active_alerts:
                severity_color = self.style.ERROR if alert.severity == 'critical' else \
                               self.style.WARNING if alert.severity == 'high' else \
                               self.style.NOTICE
                
                self.stdout.write(f"  {alert.alert_id}")
                self.stdout.write(f"    {severity_color(alert.severity.upper())}: {alert.title}")
                self.stdout.write(f"    Component: {alert.layer}.{alert.component}")
                self.stdout.write(f"    Time: {alert.timestamp}")
                self.stdout.write(f"    Message: {alert.message}")
        else:
            self.stdout.write(f"\n{self.style.SUCCESS('No active alerts')}")
        
        # Alert history
        if alert_history:
            resolved_alerts = [a for a in alert_history if a.resolved]
            self.stdout.write(f"\nAlert History ({len(alert_history)} total, "
                            f"{len(resolved_alerts)} resolved):")
            
            for alert in alert_history[-10:]:  # Show last 10
                status = "RESOLVED" if alert.resolved else "ACTIVE"
                status_color = self.style.SUCCESS if alert.resolved else self.style.ERROR
                
                self.stdout.write(f"  {alert.alert_id} - {status_color(status)}")
                self.stdout.write(f"    {alert.severity.upper()}: {alert.title}")
                self.stdout.write(f"    Time: {alert.timestamp}")

    def handle_resolve(self, alert_id, resolved_by):
        """Resolve an alert"""
        self.stdout.write(f"Resolving alert {alert_id}...")
        
        success = alerting_system.resolve_alert(alert_id, resolved_by)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"Alert {alert_id} resolved successfully")
            )
        else:
            raise CommandError(f"Alert {alert_id} not found or already resolved")