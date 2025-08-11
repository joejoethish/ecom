# Management command for running load tests
from django.core.management.base import BaseCommand
from django.utils import timezone
import asyncio
import json

from ...load_testing import LoadTestRunner, PerformanceRegressionTester
from ...models import PerformanceBenchmark

class Command(BaseCommand):
    help = 'Run performance load tests'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='http://localhost:8000/api/',
            help='URL to test'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of concurrent users'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Test duration in seconds'
        )
        parser.add_argument(
            '--ramp-up',
            type=int,
            default=10,
            help='Ramp up time in seconds'
        )
        parser.add_argument(
            '--method',
            type=str,
            default='GET',
            help='HTTP method'
        )
        parser.add_argument(
            '--regression-test',
            action='store_true',
            help='Run as regression test'
        )
        parser.add_argument(
            '--test-name',
            type=str,
            default='default_load_test',
            help='Name for the test'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting load test: {options["test_name"]}')
        )
        
        # Configure test
        test_config = {
            'url': options['url'],
            'concurrent_users': options['users'],
            'duration': options['duration'],
            'ramp_up_time': options['ramp_up'],
            'method': options['method']
        }
        
        try:
            if options['regression_test']:
                # Run regression test
                tester = PerformanceRegressionTester()
                results = tester.run_regression_test(options['test_name'], test_config)
                
                self.stdout.write(
                    self.style.SUCCESS('Regression test completed')
                )
                
                if results.get('regression_detected'):
                    self.stdout.write(
                        self.style.ERROR('REGRESSION DETECTED!')
                    )
                    for regression in results['regressions']:
                        self.stdout.write(
                            self.style.ERROR(
                                f"- {regression['metric']}: {regression['change']:.2f}% change"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('No regressions detected')
                    )
                
            else:
                # Run standard load test
                runner = LoadTestRunner()
                results = asyncio.run(runner.run_load_test(test_config))
                
                # Save benchmark results
                PerformanceBenchmark.objects.create(
                    name=f"Load Test - {options['test_name']}",
                    description=f"Load test with {options['users']} users for {options['duration']}s",
                    benchmark_type='load_test',
                    baseline_value=0,
                    current_value=results['response_times']['avg'],
                    target_value=2000,  # 2 second target
                    unit='ms',
                    test_configuration=test_config,
                    test_results=results
                )
                
                self.stdout.write(
                    self.style.SUCCESS('Load test completed successfully')
                )
                
                # Display results
                summary = results['summary']
                response_times = results['response_times']
                
                self.stdout.write(f"Total Requests: {summary['total_requests']}")
                self.stdout.write(f"Successful Requests: {summary['successful_requests']}")
                self.stdout.write(f"Failed Requests: {summary['failed_requests']}")
                self.stdout.write(f"Success Rate: {summary['success_rate']:.2f}%")
                self.stdout.write(f"Average Response Time: {response_times['avg']:.2f}ms")
                self.stdout.write(f"95th Percentile: {response_times['p95']:.2f}ms")
                self.stdout.write(f"99th Percentile: {response_times['p99']:.2f}ms")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Load test failed: {str(e)}')
            )