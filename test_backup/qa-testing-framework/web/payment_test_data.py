"""
Test Data for Payment Processing Tests

Provides test data for payment methods, sandbox configurations,
failure scenarios, refund testing, and security validation.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
import string

try:
    from ..core.models import PaymentMethod
    from ..core.interfaces import UserRole
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.models import PaymentMethod
    from core.interfaces import UserRole


class PaymentTestDataGenerator:
    """Generates test data for payment processing scenarios"""
    
    def __init__(self):
        self.sandbox_cards = self._generate_sandbox_cards()
        self.digital_wallets = self._generate_digital_wallet_data()
        self.upi_data = self._generate_upi_data()
        self.emi_options = self._generate_emi_options()
        self.failure_scenarios = self._generate_failure_scenarios()
        self.refund_scenarios = self._generate_refund_scenarios()
    
    def _generate_sandbox_cards(self) -> List[Dict[str, Any]]:
        """Generate sandbox credit/debit card test data"""
        return [
            # Valid Test Cards
            {
                'type': 'credit_card',
                'brand': 'visa',
                'card_number': '4111111111111111',
                'expiry_month': 12,
                'expiry_year': 2025,
                'cvv': '123',
                'cardholder_name': 'Test User',
                'expected_result': 'success',
                'description': 'Valid Visa test card'
            },
            {
                'type': 'credit_card',
                'brand': 'mastercard',
                'card_number': '5555555555554444',
                'expiry_month': 6,
                'expiry_year': 2026,
                'cvv': '456',
                'cardholder_name': 'Test User',
                'expected_result': 'success',
                'description': 'Valid Mastercard test card'
            },
            {
                'type': 'credit_card',
                'brand': 'amex',
                'card_number': '378282246310005',
                'expiry_month': 3,
                'expiry_year': 2027,
                'cvv': '7890',
                'cardholder_name': 'Test User',
                'expected_result': 'success',
                'description': 'Valid American Express test card'
            },
            {
                'type': 'debit_card',
                'brand': 'visa',
                'card_number': '4000056655665556',
                'expiry_month': 9,
                'expiry_year': 2025,
                'cvv': '789',
                'cardholder_name': 'Test User',
                'expected_result': 'success',
                'description': 'Valid Visa debit test card'
            },
            # Declined Cards
            {
                'type': 'credit_card',
                'brand': 'visa',
                'card_number': '4000000000000002',
                'expiry_month': 12,
                'expiry_year': 2025,
                'cvv': '123',
                'cardholder_name': 'Test User',
                'expected_result': 'declined',
                'description': 'Visa card that will be declined'
            },
            {
                'type': 'credit_card',
                'brand': 'mastercard',
                'card_number': '5200828282828210',
                'expiry_month': 6,
                'expiry_year': 2026,
                'cvv': '456',
                'cardholder_name': 'Test User',
                'expected_result': 'declined',
                'description': 'Mastercard that will be declined'
            },
            # Insufficient Funds
            {
                'type': 'credit_card',
                'brand': 'visa',
                'card_number': '4000000000009995',
                'expiry_month': 12,
                'expiry_year': 2025,
                'cvv': '123',
                'cardholder_name': 'Test User',
                'expected_result': 'insufficient_funds',
                'description': 'Card with insufficient funds'
            },
            # Processing Error
            {
                'type': 'credit_card',
                'brand': 'visa',
                'card_number': '4000000000000119',
                'expiry_month': 12,
                'expiry_year': 2025,
                'cvv': '123',
                'cardholder_name': 'Test User',
                'expected_result': 'processing_error',
                'description': 'Card that causes processing error'
            }
        ]
    
    def _generate_digital_wallet_data(self) -> List[Dict[str, Any]]:
        """Generate digital wallet test data"""
        return [
            {
                'type': 'paypal',
                'email': 'test@paypal.com',
                'password': 'testpassword123',
                'expected_result': 'success',
                'description': 'Valid PayPal sandbox account'
            },
            {
                'type': 'paypal',
                'email': 'declined@paypal.com',
                'password': 'testpassword123',
                'expected_result': 'declined',
                'description': 'PayPal account that will be declined'
            },
            {
                'type': 'google_pay',
                'account': 'test@gmail.com',
                'expected_result': 'success',
                'description': 'Valid Google Pay test account'
            },
            {
                'type': 'apple_pay',
                'device_id': 'test_device_123',
                'expected_result': 'success',
                'description': 'Valid Apple Pay test configuration'
            }
        ]
    
    def _generate_upi_data(self) -> List[Dict[str, Any]]:
        """Generate UPI test data"""
        return [
            {
                'type': 'upi',
                'upi_id': 'testuser@paytm',
                'upi_app': 'Paytm',
                'expected_result': 'success',
                'description': 'Valid UPI ID for Paytm'
            },
            {
                'type': 'upi',
                'upi_id': 'testuser@googlepay',
                'upi_app': 'Google Pay',
                'expected_result': 'success',
                'description': 'Valid UPI ID for Google Pay'
            },
            {
                'type': 'upi',
                'upi_id': 'testuser@phonepe',
                'upi_app': 'PhonePe',
                'expected_result': 'success',
                'description': 'Valid UPI ID for PhonePe'
            },
            {
                'type': 'upi',
                'upi_id': 'invalid@upi',
                'upi_app': 'Unknown',
                'expected_result': 'invalid',
                'description': 'Invalid UPI ID format'
            }
        ]
    
    def _generate_emi_options(self) -> List[Dict[str, Any]]:
        """Generate EMI test data"""
        return [
            {
                'type': 'emi',
                'tenure': 3,
                'bank': 'HDFC Bank',
                'interest_rate': 12.0,
                'processing_fee': 99.0,
                'expected_result': 'success',
                'description': '3-month EMI with HDFC Bank'
            },
            {
                'type': 'emi',
                'tenure': 6,
                'bank': 'ICICI Bank',
                'interest_rate': 13.5,
                'processing_fee': 149.0,
                'expected_result': 'success',
                'description': '6-month EMI with ICICI Bank'
            },
            {
                'type': 'emi',
                'tenure': 12,
                'bank': 'SBI',
                'interest_rate': 14.0,
                'processing_fee': 199.0,
                'expected_result': 'success',
                'description': '12-month EMI with SBI'
            },
            {
                'type': 'emi',
                'tenure': 24,
                'bank': 'Axis Bank',
                'interest_rate': 15.5,
                'processing_fee': 299.0,
                'expected_result': 'success',
                'description': '24-month EMI with Axis Bank'
            }
        ]
    
    def _generate_failure_scenarios(self) -> List[Dict[str, Any]]:
        """Generate payment failure test scenarios"""
        return [
            {
                'scenario': 'invalid_card_number',
                'payment_data': {
                    'type': 'credit_card',
                    'card_number': '1234567890123456',
                    'expiry_month': 12,
                    'expiry_year': 2025,
                    'cvv': '123',
                    'cardholder_name': 'Test User'
                },
                'expected_error': 'Invalid card number',
                'description': 'Invalid card number format'
            },
            {
                'scenario': 'expired_card',
                'payment_data': {
                    'type': 'credit_card',
                    'card_number': '4111111111111111',
                    'expiry_month': 12,
                    'expiry_year': 2020,
                    'cvv': '123',
                    'cardholder_name': 'Test User'
                },
                'expected_error': 'Card has expired',
                'description': 'Expired credit card'
            },
            {
                'scenario': 'invalid_cvv',
                'payment_data': {
                    'type': 'credit_card',
                    'card_number': '4111111111111111',
                    'expiry_month': 12,
                    'expiry_year': 2025,
                    'cvv': '12',
                    'cardholder_name': 'Test User'
                },
                'expected_error': 'Invalid CVV',
                'description': 'Invalid CVV format'
            },
            {
                'scenario': 'empty_cardholder_name',
                'payment_data': {
                    'type': 'credit_card',
                    'card_number': '4111111111111111',
                    'expiry_month': 12,
                    'expiry_year': 2025,
                    'cvv': '123',
                    'cardholder_name': ''
                },
                'expected_error': 'Cardholder name is required',
                'description': 'Empty cardholder name'
            },
            {
                'scenario': 'invalid_upi_id',
                'payment_data': {
                    'type': 'upi',
                    'upi_id': 'invalid-upi-format'
                },
                'expected_error': 'Invalid UPI ID format',
                'description': 'Invalid UPI ID format'
            },
            {
                'scenario': 'network_timeout',
                'payment_data': {
                    'type': 'credit_card',
                    'card_number': '4111111111111111',
                    'expiry_month': 12,
                    'expiry_year': 2025,
                    'cvv': '123',
                    'cardholder_name': 'Test User'
                },
                'expected_error': 'Network timeout',
                'description': 'Network timeout during processing',
                'simulate_timeout': True
            }
        ]
    
    def _generate_refund_scenarios(self) -> List[Dict[str, Any]]:
        """Generate refund test scenarios"""
        return [
            {
                'type': 'full_refund',
                'order_amount': 100.00,
                'refund_amount': 100.00,
                'reason': 'Customer Request',
                'expected_result': 'success',
                'description': 'Full order refund'
            },
            {
                'type': 'partial_refund',
                'order_amount': 150.00,
                'refund_amount': 75.00,
                'reason': 'Partial Return',
                'expected_result': 'success',
                'description': 'Partial order refund'
            },
            {
                'type': 'multiple_partial_refunds',
                'order_amount': 200.00,
                'refund_amounts': [50.00, 30.00, 25.00],
                'reasons': ['Item 1 Return', 'Item 2 Return', 'Shipping Refund'],
                'expected_result': 'success',
                'description': 'Multiple partial refunds for same order'
            },
            {
                'type': 'refund_exceeds_order',
                'order_amount': 100.00,
                'refund_amount': 150.00,
                'reason': 'Invalid Refund',
                'expected_result': 'error',
                'expected_error': 'Refund amount exceeds order total',
                'description': 'Refund amount exceeds original order'
            }
        ]
    
    def get_payment_method_data(self, payment_type: str, scenario: str = "success") -> Dict[str, Any]:
        """Get payment method test data"""
        
        if payment_type == "credit_card" or payment_type == "debit_card":
            cards = [card for card in self.sandbox_cards 
                    if card['type'] == payment_type and card['expected_result'] == scenario]
            return random.choice(cards) if cards else {}
        
        elif payment_type == "paypal":
            wallets = [wallet for wallet in self.digital_wallets 
                      if wallet['type'] == 'paypal' and wallet['expected_result'] == scenario]
            return random.choice(wallets) if wallets else {}
        
        elif payment_type == "google_pay":
            wallets = [wallet for wallet in self.digital_wallets 
                      if wallet['type'] == 'google_pay' and wallet['expected_result'] == scenario]
            return random.choice(wallets) if wallets else {}
        
        elif payment_type == "apple_pay":
            wallets = [wallet for wallet in self.digital_wallets 
                      if wallet['type'] == 'apple_pay' and wallet['expected_result'] == scenario]
            return random.choice(wallets) if wallets else {}
        
        elif payment_type == "upi":
            upi_options = [upi for upi in self.upi_data 
                          if upi['expected_result'] == scenario]
            return random.choice(upi_options) if upi_options else {}
        
        elif payment_type == "emi":
            return random.choice(self.emi_options)
        
        elif payment_type == "cod":
            return {
                'type': 'cod',
                'expected_result': 'success',
                'description': 'Cash on Delivery'
            }
        
        return {}
    
    def get_failure_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Get specific failure scenario data"""
        for scenario in self.failure_scenarios:
            if scenario['scenario'] == scenario_name:
                return scenario.copy()
        return {}
    
    def get_all_failure_scenarios(self) -> List[Dict[str, Any]]:
        """Get all failure scenarios for comprehensive testing"""
        return self.failure_scenarios.copy()
    
    def get_refund_scenario(self, refund_type: str) -> Dict[str, Any]:
        """Get refund scenario data"""
        for scenario in self.refund_scenarios:
            if scenario['type'] == refund_type:
                return scenario.copy()
        return {}
    
    def create_payment_test_scenario(self, scenario_type: str) -> Dict[str, Any]:
        """Create complete payment test scenario"""
        
        if scenario_type == "successful_credit_card":
            return {
                'payment_method': self.get_payment_method_data('credit_card', 'success'),
                'order_amount': 99.99,
                'expected_result': 'success',
                'description': 'Successful credit card payment'
            }
        
        elif scenario_type == "successful_paypal":
            return {
                'payment_method': self.get_payment_method_data('paypal', 'success'),
                'order_amount': 149.99,
                'expected_result': 'success',
                'description': 'Successful PayPal payment'
            }
        
        elif scenario_type == "successful_upi":
            return {
                'payment_method': self.get_payment_method_data('upi', 'success'),
                'order_amount': 75.50,
                'expected_result': 'success',
                'description': 'Successful UPI payment'
            }
        
        elif scenario_type == "successful_emi":
            return {
                'payment_method': self.get_payment_method_data('emi', 'success'),
                'order_amount': 1299.99,
                'expected_result': 'success',
                'description': 'Successful EMI payment'
            }
        
        elif scenario_type == "successful_cod":
            return {
                'payment_method': self.get_payment_method_data('cod', 'success'),
                'order_amount': 199.99,
                'expected_result': 'success',
                'description': 'Successful COD order'
            }
        
        elif scenario_type == "declined_card":
            return {
                'payment_method': self.get_payment_method_data('credit_card', 'declined'),
                'order_amount': 99.99,
                'expected_result': 'declined',
                'description': 'Declined credit card payment'
            }
        
        elif scenario_type == "insufficient_funds":
            return {
                'payment_method': self.get_payment_method_data('credit_card', 'insufficient_funds'),
                'order_amount': 999.99,
                'expected_result': 'insufficient_funds',
                'description': 'Insufficient funds scenario'
            }
        
        elif scenario_type == "high_value_order":
            return {
                'payment_method': self.get_payment_method_data('credit_card', 'success'),
                'order_amount': 5000.00,
                'expected_result': 'success',
                'description': 'High value order payment'
            }
        
        elif scenario_type == "international_card":
            card_data = self.get_payment_method_data('credit_card', 'success')
            card_data['international'] = True
            card_data['currency'] = 'USD'
            return {
                'payment_method': card_data,
                'order_amount': 299.99,
                'expected_result': 'success',
                'description': 'International card payment'
            }
        
        else:
            # Default scenario
            return self.create_payment_test_scenario("successful_credit_card")
    
    def get_security_test_data(self) -> Dict[str, Any]:
        """Get security testing data"""
        return {
            'sql_injection_attempts': [
                "'; DROP TABLE payments; --",
                "1' OR '1'='1",
                "admin'/*",
                "' UNION SELECT * FROM users --"
            ],
            'xss_attempts': [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//\";alert(String.fromCharCode(88,83,83))//\";alert(String.fromCharCode(88,83,83))//--></SCRIPT>\">'><SCRIPT>alert(String.fromCharCode(88,83,83))</SCRIPT>"
            ],
            'csrf_test_scenarios': [
                {
                    'description': 'Missing CSRF token',
                    'remove_csrf_token': True
                },
                {
                    'description': 'Invalid CSRF token',
                    'invalid_csrf_token': 'invalid_token_123'
                }
            ],
            'rate_limiting_test': {
                'max_attempts': 10,
                'time_window': 60,  # seconds
                'description': 'Test payment rate limiting'
            }
        }
    
    def calculate_emi_details(self, principal: float, tenure: int, interest_rate: float, 
                             processing_fee: float = 0) -> Dict[str, float]:
        """Calculate EMI details for validation"""
        
        # Monthly interest rate
        monthly_rate = interest_rate / (12 * 100)
        
        # EMI calculation using formula: P * r * (1+r)^n / ((1+r)^n - 1)
        if monthly_rate > 0:
            emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure) / (((1 + monthly_rate) ** tenure) - 1)
        else:
            emi = principal / tenure
        
        total_amount = (emi * tenure) + processing_fee
        total_interest = total_amount - principal - processing_fee
        
        return {
            'monthly_emi': round(emi, 2),
            'total_amount': round(total_amount, 2),
            'total_interest': round(total_interest, 2),
            'processing_fee': processing_fee,
            'principal': principal,
            'tenure': tenure,
            'interest_rate': interest_rate
        }
    
    def get_payment_gateway_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get payment gateway sandbox configurations"""
        return {
            'stripe': {
                'public_key': 'pk_test_123456789',
                'secret_key': 'sk_test_123456789',
                'webhook_secret': 'whsec_test_123456789',
                'base_url': 'https://api.stripe.com/v1',
                'test_mode': True
            },
            'razorpay': {
                'key_id': 'rzp_test_123456789',
                'key_secret': 'test_secret_123456789',
                'webhook_secret': 'webhook_secret_123456789',
                'base_url': 'https://api.razorpay.com/v1',
                'test_mode': True
            },
            'paypal': {
                'client_id': 'test_client_id_123456789',
                'client_secret': 'test_client_secret_123456789',
                'base_url': 'https://api.sandbox.paypal.com',
                'test_mode': True
            },
            'payu': {
                'merchant_key': 'test_merchant_key',
                'merchant_salt': 'test_merchant_salt',
                'base_url': 'https://test.payu.in',
                'test_mode': True
            }
        }


# Global instance for easy access
payment_test_data = PaymentTestDataGenerator()