"""
Product and Order Management Test Data Factory

Provides test data generation for product and order management API tests.
Includes product catalogs, order scenarios, and validation data.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random
import string
from decimal import Decimal

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import Environment, UserRole
from core.models import TestUser


class ProductTestDataFactory:
    """Factory for generating product test data"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.categories = [
            'Electronics', 'Clothing', 'Books', 'Home & Garden', 
            'Sports', 'Beauty', 'Automotive', 'Toys', 'Food'
        ]
        self.brands = [
            'TestBrand A', 'TestBrand B', 'TestBrand C', 'TestBrand D', 'TestBrand E'
        ]
    
    def generate_test_products(self) -> List[Dict[str, Any]]:
        """Generate comprehensive set of test products"""
        products = []
        
        # Generate products across different categories
        for i in range(50):
            product_id = i + 1
            category = random.choice(self.categories)
            brand = random.choice(self.brands)
            
            # Generate product variants
            variants = []
            for j in range(random.randint(1, 3)):
                variant = {
                    'id': f"{product_id}_variant_{j+1}",
                    'sku': f"SKU{product_id:03d}V{j+1}",
                    'size': random.choice(['S', 'M', 'L', 'XL']) if category == 'Clothing' else None,
                    'color': random.choice(['Red', 'Blue', 'Green', 'Black', 'White']),
                    'price': round(random.uniform(10.0, 500.0), 2),
                    'stock_quantity': random.randint(0, 100),
                    'weight': round(random.uniform(0.1, 5.0), 2)
                }
                variants.append(variant)
            
            product = {
                'id': product_id,
                'name': f"Test Product {product_id}",
                'description': f"This is a test product for {category.lower()} category. High quality {brand} product.",
                'category': category,
                'brand': brand,
                'sku': f"SKU{product_id:03d}",
                'price': round(random.uniform(10.0, 500.0), 2),
                'sale_price': None,
                'stock_quantity': random.randint(0, 100),
                'is_active': random.choice([True, True, True, False]),  # 75% active
                'is_featured': random.choice([True, False, False, False]),  # 25% featured
                'weight': round(random.uniform(0.1, 5.0), 2),
                'dimensions': {
                    'length': round(random.uniform(5.0, 50.0), 1),
                    'width': round(random.uniform(5.0, 50.0), 1),
                    'height': round(random.uniform(1.0, 20.0), 1)
                },
                'images': [
                    f"https://testcdn.example.com/products/{product_id}/image1.jpg",
                    f"https://testcdn.example.com/products/{product_id}/image2.jpg"
                ],
                'variants': variants,
                'tags': [category.lower(), brand.lower().replace(' ', '_')],
                'rating': round(random.uniform(1.0, 5.0), 1),
                'review_count': random.randint(0, 100),
                'created_at': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                'updated_at': datetime.now().isoformat(),
                'seller_id': random.randint(1, 8),  # Reference to seller users
                'meta_data': {
                    'seo_title': f"Test Product {product_id} - {brand}",
                    'seo_description': f"Buy {brand} Test Product {product_id} online",
                    'warranty_months': random.choice([6, 12, 24, 36])
                }
            }
            
            # Add sale price for some products
            if random.choice([True, False]):
                product['sale_price'] = round(product['price'] * 0.8, 2)
            
            products.append(product)
        
        return products
    
    def get_product_crud_test_data(self) -> List[Dict[str, Any]]:
        """Get test data for product CRUD operations"""
        return [
            # Valid product creation
            {
                'scenario': 'valid_product_creation',
                'data': {
                    'name': 'New Test Product',
                    'description': 'A new product for testing',
                    'category': 'Electronics',
                    'brand': 'TestBrand A',
                    'sku': 'NEWSKU001',
                    'price': 99.99,
                    'stock_quantity': 50,
                    'is_active': True,
                    'weight': 1.5
                },
                'expected_status': 201,
                'expected_fields': ['id', 'name', 'sku', 'price', 'created_at']
            },
            # Missing required fields
            {
                'scenario': 'missing_required_fields',
                'data': {
                    'description': 'Product without name',
                    'price': 50.0
                },
                'expected_status': 400,
                'expected_errors': ['name', 'category', 'sku']
            },
            # Invalid price
            {
                'scenario': 'invalid_price',
                'data': {
                    'name': 'Invalid Price Product',
                    'category': 'Electronics',
                    'sku': 'INVALID001',
                    'price': -10.0,  # Negative price
                    'stock_quantity': 10
                },
                'expected_status': 400,
                'expected_errors': ['price']
            },
            # Duplicate SKU
            {
                'scenario': 'duplicate_sku',
                'data': {
                    'name': 'Duplicate SKU Product',
                    'category': 'Electronics',
                    'sku': 'SKU001V1',  # Existing SKU
                    'price': 75.0,
                    'stock_quantity': 20
                },
                'expected_status': 400,
                'expected_errors': ['sku']
            }
        ]
    
    def get_product_search_test_data(self) -> List[Dict[str, Any]]:
        """Get test data for product search and filtering"""
        return [
            # Search by name
            {
                'scenario': 'search_by_name',
                'params': {'search': 'Test Product 1'},
                'expected_status': 200,
                'expected_min_results': 1
            },
            # Filter by category
            {
                'scenario': 'filter_by_category',
                'params': {'category': 'Electronics'},
                'expected_status': 200,
                'expected_min_results': 1
            },
            # Filter by price range
            {
                'scenario': 'filter_by_price_range',
                'params': {'min_price': 50, 'max_price': 200},
                'expected_status': 200,
                'expected_min_results': 0
            },
            # Filter by brand
            {
                'scenario': 'filter_by_brand',
                'params': {'brand': 'TestBrand A'},
                'expected_status': 200,
                'expected_min_results': 0
            },
            # Sort by price
            {
                'scenario': 'sort_by_price_asc',
                'params': {'ordering': 'price'},
                'expected_status': 200,
                'expected_min_results': 0
            },
            # Sort by name descending
            {
                'scenario': 'sort_by_name_desc',
                'params': {'ordering': '-name'},
                'expected_status': 200,
                'expected_min_results': 0
            },
            # Complex filter combination
            {
                'scenario': 'complex_filter',
                'params': {
                    'category': 'Electronics',
                    'min_price': 100,
                    'is_active': True,
                    'ordering': 'price'
                },
                'expected_status': 200,
                'expected_min_results': 0
            }
        ]


