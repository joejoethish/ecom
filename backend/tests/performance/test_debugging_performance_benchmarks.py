"""
Performance Benchmark Tests for Debugging System

This module contains performance benchmark tests with threshold validation
for the E2E Workflow Debugging System.

Requirements: 7.1, 7.2, 7.3
"""

import pytest
import time
import statistics
import psutil
import os
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection
from django.test.utils import override_settings
from rest_framework.test import APIClient
from unittest.mock import patch
import concurrent.futures
import threading

from apps.debugging.models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, PerformanceThreshold
)
from apps.debugging.services import WorkflowTracingEngine
from apps.products.models import Product, Category


User = get_user_model()


class PerformanceBenchmarkTestCase(TransactionTestCase):
    """Base test case for performance benchmarking"""
    
    def setUp(self):
        """Set up test data and performance thresholds"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='perftest',
            email='perf@example.com',
            password='testpass123'
        )
        
        # Create test data
        self.category = Category.objects.create(
            name='Perf Test Category',
            slug='perf-test-category'
        )
        
        # Create multiple products for load testing
        self.products = []
        for i in range(100):
            product = Product.objects.create(
                name=f'Test Product {i}',
                slug=f'test-product-{i}',
                description=f'Test product {i} description',
                price=99.99 + i,
                category=self.category,
                stock_quantity=10
            )
            self.products.append(product)
        
        # Set up performance thresholds
        self.setup_performance_thresholds()
    
    def setup_performance_thresholds(self):
        """Set up performance thresholds for testing"""
        thresholds = [
            # API Response Time Thresholds
            {
                'metric_name': 'response_time',
                'layer': 'api',
                'component': 'WorkflowSessionViewSet',
                'warning_threshold': 200.0,  # 200ms
                'critical_threshold': 500.0   # 500ms
            },
            {
                'metric_name': 'response_time',
                'layer': 'api',
                'component': 'ProductViewSet',
                'warning_threshold': 100.0,  # 100ms
                'critical_threshold': 300.0   # 300ms
            },
            # Database Query Thresholds
            {
                'metric_name': 'query_count',
                'layer': 'database',
                'component': 'ProductModel',
                'warning_threshold': 5.0,     # 5 queries
                'critical_threshold': 10.0    # 10 queries
            },
            {
                'metric_name': 'response_time',
                'layer': 'database',
                'component': 'WorkflowSession',
                'warning_threshold': 50.0,    # 50ms
                'critical_threshold': 100.0   # 100ms
            },
            # Memory Usage Thresholds
            {
                'metric_name': 'memory_usage',
                'layer': 'system',
                'component': 'WorkflowTracing',
                'warning_threshold': 100.0,   # 100MB
                'critical_threshold': 200.0   # 200MB
            },
            # Throughput Thresholds
            {
                'metric_name': 'throughput',
                'layer': 'api',
                'component': 'DebuggingAPI',
                'warning_threshold': 50.0,    # 50 req/sec (minimum)
                'critical_threshold': 25.0    # 25 req/sec (minimum)
            }
        ]
        
        for threshold_data in thresholds:
            PerformanceThreshold.objects.get_or_create(
                metric_name=threshold_data['metric_name'],
                layer=threshold_data['layer'],
                component=threshold_data.get('component'),
                defaults={
                    'warning_threshold': threshold_data['warning_threshold'],
                    'critical_threshold': threshold_data['critical_threshold'],
                    'enabled': True
                }
            )
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        return result, execution_time_ms
    
    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage during function execution"""
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        return result, memory_increase, memory_before, memory_after
    
    def count_database_queries(self, func, *args, **kwargs):
        """Count database queries during function execution"""
        queries_before = len(connection.queries)
        result = func(*args, **kwargs)
        queries_after = len(connection.queries)
        query_count = queries_after - queries_before
        return result, query_count
    
    def record_performance_metric(self, layer, component, metric_name, value, metadata=None):
        """Record a performance metric"""
        threshold = PerformanceThreshold.objects.filter(
            metric_name=metric_name,
            layer=layer,
            component=component
        ).first()
        
        return PerformanceSnapshot.objects.create(
            layer=layer,
            component=component,
            metric_name=metric_name,
            metric_value=value,
            threshold_warning=threshold.warning_threshold if threshold else None,
            threshold_critical=threshold.critical_threshold if threshold else None,
            metadata=metadata or {}
        )
    
    def assert_performance_threshold(self, metric_value, threshold_type, layer, component, metric_name):
        """Assert that a metric meets performance thresholds"""
        threshold = PerformanceThreshold.objects.filter(
            metric_name=metric_name,
            layer=layer,
            component=component
        ).first()
        
        if not threshold:
            return  # No threshold defined
        
        if threshold_type == 'warning':
            if metric_name == 'throughput':
                # For throughput, higher is better
                self.assertGreaterEqual(
                    metric_value,
                    threshold.warning_threshold,
                    f"{layer}.{component} {metric_name} below warning threshold: "
                    f"{metric_value} < {threshold.warning_threshold}"
                )
            else:
                # For other metrics, lower is better
                self.assertLessEqual(
                    metric_value,
                    threshold.warning_threshold,
                    f"{layer}.{component} {metric_name} exceeds warning threshold: "
                    f"{metric_value} > {threshold.warning_threshold}"
                )
        elif threshold_type == 'critical':
            if metric_name == 'throughput':
                self.assertGreaterEqual(
                    metric_value,
                    threshold.critical_threshold,
                    f"{layer}.{component} {metric_name} below critical threshold: "
                    f"{metric_value} < {threshold.critical_threshold}"
                )
            else:
                self.assertLessEqual(
                    metric_value,
                    threshold.critical_threshold,
                    f"{layer}.{component} {metric_name} exceeds critical threshold: "
                    f"{metric_value} > {threshold.critical_threshold}"
                )


