"""
Tests for the performance monitoring demo
"""

import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.debugging.performance_demo import PerformanceDemo


class PerformanceDemoTestCase(TestCase):
    """Test cases for the performance monitoring demo"""

    def setUp(self):
        self.demo = PerformanceDemo()

    def test_demo_initialization(self):
        """Test that the demo initializes correctly"""
        self.assertIsNotNone(self.demo.monitor)
        self.assertEqual(self.demo.results, [])

    @patch('time.sleep')
    def test_simulate_database_operations(self, mock_sleep):
        """Test database operations simulation"""
        result = self.demo.simulate_database_operations()
        
        self.assertEqual(result['operation'], 'database_operations')
        self.assertEqual(result['queries_executed'], 12)
        self.assertIn('total_time', result)

    @patch('time.sleep')
    def test_simulate_api_requests(self, mock_sleep):
        """Test API requests simulation"""
        result = self.demo.simulate_api_requests()
        
        self.assertEqual(result['operation'], 'api_requests')
        self.assertEqual(result['endpoints_tested'], 5)
        self.assertIn('avg_response_time', result)

    @patch('time.sleep')
    @patch('threading.Thread')
    def test_simulate_concurrent_operations(self, mock_thread, mock_sleep):
        """Test concurrent operations simulation"""
        # Mock thread behavior
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        result = self.demo.simulate_concurrent_operations()
        
        self.assertEqual(result['operation'], 'concurrent_operations')
        self.assertEqual(result['threads_executed'], 5)
        self.assertEqual(result['completion'], 'success')

    def test_simulate_memory_intensive_operations(self):
        """Test memory intensive operations simulation"""
        result = self.demo.simulate_memory_intensive_operations()
        
        self.assertEqual(result['operation'], 'memory_intensive_operations')
        self.assertEqual(result['records_processed'], 100000)
        self.assertEqual(result['memory_peak'], 'tracked')

    @patch('time.sleep')
    def test_simulate_error_scenarios(self, mock_sleep):
        """Test error scenarios simulation"""
        result = self.demo.simulate_error_scenarios()
        
        self.assertEqual(result['operation'], 'error_scenarios')
        self.assertEqual(result['scenarios_tested'], 3)
        self.assertEqual(result['errors_handled'], 'success')

    def test_generate_recommendations(self):
        """Test recommendation generation"""
        # Test with slow operations
        metrics = [
            {'operation_name': 'slow_op', 'duration': 2.0, 'memory_mb': 50},
            {'operation_name': 'fast_op', 'duration': 0.1, 'memory_mb': 10}
        ]
        
        recommendations = self.demo._generate_recommendations(metrics)
        self.assertTrue(any('slow operations' in rec for rec in recommendations))

        # Test with high memory operations
        metrics = [
            {'operation_name': 'memory_op', 'duration': 0.5, 'memory_mb': 150},
            {'operation_name': 'normal_op', 'duration': 0.1, 'memory_mb': 10}
        ]
        
        recommendations = self.demo._generate_recommendations(metrics)
        self.assertTrue(any('high memory' in rec for rec in recommendations))

        # Test with many queries
        metrics = [
            {'operation_name': f'query_{i}', 'duration': 0.1, 'memory_mb': 10}
            for i in range(10)
        ]
        
        recommendations = self.demo._generate_recommendations(metrics)
        self.assertTrue(any('N+1 query' in rec for rec in recommendations))

    @patch.object(PerformanceDemo, 'simulate_database_operations')
    @patch.object(PerformanceDemo, 'simulate_api_requests')
    @patch.object(PerformanceDemo, 'simulate_concurrent_operations')
    @patch.object(PerformanceDemo, 'simulate_memory_intensive_operations')
    @patch.object(PerformanceDemo, 'simulate_error_scenarios')
    def test_run_full_demo(self, mock_error, mock_memory, mock_concurrent, mock_api, mock_db):
        """Test the full demo execution"""
        # Mock all scenario methods
        mock_db.return_value = {'operation': 'database_operations'}
        mock_api.return_value = {'operation': 'api_requests'}
        mock_concurrent.return_value = {'operation': 'concurrent_operations'}
        mock_memory.return_value = {'operation': 'memory_intensive_operations'}
        mock_error.return_value = {'operation': 'error_scenarios'}

        # Mock performance metrics
        with patch.object(self.demo.monitor, 'get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = [
                {'operation_name': 'test_op', 'duration': 0.5, 'memory_mb': 25}
            ]
            
            result = self.demo.run_full_demo()
            
            self.assertIn('demo_execution', result)
            self.assertIn('scenario_results', result)
            self.assertIn('performance_report', result)
            
            # Verify all scenarios were called
            mock_db.assert_called_once()
            mock_api.assert_called_once()
            mock_concurrent.assert_called_once()
            mock_memory.assert_called_once()
            mock_error.assert_called_once()


class PerformanceDemoIntegrationTestCase(TestCase):
    """Integration tests for the performance demo"""

    def test_demo_runs_without_errors(self):
        """Test that the demo can run without throwing exceptions"""
        demo = PerformanceDemo()
        
        # This should not raise any exceptions
        try:
            # Run a minimal version to avoid long execution times in tests
            with patch('time.sleep'):  # Mock sleep to speed up tests
                result = demo.simulate_database_operations()
                self.assertIsInstance(result, dict)
                self.assertIn('operation', result)
        except Exception as e:
            self.fail(f"Demo raised an unexpected exception: {e}")

    def test_performance_report_generation(self):
        """Test that performance reports can be generated"""
        demo = PerformanceDemo()
        
        # Add some mock metrics
        demo.monitor.metrics = [
            {
                'operation_name': 'test_operation',
                'duration': 0.5,
                'memory_mb': 25,
                'timestamp': '2024-01-01T00:00:00'
            }
        ]
        
        report = demo.generate_performance_report()
        
        self.assertIn('summary', report)
        self.assertIn('detailed_metrics', report)
        self.assertIn('recommendations', report)
        
        # Verify summary statistics
        summary = report['summary']
        self.assertEqual(summary['total_operations'], 1)
        self.assertEqual(summary['avg_execution_time'], 0.5)
        self.assertEqual(summary['avg_memory_usage'], 25)