"""
Django management command for running automated API tests.
"""

import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.debugging.testing_framework import (
    ComprehensiveTestRunner,
    run_comprehensive_api_tests,
    run_quick_api_health_check
)


class Command(BaseCommand):
    help = 'Run automated API testing and validation suite'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            default='comprehensive',
            choices=['comprehensive', 'quick', 'health'],
            help='Test mode: comprehensive (full suite), quick (subset), or health (critical endpoints only)'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            default='console',
            choices=['console', 'json', 'file'],
            help='Output format for test results'
        )
        
        parser.add_argument(
            '--file',
            type=str,
            help='Output file path (when output=file)'
        )
        
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://localhost:8000',
            help='Base URL for API testing'
        )
        
        parser.add_argument(
            '--save-results',
            action='store_true',
            help='Save test results to database'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting automated API testing suite...')
        )
        
        try:
            # Run tests based on mode
            if options['mode'] == 'comprehensive':
                results = self._run_comprehensive_tests(options)
            elif options['mode'] == 'quick':
                results = self._run_quick_tests(options)
            elif options['mode'] == 'health':
                results = self._run_health_check(options)
            else:
                raise CommandError(f"Unknown test mode: {options['mode']}")
            
            # Output results
            self._output_results(results, options)
            
            # Save to database if requested
            if options['save_results']:
                self._save_results_to_database(results)
            
            # Print summary
            self._print_summary(results, options)
            
        except Exception as e:
            raise CommandError(f'API testing failed: {str(e)}')
    
    def _run_comprehensive_tests(self, options):
        """Run comprehensive API testing suite."""
        self.stdout.write('Running comprehensive API testing suite...')
        
        runner = ComprehensiveTestRunner(options['base_url'])
        results = runner.run_all_tests()
        
        return results
    
    def _run_quick_tests(self, options):
        """Run quick API tests (subset of comprehensive)."""
        self.stdout.write('Running quick API tests...')
        
        # Run a subset of the comprehensive tests
        runner = ComprehensiveTestRunner(options['base_url'])
        
        # Setup and discover endpoints
        runner.framework.setup_test_environment()
        endpoints = runner.framework.discovery_service.discover_all_endpoints()
        
        # Run limited tests
        results = []
        
        # Test subset of endpoints
        test_endpoints = endpoints[:5]
        endpoint_results = runner.framework.test_all_endpoints(test_endpoints)
        results.extend(endpoint_results)
        
        # Test authentication
        auth_results = runner.framework.test_authentication_flows()
        results.extend(auth_results)
        
        # Calculate summary
        total_tests = len(results)
        passed_tests = len([r for r in results if r.success])
        failed_tests = total_tests - passed_tests
        
        return {
            'test_suite': {
                'name': 'Quick API Test Suite',
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'results': results
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_health_check(self, options):
        """Run API health check."""
        self.stdout.write('Running API health check...')
        
        results = run_quick_api_health_check()
        return results
    
    def _output_results(self, results, options):
        """Output test results in specified format."""
        if options['output'] == 'json':
            output = json.dumps(results, indent=2, default=str)
        elif options['output'] == 'file':
            if not options['file']:
                raise CommandError('File path required when output=file')
            
            output = json.dumps(results, indent=2, default=str)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(options['file']), exist_ok=True)
            
            with open(options['file'], 'w') as f:
                f.write(output)
            
            self.stdout.write(
                self.style.SUCCESS(f'Results saved to {options["file"]}')
            )
            return
        else:
            # Console output
            output = self._format_console_output(results, options['verbose'])
        
        if options['output'] != 'file':
            self.stdout.write(output)
    
    def _format_console_output(self, results, verbose=False):
        """Format results for console output."""
        output = []
        
        # Header
        output.append("=" * 80)
        output.append("API Testing Results")
        output.append("=" * 80)
        
        # Summary
        if 'test_suite' in results:
            test_suite = results['test_suite']
            output.append(f"Test Suite: {test_suite.get('name', 'Unknown')}")
            output.append(f"Total Tests: {test_suite.get('total_tests', 0)}")
            output.append(f"Passed: {test_suite.get('passed_tests', 0)}")
            output.append(f"Failed: {test_suite.get('failed_tests', 0)}")
            
            if test_suite.get('total_tests', 0) > 0:
                success_rate = test_suite.get('passed_tests', 0) / test_suite.get('total_tests', 1) * 100
                output.append(f"Success Rate: {success_rate:.1f}%")
        elif 'status' in results:
            # Health check format
            output.append(f"Status: {results['status']}")
            output.append(f"Passed: {results.get('passed_tests', 0)}")
            output.append(f"Total: {results.get('total_tests', 0)}")
            output.append(f"Success Rate: {results.get('success_rate', 0):.1f}%")
        
        output.append("")
        
        # Detailed results if verbose
        if verbose:
            output.append("Detailed Results:")
            output.append("-" * 40)
            
            test_results = []
            if 'test_suite' in results and 'results' in results['test_suite']:
                test_results = results['test_suite']['results']
            elif 'results' in results:
                test_results = results['results']
            
            for result in test_results:
                if isinstance(result, dict):
                    status = "PASS" if result.get('success', False) else "FAIL"
                    output.append(f"{status}: {result.get('method', 'GET')} {result.get('endpoint', 'Unknown')}")
                    
                    if not result.get('success', False) and result.get('error_message'):
                        output.append(f"  Error: {result['error_message']}")
                    
                    if result.get('response_time'):
                        output.append(f"  Response Time: {result['response_time']*1000:.1f}ms")
                    
                    output.append("")
        
        # Failed tests summary
        failed_tests = []
        if 'test_suite' in results and 'results' in results['test_suite']:
            failed_tests = [r for r in results['test_suite']['results'] if not r.get('success', False)]
        elif 'results' in results:
            failed_tests = [r for r in results['results'] if not r.get('success', False)]
        
        if failed_tests:
            output.append("Failed Tests:")
            output.append("-" * 40)
            
            for result in failed_tests[:10]:  # Show first 10 failures
                if isinstance(result, dict):
                    output.append(f"• {result.get('method', 'GET')} {result.get('endpoint', 'Unknown')}")
                    if result.get('error_message'):
                        output.append(f"  {result['error_message']}")
            
            if len(failed_tests) > 10:
                output.append(f"... and {len(failed_tests) - 10} more failures")
        
        # Recommendations
        if 'reports' in results and 'recommendations' in results['reports']:
            recommendations = results['reports']['recommendations']
            if recommendations:
                output.append("")
                output.append("Recommendations:")
                output.append("-" * 40)
                
                for rec in recommendations[:5]:  # Show first 5 recommendations
                    output.append(f"• {rec.get('title', 'Unknown')}")
                    output.append(f"  Priority: {rec.get('priority', 'Unknown')}")
                    output.append(f"  {rec.get('description', '')}")
                    output.append("")
        
        return "\n".join(output)
    
    def _save_results_to_database(self, results):
        """Save test results to database."""
        try:
            from apps.debugging.models import ErrorLog
            
            # Save failed tests as error logs
            failed_tests = []
            if 'test_suite' in results and 'results' in results['test_suite']:
                failed_tests = [r for r in results['test_suite']['results'] if not r.get('success', False)]
            elif 'results' in results:
                failed_tests = [r for r in results['results'] if not r.get('success', False)]
            
            for result in failed_tests:
                if isinstance(result, dict):
                    ErrorLog.objects.create(
                        layer='api',
                        component='automated_testing',
                        severity='error',
                        error_type='test_failure',
                        error_message=f"Test failed: {result.get('test_name', 'unknown')} - {result.get('error_message', 'No details')}",
                        metadata={
                            'endpoint': result.get('endpoint'),
                            'method': result.get('method'),
                            'status_code': result.get('status_code'),
                            'response_time': result.get('response_time'),
                            'test_name': result.get('test_name')
                        }
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Saved {len(failed_tests)} test failures to database')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Failed to save results to database: {str(e)}')
            )
    
    def _print_summary(self, results, options):
        """Print final summary."""
        self.stdout.write("")
        
        if 'test_suite' in results:
            test_suite = results['test_suite']
            total = test_suite.get('total_tests', 0)
            passed = test_suite.get('passed_tests', 0)
            failed = test_suite.get('failed_tests', 0)
            
            if failed == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ All {total} tests passed!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ {failed} of {total} tests failed')
                )
        elif 'status' in results:
            status = results['status']
            if status == 'healthy':
                self.stdout.write(
                    self.style.SUCCESS('✓ API health check passed!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ API health check: {status}')
                )
        
        self.stdout.write(f"Completed at: {results.get('timestamp', 'Unknown')}")