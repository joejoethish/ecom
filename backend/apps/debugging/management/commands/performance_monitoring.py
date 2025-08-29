"""
Performance Monitoring Management Command

This command provides management functionality for the performance monitoring service
including initialization, status checking, and configuration management.
"""

import time
import signal
import sys
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from apps.debugging.performance_monitoring import get_performance_monitoring_service
from apps.debugging.models import PerformanceSnapshot, PerformanceThreshold, ErrorLog


class Command(BaseCommand):
    help = 'Manage the performance monitoring service'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status', 'init', 'reset', 'test', 'benchmark'],
            help='Action to perform'
        )
        
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Duration in seconds for test/benchmark actions (default: 60)'
        )
        
        parser.add_argument(
            '--metrics-count',
            type=int,
            default=1000,
            help='Number of metrics to generate for benchmark (default: 1000)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force action without confirmation'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'start':
                self.start_service()
            elif action == 'stop':
                self.stop_service()
            elif action == 'status':
                self.show_status()
            elif action == 'init':
                self.initialize_service()
            elif action == 'reset':
                self.reset_service(force=options['force'])
            elif action == 'test':
                self.test_service(duration=options['duration'])
            elif action == 'benchmark':
                self.benchmark_service(
                    duration=options['duration'],
                    metrics_count=options['metrics_count']
                )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nOperation cancelled by user'))
            sys.exit(1)
        except Exception as e:
            raise CommandError(f'Error executing {action}: {e}')
    
    def start_service(self):
        """Start the performance monitoring service"""
        self.stdout.write('Starting performance monitoring service...')
        
        service = get_performance_monitoring_service()
        
        if service._initialized:
            self.stdout.write(self.style.WARNING('Service is already running'))
            return
        
        service.initialize()
        
        self.stdout.write(self.style.SUCCESS('Performance monitoring service started successfully'))
        self.stdout.write('Service is now collecting metrics automatically')
        
        # Show initial status
        self.show_status()
    
    def stop_service(self):
        """Stop the performance monitoring service"""
        self.stdout.write('Stopping performance monitoring service...')
        
        service = get_performance_monitoring_service()
        
        if not service._initialized:
            self.stdout.write(self.style.WARNING('Service is not running'))
            return
        
        service.shutdown()
        
        self.stdout.write(self.style.SUCCESS('Performance monitoring service stopped successfully'))
    
    def show_status(self):
        """Show service status and recent metrics"""
        service = get_performance_monitoring_service()
        
        self.stdout.write(self.style.HTTP_INFO('=== Performance Monitoring Service Status ==='))
        
        # Service status
        if service._initialized:
            self.stdout.write(self.style.SUCCESS('Service Status: RUNNING'))
            self.stdout.write(f'Metrics Collection: {"ACTIVE" if service.metrics_collector.is_collecting else "INACTIVE"}')
        else:
            self.stdout.write(self.style.ERROR('Service Status: STOPPED'))
        
        # Database statistics
        self.stdout.write('\n--- Database Statistics ---')
        
        total_snapshots = PerformanceSnapshot.objects.count()
        total_thresholds = PerformanceThreshold.objects.count()
        total_errors = ErrorLog.objects.count()
        
        self.stdout.write(f'Total Performance Snapshots: {total_snapshots:,}')
        self.stdout.write(f'Total Performance Thresholds: {total_thresholds}')
        self.stdout.write(f'Total Error Logs: {total_errors:,}')
        
        # Recent activity (last hour)
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        
        recent_snapshots = PerformanceSnapshot.objects.filter(timestamp__gte=one_hour_ago).count()
        recent_errors = ErrorLog.objects.filter(timestamp__gte=one_hour_ago).count()
        
        self.stdout.write(f'Recent Snapshots (1h): {recent_snapshots:,}')
        self.stdout.write(f'Recent Errors (1h): {recent_errors:,}')
        
        # Layer breakdown
        if total_snapshots > 0:
            self.stdout.write('\n--- Metrics by Layer (Last 24h) ---')
            
            twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
            layer_stats = PerformanceSnapshot.objects.filter(
                timestamp__gte=twenty_four_hours_ago
            ).values('layer').annotate(
                count=models.Count('id')
            ).order_by('-count')
            
            for stat in layer_stats:
                self.stdout.write(f'{stat["layer"].capitalize()}: {stat["count"]:,} metrics')
        
        # System health summary if service is running
        if service._initialized:
            try:
                self.stdout.write('\n--- System Health Summary ---')
                summary = service.get_system_health_summary()
                
                health = summary['overall_health']
                self.stdout.write(f'Health Score: {health["score"]}/100 ({health["status"].upper()})')
                
                if health['issues']:
                    self.stdout.write('Issues:')
                    for issue in health['issues']:
                        self.stdout.write(f'  - {issue}')
                
                # Show top recommendations
                recommendations = summary['recommendations']
                if recommendations['high_priority_count'] > 0:
                    self.stdout.write(f'\nHigh Priority Recommendations: {recommendations["high_priority_count"]}')
                    for rec in recommendations['top_recommendations'][:3]:
                        self.stdout.write(f'  - {rec["title"]}')
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not get health summary: {e}'))
    
    def initialize_service(self):
        """Initialize the service with default configuration"""
        self.stdout.write('Initializing performance monitoring service...')
        
        service = get_performance_monitoring_service()
        service.initialize()
        
        # Show threshold summary
        thresholds = PerformanceThreshold.objects.filter(enabled=True)
        self.stdout.write(f'Initialized {thresholds.count()} performance thresholds')
        
        # Group by layer
        layer_counts = {}
        for threshold in thresholds:
            layer = threshold.layer
            if layer not in layer_counts:
                layer_counts[layer] = 0
            layer_counts[layer] += 1
        
        for layer, count in layer_counts.items():
            self.stdout.write(f'  {layer.capitalize()}: {count} thresholds')
        
        self.stdout.write(self.style.SUCCESS('Service initialized successfully'))
    
    def reset_service(self, force=False):
        """Reset the service by clearing all data"""
        if not force:
            confirm = input('This will delete ALL performance monitoring data. Continue? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Reset cancelled')
                return
        
        self.stdout.write('Resetting performance monitoring service...')
        
        # Stop service if running
        service = get_performance_monitoring_service()
        if service._initialized:
            service.shutdown()
        
        # Clear all data
        with transaction.atomic():
            snapshot_count = PerformanceSnapshot.objects.count()
            error_count = ErrorLog.objects.count()
            threshold_count = PerformanceThreshold.objects.count()
            
            PerformanceSnapshot.objects.all().delete()
            ErrorLog.objects.filter(layer__in=['api', 'database', 'system', 'cache']).delete()
            PerformanceThreshold.objects.all().delete()
            
            self.stdout.write(f'Deleted {snapshot_count:,} performance snapshots')
            self.stdout.write(f'Deleted {error_count:,} error logs')
            self.stdout.write(f'Deleted {threshold_count} performance thresholds')
        
        # Reinitialize with defaults
        service.initialize()
        
        self.stdout.write(self.style.SUCCESS('Service reset and reinitialized successfully'))
    
    def test_service(self, duration=60):
        """Test the service by generating sample data"""
        self.stdout.write(f'Testing performance monitoring service for {duration} seconds...')
        
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        start_time = time.time()
        metrics_generated = 0
        
        # Set up signal handler for graceful shutdown
        def signal_handler(signum, frame):
            self.stdout.write('\nTest interrupted by user')
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            while time.time() - start_time < duration:
                # Generate sample metrics
                import random
                
                # API metrics
                service.metrics_collector.collect_manual_metric(
                    layer='api',
                    component='test_api',
                    metric_name='response_time',
                    metric_value=random.uniform(100, 500),
                    correlation_id=None,
                    metadata={'test': True}
                )
                
                # Database metrics
                service.metrics_collector.collect_manual_metric(
                    layer='database',
                    component='mysql',
                    metric_name='avg_query_time',
                    metric_value=random.uniform(10, 200),
                    correlation_id=None,
                    metadata={'test': True}
                )
                
                # System metrics
                service.metrics_collector.collect_manual_metric(
                    layer='system',
                    component='cpu',
                    metric_name='cpu_usage',
                    metric_value=random.uniform(20, 90),
                    correlation_id=None,
                    metadata={'test': True}
                )
                
                metrics_generated += 3
                
                # Show progress every 10 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0 and elapsed > 0:
                    rate = metrics_generated / elapsed
                    self.stdout.write(f'Generated {metrics_generated} metrics ({rate:.1f}/sec)')
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            pass
        
        elapsed = time.time() - start_time
        rate = metrics_generated / elapsed if elapsed > 0 else 0
        
        self.stdout.write(f'\nTest completed:')
        self.stdout.write(f'  Duration: {elapsed:.1f} seconds')
        self.stdout.write(f'  Metrics generated: {metrics_generated}')
        self.stdout.write(f'  Average rate: {rate:.1f} metrics/second')
        
        # Show some analysis
        self.stdout.write('\n--- Test Analysis ---')
        
        # Get recent recommendations
        recommendations = service.optimization_engine.analyze_performance_issues(hours=1)
        self.stdout.write(f'Optimization recommendations: {len(recommendations)}')
        
        # Get trends
        trends = service.trend_analyzer.analyze_trends(hours=1)
        self.stdout.write(f'Performance trends detected: {len(trends)}')
        
        self.stdout.write(self.style.SUCCESS('Test completed successfully'))
    
    def benchmark_service(self, duration=60, metrics_count=1000):
        """Benchmark the service performance"""
        self.stdout.write(f'Benchmarking performance monitoring service...')
        self.stdout.write(f'Duration: {duration}s, Metrics: {metrics_count:,}')
        
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        import random
        import uuid
        
        # Benchmark metrics collection
        self.stdout.write('\n1. Benchmarking metrics collection...')
        start_time = time.time()
        
        for i in range(metrics_count):
            service.metrics_collector.collect_manual_metric(
                layer=random.choice(['api', 'database', 'system', 'cache']),
                component=f'component_{i % 20}',
                metric_name=random.choice(['response_time', 'cpu_usage', 'memory_usage', 'query_time']),
                metric_value=random.uniform(10, 1000),
                correlation_id=str(uuid.uuid4()) if i % 10 == 0 else None,
                metadata={'benchmark': True, 'batch': i // 100}
            )
            
            if i % 100 == 0 and i > 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                self.stdout.write(f'  Progress: {i:,}/{metrics_count:,} ({rate:.0f}/sec)')
        
        collection_time = time.time() - start_time
        collection_rate = metrics_count / collection_time
        
        self.stdout.write(f'  Collection completed: {collection_time:.2f}s ({collection_rate:.0f} metrics/sec)')
        
        # Benchmark trend analysis
        self.stdout.write('\n2. Benchmarking trend analysis...')
        start_time = time.time()
        
        trends = service.trend_analyzer.analyze_trends(hours=1)
        
        trend_time = time.time() - start_time
        self.stdout.write(f'  Trend analysis completed: {trend_time:.2f}s ({len(trends)} trends)')
        
        # Benchmark optimization analysis
        self.stdout.write('\n3. Benchmarking optimization analysis...')
        start_time = time.time()
        
        recommendations = service.optimization_engine.analyze_performance_issues(hours=1)
        
        optimization_time = time.time() - start_time
        self.stdout.write(f'  Optimization analysis completed: {optimization_time:.2f}s ({len(recommendations)} recommendations)')
        
        # Benchmark health summary
        self.stdout.write('\n4. Benchmarking health summary...')
        start_time = time.time()
        
        summary = service.get_system_health_summary()
        
        summary_time = time.time() - start_time
        self.stdout.write(f'  Health summary completed: {summary_time:.2f}s')
        
        # Overall results
        total_time = collection_time + trend_time + optimization_time + summary_time
        
        self.stdout.write(f'\n--- Benchmark Results ---')
        self.stdout.write(f'Metrics Collection: {collection_time:.2f}s ({collection_rate:.0f} metrics/sec)')
        self.stdout.write(f'Trend Analysis: {trend_time:.2f}s')
        self.stdout.write(f'Optimization Analysis: {optimization_time:.2f}s')
        self.stdout.write(f'Health Summary: {summary_time:.2f}s')
        self.stdout.write(f'Total Time: {total_time:.2f}s')
        
        # Performance assessment
        if collection_rate > 500:
            self.stdout.write(self.style.SUCCESS('Collection performance: EXCELLENT'))
        elif collection_rate > 200:
            self.stdout.write(self.style.SUCCESS('Collection performance: GOOD'))
        elif collection_rate > 100:
            self.stdout.write(self.style.WARNING('Collection performance: FAIR'))
        else:
            self.stdout.write(self.style.ERROR('Collection performance: POOR'))
        
        if trend_time < 2.0:
            self.stdout.write(self.style.SUCCESS('Analysis performance: EXCELLENT'))
        elif trend_time < 5.0:
            self.stdout.write(self.style.SUCCESS('Analysis performance: GOOD'))
        elif trend_time < 10.0:
            self.stdout.write(self.style.WARNING('Analysis performance: FAIR'))
        else:
            self.stdout.write(self.style.ERROR('Analysis performance: POOR'))
        
        self.stdout.write(self.style.SUCCESS('Benchmark completed successfully'))


# Add missing import
from django.db import models