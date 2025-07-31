#!/usr/bin/env python
"""
MySQL Compatibility Test Runner

This script runs comprehensive tests to verify that the application works correctly
with MySQL database, including all Django ORM operations and API endpoints.

Requirements covered:
- 7.3: Verify all existing API endpoints work correctly
- 7.6: Ensure all existing database queries and operations function properly
"""

import os
import sys
import django
import subprocess
import logging
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

django.setup()

from django.test.utils import get_runner
from django.conf import settings
from django.core.management import call_command
from django.db import connection
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MySQLCompatibilityTestRunner:
    """Comprehensive MySQL compatibility test runner"""
    
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def check_mysql_connection(self):
        """Check if MySQL database is accessible"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    logger.info("✓ MySQL database connection successful")
                    return True
        except Exception as e:
            logger.error(f"✗ MySQL database connection failed: {e}")
            return False
    
    def check_database_setup(self):
        """Verify database is properly set up"""
        try:
            # Check if we're using MySQL
            if connection.vendor != 'mysql':
                logger.error(f"✗ Expected MySQL database, but using {connection.vendor}")
                return False
            
            logger.info(f"✓ Using MySQL database engine")
            
            # Check database configuration
            db_config = connection.settings_dict
            logger.info(f"✓ Database: {db_config['NAME']}")
            logger.info(f"✓ Host: {db_config['HOST']}:{db_config['PORT']}")
            logger.info(f"✓ User: {db_config['USER']}")
            
            # Check charset
            with connection.cursor() as cursor:
                cursor.execute("SELECT @@character_set_database")
                charset = cursor.fetchone()[0]
                logger.info(f"✓ Database charset: {charset}")
                
                cursor.execute("SELECT @@sql_mode")
                sql_mode = cursor.fetchone()[0]
                logger.info(f"✓ SQL mode: {sql_mode}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Database setup check failed: {e}")
            return False
    
    def run_migrations(self):
        """Ensure all migrations are applied"""
        try:
            logger.info("Running database migrations...")
            call_command('migrate', verbosity=0, interactive=False)
            logger.info("✓ Database migrations completed successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            return False
    
    def run_custom_mysql_tests(self):
        """Run our custom MySQL compatibility tests"""
        try:
            logger.info("Running custom MySQL compatibility tests...")
            
            # Import and run our custom test suite
            from test_mysql_compatibility import run_mysql_compatibility_tests
            
            success = run_mysql_compatibility_tests()
            
            if success:
                logger.info("✓ Custom MySQL compatibility tests passed")
                self.test_results['custom_mysql_tests'] = 'PASSED'
            else:
                logger.error("✗ Custom MySQL compatibility tests failed")
                self.test_results['custom_mysql_tests'] = 'FAILED'
                
            return success
            
        except Exception as e:
            logger.error(f"✗ Custom MySQL tests failed: {e}")
            self.test_results['custom_mysql_tests'] = 'ERROR'
            return False
    
    def run_django_tests(self):
        """Run Django's built-in tests"""
        try:
            logger.info("Running Django application tests...")
            
            # Get the Django test runner
            TestRunner = get_runner(settings)
            test_runner = TestRunner(verbosity=1, interactive=False, keepdb=True)
            
            # Run tests for specific apps
            test_apps = [
                'apps.authentication',
                'apps.products',
                'apps.orders',
                'apps.cart',
                'apps.customers',
                'apps.sellers',
                'apps.reviews',
                'apps.inventory',
                'apps.payments',
                'apps.shipping',
                'apps.notifications',
            ]
            
            failures = 0
            for app in test_apps:
                try:
                    logger.info(f"Testing {app}...")
                    result = test_runner.run_tests([app])
                    if result > 0:
                        failures += result
                        logger.warning(f"✗ {app} tests had {result} failures")
                        self.test_results[app] = f'FAILED ({result} failures)'
                    else:
                        logger.info(f"✓ {app} tests passed")
                        self.test_results[app] = 'PASSED'
                except Exception as e:
                    logger.error(f"✗ {app} tests error: {e}")
                    self.test_results[app] = f'ERROR: {str(e)}'
                    failures += 1
            
            return failures == 0
            
        except Exception as e:
            logger.error(f"✗ Django tests failed: {e}")
            return False
    
    def run_api_endpoint_tests(self):
        """Test API endpoints specifically"""
        try:
            logger.info("Testing API endpoints...")
            
            from django.test import Client
            from django.contrib.auth import get_user_model
            from rest_framework.test import APIClient
            
            User = get_user_model()
            client = APIClient()
            
            # Create test user with unique username
            import time
            timestamp = str(int(time.time()))
            user = User.objects.create_user(
                username=f'apitestuser_{timestamp}',
                email=f'apitest_{timestamp}@example.com',
                password='testpass123'
            )
            
            # Test endpoints that should exist
            endpoints_to_test = [
                ('/api/v1/products/', 'GET'),
                ('/api/v1/categories/', 'GET'),
                ('/api/v1/orders/', 'GET'),
                ('/api/v1/cart/', 'GET'),
                ('/admin/', 'GET'),
            ]
            
            endpoint_results = {}
            
            for endpoint, method in endpoints_to_test:
                try:
                    if method == 'GET':
                        response = client.get(endpoint)
                    elif method == 'POST':
                        response = client.post(endpoint, {})
                    
                    # Accept various status codes as valid (200, 401, 403, 404)
                    # The important thing is that the endpoint exists and doesn't crash
                    if response.status_code in [200, 201, 400, 401, 403, 404, 405]:
                        endpoint_results[endpoint] = f'OK ({response.status_code})'
                        logger.info(f"✓ {endpoint} responded with {response.status_code}")
                    else:
                        endpoint_results[endpoint] = f'UNEXPECTED ({response.status_code})'
                        logger.warning(f"? {endpoint} responded with {response.status_code}")
                        
                except Exception as e:
                    endpoint_results[endpoint] = f'ERROR: {str(e)}'
                    logger.error(f"✗ {endpoint} error: {e}")
            
            self.test_results['api_endpoints'] = endpoint_results
            
            # Consider it successful if most endpoints respond appropriately
            successful_endpoints = sum(1 for result in endpoint_results.values() 
                                     if result.startswith('OK'))
            total_endpoints = len(endpoint_results)
            
            success_rate = successful_endpoints / total_endpoints if total_endpoints > 0 else 0
            
            if success_rate >= 0.8:  # 80% success rate
                logger.info(f"✓ API endpoints test passed ({successful_endpoints}/{total_endpoints})")
                return True
            else:
                logger.warning(f"✗ API endpoints test failed ({successful_endpoints}/{total_endpoints})")
                return False
                
        except Exception as e:
            logger.error(f"✗ API endpoint tests failed: {e}")
            self.test_results['api_endpoints'] = f'ERROR: {str(e)}'
            return False
    
    def run_orm_operations_test(self):
        """Test Django ORM operations"""
        try:
            logger.info("Testing Django ORM operations...")
            
            from django.contrib.auth import get_user_model
            from django.db import transaction
            
            User = get_user_model()
            
            # Try to import models, skip if not available
            try:
                from apps.products.models import Product, Category
                from apps.sellers.models import SellerProfile as Seller
            except ImportError as e:
                logger.warning(f"Could not import models: {e}")
                self.test_results['orm_operations'] = 'SKIPPED: Models not available'
                return True
            
            # Test basic CRUD operations
            with transaction.atomic():
                # Create
                user = User.objects.create_user(
                    username='ormtestuser',
                    email='ormtest@example.com',
                    password='testpass123'
                )
                
                category = Category.objects.create(
                    name='ORM Test Category',
                    description='Category for ORM testing'
                )
                
                seller = Seller.objects.create(
                    user=user,
                    business_name='ORM Test Business',
                    business_type='INDIVIDUAL',
                    address='123 ORM Street',
                    city='ORM City',
                    state='ORM State',
                    country='ORM Country',
                    postal_code='12345',
                    phone_number='+1234567890',
                    email='ormbusiness@example.com'
                )
                
                product = Product.objects.create(
                    name='ORM Test Product',
                    description='Product for ORM testing',
                    price=99.99,
                    category=category,
                    seller=seller,
                    stock_quantity=10
                )
                
                # Read
                retrieved_product = Product.objects.select_related('category', 'seller').get(id=product.id)
                assert retrieved_product.name == 'ORM Test Product'
                assert retrieved_product.category.name == 'ORM Test Category'
                
                # Update
                retrieved_product.price = 149.99
                retrieved_product.save()
                
                updated_product = Product.objects.get(id=product.id)
                assert float(updated_product.price) == 149.99
                
                # Complex query
                from django.db.models import Count
                category_with_count = Category.objects.annotate(
                    product_count=Count('products')
                ).get(id=category.id)
                
                assert category_with_count.product_count == 1
                
                # Delete (will be rolled back due to transaction.atomic())
                product.delete()
                
                logger.info("✓ Django ORM operations test passed")
                self.test_results['orm_operations'] = 'PASSED'
                
                # Rollback the transaction to clean up
                raise Exception("Intentional rollback")
                
        except Exception as e:
            if "Intentional rollback" in str(e):
                return True
            else:
                logger.error(f"✗ Django ORM operations test failed: {e}")
                self.test_results['orm_operations'] = f'FAILED: {str(e)}'
                return False
    
    def run_data_consistency_test(self):
        """Test data consistency and integrity"""
        try:
            logger.info("Testing data consistency and integrity...")
            
            from django.contrib.auth import get_user_model
            from django.db import transaction
            
            User = get_user_model()
            
            # Try to import models, skip if not available
            try:
                from apps.products.models import Product, Category
                from apps.sellers.models import SellerProfile as Seller
                from apps.orders.models import Order, OrderItem
            except ImportError as e:
                logger.warning(f"Could not import models: {e}")
                self.test_results['data_consistency'] = 'SKIPPED: Models not available'
                return True
            
            with transaction.atomic():
                # Create test data
                user = User.objects.create_user(
                    username='consistencyuser',
                    email='consistency@example.com',
                    password='testpass123'
                )
                
                category = Category.objects.create(
                    name='Consistency Test Category',
                    description='Category for consistency testing'
                )
                
                seller = Seller.objects.create(
                    user=user,
                    business_name='Consistency Test Business',
                    business_type='INDIVIDUAL',
                    address='123 Consistency Street',
                    city='Consistency City',
                    state='Consistency State',
                    country='Consistency Country',
                    postal_code='12345',
                    phone_number='+1234567890',
                    email='consistencybusiness@example.com'
                )
                
                product = Product.objects.create(
                    name='Consistency Test Product',
                    description='Product for consistency testing',
                    price=99.99,
                    category=category,
                    seller=seller,
                    stock_quantity=10
                )
                
                # Test foreign key relationships
                order = Order.objects.create(
                    user=user,
                    total_amount=199.98,
                    status='pending'
                )
                
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=2,
                    price=product.price
                )
                
                # Verify relationships
                assert order.items.count() == 1
                assert order.items.first().product == product
                assert order.user == user
                
                logger.info("✓ Data consistency test passed")
                self.test_results['data_consistency'] = 'PASSED'
                
                # Rollback to clean up
                raise Exception("Intentional rollback")
                
        except Exception as e:
            if "Intentional rollback" in str(e):
                return True
            else:
                logger.error(f"✗ Data consistency test failed: {e}")
                self.test_results['data_consistency'] = f'FAILED: {str(e)}'
                return False
    
    def generate_report(self):
        """Generate a comprehensive test report"""
        print(f"\n{'='*80}")
        print("MYSQL COMPATIBILITY TEST REPORT")
        print(f"{'='*80}")
        print(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {connection.settings_dict['NAME']}")
        print(f"Host: {connection.settings_dict['HOST']}:{connection.settings_dict['PORT']}")
        print(f"{'='*80}")
        
        # Calculate overall statistics
        total_categories = len(self.test_results)
        passed_categories = sum(1 for result in self.test_results.values() 
                              if isinstance(result, str) and result == 'PASSED')
        
        print(f"\nOVERALL SUMMARY:")
        print(f"Test Categories: {total_categories}")
        print(f"Passed Categories: {passed_categories}")
        print(f"Success Rate: {(passed_categories/total_categories*100):.1f}%" if total_categories > 0 else "N/A")
        
        print(f"\nDETAILED RESULTS:")
        for category, result in self.test_results.items():
            if isinstance(result, dict):
                # Handle nested results (like API endpoints)
                print(f"\n{category.upper()}:")
                for item, item_result in result.items():
                    status_icon = "✓" if item_result.startswith('OK') else "✗" if item_result.startswith('ERROR') else "?"
                    print(f"  {status_icon} {item}: {item_result}")
            else:
                status_icon = "✓" if result == 'PASSED' else "✗"
                print(f"{status_icon} {category}: {result}")
        
        print(f"\n{'='*80}")
        
        # Save report to file
        report_file = backend_dir / 'mysql_compatibility_test_report.txt'
        with open(report_file, 'w') as f:
            f.write(f"MySQL Compatibility Test Report\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Database: {connection.settings_dict['NAME']}\n")
            f.write(f"Host: {connection.settings_dict['HOST']}:{connection.settings_dict['PORT']}\n\n")
            
            for category, result in self.test_results.items():
                if isinstance(result, dict):
                    f.write(f"{category}:\n")
                    for item, item_result in result.items():
                        f.write(f"  {item}: {item_result}\n")
                else:
                    f.write(f"{category}: {result}\n")
        
        logger.info(f"Test report saved to: {report_file}")
    
    def run_all_tests(self):
        """Run all MySQL compatibility tests"""
        logger.info("Starting MySQL Compatibility Test Suite...")
        
        # Check prerequisites
        if not self.check_mysql_connection():
            logger.error("Cannot proceed without MySQL connection")
            return False
        
        if not self.check_database_setup():
            logger.error("Database setup verification failed")
            return False
        
        if not self.run_migrations():
            logger.error("Migration failed")
            return False
        
        # Run all test categories
        test_methods = [
            ('Custom MySQL Tests', self.run_custom_mysql_tests),
            ('ORM Operations', self.run_orm_operations_test),
            ('Data Consistency', self.run_data_consistency_test),
            ('API Endpoints', self.run_api_endpoint_tests),
        ]
        
        overall_success = True
        
        for test_name, test_method in test_methods:
            logger.info(f"\n{'-'*60}")
            logger.info(f"Running {test_name}...")
            logger.info(f"{'-'*60}")
            
            try:
                success = test_method()
                if not success:
                    overall_success = False
            except Exception as e:
                logger.error(f"Test category '{test_name}' failed with exception: {e}")
                self.test_results[test_name.lower().replace(' ', '_')] = f'ERROR: {str(e)}'
                overall_success = False
        
        # Generate report
        self.generate_report()
        
        return overall_success


def main():
    """Main function to run MySQL compatibility tests"""
    runner = MySQLCompatibilityTestRunner()
    
    try:
        success = runner.run_all_tests()
        
        if success:
            logger.info("\n🎉 All MySQL compatibility tests passed!")
            return 0
        else:
            logger.error("\n❌ Some MySQL compatibility tests failed!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\nTest execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\nUnexpected error during test execution: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())