class WorkflowTracingPerformanceTest(PerformanceBenchmarkTestCase):
    """Performance tests for workflow tracing operations"""
    
    def test_workflow_session_creation_performance(self):
        """Test performance of workflow session creation
        
        Requirements: 7.1 - Workflow tracing performance
        """
        def create_workflow_session():
            engine = WorkflowTracingEngine()
            return engine.start_workflow(
                workflow_type='login',
                user=self.user,
                metadata={'test': 'performance'}
            )
        
        # Measure execution time
        session, execution_time = self.measure_execution_time(create_workflow_session)
        
        # Measure database queries
        _, query_count = self.count_database_queries(create_workflow_session)
        
        # Record metrics
        self.record_performance_metric(
            'api', 'WorkflowTracingEngine', 'response_time', execution_time,
            {'operation': 'create_session'}
        )
        
        self.record_performance_metric(
            'database', 'WorkflowSession', 'query_count', query_count,
            {'operation': 'create_session'}
        )
        
        # Assertions
        self.assert_performance_threshold(
            execution_time, 'warning', 'api', 'WorkflowTracingEngine', 'response_time'
        )
        
        self.assert_performance_threshold(
            query_count, 'warning', 'database', 'WorkflowSession', 'query_count'
        )
        
        # Verify session was created
        self.assertIsNotNone(session)
        self.assertEqual(session.workflow_type, 'login')
    
    def test_trace_step_creation_performance(self):
        """Test performance of trace step creation
        
        Requirements: 7.1 - Trace step performance
        """
        # Create workflow session
        engine = WorkflowTracingEngine()
        session = engine.start_workflow('login', user=self.user)
        
        def create_trace_step():
            return engine.trace_step(
                layer='api',
                component='AuthView',
                operation='authenticate',
                metadata={'test': 'performance'}
            )
        
        # Measure performance for multiple trace steps
        execution_times = []
        query_counts = []
        
        for i in range(10):
            _, execution_time = self.measure_execution_time(create_trace_step)
            _, query_count = self.count_database_queries(create_trace_step)
            
            execution_times.append(execution_time)
            query_counts.append(query_count)
        
        # Calculate statistics
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        avg_query_count = statistics.mean(query_counts)
        
        # Record metrics
        self.record_performance_metric(
            'api', 'WorkflowTracingEngine', 'response_time', avg_execution_time,
            {'operation': 'create_trace_step', 'samples': 10, 'max_time': max_execution_time}
        )
        
        # Assertions
        self.assert_performance_threshold(
            avg_execution_time, 'warning', 'api', 'WorkflowTracingEngine', 'response_time'
        )
        
        self.assertLessEqual(avg_query_count, 2, "Too many queries per trace step")
    
    def test_workflow_completion_performance(self):
        """Test performance of workflow completion
        
        Requirements: 7.1 - Workflow completion performance
        """
        # Create workflow with multiple trace steps
        engine = WorkflowTracingEngine()
        session = engine.start_workflow('product_fetch', user=self.user)
        
        # Add multiple trace steps
        for i in range(5):
            engine.trace_step(
                layer='api',
                component=f'Component{i}',
                operation=f'operation_{i}',
                metadata={'step': i}
            )
        
        def complete_workflow():
            return engine.complete_workflow()
        
        # Measure performance
        analysis, execution_time = self.measure_execution_time(complete_workflow)
        _, query_count = self.count_database_queries(complete_workflow)
        
        # Record metrics
        self.record_performance_metric(
            'api', 'WorkflowTracingEngine', 'response_time', execution_time,
            {'operation': 'complete_workflow', 'trace_steps': 5}
        )
        
        # Assertions
        self.assert_performance_threshold(
            execution_time, 'warning', 'api', 'WorkflowTracingEngine', 'response_time'
        )
        
        self.assertIsNotNone(analysis)
        self.assertIn('total_duration_ms', analysis)


