"""
API Performance Monitoring and Load Testing

Provides comprehensive performance testing capabilities including
load testing, stress testing, and performance monitoring for API endpoints.
"""

import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APITestClient, APIResponse
from core.interfaces import Environment


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    concurrent_users: int = 10
    duration_seconds: int = 60
    ramp_up_seconds: int = 10
    ramp_down_seconds: int = 10
    requests_per_second: Optional[float] = None
    max_requests: Optional[int] = None
    think_time_seconds: float = 0.0
    
    def validate(self) -> List[str]:
        """Validate load test configuration"""
        errors = []
        
        if self.concurrent_users <= 0:
            errors.append("concurrent_users must be positive")
        
        if self.duration_seconds <= 0:
            errors.append("duration_seconds must be positive")
        
        if self.ramp_up_seconds < 0:
            errors.append("ramp_up_seconds cannot be negative")
        
        if self.ramp_down_seconds < 0:
            errors.append("ramp_down_seconds cannot be negative")
        
        if self.requests_per_second is not None and self.requests_per_second <= 0:
            errors.append("requests_per_second must be positive")
        
        if self.max_requests is not None and self.max_requests <= 0:
            errors.append("max_requests must be positive")
        
        if self.think_time_seconds < 0:
            errors.append("think_time_seconds cannot be negative")
        
        return errors


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single request"""
    timestamp: datetime
    response_time: float
    status_code: int
    success: bool
    error_message: Optional[str] = None
    thread_id: int = 0
    
    @property
    def is_success(self) -> bool:
        """Check if request was successful"""
        return self.success and 200 <= self.status_code < 400


@dataclass
class LoadTestResults:
    """Results from load testing"""
    config: LoadTestConfig
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    metrics: List[PerformanceMetrics] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Actual test duration"""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def requests_per_second(self) -> float:
        """Actual requests per second"""
        if self.duration_seconds == 0:
            return 0.0
        return self.total_requests / self.duration_seconds
    
    @property
    def response_times(self) -> List[float]:
        """List of all response times"""
        return [m.response_time for m in self.metrics]
    
    @property
    def successful_response_times(self) -> List[float]:
        """List of successful response times only"""
        return [m.response_time for m in self.metrics if m.is_success]
    
    def get_response_time_stats(self) -> Dict[str, float]:
        """Get response time statistics"""
        times = self.successful_response_times
        if not times:
            return {}
        
        return {
            'min': min(times),
            'max': max(times),
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'p90': self._percentile(times, 90),
            'p95': self._percentile(times, 95),
            'p99': self._percentile(times, 99),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by type"""
        error_counts = {}
        for metric in self.metrics:
            if not metric.is_success and metric.error_message:
                error_counts[metric.error_message] = error_counts.get(metric.error_message, 0) + 1
        return error_counts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary"""
        return {
            'config': {
                'concurrent_users': self.config.concurrent_users,
                'duration_seconds': self.config.duration_seconds,
                'ramp_up_seconds': self.config.ramp_up_seconds,
                'ramp_down_seconds': self.config.ramp_down_seconds,
                'requests_per_second': self.config.requests_per_second,
                'max_requests': self.config.max_requests,
                'think_time_seconds': self.config.think_time_seconds,
            },
            'summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'duration_seconds': self.duration_seconds,
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': self.success_rate,
                'requests_per_second': self.requests_per_second,
            },
            'response_times': self.get_response_time_stats(),
            'errors': self.get_error_summary(),
        }


