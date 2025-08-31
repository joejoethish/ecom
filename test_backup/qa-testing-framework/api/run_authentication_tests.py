#!/usr/bin/env python3
"""
Authentication API Test Runner

Executes comprehensive authentication and user management API tests
with detailed reporting and validation.

This script runs all tests for task 6.2 of the QA testing framework.
"""

import sys
import os
import pytest
import json
from datetime import datetime
from typing import Dict, Any, List

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import Environment, TestModule, Priority, ExecutionStatus, Severity
from core.models import TestExecution, TestCase, Defect


class AuthenticationTestRunner:
    """Test runner for authentication API tests"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.test_results = []
        self.execution_start_time = datetime.now()
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all authentication API tests"""
        print("=" * 80)
        print("AUTHENTICATION AND USER MANAGEMENT API TESTS")
        print("=" * 80)
        print(f"Environment: {self.environment.value}")
        print(f"Start Time: {self.execution_start_time}")
        print()
        
        # Define test modules to run
        test_modules = [
            {
                'name': 'Authentication API Tests',
                'module': 'test_authentication::TestAuthenticationAPI',
                'description': 'User registration, login, logout, and token management tests'
            },
            {
                'name': 'User Management API Tests',
                'module': 'test_authentication::TestUserManagementAPI',
                'description': 'User profile management and CRUD operations tests'
            },
            {
                'name': 'Role-Based Access Control Tests',
                'module': 'test_authentication::TestRoleBasedAccessControl',
                'description': 'Role-based API access control validation tests'
            },
            {
                'name': 'API Rate Limiting Tests',
                'module': 'test_authentication::TestAPIRateLimiting',
                'description': 'Rate limiting and throttling validation tests'
            },
            {
                'name': 'API Security Validation Tests',
                'module': 'test_authentication::TestAPISecurityValidation',
                'description': 'Security headers and vulnerability protection tests'
            }
        ]
        
        overall_results = {
            'total_modules': len(test_modules),
            'passed_modules': 0,
            'failed_modules': 0,
            'module_results': [],
            'execution_time': None,
            'summary': {}
        }
        
        # Run each test module
        for module_info in test_modules:
            print(f"Running {module_info['name']}...")
            print(f"Description: {module_info['description']}")
            print("-" * 60)
            
            module_result = self._run_test_module(module_info)
            overall_results['module_results'].append(module_result)
            
            if module_result['passed']:
                overall_results['passed_modules'] += 1
                print(f"✅ {module_info['name']} - PASSED")
            else:
                overall_results['failed_modules'] += 1
                print(f"❌ {module_info['name']} - FAILED")
            
            print(f"Tests: {module_result['total']} total, {module_result['passed']} passed, {module_result['failed']} failed")
            print()
        
        # Calculate overall execution time
        execution_end_time = datetime.now()
        execution_duration = (execution_end_time - self.execution_start_time).total_seconds()
        overall_results['execution_time'] = execution_duration
        
        # Generate summary
        overall_results['summary'] = self._generate_summary(overall_results)
        
        # Print final results
        self._print_final_results(overall_results)
        
        return overall_results
    
    def _run_test_module(self, module_info: Dict[str, str]) -> Dict[str, Any]:
        """Run a specific test module"""
        module_name = module_info['module']
        
        # Prepare pytest arguments
        pytest_args = [
            f"test_authentication.py::{module_name.split('::')[1]}",
            '-v',
            '--tb=short',
            '--json-report',
            '--json-report-file=temp_test_results.json'
        ]
        
        # Run pytest
        exit_code = pytest.main(pytest_args)
        
        # Parse results
        module_result = {
            'name': module_info['name'],
            'description': module_info['description'],
            'passed': exit_code == 0,
            'exit_code': exit_code,
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
            'test_details': []
        }
        
        # Try to read detailed results from JSON report
        try:
            if os.path.exists('temp_test_results.json'):
                with open('temp_test_results.json', 'r') as f:
                    json_results = json.load(f)
                
                module_result['total'] = json_results.get('summary', {}).get('total', 0)
                module_result['passed'] = json_results.get('summary', {}).get('passed', 0)
                module_result['failed'] = json_results.get('summary', {}).get('failed', 0)
                module_result['skipped'] = json_results.get('summary', {}).get('skipped', 0)
                
                # Extract test details
                for test in json_results.get('tests', []):
                    test_detail = {
                        'name': test.get('nodeid', ''),
                        'outcome': test.get('outcome', ''),
                        'duration': test.get('duration', 0),
                        'error': test.get('call', {}).get('longrepr', '') if test.get('outcome') == 'failed' else None
                    }
                    module_result['test_details'].append(test_detail)
                
                # Clean up temp file
                os.remove('temp_test_results.json')
        
        except Exception as e:
            print(f"Warning: Could not parse detailed test results: {e}")
        
        return module_result
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test execution summary"""
        total_tests = sum(module['total'] for module in results['module_results'])
        total_passed = sum(module['passed'] for module in results['module_results'])
        total_failed = sum(module['failed'] for module in results['module_results'])
        total_skipped = sum(module['skipped'] for module in results['module_results'])
        
        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': total_skipped,
            'pass_rate': round(pass_rate, 2),
            'execution_time_seconds': results['execution_time'],
            'execution_time_formatted': f"{results['execution_time']:.2f}s",
            'modules_passed': results['passed_modules'],
            'modules_failed': results['failed_modules'],
            'overall_status': 'PASSED' if results['failed_modules'] == 0 else 'FAILED'
        }
    
    def _print_final_results(self, results: Dict[str, Any]):
        """Print final test results summary"""
        summary = results['summary']
        
        print("=" * 80)
        print("AUTHENTICATION API TESTS - FINAL RESULTS")
        print("=" * 80)
        
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Execution Time: {summary['execution_time_formatted']}")
        print()
        
        print("Module Summary:")
        print(f"  Total Modules: {results['total_modules']}")
        print(f"  Passed Modules: {summary['modules_passed']}")
        print(f"  Failed Modules: {summary['modules_failed']}")
        print()
        
        print("Test Summary:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed Tests: {summary['total_passed']}")
        print(f"  Failed Tests: {summary['total_failed']}")
        print(f"  Skipped Tests: {summary['total_skipped']}")
        print(f"  Pass Rate: {summary['pass_rate']}%")
        print()
        
        # Print module details
        print("Module Details:")
        for module in results['module_results']:
            status_icon = "✅" if module['passed'] else "❌"
            print(f"  {status_icon} {module['name']}")
            print(f"     Tests: {module['total']} total, {module['passed']} passed, {module['failed']} failed")
            
            # Print failed test details
            if module['failed'] > 0:
                failed_tests = [test for test in module['test_details'] if test['outcome'] == 'failed']
                for test in failed_tests[:3]:  # Show first 3 failures
                    print(f"     ❌ {test['name']}")
                if len(failed_tests) > 3:
                    print(f"     ... and {len(failed_tests) - 3} more failures")
        
        print()
        print("=" * 80)
    
    def generate_detailed_report(self, results: Dict[str, Any], output_file: str = None):
        """Generate detailed test report"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"authentication_test_report_{timestamp}.json"
        
        report = {
            'test_run_info': {
                'environment': self.environment.value,
                'start_time': self.execution_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': results['execution_time']
            },
            'summary': results['summary'],
            'module_results': results['module_results'],
            'requirements_coverage': {
                'requirement_1_1': 'Authentication flow testing - COVERED',
                'requirement_1_2': 'User management testing - COVERED',
                'requirement_2_1': 'Role-based access control - COVERED',
                'requirement_2_2': 'API security validation - COVERED'
            },
            'test_categories': {
                'user_registration': 'Tests user signup, validation, and email verification',
                'user_authentication': 'Tests login, logout, and token management',
                'user_profile_management': 'Tests profile CRUD operations',
                'role_based_access_control': 'Tests API access permissions by user role',
                'rate_limiting': 'Tests API rate limiting and throttling',
                'security_validation': 'Tests security headers and vulnerability protection'
            }
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Detailed report saved to: {output_file}")
        return output_file


def main():
    """Main execution function"""
    # Parse command line arguments
    environment = Environment.DEVELOPMENT
    if len(sys.argv) > 1:
        env_arg = sys.argv[1].upper()
        if env_arg in ['DEVELOPMENT', 'STAGING', 'PRODUCTION']:
            environment = Environment(env_arg.lower())
    
    # Create and run test runner
    runner = AuthenticationTestRunner(environment)
    results = runner.run_all_tests()
    
    # Generate detailed report
    report_file = runner.generate_detailed_report(results)
    
    # Exit with appropriate code
    exit_code = 0 if results['summary']['overall_status'] == 'PASSED' else 1
    sys.exit(exit_code)


if __name__ == '__main__':
    main()