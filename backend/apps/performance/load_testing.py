# Performance Load Testing and Benchmarking
import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
import json
import logging

from .models import PerformanceBenchmark, PerformanceMetric

logger = logging.getLogger(__name__)

class LoadTestRunner:
    """Load testing and performance benchmarking"""
    
    def __init__(self):
        self.results = []
        self.errors = []
    
    async def run_load_test(self, config):
        """Run load test with given configuration"""
        test_config = {
            'url': config.get('url', 'http://localhost:8000/api/'),
            'concurrent_users': config.get('concurrent_users', 10),
            'duration': config.get('duration', 60),  # seconds
            'ramp_up_time': config.get('ramp_up_time', 10),
            'method': config.get('method', 'GET'),
            'headers': config.get('headers', {}),
            'payload': config.get('payload', None)
        }
        
        start_time = time.time()
        tasks = []
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(test_config['concurrent_users'])
        
        async with aiohttp.ClientSession() as session:
            # Ramp up users gradually
            for i in range(test_config['concurrent_users']):
                await asyncio.sleep(test_config['ramp_up_time'] / test_config['concurrent_users'])
                task = asyncio.create_task(
                    self._user_session(session, test_config, semaphore, start_time)
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return self._analyze_results()
    
    async def _user_session(self, session, config, semaphore, start_time):
        """Simulate a user session"""
        end_time = start_time + config['duration']
        
        while time.time() < end_time:
            async with semaphore:
                try:
                    request_start = time.time()
                    
                    async with session.request(
                        config['method'],
                        config['url'],
                        headers=config['headers'],
                        json=config['payload']
                    ) as response:
                        await response.text()
                        request_end = time.time()
                        
                        self.results.append({
                            'timestamp': request_start,
                            'response_time': (request_end - request_start) * 1000,  # ms
                            'status_code': response.status,
                            'success': 200 <= response.status < 400
                        })
                        
                except Exception as e:
                    self.errors.append({
                        'timestamp': time.time(),
                        'error': str(e)
                    })
            
            # Small delay between requests
            await asyncio.sleep(0.1)
    
    def _analyze_results(self):
        """Analyze load test results"""
        if not self.results:
            return {'error': 'No results collected'}
        
        response_times = [r['response_time'] for r in self.results]
        successful_requests = [r for r in self.results if r['success']]
        
        total_requests = len(self.results)
        successful_count = len(successful_requests)
        error_count = len(self.errors)
        
        analysis = {
            'summary': {
                'total_requests': total_requests,
                'successful_requests': successful_count,
                'failed_requests': total_requests - successful_count,
                'errors': error_count,
                'success_rate': (successful_count / total_requests) * 100 if total_requests > 0 else 0
            },
            'response_times': {
                'min': min(response_times),
                'max': max(response_times),
                'avg': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p95': self._percentile(response_times, 95),
                'p99': self._percentile(response_times, 99)
            },
            'throughput': {
                'requests_per_second': total_requests / (max([r['timestamp'] for r in self.results]) - min([r['timestamp'] for r in self.results])) if total_requests > 1 else 0
            }
        }
        
        return analysis
    
    def _percentile(self, data, percentile):
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class PerformanceRegressionTester:
    """Performance regression testing"""
    
    def __init__(self):
        self.baseline_metrics = {}
        self.current_metrics = {}
    
    def set_baseline(self, test_name, metrics):
        """Set baseline performance metrics"""
        self.baseline_metrics[test_name] = {
            'timestamp': timezone.now(),
            'metrics': metrics
        }
    
    def run_regression_test(self, test_name, test_config):
        """Run regression test and compare with baseline"""
        # Run current test
        runner = LoadTestRunner()
        current_results = asyncio.run(runner.run_load_test(test_config))
        
        self.current_metrics[test_name] = {
            'timestamp': timezone.now(),
            'metrics': current_results
        }
        
        # Compare with baseline
        if test_name in self.baseline_metrics:
            return self._compare_metrics(test_name)
        else:
            return {'warning': 'No baseline found for comparison'}
    
    def _compare_metrics(self, test_name):
        """Compare current metrics with baseline"""
        baseline = self.baseline_metrics[test_name]['metrics']
        current = self.current_metrics[test_name]['metrics']
        
        comparison = {
            'test_name': test_name,
            'baseline_timestamp': self.baseline_metrics[test_name]['timestamp'],
            'current_timestamp': self.current_metrics[test_name]['timestamp'],
            'regression_detected': False,
            'improvements': [],
            'regressions': [],
            'metrics_comparison': {}
        }
        
        # Compare response times
        baseline_avg = baseline['response_times']['avg']
        current_avg = current['response_times']['avg']
        
        response_time_change = ((current_avg - baseline_avg) / baseline_avg) * 100
        
        comparison['metrics_comparison']['response_time'] = {
            'baseline': baseline_avg,
            'current': current_avg,
            'change_percent': response_time_change
        }
        
        if response_time_change > 10:  # 10% regression threshold
            comparison['regression_detected'] = True
            comparison['regressions'].append({
                'metric': 'response_time',
                'change': response_time_change,
                'severity': 'high' if response_time_change > 25 else 'medium'
            })
        elif response_time_change < -5:  # 5% improvement
            comparison['improvements'].append({
                'metric': 'response_time',
                'improvement': abs(response_time_change)
            })
        
        # Compare success rates
        baseline_success = baseline['summary']['success_rate']
        current_success = current['summary']['success_rate']
        
        success_rate_change = current_success - baseline_success
        
        comparison['metrics_comparison']['success_rate'] = {
            'baseline': baseline_success,
            'current': current_success,
            'change_percent': success_rate_change
        }
        
        if success_rate_change < -2:  # 2% drop in success rate
            comparison['regression_detected'] = True
            comparison['regressions'].append({
                'metric': 'success_rate',
                'change': success_rate_change,
                'severity': 'critical' if success_rate_change < -5 else 'high'
            })
        
        return comparison


class SLAMonitor:
    """SLA monitoring and reporting"""
    
    def __init__(self):
        self.sla_definitions = {
            'response_time': {
                'target': 2000,  # 2 seconds
                'threshold': 95   # 95% of requests
            },
            'availability': {
                'target': 99.9    # 99.9% uptime
            },
            'error_rate': {
                'target': 1.0     # Less than 1% error rate
            }
        }
    
    def check_sla_compliance(self, start_date, end_date):
        """Check SLA compliance for given period"""
        compliance_report = {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'sla_status': {},
            'violations': [],
            'overall_compliance': True
        }
        
        # Check response time SLA
        response_time_compliance = self._check_response_time_sla(start_date, end_date)
        compliance_report['sla_status']['response_time'] = response_time_compliance
        
        if not response_time_compliance['compliant']:
            compliance_report['overall_compliance'] = False
            compliance_report['violations'].append(response_time_compliance)
        
        # Check availability SLA
        availability_compliance = self._check_availability_sla(start_date, end_date)
        compliance_report['sla_status']['availability'] = availability_compliance
        
        if not availability_compliance['compliant']:
            compliance_report['overall_compliance'] = False
            compliance_report['violations'].append(availability_compliance)
        
        # Check error rate SLA
        error_rate_compliance = self._check_error_rate_sla(start_date, end_date)
        compliance_report['sla_status']['error_rate'] = error_rate_compliance
        
        if not error_rate_compliance['compliant']:
            compliance_report['overall_compliance'] = False
            compliance_report['violations'].append(error_rate_compliance)
        
        return compliance_report
    
    def _check_response_time_sla(self, start_date, end_date):
        """Check response time SLA compliance"""
        from django.db.models import Count, Q
        
        total_requests = PerformanceMetric.objects.filter(
            metric_type='response_time',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).count()
        
        if total_requests == 0:
            return {
                'metric': 'response_time',
                'compliant': True,
                'reason': 'No data available'
            }
        
        fast_requests = PerformanceMetric.objects.filter(
            metric_type='response_time',
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            value__lte=self.sla_definitions['response_time']['target']
        ).count()
        
        compliance_percentage = (fast_requests / total_requests) * 100
        target_percentage = self.sla_definitions['response_time']['threshold']
        
        return {
            'metric': 'response_time',
            'compliant': compliance_percentage >= target_percentage,
            'actual': compliance_percentage,
            'target': target_percentage,
            'total_requests': total_requests,
            'fast_requests': fast_requests
        }
    
    def _check_availability_sla(self, start_date, end_date):
        """Check availability SLA compliance"""
        # This would integrate with uptime monitoring
        # For now, return mock data
        return {
            'metric': 'availability',
            'compliant': True,
            'actual': 99.95,
            'target': self.sla_definitions['availability']['target']
        }
    
    def _check_error_rate_sla(self, start_date, end_date):
        """Check error rate SLA compliance"""
        total_requests = PerformanceMetric.objects.filter(
            metric_type='response_time',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).count()
        
        if total_requests == 0:
            return {
                'metric': 'error_rate',
                'compliant': True,
                'reason': 'No data available'
            }
        
        error_requests = PerformanceMetric.objects.filter(
            metric_type='error_rate',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).count()
        
        error_rate = (error_requests / total_requests) * 100
        target_error_rate = self.sla_definitions['error_rate']['target']
        
        return {
            'metric': 'error_rate',
            'compliant': error_rate <= target_error_rate,
            'actual': error_rate,
            'target': target_error_rate,
            'total_requests': total_requests,
            'error_requests': error_requests
        }


class CostOptimizer:
    """Performance cost optimization"""
    
    def analyze_resource_costs(self):
        """Analyze resource usage costs"""
        analysis = {
            'cpu_cost_analysis': self._analyze_cpu_costs(),
            'memory_cost_analysis': self._analyze_memory_costs(),
            'storage_cost_analysis': self._analyze_storage_costs(),
            'network_cost_analysis': self._analyze_network_costs(),
            'recommendations': []
        }
        
        # Generate cost optimization recommendations
        analysis['recommendations'] = self._generate_cost_recommendations(analysis)
        
        return analysis
    
    def _analyze_cpu_costs(self):
        """Analyze CPU usage and costs"""
        # Mock implementation - would integrate with cloud provider APIs
        return {
            'current_usage': 65.5,
            'peak_usage': 89.2,
            'average_usage': 58.3,
            'estimated_monthly_cost': 450.00,
            'optimization_potential': 15.2  # percentage
        }
    
    def _analyze_memory_costs(self):
        """Analyze memory usage and costs"""
        return {
            'current_usage': 72.1,
            'peak_usage': 91.5,
            'average_usage': 64.8,
            'estimated_monthly_cost': 320.00,
            'optimization_potential': 12.5
        }
    
    def _analyze_storage_costs(self):
        """Analyze storage usage and costs"""
        return {
            'current_usage': 78.3,
            'growth_rate': 2.1,  # per month
            'estimated_monthly_cost': 180.00,
            'optimization_potential': 8.7
        }
    
    def _analyze_network_costs(self):
        """Analyze network usage and costs"""
        return {
            'bandwidth_usage': 1250.5,  # GB
            'estimated_monthly_cost': 125.00,
            'optimization_potential': 5.3
        }
    
    def _generate_cost_recommendations(self, analysis):
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # CPU optimization
        if analysis['cpu_cost_analysis']['optimization_potential'] > 10:
            recommendations.append({
                'type': 'cpu_optimization',
                'priority': 'high',
                'potential_savings': analysis['cpu_cost_analysis']['estimated_monthly_cost'] * 0.15,
                'recommendation': 'Consider right-sizing CPU resources or implementing auto-scaling'
            })
        
        # Memory optimization
        if analysis['memory_cost_analysis']['optimization_potential'] > 10:
            recommendations.append({
                'type': 'memory_optimization',
                'priority': 'medium',
                'potential_savings': analysis['memory_cost_analysis']['estimated_monthly_cost'] * 0.12,
                'recommendation': 'Optimize memory usage patterns and consider memory-efficient algorithms'
            })
        
        return recommendations