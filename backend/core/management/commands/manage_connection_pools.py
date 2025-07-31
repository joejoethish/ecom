"""
Management command for connection pool operations
"""
import json
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.connection_pool import get_pool_manager, initialize_connection_pools
from core.connection_monitor import get_connection_monitor
from core.database_router import get_router_stats


class Command(BaseCommand):
    help = 'Manage MySQL connection pools and monitoring'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['status', 'start', 'stop', 'restart', 'metrics', 'test', 'optimize'],
            help='Action to perform'
        )
        parser.add_argument(
            '--pool',
            type=str,
            help='Specific pool name to operate on'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Monitoring interval in seconds'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Test duration in seconds'
        )
        parser.add_argument(
            '--format',
            choices=['table', 'json'],
            default='table',
            help='Output format'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'status':
                self.show_status(options)
            elif action == 'start':
                self.start_pools(options)
            elif action == 'stop':
                self.stop_pools(options)
            elif action == 'restart':
                self.restart_pools(options)
            elif action == 'metrics':
                self.show_metrics(options)
            elif action == 'test':
                self.test_pools(options)
            elif action == 'optimize':
                self.optimize_pools(options)
        except Exception as e:
            raise CommandError(f'Command failed: {e}')
    
    def show_status(self, options):
        """Show connection pool status"""
        self.stdout.write(self.style.SUCCESS('Connection Pool Status'))
        self.stdout.write('=' * 50)
        
        try:
            pool_manager = get_pool_manager()
            status = pool_manager.get_pool_status()
            
            if options['format'] == 'json':
                self.stdout.write(json.dumps(status, indent=2))
                return
            
            for pool_name, pool_info in status.items():
                self.stdout.write(f"\nPool: {pool_name}")
                self.stdout.write(f"  Healthy: {'✓' if pool_info['healthy'] else '✗'}")
                self.stdout.write(f"  Pool Size: {pool_info['pool_size']}")
                self.stdout.write(f"  Active Connections: {pool_info['active_connections']}")
                self.stdout.write(f"  Total Requests: {pool_info['total_requests']}")
                self.stdout.write(f"  Failed Requests: {pool_info['failed_requests']}")
                self.stdout.write(f"  Avg Response Time: {pool_info['average_response_time']:.3f}s")
                self.stdout.write(f"  Peak Connections: {pool_info['peak_connections']}")
                
                if pool_info['failed_requests'] > 0:
                    failure_rate = (pool_info['failed_requests'] / pool_info['total_requests']) * 100
                    if failure_rate > 5:
                        self.stdout.write(
                            self.style.ERROR(f"  ⚠ High failure rate: {failure_rate:.1f}%")
                        )
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to get pool status: {e}'))
        
        # Show database router stats
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Database Router Status'))
        
        try:
            router_stats = get_router_stats()
            
            if options['format'] == 'json':
                self.stdout.write(json.dumps(router_stats, indent=2, default=str))
                return
            
            self.stdout.write(f"Read Databases: {', '.join(router_stats['read_databases'])}")
            self.stdout.write(f"Write Database: {router_stats['write_database']}")
            self.stdout.write(f"Replica Lag Threshold: {router_stats['replica_lag_threshold']}s")
            
            self.stdout.write("\nDatabase Health:")
            for db_alias, health in router_stats['database_health'].items():
                status_icon = '✓' if health.get('healthy', False) else '✗'
                self.stdout.write(f"  {db_alias}: {status_icon}")
                if 'replication_lag' in health:
                    self.stdout.write(f"    Replication Lag: {health['replication_lag']}s")
                if 'error' in health:
                    self.stdout.write(f"    Error: {health['error']}")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to get router stats: {e}'))
    
    def start_pools(self, options):
        """Start connection pools"""
        self.stdout.write('Starting connection pools...')
        
        try:
            pool_manager = initialize_connection_pools()
            monitor = get_connection_monitor()
            
            self.stdout.write(self.style.SUCCESS('✓ Connection pools started'))
            self.stdout.write(self.style.SUCCESS('✓ Connection monitoring started'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to start pools: {e}'))
    
    def stop_pools(self, options):
        """Stop connection pools"""
        self.stdout.write('Stopping connection pools...')
        
        try:
            pool_manager = get_pool_manager()
            pool_manager.close_all_pools()
            
            monitor = get_connection_monitor()
            monitor.stop_monitoring()
            
            self.stdout.write(self.style.SUCCESS('✓ Connection pools stopped'))
            self.stdout.write(self.style.SUCCESS('✓ Connection monitoring stopped'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to stop pools: {e}'))
    
    def restart_pools(self, options):
        """Restart connection pools"""
        self.stdout.write('Restarting connection pools...')
        
        try:
            # Stop existing pools
            pool_manager = get_pool_manager()
            pool_manager.close_all_pools()
            
            monitor = get_connection_monitor()
            monitor.stop_monitoring()
            
            # Start new pools
            time.sleep(1)  # Brief pause
            pool_manager = initialize_connection_pools()
            
            self.stdout.write(self.style.SUCCESS('✓ Connection pools restarted'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to restart pools: {e}'))
    
    def show_metrics(self, options):
        """Show connection metrics"""
        self.stdout.write(self.style.SUCCESS('Connection Metrics'))
        self.stdout.write('=' * 50)
        
        try:
            monitor = get_connection_monitor()
            metrics = monitor.get_current_metrics()
            
            if options['format'] == 'json':
                self.stdout.write(json.dumps(metrics, indent=2))
                return
            
            for db_alias, db_metrics in metrics.items():
                self.stdout.write(f"\nDatabase: {db_alias}")
                self.stdout.write(f"  Active Connections: {db_metrics.get('active_connections', 0)}")
                self.stdout.write(f"  Queries/Second: {db_metrics.get('queries_per_second', 0):.2f}")
                self.stdout.write(f"  Avg Query Time: {db_metrics.get('average_query_time', 0):.3f}s")
                self.stdout.write(f"  Slow Queries: {db_metrics.get('slow_queries', 0)}")
                self.stdout.write(f"  Failed Connections: {db_metrics.get('failed_connections', 0)}")
                self.stdout.write(f"  Replication Lag: {db_metrics.get('replication_lag', 0):.2f}s")
                
                # Health indicators
                if db_metrics.get('failed_connections', 0) > 0:
                    self.stdout.write(self.style.ERROR('  ⚠ Connection failures detected'))
                
                if db_metrics.get('replication_lag', 0) > 5:
                    self.stdout.write(self.style.WARNING('  ⚠ High replication lag'))
                
                if db_metrics.get('slow_queries', 0) > 10:
                    self.stdout.write(self.style.WARNING('  ⚠ High slow query count'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to get metrics: {e}'))
    
    def test_pools(self, options):
        """Test connection pool performance"""
        duration = options['duration']
        self.stdout.write(f'Testing connection pools for {duration} seconds...')
        
        import threading
        import random
        from django.db import connections
        
        results = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_time': 0,
            'errors': []
        }
        
        def test_worker():
            """Worker function for testing connections"""
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    # Test random database
                    db_alias = random.choice(list(settings.DATABASES.keys()))
                    connection = connections[db_alias]
                    
                    query_start = time.time()
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                    
                    query_time = time.time() - query_start
                    
                    results['total_queries'] += 1
                    results['successful_queries'] += 1
                    results['total_time'] += query_time
                    
                    # Record query time in monitor
                    monitor = get_connection_monitor()
                    monitor.record_query_time(db_alias, query_time)
                    
                    time.sleep(0.1)  # Brief pause between queries
                    
                except Exception as e:
                    results['failed_queries'] += 1
                    results['errors'].append(str(e))
        
        # Start test threads
        threads = []
        for i in range(5):  # 5 concurrent threads
            thread = threading.Thread(target=test_worker)
            thread.start()
            threads.append(thread)
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Show results
        self.stdout.write('\nTest Results:')
        self.stdout.write(f"  Total Queries: {results['total_queries']}")
        self.stdout.write(f"  Successful: {results['successful_queries']}")
        self.stdout.write(f"  Failed: {results['failed_queries']}")
        
        if results['successful_queries'] > 0:
            avg_time = results['total_time'] / results['successful_queries']
            qps = results['successful_queries'] / duration
            self.stdout.write(f"  Average Query Time: {avg_time:.3f}s")
            self.stdout.write(f"  Queries per Second: {qps:.2f}")
        
        if results['failed_queries'] > 0:
            failure_rate = (results['failed_queries'] / results['total_queries']) * 100
            self.stdout.write(self.style.ERROR(f"  Failure Rate: {failure_rate:.1f}%"))
            
            # Show unique errors
            unique_errors = list(set(results['errors'][:5]))  # Show first 5 unique errors
            for error in unique_errors:
                self.stdout.write(f"    Error: {error}")
    
    def optimize_pools(self, options):
        """Optimize connection pool sizes"""
        self.stdout.write('Analyzing connection pool usage...')
        
        try:
            pool_manager = get_pool_manager()
            
            if options['pool']:
                # Optimize specific pool
                pool_manager.optimize_pool_size(options['pool'])
                self.stdout.write(f'✓ Optimized pool: {options["pool"]}')
            else:
                # Optimize all pools
                status = pool_manager.get_pool_status()
                for pool_name in status.keys():
                    pool_manager.optimize_pool_size(pool_name)
                
                self.stdout.write('✓ Optimized all connection pools')
            
            # Show updated status
            self.stdout.write('\nUpdated Pool Status:')
            self.show_status(options)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to optimize pools: {e}'))