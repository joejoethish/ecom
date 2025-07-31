"""
Management command to monitor read replica health
"""
import logging
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.replica_health_monitor import ReplicaHealthMonitor, ReplicaMetricsCollector

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitor read replica health and perform automatic failover'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            action='store_true',
            help='Start continuous replica monitoring',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Check current replica health status',
        )
        parser.add_argument(
            '--metrics',
            action='store_true',
            help='Show replica performance metrics',
        )
        parser.add_argument(
            '--force-check',
            action='store_true',
            help='Force immediate health check',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Monitoring interval in seconds (default: 30)',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Hours of metrics to show (default: 24)',
        )
    
    def handle(self, *args, **options):
        monitor = ReplicaHealthMonitor()
        
        if options['start']:
            self.start_monitoring(monitor, options['interval'])
        elif options['status']:
            self.show_status(monitor)
        elif options['metrics']:
            self.show_metrics(options['hours'])
        elif options['force_check']:
            self.force_health_check(monitor)
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify an action: --start, --status, --metrics, or --force-check'
                )
            )
    
    def start_monitoring(self, monitor, interval):
        """Start continuous monitoring"""
        self.stdout.write(f"Starting replica health monitoring (interval: {interval}s)...")
        self.stdout.write("Press Ctrl+C to stop monitoring")
        
        # Update monitoring interval
        monitor.check_interval = interval
        
        try:
            monitor.start_monitoring()
            
            # Keep the command running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.stdout.write("\nStopping replica monitoring...")
            monitor.stop_monitoring()
            self.stdout.write("Monitoring stopped.")
        except Exception as e:
            raise CommandError(f'Error in monitoring: {e}')
    
    def show_status(self, monitor):
        """Show current monitoring status"""
        self.stdout.write("Replica Monitoring Status:")
        self.stdout.write("-" * 40)
        
        try:
            status = monitor.get_monitoring_status()
            
            # Monitoring configuration
            self.stdout.write(f"Monitoring Enabled: {status['monitoring_enabled']}")
            self.stdout.write(f"Monitoring Active: {status['monitoring_active']}")
            self.stdout.write(f"Check Interval: {status['check_interval']}s")
            self.stdout.write(f"Lag Threshold: {status['lag_threshold']}s")
            self.stdout.write(f"Max Failures: {status['max_failures']}")
            self.stdout.write(f"Failure Window: {status['failure_window']}s")
            
            # Failure counts
            if status['failure_counts']:
                self.stdout.write("\nCurrent Failure Counts:")
                for replica, failures in status['failure_counts'].items():
                    self.stdout.write(f"  {replica}: {len(failures)} failures")
            
            # Last alert times
            if status['last_alert_times']:
                self.stdout.write("\nLast Alert Times:")
                for replica, alert_time in status['last_alert_times'].items():
                    alert_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert_time))
                    self.stdout.write(f"  {replica}: {alert_datetime}")
            
            # Current health status
            self.stdout.write("\nCurrent Health Status:")
            health_results = monitor.force_health_check()
            
            for replica_alias, health_data in health_results.items():
                if health_data['healthy']:
                    status_color = self.style.SUCCESS
                    status_text = "HEALTHY"
                else:
                    status_color = self.style.ERROR
                    status_text = "UNHEALTHY"
                
                self.stdout.write(f"  {replica_alias}: {status_color(status_text)}")
                self.stdout.write(f"    Lag: {health_data['replication_lag']}s")
                self.stdout.write(f"    IO: {health_data['io_running']}")
                self.stdout.write(f"    SQL: {health_data['sql_running']}")
                
                if health_data['last_error']:
                    self.stdout.write(f"    Error: {health_data['last_error']}")
                    
        except Exception as e:
            raise CommandError(f'Error getting monitoring status: {e}')
    
    def show_metrics(self, hours):
        """Show replica performance metrics"""
        self.stdout.write(f"Replica Performance Metrics (last {hours} hours):")
        self.stdout.write("-" * 50)
        
        try:
            collector = ReplicaMetricsCollector()
            
            # Collect current metrics
            current_metrics = collector.collect_metrics()
            
            # Get metrics summary
            summary = collector.get_metrics_summary(hours)
            
            if not summary.get('replicas'):
                self.stdout.write("No replica metrics available.")
                return
            
            for replica_alias, replica_metrics in summary['replicas'].items():
                current = replica_metrics['current_status']
                
                self.stdout.write(f"\n{replica_alias}:")
                self.stdout.write(f"  Current Status: {'HEALTHY' if current['healthy'] else 'UNHEALTHY'}")
                self.stdout.write(f"  Current Lag: {current['replication_lag']}s")
                self.stdout.write(f"  Uptime: {replica_metrics['uptime_percentage']:.1f}%")
                self.stdout.write(f"  Average Lag: {replica_metrics['average_lag']}s")
                self.stdout.write(f"  Max Lag: {replica_metrics['max_lag']}s")
                self.stdout.write(f"  IO Running: {current['io_running']}")
                self.stdout.write(f"  SQL Running: {current['sql_running']}")
                self.stdout.write(f"  Has Errors: {current['has_error']}")
            
            # Overall summary
            total_replicas = len(summary['replicas'])
            healthy_replicas = sum(1 for r in summary['replicas'].values() 
                                 if r['current_status']['healthy'])
            
            self.stdout.write(f"\nOverall Summary:")
            self.stdout.write(f"  Total Replicas: {total_replicas}")
            self.stdout.write(f"  Healthy Replicas: {healthy_replicas}")
            self.stdout.write(f"  Health Percentage: {(healthy_replicas/total_replicas)*100:.1f}%")
            
        except Exception as e:
            raise CommandError(f'Error getting metrics: {e}')
    
    def force_health_check(self, monitor):
        """Force immediate health check"""
        self.stdout.write("Performing immediate health check...")
        
        try:
            results = monitor.force_health_check()
            
            self.stdout.write("\nHealth Check Results:")
            self.stdout.write("-" * 30)
            
            for replica_alias, health_data in results.items():
                if health_data['healthy']:
                    status_color = self.style.SUCCESS
                    status_text = "HEALTHY"
                else:
                    status_color = self.style.ERROR
                    status_text = "UNHEALTHY"
                
                self.stdout.write(f"\n{replica_alias}: {status_color(status_text)}")
                self.stdout.write(f"  Replication Lag: {health_data['replication_lag']}s")
                self.stdout.write(f"  IO Running: {health_data['io_running']}")
                self.stdout.write(f"  SQL Running: {health_data['sql_running']}")
                
                if health_data['last_error']:
                    self.stdout.write(f"  Last Error: {health_data['last_error']}")
                
                check_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                         time.localtime(health_data['check_time']))
                self.stdout.write(f"  Check Time: {check_time}")
            
        except Exception as e:
            raise CommandError(f'Error performing health check: {e}')