class APIEndpointPerformanceTest(PerformanceBenchmarkTestCase):
    """Performance tests for debugging API endpoints"""
    
    def test_workflow_session_list_performance(self):
        """Test performance of workflow session list endpoint
        
        Requirements: 7.2 - API endpoint performance
        """
        # Create multiple workflow sessions
        for i in range(50):
            WorkflowSession.objects.create(
                workflow_type='login',
                user=self.user,
                status='completed',
                metadata={'test_session': i}
            )
        
        self.client.force_authenticate(user=self.user)
        
        def fetch_workflow_sessions():
            url = reverse('debugging:workflowsession-list')
            return self.client.get(url)
        
        # Measure performance
        response, execution_time = self.measure_execution_time(fetch_workflow_sessions)
        _, query_count = self.count_database_queries(fetch_workflow_sessions)
        
        # Record metrics
        self.record_performance_metric(
            'api', 'WorkflowSessionViewSet', 'response_time', execution_time,
            {'operation': 'list', 'session_count': 50}
        )
        
        self.record_performance_metric(
            'database', 'WorkflowSession', 'query_count', query_count,
            {'operation': 'list', 'session_count': 50}
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assert_performance_threshold(
            execution_time, 'warning', 'api', 'WorkflowSessionViewSet', 'response_time'
        )
        
        # Should use pagination and select_related to minimize queries
        self.assertLessEqual(query_count, 5, "Too many database queries for session list")
    
    def test_system_health_endpoint_performance(self):
        """Test performance of system health endpoint
        
        Requirements: 7.2 - System health performance
        """
        # Create test data
        for i in range(20):
            ErrorLog.objects.create(
                layer='api',
                component='TestComponent',
                error_type='TestError',
                error_message=f'Test error {i}',
                severity='error'
            )
        
        for i in range(30):
            PerformanceSnapshot.objects.create(
                layer='api',
                component='TestComponent',
                metric_name='response_time',
                metric_value=100 + i
            )
        
        self.client.force_authenticate(user=self.user)
        
        def fetch_system_health():
            url = reverse('debugging:systemhealth-list')
            return self.client.get(url)
        
        # Measure performance
        response, execution_time = self.measure_execution_time(fetch_system_health)
        _, query_count = self.count_database_queries(fetch_system_health)
        
        # Record metrics
        self.record_performance_metric(
            'api', 'SystemHealthViewSet', 'response_time', execution_time,
            {'operation': 'health_check'}
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assert_performance_threshold(
            execution_time, 'warning', 'api', 'SystemHealthViewSet', 'response_time'
        )
        
        # Health check should be fast
        self.assertLessEqual(execution_time, 100, "System health check too slow")
    
    def test_error_log_creation_performance(self):
        """Test performance of error log creation
        
        Requirements: 7.2 - Error logging performance
        """
        self.client.force_authenticate(user=self.user)
        
        def create_error_log():
            url = reverse('debugging:errorlog-list')
            return self.client.post(url, {
                'layer': 'frontend',
                'component': 'TestComponent',
                'severity': 'error',
                'error_type': 'TestError',
                'error_message': 'Test error message',
                'metadata': {'test': True}
            })
        
        # Measure performance for multiple error logs
        execution_times = []
        
        for i in range(10):
            _, execution_time = self.measure_execution_time(create_error_log)
            execution_times.append(execution_time)
        
        avg_execution_time = statistics.mean(execution_times)
        
        # Record metrics
        self.record_performance_metric(
            'api', 'ErrorLogViewSet', 'response_time', avg_execution_time,
            {'operation': 'create', 'samples': 10}
        )
        
        # Assertions
        self.assert_performance_threshold(
            avg_execution_time, 'warning', 'api', 'ErrorLogViewSet', 'response_time'
        )


class DatabasePerformanceTest(PerformanceBenchmarkTestCase):
    """Performance tests for database operations"""
    
    def test_workflow_session_query_performance(self):
        """Test database query performance for workflow sessions
        
        Requirements: 7.3 - Database performance
        """
        # Create large dataset
        sessions = []
        for i in range(1000):
            session = WorkflowSession.objects.create(
                workflow_type='login' if i % 2 == 0 else 'product_fetch',
                user=self.user,
                status='completed' if i % 3 == 0 else 'in_progress',
                metadata={'batch': i // 100}
            )
            sessions.append(session)
        
        def query_recent_sessions():
            cutoff_time = datetime.now() - timedelta(hours=1)
            return list(WorkflowSession.objects.filter(
                start_time__gte=cutoff_time
            ).select_related('user')[:100])
        
        # Measure query performance
        results, execution_time = self.measure_execution_time(query_recent_sessions)
        _, query_count = self.count_database_queries(query_recent_sessions)
        
        # Record metrics
        self.record_performance_metric(
            'database', 'WorkflowSession', 'response_time', execution_time,
            {'operation': 'query_recent', 'total_sessions': 1000}
        )
        
        self.record_performance_metric(
            'database', 'WorkflowSession', 'query_count', query_count,
            {'operation': 'query_recent'}
        )
        
        # Assertions
        self.assert_performance_threshold(
            execution_time, 'warning', 'database', 'WorkflowSession', 'response_time'
        )
        
        self.assertEqual(len(results), 100)
        self.assertLessEqual(query_count, 2, "Should use select_related to minimize queries")
    
    def test_trace_step_aggregation_performance(self):
        """Test performance of trace step aggregations
        
        Requirements: 7.3 - Database aggregation performance
        """
        # Create workflow with many trace steps
        session = WorkflowSession.objects.create(
            workflow_type='checkout',
            user=self.user,
            status='completed'
        )
        
        # Create many trace steps
        for i in range(100):
            TraceStep.objects.create(
                workflow_session=session,
                layer='api' if i % 2 == 0 else 'database',
                component=f'Component{i % 10}',
                operation=f'operation_{i}',
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_ms=50 + (i % 100),
                status='completed'
            )
        
        def aggregate_trace_steps():
            from django.db.models import Avg, Count, Max, Min
            return TraceStep.objects.filter(
                workflow_session=session
            ).aggregate(
                avg_duration=Avg('duration_ms'),
                total_steps=Count('id'),
                max_duration=Max('duration_ms'),
                min_duration=Min('duration_ms')
            )
        
        # Measure aggregation performance
        results, execution_time = self.measure_execution_time(aggregate_trace_steps)
        
        # Record metrics
        self.record_performance_metric(
            'database', 'TraceStep', 'response_time', execution_time,
            {'operation': 'aggregation', 'step_count': 100}
        )
        
        # Assertions
        self.assertLessEqual(execution_time, 50, "Trace step aggregation too slow")
        self.assertEqual(results['total_steps'], 100)
        self.assertIsNotNone(results['avg_duration'])


class ConcurrencyPerformanceTest(PerformanceBenchmarkTestCase):
    """Performance tests under concurrent load"""
    
    def test_concurrent_workflow_creation_performance(self):
        """Test performance under concurrent workflow creation
        
        Requirements: 7.1, 7.2 - Concurrent performance
        """
        def create_concurrent_workflow(thread_id):
            """Create a workflow in a separate thread"""
            engine = WorkflowTracingEngine()
            session = engine.start_workflow(
                workflow_type='login',
                user=self.user,
                metadata={'thread_id': thread_id}
            )
            
            # Add some trace steps
            for i in range(3):
                engine.trace_step(
                    layer='api',
                    component=f'Component{i}',
                    operation=f'operation_{i}',
                    metadata={'thread_id': thread_id, 'step': i}
                )
            
            engine.complete_workflow()
            return session.correlation_id
        
        # Run concurrent workflows
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(create_concurrent_workflow, i) 
                for i in range(50)
            ]
            correlation_ids = [
                future.result() 
                for future in concurrent.futures.as_completed(futures)
            ]
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # ms
        
        # Calculate throughput
        throughput = len(correlation_ids) / (total_time / 1000)  # workflows per second
        
        # Record metrics
        self.record_performance_metric(
            'api', 'WorkflowTracingEngine', 'throughput', throughput,
            {'concurrent_workflows': 50, 'total_time_ms': total_time}
        )
        
        # Assertions
        self.assertEqual(len(correlation_ids), 50)
        self.assert_performance_threshold(
            throughput, 'warning', 'api', 'DebuggingAPI', 'throughput'
        )
        
        # Verify all workflows completed
        completed_sessions = WorkflowSession.objects.filter(
            correlation_id__in=correlation_ids,
            status='completed'
        ).count()
        self.assertEqual(completed_sessions, 50)
    
    def test_concurrent_api_requests_performance(self):
        """Test API performance under concurrent requests
        
        Requirements: 7.2 - Concurrent API performance
        """
        self.client.force_authenticate(user=self.user)
        
        def make_api_request(request_id):
            """Make an API request"""
            url = reverse('debugging:systemhealth-list')
            response = self.client.get(url)
            return response.status_code, request_id
        
        # Make concurrent API requests
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_api_request, i) 
                for i in range(100)
            ]
            results = [
                future.result() 
                for future in concurrent.futures.as_completed(futures)
            ]
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # ms
        
        # Calculate throughput
        successful_requests = sum(1 for status_code, _ in results if status_code == 200)
        throughput = successful_requests / (total_time / 1000)  # requests per second
        
        # Record metrics
        self.record_performance_metric(
            'api', 'DebuggingAPI', 'throughput', throughput,
            {'concurrent_requests': 100, 'successful_requests': successful_requests}
        )
        
        # Assertions
        self.assertEqual(successful_requests, 100)
        self.assert_performance_threshold(
            throughput, 'warning', 'api', 'DebuggingAPI', 'throughput'
        )


