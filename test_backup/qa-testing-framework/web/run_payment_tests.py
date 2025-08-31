"""
Payment Processing Test Runner

Executes comprehensive payment processing tests including all payment methods,
failure scenarios, refund processing, and security validation.
"""

import sys
import os
import unittest
import time
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from qa_testing_framework.web.test_payment_processing import PaymentProcessingTestSuite
from qa_testing_framework.core.interfaces import Environment, Severity
from qa_testing_framework.core.config import get_config
from qa_testing_framework.core.logging_utils import setup_logger


class PaymentTestRunner:
    """Test runner for payment processing tests"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config = get_config("web", environment)
        self.logger = setup_logger("payment_test_runner")
        
        # Test execution tracking
        self.start_time = None
        self.end_time = None
        self.test_results = {}
        self.defects_found = []
    
    def run_all_payment_tests(self) -> Dict[str, Any]:
        """Run all payment processing tests"""
        self.logger.info("Starting comprehensive payment processing test suite")
        self.start_time = datetime.now()
        
        # Create test suite
        suite = unittest.TestSuite()
        
        # Add all payment test methods
        test_methods = [
            'test_successful_credit_card_payment',
            'test_successful_debit_card_payment',
            'test_successful_paypal_payment',
            'test_successful_google_pay_payment',
            'test_successful_apple_pay_payment',
            'test_successful_upi_payment',
            'test_successful_emi_payment',
            'test_successful_cod_payment',
            'test_declined_card_payment',
            'test_insufficient_funds_scenario',
            'test_invalid_card_number_validation',
            'test_expired_card_validation',
            'test_invalid_cvv_validation',
            'test_invalid_upi_id_validation',
            'test_payment_security_indicators',
            'test_full_order_refund',
            'test_partial_order_refund',
            'test_high_value_payment',
            'test_international_card_payment'
        ]
        
        for method in test_methods:
            suite.addTest(PaymentProcessingTestSuite(method))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        self.end_time = datetime.now()
        
        # Process results
        self._process_test_results(result)
        
        return self._generate_test_report()
    
    def run_payment_method_tests(self, payment_methods: List[str]) -> Dict[str, Any]:
        """Run tests for specific payment methods"""
        self.logger.info(f"Running payment tests for methods: {payment_methods}")
        self.start_time = datetime.now()
        
        # Map payment methods to test methods
        method_test_map = {
            'credit_card': ['test_successful_credit_card_payment', 'test_declined_card_payment'],
            'debit_card': ['test_successful_debit_card_payment'],
            'paypal': ['test_successful_paypal_payment'],
            'google_pay': ['test_successful_google_pay_payment'],
            'apple_pay': ['test_successful_apple_pay_payment'],
            'upi': ['test_successful_upi_payment', 'test_invalid_upi_id_validation'],
            'emi': ['test_successful_emi_payment'],
            'cod': ['test_successful_cod_payment']
        }
        
        # Create test suite
        suite = unittest.TestSuite()
        
        for payment_method in payment_methods:
            if payment_method in method_test_map:
                for test_method in method_test_map[payment_method]:
                    suite.addTest(PaymentProcessingTestSuite(test_method))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        self.end_time = datetime.now()
        self._process_test_results(result)
        
        return self._generate_test_report()
    
    def run_validation_tests(self) -> Dict[str, Any]:
        """Run payment validation tests"""
        self.logger.info("Running payment validation tests")
        self.start_time = datetime.now()
        
        # Validation test methods
        validation_tests = [
            'test_invalid_card_number_validation',
            'test_expired_card_validation',
            'test_invalid_cvv_validation',
            'test_invalid_upi_id_validation',
            'test_payment_security_indicators'
        ]
        
        # Create test suite
        suite = unittest.TestSuite()
        for test_method in validation_tests:
            suite.addTest(PaymentProcessingTestSuite(test_method))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        self.end_time = datetime.now()
        self._process_test_results(result)
        
        return self._generate_test_report()
    
    def run_failure_scenario_tests(self) -> Dict[str, Any]:
        """Run payment failure scenario tests"""
        self.logger.info("Running payment failure scenario tests")
        self.start_time = datetime.now()
        
        # Failure scenario test methods
        failure_tests = [
            'test_declined_card_payment',
            'test_insufficient_funds_scenario',
            'test_invalid_card_number_validation',
            'test_expired_card_validation',
            'test_invalid_cvv_validation',
            'test_invalid_upi_id_validation'
        ]
        
        # Create test suite
        suite = unittest.TestSuite()
        for test_method in failure_tests:
            suite.addTest(PaymentProcessingTestSuite(test_method))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        self.end_time = datetime.now()
        self._process_test_results(result)
        
        return self._generate_test_report()
    
    def run_refund_tests(self) -> Dict[str, Any]:
        """Run refund processing tests"""
        self.logger.info("Running refund processing tests")
        self.start_time = datetime.now()
        
        # First run a successful payment to create order for refund
        payment_suite = unittest.TestSuite()
        payment_suite.addTest(PaymentProcessingTestSuite('test_successful_credit_card_payment'))
        
        payment_runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
        payment_result = payment_runner.run(payment_suite)
        
        if payment_result.wasSuccessful():
            # Now run refund tests
            refund_tests = [
                'test_full_order_refund',
                'test_partial_order_refund'
            ]
            
            refund_suite = unittest.TestSuite()
            for test_method in refund_tests:
                refund_suite.addTest(PaymentProcessingTestSuite(test_method))
            
            # Run refund tests
            refund_runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
            result = refund_runner.run(refund_suite)
        else:
            self.logger.error("Payment test failed, cannot run refund tests")
            result = payment_result
        
        self.end_time = datetime.now()
        self._process_test_results(result)
        
        return self._generate_test_report()
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run payment security tests"""
        self.logger.info("Running payment security tests")
        self.start_time = datetime.now()
        
        # Security test methods
        security_tests = [
            'test_payment_security_indicators'
        ]
        
        # Create test suite
        suite = unittest.TestSuite()
        for test_method in security_tests:
            suite.addTest(PaymentProcessingTestSuite(test_method))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        self.end_time = datetime.now()
        self._process_test_results(result)
        
        return self._generate_test_report()
    
    def _process_test_results(self, result: unittest.TestResult):
        """Process test execution results"""
        self.test_results = {
            'total_tests': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'failed': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        }
        
        # Process failures and errors as defects
        for test, traceback in result.failures:
            self.defects_found.append({
                'test_name': str(test),
                'type': 'failure',
                'details': traceback,
                'severity': Severity.MAJOR
            })
        
        for test, traceback in result.errors:
            self.defects_found.append({
                'test_name': str(test),
                'type': 'error',
                'details': traceback,
                'severity': Severity.CRITICAL
            })
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        
        report = {
            'execution_summary': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_seconds': duration,
                'environment': self.environment.value,
                'test_results': self.test_results
            },
            'defects_summary': {
                'total_defects': len(self.defects_found),
                'critical_defects': len([d for d in self.defects_found if d['severity'] == Severity.CRITICAL]),
                'major_defects': len([d for d in self.defects_found if d['severity'] == Severity.MAJOR]),
                'defects': self.defects_found
            },
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if self.test_results.get('success_rate', 0) < 90:
            recommendations.append("Payment success rate is below 90%. Review payment gateway configurations and error handling.")
        
        critical_defects = len([d for d in self.defects_found if d['severity'] == Severity.CRITICAL])
        if critical_defects > 0:
            recommendations.append(f"Found {critical_defects} critical payment defects. Immediate attention required.")
        
        if self.test_results.get('failed', 0) > 0:
            recommendations.append("Some payment tests failed. Review payment processing logic and validation rules.")
        
        if not recommendations:
            recommendations.append("All payment tests passed successfully. Payment system is functioning correctly.")
        
        return recommendations
    
    def print_summary_report(self, report: Dict[str, Any]):
        """Print summary report to console"""
        print("\n" + "="*80)
        print("PAYMENT PROCESSING TEST SUMMARY REPORT")
        print("="*80)
        
        # Execution Summary
        execution = report['execution_summary']
        print(f"\nExecution Details:")
        print(f"  Environment: {execution['environment']}")
        print(f"  Start Time: {execution['start_time']}")
        print(f"  End Time: {execution['end_time']}")
        print(f"  Duration: {execution['duration_seconds']:.2f} seconds")
        
        # Test Results
        results = execution['test_results']
        print(f"\nTest Results:")
        print(f"  Total Tests: {results['total_tests']}")
        print(f"  Passed: {results['passed']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Errors: {results['errors']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Success Rate: {results['success_rate']:.1f}%")
        
        # Defects Summary
        defects = report['defects_summary']
        print(f"\nDefects Summary:")
        print(f"  Total Defects: {defects['total_defects']}")
        print(f"  Critical: {defects['critical_defects']}")
        print(f"  Major: {defects['major_defects']}")
        
        # Recommendations
        print(f"\nRecommendations:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        
        print("\n" + "="*80)


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Payment Processing Tests')
    parser.add_argument('--test-type', choices=['all', 'methods', 'validation', 'failures', 'refunds', 'security'], 
                       default='all', help='Type of tests to run')
    parser.add_argument('--payment-methods', nargs='+', 
                       choices=['credit_card', 'debit_card', 'paypal', 'google_pay', 'apple_pay', 'upi', 'emi', 'cod'],
                       help='Specific payment methods to test')
    parser.add_argument('--environment', choices=['development', 'staging', 'production'], 
                       default='development', help='Test environment')
    
    args = parser.parse_args()
    
    # Convert environment string to enum
    env_map = {
        'development': Environment.DEVELOPMENT,
        'staging': Environment.STAGING,
        'production': Environment.PRODUCTION
    }
    environment = env_map[args.environment]
    
    # Create test runner
    runner = PaymentTestRunner(environment)
    
    # Run tests based on type
    if args.test_type == 'all':
        report = runner.run_all_payment_tests()
    elif args.test_type == 'methods':
        payment_methods = args.payment_methods or ['credit_card', 'paypal', 'upi']
        report = runner.run_payment_method_tests(payment_methods)
    elif args.test_type == 'validation':
        report = runner.run_validation_tests()
    elif args.test_type == 'failures':
        report = runner.run_failure_scenario_tests()
    elif args.test_type == 'refunds':
        report = runner.run_refund_tests()
    elif args.test_type == 'security':
        report = runner.run_security_tests()
    
    # Print summary report
    runner.print_summary_report(report)
    
    # Return exit code based on results
    if report['execution_summary']['test_results']['failed'] > 0 or report['execution_summary']['test_results']['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()