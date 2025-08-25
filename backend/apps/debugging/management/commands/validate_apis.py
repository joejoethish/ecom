"""
Django management command for API validation.

Usage:
    python manage.py validate_apis
    python manage.py validate_apis --endpoint /api/v1/products/
    python manage.py validate_apis --output json
    python manage.py validate_apis --output file --file validation_report.json
"""

import json
from django.core.management.base import BaseCommand
from dataclasses import asdict
from apps.debugging.api_validation import (
    APIValidationEngine,
    test_single_endpoint,
    check_api_health
)


class Command(BaseCommand):
    """Django management command for API validation."""
    
    help = 'Run comprehensive API validation'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--endpoint',
            type=str,
            help='Validate specific endpoint only'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='console',
            choices=['console', 'json', 'file'],
            help='Output format for validation results'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Output file path (when output=file)'
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Run quick health check on critical endpoints'
        )
    
    def handle(self, *args, **options):
        if options['health_check']:
            # Run health check
            results = check_api_health()
            self._output_health_results(results, options)
        elif options['endpoint']:
            # Validate single endpoint
            result = test_single_endpoint(options['endpoint'])
            self._output_result(result, options)
        else:
            # Run full validation
            engine = APIValidationEngine()
            results = engine.run_full_validation()
            self._output_results(results, options)
    
    def _output_result(self, result, options):
        """Output single validation result."""
        if options['output'] == 'json':
            output = json.dumps(asdict(result), indent=2)
        else:
            output = f"""
Endpoint Validation Result
=========================
Endpoint: {result.endpoint}
Method: {result.method}
Status: {'SUCCESS' if result.success else 'FAILED'}
Status Code: {result.status_code}
Response Time: {result.response_time:.3f}s
"""
            if result.error_message:
                output += f"Error: {result.error_message}\n"
            if result.payload_used:
                output += f"Payload Used: {json.dumps(result.payload_used, indent=2)}\n"
        
        self._write_output(output, options)
    
    def _output_results(self, results, options):
        """Output full validation results."""
        if options['output'] == 'json':
            output = json.dumps(results, indent=2)
        else:
            summary = results['summary']
            output = f"""
API Validation Results
=====================
Total Endpoints: {summary['total_endpoints']}
Total Tests: {summary['total_tests']}
Successful Tests: {summary['successful_tests']}
Failed Tests: {summary['failed_tests']}
Success Rate: {summary['success_rate']:.1f}%
Average Response Time: {summary['average_response_time']:.3f}s

"""
            if results['failed_tests']:
                output += "Failed Tests:\n"
                for failed_test in results['failed_tests']:
                    output += f"- {failed_test['method']} {failed_test['endpoint']}: {failed_test['error_message']}\n"
            else:
                output += "All tests passed successfully!\n"
        
        self._write_output(output, options)
    
    def _output_health_results(self, results, options):
        """Output health check results."""
        if options['output'] == 'json':
            output = json.dumps(results, indent=2)
        else:
            output = f"""
API Health Check Results
=======================
Timestamp: {results['timestamp']}
Overall Health: {results['overall_health'].upper()}

Endpoint Status:
"""
            for result in results['results']:
                status_icon = "✓" if result['status'] == 'healthy' else "✗"
                output += f"{status_icon} {result['endpoint']}: {result['status']}"
                if 'response_time' in result:
                    output += f" ({result['response_time']:.3f}s)"
                if 'error' in result:
                    output += f" - {result['error']}"
                output += "\n"
        
        self._write_output(output, options)
    
    def _write_output(self, output, options):
        """Write output to console or file."""
        if options['output'] == 'file' and options['file']:
            with open(options['file'], 'w') as f:
                f.write(output)
            self.stdout.write(
                self.style.SUCCESS(f"Results written to {options['file']}")
            )
        else:
            self.stdout.write(output)