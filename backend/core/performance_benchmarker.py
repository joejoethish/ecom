"""
Database Performance Benchmarking Tool for MySQL Integration

This module provides comprehensive database performance benchmarking capabilities including:
- Database connection performance testing
- Query execution benchmarking
- Load testing and stress testing
- Performance regression detection
- Comparative analysis between SQLite and MySQL
- Resource utilization monitoring
- Performance reporting and visualization
"""

import logging
import time
import threading
import statistics
import psutil
import json
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager

from django.db import connections, connection
from django.db.utils import OperationalError, DatabaseError
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.test.utils import override_settings

# Import these conditionally to avoid circular import issues
try:
    from .query_optimizer import QueryPerformanceMonitor, monitor_query_performance
except ImportError:
    QueryPerformanceMonitor = None
    monitor_query_performance = None

try:
    from .cache_manager import cache_manager
except ImportError:
    cache_manager = None

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Individual benchmark test result"""
    test_name: str
    database_alias: str
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    rows_affected: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results"""
    suite_name: str
    database_alias: str
    start_time: datetime
    end_time: Optional[datetime] = None
    results: List[BenchmarkResult] = field(default_factory=list)
    system_info: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Total benchmark duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Percentage of successful tests"""
        if not self.results:
            return 0.0
        successful = sum(1 for r in self.results if r.success)
        return (successful / len(self.results)) * 100
    
    @property
    def average_execution_time(self) -> float:
        """Average execution time of all tests"""
        if not self.results:
            return 0.0
        times = [r.execution_time for r in self.results if r.success]
        return statistics.mean(times) if times else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['results'] = [r.to_dict() for r in self.results]
        return data


@dataclass
class LoadTestConfig:
    """Load testing configuration"""
    concurrent_users: int = 10
    test_duration: int = 60  # seconds
    ramp_up_time: int = 10  # seconds
    queries_per_user: int = 100
    think_time: float = 0.1  # seconds between queries
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class SystemMonitor:
    """Monitor system resources during benchmarks"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
        
    def start_monitoring(self, interval: float = 1.0):
        """Start system monitoring"""
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,)
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> List[Dict[str, Any]]:
        """Stop monitoring and return collected metrics"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        return self.metrics
    
    def _monitor_loop(self, interval: float):
        """Monitor system resources in a loop"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                net_io = psutil.net_io_counters()
                
                metric = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_mb': memory.used / (1024 * 1024),
                    'disk_read_mb': disk_io.read_bytes / (1024 * 1024) if disk_io else 0,
                    'disk_write_mb': disk_io.write_bytes / (1024 * 1024) if disk_io else 0,
                    'network_sent_mb': net_io.bytes_sent / (1024 * 1024) if net_io else 0,
                    'network_recv_mb': net_io.bytes_recv / (1024 * 1024) if net_io else 0
                }
                
                self.metrics.append(metric)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                break
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        try:
            return {
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'disk_usage': {
                    path: psutil.disk_usage(path)._asdict() 
                    for path in ['/'] if psutil.disk_usage(path)
                },
                'python_version': f"{psutil.version_info}",
                'platform': psutil.os.name
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}