class OrderTestDataFactory:
    """Factory for generating order test data"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.order_statuses = [
            'pending', 'confirmed', 'processing', 'shipped', 
            'delivered', 'cancelled', 'refunded'
        ]
        self.payment_methods = ['credit_card', 'paypal', 'bank_transfer', 'cash_on_delivery']
        self.shipping_methods = ['standard', 'express', 'overnight', 'pickup']
    
    def generate_test_orders(self) -> List[Dict[str, Any]]:
        """Generate comprehensive set of test orders"""
        orders = []
        
        for i in range(30):
            order_id = i + 1
            customer_id = random.randint(1, 10)  # Reference to customer users
            
            # Generate order items
            items = []
            total_amount = 0
            for j in range(random.randint(1, 5)):
                product_id = random.randint(1, 50)
                quantity = random.randint(1, 3)
                unit_price = round(random.uniform(10.0, 200.0), 2)
                item_total = unit_price * quantity
                total_amount += item_total
                
                item = {
                    'id': f"{order_id}_item_{j+1}",
                    'product_id': product_id,
                    'product_name': f"Test Product {product_id}",
                    'sku': f"SKU{product_id:03d}",
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': item_total,
                    'variant_id': f"{product_id}_variant_1" if random.choice([True, False]) else None
                }
                items.append(item)
            
            # Calculate totals
            subtotal = total_amount
            tax_amount = round(subtotal * 0.08, 2)  # 8% tax
            shipping_cost = round(random.uniform(5.0, 25.0), 2)
            discount_amount = round(random.uniform(0, subtotal * 0.2), 2) if random.choice([True, False]) else 0
            total_amount = subtotal + tax_amount + shipping_cost - discount_amount
            
            order = {
                'id': order_id,
                'order_number': f"ORD{order_id:06d}",
                'customer_id': customer_id,
                'status': random.choice(self.order_statuses),
                'items': items,
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'shipping_cost': shipping_cost,
                'discount_amount': discount_amount,
                'total_amount': total_amount,
                'currency': 'USD',
                'payment_method': random.choice(self.payment_methods),
                'payment_status': random.choice(['pending', 'paid', 'failed', 'refunded']),
                'shipping_method': random.choice(self.shipping_methods),
                'shipping_address': {
                    'street': f"{100 + order_id} Test Street",
                    'city': 'Test City',
                    'state': 'TS',
                    'postal_code': f"{10000 + order_id}",
                    'country': 'US'
                },
                'billing_address': {
                    'street': f"{200 + order_id} Billing Ave",
                    'city': 'Billing City',
                    'state': 'BC',
                    'postal_code': f"{20000 + order_id}",
                    'country': 'US'
                },
                'notes': f"Test order {order_id} notes" if random.choice([True, False]) else None,
                'created_at': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
                'updated_at': datetime.now().isoformat(),
                'estimated_delivery': (datetime.now() + timedelta(days=random.randint(3, 14))).isoformat(),
                'tracking_number': f"TRACK{order_id:08d}" if random.choice([True, False]) else None
            }
            
            orders.append(order)
        
        return orders
    
    def get_order_crud_test_data(self) -> List[Dict[str, Any]]:
        """Get test data for order CRUD operations"""
        return [
            # Valid order creation
            {
                'scenario': 'valid_order_creation',
                'data': {
                    'customer_id': 1,
                    'items': [
                        {
                            'product_id': 1,
                            'quantity': 2,
                            'unit_price': 50.0
                        },
                        {
                            'product_id': 2,
                            'quantity': 1,
                            'unit_price': 75.0
                        }
                    ],
                    'shipping_address': {
                        'street': '123 Test St',
                        'city': 'Test City',
                        'state': 'TS',
                        'postal_code': '12345',
                        'country': 'US'
                    },
                    'payment_method': 'credit_card',
                    'shipping_method': 'standard'
                },
                'expected_status': 201,
                'expected_fields': ['id', 'order_number', 'total_amount', 'status']
            },
            # Missing customer
            {
                'scenario': 'missing_customer',
                'data': {
                    'items': [
                        {
                            'product_id': 1,
                            'quantity': 1,
                            'unit_price': 50.0
                        }
                    ]
                },
                'expected_status': 400,
                'expected_errors': ['customer_id']
            },
            # Empty items
            {
                'scenario': 'empty_items',
                'data': {
                    'customer_id': 1,
                    'items': [],
                    'shipping_address': {
                        'street': '123 Test St',
                        'city': 'Test City',
                        'state': 'TS',
                        'postal_code': '12345',
                        'country': 'US'
                    }
                },
                'expected_status': 400,
                'expected_errors': ['items']
            },
            # Invalid product in items
            {
                'scenario': 'invalid_product',
                'data': {
                    'customer_id': 1,
                    'items': [
                        {
                            'product_id': 99999,  # Non-existent product
                            'quantity': 1,
                            'unit_price': 50.0
                        }
                    ],
                    'shipping_address': {
                        'street': '123 Test St',
                        'city': 'Test City',
                        'state': 'TS',
                        'postal_code': '12345',
                        'country': 'US'
                    }
                },
                'expected_status': 400,
                'expected_errors': ['items']
            }
        ]
    
    def get_order_status_test_data(self) -> List[Dict[str, Any]]:
        """Get test data for order status management"""
        return [
            # Valid status transitions
            {
                'scenario': 'pending_to_confirmed',
                'from_status': 'pending',
                'to_status': 'confirmed',
                'expected_status': 200,
                'is_valid_transition': True
            },
            {
                'scenario': 'confirmed_to_processing',
                'from_status': 'confirmed',
                'to_status': 'processing',
                'expected_status': 200,
                'is_valid_transition': True
            },
            {
                'scenario': 'processing_to_shipped',
                'from_status': 'processing',
                'to_status': 'shipped',
                'expected_status': 200,
                'is_valid_transition': True
            },
            {
                'scenario': 'shipped_to_delivered',
                'from_status': 'shipped',
                'to_status': 'delivered',
                'expected_status': 200,
                'is_valid_transition': True
            },
            # Invalid status transitions
            {
                'scenario': 'delivered_to_pending',
                'from_status': 'delivered',
                'to_status': 'pending',
                'expected_status': 400,
                'is_valid_transition': False
            },
            {
                'scenario': 'cancelled_to_processing',
                'from_status': 'cancelled',
                'to_status': 'processing',
                'expected_status': 400,
                'is_valid_transition': False
            }
        ]
    
    def get_order_search_test_data(self) -> List[Dict[str, Any]]:
        """Get test data for order search and filtering"""
        return [
            # Search by order number
            {
                'scenario': 'search_by_order_number',
                'params': {'search': 'ORD000001'},
                'expected_status': 200,
                'expected_min_results': 0
            },
            # Filter by status
            {
                'scenario': 'filter_by_status',
                'params': {'status': 'pending'},
                'expected_status': 200,
                'expected_min_results': 0
            },
            # Filter by customer
            {
                'scenario': 'filter_by_customer',
                'params': {'customer_id': 1},
                'expected_status': 200,
                'expected_min_results': 0
            },
            # Filter by date range
            {
                'scenario': 'filter_by_date_range',
                'params': {
                    'created_after': '2024-01-01',
                    'created_before': '2024-12-31'
                },
                'expected_status': 200,
                'expected_min_results': 0
            },
            # Filter by total amount range
            {
                'scenario': 'filter_by_amount_range',
                'params': {'min_total': 50, 'max_total': 500},
                'expected_status': 200,
                'expected_min_results': 0
            },
            # Sort by created date
            {
                'scenario': 'sort_by_created_date',
                'params': {'ordering': '-created_at'},
                'expected_status': 200,
                'expected_min_results': 0
            }
        ]
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Get all API endpoints for product and order testing"""
        base_url = f"http://localhost:8000"
        
        return {
            # Product endpoints
            'products': f"{base_url}/api/v1/products/",
            'product_detail': f"{base_url}/api/v1/products/{{id}}/",
            'product_categories': f"{base_url}/api/v1/products/categories/",
            'product_brands': f"{base_url}/api/v1/products/brands/",
            'product_search': f"{base_url}/api/v1/products/search/",
            
            # Order endpoints
            'orders': f"{base_url}/api/v1/orders/",
            'order_detail': f"{base_url}/api/v1/orders/{{id}}/",
            'order_status': f"{base_url}/api/v1/orders/{{id}}/status/",
            'order_items': f"{base_url}/api/v1/orders/{{id}}/items/",
            'order_tracking': f"{base_url}/api/v1/orders/{{id}}/tracking/",
            
            # Inventory endpoints
            'inventory': f"{base_url}/api/v1/inventory/",
            'inventory_detail': f"{base_url}/api/v1/inventory/{{product_id}}/",
            
            # Seller endpoints (for product management)
            'seller_products': f"{base_url}/api/v1/sellers/products/",
            'seller_orders': f"{base_url}/api/v1/sellers/orders/"
        }


# Convenience functions
def get_test_products(environment: Environment = Environment.DEVELOPMENT) -> List[Dict[str, Any]]:
    """Get all test products for the specified environment"""
    factory = ProductTestDataFactory(environment)
    return factory.generate_test_products()


def get_test_orders(environment: Environment = Environment.DEVELOPMENT) -> List[Dict[str, Any]]:
    """Get all test orders for the specified environment"""
    factory = OrderTestDataFactory(environment)
    return factory.generate_test_orders()


if __name__ == '__main__':
    # Example usage
    product_factory = ProductTestDataFactory()
    order_factory = OrderTestDataFactory()
    
    products = product_factory.generate_test_products()
    orders = order_factory.generate_test_orders()
    
    print(f"Generated {len(products)} test products")
    print(f"Generated {len(orders)} test orders")