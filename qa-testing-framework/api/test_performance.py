"""
Unit tests for API Performance Testing

Tests the performance testing capabilities including load testing,
stress testing, and performance monitoring.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.performance import (
    LoadTestConfig, PerformanceMetrics, LoadTestResults,
    LoadTester, PerformanceMonitor, APIPerformanceTester
)
from api.client import APITestClient, APIResponse


class TestLoadTestConfig:
    """Test LoadTestConfig class"""
    
    def test_load_test_config_creation(self):
        """Test LoadTestConfig object creation"""
        config = LoadTestConfig(
            concurrent_users=10,
            duration_seconds=60,
            ramp_up_seconds=10,
            ramp_down_seconds=5
        )
        
        assert config.concurrent_users == 10
        assert config.duration_seconds == 60
        assert config.ramp_up_seconds == 10
        assert config.ramp_down_seconds == 5
    
    def test_load_test_config_validation_valid(self):
        """Test valid configuration validation"""
        config = LoadTestConfig(
            concurrent_users=5,
            duration_seconds=30,
            ramp_up_seconds=5,
            ramp_down_seconds=5,
            requests_per_second=10.0,
            max_requests=100,
            think_time_seconds=1.0
        )
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_load_test_config_validation_invalid(self):
        """Test invalid configuration validation"""
        config = LoadTestConfig(
            concurrent_users=-1,  # Invalid
            duration_seconds=0,   # Invalid
            ramp_up_seconds=-5,   # Invalid
            requests_per_second=-10.0,  # Invalid
            max_requests=0,       # Invalid
            think_time_seconds=-1.0  # Invalid
        )
        
        errors = config.validate()
        assert len(errors) > 0
        assert any('concurrent_users' in error for error in errors)
        assert any('duration_seconds' in error for error in errors)


class TestPerformanceMetrics:
    """Test PerformanceMetrics class"""
    
    def test_performance_metrics_creation(self):
        """Test PerformanceMetrics object creation"""
        timestamp = datetime.now()
        metrics = PerformanceMetrics(
            timestamp=timestamp,
            response_time=0.5,
            status_code=200,
            success=True,
            thread_id=1
        )
        
        assert metrics.timestamp == timestamp
        assert metrics.response_time == 0.5
        assert metrics.status_code == 200
        assert metrics.success
        assert metrics.is_success
        assert metrics.thread_id == 1
    
    def test_performance_metrics_is_success(self):
        """Test is_success property"""
        # Successful metrics
        success_metrics = PerformanceMetrics(
            datetime.now(), 0.5, 200, True
        )
        assert success_metrics.is_success
        
        # Failed metrics (success=False)
        failed_metrics = PerformanceMetrics(
            datetime.now(), 0.5, 200, False
        )
        assert not failed_metrics.is_success
        
        # Failed metrics (error status code)
        error_metrics = PerformanceMetrics(
            datetime.now(), 0.5, 500, True
        )
        assert not error_metrics.is_success


class TestLoadTestResults:
    """Test LoadTestResults class"""
    
    def setup_method(self):
        """Setup test results"""
        self.config = LoadTestConfig(concurrent_users=5, duration_seconds=30)
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=30)
        
        self.results = LoadTestResults(
            config=self.config,
            start_time=self.start_time,
            end_time=self.end_time,
            total_requests=100,
            successful_requests=95,
            failed_requests=5
        )
    
    def test_load_test_results_properties(self):
        """Test LoadTestResults calculated properties"""
        assert self.results.duration_seconds == 30.0
        assert self.results.success_rate == 95.0
        assert abs(self.results.requests_per_second - (100/30)) < 0.01
    
    def test_response_time_stats(self):
        """Test response time statistics calculation"""
        # Add some metrics
        metrics = [
            PerformanceMetrics(datetime.now(), 0.1, 200, True),
            PerformanceMetrics(datetime.now(), 0.2, 200, True),
            PerformanceMetrics(datetime.now(), 0.3, 200, True),
            PerformanceMetrics(datetime.now(), 0.4, 200, True),
            PerformanceMetrics(datetime.now(), 0.5, 200, True),
            PerformanceMetrics(datetime.now(), 1.0, 500, False),  # Failed request
        ]
        
        self.results.metrics = metrics
        
        stats = self.results.get_response_time_stats()
        
        assert 'min' in stats
        assert 'max' in stats
        assert 'mean' in stats
        assert 'median' in stats
        assert 'p90' in stats
        assert 'p95' in stats
        assert 'p99' in stats
        
        # Should only include successful requests
        assert stats['min'] == 0.1
        assert stats['max'] == 0.5
        assert stats['mean'] == 0.3  # (0.1+0.2+0.3+0.4+0.5)/5
    
    def test_error_summary(self):
        """Test error summary generation"""
        metrics = [
            PerformanceMetrics(datetime.now(), 0.1, 200, True),
            PerformanceMetrics(datetime.now(), 0.0, 0, False, "Connection timeout"),
            PerformanceMetrics(datetime.now(), 0.0, 0, False, "Connection timeout"),
            PerformanceMetrics(datetime.now(), 0.0, 500, False, "Server error"),
        ]
        
        self.results.metrics = metrics
        
        error_summary = self.results.get_error_summary()
        
        assert "Connection timeout" in error_summary
        assert error_summary["Connection timeout"] == 2
        assert "Server error" in error_summary
        assert error_summary["Server error"] == 1
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        result_dict = self.results.to_dict()
        
        assert 'config' in result_dict
        assert 'summary' in result_dict
        assert 'response_times' in result_dict
        assert 'errors' in result_dict
        
        assert result_dict['summary']['total_requests'] == 100
        assert result_dict['summary']['success_rate'] == 95.0


class TestLoadTester:
    """Test LoadTester class"""
    
    def setup_method(self):
        """Setup test load tester"""
        self.load_tester = LoadTester('http://test.com', 'test')
    
    def test_load_tester_initialization(self):
        """Test LoadTester initialization"""
        assert self.load_tester.base_url == 'http://test.com'
        assert self.load_tester.environment == 'test'
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_run_load_test_basic(self, mock_sleep):
        """Test basic load test execution"""
        # Mock test scenario
        def mock_scenario(client):
            return APIResponse(200, {}, {'data': 'test'}, 0.1, 'http://test.com/api', 'GET', {})
        
        # Short test configuration
        config = LoadTestConfig(
            concurrent_users=2,
            duration_seconds=1,  # Very short for testing
            ramp_up_seconds=0,
            ramp_down_seconds=0
        )
        
        results = self.load_tester.run_load_test(mock_scenario, config)
        
        assert isinstance(results, LoadTestResults)
        assert results.config == config
        assert results.total_requests >= 0
    
    def test_run_load_test_invalid_config(self):
        """Test load test with invalid configuration"""
        def mock_scenario(client):
            return APIResponse(200, {}, {}, 0.1, '', 'GET', {})
        
        # Invalid configuration
        config = LoadTestConfig(concurrent_users=-1)
        
        with pytest.raises(ValueError):
            self.load_tester.run_load_test(mock_scenario, config)
    
    @patch('time.sleep')
    def test_run_stress_test(self, mock_sleep):
        """Test stress test execution"""
        def mock_scenario(client):
            return APIResponse(200, {}, {'data': 'test'}, 0.1, 'http://test.com/api', 'GET', {})
        
        results = self.load_tester.run_stress_test(
            mock_scenario,
            max_users=4,
            step_size=2,
            step_duration=1  # Very short for testing
        )
        
        assert isinstance(results, list)
        assert len(results) >= 1  # At least one step should run
        
        for result in results:
            assert isinstance(result, LoadTestResults)
    
    @patch('time.sleep')
    def test_run_spike_test(self, mock_sleep):
        """Test spike test execution"""
        def mock_scenario(client):
            return APIResponse(200, {}, {'data': 'test'}, 0.1, 'http://test.com/api', 'GET', {})
        
        baseline_results, spike_results = self.load_tester.run_spike_test(
            mock_scenario,
            baseline_users=2,
            spike_users=4,
            spike_duration=1  # Very short for testing
        )
        
        assert isinstance(baseline_results, LoadTestResults)
        assert isinstance(spike_results, LoadTestResults)
        assert baseline_results.config.concurrent_users == 2
        assert spike_results.config.concurrent_users == 4


class TestPerformanceMonitor:
    """Test PerformanceMonitor class"""
    
    def setup_method(self):
        """Setup test monitor"""
        self.monitor = PerformanceMonitor()
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization"""
        assert len(self.monitor.metrics_history) == 0
        assert not self.monitor.monitoring_active
        assert self.monitor.monitor_thread is None
    
    @patch('qa_testing_framework.api.client.APITestClient.get')
    def test_start_stop_monitoring(self, mock_get):
        """Test starting and stopping monitoring"""
        # Mock successful response
        mock_get.return_value = APIResponse(200, {}, {'data': 'test'}, 0.1, 'http://test.com/api', 'GET', {})
        
        # Create mock client
        mock_client = Mock()
        mock_client.get = mock_get
        
        # Start monitoring
        self.monitor.start_monitoring(mock_client, '/api/test', 0.1)
        
        assert self.monitor.monitoring_active
        assert self.monitor.monitor_thread is not None
        
        # Let it run briefly
        time.sleep(0.2)
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        assert not self.monitor.monitoring_active
        assert len(self.monitor.metrics_history) > 0
    
    def test_get_current_metrics_empty(self):
        """Test getting metrics when history is empty"""
        metrics = self.monitor.get_current_metrics()
        
        assert metrics == {}
    
    def test_get_current_metrics_with_data(self):
        """Test getting metrics with data"""
        # Add some test metrics
        now = datetime.now()
        metrics = [
            PerformanceMetrics(now, 0.1, 200, True),
            PerformanceMetrics(now, 0.2, 200, True),
            PerformanceMetrics(now, 0.3, 500, False),
        ]
        
        self.monitor.metrics_history = metrics
        
        current_metrics = self.monitor.get_current_metrics(window_minutes=10)
        
        assert 'total_requests' in current_metrics
        assert 'successful_requests' in current_metrics
        assert 'success_rate' in current_metrics
        assert 'avg_response_time' in current_metrics
        
        assert current_metrics['total_requests'] == 3
        assert current_metrics['successful_requests'] == 2
        assert abs(current_metrics['success_rate'] - 66.67) < 0.1
    
    def test_clear_history(self):
        """Test clearing metrics history"""
        # Add some test data
        self.monitor.metrics_history.append(
            PerformanceMetrics(datetime.now(), 0.1, 200, True)
        )
        
        assert len(self.monitor.metrics_history) == 1
        
        self.monitor.clear_history()
        
        assert len(self.monitor.metrics_history) == 0