class DatabaseBenchmarker:
    """Comprehensive database performance benchmarking tool"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.query_monitor = QueryPerformanceMonitor() if QueryPerformanceMonitor else None
        self.benchmark_history = []
        
    def benchmark_connection_performance(self, database_alias: str = 'default', 
                                       iterations: int = 100) -> BenchmarkSuite:
        """Benchmark database connection performance"""
        suite = BenchmarkSuite(
            suite_name=f"Connection Performance - {database_alias}",
            database_alias=database_alias,
            start_time=datetime.now(),
            system_info=self.system_monitor.get_system_info()
        )
        
        self.system_monitor.start_monitoring()
        
        try:
            for i in range(iterations):
                start_time = time.time()
                success = True
                error_message = None
                
                try:
                    # Test connection establishment
                    db_connection = connections[database_alias]
                    with db_connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                    
                except Exception as e:
                    success = False
                    error_message = str(e)
                    logger.error(f"Connection test {i+1} failed: {e}")
                
                execution_time = time.time() - start_time
                
                result = BenchmarkResult(
                    test_name=f"connection_test_{i+1}",
                    database_alias=database_alias,
                    execution_time=execution_time,
                    success=success,
                    error_message=error_message
                )
                
                suite.results.append(result)
                
        finally:
            suite.end_time = datetime.now()
            self.system_monitor.stop_monitoring()
            
        return suite
    
    def benchmark_crud_operations(self, database_alias: str = 'default',
                                 iterations: int = 1000) -> BenchmarkSuite:
        """Benchmark basic CRUD operations"""
        suite = BenchmarkSuite(
            suite_name=f"CRUD Operations - {database_alias}",
            database_alias=database_alias,
            start_time=datetime.now(),
            system_info=self.system_monitor.get_system_info()
        )
        
        self.system_monitor.start_monitoring()
        
        try:
            db_connection = connections[database_alias]
            
            # Create test table
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TEMPORARY TABLE benchmark_test (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        name VARCHAR(100),
                        value INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            # Benchmark INSERT operations
            for i in range(iterations // 4):
                start_time = time.time()
                success = True
                error_message = None
                
                try:
                    with db_connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO benchmark_test (name, value) VALUES (%s, %s)",
                            [f"test_record_{i}", i * 10]
                        )
                    
                except Exception as e:
                    success = False
                    error_message = str(e)
                
                execution_time = time.time() - start_time
                
                suite.results.append(BenchmarkResult(
                    test_name=f"insert_{i+1}",
                    database_alias=database_alias,
                    execution_time=execution_time,
                    success=success,
                    error_message=error_message,
                    rows_affected=1 if success else 0
                ))
            
            # Benchmark SELECT operations
            for i in range(iterations // 4):
                start_time = time.time()
                success = True
                error_message = None
                rows_affected = 0
                
                try:
                    with db_connection.cursor() as cursor:
                        cursor.execute("SELECT * FROM benchmark_test WHERE value > %s", [i * 5])
                        results = cursor.fetchall()
                        rows_affected = len(results)
                    
                except Exception as e:
                    success = False
                    error_message = str(e)
                
                execution_time = time.time() - start_time
                
                suite.results.append(BenchmarkResult(
                    test_name=f"select_{i+1}",
                    database_alias=database_alias,
                    execution_time=execution_time,
                    success=success,
                    error_message=error_message,
                    rows_affected=rows_affected
                ))
            
            # Benchmark UPDATE operations
            for i in range(iterations // 4):
                start_time = time.time()
                success = True
                error_message = None
                
                try:
                    with db_connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE benchmark_test SET value = %s WHERE id = %s",
                            [i * 20, i + 1]
                        )
                    
                except Exception as e:
                    success = False
                    error_message = str(e)
                
                execution_time = time.time() - start_time
                
                suite.results.append(BenchmarkResult(
                    test_name=f"update_{i+1}",
                    database_alias=database_alias,
                    execution_time=execution_time,
                    success=success,
                    error_message=error_message,
                    rows_affected=1 if success else 0
                ))
            
            # Benchmark DELETE operations
            for i in range(iterations // 4):
                start_time = time.time()
                success = True
                error_message = None
                
                try:
                    with db_connection.cursor() as cursor:
                        cursor.execute("DELETE FROM benchmark_test WHERE id = %s", [i + 1])
                    
                except Exception as e:
                    success = False
                    error_message = str(e)
                
                execution_time = time.time() - start_time
                
                suite.results.append(BenchmarkResult(
                    test_name=f"delete_{i+1}",
                    database_alias=database_alias,
                    execution_time=execution_time,
                    success=success,
                    error_message=error_message,
                    rows_affected=1 if success else 0
                ))
                
        except Exception as e:
            logger.error(f"CRUD benchmark setup failed: {e}")
            
        finally:
            suite.end_time = datetime.now()
            self.system_monitor.stop_monitoring()
            
        return suite
    
    def benchmark_complex_queries(self, database_alias: str = 'default') -> BenchmarkSuite:
        """Benchmark complex query operations"""
        suite = BenchmarkSuite(
            suite_name=f"Complex Queries - {database_alias}",
            database_alias=database_alias,
            start_time=datetime.now(),
            system_info=self.system_monitor.get_system_info()
        )
        
        self.system_monitor.start_monitoring()
        
        try:
            # Test queries that simulate real application workload
            test_queries = [
                {
                    'name': 'product_search',
                    'query': """
                        SELECT p.*, c.name as category_name 
                        FROM products_product p 
                        JOIN products_category c ON p.category_id = c.id 
                        WHERE p.name LIKE %s AND p.is_active = 1 
                        ORDER BY p.created_at DESC 
                        LIMIT 20
                    """,
                    'params': ['%test%']
                },
                {
                    'name': 'order_summary',
                    'query': """
                        SELECT o.id, o.total_amount, u.username, 
                               COUNT(oi.id) as item_count
                        FROM orders_order o
                        JOIN auth_user u ON o.user_id = u.id
                        LEFT JOIN orders_orderitem oi ON o.id = oi.order_id
                        WHERE o.created_at >= %s
                        GROUP BY o.id, o.total_amount, u.username
                        ORDER BY o.total_amount DESC
                        LIMIT 50
                    """,
                    'params': [datetime.now() - timedelta(days=30)]
                },
                {
                    'name': 'category_stats',
                    'query': """
                        SELECT c.name, COUNT(p.id) as product_count,
                               AVG(p.price) as avg_price,
                               MAX(p.price) as max_price
                        FROM products_category c
                        LEFT JOIN products_product p ON c.id = p.category_id
                        WHERE c.is_active = 1
                        GROUP BY c.id, c.name
                        HAVING product_count > 0
                        ORDER BY product_count DESC
                    """,
                    'params': []
                }
            ]
            
            db_connection = connections[database_alias]
            
            for query_info in test_queries:
                for iteration in range(10):  # Run each query 10 times
                    start_time = time.time()
                    success = True
                    error_message = None
                    rows_affected = 0
                    
                    try:
                        with db_connection.cursor() as cursor:
                            cursor.execute(query_info['query'], query_info['params'])
                            results = cursor.fetchall()
                            rows_affected = len(results)
                        
                    except Exception as e:
                        success = False
                        error_message = str(e)
                        logger.error(f"Complex query {query_info['name']} failed: {e}")
                    
                    execution_time = time.time() - start_time
                    
                    suite.results.append(BenchmarkResult(
                        test_name=f"{query_info['name']}_{iteration+1}",
                        database_alias=database_alias,
                        execution_time=execution_time,
                        success=success,
                        error_message=error_message,
                        rows_affected=rows_affected
                    ))
                    
        except Exception as e:
            logger.error(f"Complex query benchmark failed: {e}")
            
        finally:
            suite.end_time = datetime.now()
            self.system_monitor.stop_monitoring()
            
        return suite
    
    def run_load_test(self, database_alias: str = 'default', 
                     config: LoadTestConfig = None) -> BenchmarkSuite:
        """Run load testing with concurrent users"""
        if config is None:
            config = LoadTestConfig()
            
        suite = BenchmarkSuite(
            suite_name=f"Load Test - {database_alias}",
            database_alias=database_alias,
            start_time=datetime.now(),
            system_info=self.system_monitor.get_system_info()
        )
        
        self.system_monitor.start_monitoring()
        
        def user_simulation(user_id: int) -> List[BenchmarkResult]:
            """Simulate a single user's database interactions"""
            user_results = []
            
            # Ramp up delay
            ramp_delay = (config.ramp_up_time / config.concurrent_users) * user_id
            time.sleep(ramp_delay)
            
            for query_num in range(config.queries_per_user):
                start_time = time.time()
                success = True
                error_message = None
                
                try:
                    db_connection = connections[database_alias]
                    with db_connection.cursor() as cursor:
                        # Simulate typical application queries
                        cursor.execute("SELECT COUNT(*) FROM auth_user")
                        cursor.fetchone()
                    
                except Exception as e:
                    success = False
                    error_message = str(e)
                
                execution_time = time.time() - start_time
                
                user_results.append(BenchmarkResult(
                    test_name=f"user_{user_id}_query_{query_num+1}",
                    database_alias=database_alias,
                    execution_time=execution_time,
                    success=success,
                    error_message=error_message
                ))
                
                # Think time between queries
                time.sleep(config.think_time)
            
            return user_results
        
        try:
            # Run concurrent user simulations
            with ThreadPoolExecutor(max_workers=config.concurrent_users) as executor:
                futures = [
                    executor.submit(user_simulation, user_id) 
                    for user_id in range(config.concurrent_users)
                ]
                
                for future in as_completed(futures):
                    try:
                        user_results = future.result()
                        suite.results.extend(user_results)
                    except Exception as e:
                        logger.error(f"Load test user simulation failed: {e}")
                        
        except Exception as e:
            logger.error(f"Load test execution failed: {e}")
            
        finally:
            suite.end_time = datetime.now()
            self.system_monitor.stop_monitoring()
            
        return suite
    
    def compare_databases(self, database_aliases: List[str], 
                         test_types: List[str] = None) -> Dict[str, Any]:
        """Compare performance between different databases"""
        if test_types is None:
            test_types = ['connection', 'crud', 'complex_queries']
        
        comparison_results = {
            'databases': database_aliases,
            'test_types': test_types,
            'results': {},
            'summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for db_alias in database_aliases:
            comparison_results['results'][db_alias] = {}
            
            if 'connection' in test_types:
                suite = self.benchmark_connection_performance(db_alias, iterations=50)
                comparison_results['results'][db_alias]['connection'] = suite.to_dict()
            
            if 'crud' in test_types:
                suite = self.benchmark_crud_operations(db_alias, iterations=200)
                comparison_results['results'][db_alias]['crud'] = suite.to_dict()
            
            if 'complex_queries' in test_types:
                suite = self.benchmark_complex_queries(db_alias)
                comparison_results['results'][db_alias]['complex_queries'] = suite.to_dict()
        
        # Generate comparison summary
        comparison_results['summary'] = self._generate_comparison_summary(
            comparison_results['results']
        )
        
        return comparison_results
    
    def _generate_comparison_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary comparison between databases"""
        summary = {}
        
        for test_type in ['connection', 'crud', 'complex_queries']:
            if test_type not in summary:
                summary[test_type] = {}
            
            db_performance = {}
            
            for db_alias, db_results in results.items():
                if test_type in db_results:
                    suite_data = db_results[test_type]
                    db_performance[db_alias] = {
                        'avg_execution_time': suite_data.get('average_execution_time', 0),
                        'success_rate': suite_data.get('success_rate', 0),
                        'total_tests': len(suite_data.get('results', []))
                    }
            
            if db_performance:
                # Find best performing database for this test type
                best_db = min(db_performance.keys(), 
                            key=lambda x: db_performance[x]['avg_execution_time'])
                
                summary[test_type] = {
                    'best_performer': best_db,
                    'performance_data': db_performance,
                    'performance_difference': {}
                }
                
                # Calculate performance differences
                best_time = db_performance[best_db]['avg_execution_time']
                for db_alias, perf_data in db_performance.items():
                    if db_alias != best_db and best_time > 0:
                        diff_percent = ((perf_data['avg_execution_time'] - best_time) / best_time) * 100
                        summary[test_type]['performance_difference'][db_alias] = f"{diff_percent:.1f}% slower"
        
        return summary
    
    def generate_performance_report(self, suite: BenchmarkSuite) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        successful_results = [r for r in suite.results if r.success]
        failed_results = [r for r in suite.results if not r.success]
        
        if successful_results:
            execution_times = [r.execution_time for r in successful_results]
            
            report = {
                'suite_info': {
                    'name': suite.suite_name,
                    'database': suite.database_alias,
                    'duration': suite.duration,
                    'start_time': suite.start_time.isoformat(),
                    'end_time': suite.end_time.isoformat() if suite.end_time else None
                },
                'performance_metrics': {
                    'total_tests': len(suite.results),
                    'successful_tests': len(successful_results),
                    'failed_tests': len(failed_results),
                    'success_rate': suite.success_rate,
                    'average_execution_time': statistics.mean(execution_times),
                    'median_execution_time': statistics.median(execution_times),
                    'min_execution_time': min(execution_times),
                    'max_execution_time': max(execution_times),
                    'std_deviation': statistics.stdev(execution_times) if len(execution_times) > 1 else 0
                },
                'percentiles': {
                    'p50': statistics.quantiles(execution_times, n=2)[0] if len(execution_times) > 1 else 0,
                    'p90': statistics.quantiles(execution_times, n=10)[8] if len(execution_times) > 9 else 0,
                    'p95': statistics.quantiles(execution_times, n=20)[18] if len(execution_times) > 19 else 0,
                    'p99': statistics.quantiles(execution_times, n=100)[98] if len(execution_times) > 99 else 0
                },
                'system_info': suite.system_info,
                'errors': [
                    {'test_name': r.test_name, 'error': r.error_message} 
                    for r in failed_results
                ],
                'generated_at': datetime.now().isoformat()
            }
        else:
            report = {
                'suite_info': {
                    'name': suite.suite_name,
                    'database': suite.database_alias,
                    'duration': suite.duration
                },
                'performance_metrics': {
                    'total_tests': len(suite.results),
                    'successful_tests': 0,
                    'failed_tests': len(failed_results),
                    'success_rate': 0
                },
                'errors': [
                    {'test_name': r.test_name, 'error': r.error_message} 
                    for r in failed_results
                ],
                'generated_at': datetime.now().isoformat()
            }
        
        return report
    
    def save_benchmark_results(self, suite: BenchmarkSuite, filepath: str = None):
        """Save benchmark results to file"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"benchmark_results_{suite.database_alias}_{timestamp}.json"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(suite.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Benchmark results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save benchmark results: {e}")
    
    def run_comprehensive_benchmark(self, database_alias: str = 'default') -> Dict[str, Any]:
        """Run a comprehensive benchmark suite"""
        logger.info(f"Starting comprehensive benchmark for {database_alias}")
        
        results = {
            'database_alias': database_alias,
            'start_time': datetime.now().isoformat(),
            'benchmarks': {}
        }
        
        try:
            # Connection performance
            logger.info("Running connection performance benchmark...")
            connection_suite = self.benchmark_connection_performance(database_alias)
            results['benchmarks']['connection'] = self.generate_performance_report(connection_suite)
            
            # CRUD operations
            logger.info("Running CRUD operations benchmark...")
            crud_suite = self.benchmark_crud_operations(database_alias)
            results['benchmarks']['crud'] = self.generate_performance_report(crud_suite)
            
            # Complex queries
            logger.info("Running complex queries benchmark...")
            complex_suite = self.benchmark_complex_queries(database_alias)
            results['benchmarks']['complex_queries'] = self.generate_performance_report(complex_suite)
            
            # Load test
            logger.info("Running load test...")
            load_config = LoadTestConfig(concurrent_users=5, test_duration=30, queries_per_user=20)
            load_suite = self.run_load_test(database_alias, load_config)
            results['benchmarks']['load_test'] = self.generate_performance_report(load_suite)
            
        except Exception as e:
            logger.error(f"Comprehensive benchmark failed: {e}")
            results['error'] = str(e)
        
        results['end_time'] = datetime.now().isoformat()
        
        return results


# Global benchmarker instance
performance_benchmarker = DatabaseBenchmarker()


# Convenience functions
def benchmark_database(database_alias: str = 'default') -> Dict[str, Any]:
    """Run comprehensive database benchmark"""
    return performance_benchmarker.run_comprehensive_benchmark(database_alias)


def compare_database_performance(database_aliases: List[str]) -> Dict[str, Any]:
    """Compare performance between multiple databases"""
    return performance_benchmarker.compare_databases(database_aliases)


def run_load_test(database_alias: str = 'default', concurrent_users: int = 10, 
                 duration: int = 60) -> BenchmarkSuite:
    """Run load test with specified parameters"""
    config = LoadTestConfig(
        concurrent_users=concurrent_users,
        test_duration=duration,
        queries_per_user=duration // 2  # Adjust based on duration
    )
    return performance_benchmarker.run_load_test(database_alias, config)