class MemoryPerformanceTest(PerformanceBenchmarkTestCase):
    """Memory usage performance tests"""
    
    def test_workflow_tracing_memory_usage(self):
        """Test memory usage during workflow tracing
        
        Requirements: 7.1 - Memory performance
        """
        def create_large_workflow():
            """Create a workflow with many trace steps"""
            engine = WorkflowTracingEngine()
            session = engine.start_workflow(
                workflow_type='checkout',
                user=self.user,
                metadata={'large_workflow': True}
            )
            
            # Create many trace steps with large metadata
            for i in range(1000):
                engine.trace_step(
                    layer='api',
                    component=f'Component{i}',
                    operation=f'operation_{i}',
                    metadata={
                        'large_data': 'x' * 1000,  # 1KB of data per step
                        'step_number': i,
                        'additional_data': list(range(100))
                    }
                )
            
            return engine.complete_workflow()
        
        # Measure memory usage
        result, memory_increase, memory_before, memory_after = self.measure_memory_usage(
            create_large_workflow
        )
        
        # Record metrics
        self.record_performance_metric(
            'system', 'WorkflowTracing', 'memory_usage', memory_increase,
            {
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'trace_steps': 1000
            }
        )
        
        # Assertions
        self.assert_performance_threshold(
            memory_increase, 'warning', 'system', 'WorkflowTracing', 'memory_usage'
        )
        
        self.assertIsNotNone(result)
    
    def test_error_log_memory_usage(self):
        """Test memory usage during error logging
        
        Requirements: 7.1 - Error logging memory performance
        """
        def create_many_error_logs():
            """Create many error logs"""
            for i in range(1000):
                ErrorLog.objects.create(
                    layer='api',
                    component='TestComponent',
                    error_type='TestError',
                    error_message=f'Test error message {i}' * 10,  # Longer messages
                    stack_trace='x' * 5000,  # 5KB stack trace
                    severity='error',
                    metadata={'error_id': i, 'large_data': 'x' * 1000}
                )
        
        # Measure memory usage
        _, memory_increase, memory_before, memory_after = self.measure_memory_usage(
            create_many_error_logs
        )
        
        # Record metrics
        self.record_performance_metric(
            'system', 'ErrorLogging', 'memory_usage', memory_increase,
            {
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'error_logs': 1000
            }
        )
        
        # Assertions
        self.assert_performance_threshold(
            memory_increase, 'warning', 'system', 'ErrorLogging', 'memory_usage'
        )


