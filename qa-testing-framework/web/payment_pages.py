"""
Payment Processing Page Objects

Page object models for payment processing functionality including
credit/debit cards, digital wallets, UPI, EMI, COD, and payment security.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException

try:
    from .page_objects import BasePage, BaseFormPage
    from .webdriver_manager import WebDriverManager
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from web.page_objects import BasePage, BaseFormPage
    from web.webdriver_manager import WebDriverManager


class PaymentPage(BaseFormPage):
    """Payment processing page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
        
        # Payment method selection
        self.payment_methods_container = (By.CSS_SELECTOR, ".payment-methods, [data-testid='payment-methods']")
        self.credit_card_option = (By.CSS_SELECTOR, "input[value='credit_card'], [data-testid='credit-card']")
        self.debit_card_option = (By.CSS_SELECTOR, "input[value='debit_card'], [data-testid='debit-card']")
        self.paypal_option = (By.CSS_SELECTOR, "input[value='paypal'], [data-testid='paypal']")
        self.google_pay_option = (By.CSS_SELECTOR, "input[value='google_pay'], [data-testid='google-pay']")
        self.apple_pay_option = (By.CSS_SELECTOR, "input[value='apple_pay'], [data-testid='apple-pay']")
        self.upi_option = (By.CSS_SELECTOR, "input[value='upi'], [data-testid='upi']")
        self.emi_option = (By.CSS_SELECTOR, "input[value='emi'], [data-testid='emi']")
        self.cod_option = (By.CSS_SELECTOR, "input[value='cod'], [data-testid='cod']")
        
        # Credit/Debit Card Form
        self.card_form = (By.CSS_SELECTOR, ".card-form, [data-testid='card-form']")
        self.card_number_input = (By.CSS_SELECTOR, "input[name='cardNumber'], [data-testid='card-number']")
        self.expiry_month_select = (By.CSS_SELECTOR, "select[name='expiryMonth'], [data-testid='expiry-month']")
        self.expiry_year_select = (By.CSS_SELECTOR, "select[name='expiryYear'], [data-testid='expiry-year']")
        self.cvv_input = (By.CSS_SELECTOR, "input[name='cvv'], [data-testid='cvv']")
        self.cardholder_name_input = (By.CSS_SELECTOR, "input[name='cardholderName'], [data-testid='cardholder-name']")
        
        # Card validation messages
        self.card_number_error = (By.CSS_SELECTOR, ".card-number-error, [data-testid='card-number-error']")
        self.expiry_error = (By.CSS_SELECTOR, ".expiry-error, [data-testid='expiry-error']")
        self.cvv_error = (By.CSS_SELECTOR, ".cvv-error, [data-testid='cvv-error']")
        self.cardholder_error = (By.CSS_SELECTOR, ".cardholder-error, [data-testid='cardholder-error']")
        
        # Digital Wallet Forms
        self.paypal_form = (By.CSS_SELECTOR, ".paypal-form, [data-testid='paypal-form']")
        self.paypal_email_input = (By.CSS_SELECTOR, "input[name='paypalEmail'], [data-testid='paypal-email']")
        self.paypal_login_btn = (By.CSS_SELECTOR, ".paypal-login, [data-testid='paypal-login']")
        
        self.google_pay_form = (By.CSS_SELECTOR, ".google-pay-form, [data-testid='google-pay-form']")
        self.google_pay_btn = (By.CSS_SELECTOR, ".google-pay-button, [data-testid='google-pay-button']")
        
        self.apple_pay_form = (By.CSS_SELECTOR, ".apple-pay-form, [data-testid='apple-pay-form']")
        self.apple_pay_btn = (By.CSS_SELECTOR, ".apple-pay-button, [data-testid='apple-pay-button']")
        
        # UPI Form
        self.upi_form = (By.CSS_SELECTOR, ".upi-form, [data-testid='upi-form']")
        self.upi_id_input = (By.CSS_SELECTOR, "input[name='upiId'], [data-testid='upi-id']")
        self.upi_app_select = (By.CSS_SELECTOR, "select[name='upiApp'], [data-testid='upi-app']")
        self.upi_verify_btn = (By.CSS_SELECTOR, ".upi-verify, [data-testid='upi-verify']")
        
        # EMI Form
        self.emi_form = (By.CSS_SELECTOR, ".emi-form, [data-testid='emi-form']")
        self.emi_tenure_select = (By.CSS_SELECTOR, "select[name='emiTenure'], [data-testid='emi-tenure']")
        self.emi_bank_select = (By.CSS_SELECTOR, "select[name='emiBank'], [data-testid='emi-bank']")
        self.emi_interest_rate = (By.CSS_SELECTOR, ".emi-interest-rate, [data-testid='emi-interest']")
        self.emi_monthly_amount = (By.CSS_SELECTOR, ".emi-monthly-amount, [data-testid='emi-monthly']")
        
        # COD Form
        self.cod_form = (By.CSS_SELECTOR, ".cod-form, [data-testid='cod-form']")
        self.cod_instructions = (By.CSS_SELECTOR, ".cod-instructions, [data-testid='cod-instructions']")
        self.cod_availability = (By.CSS_SELECTOR, ".cod-availability, [data-testid='cod-availability']")
        
        # Payment Security Elements
        self.ssl_indicator = (By.CSS_SELECTOR, ".ssl-secure, [data-testid='ssl-secure']")
        self.security_badges = (By.CSS_SELECTOR, ".security-badge, [data-testid='security-badge']")
        self.encryption_notice = (By.CSS_SELECTOR, ".encryption-notice, [data-testid='encryption-notice']")
        
        # Payment Processing
        self.process_payment_btn = (By.CSS_SELECTOR, ".process-payment, [data-testid='process-payment']")
        self.payment_processing_indicator = (By.CSS_SELECTOR, ".payment-processing, [data-testid='payment-processing']")
        self.payment_success_message = (By.CSS_SELECTOR, ".payment-success, [data-testid='payment-success']")
        self.payment_error_message = (By.CSS_SELECTOR, ".payment-error, [data-testid='payment-error']")
        
        # Payment Gateway Integration
        self.gateway_iframe = (By.CSS_SELECTOR, "iframe[name='payment-gateway'], [data-testid='payment-iframe']")
        self.gateway_redirect_form = (By.CSS_SELECTOR, ".gateway-redirect, [data-testid='gateway-redirect']")
        
        # Transaction Details
        self.transaction_id = (By.CSS_SELECTOR, ".transaction-id, [data-testid='transaction-id']")
        self.payment_reference = (By.CSS_SELECTOR, ".payment-reference, [data-testid='payment-reference']")
        self.payment_status = (By.CSS_SELECTOR, ".payment-status, [data-testid='payment-status']")
        
        # Retry and Failure Handling
        self.retry_payment_btn = (By.CSS_SELECTOR, ".retry-payment, [data-testid='retry-payment']")
        self.change_payment_method_btn = (By.CSS_SELECTOR, ".change-payment-method, [data-testid='change-payment-method']")
        self.payment_failure_details = (By.CSS_SELECTOR, ".payment-failure-details, [data-testid='failure-details']")
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/payment"
    
    @property
    def page_title(self) -> str:
        return "Payment Processing"
    
    @property
    def unique_element(self) -> Tuple[str, str]:
        return self.payment_methods_container
    
    def select_payment_method(self, payment_type: str) -> bool:
        """Select payment method"""
        try:
            payment_map = {
                "credit_card": self.credit_card_option,
                "debit_card": self.debit_card_option,
                "paypal": self.paypal_option,
                "google_pay": self.google_pay_option,
                "apple_pay": self.apple_pay_option,
                "upi": self.upi_option,
                "emi": self.emi_option,
                "cod": self.cod_option
            }
            
            if payment_type in payment_map:
                self.click_element(payment_map[payment_type])
                time.sleep(1)  # Wait for form to appear
                return True
            
            self.logger.error(f"Unknown payment type: {payment_type}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to select payment method: {str(e)}")
            return False
    
    def fill_credit_card_form(self, card_data: Dict[str, Any]) -> bool:
        """Fill credit card payment form"""
        try:
            if not self.is_element_visible(self.card_form):
                self.logger.error("Credit card form not visible")
                return False
            
            # Clear and fill card number
            self.clear_and_send_keys(self.card_number_input, card_data['card_number'])
            
            # Select expiry month and year
            if self.is_element_present(self.expiry_month_select):
                self.select_dropdown_by_value(self.expiry_month_select, str(card_data['expiry_month']))
            
            if self.is_element_present(self.expiry_year_select):
                self.select_dropdown_by_value(self.expiry_year_select, str(card_data['expiry_year']))
            
            # Fill CVV
            self.clear_and_send_keys(self.cvv_input, card_data['cvv'])
            
            # Fill cardholder name if present
            if 'cardholder_name' in card_data and self.is_element_present(self.cardholder_name_input):
                self.clear_and_send_keys(self.cardholder_name_input, card_data['cardholder_name'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill credit card form: {str(e)}")
            return False
    
    def fill_debit_card_form(self, card_data: Dict[str, Any]) -> bool:
        """Fill debit card payment form (same as credit card)"""
        return self.fill_credit_card_form(card_data)
    
    def fill_paypal_form(self, paypal_data: Dict[str, Any]) -> bool:
        """Fill PayPal payment form"""
        try:
            if not self.is_element_visible(self.paypal_form):
                self.logger.error("PayPal form not visible")
                return False
            
            if 'email' in paypal_data:
                self.clear_and_send_keys(self.paypal_email_input, paypal_data['email'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill PayPal form: {str(e)}")
            return False
    
    def fill_upi_form(self, upi_data: Dict[str, Any]) -> bool:
        """Fill UPI payment form"""
        try:
            if not self.is_element_visible(self.upi_form):
                self.logger.error("UPI form not visible")
                return False
            
            # Fill UPI ID
            self.clear_and_send_keys(self.upi_id_input, upi_data['upi_id'])
            
            # Select UPI app if provided
            if 'upi_app' in upi_data and self.is_element_present(self.upi_app_select):
                self.select_dropdown_by_text(self.upi_app_select, upi_data['upi_app'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill UPI form: {str(e)}")
            return False
    
    def configure_emi_options(self, emi_data: Dict[str, Any]) -> bool:
        """Configure EMI payment options"""
        try:
            if not self.is_element_visible(self.emi_form):
                self.logger.error("EMI form not visible")
                return False
            
            # Select EMI tenure
            if 'tenure' in emi_data:
                self.select_dropdown_by_value(self.emi_tenure_select, str(emi_data['tenure']))
                time.sleep(1)  # Wait for interest rate calculation
            
            # Select bank if provided
            if 'bank' in emi_data and self.is_element_present(self.emi_bank_select):
                self.select_dropdown_by_text(self.emi_bank_select, emi_data['bank'])
                time.sleep(1)  # Wait for rate update
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure EMI options: {str(e)}")
            return False
    
    def get_emi_details(self) -> Dict[str, str]:
        """Get EMI calculation details"""
        details = {}
        
        try:
            if self.is_element_present(self.emi_interest_rate):
                details['interest_rate'] = self.get_element_text(self.emi_interest_rate)
            
            if self.is_element_present(self.emi_monthly_amount):
                details['monthly_amount'] = self.get_element_text(self.emi_monthly_amount)
                
        except Exception as e:
            self.logger.error(f"Failed to get EMI details: {str(e)}")
        
        return details
    
    def verify_cod_availability(self) -> Dict[str, Any]:
        """Verify COD availability and get details"""
        result = {
            'available': False,
            'message': '',
            'instructions': ''
        }
        
        try:
            if self.is_element_visible(self.cod_form):
                result['available'] = True
                
                if self.is_element_present(self.cod_availability):
                    result['message'] = self.get_element_text(self.cod_availability)
                
                if self.is_element_present(self.cod_instructions):
                    result['instructions'] = self.get_element_text(self.cod_instructions)
                    
        except Exception as e:
            self.logger.error(f"Failed to verify COD availability: {str(e)}")
        
        return result
    
    def verify_payment_security_indicators(self) -> Dict[str, bool]:
        """Verify payment security indicators are present"""
        security_checks = {
            'ssl_indicator': False,
            'security_badges': False,
            'encryption_notice': False
        }
        
        try:
            security_checks['ssl_indicator'] = self.is_element_present(self.ssl_indicator)
            security_checks['security_badges'] = self.is_element_present(self.security_badges)
            security_checks['encryption_notice'] = self.is_element_present(self.encryption_notice)
            
        except Exception as e:
            self.logger.error(f"Failed to verify security indicators: {str(e)}")
        
        return security_checks
    
    def process_payment(self) -> bool:
        """Process the payment"""
        try:
            self.click_element(self.process_payment_btn)
            
            # Wait for processing indicator
            if self.wait_for_element(self.payment_processing_indicator, timeout=5):
                self.logger.info("Payment processing started")
            
            # Wait for completion (success or error)
            time.sleep(10)  # Allow time for payment processing
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process payment: {str(e)}")
            return False
    
    def get_payment_result(self) -> Dict[str, Any]:
        """Get payment processing result"""
        result = {
            'success': False,
            'transaction_id': '',
            'reference': '',
            'status': '',
            'error_message': ''
        }
        
        try:
            # Check for success
            if self.is_element_present(self.payment_success_message):
                result['success'] = True
                result['status'] = 'success'
                
                # Get transaction details
                if self.is_element_present(self.transaction_id):
                    result['transaction_id'] = self.get_element_text(self.transaction_id)
                
                if self.is_element_present(self.payment_reference):
                    result['reference'] = self.get_element_text(self.payment_reference)
            
            # Check for error
            elif self.is_element_present(self.payment_error_message):
                result['success'] = False
                result['status'] = 'failed'
                result['error_message'] = self.get_element_text(self.payment_error_message)
            
            # Check general status
            if self.is_element_present(self.payment_status):
                result['status'] = self.get_element_text(self.payment_status)
                
        except Exception as e:
            self.logger.error(f"Failed to get payment result: {str(e)}")
            result['error_message'] = str(e)
        
        return result
    
    def retry_payment(self) -> bool:
        """Retry failed payment"""
        try:
            if self.is_element_present(self.retry_payment_btn):
                self.click_element(self.retry_payment_btn)
                time.sleep(2)
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to retry payment: {str(e)}")
            return False
    
    def change_payment_method(self) -> bool:
        """Change payment method after failure"""
        try:
            if self.is_element_present(self.change_payment_method_btn):
                self.click_element(self.change_payment_method_btn)
                time.sleep(2)
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to change payment method: {str(e)}")
            return False
    
    def get_payment_failure_details(self) -> str:
        """Get detailed payment failure information"""
        try:
            if self.is_element_present(self.payment_failure_details):
                return self.get_element_text(self.payment_failure_details)
            return ""
            
        except Exception as e:
            self.logger.error(f"Failed to get failure details: {str(e)}")
            return ""
    
    def validate_card_number_format(self, card_number: str) -> bool:
        """Validate card number format in real-time"""
        try:
            # Fill card number
            self.clear_and_send_keys(self.card_number_input, card_number)
            
            # Trigger validation (click elsewhere or tab out)
            self.send_keys_to_element(self.card_number_input, "\t")
            time.sleep(1)
            
            # Check for validation error
            return not self.is_element_present(self.card_number_error)
            
        except Exception as e:
            self.logger.error(f"Failed to validate card number: {str(e)}")
            return False
    
    def validate_expiry_date(self, month: int, year: int) -> bool:
        """Validate expiry date"""
        try:
            # Select month and year
            self.select_dropdown_by_value(self.expiry_month_select, str(month))
            self.select_dropdown_by_value(self.expiry_year_select, str(year))
            
            # Trigger validation
            time.sleep(1)
            
            # Check for validation error
            return not self.is_element_present(self.expiry_error)
            
        except Exception as e:
            self.logger.error(f"Failed to validate expiry date: {str(e)}")
            return False
    
    def validate_cvv_format(self, cvv: str) -> bool:
        """Validate CVV format"""
        try:
            # Fill CVV
            self.clear_and_send_keys(self.cvv_input, cvv)
            
            # Trigger validation
            self.send_keys_to_element(self.cvv_input, "\t")
            time.sleep(1)
            
            # Check for validation error
            return not self.is_element_present(self.cvv_error)
            
        except Exception as e:
            self.logger.error(f"Failed to validate CVV: {str(e)}")
            return False
    
    def handle_gateway_redirect(self) -> bool:
        """Handle payment gateway redirect"""
        try:
            # Check for iframe
            if self.is_element_present(self.gateway_iframe):
                self.logger.info("Payment gateway iframe detected")
                # Switch to iframe if needed
                iframe = self.find_element(self.gateway_iframe)
                self.driver.switch_to.frame(iframe)
                
                # Perform gateway-specific actions here
                # This would be customized based on the actual gateway
                
                # Switch back to main content
                self.driver.switch_to.default_content()
                return True
            
            # Check for redirect form
            elif self.is_element_present(self.gateway_redirect_form):
                self.logger.info("Payment gateway redirect form detected")
                # Handle redirect form submission
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to handle gateway redirect: {str(e)}")
            return False
    
    def verify_upi_id_format(self, upi_id: str) -> bool:
        """Verify UPI ID format validation"""
        try:
            # Fill UPI ID
            self.clear_and_send_keys(self.upi_id_input, upi_id)
            
            # Trigger validation
            if self.is_element_present(self.upi_verify_btn):
                self.click_element(self.upi_verify_btn)
                time.sleep(2)
            
            # Check for validation success (no error message)
            return not self.has_validation_errors()
            
        except Exception as e:
            self.logger.error(f"Failed to verify UPI ID: {str(e)}")
            return False
    
    def has_validation_errors(self) -> bool:
        """Check if any validation errors are present"""
        error_selectors = [
            self.card_number_error,
            self.expiry_error,
            self.cvv_error,
            self.cardholder_error
        ]
        
        for selector in error_selectors:
            if self.is_element_present(selector):
                return True
        
        return False
    
    def get_validation_errors(self) -> List[str]:
        """Get all validation error messages"""
        errors = []
        
        error_selectors = [
            self.card_number_error,
            self.expiry_error,
            self.cvv_error,
            self.cardholder_error
        ]
        
        for selector in error_selectors:
            if self.is_element_present(selector):
                error_text = self.get_element_text(selector)
                if error_text:
                    errors.append(error_text)
        
        return errors


class RefundPage(BasePage):
    """Refund processing page object"""
    
    def __init__(self, driver: WebDriver, webdriver_manager: WebDriverManager, base_url: str):
        super().__init__(driver, webdriver_manager)
        self.base_url = base_url
        
        # Refund form elements
        self.refund_form = (By.CSS_SELECTOR, ".refund-form, [data-testid='refund-form']")
        self.order_number_input = (By.CSS_SELECTOR, "input[name='orderNumber'], [data-testid='order-number']")
        self.refund_amount_input = (By.CSS_SELECTOR, "input[name='refundAmount'], [data-testid='refund-amount']")
        self.refund_reason_select = (By.CSS_SELECTOR, "select[name='refundReason'], [data-testid='refund-reason']")
        self.refund_method_select = (By.CSS_SELECTOR, "select[name='refundMethod'], [data-testid='refund-method']")
        
        # Partial refund elements
        self.partial_refund_option = (By.CSS_SELECTOR, "input[name='partialRefund'], [data-testid='partial-refund']")
        self.refund_items_list = (By.CSS_SELECTOR, ".refund-items, [data-testid='refund-items']")
        self.item_refund_checkbox = (By.CSS_SELECTOR, ".item-refund-checkbox, [data-testid='item-checkbox']")
        
        # Refund processing
        self.process_refund_btn = (By.CSS_SELECTOR, ".process-refund, [data-testid='process-refund']")
        self.refund_confirmation = (By.CSS_SELECTOR, ".refund-confirmation, [data-testid='refund-confirmation']")
        self.refund_reference = (By.CSS_SELECTOR, ".refund-reference, [data-testid='refund-reference']")
        self.refund_status = (By.CSS_SELECTOR, ".refund-status, [data-testid='refund-status']")
    
    @property
    def page_url(self) -> str:
        return f"{self.base_url}/refund"
    
    @property
    def page_title(self) -> str:
        return "Process Refund"
    
    @property
    def unique_element(self) -> Tuple[str, str]:
        return self.refund_form
    
    def process_full_refund(self, order_number: str, reason: str = "Customer Request") -> Dict[str, Any]:
        """Process full order refund"""
        result = {
            'success': False,
            'refund_reference': '',
            'status': '',
            'error': ''
        }
        
        try:
            # Fill order number
            self.clear_and_send_keys(self.order_number_input, order_number)
            
            # Select refund reason
            self.select_dropdown_by_text(self.refund_reason_select, reason)
            
            # Process refund
            self.click_element(self.process_refund_btn)
            time.sleep(5)  # Wait for processing
            
            # Check result
            if self.is_element_present(self.refund_confirmation):
                result['success'] = True
                
                if self.is_element_present(self.refund_reference):
                    result['refund_reference'] = self.get_element_text(self.refund_reference)
                
                if self.is_element_present(self.refund_status):
                    result['status'] = self.get_element_text(self.refund_status)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def process_partial_refund(self, order_number: str, refund_amount: float, 
                              reason: str = "Partial Return") -> Dict[str, Any]:
        """Process partial refund"""
        result = {
            'success': False,
            'refund_reference': '',
            'status': '',
            'error': ''
        }
        
        try:
            # Fill order number
            self.clear_and_send_keys(self.order_number_input, order_number)
            
            # Select partial refund option
            self.click_element(self.partial_refund_option)
            
            # Enter refund amount
            self.clear_and_send_keys(self.refund_amount_input, str(refund_amount))
            
            # Select reason
            self.select_dropdown_by_text(self.refund_reason_select, reason)
            
            # Process refund
            self.click_element(self.process_refund_btn)
            time.sleep(5)
            
            # Check result
            if self.is_element_present(self.refund_confirmation):
                result['success'] = True
                
                if self.is_element_present(self.refund_reference):
                    result['refund_reference'] = self.get_element_text(self.refund_reference)
                
                if self.is_element_present(self.refund_status):
                    result['status'] = self.get_element_text(self.refund_status)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result