"""
Payment Implementation Validation Script

Validates the payment processing test implementation to ensure all components
are properly configured and functional.
"""

import sys
import os
import importlib
import inspect
from typing import Dict, Any, List, Tuple

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from qa_testing_framework.core.logging_utils import setup_logger


class PaymentImplementationValidator:
    """Validates payment testing implementation"""
    
    def __init__(self):
        self.logger = setup_logger("payment_validator")
        self.validation_results = {
            'page_objects': {'status': 'pending', 'details': []},
            'test_data': {'status': 'pending', 'details': []},
            'test_cases': {'status': 'pending', 'details': []},
            'test_runner': {'status': 'pending', 'details': []},
            'integration': {'status': 'pending', 'details': []}
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        self.logger.info("Starting payment implementation validation")
        
        # Validate each component
        self.validate_page_objects()
        self.validate_test_data()
        self.validate_test_cases()
        self.validate_test_runner()
        self.validate_integration()
        
        # Generate summary
        return self.generate_validation_report()
    
    def validate_page_objects(self):
        """Validate payment page objects"""
        self.logger.info("Validating payment page objects")
        
        try:
            # Import payment pages module
            from qa_testing_framework.web.payment_pages import PaymentPage, RefundPage
            
            # Check PaymentPage class
            payment_page_methods = [
                'select_payment_method',
                'fill_credit_card_form',
                'fill_debit_card_form',
                'fill_paypal_form',
                'fill_upi_form',
                'configure_emi_options',
                'verify_cod_availability',
                'verify_payment_security_indicators',
                'process_payment',
                'get_payment_result',
                'retry_payment',
                'change_payment_method',
                'validate_card_number_format',
                'validate_expiry_date',
                'validate_cvv_format',
                'verify_upi_id_format',
                'handle_gateway_redirect'
            ]
            
            missing_methods = []
            for method in payment_page_methods:
                if not hasattr(PaymentPage, method):
                    missing_methods.append(f"PaymentPage.{method}")
            
            # Check RefundPage class
            refund_page_methods = [
                'process_full_refund',
                'process_partial_refund'
            ]
            
            for method in refund_page_methods:
                if not hasattr(RefundPage, method):
                    missing_methods.append(f"RefundPage.{method}")
            
            if missing_methods:
                self.validation_results['page_objects']['status'] = 'failed'
                self.validation_results['page_objects']['details'] = [
                    f"Missing methods: {', '.join(missing_methods)}"
                ]
            else:
                self.validation_results['page_objects']['status'] = 'passed'
                self.validation_results['page_objects']['details'] = [
                    f"PaymentPage has {len(payment_page_methods)} required methods",
                    f"RefundPage has {len(refund_page_methods)} required methods"
                ]
            
        except ImportError as e:
            self.validation_results['page_objects']['status'] = 'failed'
            self.validation_results['page_objects']['details'] = [f"Import error: {str(e)}"]
        except Exception as e:
            self.validation_results['page_objects']['status'] = 'failed'
            self.validation_results['page_objects']['details'] = [f"Validation error: {str(e)}"]
    
    def validate_test_data(self):
        """Validate payment test data"""
        self.logger.info("Validating payment test data")
        
        try:
            # Import payment test data module
            from qa_testing_framework.web.payment_test_data import payment_test_data
            
            # Check required data generators
            required_data_methods = [
                'get_payment_method_data',
                'get_failure_scenario',
                'get_all_failure_scenarios',
                'get_refund_scenario',
                'create_payment_test_scenario',
                'get_security_test_data',
                'calculate_emi_details',
                'get_payment_gateway_configs'
            ]
            
            missing_methods = []
            for method in required_data_methods:
                if not hasattr(payment_test_data, method):
                    missing_methods.append(method)
            
            # Validate test data content
            validation_details = []
            
            # Check sandbox cards
            if hasattr(payment_test_data, 'sandbox_cards'):
                card_count = len(payment_test_data.sandbox_cards)
                validation_details.append(f"Sandbox cards: {card_count} configured")
            else:
                missing_methods.append("sandbox_cards attribute")
            
            # Check digital wallets
            if hasattr(payment_test_data, 'digital_wallets'):
                wallet_count = len(payment_test_data.digital_wallets)
                validation_details.append(f"Digital wallets: {wallet_count} configured")
            else:
                missing_methods.append("digital_wallets attribute")
            
            # Check UPI data
            if hasattr(payment_test_data, 'upi_data'):
                upi_count = len(payment_test_data.upi_data)
                validation_details.append(f"UPI data: {upi_count} configured")
            else:
                missing_methods.append("upi_data attribute")
            
            # Check EMI options
            if hasattr(payment_test_data, 'emi_options'):
                emi_count = len(payment_test_data.emi_options)
                validation_details.append(f"EMI options: {emi_count} configured")
            else:
                missing_methods.append("emi_options attribute")
            
            # Check failure scenarios
            if hasattr(payment_test_data, 'failure_scenarios'):
                failure_count = len(payment_test_data.failure_scenarios)
                validation_details.append(f"Failure scenarios: {failure_count} configured")
            else:
                missing_methods.append("failure_scenarios attribute")
            
            if missing_methods:
                self.validation_results['test_data']['status'] = 'failed'
                self.validation_results['test_data']['details'] = [
                    f"Missing methods/attributes: {', '.join(missing_methods)}"
                ]
            else:
                self.validation_results['test_data']['status'] = 'passed'
                self.validation_results['test_data']['details'] = validation_details
            
        except ImportError as e:
            self.validation_results['test_data']['status'] = 'failed'
            self.validation_results['test_data']['details'] = [f"Import error: {str(e)}"]
        except Exception as e:
            self.validation_results['test_data']['status'] = 'failed'
            self.validation_results['test_data']['details'] = [f"Validation error: {str(e)}"]
    
    def validate_test_cases(self):
        """Validate payment test cases"""
        self.logger.info("Validating payment test cases")
        
        try:
            # Import test suite
            from qa_testing_framework.web.test_payment_processing import PaymentProcessingTestSuite
            
            # Get all test methods
            test_methods = [method for method in dir(PaymentProcessingTestSuite) 
                          if method.startswith('test_')]
            
            # Required test categories
            required_test_patterns = [
                'test_successful_credit_card_payment',
                'test_successful_debit_card_payment',
                'test_successful_paypal_payment',
                'test_successful_upi_payment',
                'test_successful_emi_payment',
                'test_successful_cod_payment',
                'test_declined_card_payment',
                'test_insufficient_funds_scenario',
                'test_invalid_card_number_validation',
                'test_expired_card_validation',
                'test_invalid_cvv_validation',
                'test_payment_security_indicators',
                'test_full_order_refund',
                'test_partial_order_refund'
            ]
            
            missing_tests = []
            for required_test in required_test_patterns:
                if required_test not in test_methods:
                    missing_tests.append(required_test)
            
            # Validate test method structure
            validation_details = [f"Total test methods: {len(test_methods)}"]
            
            # Check for proper test case IDs
            test_case_ids = []
            for method_name in test_methods:
                method = getattr(PaymentProcessingTestSuite, method_name)
                if hasattr(method, '__doc__') and method.__doc__:
                    validation_details.append(f"{method_name}: Has documentation")
                else:
                    validation_details.append(f"{method_name}: Missing documentation")
            
            if missing_tests:
                self.validation_results['test_cases']['status'] = 'failed'
                self.validation_results['test_cases']['details'] = [
                    f"Missing required tests: {', '.join(missing_tests)}"
                ] + validation_details
            else:
                self.validation_results['test_cases']['status'] = 'passed'
                self.validation_results['test_cases']['details'] = validation_details
            
        except ImportError as e:
            self.validation_results['test_cases']['status'] = 'failed'
            self.validation_results['test_cases']['details'] = [f"Import error: {str(e)}"]
        except Exception as e:
            self.validation_results['test_cases']['status'] = 'failed'
            self.validation_results['test_cases']['details'] = [f"Validation error: {str(e)}"]
    
    def validate_test_runner(self):
        """Validate payment test runner"""
        self.logger.info("Validating payment test runner")
        
        try:
            # Import test runner
            from qa_testing_framework.web.run_payment_tests import PaymentTestRunner
            
            # Check required methods
            required_runner_methods = [
                'run_all_payment_tests',
                'run_payment_method_tests',
                'run_validation_tests',
                'run_failure_scenario_tests',
                'run_refund_tests',
                'run_security_tests'
            ]
            
            missing_methods = []
            for method in required_runner_methods:
                if not hasattr(PaymentTestRunner, method):
                    missing_methods.append(method)
            
            validation_details = []
            
            # Check if main function exists
            import qa_testing_framework.web.run_payment_tests as runner_module
            if hasattr(runner_module, 'main'):
                validation_details.append("Main function: Present")
            else:
                missing_methods.append("main function")
            
            if missing_methods:
                self.validation_results['test_runner']['status'] = 'failed'
                self.validation_results['test_runner']['details'] = [
                    f"Missing methods: {', '.join(missing_methods)}"
                ]
            else:
                self.validation_results['test_runner']['status'] = 'passed'
                self.validation_results['test_runner']['details'] = [
                    f"PaymentTestRunner has {len(required_runner_methods)} required methods"
                ] + validation_details
            
        except ImportError as e:
            self.validation_results['test_runner']['status'] = 'failed'
            self.validation_results['test_runner']['details'] = [f"Import error: {str(e)}"]
        except Exception as e:
            self.validation_results['test_runner']['status'] = 'failed'
            self.validation_results['test_runner']['details'] = [f"Validation error: {str(e)}"]
    
    def validate_integration(self):
        """Validate integration with existing framework"""
        self.logger.info("Validating framework integration")
        
        try:
            validation_details = []
            
            # Check integration with core models
            from qa_testing_framework.core.models import PaymentMethod
            validation_details.append("PaymentMethod model: Available")
            
            # Check integration with interfaces
            from qa_testing_framework.core.interfaces import Environment, Severity
            validation_details.append("Core interfaces: Available")
            
            # Check integration with webdriver manager
            from qa_testing_framework.web.webdriver_manager import WebDriverManager
            validation_details.append("WebDriverManager: Available")
            
            # Check integration with base page objects
            from qa_testing_framework.web.page_objects import BasePage, BaseFormPage
            validation_details.append("Base page objects: Available")
            
            # Check file structure
            expected_files = [
                'payment_pages.py',
                'payment_test_data.py',
                'test_payment_processing.py',
                'run_payment_tests.py',
                'README_PAYMENT_TESTS.md'
            ]
            
            current_dir = os.path.dirname(__file__)
            missing_files = []
            
            for file_name in expected_files:
                file_path = os.path.join(current_dir, file_name)
                if os.path.exists(file_path):
                    validation_details.append(f"File {file_name}: Present")
                else:
                    missing_files.append(file_name)
            
            if missing_files:
                self.validation_results['integration']['status'] = 'failed'
                self.validation_results['integration']['details'] = [
                    f"Missing files: {', '.join(missing_files)}"
                ] + validation_details
            else:
                self.validation_results['integration']['status'] = 'passed'
                self.validation_results['integration']['details'] = validation_details
            
        except ImportError as e:
            self.validation_results['integration']['status'] = 'failed'
            self.validation_results['integration']['details'] = [f"Import error: {str(e)}"]
        except Exception as e:
            self.validation_results['integration']['status'] = 'failed'
            self.validation_results['integration']['details'] = [f"Validation error: {str(e)}"]
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        # Calculate overall status
        all_passed = all(result['status'] == 'passed' for result in self.validation_results.values())
        any_failed = any(result['status'] == 'failed' for result in self.validation_results.values())
        
        overall_status = 'passed' if all_passed else ('failed' if any_failed else 'partial')
        
        # Count results
        passed_count = sum(1 for result in self.validation_results.values() if result['status'] == 'passed')
        failed_count = sum(1 for result in self.validation_results.values() if result['status'] == 'failed')
        total_count = len(self.validation_results)
        
        report = {
            'overall_status': overall_status,
            'summary': {
                'total_validations': total_count,
                'passed': passed_count,
                'failed': failed_count,
                'success_rate': (passed_count / total_count * 100) if total_count > 0 else 0
            },
            'detailed_results': self.validation_results,
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        for component, result in self.validation_results.items():
            if result['status'] == 'failed':
                recommendations.append(f"Fix {component} issues: {', '.join(result['details'])}")
        
        if not recommendations:
            recommendations.append("All payment implementation validations passed successfully.")
            recommendations.append("Payment testing framework is ready for use.")
        
        return recommendations
    
    def print_validation_report(self, report: Dict[str, Any]):
        """Print validation report to console"""
        print("\n" + "="*80)
        print("PAYMENT IMPLEMENTATION VALIDATION REPORT")
        print("="*80)
        
        # Overall Status
        status_symbol = "✓" if report['overall_status'] == 'passed' else "✗"
        print(f"\nOverall Status: {status_symbol} {report['overall_status'].upper()}")
        
        # Summary
        summary = report['summary']
        print(f"\nValidation Summary:")
        print(f"  Total Validations: {summary['total_validations']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        # Detailed Results
        print(f"\nDetailed Results:")
        for component, result in report['detailed_results'].items():
            status_symbol = "✓" if result['status'] == 'passed' else "✗"
            print(f"  {status_symbol} {component.replace('_', ' ').title()}: {result['status']}")
            
            for detail in result['details']:
                print(f"    - {detail}")
        
        # Recommendations
        print(f"\nRecommendations:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        
        print("\n" + "="*80)


def main():
    """Main validation function"""
    validator = PaymentImplementationValidator()
    report = validator.validate_all()
    validator.print_validation_report(report)
    
    # Return exit code based on validation results
    if report['overall_status'] == 'failed':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()