@pytest.mark.performance
class PerformanceRegressionTest(PerformanceBenchmarkTestCase):
    """Performance regression tests"""
    
    def test_performance_regression_detection(self):
        """Test detection of performance regressions
        
        Requirements: 7.1, 7.2, 7.3 - Performance regression detection
        """
        # Baseline performance measurement
        def baseline_operation():
            engine = WorkflowTracingEngine()
            session = engine.start_workflow('login', user=self.user)
            engine.trace_step('api', 'AuthView', 'authenticate')
            return engine.complete_workflow()
        
        # Measure baseline performance
        baseline_times = []
        for i in range(10):
            _, execution_time = self.measure_execution_time(baseline_operation)
            baseline_times.append(execution_time)
        
        baseline_avg = statistics.mean(baseline_times)
        baseline_std = statistics.stdev(baseline_times)
        
        # Simulate performance regression (artificially slow operation)
        def regressed_operation():
            time.sleep(0.1)  # Add 100ms delay to simulate regression
            return baseline_operation()
        
        # Measure regressed performance
        regressed_times = []
        for i in range(5):
            _, execution_time = self.measure_execution_time(regressed_operation)
            regressed_times.append(execution_time)
        
        regressed_avg = statistics.mean(regressed_times)
        
        # Calculate performance degradation
        performance_degradation = ((regressed_avg - baseline_avg) / baseline_avg) * 100
        
        # Record regression metrics
        self.record_performance_metric(
            'system', 'PerformanceRegression', 'degradation_percent', performance_degradation,
            {
                'baseline_avg_ms': baseline_avg,
                'regressed_avg_ms': regressed_avg,
                'baseline_std_ms': baseline_std
            }
        )
        
        # Assertions
        self.assertGreater(
            performance_degradation, 
            50,  # Should detect >50% degradation
            "Performance regression not detected"
        )
        
        # Should trigger alert for significant regression
        if performance_degradation > 100:  # >100% degradation
            self.record_performance_metric(
                'system', 'PerformanceAlert', 'regression_detected', 1,
                {'degradation_percent': performance_degradation}
            )