class TestAPIPerformanceTester:
    """Test APIPerformanceTester class"""
    
    def setup_method(self):
        """Setup test performance tester"""
        self.tester = APIPerformanceTester('http://test.com', 'test')
    
    def test_api_performance_tester_initialization(self):
        """Test APIPerformanceTester initialization"""
        assert self.tester.load_tester.base_url == 'http://test.com'
        assert isinstance(self.tester.monitor, PerformanceMonitor)
    
    @patch('qa_testing_framework.api.performance.LoadTester.run_load_test')
    def test_test_endpoint_performance(self, mock_run_load_test):
        """Test endpoint performance testing"""
        # Mock load test results
        mock_results = LoadTestResults(
            config=LoadTestConfig(),
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_requests=100,
            successful_requests=95,
            failed_requests=5
        )
        mock_run_load_test.return_value = mock_results
        
        results = self.tester.test_endpoint_performance(
            '/api/test',
            method='GET',
            concurrent_users=5,
            duration_seconds=30
        )
        
        assert results == mock_results
        mock_run_load_test.assert_called_once()
    
    @patch('qa_testing_framework.api.performance.LoadTester.run_load_test')
    def test_test_user_journey_performance(self, mock_run_load_test):
        """Test user journey performance testing"""
        # Mock load test results
        mock_results = LoadTestResults(
            config=LoadTestConfig(),
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_requests=50,
            successful_requests=48,
            failed_requests=2
        )
        mock_run_load_test.return_value = mock_results
        
        journey_steps = [
            {'endpoint': '/api/login', 'method': 'POST', 'data': {'username': 'test'}},
            {'endpoint': '/api/products', 'method': 'GET', 'think_time': 1.0},
            {'endpoint': '/api/cart', 'method': 'POST', 'data': {'product_id': 1}}
        ]
        
        results = self.tester.test_user_journey_performance(
            journey_steps,
            concurrent_users=3,
            duration_seconds=60
        )
        
        assert results == mock_results
        mock_run_load_test.assert_called_once()
    
    def test_unsupported_http_method(self):
        """Test endpoint performance with unsupported HTTP method"""
        with pytest.raises(ValueError):
            self.tester.test_endpoint_performance(
                '/api/test',
                method='INVALID',
                concurrent_users=1,
                duration_seconds=1
            )


class TestPerformanceIntegration:
    """Integration tests for performance testing components"""
    
    @patch('requests.Session.request')
    def test_end_to_end_performance_test(self, mock_request):
        """Test end-to-end performance testing flow"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'data': 'test'}
        mock_request.return_value = mock_response
        
        # Create performance tester
        tester = APIPerformanceTester('http://test.com', 'test')
        
        # Run a very short performance test
        results = tester.test_endpoint_performance(
            '/api/test',
            method='GET',
            concurrent_users=2,
            duration_seconds=1
        )
        
        # Verify results
        assert isinstance(results, LoadTestResults)
        assert results.total_requests > 0
        assert results.success_rate >= 0
        
        # Verify HTTP requests were made
        assert mock_request.called


if __name__ == '__main__':
    pytest.main([__file__])