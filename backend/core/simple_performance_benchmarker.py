"""
Simplified Database Performance Benchmarking Tool for MySQL Integration

This module provides basic database performance benchmarking capabilities.
"""

import logging
import time
import threading
import statistics
import psutil
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager

from django.db import connections, connection
from django.db.utils import OperationalError, DatabaseError
from django.conf import settings
from django.utils import timezone

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


class SimpleDatabaseBenchmarker:
    """Simplified database performance benchmarking tool"""
    
    def __init__(self):
        self.benchmark_history = []
    
    def benchmark_connection_performance(self, database_alias: str = 'default', 
                                       iterations: int = 100) -> BenchmarkSuite:
        """Benchmark database connection performance"""
        suite = BenchmarkSuite(
            suite_name=f"Connection Performance - {database_alias}",
            database_alias=database_alias,
            start_time=datetime.now()
        )
        
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
            
        return suite
    
    def benchmark_simple_queries(self, database_alias: str = 'default',
                                iterations: int = 50) -> BenchmarkSuite:
        """Benchmark simple query operations"""
        suite = BenchmarkSuite(
            suite_name=f"Simple Queries - {database_alias}",
            database_alias=database_alias,
            start_time=datetime.now()
        )
        
        try:
            db_connection = connections[database_alias]
            
            # Test simple queries
            test_queries = [
                ("SELECT 1", []),
                ("SELECT COUNT(*) FROM auth_user", []),
                ("SELECT * FROM auth_user LIMIT 5", []),
            ]
            
            for query_name, (query, params) in enumerate(test_queries):
                for iteration in range(iterations // len(test_queries)):
                    start_time = time.time()
                    success = True
                    error_message = None
                    rows_affected = 0
                    
                    try:
                        with db_connection.cursor() as cursor:
                            cursor.execute(query, params)
                            results = cursor.fetchall()
                            rows_affected = len(results)
                        
                    except Exception as e:
                        success = False
                        error_message = str(e)
                        logger.error(f"Query {query_name} failed: {e}")
                    
                    execution_time = time.time() - start_time
                    
                    suite.results.append(BenchmarkResult(
                        test_name=f"query_{query_name}_{iteration+1}",
                        database_alias=database_alias,
                        execution_time=execution_time,
                        success=success,
                        error_message=error_message,
                        rows_affected=rows_affected
                    ))
                    
        except Exception as e:
            logger.error(f"Simple query benchmark failed: {e}")
            
        finally:
            suite.end_time = datetime.now()
            
        return suite
    
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
    
    def run_basic_benchmark(self, database_alias: str = 'default') -> Dict[str, Any]:
        """Run a basic benchmark suite"""
        logger.info(f"Starting basic benchmark for {database_alias}")
        
        results = {
            'database_alias': database_alias,
            'start_time': datetime.now().isoformat(),
            'benchmarks': {}
        }
        
        try:
            # Connection performance
            logger.info("Running connection performance benchmark...")
            connection_suite = self.benchmark_connection_performance(database_alias, iterations=20)
            results['benchmarks']['connection'] = self.generate_performance_report(connection_suite)
            
            # Simple queries
            logger.info("Running simple queries benchmark...")
            query_suite = self.benchmark_simple_queries(database_alias, iterations=30)
            results['benchmarks']['simple_queries'] = self.generate_performance_report(query_suite)
            
        except Exception as e:
            logger.error(f"Basic benchmark failed: {e}")
            results['error'] = str(e)
        
        results['end_time'] = datetime.now().isoformat()
        
        return results


# Global benchmarker instance
simple_benchmarker = SimpleDatabaseBenchmarker()


# Convenience functions
def run_basic_benchmark(database_alias: str = 'default') -> Dict[str, Any]:
    """Run basic database benchmark"""
    return simple_benchmarker.run_basic_benchmark(database_alias)