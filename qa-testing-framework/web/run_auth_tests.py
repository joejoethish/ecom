"""
Authentication Test Runner

Runs the complete authentication test suite and generates detailed reports
for all authentication and user management functionality.
"""

import unittest
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from qa_testing_framework.web.test_authentication import AuthenticationTestSuite
from qa_testing_framework.core.interfaces import Environment, ExecutionStatus, Severity
from qa_testing_framework.core.models import TestExecution, Defect
from qa_testing_framework.core.config import get_config


class AuthTestRunner:
    """Custom test runner for authentication tests"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config = get_config("web", environment)
        self.start_time = datetime.now()
        self.results = {
            'environment': environment.value,
            'start_time': self.start_time.isoformat(),
            'end_time': None,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'test_results': [],
            'defects': [],
            'summary': {}
        }
    
    def run_tests(self, test_pattern: str = None) -> Dict[str, Any]:
        """Run authentication tests and collect results"""
        print(f"Starting Authentication Test Suite - Environment: {self.environment.value}")
        print("=" * 60)
        
        # Create test suite
        if test_pattern:
            suite = unittest.TestLoader().loadTestsFromName(test_pattern, AuthenticationTestSuite)
        else:
            suite = unittest.TestLoader().loadTestsFromTestCase(AuthenticationTestSuite)
        
        # Run tests with custom result collector
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        test_result = runner.run(suite)
        
        # Collect results
        self._collect_results(test_result)
        
        # Generate report
        self._generate_report()
        
        return self.results
    
    def _collect_results(self, test_result: unittest.TestResult):
        """Collect test results and metrics"""
        self.results['total_tests'] = test_result.testsRun
        self.results['failed_tests'] = len(test_result.failures) + len(test_result.errors)
        self.results['passed_tests'] = test_result.testsRun - self.results['failed_tests']
        self.results['skipped_tests'] = len(test_result.skipped) if hasattr(test_result, 'skipped') else 0
        
        # Collect individual test results
        for test, error in test_result.failures:
            self.results['test_results'].append({
                'test_name': str(test),
                'status': 'FAILED',
                'error': error,
                'type': 'failure'
            })
        
        for test, error in test_result.errors:
            self.results['test_results'].append({
                'test_name': str(test),
                'status': 'ERROR',
                'error': error,
                'type': 'error'
            })
        
        # Collect defects from test suite
        if hasattr(AuthenticationTestSuite, 'defects'):
            for defect in AuthenticationTestSuite.defects:
                self.results['defects'].append({
                    'id': defect.id,
                    'title': defect.title,
                    'description': defect.description,
                    'severity': defect.severity.value,
                    'test_case_id': defect.test_case_id,
                    'reproduction_steps': defect.reproduction_steps
                })
        
        # Collect test executions
        if hasattr(AuthenticationTestSuite, 'test_executions'):
            for execution in AuthenticationTestSuite.test_executions:
                self.results['test_results'].append({
                    'test_name': execution.test_case_id,
                    'status': execution.status.value,
                    'duration': execution.duration,
                    'screenshots': execution.screenshots
                })
        
        self.results['end_time'] = datetime.now().isoformat()
    
    def _generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate summary statistics
        self.results['summary'] = {
            'total_duration_seconds': duration,
            'pass_rate': (self.results['passed_tests'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0,
            'critical_defects': len([d for d in self.results['defects'] if d['severity'] == 'critical']),
            'major_defects': len([d for d in self.results['defects'] if d['severity'] == 'major']),
            'minor_defects': len([d for d in self.results['defects'] if d['severity'] == 'minor']),
            'test_categories': {
                'registration_tests': len([t for t in self.results['test_results'] if 'registration' in t.get('test_name', '').lower()]),
                'login_tests': len([t for t in self.results['test_results'] if 'login' in t.get('test_name', '').lower()]),
                'logout_tests': len([t for t in self.results['test_results'] if 'logout' in t.get('test_name', '').lower()]),
                'password_tests': len([t for t in self.results['test_results'] if 'password' in t.get('test_name', '').lower()]),
                'profile_tests': len([t for t in self.results['test_results'] if 'profile' in t.get('test_name', '').lower()]),
                'security_tests': len([t for t in self.results['test_results'] if 'security' in t.get('test_name', '').lower() or 'sql' in t.get('test_name', '').lower() or 'xss' in t.get('test_name', '').lower()]),
                'access_control_tests': len([t for t in self.results['test_results'] if 'access' in t.get('test_name', '').lower() or 'role' in t.get('test_name', '').lower()]),
                'session_tests': len([t for t in self.results['test_results'] if 'session' in t.get('test_name', '').lower()])
            }
        }
        
        # Print summary to console
        self._print_summary()
        
        # Save detailed report to file
        self._save_report_to_file()
    
    def _print_summary(self):
        """Print test summary to console"""
        print("\n" + "=" * 60)
        print("AUTHENTICATION TEST SUITE SUMMARY")
        print("=" * 60)
        
        print(f"Environment: {self.results['environment']}")
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed_tests']}")
        print(f"Failed: {self.results['failed_tests']}")
        print(f"Pass Rate: {self.results['summary']['pass_rate']:.1f}%")
        print(f"Duration: {self.results['summary']['total_duration_seconds']:.2f} seconds")
        
        print(f"\nDefects Found:")
        print(f"  Critical: {self.results['summary']['critical_defects']}")
        print(f"  Major: {self.results['summary']['major_defects']}")
        print(f"  Minor: {self.results['summary']['minor_defects']}")
        
        print(f"\nTest Categories:")
        for category, count in self.results['summary']['test_categories'].items():
            print(f"  {category.replace('_', ' ').title()}: {count}")
        
        if self.results['defects']:
            print(f"\nCritical Issues:")
            for defect in self.results['defects']:
                if defect['severity'] == 'critical':
                    print(f"  - {defect['title']}")
        
        print("\n" + "=" * 60)
    
    def _save_report_to_file(self):
        """Save detailed report to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"auth_test_report_{self.environment.value}_{timestamp}.json"
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Detailed report saved to: {filepath}")


def main():
    """Main function to run authentication tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Authentication Test Suite')
    parser.add_argument('--environment', '-e', 
                       choices=['development', 'staging', 'production'],
                       default='development',
                       help='Test environment (default: development)')
    parser.add_argument('--test-pattern', '-t',
                       help='Specific test pattern to run (e.g., test_user_login_valid_credentials)')
    parser.add_argument('--browser', '-b',
                       choices=['chrome', 'firefox', 'edge', 'safari'],
                       default='chrome',
                       help='Browser to use for testing (default: chrome)')
    parser.add_argument('--headless', 
                       action='store_true',
                       help='Run tests in headless mode')
    
    args = parser.parse_args()
    
    # Set environment
    env_map = {
        'development': Environment.DEVELOPMENT,
        'staging': Environment.STAGING,
        'production': Environment.PRODUCTION
    }
    environment = env_map[args.environment]
    
    # Create and run test runner
    runner = AuthTestRunner(environment)
    
    try:
        results = runner.run_tests(args.test_pattern)
        
        # Exit with appropriate code
        if results['failed_tests'] > 0:
            print(f"\nTests completed with {results['failed_tests']} failures.")
            sys.exit(1)
        else:
            print(f"\nAll {results['passed_tests']} tests passed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        sys.exit(2)
    except Exception as e:
        print(f"\nTest execution failed with error: {str(e)}")
        sys.exit(3)


if __name__ == '__main__':
    main()