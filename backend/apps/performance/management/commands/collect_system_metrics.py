from django.core.management.base import BaseCommand
from django.utils import timezone
import psutil
import time
import logging

from apps.performance.models import PerformanceMetric, ServerMetrics

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Collect system performance metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Collection interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=0,
            help='Duration to run in seconds (0 for infinite)'
        )
        parser.add_argument(
            '--server-name',
            type=str,
            default='default',
            help='Server name identifier'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        duration = options['duration']
        server_name = options['server_name']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting system metrics collection (interval: {interval}s, server: {server_name})'
            )
        )
        
        start_time = time.time()
        
        try:
            while True:
                self.collect_metrics(server_name)
                
                # Check if duration limit reached
                if duration > 0 and (time.time() - start_time) >= duration:
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Metrics collection stopped by user')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error collecting metrics: {e}')
            )
    
    def collect_metrics(self, server_name):
        """Collect and store system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            processes = len(psutil.pids())
            
            # Boot time (uptime)
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            # Store server metrics
            ServerMetrics.objects.create(
                server_name=server_name,
                server_type='web',  # Could be configurable
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                memory_total=memory.total,
                disk_usage=(disk.used / disk.total) * 100,
                disk_total=disk.total,
                network_in=network.bytes_recv,
                network_out=network.bytes_sent,
                load_average=list(load_avg),
                processes_count=processes,
                uptime=int(uptime)
            )
            
            # Store individual performance metrics
            metrics_to_create = [
                {
                    'metric_type': 'cpu_usage',
                    'name': f'CPU Usage - {server_name}',
                    'value': cpu_percent,
                    'unit': '%',
                    'source': 'system',
                    'metadata': {
                        'cpu_count': cpu_count,
                        'load_avg': list(load_avg)
                    },
                    'severity': self.get_severity('cpu', cpu_percent)
                },
                {
                    'metric_type': 'memory_usage',
                    'name': f'Memory Usage - {server_name}',
                    'value': memory.percent,
                    'unit': '%',
                    'source': 'system',
                    'metadata': {
                        'total_gb': round(memory.total / (1024**3), 2),
                        'available_gb': round(memory.available / (1024**3), 2),
                        'used_gb': round(memory.used / (1024**3), 2)
                    },
                    'severity': self.get_severity('memory', memory.percent)
                },
                {
                    'metric_type': 'disk_usage',
                    'name': f'Disk Usage - {server_name}',
                    'value': (disk.used / disk.total) * 100,
                    'unit': '%',
                    'source': 'system',
                    'metadata': {
                        'total_gb': round(disk.total / (1024**3), 2),
                        'used_gb': round(disk.used / (1024**3), 2),
                        'free_gb': round(disk.free / (1024**3), 2)
                    },
                    'severity': self.get_severity('disk', (disk.used / disk.total) * 100)
                }
            ]
            
            # Bulk create metrics
            PerformanceMetric.objects.bulk_create([
                PerformanceMetric(**metric) for metric in metrics_to_create
            ])
            
            self.stdout.write(f'Collected metrics at {timezone.now()}')
            
        except Exception as e:
            logger.error(f'Error collecting system metrics: {e}')
            self.stdout.write(
                self.style.ERROR(f'Error collecting metrics: {e}')
            )
    
    def get_severity(self, metric_type, value):
        """Determine severity level based on metric type and value"""
        thresholds = {
            'cpu': {'critical': 90, 'high': 80, 'medium': 70},
            'memory': {'critical': 95, 'high': 85, 'medium': 75},
            'disk': {'critical': 95, 'high': 90, 'medium': 80}
        }
        
        if metric_type in thresholds:
            levels = thresholds[metric_type]
            if value >= levels['critical']:
                return 'critical'
            elif value >= levels['high']:
                return 'high'
            elif value >= levels['medium']:
                return 'medium'
        
        return 'low'