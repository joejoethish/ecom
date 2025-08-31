"""
Test Data for Shopping Cart and Checkout Tests

Provides test data for cart operations, checkout scenarios,
address information, payment methods, and coupon codes.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
import string

from ..core.models import Address, PaymentMethod, TestUser
from ..core.interfaces import UserRole


class CartTestDataGenerator:
    """Generates test data for cart and checkout scenarios"""
    
    def __init__(self):
        self.test_products = self._generate_test_products()
        self.test_addresses = self._generate_test_addresses()
        self.test_payment_methods = self._generate_test_payment_methods()
        self.test_coupons = self._generate_test_coupons()
    
    def _generate_test_products(self) -> List[Dict[str, Any]]:
        """Generate test product data for cart operations"""
        return [
            {
                'id': 'PROD_001',
                'name': 'Wireless Bluetooth Headphones',
                'price': 99.99,
                'category': 'Electronics',
                'stock': 50,
                'sku': 'WBH-001'
            },
            {
                'id': 'PROD_002',
                'name': 'Cotton T-Shirt',
                'price': 24.99,
                'category': 'Clothing',
                'stock': 100,
                'sku': 'CTS-002'
            },
            {
                'id': 'PROD_003',
                'name': 'Coffee Maker',
                'price': 149.99,
                'category': 'Home & Kitchen',
                'stock': 25,
                'sku': 'CM-003'
            },
            {
                'id': 'PROD_004',
                'name': 'Running Shoes',
                'price': 79.99,
                'category': 'Sports',
                'stock': 75,
                'sku': 'RS-004'
            },
            {
                'id': 'PROD_005',
                'name': 'Smartphone Case',
                'price': 19.99,
                'category': 'Electronics',
                'stock': 200,
                'sku': 'SC-005'
            }
        ]
    
    def _generate_test_addresses(self) -> List[Dict[str, Any]]:
        """Generate test address data"""
        return [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'phone': '+1-555-0123',
                'street': '123 Main Street',
                'address_line2': 'Apt 4B',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'United States'
            },
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@example.com',
                'phone': '+1-555-0456',
                'street': '456 Oak Avenue',
                'city': 'Los Angeles',
                'state': 'CA',
                'postal_code': '90210',
                'country': 'United States'
            },
            {
                'first_name': 'Bob',
                'last_name': 'Johnson',
                'email': 'bob.johnson@example.com',
                'phone': '+1-555-0789',
                'street': '789 Pine Road',
                'city': 'Chicago',
                'state': 'IL',
                'postal_code': '60601',
                'country': 'United States'
            },
            {
                'first_name': 'Alice',
                'last_name': 'Brown',
                'email': 'alice.brown@example.com',
                'phone': '+1-555-0321',
                'street': '321 Elm Street',
                'city': 'Houston',
                'state': 'TX',
                'postal_code': '77001',
                'country': 'United States'
            }
        ]
    
    def _generate_test_payment_methods(self) -> List[Dict[str, Any]]:
        """Generate test payment method data"""
        return [
            {
                'type': 'credit_card',
                'card_number': '4111111111111111',  # Test Visa card
                'expiry_month': 12,
                'expiry_year': 2025,
                'cvv': '123',
                'cardholder_name': 'John Doe'
            },
            {
                'type': 'credit_card',
                'card_number': '5555555555554444',  # Test Mastercard
                'expiry_month': 6,
                'expiry_year': 2026,
                'cvv': '456',
                'cardholder_name': 'Jane Smith'
            },
            {
                'type': 'credit_card',
                'card_number': '378282246310005',  # Test Amex
                'expiry_month': 3,
                'expiry_year': 2027,
                'cvv': '7890',
                'cardholder_name': 'Bob Johnson'
            },
            {
                'type': 'paypal',
                'email': 'test@paypal.com'
            },
            {
                'type': 'cod'  # Cash on Delivery
            }
        ]
    
    def _generate_test_coupons(self) -> List[Dict[str, Any]]:
        """Generate test coupon codes"""
        return [
            {
                'code': 'SAVE10',
                'type': 'percentage',
                'value': 10,
                'minimum_order': 50.00,
                'valid': True,
                'description': '10% off orders over $50'
            },
            {
                'code': 'FLAT20',
                'type': 'fixed',
                'value': 20.00,
                'minimum_order': 100.00,
                'valid': True,
                'description': '$20 off orders over $100'
            },
            {
                'code': 'FREESHIP',
                'type': 'free_shipping',
                'value': 0,
                'minimum_order': 75.00,
                'valid': True,
                'description': 'Free shipping on orders over $75'
            },
            {
                'code': 'EXPIRED',
                'type': 'percentage',
                'value': 15,
                'minimum_order': 0,
                'valid': False,
                'description': 'Expired 15% off coupon'
            },
            {
                'code': 'INVALID',
                'type': 'percentage',
                'value': 25,
                'minimum_order': 0,
                'valid': False,
                'description': 'Invalid coupon code'
            }
        ]
    
    def get_test_product(self, product_id: str = None) -> Dict[str, Any]:
        """Get specific test product or random one"""
        if product_id:
            for product in self.test_products:
                if product['id'] == product_id:
                    return product.copy()
        
        return random.choice(self.test_products).copy()
    
    def get_multiple_test_products(self, count: int = 3) -> List[Dict[str, Any]]:
        """Get multiple test products for cart scenarios"""
        return random.sample(self.test_products, min(count, len(self.test_products)))
    
    def get_test_address(self, address_type: str = "shipping") -> Dict[str, Any]:
        """Get test address data"""
        address = random.choice(self.test_addresses).copy()
        address['address_type'] = address_type
        return address
    
    def get_test_payment_method(self, payment_type: str = None) -> Dict[str, Any]:
        """Get test payment method"""
        if payment_type:
            for method in self.test_payment_methods:
                if method['type'] == payment_type:
                    return method.copy()
        
        return random.choice(self.test_payment_methods).copy()
    
    def get_test_coupon(self, coupon_type: str = "valid") -> Dict[str, Any]:
        """Get test coupon code"""
        valid_coupons = [c for c in self.test_coupons if c['valid']]
        invalid_coupons = [c for c in self.test_coupons if not c['valid']]
        
        if coupon_type == "valid":
            return random.choice(valid_coupons).copy()
        elif coupon_type == "invalid":
            return random.choice(invalid_coupons).copy()
        else:
            return random.choice(self.test_coupons).copy()
    
    def create_cart_scenario_data(self, scenario_type: str) -> Dict[str, Any]:
        """Create complete test data for specific cart scenarios"""
        
        if scenario_type == "single_item":
            return {
                'products': [self.get_test_product()],
                'quantities': [1],
                'address': self.get_test_address(),
                'payment': self.get_test_payment_method('credit_card'),
                'shipping': 'standard',
                'coupon': None
            }
        
        elif scenario_type == "multiple_items":
            products = self.get_multiple_test_products(3)
            return {
                'products': products,
                'quantities': [random.randint(1, 3) for _ in products],
                'address': self.get_test_address(),
                'payment': self.get_test_payment_method('credit_card'),
                'shipping': 'standard',
                'coupon': None
            }
        
        elif scenario_type == "with_coupon":
            products = self.get_multiple_test_products(2)
            return {
                'products': products,
                'quantities': [2, 1],
                'address': self.get_test_address(),
                'payment': self.get_test_payment_method('credit_card'),
                'shipping': 'standard',
                'coupon': self.get_test_coupon('valid')
            }
        
        elif scenario_type == "express_shipping":
            return {
                'products': [self.get_test_product()],
                'quantities': [1],
                'address': self.get_test_address(),
                'payment': self.get_test_payment_method('credit_card'),
                'shipping': 'express',
                'coupon': None
            }
        
        elif scenario_type == "paypal_payment":
            return {
                'products': [self.get_test_product()],
                'quantities': [1],
                'address': self.get_test_address(),
                'payment': self.get_test_payment_method('paypal'),
                'shipping': 'standard',
                'coupon': None
            }
        
        elif scenario_type == "cod_payment":
            return {
                'products': [self.get_test_product()],
                'quantities': [1],
                'address': self.get_test_address(),
                'payment': self.get_test_payment_method('cod'),
                'shipping': 'standard',
                'coupon': None
            }
        
        elif scenario_type == "high_value_order":
            # Create high-value order for testing tax calculations
            expensive_products = [
                {
                    'id': 'PROD_EXPENSIVE_1',
                    'name': 'Premium Laptop',
                    'price': 1299.99,
                    'category': 'Electronics',
                    'stock': 10,
                    'sku': 'PL-001'
                },
                {
                    'id': 'PROD_EXPENSIVE_2',
                    'name': 'Designer Watch',
                    'price': 899.99,
                    'category': 'Accessories',
                    'stock': 5,
                    'sku': 'DW-002'
                }
            ]
            return {
                'products': expensive_products,
                'quantities': [1, 1],
                'address': self.get_test_address(),
                'payment': self.get_test_payment_method('credit_card'),
                'shipping': 'overnight',
                'coupon': self.get_test_coupon('valid')
            }
        
        else:
            # Default scenario
            return self.create_cart_scenario_data("single_item")
    
    def create_guest_user_data(self) -> Dict[str, Any]:
        """Create guest user data for checkout"""
        address = self.get_test_address()
        return {
            'first_name': address['first_name'],
            'last_name': address['last_name'],
            'email': address['email'],
            'phone': address['phone'],
            'is_guest': True
        }
    
    def create_registered_user_data(self) -> Dict[str, Any]:
        """Create registered user data with saved addresses and payment methods"""
        timestamp = int(datetime.now().timestamp())
        
        return {
            'id': f'USER_{timestamp}',
            'email': f'testuser_{timestamp}@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+1-555-0999',
            'addresses': [
                Address(
                    street='123 Test Street',
                    city='Test City',
                    state='Test State',
                    postal_code='12345',
                    country='United States',
                    address_type='shipping'
                ),
                Address(
                    street='456 Billing Avenue',
                    city='Billing City',
                    state='Billing State',
                    postal_code='67890',
                    country='United States',
                    address_type='billing'
                )
            ],
            'payment_methods': [
                PaymentMethod(
                    type='credit_card',
                    details={
                        'card_number': '4111111111111111',
                        'expiry_month': 12,
                        'expiry_year': 2025,
                        'cvv': '123',
                        'cardholder_name': 'Test User'
                    },
                    is_default=True
                )
            ]
        }
    
    def get_invalid_payment_data(self) -> List[Dict[str, Any]]:
        """Get invalid payment data for negative testing"""
        return [
            {
                'type': 'credit_card',
                'card_number': '1234567890123456',  # Invalid card number
                'expiry_month': 12,
                'expiry_year': 2025,
                'cvv': '123',
                'cardholder_name': 'Test User',
                'error_type': 'invalid_card_number'
            },
            {
                'type': 'credit_card',
                'card_number': '4111111111111111',
                'expiry_month': 13,  # Invalid month
                'expiry_year': 2025,
                'cvv': '123',
                'cardholder_name': 'Test User',
                'error_type': 'invalid_expiry_month'
            },
            {
                'type': 'credit_card',
                'card_number': '4111111111111111',
                'expiry_month': 12,
                'expiry_year': 2020,  # Expired year
                'cvv': '123',
                'cardholder_name': 'Test User',
                'error_type': 'expired_card'
            },
            {
                'type': 'credit_card',
                'card_number': '4111111111111111',
                'expiry_month': 12,
                'expiry_year': 2025,
                'cvv': '12',  # Invalid CVV
                'cardholder_name': 'Test User',
                'error_type': 'invalid_cvv'
            },
            {
                'type': 'credit_card',
                'card_number': '4111111111111111',
                'expiry_month': 12,
                'expiry_year': 2025,
                'cvv': '123',
                'cardholder_name': '',  # Empty cardholder name
                'error_type': 'empty_cardholder_name'
            }
        ]
    
    def get_invalid_address_data(self) -> List[Dict[str, Any]]:
        """Get invalid address data for negative testing"""
        base_address = self.get_test_address()
        
        return [
            {
                **base_address,
                'street': '',  # Empty street
                'error_type': 'empty_street'
            },
            {
                **base_address,
                'city': '',  # Empty city
                'error_type': 'empty_city'
            },
            {
                **base_address,
                'postal_code': '123',  # Invalid postal code
                'error_type': 'invalid_postal_code'
            },
            {
                **base_address,
                'email': 'invalid-email',  # Invalid email format
                'error_type': 'invalid_email'
            },
            {
                **base_address,
                'phone': '123',  # Invalid phone number
                'error_type': 'invalid_phone'
            }
        ]
    
    def calculate_expected_totals(self, products: List[Dict[str, Any]], quantities: List[int], 
                                 shipping_cost: float = 9.99, tax_rate: float = 0.08, 
                                 coupon: Dict[str, Any] = None) -> Dict[str, float]:
        """Calculate expected order totals for validation"""
        
        # Calculate subtotal
        subtotal = sum(product['price'] * qty for product, qty in zip(products, quantities))
        
        # Apply coupon discount
        discount = 0.0
        if coupon and coupon.get('valid', False):
            if subtotal >= coupon.get('minimum_order', 0):
                if coupon['type'] == 'percentage':
                    discount = subtotal * (coupon['value'] / 100)
                elif coupon['type'] == 'fixed':
                    discount = min(coupon['value'], subtotal)
                elif coupon['type'] == 'free_shipping':
                    shipping_cost = 0.0
        
        # Calculate tax on discounted subtotal
        taxable_amount = subtotal - discount
        tax = taxable_amount * tax_rate
        
        # Calculate total
        total = subtotal - discount + tax + shipping_cost
        
        return {
            'subtotal': round(subtotal, 2),
            'discount': round(discount, 2),
            'tax': round(tax, 2),
            'shipping': round(shipping_cost, 2),
            'total': round(total, 2)
        }


# Global instance for easy access
cart_test_data = CartTestDataGenerator()