class LoadTester:
    """Load testing engine for API endpoints"""
    
    def __init__(self, base_url: str, environment: str = "development"):
        self.base_url = base_url
        self.environment = environment
        self.logger = logging.getLogger(f'load_tester_{environment}')
        self._stop_event = threading.Event()
        
    def run_load_test(self, test_scenario: Callable[[APITestClient], APIResponse],
                     config: LoadTestConfig, auth_data: Optional[Dict[str, Any]] = None) -> LoadTestResults:
        """
        Run load test with specified scenario
        
        Args:
            test_scenario: Function that takes APITestClient and returns APIResponse
            config: Load test configuration
            auth_data: Authentication data for test users
            
        Returns:
            LoadTestResults: Comprehensive test results
        """
        # Validate configuration
        config_errors = config.validate()
        if config_errors:
            raise ValueError(f"Invalid load test configuration: {', '.join(config_errors)}")
        
        self.logger.info(f"Starting load test with {config.concurrent_users} users for {config.duration_seconds}s")
        
        # Initialize results
        results = LoadTestResults(
            config=config,
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_requests=0,
            successful_requests=0,
            failed_requests=0
        )
        
        # Reset stop event
        self._stop_event.clear()
        
        try:
            # Run the load test
            self._execute_load_test(test_scenario, config, auth_data, results)
            
        except Exception as e:
            self.logger.error(f"Load test execution error: {str(e)}")
            results.errors.append(str(e))
        
        finally:
            results.end_time = datetime.now()
            self.logger.info(f"Load test completed. Total requests: {results.total_requests}, "
                           f"Success rate: {results.success_rate:.1f}%")
        
        return results
    
    def _execute_load_test(self, test_scenario: Callable[[APITestClient], APIResponse],
                          config: LoadTestConfig, auth_data: Optional[Dict[str, Any]],
                          results: LoadTestResults):
        """Execute the actual load test"""
        
        # Calculate timing
        test_start = time.time()
        ramp_up_end = test_start + config.ramp_up_seconds
        test_end = test_start + config.duration_seconds
        ramp_down_start = test_end - config.ramp_down_seconds
        
        # Thread-safe metrics collection
        metrics_lock = threading.Lock()
        
        def worker_thread(thread_id: int, start_delay: float):
            """Worker thread for load testing"""
            # Wait for ramp-up delay
            time.sleep(start_delay)
            
            # Create client for this thread
            client = APITestClient(self.base_url, Environment.DEVELOPMENT if isinstance(self.environment, str) else self.environment)
            
            # Authenticate if auth data provided
            if auth_data:
                try:
                    if 'username' in auth_data and 'password' in auth_data:
                        client.authenticate_jwt(auth_data['username'], auth_data['password'])
                    elif 'api_key' in auth_data:
                        client.authenticate_api_key(auth_data['api_key'])
                except Exception as e:
                    self.logger.warning(f"Thread {thread_id} authentication failed: {str(e)}")
            
            request_count = 0
            last_request_time = time.time()
            
            while not self._stop_event.is_set():
                current_time = time.time()
                
                # Check if we're past the test end time
                if current_time > test_end:
                    break
                
                # Check if we're in ramp-down phase
                if current_time > ramp_down_start:
                    # Gradually reduce load during ramp-down
                    ramp_down_progress = (current_time - ramp_down_start) / config.ramp_down_seconds
                    if ramp_down_progress > thread_id / config.concurrent_users:
                        break
                
                # Rate limiting
                if config.requests_per_second:
                    min_interval = config.concurrent_users / config.requests_per_second
                    elapsed = current_time - last_request_time
                    if elapsed < min_interval:
                        time.sleep(min_interval - elapsed)
                
                # Max requests check
                if config.max_requests and request_count >= config.max_requests:
                    break
                
                # Execute test scenario
                try:
                    start_time = time.time()
                    response = test_scenario(client)
                    end_time = time.time()
                    
                    # Create performance metric
                    metric = PerformanceMetrics(
                        timestamp=datetime.now(),
                        response_time=end_time - start_time,
                        status_code=response.status_code,
                        success=response.is_success,
                        thread_id=thread_id
                    )
                    
                    # Thread-safe metrics collection
                    with metrics_lock:
                        results.metrics.append(metric)
                        results.total_requests += 1
                        if metric.is_success:
                            results.successful_requests += 1
                        else:
                            results.failed_requests += 1
                    
                    request_count += 1
                    last_request_time = end_time
                    
                    # Think time
                    if config.think_time_seconds > 0:
                        time.sleep(config.think_time_seconds)
                
                except Exception as e:
                    error_msg = str(e)
                    metric = PerformanceMetrics(
                        timestamp=datetime.now(),
                        response_time=0.0,
                        status_code=0,
                        success=False,
                        error_message=error_msg,
                        thread_id=thread_id
                    )
                    
                    with metrics_lock:
                        results.metrics.append(metric)
                        results.total_requests += 1
                        results.failed_requests += 1
                    
                    self.logger.warning(f"Thread {thread_id} request failed: {error_msg}")
        
        # Start worker threads with ramp-up
        with ThreadPoolExecutor(max_workers=config.concurrent_users) as executor:
            futures = []
            
            for i in range(config.concurrent_users):
                # Calculate ramp-up delay for this thread
                if config.ramp_up_seconds > 0:
                    delay = (i / config.concurrent_users) * config.ramp_up_seconds
                else:
                    delay = 0.0
                
                future = executor.submit(worker_thread, i, delay)
                futures.append(future)
            
            # Wait for test duration
            time.sleep(config.duration_seconds)
            
            # Signal threads to stop
            self._stop_event.set()
            
            # Wait for all threads to complete
            for future in as_completed(futures, timeout=30):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Worker thread error: {str(e)}")
    
    def run_stress_test(self, test_scenario: Callable[[APITestClient], APIResponse],
                       max_users: int = 100, step_size: int = 10, step_duration: int = 30,
                       auth_data: Optional[Dict[str, Any]] = None) -> List[LoadTestResults]:
        """
        Run stress test by gradually increasing load
        
        Args:
            test_scenario: Function that takes APITestClient and returns APIResponse
            max_users: Maximum number of concurrent users
            step_size: Number of users to add in each step
            step_duration: Duration of each step in seconds
            auth_data: Authentication data for test users
            
        Returns:
            List[LoadTestResults]: Results for each step
        """
        self.logger.info(f"Starting stress test up to {max_users} users")
        
        results = []
        current_users = step_size
        
        while current_users <= max_users:
            self.logger.info(f"Stress test step: {current_users} users")
            
            config = LoadTestConfig(
                concurrent_users=current_users,
                duration_seconds=step_duration,
                ramp_up_seconds=min(10, step_duration // 3),
                ramp_down_seconds=min(5, step_duration // 6)
            )
            
            step_results = self.run_load_test(test_scenario, config, auth_data)
            results.append(step_results)
            
            # Check if system is breaking down
            if step_results.success_rate < 50:
                self.logger.warning(f"System breaking down at {current_users} users (success rate: {step_results.success_rate:.1f}%)")
                break
            
            current_users += step_size
        
        return results
    
    def run_spike_test(self, test_scenario: Callable[[APITestClient], APIResponse],
                      baseline_users: int = 10, spike_users: int = 100, spike_duration: int = 60,
                      auth_data: Optional[Dict[str, Any]] = None) -> Tuple[LoadTestResults, LoadTestResults]:
        """
        Run spike test with sudden load increase
        
        Args:
            test_scenario: Function that takes APITestClient and returns APIResponse
            baseline_users: Normal load user count
            spike_users: Spike load user count
            spike_duration: Duration of spike in seconds
            auth_data: Authentication data for test users
            
        Returns:
            Tuple[LoadTestResults, LoadTestResults]: Baseline and spike results
        """
        self.logger.info(f"Starting spike test: {baseline_users} -> {spike_users} users")
        
        # Run baseline test
        baseline_config = LoadTestConfig(
            concurrent_users=baseline_users,
            duration_seconds=60,
            ramp_up_seconds=10,
            ramp_down_seconds=5
        )
        
        baseline_results = self.run_load_test(test_scenario, baseline_config, auth_data)
        
        # Run spike test
        spike_config = LoadTestConfig(
            concurrent_users=spike_users,
            duration_seconds=spike_duration,
            ramp_up_seconds=5,  # Quick ramp-up for spike
            ramp_down_seconds=5
        )
        
        spike_results = self.run_load_test(test_scenario, spike_config, auth_data)
        
        return baseline_results, spike_results


class PerformanceMonitor:
    """Real-time performance monitoring for API endpoints"""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.monitoring_active = False
        self.monitor_thread = None
        self.logger = logging.getLogger('performance_monitor')
    
    def start_monitoring(self, client: APITestClient, endpoint: str, interval_seconds: float = 1.0):
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(client, endpoint, interval_seconds),
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info(f"Started monitoring {endpoint} every {interval_seconds}s")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Stopped performance monitoring")
    
    def _monitor_loop(self, client: APITestClient, endpoint: str, interval_seconds: float):
        """Monitoring loop"""
        while self.monitoring_active:
            try:
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                metric = PerformanceMetrics(
                    timestamp=datetime.now(),
                    response_time=end_time - start_time,
                    status_code=response.status_code,
                    success=response.is_success
                )
                
                self.metrics_history.append(metric)
                
                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                time.sleep(interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {str(e)}")
                time.sleep(interval_seconds)
    
    def get_current_metrics(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Get performance metrics for recent time window"""
        if not self.metrics_history:
            return {}
        
        # Filter metrics within time window
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        response_times = [m.response_time for m in recent_metrics if m.is_success]
        success_count = len([m for m in recent_metrics if m.is_success])
        total_count = len(recent_metrics)
        
        return {
            'window_minutes': window_minutes,
            'total_requests': total_count,
            'successful_requests': success_count,
            'success_rate': (success_count / total_count * 100) if total_count > 0 else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'requests_per_minute': total_count / window_minutes if window_minutes > 0 else 0,
        }
    
    def clear_history(self):
        """Clear metrics history"""
        self.metrics_history.clear()


class APIPerformanceTester:
    """High-level API performance testing interface"""
    
    def __init__(self, base_url: str, environment: str = "development"):
        self.load_tester = LoadTester(base_url, environment)
        self.monitor = PerformanceMonitor()
        self.logger = logging.getLogger(f'api_performance_tester_{environment}')
    
    def test_endpoint_performance(self, endpoint: str, method: str = 'GET',
                                 data: Optional[Dict[str, Any]] = None,
                                 auth_data: Optional[Dict[str, Any]] = None,
                                 concurrent_users: int = 10, duration_seconds: int = 60) -> LoadTestResults:
        """Test single endpoint performance"""
        
        def test_scenario(client: APITestClient) -> APIResponse:
            if method.upper() == 'GET':
                return client.get(endpoint)
            elif method.upper() == 'POST':
                return client.post(endpoint, data=data)
            elif method.upper() == 'PUT':
                return client.put(endpoint, data=data)
            elif method.upper() == 'DELETE':
                return client.delete(endpoint)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        
        config = LoadTestConfig(
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            ramp_up_seconds=min(10, duration_seconds // 6),
            ramp_down_seconds=min(5, duration_seconds // 12)
        )
        
        return self.load_tester.run_load_test(test_scenario, config, auth_data)
    
    def test_user_journey_performance(self, journey_steps: List[Dict[str, Any]],
                                    auth_data: Optional[Dict[str, Any]] = None,
                                    concurrent_users: int = 5, duration_seconds: int = 120) -> LoadTestResults:
        """Test complete user journey performance"""
        
        def journey_scenario(client: APITestClient) -> APIResponse:
            last_response = None
            
            for step in journey_steps:
                endpoint = step['endpoint']
                method = step.get('method', 'GET')
                data = step.get('data')
                
                if method.upper() == 'GET':
                    last_response = client.get(endpoint)
                elif method.upper() == 'POST':
                    last_response = client.post(endpoint, data=data)
                elif method.upper() == 'PUT':
                    last_response = client.put(endpoint, data=data)
                elif method.upper() == 'DELETE':
                    last_response = client.delete(endpoint)
                
                # Add think time between steps
                think_time = step.get('think_time', 1.0)
                if think_time > 0:
                    time.sleep(think_time)
            
            return last_response or APIResponse(200, {}, {}, 0.0, "", "GET", {})
        
        config = LoadTestConfig(
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            ramp_up_seconds=min(20, duration_seconds // 6),
            ramp_down_seconds=min(10, duration_seconds // 12),
            think_time_seconds=2.0  # Additional think time between journey iterations
        )
        
        return self.load_tester.run_load_test(journey_scenario, config, auth_data)