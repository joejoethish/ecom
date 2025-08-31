#!/usr/bin/env python
"""
Comprehensive Test Runner for E2E Workflow Debugging System

This script runs all debugging system tests including:
- End-to-end workflow tests
- Performance benchmark tests
- Regression tests
- Integration tests

Requirements: 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')

import django
django.setup()

from django.test.utils import get_runner
from django.conf import settings
from django.core.management import call_command
from django.db import connection


class DebuggingTestRunner:
    """Comprehensive test runner for the debugging system"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            'start_time': self.start_time.isoformat(),
            'test_suites': {},
            'summary': {},
            'errors': []
        }
        
        # Test configuration
        self.test_suites = {
            'e2e_workflows': {
                'path': 'tests.e2e.test_workflow_debugging_e2e',
                'description': 'End-to-end workflow debugging tests',
                'timeout': 300,  # 5 minutes
                'required': True
            },
            'performance_benchmarks': {
                'path': 'tests.performance.test_debugging_performance_benchmarks',
                'description': 'Performance benchmark tests with threshold validation',
                'timeout': 600,  # 10 minutes
                'required': True
            },
            'regression_tests': {
                'path': 'tests.integration.test_debugging_regression',
                'description': 'Automated regression tests for system health monitoring',
                'timeout': 300,  # 5 minutes
                'required': True
            },
            'unit_tests': {
                'path': 'apps.debugging.tests',
                'description': 'Unit tests for debugging components',
                'timeout': 120,  # 2 minutes
                'required': True
            },
            'integration_tests': {
                'path': 'tests.integration',
                'description': 'Integration tests for debugging system',
                'timeout': 240,  # 4 minutes
                'required': False
            }
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            'test_execution_time': 1200,  # 20 minutes max
            'memory_usage_mb': 1000,      # 1GB max
            'database_queries': 1000,     # Max queries per test suite
            'test_failure_rate': 0.05     # 5% max failure rate
        }
    
    def setup_test_environment(self):
        """Set up the test environment"""
        print("🔧 Setting up test environment...")
        
        try:
            # Create test database
            print("  📊 Setting up test database...")
            call_command('migrate', verbosity=0, interactive=False)
            
            # Load test fixtures
            print("  📋 Loading test fixtures...")
            self.load_test_fixtures()
            
            # Clear any existing test data
            print("  🧹 Clearing existing test data...")
            self.clear_test_data()
            
            # Verify system health
            print("  ❤️  Verifying system health...")
            self.verify_system_health()
            
            print("✅ Test environment setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup test environment: {e}")
            self.results['errors'].append(f"Environment setup failed: {e}")
            return False
    
    def load_test_fixtures(self):
        """Load test fixtures for debugging system"""
        fixtures = [
            'apps/debugging/fixtures/test_users.json',
            'apps/debugging/fixtures/test_products.json',
            'apps/debugging/fixtures/performance_thresholds.json'
        ]
        
        for fixture in fixtures:
            fixture_path = project_root / fixture
            if fixture_path.exists():
                call_command('loaddata', str(fixture_path), verbosity=0)
    
    def clear_test_data(self):
        """Clear any existing test data"""
        from apps.debugging.models import (
            WorkflowSession, TraceStep, PerformanceSnapshot, ErrorLog
        )
        
        # Clear debugging data
        WorkflowSession.objects.all().delete()
        TraceStep.objects.all().delete()
        PerformanceSnapshot.objects.all().delete()
        ErrorLog.objects.all().delete()
    
    def verify_system_health(self):
        """Verify system health before running tests"""
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check Redis connection (if available)
        try:
            from django.core.cache import cache
            cache.set('test_key', 'test_value', 10)
            assert cache.get('test_key') == 'test_value'
        except Exception:
            print("  ⚠️  Redis not available, some tests may be skipped")
    
    def run_test_suite(self, suite_name, suite_config):
        """Run a specific test suite"""
        print(f"\n🧪 Running {suite_name}: {suite_config['description']}")
        
        suite_start_time = time.time()
        suite_results = {
            'start_time': datetime.now().isoformat(),
            'description': suite_config['description'],
            'status': 'running',
            'tests_run': 0,
            'failures': 0,
            'errors': 0,
            'skipped': 0,
            'execution_time': 0,
            'memory_usage': 0,
            'database_queries': 0,
            'details': []
        }
        
        try:
            # Get initial metrics
            initial_queries = len(connection.queries)
            
            # Run the test suite
            TestRunner = get_runner(settings)
            test_runner = TestRunner(verbosity=2, interactive=False, keepdb=True)
            
            # Run tests with timeout
            result = self.run_with_timeout(
                lambda: test_runner.run_tests([suite_config['path']]),
                suite_config['timeout']
            )
            
            if result is None:
                raise TimeoutError(f"Test suite timed out after {suite_config['timeout']} seconds")
            
            # Calculate metrics
            suite_end_time = time.time()
            execution_time = suite_end_time - suite_start_time
            final_queries = len(connection.queries)
            database_queries = final_queries - initial_queries
            
            # Update results
            suite_results.update({
                'status': 'completed' if result == 0 else 'failed',
                'tests_run': getattr(test_runner, 'tests_run', 0),
                'failures': getattr(test_runner, 'failures', 0),
                'errors': getattr(test_runner, 'errors', 0),
                'skipped': getattr(test_runner, 'skipped', 0),
                'execution_time': execution_time,
                'database_queries': database_queries,
                'end_time': datetime.now().isoformat()
            })
            
            # Check performance thresholds
            self.check_suite_performance(suite_name, suite_results)
            
            print(f"✅ {suite_name} completed in {execution_time:.2f}s")
            
        except TimeoutError as e:
            suite_results.update({
                'status': 'timeout',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
            print(f"⏰ {suite_name} timed out")
            
        except Exception as e:
            suite_results.update({
                'status': 'error',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
            print(f"❌ {suite_name} failed: {e}")
        
        self.results['test_suites'][suite_name] = suite_results
        return suite_results['status'] == 'completed'
    
    def run_with_timeout(self, func, timeout):
        """Run a function with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError()
        
        # Set up timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            result = func()
            signal.alarm(0)  # Cancel timeout
            return result
        except TimeoutError:
            return None
        finally:
            signal.signal(signal.SIGALRM, old_handler)
    
    def check_suite_performance(self, suite_name, suite_results):
        """Check if test suite meets performance thresholds"""
        warnings = []
        
        # Check execution time
        if suite_results['execution_time'] > 300:  # 5 minutes
            warnings.append(f"Long execution time: {suite_results['execution_time']:.2f}s")
        
        # Check database queries
        if suite_results['database_queries'] > 500:
            warnings.append(f"High database query count: {suite_results['database_queries']}")
        
        # Check failure rate
        if suite_results['tests_run'] > 0:
            failure_rate = (suite_results['failures'] + suite_results['errors']) / suite_results['tests_run']
            if failure_rate > 0.1:  # 10% failure rate
                warnings.append(f"High failure rate: {failure_rate:.2%}")
        
        if warnings:
            suite_results['performance_warnings'] = warnings
            print(f"  ⚠️  Performance warnings for {suite_name}:")
            for warning in warnings:
                print(f"    - {warning}")
    
    def run_frontend_tests(self):
        """Run frontend tests"""
        print("\n🌐 Running frontend tests...")
        
        frontend_dir = project_root.parent / 'frontend'
        if not frontend_dir.exists():
            print("  ⚠️  Frontend directory not found, skipping frontend tests")
            return True
        
        try:
            # Change to frontend directory
            os.chdir(frontend_dir)
            
            # Install dependencies if needed
            if not (frontend_dir / 'node_modules').exists():
                print("  📦 Installing frontend dependencies...")
                subprocess.run(['npm', 'install'], check=True, capture_output=True)
            
            # Run tests
            print("  🧪 Running Jest tests...")
            result = subprocess.run(
                ['npm', 'test', '--', '--watchAll=false', '--coverage'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            if result.returncode == 0:
                print("✅ Frontend tests passed")
                return True
            else:
                print(f"❌ Frontend tests failed: {result.stderr}")
                self.results['errors'].append(f"Frontend tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Frontend tests timed out")
            self.results['errors'].append("Frontend tests timed out")
            return False
        except Exception as e:
            print(f"❌ Frontend test error: {e}")
            self.results['errors'].append(f"Frontend test error: {e}")
            return False
        finally:
            # Change back to backend directory
            os.chdir(project_root)
    
    def run_performance_benchmarks(self):
        """Run performance benchmarks and validate thresholds"""
        print("\n📊 Running performance benchmarks...")
        
        try:
            # Import performance test modules
            from tests.performance.test_debugging_performance_benchmarks import (
                WorkflowTracingPerformanceTest,
                APIEndpointPerformanceTest,
                DatabasePerformanceTest,
                ConcurrencyPerformanceTest
            )
            
            benchmark_results = {}
            
            # Run workflow tracing benchmarks
            print("  🔄 Workflow tracing performance...")
            workflow_test = WorkflowTracingPerformanceTest()
            workflow_test.setUp()
            
            # Measure workflow session creation
            start_time = time.time()
            workflow_test.test_workflow_session_creation_performance()
            workflow_creation_time = time.time() - start_time
            
            benchmark_results['workflow_creation_time'] = workflow_creation_time
            
            # Run API endpoint benchmarks
            print("  🌐 API endpoint performance...")
            api_test = APIEndpointPerformanceTest()
            api_test.setUp()
            
            start_time = time.time()
            api_test.test_workflow_session_list_performance()
            api_response_time = time.time() - start_time
            
            benchmark_results['api_response_time'] = api_response_time
            
            # Run database benchmarks
            print("  🗄️  Database performance...")
            db_test = DatabasePerformanceTest()
            db_test.setUp()
            
            start_time = time.time()
            db_test.test_workflow_session_query_performance()
            db_query_time = time.time() - start_time
            
            benchmark_results['db_query_time'] = db_query_time
            
            # Validate against thresholds
            self.validate_performance_thresholds(benchmark_results)
            
            self.results['performance_benchmarks'] = benchmark_results
            print("✅ Performance benchmarks completed")
            return True
            
        except Exception as e:
            print(f"❌ Performance benchmark error: {e}")
            self.results['errors'].append(f"Performance benchmark error: {e}")
            return False
    
    def validate_performance_thresholds(self, benchmark_results):
        """Validate performance results against thresholds"""
        thresholds = {
            'workflow_creation_time': 1.0,  # 1 second
            'api_response_time': 2.0,       # 2 seconds
            'db_query_time': 0.5            # 0.5 seconds
        }
        
        violations = []
        
        for metric, value in benchmark_results.items():
            if metric in thresholds and value > thresholds[metric]:
                violations.append(f"{metric}: {value:.3f}s > {thresholds[metric]}s")
        
        if violations:
            print("  ⚠️  Performance threshold violations:")
            for violation in violations:
                print(f"    - {violation}")
            benchmark_results['threshold_violations'] = violations
        else:
            print("  ✅ All performance thresholds met")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_execution_time = (end_time - self.start_time).total_seconds()
        
        # Calculate summary statistics
        total_tests = sum(suite.get('tests_run', 0) for suite in self.results['test_suites'].values())
        total_failures = sum(suite.get('failures', 0) for suite in self.results['test_suites'].values())
        total_errors = sum(suite.get('errors', 0) for suite in self.results['test_suites'].values())
        total_skipped = sum(suite.get('skipped', 0) for suite in self.results['test_suites'].values())
        
        success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        
        self.results.update({
            'end_time': end_time.isoformat(),
            'total_execution_time': total_execution_time,
            'summary': {
                'total_tests': total_tests,
                'total_failures': total_failures,
                'total_errors': total_errors,
                'total_skipped': total_skipped,
                'success_rate': success_rate,
                'suites_passed': sum(1 for suite in self.results['test_suites'].values() 
                                   if suite.get('status') == 'completed'),
                'suites_failed': sum(1 for suite in self.results['test_suites'].values() 
                                   if suite.get('status') in ['failed', 'error', 'timeout'])
            }
        })
        
        # Generate report
        report_path = project_root / 'test_reports' / f'debugging_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate HTML report
        self.generate_html_report(report_path.with_suffix('.html'))
        
        print(f"\n📋 Test report generated: {report_path}")
        return report_path
    
    def generate_html_report(self, report_path):
        """Generate HTML test report"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>E2E Workflow Debugging System - Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                .summary { display: flex; gap: 20px; margin: 20px 0; }
                .metric { background: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }
                .suite { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .passed { border-left: 5px solid #4CAF50; }
                .failed { border-left: 5px solid #f44336; }
                .warning { border-left: 5px solid #ff9800; }
                .error { color: #f44336; }
                .success { color: #4CAF50; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>E2E Workflow Debugging System - Test Report</h1>
                <p>Generated: {timestamp}</p>
                <p>Total Execution Time: {total_time:.2f} seconds</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>Total Tests</h3>
                    <p>{total_tests}</p>
                </div>
                <div class="metric">
                    <h3>Success Rate</h3>
                    <p class="{success_class}">{success_rate:.1f}%</p>
                </div>
                <div class="metric">
                    <h3>Failures</h3>
                    <p class="error">{total_failures}</p>
                </div>
                <div class="metric">
                    <h3>Errors</h3>
                    <p class="error">{total_errors}</p>
                </div>
            </div>
            
            <h2>Test Suites</h2>
            {suites_html}
            
            {errors_html}
        </body>
        </html>
        """
        
        # Generate suites HTML
        suites_html = ""
        for suite_name, suite_data in self.results['test_suites'].items():
            status_class = "passed" if suite_data.get('status') == 'completed' else "failed"
            
            suites_html += f"""
            <div class="suite {status_class}">
                <h3>{suite_name}</h3>
                <p>{suite_data.get('description', '')}</p>
                <p>Status: <span class="{status_class}">{suite_data.get('status', 'unknown')}</span></p>
                <p>Tests Run: {suite_data.get('tests_run', 0)}</p>
                <p>Execution Time: {suite_data.get('execution_time', 0):.2f}s</p>
                <p>Database Queries: {suite_data.get('database_queries', 0)}</p>
            </div>
            """
        
        # Generate errors HTML
        errors_html = ""
        if self.results['errors']:
            errors_html = "<h2>Errors</h2><ul>"
            for error in self.results['errors']:
                errors_html += f"<li class='error'>{error}</li>"
            errors_html += "</ul>"
        
        # Fill template
        html_content = html_template.format(
            timestamp=self.results['end_time'],
            total_time=self.results['total_execution_time'],
            total_tests=self.results['summary']['total_tests'],
            success_rate=self.results['summary']['success_rate'],
            success_class="success" if self.results['summary']['success_rate'] > 90 else "error",
            total_failures=self.results['summary']['total_failures'],
            total_errors=self.results['summary']['total_errors'],
            suites_html=suites_html,
            errors_html=errors_html
        )
        
        with open(report_path, 'w') as f:
            f.write(html_content)
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting E2E Workflow Debugging System Test Suite")
        print(f"📅 Start time: {self.start_time}")
        
        # Setup test environment
        if not self.setup_test_environment():
            return False
        
        # Track overall success
        overall_success = True
        
        # Run backend test suites
        for suite_name, suite_config in self.test_suites.items():
            success = self.run_test_suite(suite_name, suite_config)
            
            if not success and suite_config.get('required', False):
                overall_success = False
                if suite_config.get('required', False):
                    print(f"❌ Required test suite {suite_name} failed")
        
        # Run frontend tests
        frontend_success = self.run_frontend_tests()
        if not frontend_success:
            overall_success = False
        
        # Run performance benchmarks
        benchmark_success = self.run_performance_benchmarks()
        if not benchmark_success:
            overall_success = False
        
        # Generate report
        report_path = self.generate_test_report()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.results['summary']['total_tests']}")
        print(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        print(f"Failures: {self.results['summary']['total_failures']}")
        print(f"Errors: {self.results['summary']['total_errors']}")
        print(f"Execution Time: {self.results['total_execution_time']:.2f}s")
        
        if overall_success:
            print("\n✅ ALL TESTS PASSED!")
        else:
            print("\n❌ SOME TESTS FAILED!")
            
        print(f"\n📋 Detailed report: {report_path}")
        
        return overall_success


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run E2E Workflow Debugging System tests')
    parser.add_argument('--suite', help='Run specific test suite only')
    parser.add_argument('--skip-frontend', action='store_true', help='Skip frontend tests')
    parser.add_argument('--skip-benchmarks', action='store_true', help='Skip performance benchmarks')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = DebuggingTestRunner()
    
    if args.suite:
        # Run specific suite only
        if args.suite in runner.test_suites:
            runner.setup_test_environment()
            success = runner.run_test_suite(args.suite, runner.test_suites[args.suite])
            runner.generate_test_report()
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Unknown test suite: {args.suite}")
            print(f"Available suites: {', '.join(runner.test_suites.keys())}")
            sys.exit(1)
    else:
        # Run all tests
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()