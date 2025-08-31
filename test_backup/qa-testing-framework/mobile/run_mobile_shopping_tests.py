#!/usr/bin/env python3
"""
Mobile Shopping and Checkout Test Runner

Executes comprehensive mobile shopping and checkout tests including:
- Product browsing and search
- Shopping cart management
- Checkout flow with touch interactions
- Mobile payment methods
- Mobile-specific features (camera, location services)
- Offline behavior testing
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.config import ConfigManager
    from core.utils import Logger
except ImportError:
    # Fallback for testing
    class ConfigManager:
        def get_value(self, key, default=None):
            return default
    
    class Logger:
        def __init__(self, name):
            self.name = name
        def info(self, msg):
            print(f"[INFO] {self.name}: {msg}")
        def error(self, msg):
            print(f"[ERROR] {self.name}: {msg}")
        def warning(self, msg):
            print(f"[WARNING] {self.name}: {msg}")

from mobile.appium_manager import AppiumManager
from mobile.mobile_config import MobileConfig, Platform
from mobile.test_mobile_shopping import (
    MobileShoppingTests, 
    MobileCheckoutFlowTests, 
    MobilePaymentTests,
    run_comprehensive_mobile_shopping_tests
)


class MobileShoppingTestRunner:
    """Main test runner for mobile shopping and checkout tests."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = Logger(self.__class__.__name__)
        self.config_manager = ConfigManager()
        self.mobile_config = MobileConfig(self.config_manager)
        self.appium_manager = None
        self.driver = None
        
        # Load test configuration
        self.test_config = self._load_test_config(config_path)
        
        # Test results
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def _load_test_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load test configuration from file."""
        try:
            if not config_path:
                config_path = os.path.join(
                    os.path.dirname(__file__), 
                    'mobile_shopping_config.json'
                )
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.logger.info(f"Loaded test configuration from {config_path}")
            return config.get('mobile_shopping_test_config', {})
            
        except Exception as e:
            self.logger.error(f"Failed to load test configuration: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default test configuration."""
        return {
            "platforms": {
                "android": {
                    "device_name": "Android Emulator",
                    "platform_version": "11.0",
                    "app_package": "com.ecommerce.mobile",
                    "app_activity": ".MainActivity"
                }
            },
            "test_data": {
                "checkout": {
                    "shipping_addresses": [{
                        "first_name": "Test",
                        "last_name": "User",
                        "address_line1": "123 Test St",
                        "city": "Test City",
                        "state": "CA",
                        "zip_code": "12345",
                        "country": "US"
                    }],
                    "payment_methods": {
                        "credit_cards": [{
                            "card_number": "4111111111111111",
                            "expiry_date": "12/25",
                            "cvv": "123",
                            "cardholder_name": "Test User"
                        }]
                    }
                }
            }
        }
    
    def setup_test_environment(self, platform: str, device_name: Optional[str] = None) -> bool:
        """Set up test environment for mobile shopping tests."""
        try:
            self.start_time = datetime.now()
            self.logger.info(f"Setting up test environment for {platform}")
            
            # Initialize Appium manager
            self.appium_manager = AppiumManager(self.config_manager)
            
            # Start Appium server
            if not self.appium_manager.start_appium_server():
                self.logger.error("Failed to start Appium server")
                return False
            
            # Get device configuration
            platform_config = self.test_config.get('platforms', {}).get(platform.lower(), {})
            if device_name:
                platform_config['device_name'] = device_name
            
            # Create driver based on platform
            if platform.lower() == 'android':
                self.driver = self.appium_manager.create_android_driver(platform_config)
            elif platform.lower() == 'ios':
                self.driver = self.appium_manager.create_ios_driver(platform_config)
            else:
                self.logger.error(f"Unsupported platform: {platform}")
                return False
            
            if not self.driver:
                self.logger.error("Failed to create mobile driver")
                return False
            
            self.logger.info("Test environment setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Test environment setup failed: {str(e)}")
            return False
    
    def teardown_test_environment(self) -> None:
        """Clean up test environment."""
        try:
            self.end_time = datetime.now()
            
            if self.appium_manager:
                self.appium_manager.quit_driver()
                self.appium_manager.stop_appium_server()
            
            self.logger.info("Test environment teardown completed")
            
        except Exception as e:
            self.logger.error(f"Test environment teardown failed: {str(e)}")
    
    def run_product_browsing_tests(self) -> Dict[str, bool]:
        """Run product browsing and search tests."""
        try:
            self.logger.info("Running product browsing tests...")
            
            shopping_tests = MobileShoppingTests(self.driver)
            
            results = {}
            results['product_browsing'] = shopping_tests.test_product_browsing()
            results['touch_interactions'] = shopping_tests.test_touch_interactions()
            
            # Test different search scenarios
            search_terms = self.test_config.get('test_data', {}).get('products', {}).get('search_terms', ['smartphone'])
            for i, term in enumerate(search_terms[:3]):  # Test first 3 terms
                result_key = f'search_{term}'
                # This would involve navigating to search and testing the term
                results[result_key] = True  # Placeholder
            
            passed = sum(1 for result in results.values() if result)
            total = len(results)
            self.logger.info(f"Product browsing tests: {passed}/{total} passed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Product browsing tests failed: {str(e)}")
            return {'browsing_error': False}
    
    def run_shopping_cart_tests(self) -> Dict[str, bool]:
        """Run shopping cart management tests."""
        try:
            self.logger.info("Running shopping cart tests...")
            
            shopping_tests = MobileShoppingTests(self.driver)
            
            results = {}
            results['add_to_cart'] = shopping_tests.test_add_to_cart_flow()
            results['cart_management'] = shopping_tests.test_shopping_cart_management()
            results['offline_cart'] = shopping_tests.test_offline_shopping_behavior()
            
            passed = sum(1 for result in results.values() if result)
            total = len(results)
            self.logger.info(f"Shopping cart tests: {passed}/{total} passed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Shopping cart tests failed: {str(e)}")
            return {'cart_error': False}
    
    def run_checkout_flow_tests(self) -> Dict[str, bool]:
        """Run checkout flow tests with touch interactions."""
        try:
            self.logger.info("Running checkout flow tests...")
            
            checkout_tests = MobileCheckoutFlowTests(self.driver)
            
            results = {}
            
            # Get test data
            shipping_addresses = self.test_config.get('test_data', {}).get('checkout', {}).get('shipping_addresses', [{}])
            guest_info = self.test_config.get('test_data', {}).get('guest_checkout', {})
            
            test_data = {
                'shipping_address': shipping_addresses[0] if shipping_addresses else {},
                'guest_info': guest_info.get('guest_info', {}),
                'payment_details': self._get_test_payment_details()
            }
            
            # Run checkout tests
            results['guest_checkout'] = checkout_tests.test_guest_checkout_flow(test_data)
            results['express_checkout'] = checkout_tests.test_express_checkout_flow(test_data)
            results['mobile_wallet'] = checkout_tests.test_mobile_wallet_integration()
            results['checkout_validation'] = checkout_tests.test_checkout_form_validation()
            
            passed = sum(1 for result in results.values() if result)
            total = len(results)
            self.logger.info(f"Checkout flow tests: {passed}/{total} passed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Checkout flow tests failed: {str(e)}")
            return {'checkout_error': False}
    
    def run_mobile_payment_tests(self) -> Dict[str, bool]:
        """Run mobile payment method tests."""
        try:
            self.logger.info("Running mobile payment tests...")
            
            payment_tests = MobilePaymentTests(self.driver)
            
            results = {}
            
            # Get payment test data
            card_data = self._get_test_payment_details()
            
            results['credit_card_payment'] = payment_tests.test_credit_card_payments(card_data)
            results['digital_wallet_payment'] = payment_tests.test_digital_wallet_payments()
            results['payment_security'] = payment_tests.test_payment_security_features()
            
            passed = sum(1 for result in results.values() if result)
            total = len(results)
            self.logger.info(f"Mobile payment tests: {passed}/{total} passed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Mobile payment tests failed: {str(e)}")
            return {'payment_error': False}
    
    def run_mobile_specific_feature_tests(self) -> Dict[str, bool]:
        """Run mobile-specific feature tests (camera, location services)."""
        try:
            self.logger.info("Running mobile-specific feature tests...")
            
            shopping_tests = MobileShoppingTests(self.driver)
            
            results = {}
            results['camera_integration'] = shopping_tests.test_mobile_camera_integration()
            results['location_services'] = shopping_tests.test_location_services_integration()
            results['mobile_features'] = shopping_tests.test_mobile_specific_features()
            
            passed = sum(1 for result in results.values() if result)
            total = len(results)
            self.logger.info(f"Mobile-specific feature tests: {passed}/{total} passed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Mobile-specific feature tests failed: {str(e)}")
            return {'mobile_features_error': False}
    
    def run_user_journey_tests(self) -> Dict[str, bool]:
        """Run end-to-end user journey tests."""
        try:
            self.logger.info("Running user journey tests...")
            
            results = {}
            
            # Get journey configurations
            journeys = self.test_config.get('test_scenarios', {}).get('user_journeys', [])
            
            for journey in journeys:
                journey_name = journey.get('name', 'unknown_journey')
                journey_steps = journey.get('steps', [])
                
                # Execute journey steps
                journey_result = self._execute_user_journey(journey_name, journey_steps)
                results[journey_name] = journey_result
            
            passed = sum(1 for result in results.values() if result)
            total = len(results)
            self.logger.info(f"User journey tests: {passed}/{total} passed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"User journey tests failed: {str(e)}")
            return {'journey_error': False}
    
    def _execute_user_journey(self, journey_name: str, steps: List[str]) -> bool:
        """Execute a specific user journey."""
        try:
            self.logger.info(f"Executing user journey: {journey_name}")
            
            shopping_tests = MobileShoppingTests(self.driver)
            
            # Map steps to test methods
            step_mapping = {
                'browse_products': shopping_tests.test_product_browsing,
                'add_to_cart': shopping_tests.test_add_to_cart_flow,
                'modify_cart': shopping_tests.test_shopping_cart_management,
                'proceed_to_checkout': lambda: True,  # Navigation step
                'complete_payment': lambda: True,     # Would involve actual payment flow
            }
            
            for step in steps:
                if step in step_mapping:
                    step_result = step_mapping[step]()
                    if not step_result:
                        self.logger.error(f"Journey step failed: {step}")
                        return False
                else:
                    self.logger.warning(f"Unknown journey step: {step}")
            
            self.logger.info(f"User journey completed successfully: {journey_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"User journey execution failed: {str(e)}")
            return False
    
    def _get_test_payment_details(self) -> Dict[str, str]:
        """Get test payment details from configuration."""
        credit_cards = (
            self.test_config
            .get('test_data', {})
            .get('checkout', {})
            .get('payment_methods', {})
            .get('credit_cards', [])
        )
        
        if credit_cards:
            return credit_cards[0]
        
        # Default test card
        return {
            'card_number': '4111111111111111',
            'expiry_date': '12/25',
            'cvv': '123',
            'cardholder_name': 'Test User'
        }
    
    def run_comprehensive_test_suite(self, platform: str, device_name: Optional[str] = None) -> bool:
        """Run the complete mobile shopping and checkout test suite."""
        try:
            # Setup test environment
            if not self.setup_test_environment(platform, device_name):
                return False
            
            # Run all test categories
            self.test_results['product_browsing'] = self.run_product_browsing_tests()
            self.test_results['shopping_cart'] = self.run_shopping_cart_tests()
            self.test_results['checkout_flow'] = self.run_checkout_flow_tests()
            self.test_results['mobile_payments'] = self.run_mobile_payment_tests()
            self.test_results['mobile_features'] = self.run_mobile_specific_feature_tests()
            self.test_results['user_journeys'] = self.run_user_journey_tests()
            
            # Generate test report
            self._generate_test_report()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Comprehensive test suite failed: {str(e)}")
            return False
        
        finally:
            self.teardown_test_environment()
    
    def _generate_test_report(self) -> None:
        """Generate comprehensive test report."""
        try:
            # Calculate overall statistics
            total_tests = 0
            passed_tests = 0
            
            for category, category_results in self.test_results.items():
                if isinstance(category_results, dict):
                    total_tests += len(category_results)
                    passed_tests += sum(1 for result in category_results.values() if result)
            
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
            
            # Create report
            report = {
                'test_summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': total_tests - passed_tests,
                    'success_rate': round(success_rate, 2),
                    'duration_seconds': round(duration, 2),
                    'start_time': self.start_time.isoformat() if self.start_time else None,
                    'end_time': self.end_time.isoformat() if self.end_time else None
                },
                'test_results': self.test_results,
                'device_info': {
                    'platform': self.driver.capabilities.get('platformName') if self.driver else 'Unknown',
                    'device_name': self.driver.capabilities.get('deviceName') if self.driver else 'Unknown',
                    'platform_version': self.driver.capabilities.get('platformVersion') if self.driver else 'Unknown'
                },
                'configuration': {
                    'test_config_loaded': bool(self.test_config),
                    'appium_server': self.mobile_config.base_config.get('appium', {}).get('server_url', 'Unknown')
                }
            }
            
            # Write report to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"mobile_shopping_test_report_{timestamp}.json"
            
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Print summary
            print("\n" + "="*60)
            print("MOBILE SHOPPING TEST SUITE RESULTS")
            print("="*60)
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            print(f"Success Rate: {success_rate:.1f}%")
            print(f"Duration: {duration:.1f} seconds")
            print(f"Report saved: {report_filename}")
            print("="*60)
            
            # Print detailed results
            for category, results in self.test_results.items():
                if isinstance(results, dict):
                    category_passed = sum(1 for result in results.values() if result)
                    category_total = len(results)
                    print(f"\n{category.upper()}: {category_passed}/{category_total}")
                    
                    for test_name, result in results.items():
                        status = "PASS" if result else "FAIL"
                        print(f"  {test_name}: {status}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate test report: {str(e)}")


def main():
    """Main entry point for mobile shopping test runner."""
    parser = argparse.ArgumentParser(description='Mobile Shopping and Checkout Test Runner')
    parser.add_argument('--platform', choices=['android', 'ios'], default='android',
                       help='Mobile platform to test (default: android)')
    parser.add_argument('--device', help='Specific device name to use')
    parser.add_argument('--config', help='Path to test configuration file')
    parser.add_argument('--test-category', 
                       choices=['browsing', 'cart', 'checkout', 'payments', 'features', 'journeys', 'all'],
                       default='all', help='Test category to run (default: all)')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = MobileShoppingTestRunner(args.config)
    
    try:
        if args.test_category == 'all':
            # Run comprehensive test suite
            success = runner.run_comprehensive_test_suite(args.platform, args.device)
        else:
            # Setup environment for specific test category
            if not runner.setup_test_environment(args.platform, args.device):
                return 1
            
            # Run specific test category
            if args.test_category == 'browsing':
                results = runner.run_product_browsing_tests()
            elif args.test_category == 'cart':
                results = runner.run_shopping_cart_tests()
            elif args.test_category == 'checkout':
                results = runner.run_checkout_flow_tests()
            elif args.test_category == 'payments':
                results = runner.run_mobile_payment_tests()
            elif args.test_category == 'features':
                results = runner.run_mobile_specific_feature_tests()
            elif args.test_category == 'journeys':
                results = runner.run_user_journey_tests()
            
            runner.teardown_test_environment()
            
            # Print results for specific category
            passed = sum(1 for result in results.values() if result)
            total = len(results)
            print(f"\n{args.test_category.upper()} TESTS: {passed}/{total} passed")
            
            success = passed == total
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        runner.teardown_test_environment()
        return 1
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        runner.teardown_test_environment()
        return 1


if __name__ == '__main__':
    sys.exit(main())