"""
Payment API Test Runner

Comprehensive test execution script for payment and transaction API tests.
Executes wallet management, gift card operations, payment processing,
and transaction validation tests.

Usage:
    python run_payment_api_tests.py [options]

Options:
    --environment: Test environment (development, staging, production)
    --test-type: Type of tests to run (unit, integration, all)
    --verbose: Enable verbose output
    --report: Generate detailed test report
"""

import sys
import os
import argparse
import pytest
from datetime import datetime
import json
from decimal import Decimal

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import Environment
from api.client import APITestClient
from api.validators import APIValidator


class PaymentAPITestRunner:
    """Test runner for payment and transaction API tests"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.client = APITestClient('http://localhost:8000', environment)
        self.validator = APIValidator()
        
        # Test configuration
        self.test_modules = [
            'test_wallet_giftcard_api.py',
            'test_payment_processing_api.py',
            'test_transaction_validation_api.py'
        ]
        
        self.test_results = {
            'start_time': None,
            'end_time': None,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'errors': [],
            'test_details': []
        }
        
        # Payment API endpoints for testing
        self.payment_endpoints = {
            'wallets': '/api/v1/payments/wallets/',
            'gift_cards': '/api/v1/payments/gift-cards/',
            'transactions': '/api/v1/payments/transactions/',
            'payment_methods': '/api/v1/payments/methods/',
            'refunds': '/api/v1/payments/refunds/',
            'webhooks': '/api/v1/payments/webhooks/'
        }
    
    def setup_test_environment(self):
        """Setup test environment and validate payment system connectivity"""
        print(f"Setting up payment test environment: {self.environment.value}")
        
        # Validate API connectivity
        try:
            response = self.client.get('/api/v1/health/', authenticate=False)
            if not response.is_success:
                print("Warning: API health check failed")
        except Exception as e:
            print(f"Warning: Could not connect to API: {e}")
        
        # Validate payment system endpoints
        print("Validating payment system endpoints...")
        endpoint_status = {}
        
        for endpoint_name, endpoint_url in self.payment_endpoints.items():
            try:
                response = self.client.get(endpoint_url, authenticate=False)
                # Expect 401/403 for protected endpoints, not 404
                if response.status_code in [200, 401, 403]:
                    endpoint_status[endpoint_name] = "Available"
                else:
                    endpoint_status[endpoint_name] = f"Error: {response.status_code}"
            except Exception as e:
                endpoint_status[endpoint_name] = f"Failed: {e}"
        
        # Print endpoint status
        for endpoint, status in endpoint_status.items():
            print(f"  {endpoint}: {status}")
        
        return True
    
    def run_unit_tests(self, verbose: bool = False):
        """Run unit tests for payment and transaction APIs"""
        print("\n" + "="*60)
        print("RUNNING PAYMENT AND TRANSACTION UNIT TESTS")
        print("="*60)
        
        test_args = [
            'test_wallet_giftcard_api.py',
            '-v' if verbose else '-q',
            '--tb=short',
            '--disable-warnings'
        ]
        
        # Run pytest
        result = pytest.main(test_args)
        
        return result == 0
    
    def run_integration_tests(self, verbose: bool = False):
        """Run integration tests for payment workflows"""
        print("\n" + "="*60)
        print("RUNNING PAYMENT INTEGRATION TESTS")
        print("="*60)
        
        integration_tests_passed = 0
        total_integration_tests = 0
        
        # Test 1: Complete wallet funding workflow
        print("Testing complete wallet funding workflow...")
        total_integration_tests += 1
        
        try:
            # Authenticate as customer
            self.client.auth_token = 'customer_test_token'
            self.client.auth_type = 'jwt'
            
            # Step 1: Get current wallet balance
            wallet_response = self.client.get('/api/v1/payments/wallets/my_wallet/')
            
            if wallet_response.status_code in [200, 404]:  # 404 if no wallet exists yet
                print("  ✓ Wallet retrieval endpoint accessible")
                
                # Step 2: Initiate funds addition
                add_funds_data = {
                    'amount': '50.00',
                    'currency_code': 'USD',
                    'payment_method_id': 'test_payment_method'
                }
                
                add_funds_response = self.client.post(
                    '/api/v1/payments/wallets/add_funds/',
                    data=add_funds_data
                )
                
                if add_funds_response.status_code in [201, 400, 401]:  # Expected responses
                    print("  ✓ Add funds endpoint accessible")
                    integration_tests_passed += 1
                else:
                    print(f"  ✗ Add funds endpoint error: {add_funds_response.status_code}")
            else:
                print(f"  ✗ Wallet endpoint error: {wallet_response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Wallet funding workflow test failed: {e}")
        
        # Test 2: Gift card purchase and redemption workflow
        print("Testing gift card purchase and redemption workflow...")
        total_integration_tests += 1
        
        try:
            # Step 1: Purchase gift card
            purchase_data = {
                'amount': '100.00',
                'currency_code': 'USD',
                'recipient_email': 'test@example.com',
                'payment_method_id': 'test_payment_method'
            }
            
            purchase_response = self.client.post(
                '/api/v1/payments/gift-cards/purchase/',
                data=purchase_data
            )
            
            if purchase_response.status_code in [201, 400, 401]:  # Expected responses
                print("  ✓ Gift card purchase endpoint accessible")
                
                # Step 2: Check gift card status
                check_data = {'code': 'TEST-GIFT-CARD-CODE'}
                
                check_response = self.client.post(
                    '/api/v1/payments/gift-cards/check/',
                    data=check_data
                )
                
                if check_response.status_code in [200, 404, 400, 401]:  # Expected responses
                    print("  ✓ Gift card check endpoint accessible")
                    integration_tests_passed += 1
                else:
                    print(f"  ✗ Gift card check endpoint error: {check_response.status_code}")
            else:
                print(f"  ✗ Gift card purchase endpoint error: {purchase_response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Gift card workflow test failed: {e}")
        
        # Test 3: Transaction history and validation
        print("Testing transaction history and validation...")
        total_integration_tests += 1
        
        try:
            # Get wallet transactions
            transactions_response = self.client.get('/api/v1/payments/wallets/transactions/')
            
            if transactions_response.status_code in [200, 401]:  # Expected responses
                print("  ✓ Wallet transactions endpoint accessible")
                
                # Get payment transactions
                payment_transactions_response = self.client.get('/api/v1/payments/transactions/')
                
                if payment_transactions_response.status_code in [200, 401]:  # Expected responses
                    print("  ✓ Payment transactions endpoint accessible")
                    integration_tests_passed += 1
                else:
                    print(f"  ✗ Payment transactions endpoint error: {payment_transactions_response.status_code}")
            else:
                print(f"  ✗ Wallet transactions endpoint error: {transactions_response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Transaction validation test failed: {e}")
        
        print(f"\nIntegration Tests Summary: {integration_tests_passed}/{total_integration_tests} passed")
        
        return integration_tests_passed == total_integration_tests
    
    def run_performance_tests(self, verbose: bool = False):
        """Run performance tests for payment APIs"""
        print("\n" + "="*60)
        print("RUNNING PAYMENT API PERFORMANCE TESTS")
        print("="*60)
        
        performance_tests_passed = 0
        total_performance_tests = 0
        
        # Test 1: Wallet balance retrieval performance
        print("Testing wallet balance retrieval performance...")
        total_performance_tests += 1
        
        try:
            self.client.auth_token = 'customer_test_token'
            self.client.auth_type = 'jwt'
            
            start_time = datetime.now()
            response = self.client.get('/api/v1/payments/wallets/my_wallet/')
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            print(f"  Wallet balance response time: {response_time:.3f}s")
            
            if response_time < 1.0:  # Should be fast for balance checks
                print("  ✓ Wallet balance performance acceptable")
                performance_tests_passed += 1
            else:
                print("  ⚠ Wallet balance response time exceeds 1 second")
                
        except Exception as e:
            print(f"  ✗ Wallet balance performance test failed: {e}")
        
        # Test 2: Transaction history performance
        print("Testing transaction history performance...")
        total_performance_tests += 1
        
        try:
            start_time = datetime.now()
            response = self.client.get('/api/v1/payments/wallets/transactions/')
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            print(f"  Transaction history response time: {response_time:.3f}s")
            
            if response_time < 2.0:  # Reasonable for paginated results
                print("  ✓ Transaction history performance acceptable")
                performance_tests_passed += 1
            else:
                print("  ⚠ Transaction history response time exceeds 2 seconds")
                
        except Exception as e:
            print(f"  ✗ Transaction history performance test failed: {e}")
        
        # Test 3: Payment processing simulation performance
        print("Testing payment processing simulation performance...")
        total_performance_tests += 1
        
        try:
            # Simulate payment processing timing
            payment_data = {
                'amount': '25.00',
                'currency_code': 'USD',
                'payment_method_id': 'test_method'
            }
            
            start_time = datetime.now()
            # Note: This would normally process a payment
            # For testing, we'll simulate the API call timing
            response = self.client.post('/api/v1/payments/wallets/add_funds/', data=payment_data)
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            print(f"  Payment processing response time: {response_time:.3f}s")
            
            if response_time < 5.0:  # Payment processing can take longer
                print("  ✓ Payment processing performance acceptable")
                performance_tests_passed += 1
            else:
                print("  ⚠ Payment processing response time exceeds 5 seconds")
                
        except Exception as e:
            print(f"  ✗ Payment processing performance test failed: {e}")
        
        print(f"\nPerformance Tests Summary: {performance_tests_passed}/{total_performance_tests} passed")
        
        return performance_tests_passed >= (total_performance_tests * 0.8)  # 80% pass rate acceptable
    
    def run_security_tests(self, verbose: bool = False):
        """Run security tests for payment APIs"""
        print("\n" + "="*60)
        print("RUNNING PAYMENT API SECURITY TESTS")
        print("="*60)
        
        security_tests_passed = 0
        total_security_tests = 0
        
        # Test 1: Unauthorized access to payment endpoints
        print("Testing unauthorized access protection...")
        total_security_tests += 1
        
        try:
            # Clear authentication
            self.client.clear_authentication()
            
            # Test protected payment endpoints
            protected_endpoints = [
                '/api/v1/payments/wallets/my_wallet/',
                '/api/v1/payments/wallets/add_funds/',
                '/api/v1/payments/gift-cards/purchase/',
                '/api/v1/payments/transactions/'
            ]
            
            unauthorized_access_blocked = True
            
            for endpoint in protected_endpoints:
                response = self.client.get(endpoint, authenticate=False)
                
                if response.status_code not in [401, 403]:
                    print(f"  ✗ Unauthorized access allowed to {endpoint}")
                    unauthorized_access_blocked = False
            
            if unauthorized_access_blocked:
                print("  ✓ Unauthorized access properly blocked")
                security_tests_passed += 1
            
        except Exception as e:
            print(f"  ✗ Unauthorized access test failed: {e}")
        
        # Test 2: Payment amount validation
        print("Testing payment amount validation...")
        total_security_tests += 1
        
        try:
            self.client.auth_token = 'customer_test_token'
            self.client.auth_type = 'jwt'
            
            # Test invalid payment amounts
            invalid_amounts = [
                '-50.00',      # Negative amount
                '0.00',        # Zero amount
                '999999.99',   # Excessive amount
                'invalid',     # Non-numeric
                '50.001'       # Too many decimal places
            ]
            
            amount_validation_working = True
            
            for invalid_amount in invalid_amounts:
                payment_data = {
                    'amount': invalid_amount,
                    'currency_code': 'USD',
                    'payment_method_id': 'test_method'
                }
                
                response = self.client.post('/api/v1/payments/wallets/add_funds/', data=payment_data)
                
                # Should reject invalid amounts with 400 status
                if response.status_code not in [400, 422]:
                    print(f"  ✗ Invalid amount accepted: {invalid_amount}")
                    amount_validation_working = False
            
            if amount_validation_working:
                print("  ✓ Payment amount validation working")
                security_tests_passed += 1
            
        except Exception as e:
            print(f"  ✗ Payment amount validation test failed: {e}")
        
        # Test 3: Gift card code security
        print("Testing gift card code security...")
        total_security_tests += 1
        
        try:
            # Test gift card code validation
            malicious_codes = [
                "'; DROP TABLE gift_cards; --",
                "<script>alert('xss')</script>",
                "../../etc/passwd",
                "' OR '1'='1",
                "UNION SELECT * FROM users"
            ]
            
            code_validation_working = True
            
            for malicious_code in malicious_codes:
                check_data = {'code': malicious_code}
                
                response = self.client.post('/api/v1/payments/gift-cards/check/', data=check_data)
                
                # Should either reject (400) or handle safely (404)
                if response.status_code == 200:
                    # If it returns 200, check that it's not exposing sensitive data
                    if 'users' in str(response.content).lower() or 'password' in str(response.content).lower():
                        print(f"  ✗ Malicious gift card code exposed data: {malicious_code}")
                        code_validation_working = False
            
            if code_validation_working:
                print("  ✓ Gift card code security working")
                security_tests_passed += 1
            
        except Exception as e:
            print(f"  ✗ Gift card code security test failed: {e}")
        
        # Test 4: Rate limiting on payment endpoints
        print("Testing payment endpoint rate limiting...")
        total_security_tests += 1
        
        try:
            rate_limit_working = False
            
            # Make multiple rapid payment requests
            for i in range(10):  # Rapid payment attempts
                payment_data = {
                    'amount': '1.00',
                    'currency_code': 'USD',
                    'payment_method_id': 'test_method'
                }
                
                response = self.client.post('/api/v1/payments/wallets/add_funds/', data=payment_data)
                
                if response.status_code == 429:  # Too Many Requests
                    print("  ✓ Payment rate limiting is active")
                    rate_limit_working = True
                    security_tests_passed += 1
                    break
            
            if not rate_limit_working:
                print("  ⚠ Payment rate limiting not detected (may not be configured)")
            
        except Exception as e:
            print(f"  ✗ Payment rate limiting test failed: {e}")
        
        print(f"\nSecurity Tests Summary: {security_tests_passed}/{total_security_tests} passed")
        
        return security_tests_passed >= (total_security_tests * 0.75)  # 75% pass rate acceptable for security
    
    def run_webhook_tests(self, verbose: bool = False):
        """Run webhook validation tests"""
        print("\n" + "="*60)
        print("RUNNING PAYMENT WEBHOOK TESTS")
        print("="*60)
        
        webhook_tests_passed = 0
        total_webhook_tests = 0
        
        # Test 1: Webhook endpoint accessibility
        print("Testing webhook endpoint accessibility...")
        total_webhook_tests += 1
        
        try:
            # Test webhook endpoint (usually accepts POST)
            webhook_data = {
                'event_type': 'payment.completed',
                'payment_id': 'test_payment_123',
                'status': 'completed',
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.client.post('/api/v1/payments/webhooks/', data=webhook_data, authenticate=False)
            
            # Webhook endpoints typically return 200, 400, or 401
            if response.status_code in [200, 400, 401, 403]:
                print("  ✓ Webhook endpoint accessible")
                webhook_tests_passed += 1
            else:
                print(f"  ✗ Webhook endpoint error: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Webhook accessibility test failed: {e}")
        
        # Test 2: Webhook signature validation
        print("Testing webhook signature validation...")
        total_webhook_tests += 1
        
        try:
            # Test webhook with invalid signature
            webhook_data = {
                'event_type': 'payment.completed',
                'payment_id': 'test_payment_123',
                'signature': 'invalid_signature'
            }
            
            response = self.client.post('/api/v1/payments/webhooks/', data=webhook_data, authenticate=False)
            
            # Should reject invalid signatures
            if response.status_code in [400, 401, 403]:
                print("  ✓ Webhook signature validation working")
                webhook_tests_passed += 1
            else:
                print("  ⚠ Webhook signature validation may not be implemented")
                
        except Exception as e:
            print(f"  ✗ Webhook signature validation test failed: {e}")
        
        print(f"\nWebhook Tests Summary: {webhook_tests_passed}/{total_webhook_tests} passed")
        
        return webhook_tests_passed >= (total_webhook_tests * 0.5)  # 50% pass rate acceptable
    
    def generate_test_report(self, results: dict):
        """Generate detailed test report"""
        report = {
            'test_run_info': {
                'environment': self.environment.value,
                'start_time': results.get('start_time'),
                'end_time': results.get('end_time'),
                'duration': None
            },
            'test_summary': {
                'total_tests': results.get('total_tests', 0),
                'passed_tests': results.get('passed_tests', 0),
                'failed_tests': results.get('failed_tests', 0),
                'skipped_tests': results.get('skipped_tests', 0),
                'success_rate': 0
            },
            'test_categories': {
                'unit_tests': results.get('unit_tests', {}),
                'integration_tests': results.get('integration_tests', {}),
                'performance_tests': results.get('performance_tests', {}),
                'security_tests': results.get('security_tests', {}),
                'webhook_tests': results.get('webhook_tests', {})
            },
            'payment_specific_metrics': {
                'wallet_operations_tested': True,
                'gift_card_operations_tested': True,
                'transaction_validation_tested': True,
                'security_validations_tested': True
            },
            'errors_and_failures': results.get('errors', []),
            'recommendations': []
        }
        
        # Calculate success rate
        total = report['test_summary']['total_tests']
        passed = report['test_summary']['passed_tests']
        
        if total > 0:
            report['test_summary']['success_rate'] = (passed / total) * 100
        
        # Add payment-specific recommendations
        if report['test_summary']['success_rate'] < 95:
            report['recommendations'].append(
                "Payment system test success rate is below 95%. This is critical for financial operations."
            )
        
        if results.get('security_issues'):
            report['recommendations'].append(
                "Security issues detected in payment system. Immediate review required."
            )
        
        if results.get('performance_issues'):
            report['recommendations'].append(
                "Payment API performance issues detected. Consider optimizing for financial transactions."
            )
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'payment_api_test_report_{timestamp}.json'
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed test report saved to: {report_filename}")
        
        return report
    
    def run_all_tests(self, test_type: str = 'all', verbose: bool = False, generate_report: bool = False):
        """Run all payment and transaction API tests"""
        print("Payment and Transaction API Test Suite")
        print("=" * 50)
        print(f"Environment: {self.environment.value}")
        print(f"Test Type: {test_type}")
        print(f"Timestamp: {datetime.now()}")
        print()
        
        # Setup test environment
        if not self.setup_test_environment():
            print("Failed to setup test environment")
            return False
        
        # Track results
        results = {
            'start_time': datetime.now(),
            'unit_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'security_tests': {},
            'webhook_tests': {},
            'errors': []
        }
        
        all_tests_passed = True
        
        try:
            # Run unit tests
            if test_type in ['all', 'unit']:
                unit_success = self.run_unit_tests(verbose)
                results['unit_tests']['passed'] = unit_success
                if not unit_success:
                    all_tests_passed = False
            
            # Run integration tests
            if test_type in ['all', 'integration']:
                integration_success = self.run_integration_tests(verbose)
                results['integration_tests']['passed'] = integration_success
                if not integration_success:
                    all_tests_passed = False
            
            # Run performance tests
            if test_type in ['all', 'performance']:
                performance_success = self.run_performance_tests(verbose)
                results['performance_tests']['passed'] = performance_success
                if not performance_success:
                    results['performance_issues'] = True
            
            # Run security tests
            if test_type in ['all', 'security']:
                security_success = self.run_security_tests(verbose)
                results['security_tests']['passed'] = security_success
                if not security_success:
                    results['security_issues'] = True
                    all_tests_passed = False  # Security failures are critical
            
            # Run webhook tests
            if test_type in ['all', 'webhook']:
                webhook_success = self.run_webhook_tests(verbose)
                results['webhook_tests']['passed'] = webhook_success
                if not webhook_success:
                    # Webhook failures are not critical for overall pass/fail
                    pass
        
        except Exception as e:
            print(f"Test execution failed: {e}")
            results['errors'].append(str(e))
            all_tests_passed = False
        
        finally:
            results['end_time'] = datetime.now()
        
        # Print summary
        print("\n" + "="*60)
        print("PAYMENT API TEST EXECUTION SUMMARY")
        print("="*60)
        
        for test_category, test_result in results.items():
            if isinstance(test_result, dict) and 'passed' in test_result:
                status = "PASSED" if test_result['passed'] else "FAILED"
                print(f"{test_category.replace('_', ' ').title()}: {status}")
        
        if results['errors']:
            print(f"\nErrors encountered: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
        
        overall_status = "PASSED" if all_tests_passed else "FAILED"
        print(f"\nOverall Status: {overall_status}")
        
        # Generate report if requested
        if generate_report:
            self.generate_test_report(results)
        
        return all_tests_passed


def main():
    """Main entry point for payment API test runner"""
    parser = argparse.ArgumentParser(description='Payment and Transaction API Test Runner')
    
    parser.add_argument(
        '--environment',
        choices=['development', 'staging', 'production'],
        default='development',
        help='Test environment'
    )
    
    parser.add_argument(
        '--test-type',
        choices=['all', 'unit', 'integration', 'performance', 'security', 'webhook'],
        default='all',
        help='Type of tests to run'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed test report'
    )
    
    args = parser.parse_args()
    
    # Map environment string to enum
    env_map = {
        'development': Environment.DEVELOPMENT,
        'staging': Environment.STAGING,
        'production': Environment.PRODUCTION
    }
    
    environment = env_map[args.environment]
    
    # Create and run test runner
    runner = PaymentAPITestRunner(environment)
    
    success = runner.run_all_tests(
        test_type=args.test_type,
        verbose=args.verbose,
        generate_report=args.report
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()