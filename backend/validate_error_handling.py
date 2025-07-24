#!/usr/bin/env python
"""
Error Handling and Edge Case Validation Script

This script tests error handling and edge cases in the e-commerce platform,
ensuring that the system gracefully handles errors and edge conditions.
"""

import os
import sys
import django
import json
import uuid
import requests
from decimal import Decimal
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework.exceptions import APIException

from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from apps.customers.models import Address
from apps.cart.models import Cart, CartItem
from apps.inventory.models import Inventory
from apps.payments.models import Payment
from apps.shipping.models import ShippingPartner
from apps.core.exceptions import EcommerceException, InsufficientStockException

User = get_user_model()


class ErrorHandlingValidator:
    """Validates error handling and edge cases"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Create test data
        self.setup_test_data()
    
    def setup_test_data(self):
        """Set up test data for validation"""
        try:
            # Create test user
            self.user, _ = User.objects.get_or_create(
                username='erroruser',
                defaults={
                    'email': 'error@example.com',
                    'password': 'testpass123',
                    'first_name': 'Error',
                    'last_name': 'User'
                }
            )
            
            # Create category
            self.category, _ = Category.objects.get_or_create(
                name='Test Category',
                defaults={
                    'slug': 'test-category',
                    'is_active': True
                }
            )
            
            # Create product
            self.product, _ = Product.objects.get_or_create(
                name='Test Product',
                defaults={
                    'slug': 'test-product',
                    'description': 'Test product description',
                    'short_description': 'Test product short description',
                    'category': self.category,
                    'brand': 'Test Brand',
                    'sku': 'TEST001',
                    'price': Decimal('99.99'),
                    'is_active': True
                }
            )
            
            # Create inventory
            self.inventory, _ = Inventory.objects.get_or_create(
                product=self.product,
                defaults={
                    'quantity': 100,
                    'reserved_quantity': 0,
                    'minimum_stock_level': 10,
                    'cost_price': Decimal('50.00')
                }
            )
            
            # Create cart
            self.cart, _ = Cart.objects.get_or_create(
                user=self.user
            )
            
            # Create shipping partner
            self.shipping_partner, _ = ShippingPartner.objects.get_or_create(
                name='Test Shipping',
                defaults={
                    'code': 'TEST',
                    'is_active': True
                }
            )
            
            print("✓ Test data setup complete")
        except Exception as e:
            print(f"✗ Test data setup failed: {str(e)}")
            raise
    
    def test_database_constraints(self):
        """Test database constraints and integrity errors"""
        print("\nTesting database constraints...")
        
        # Test unique constraint violation
        try:
            with transaction.atomic():
                # Try to create a product with the same slug
                duplicate_product = Product(
                    name='Duplicate Product',
                    slug='test-product',  # Same slug as existing product
                    description='Duplicate product description',
                    short_description='Duplicate product short description',
                    category=self.category,
                    brand='Test Brand',
                    sku='TEST002',
                    price=Decimal('99.99'),
                    is_active=True
                )
                duplicate_product.save()
                
                # If we get here, the constraint didn't work
                self.results['tests']['unique_constraint'] = {
                    'status': 'FAILED',
                    'message': 'Unique constraint not enforced'
                }
                print("✗ Unique constraint test failed")
                return False
        except IntegrityError:
            # This is expected
            self.results['tests']['unique_constraint'] = {
                'status': 'PASSED',
                'message': 'Unique constraint properly enforced'
            }
            print("✓ Unique constraint test passed")
        
        # Test foreign key constraint
        try:
            with transaction.atomic():
                # Try to create a product with non-existent category
                invalid_product = Product(
                    name='Invalid Product',
                    slug='invalid-product',
                    description='Invalid product description',
                    short_description='Invalid product short description',
                    category_id=99999,  # Non-existent category ID
                    brand='Test Brand',
                    sku='TEST003',
                    price=Decimal('99.99'),
                    is_active=True
                )
                invalid_product.save()
                
                # If we get here, the constraint didn't work
                self.results['tests']['foreign_key_constraint'] = {
                    'status': 'FAILED',
                    'message': 'Foreign key constraint not enforced'
                }
                print("✗ Foreign key constraint test failed")
                return False
        except IntegrityError:
            # This is expected
            self.results['tests']['foreign_key_constraint'] = {
                'status': 'PASSED',
                'message': 'Foreign key constraint properly enforced'
            }
            print("✓ Foreign key constraint test passed")
        
        return True
    
    def test_validation_errors(self):
        """Test validation errors"""
        print("\nTesting validation errors...")
        
        # Test model validation
        try:
            # Try to create a product with negative price
            invalid_product = Product(
                name='Invalid Product',
                slug='invalid-product',
                description='Invalid product description',
                short_description='Invalid product short description',
                category=self.category,
                brand='Test Brand',
                sku='TEST004',
                price=Decimal('-99.99'),  # Negative price
                is_active=True
            )
            invalid_product.full_clean()  # This should raise ValidationError
            
            # If we get here, the validation didn't work
            self.results['tests']['model_validation'] = {
                'status': 'FAILED',
                'message': 'Model validation not enforced'
            }
            print("✗ Model validation test failed")
            return False
        except ValidationError:
            # This is expected
            self.results['tests']['model_validation'] = {
                'status': 'PASSED',
                'message': 'Model validation properly enforced'
            }
            print("✓ Model validation test passed")
        
        return True
    
    def test_business_logic_errors(self):
        """Test business logic errors"""
        print("\nTesting business logic errors...")
        
        # Test insufficient stock exception
        try:
            # Set inventory to 0
            self.inventory.quantity = 0
            self.inventory.save()
            
            # Try to add to cart
            from apps.cart.services import CartService
            cart_service = CartService()
            cart_service.add_to_cart(self.user, self.product.id, 1)
            
            # If we get here, the business logic didn't work
            self.results['tests']['insufficient_stock'] = {
                'status': 'FAILED',
                'message': 'Insufficient stock check not enforced'
            }
            print("✗ Insufficient stock test failed")
            
            # Reset inventory
            self.inventory.quantity = 100
            self.inventory.save()
            
            return False
        except InsufficientStockException:
            # This is expected
            self.results['tests']['insufficient_stock'] = {
                'status': 'PASSED',
                'message': 'Insufficient stock check properly enforced'
            }
            print("✓ Insufficient stock test passed")
            
            # Reset inventory
            self.inventory.quantity = 100
            self.inventory.save()
        
        # Test order validation
        try:
            # Try to create an order with no items
            from apps.orders.services import OrderService
            order_service = OrderService()
            
            # Clear cart first
            CartItem.objects.filter(cart=self.cart).delete()
            
            # Try to create order from empty cart
            shipping_address = {
                'first_name': 'Test',
                'last_name': 'User',
                'address_line_1': '123 Test Street',
                'city': 'Test City',
                'state': 'Test State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            }
            
            order_service.create_order(
                user=self.user,
                shipping_address=shipping_address,
                billing_address=shipping_address,
                payment_method='PREPAID',
                shipping_method='STANDARD',
                shipping_partner_code='TEST'
            )
            
            # If we get here, the business logic didn't work
            self.results['tests']['empty_cart_order'] = {
                'status': 'FAILED',
                'message': 'Empty cart order validation not enforced'
            }
            print("✗ Empty cart order test failed")
            return False
        except EcommerceException:
            # This is expected
            self.results['tests']['empty_cart_order'] = {
                'status': 'PASSED',
                'message': 'Empty cart order validation properly enforced'
            }
            print("✓ Empty cart order test passed")
        
        return True
    
    def test_api_error_handling(self):
        """Test API error handling"""
        print("\nTesting API error handling...")
        
        # Test 404 handling
        try:
            # Try to access non-existent product
            url = 'http://localhost:8000/api/v1/products/99999/'
            response = requests.get(url)
            
            if response.status_code != 404:
                self.results['tests']['api_404'] = {
                    'status': 'FAILED',
                    'message': f'API 404 handling not working properly. Got status {response.status_code}'
                }
                print(f"✗ API 404 test failed. Got status {response.status_code}")
                return False
            
            # Check if response is properly formatted
            error_data = response.json()
            if 'detail' not in error_data:
                self.results['tests']['api_404'] = {
                    'status': 'FAILED',
                    'message': 'API 404 response not properly formatted'
                }
                print("✗ API 404 test failed. Response not properly formatted")
                return False
            
            self.results['tests']['api_404'] = {
                'status': 'PASSED',
                'message': 'API 404 handling properly implemented'
            }
            print("✓ API 404 test passed")
        except Exception as e:
            self.results['tests']['api_404'] = {
                'status': 'ERROR',
                'message': f'API 404 test error: {str(e)}'
            }
            print(f"✗ API 404 test error: {str(e)}")
            return False
        
        # Test validation error handling
        try:
            # Try to create a product with invalid data
            url = 'http://localhost:8000/api/v1/products/'
            data = {
                'name': '',  # Empty name should fail validation
                'price': -10.99  # Negative price should fail validation
            }
            response = requests.post(url, json=data)
            
            if response.status_code != 400:
                self.results['tests']['api_validation'] = {
                    'status': 'FAILED',
                    'message': f'API validation error handling not working properly. Got status {response.status_code}'
                }
                print(f"✗ API validation test failed. Got status {response.status_code}")
                return False
            
            # Check if response is properly formatted
            error_data = response.json()
            if not any(field in error_data for field in ['name', 'price', 'errors', 'detail']):
                self.results['tests']['api_validation'] = {
                    'status': 'FAILED',
                    'message': 'API validation error response not properly formatted'
                }
                print("✗ API validation test failed. Response not properly formatted")
                return False
            
            self.results['tests']['api_validation'] = {
                'status': 'PASSED',
                'message': 'API validation error handling properly implemented'
            }
            print("✓ API validation test passed")
        except Exception as e:
            self.results['tests']['api_validation'] = {
                'status': 'ERROR',
                'message': f'API validation test error: {str(e)}'
            }
            print(f"✗ API validation test error: {str(e)}")
            return False
        
        return True
    
    def test_transaction_rollback(self):
        """Test transaction rollback on error"""
        print("\nTesting transaction rollback...")
        
        # Get initial product count
        initial_count = Product.objects.count()
        
        # Try to create products in a transaction that will fail
        try:
            with transaction.atomic():
                # Create a valid product
                valid_product = Product.objects.create(
                    name='Valid Product',
                    slug='valid-product',
                    description='Valid product description',
                    short_description='Valid product short description',
                    category=self.category,
                    brand='Test Brand',
                    sku='TEST005',
                    price=Decimal('99.99'),
                    is_active=True
                )
                
                # Create an invalid product that will cause the transaction to fail
                invalid_product = Product.objects.create(
                    name='Invalid Product',
                    slug='test-product',  # Duplicate slug will cause IntegrityError
                    description='Invalid product description',
                    short_description='Invalid product short description',
                    category=self.category,
                    brand='Test Brand',
                    sku='TEST006',
                    price=Decimal('99.99'),
                    is_active=True
                )
        except IntegrityError:
            # This is expected
            pass
        
        # Check if product count is still the same
        final_count = Product.objects.count()
        
        if final_count != initial_count:
            self.results['tests']['transaction_rollback'] = {
                'status': 'FAILED',
                'message': f'Transaction rollback not working properly. Initial count: {initial_count}, Final count: {final_count}'
            }
            print(f"✗ Transaction rollback test failed. Initial count: {initial_count}, Final count: {final_count}")
            return False
        
        self.results['tests']['transaction_rollback'] = {
            'status': 'PASSED',
            'message': 'Transaction rollback properly implemented'
        }
        print("✓ Transaction rollback test passed")
        
        return True
    
    def test_edge_cases(self):
        """Test edge cases"""
        print("\nTesting edge cases...")
        
        # Test very large order
        try:
            # Add a large quantity to cart
            CartItem.objects.filter(cart=self.cart).delete()
            cart_item = CartItem.objects.create(
                cart=self.cart,
                product=self.product,
                quantity=1000  # Very large quantity
            )
            
            # Try to create order
            from apps.orders.services import OrderService
            order_service = OrderService()
            
            shipping_address = {
                'first_name': 'Test',
                'last_name': 'User',
                'address_line_1': '123 Test Street',
                'city': 'Test City',
                'state': 'Test State',
                'postal_code': '12345',
                'country': 'India',
                'phone': '1234567890'
            }
            
            # This should fail because we don't have enough inventory
            order_service.create_order(
                user=self.user,
                shipping_address=shipping_address,
                billing_address=shipping_address,
                payment_method='PREPAID',
                shipping_method='STANDARD',
                shipping_partner_code='TEST'
            )
            
            # If we get here, the edge case handling didn't work
            self.results['tests']['large_order'] = {
                'status': 'FAILED',
                'message': 'Large order quantity not properly validated'
            }
            print("✗ Large order test failed")
            
            # Clean up
            CartItem.objects.filter(cart=self.cart).delete()
            
            return False
        except InsufficientStockException:
            # This is expected
            self.results['tests']['large_order'] = {
                'status': 'PASSED',
                'message': 'Large order quantity properly validated'
            }
            print("✓ Large order test passed")
            
            # Clean up
            CartItem.objects.filter(cart=self.cart).delete()
        
        # Test very long text inputs
        try:
            # Try to create a product with very long text
            long_text = 'A' * 10000  # Very long text
            
            long_text_product = Product(
                name=long_text[:200],  # Truncate to avoid immediate validation error
                slug='long-text-product',
                description=long_text,
                short_description=long_text[:500],  # Truncate to avoid immediate validation error
                category=self.category,
                brand='Test Brand',
                sku='TEST007',
                price=Decimal('99.99'),
                is_active=True
            )
            
            # This should either truncate the text or raise a validation error
            long_text_product.full_clean()
            long_text_product.save()
            
            # If we get here, check if the text was truncated
            saved_product = Product.objects.get(slug='long-text-product')
            if len(saved_product.description) == len(long_text):
                self.results['tests']['long_text'] = {
                    'status': 'FAILED',
                    'message': 'Very long text not properly handled'
                }
                print("✗ Long text test failed")
                
                # Clean up
                saved_product.delete()
                
                return False
            
            self.results['tests']['long_text'] = {
                'status': 'PASSED',
                'message': 'Very long text properly handled'
            }
            print("✓ Long text test passed")
            
            # Clean up
            saved_product.delete()
        except ValidationError:
            # This is also acceptable
            self.results['tests']['long_text'] = {
                'status': 'PASSED',
                'message': 'Very long text properly validated'
            }
            print("✓ Long text test passed")
        
        return True
    
    def validate_all(self):
        """Run all validation tests"""
        print("\n=== Starting Error Handling and Edge Case Validation ===\n")
        
        # Run all tests
        db_constraints = self.test_database_constraints()
        validation_errors = self.test_validation_errors()
        business_logic = self.test_business_logic_errors()
        api_errors = self.test_api_error_handling()
        transaction_rollback = self.test_transaction_rollback()
        edge_cases = self.test_edge_cases()
        
        # Determine overall status
        if all([db_constraints, validation_errors, business_logic, api_errors, transaction_rollback, edge_cases]):
            self.results['overall_status'] = 'PASSED'
        else:
            self.results['overall_status'] = 'FAILED'
        
        print("\n=== Error Handling and Edge Case Validation Complete ===\n")
        print(f"Overall Status: {self.results['overall_status']}")
        
        # Save results to file
        with open('error_handling_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Results saved to error_handling_results.json")
        
        return self.results['overall_status'] == 'PASSED'


if __name__ == '__main__':
    validator = ErrorHandlingValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)