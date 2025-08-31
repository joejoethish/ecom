"""
Payment Processing Tests

Comprehensive test suite for payment processing functionality including
all supported payment methods, gateway integration, failure scenarios,
refund processing, and security validation.
"""

import unittest
import time
from typing import Dict, Any, List
from selenium.webdriver.remote.webdriver import WebDriver

from .webdriver_manager import WebDriverManager
from .payment_pages import PaymentPage, RefundPage
from .payment_test_data import payment_test_data
from .cart_pages import ShoppingCartPage, CheckoutPage
from .auth_pages import LoginPage
from ..core.interfaces import Environment, UserRole, TestModule, Priority, ExecutionStatus, Severity
from ..core.models import TestCase, TestStep, TestExecution, Defect, BrowserInfo
from ..core.data_manager import TestDataManager
from ..core.error_handling import ErrorHandler
from ..core.config import get_config


class PaymentProcessingTestSuite(unittest.TestCase):
    """Test suite for payment processing functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test suite"""
        cls.environment = Environment.DEVELOPMENT
        cls.config = get_config("web", cls.environment)
        cls.base_url = cls.config.get("base_url", "http://localhost:3000")
        cls.webdriver_manager = WebDriverManager(cls.environment)
        cls.data_manager = TestDataManager(cls.environment)
        cls.error_handler = ErrorHandler()
        
        # Test data
        cls.test_users = {}
        cls.test_executions = []
        cls.defects = []
        cls.processed_orders = []  # Track orders for refund testing
    
    def setUp(self):
        """Set up individual test"""
        self.driver = self.webdriver_manager.create_driver("chrome", headless=False)
        self.browser_info = self.webdriver_manager.get_browser_info(self.driver)
        
        # Initialize page objects
        self.payment_page = PaymentPage(self.driver, self.webdriver_manager, self.base_url)
        self.refund_page = RefundPage(self.driver, self.webdriver_manager, self.base_url)
        self.cart_page = ShoppingCartPage(self.driver, self.webdriver_manager, self.base_url)
        self.checkout_page = CheckoutPage(self.driver, self.webdriver_manager, self.base_url)
        self.login_page = LoginPage(self.driver, self.webdriver_manager, self.base_url)
        
        # Create test execution record
        self.test_execution = TestExecution(
            id=f"EXE_PAY_{int(time.time())}",
            test_case_id="",
            environment=self.environment,
            status=ExecutionStatus.IN_PROGRESS,
            start_time=time.time(),
            browser_info=self.browser_info,
            executed_by="qa_framework"
        )
    
    def tearDown(self):
        """Clean up after test"""
        # Capture screenshot if test failed
        if hasattr(self, '_outcome') and not self._outcome.success:
            screenshot_path = self.webdriver_manager.capture_screenshot(
                self.driver, 
                f"failed_payment_{self._testMethodName}_{int(time.time())}.png"
            )
            self.test_execution.screenshots.append(screenshot_path)
        
        # Update test execution
        self.test_execution.end_time = time.time()
        self.test_execution.status = ExecutionStatus.PASSED if self._outcome.success else ExecutionStatus.FAILED
        self.__class__.test_executions.append(self.test_execution)
        
        # Close driver
        self.webdriver_manager.close_driver(self.driver)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test suite"""
        cls.webdriver_manager.close_all_drivers()
    
    def log_defect(self, title: str, description: str, severity: Severity, reproduction_steps: List[str]):
        """Log a defect"""
        defect = Defect(
            id=f"DEF_PAY_{int(time.time())}",
            test_case_id=self.test_execution.test_case_id,
            test_execution_id=self.test_execution.id,
            severity=severity,
            title=title,
            description=description,
            reproduction_steps=reproduction_steps,
            environment=self.environment,
            browser_info=self.browser_info,
            screenshots=self.test_execution.screenshots.copy()
        )
        self.__class__.defects.append(defect)
        return defect
    
    def setup_checkout_for_payment(self, order_amount: float = 99.99) -> bool:
        """Helper method to set up checkout process for payment testing"""
        try:
            # Navigate to checkout (simulate having items in cart)
            self.checkout_page.navigate_to()
            
            # For testing purposes, assume we're at payment step
            # In real scenario, would go through cart -> checkout -> payment
            self.payment_page.navigate_to()
            
            return self.payment_page.is_page_loaded()
            
        except Exception as e:
            self.logger.error(f"Failed to setup checkout: {str(e)}")
            return False
    
    # Credit Card Payment Tests
    
    def test_successful_credit_card_payment(self):
        """Test successful credit card payment processing"""
        self.test_execution.test_case_id = "TC_PAY_001"
        
        try:
            # Setup checkout
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get test data
            scenario_data = payment_test_data.create_payment_test_scenario("successful_credit_card")
            payment_method = scenario_data['payment_method']
            
            # Select credit card payment
            success = self.payment_page.select_payment_method('credit_card')
            self.assertTrue(success, "Should be able to select credit card payment")
            
            # Fill credit card details
            success = self.payment_page.fill_credit_card_form(payment_method)
            self.assertTrue(success, "Should be able to fill credit card details")
            
            # Verify security indicators
            security_checks = self.payment_page.verify_payment_security_indicators()
            self.assertTrue(security_checks['ssl_indicator'], "SSL indicator should be present")
            
            # Process payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process payment")
            
            # Verify payment result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"Payment should succeed: {result.get('error_message', '')}")
            self.assertNotEqual(result['transaction_id'], '', "Should receive transaction ID")
            
            # Store order for refund testing
            if result['success']:
                self.__class__.processed_orders.append({
                    'transaction_id': result['transaction_id'],
                    'amount': scenario_data['order_amount'],
                    'payment_method': 'credit_card'
                })
            
        except Exception as e:
            self.log_defect(
                "Credit card payment failed",
                f"Successful credit card payment processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to payment page",
                    "Select credit card payment method",
                    "Fill valid credit card details",
                    "Process payment",
                    "Verify payment success"
                ]
            )
            raise
    
    def test_successful_debit_card_payment(self):
        """Test successful debit card payment processing"""
        self.test_execution.test_case_id = "TC_PAY_002"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get debit card test data
            scenario_data = payment_test_data.create_payment_test_scenario("successful_credit_card")
            payment_method = payment_test_data.get_payment_method_data('debit_card', 'success')
            
            # Select debit card payment
            success = self.payment_page.select_payment_method('debit_card')
            self.assertTrue(success, "Should be able to select debit card payment")
            
            # Fill debit card details
            success = self.payment_page.fill_debit_card_form(payment_method)
            self.assertTrue(success, "Should be able to fill debit card details")
            
            # Process payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process payment")
            
            # Verify payment result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"Debit card payment should succeed: {result.get('error_message', '')}")
            
        except Exception as e:
            self.log_defect(
                "Debit card payment failed",
                f"Debit card payment processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to payment page",
                    "Select debit card payment method",
                    "Fill valid debit card details",
                    "Process payment",
                    "Verify payment success"
                ]
            )
            raise
    
    # Digital Wallet Payment Tests
    
    def test_successful_paypal_payment(self):
        """Test successful PayPal payment processing"""
        self.test_execution.test_case_id = "TC_PAY_003"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get PayPal test data
            scenario_data = payment_test_data.create_payment_test_scenario("successful_paypal")
            payment_method = scenario_data['payment_method']
            
            # Select PayPal payment
            success = self.payment_page.select_payment_method('paypal')
            self.assertTrue(success, "Should be able to select PayPal payment")
            
            # Fill PayPal details
            success = self.payment_page.fill_paypal_form(payment_method)
            self.assertTrue(success, "Should be able to fill PayPal details")
            
            # Process payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process PayPal payment")
            
            # Handle gateway redirect if needed
            self.payment_page.handle_gateway_redirect()
            
            # Verify payment result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"PayPal payment should succeed: {result.get('error_message', '')}")
            
        except Exception as e:
            self.log_defect(
                "PayPal payment failed",
                f"PayPal payment processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to payment page",
                    "Select PayPal payment method",
                    "Fill PayPal account details",
                    "Process payment through PayPal gateway",
                    "Verify payment success"
                ]
            )
            raise
    
    def test_successful_google_pay_payment(self):
        """Test successful Google Pay payment processing"""
        self.test_execution.test_case_id = "TC_PAY_004"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get Google Pay test data
            payment_method = payment_test_data.get_payment_method_data('google_pay', 'success')
            
            # Select Google Pay payment
            success = self.payment_page.select_payment_method('google_pay')
            self.assertTrue(success, "Should be able to select Google Pay payment")
            
            # Process Google Pay payment (usually involves clicking Google Pay button)
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process Google Pay payment")
            
            # Verify payment result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"Google Pay payment should succeed: {result.get('error_message', '')}")
            
        except Exception as e:
            self.log_defect(
                "Google Pay payment failed",
                f"Google Pay payment processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to payment page",
                    "Select Google Pay payment method",
                    "Process payment through Google Pay",
                    "Verify payment success"
                ]
            )
            raise
    
    def test_successful_apple_pay_payment(self):
        """Test successful Apple Pay payment processing"""
        self.test_execution.test_case_id = "TC_PAY_005"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get Apple Pay test data
            payment_method = payment_test_data.get_payment_method_data('apple_pay', 'success')
            
            # Select Apple Pay payment
            success = self.payment_page.select_payment_method('apple_pay')
            self.assertTrue(success, "Should be able to select Apple Pay payment")
            
            # Process Apple Pay payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process Apple Pay payment")
            
            # Verify payment result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"Apple Pay payment should succeed: {result.get('error_message', '')}")
            
        except Exception as e:
            self.log_defect(
                "Apple Pay payment failed",
                f"Apple Pay payment processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to payment page",
                    "Select Apple Pay payment method",
                    "Process payment through Apple Pay",
                    "Verify payment success"
                ]
            )
            raise
    
    # UPI Payment Tests
    
    def test_successful_upi_payment(self):
        """Test successful UPI payment processing"""
        self.test_execution.test_case_id = "TC_PAY_006"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get UPI test data
            scenario_data = payment_test_data.create_payment_test_scenario("successful_upi")
            payment_method = scenario_data['payment_method']
            
            # Select UPI payment
            success = self.payment_page.select_payment_method('upi')
            self.assertTrue(success, "Should be able to select UPI payment")
            
            # Fill UPI details
            success = self.payment_page.fill_upi_form(payment_method)
            self.assertTrue(success, "Should be able to fill UPI details")
            
            # Verify UPI ID format
            upi_valid = self.payment_page.verify_upi_id_format(payment_method['upi_id'])
            self.assertTrue(upi_valid, "UPI ID format should be valid")
            
            # Process payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process UPI payment")
            
            # Verify payment result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"UPI payment should succeed: {result.get('error_message', '')}")
            
        except Exception as e:
            self.log_defect(
                "UPI payment failed",
                f"UPI payment processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to payment page",
                    "Select UPI payment method",
                    "Fill valid UPI ID",
                    "Process payment",
                    "Verify payment success"
                ]
            )
            raise
    
    # EMI Payment Tests
    
    def test_successful_emi_payment(self):
        """Test successful EMI payment processing"""
        self.test_execution.test_case_id = "TC_PAY_007"
        
        try:
            # Use higher amount for EMI eligibility
            self.assertTrue(self.setup_checkout_for_payment(1299.99), "Should setup checkout successfully")
            
            # Get EMI test data
            scenario_data = payment_test_data.create_payment_test_scenario("successful_emi")
            payment_method = scenario_data['payment_method']
            
            # Select EMI payment
            success = self.payment_page.select_payment_method('emi')
            self.assertTrue(success, "Should be able to select EMI payment")
            
            # Configure EMI options
            success = self.payment_page.configure_emi_options(payment_method)
            self.assertTrue(success, "Should be able to configure EMI options")
            
            # Verify EMI calculations
            emi_details = self.payment_page.get_emi_details()
            self.assertIn('monthly_amount', emi_details, "Should display monthly EMI amount")
            self.assertIn('interest_rate', emi_details, "Should display interest rate")
            
            # Validate EMI calculation
            expected_emi = payment_test_data.calculate_emi_details(
                scenario_data['order_amount'],
                payment_method['tenure'],
                payment_method['interest_rate'],
                payment_method.get('processing_fee', 0)
            )
            
            # Process payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process EMI payment")
            
            # Verify payment result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"EMI payment should succeed: {result.get('error_message', '')}")
            
        except Exception as e:
            self.log_defect(
                "EMI payment failed",
                f"EMI payment processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to payment page",
                    "Select EMI payment method",
                    "Configure EMI tenure and bank",
                    "Verify EMI calculations",
                    "Process payment",
                    "Verify payment success"
                ]
            )
            raise
    
    # COD Payment Tests
    
    def test_successful_cod_payment(self):
        """Test successful Cash on Delivery order"""
        self.test_execution.test_case_id = "TC_PAY_008"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get COD test data
            scenario_data = payment_test_data.create_payment_test_scenario("successful_cod")
            
            # Select COD payment
            success = self.payment_page.select_payment_method('cod')
            self.assertTrue(success, "Should be able to select COD payment")
            
            # Verify COD availability
            cod_details = self.payment_page.verify_cod_availability()
            self.assertTrue(cod_details['available'], "COD should be available")
            self.assertNotEqual(cod_details['instructions'], '', "Should provide COD instructions")
            
            # Process COD order
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process COD order")
            
            # Verify order result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"COD order should succeed: {result.get('error_message', '')}")
            
        except Exception as e:
            self.log_defect(
                "COD order failed",
                f"Cash on Delivery order processing failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to payment page",
                    "Select COD payment method",
                    "Verify COD availability",
                    "Process COD order",
                    "Verify order success"
                ]
            )
            raise
    
    # Payment Failure and Retry Tests
    
    def test_declined_card_payment(self):
        """Test declined credit card payment handling"""
        self.test_execution.test_case_id = "TC_PAY_009"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get declined card test data
            scenario_data = payment_test_data.create_payment_test_scenario("declined_card")
            payment_method = scenario_data['payment_method']
            
            # Select credit card payment
            success = self.payment_page.select_payment_method('credit_card')
            self.assertTrue(success, "Should be able to select credit card payment")
            
            # Fill declined card details
            success = self.payment_page.fill_credit_card_form(payment_method)
            self.assertTrue(success, "Should be able to fill card details")
            
            # Process payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to attempt payment processing")
            
            # Verify payment was declined
            result = self.payment_page.get_payment_result()
            self.assertFalse(result['success'], "Payment should be declined")
            self.assertEqual(result['status'], 'failed', "Payment status should be failed")
            self.assertNotEqual(result['error_message'], '', "Should provide error message")
            
            # Test retry functionality
            retry_success = self.payment_page.retry_payment()
            self.assertTrue(retry_success, "Should be able to retry payment")
            
        except Exception as e:
            self.log_defect(
                "Declined card handling failed",
                f"Declined card payment handling failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to payment page",
                    "Select credit card payment",
                    "Fill declined card details",
                    "Process payment",
                    "Verify decline handling",
                    "Test retry functionality"
                ]
            )
            raise
    
    def test_insufficient_funds_scenario(self):
        """Test insufficient funds payment scenario"""
        self.test_execution.test_case_id = "TC_PAY_010"
        
        try:
            # Use high amount to trigger insufficient funds
            self.assertTrue(self.setup_checkout_for_payment(999.99), "Should setup checkout successfully")
            
            # Get insufficient funds test data
            scenario_data = payment_test_data.create_payment_test_scenario("insufficient_funds")
            payment_method = scenario_data['payment_method']
            
            # Select credit card payment
            success = self.payment_page.select_payment_method('credit_card')
            self.assertTrue(success, "Should be able to select credit card payment")
            
            # Fill card details
            success = self.payment_page.fill_credit_card_form(payment_method)
            self.assertTrue(success, "Should be able to fill card details")
            
            # Process payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to attempt payment processing")
            
            # Verify insufficient funds error
            result = self.payment_page.get_payment_result()
            self.assertFalse(result['success'], "Payment should fail due to insufficient funds")
            self.assertIn('insufficient', result['error_message'].lower(), "Should indicate insufficient funds")
            
            # Test change payment method option
            change_success = self.payment_page.change_payment_method()
            self.assertTrue(change_success, "Should be able to change payment method")
            
        except Exception as e:
            self.log_defect(
                "Insufficient funds handling failed",
                f"Insufficient funds scenario handling failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to payment page",
                    "Select credit card payment",
                    "Fill card with insufficient funds",
                    "Process payment",
                    "Verify insufficient funds error",
                    "Test change payment method"
                ]
            )
            raise
    
    # Payment Validation Tests
    
    def test_invalid_card_number_validation(self):
        """Test invalid card number validation"""
        self.test_execution.test_case_id = "TC_PAY_011"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get invalid card number scenario
            failure_scenario = payment_test_data.get_failure_scenario('invalid_card_number')
            payment_method = failure_scenario['payment_data']
            
            # Select credit card payment
            success = self.payment_page.select_payment_method('credit_card')
            self.assertTrue(success, "Should be able to select credit card payment")
            
            # Test card number validation
            valid = self.payment_page.validate_card_number_format(payment_method['card_number'])
            self.assertFalse(valid, "Invalid card number should be rejected")
            
            # Verify validation errors
            errors = self.payment_page.get_validation_errors()
            self.assertGreater(len(errors), 0, "Should show validation errors")
            
        except Exception as e:
            self.log_defect(
                "Card number validation failed",
                f"Invalid card number validation failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to payment page",
                    "Select credit card payment",
                    "Enter invalid card number",
                    "Verify validation error appears"
                ]
            )
            raise
    
    def test_expired_card_validation(self):
        """Test expired card validation"""
        self.test_execution.test_case_id = "TC_PAY_012"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get expired card scenario
            failure_scenario = payment_test_data.get_failure_scenario('expired_card')
            payment_method = failure_scenario['payment_data']
            
            # Select credit card payment
            success = self.payment_page.select_payment_method('credit_card')
            self.assertTrue(success, "Should be able to select credit card payment")
            
            # Test expiry date validation
            valid = self.payment_page.validate_expiry_date(
                payment_method['expiry_month'],
                payment_method['expiry_year']
            )
            self.assertFalse(valid, "Expired card should be rejected")
            
        except Exception as e:
            self.log_defect(
                "Expired card validation failed",
                f"Expired card validation failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to payment page",
                    "Select credit card payment",
                    "Enter expired card details",
                    "Verify expiry validation error"
                ]
            )
            raise
    
    def test_invalid_cvv_validation(self):
        """Test invalid CVV validation"""
        self.test_execution.test_case_id = "TC_PAY_013"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get invalid CVV scenario
            failure_scenario = payment_test_data.get_failure_scenario('invalid_cvv')
            payment_method = failure_scenario['payment_data']
            
            # Select credit card payment
            success = self.payment_page.select_payment_method('credit_card')
            self.assertTrue(success, "Should be able to select credit card payment")
            
            # Test CVV validation
            valid = self.payment_page.validate_cvv_format(payment_method['cvv'])
            self.assertFalse(valid, "Invalid CVV should be rejected")
            
        except Exception as e:
            self.log_defect(
                "CVV validation failed",
                f"Invalid CVV validation failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to payment page",
                    "Select credit card payment",
                    "Enter invalid CVV",
                    "Verify CVV validation error"
                ]
            )
            raise
    
    def test_invalid_upi_id_validation(self):
        """Test invalid UPI ID validation"""
        self.test_execution.test_case_id = "TC_PAY_014"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get invalid UPI ID scenario
            failure_scenario = payment_test_data.get_failure_scenario('invalid_upi_id')
            payment_method = failure_scenario['payment_data']
            
            # Select UPI payment
            success = self.payment_page.select_payment_method('upi')
            self.assertTrue(success, "Should be able to select UPI payment")
            
            # Test UPI ID validation
            valid = self.payment_page.verify_upi_id_format(payment_method['upi_id'])
            self.assertFalse(valid, "Invalid UPI ID should be rejected")
            
        except Exception as e:
            self.log_defect(
                "UPI ID validation failed",
                f"Invalid UPI ID validation failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to payment page",
                    "Select UPI payment",
                    "Enter invalid UPI ID",
                    "Verify UPI ID validation error"
                ]
            )
            raise
    
    # Payment Security Tests
    
    def test_payment_security_indicators(self):
        """Test payment security indicators are present"""
        self.test_execution.test_case_id = "TC_PAY_015"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Verify security indicators
            security_checks = self.payment_page.verify_payment_security_indicators()
            
            self.assertTrue(security_checks['ssl_indicator'], "SSL security indicator should be present")
            self.assertTrue(security_checks['security_badges'], "Security badges should be displayed")
            self.assertTrue(security_checks['encryption_notice'], "Encryption notice should be present")
            
            # Verify HTTPS connection
            current_url = self.payment_page.get_current_url()
            self.assertTrue(current_url.startswith('https://'), "Payment page should use HTTPS")
            
        except Exception as e:
            self.log_defect(
                "Payment security indicators missing",
                f"Payment security indicators validation failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to payment page",
                    "Verify SSL indicator presence",
                    "Verify security badges",
                    "Verify encryption notice",
                    "Verify HTTPS connection"
                ]
            )
            raise
    
    # Refund Processing Tests
    
    def test_full_order_refund(self):
        """Test full order refund processing"""
        self.test_execution.test_case_id = "TC_PAY_016"
        
        try:
            # Skip if no processed orders available
            if not self.__class__.processed_orders:
                self.skipTest("No processed orders available for refund testing")
            
            # Get a processed order
            order = self.__class__.processed_orders[0]
            
            # Navigate to refund page
            self.refund_page.navigate_to()
            self.assertTrue(self.refund_page.is_page_loaded(), "Refund page should load")
            
            # Process full refund
            refund_result = self.refund_page.process_full_refund(
                order['transaction_id'],
                "Customer Request"
            )
            
            self.assertTrue(refund_result['success'], f"Full refund should succeed: {refund_result.get('error', '')}")
            self.assertNotEqual(refund_result['refund_reference'], '', "Should receive refund reference")
            self.assertEqual(refund_result['status'], 'processed', "Refund status should be processed")
            
        except Exception as e:
            self.log_defect(
                "Full refund processing failed",
                f"Full order refund processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to refund page",
                    "Enter order number",
                    "Select refund reason",
                    "Process full refund",
                    "Verify refund success"
                ]
            )
            raise
    
    def test_partial_order_refund(self):
        """Test partial order refund processing"""
        self.test_execution.test_case_id = "TC_PAY_017"
        
        try:
            # Skip if no processed orders available
            if not self.__class__.processed_orders:
                self.skipTest("No processed orders available for refund testing")
            
            # Get a processed order
            order = self.__class__.processed_orders[0]
            partial_amount = order['amount'] / 2  # Refund half the amount
            
            # Navigate to refund page
            self.refund_page.navigate_to()
            self.assertTrue(self.refund_page.is_page_loaded(), "Refund page should load")
            
            # Process partial refund
            refund_result = self.refund_page.process_partial_refund(
                order['transaction_id'],
                partial_amount,
                "Partial Return"
            )
            
            self.assertTrue(refund_result['success'], f"Partial refund should succeed: {refund_result.get('error', '')}")
            self.assertNotEqual(refund_result['refund_reference'], '', "Should receive refund reference")
            
        except Exception as e:
            self.log_defect(
                "Partial refund processing failed",
                f"Partial order refund processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Navigate to refund page",
                    "Enter order number",
                    "Select partial refund option",
                    "Enter refund amount",
                    "Process partial refund",
                    "Verify refund success"
                ]
            )
            raise
    
    # High Value and International Payment Tests
    
    def test_high_value_payment(self):
        """Test high value payment processing"""
        self.test_execution.test_case_id = "TC_PAY_018"
        
        try:
            # Setup high value order
            self.assertTrue(self.setup_checkout_for_payment(5000.00), "Should setup high value checkout")
            
            # Get high value payment scenario
            scenario_data = payment_test_data.create_payment_test_scenario("high_value_order")
            payment_method = scenario_data['payment_method']
            
            # Select credit card payment
            success = self.payment_page.select_payment_method('credit_card')
            self.assertTrue(success, "Should be able to select credit card payment")
            
            # Fill card details
            success = self.payment_page.fill_credit_card_form(payment_method)
            self.assertTrue(success, "Should be able to fill card details")
            
            # Process high value payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process high value payment")
            
            # Verify payment result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"High value payment should succeed: {result.get('error_message', '')}")
            
        except Exception as e:
            self.log_defect(
                "High value payment failed",
                f"High value payment processing failed: {str(e)}",
                Severity.CRITICAL,
                [
                    "Setup high value order (>$5000)",
                    "Select credit card payment",
                    "Fill valid card details",
                    "Process payment",
                    "Verify payment success"
                ]
            )
            raise
    
    def test_international_card_payment(self):
        """Test international credit card payment"""
        self.test_execution.test_case_id = "TC_PAY_019"
        
        try:
            self.assertTrue(self.setup_checkout_for_payment(), "Should setup checkout successfully")
            
            # Get international card scenario
            scenario_data = payment_test_data.create_payment_test_scenario("international_card")
            payment_method = scenario_data['payment_method']
            
            # Select credit card payment
            success = self.payment_page.select_payment_method('credit_card')
            self.assertTrue(success, "Should be able to select credit card payment")
            
            # Fill international card details
            success = self.payment_page.fill_credit_card_form(payment_method)
            self.assertTrue(success, "Should be able to fill international card details")
            
            # Process payment
            success = self.payment_page.process_payment()
            self.assertTrue(success, "Should be able to process international payment")
            
            # Verify payment result
            result = self.payment_page.get_payment_result()
            self.assertTrue(result['success'], f"International card payment should succeed: {result.get('error_message', '')}")
            
        except Exception as e:
            self.log_defect(
                "International card payment failed",
                f"International card payment processing failed: {str(e)}",
                Severity.MAJOR,
                [
                    "Navigate to payment page",
                    "Select credit card payment",
                    "Fill international card details",
                    "Process payment",
                    "Verify payment success"
                ]
            )
            raise


if __name__ == '__main__':
    unittest.main()