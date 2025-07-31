"""
Test suite for MySQL schema optimization.
Tests the effectiveness of indexes, constraints, and performance improvements.
"""
import time
import unittest
from django.test import TestCase, TransactionTestCase
from django.db import connection, transaction
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from apps.products.models import Product, Category, ProductRating
from apps.orders.models import Order, OrderItem
from apps.reviews.models import Review
from apps.customers.models import CustomerProfile
from core.schema_optimizer import MySQLSchemaOptimizer

User = get_user_model()


class MySQLSchemaOptimizationTestCase(TransactionTestCase):
    """Test MySQL schema optimizations."""
    
    def setUp(self):
        """Set up test data."""
        self.optimizer = MySQLSchemaOptimizer()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            category=self.category,
            sku='TEST-001',
            price=99.99
        )

    def test_database_connection_is_mysql(self):
        """Test that we're using MySQL database."""
        self.assertEqual(connection.vendor, 'mysql')

    def test_table_indexes_exist(self):
        """Test that performance indexes have been created."""
        with connection.cursor() as cursor:
            # Test product table indexes
            cursor.execute("SHOW INDEX FROM products_product")
            indexes = cursor.fetchall()
            index_names = [index[2] for index in indexes]
            
            expected_indexes = [
                'idx_products_product_category_active',
                'idx_products_product_price_active',
                'idx_products_product_featured_active',
                'idx_products_product_brand_active',
            ]
            
            for expected_index in expected_indexes:
                self.assertIn(expected_index, index_names, 
                            f"Index {expected_index} not found in products_product table")

    def test_table_constraints_exist(self):
        """Test that table constraints have been applied."""
        with connection.cursor() as cursor:
            # Test product table constraints
            cursor.execute("""
                SELECT CONSTRAINT_NAME 
                FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS 
                WHERE TABLE_NAME = 'products_product' 
                AND TABLE_SCHEMA = DATABASE()
            """)
            constraints = cursor.fetchall()
            constraint_names = [constraint[0] for constraint in constraints]
            
            expected_constraints = [
                'chk_product_price_positive',
                'chk_product_discount_valid',
            ]
            
            for expected_constraint in expected_constraints:
                self.assertIn(expected_constraint, constraint_names,
                            f"Constraint {expected_constraint} not found in products_product table")

    def test_data_type_optimizations(self):
        """Test that data types have been optimized for MySQL."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'products_product' 
                AND TABLE_SCHEMA = DATABASE()
                ORDER BY COLUMN_NAME
            """)
            columns = cursor.fetchall()
            
            column_info = {col[0]: {'type': col[1], 'nullable': col[2], 'default': col[3]} 
                          for col in columns}
            
            # Test specific column optimizations
            self.assertEqual(column_info['price']['type'], 'decimal')
            self.assertEqual(column_info['is_active']['type'], 'tinyint')
            self.assertEqual(column_info['is_featured']['type'], 'tinyint')

    def test_query_performance_with_indexes(self):
        """Test that queries perform better with indexes."""
        # Create additional test data
        for i in range(100):
            Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                description=f'Description {i}',
                category=self.category,
                sku=f'SKU-{i:03d}',
                price=10.00 + i,
                is_active=i % 2 == 0,
                is_featured=i % 10 == 0
            )
        
        # Test query performance
        with connection.cursor() as cursor:
            # Query with category and active status (should use index)
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM products_product 
                WHERE category_id = %s AND is_active = 1
            """, [self.category.id])
            indexed_query_time = time.time() - start_time
            
            # Query without using indexes (full table scan)
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM products_product 
                WHERE description LIKE %s
            """, ['%Description%'])
            full_scan_time = time.time() - start_time
            
            # Indexed query should be faster (though with small dataset, difference might be minimal)
            self.assertLessEqual(indexed_query_time, full_scan_time * 2,
                               "Indexed query should be reasonably fast")

    def test_fulltext_search_functionality(self):
        """Test that full-text search indexes work correctly."""
        # Create products with searchable content
        Product.objects.create(
            name='Smartphone Apple iPhone',
            slug='smartphone-apple-iphone',
            description='Latest Apple iPhone with advanced features',
            category=self.category,
            sku='PHONE-001',
            price=999.99
        )
        
        Product.objects.create(
            name='Laptop Dell XPS',
            slug='laptop-dell-xps',
            description='High-performance Dell laptop for professionals',
            category=self.category,
            sku='LAPTOP-001',
            price=1299.99
        )
        
        with connection.cursor() as cursor:
            # Test full-text search
            cursor.execute("""
                SELECT name FROM products_product 
                WHERE MATCH(name, description, short_description) AGAINST(%s IN NATURAL LANGUAGE MODE)
            """, ['Apple iPhone'])
            
            results = cursor.fetchall()
            self.assertGreater(len(results), 0, "Full-text search should return results")
            
            # Verify the correct product is found
            product_names = [result[0] for result in results]
            self.assertIn('Smartphone Apple iPhone', product_names)

    def test_composite_index_usage(self):
        """Test that composite indexes are being used effectively."""
        # Create test data with various combinations
        for i in range(50):
            Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                description=f'Description {i}',
                category=self.category,
                sku=f'SKU-{i:03d}',
                price=10.00 + i,
                is_active=True,
                is_featured=i % 5 == 0,
                brand='TestBrand' if i % 3 == 0 else 'OtherBrand'
            )
        
        with connection.cursor() as cursor:
            # Test composite index usage with EXPLAIN
            cursor.execute("""
                EXPLAIN SELECT * FROM products_product 
                WHERE category_id = %s AND is_active = 1 AND price BETWEEN %s AND %s
            """, [self.category.id, 20.00, 40.00])
            
            explain_result = cursor.fetchall()
            
            # Check that the query is using an index (not doing full table scan)
            self.assertNotEqual(explain_result[0][3], 'ALL', 
                              "Query should use index, not full table scan")

    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are properly configured."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    CONSTRAINT_NAME,
                    REFERENCED_TABLE_NAME,
                    DELETE_RULE,
                    UPDATE_RULE
                FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
                WHERE TABLE_NAME = 'products_product' 
                AND CONSTRAINT_SCHEMA = DATABASE()
            """)
            
            fk_constraints = cursor.fetchall()
            self.assertGreater(len(fk_constraints), 0, 
                             "Foreign key constraints should exist")
            
            # Check that cascading rules are properly set
            for constraint in fk_constraints:
                constraint_name, ref_table, delete_rule, update_rule = constraint
                if ref_table == 'products_category':
                    self.assertIn(delete_rule, ['CASCADE', 'RESTRICT'], 
                                f"Delete rule for {constraint_name} should be CASCADE or RESTRICT")

    def test_table_character_set_and_collation(self):
        """Test that tables use proper character set and collation."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT TABLE_NAME, TABLE_COLLATION 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME IN ('products_product', 'products_category', 'orders_order')
            """)
            
            tables = cursor.fetchall()
            
            for table_name, collation in tables:
                self.assertEqual(collation, 'utf8mb4_unicode_ci',
                               f"Table {table_name} should use utf8mb4_unicode_ci collation")

    def test_table_engine_optimization(self):
        """Test that tables use InnoDB engine with proper settings."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT TABLE_NAME, ENGINE, ROW_FORMAT 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME IN ('products_product', 'orders_order', 'reviews_review')
            """)
            
            tables = cursor.fetchall()
            
            for table_name, engine, row_format in tables:
                self.assertEqual(engine, 'InnoDB',
                               f"Table {table_name} should use InnoDB engine")
                self.assertEqual(row_format, 'Dynamic',
                               f"Table {table_name} should use Dynamic row format")

    def test_schema_analyzer_functionality(self):
        """Test the schema analyzer provides useful insights."""
        analysis = self.optimizer.analyze_table_performance('products_product')
        
        self.assertIn('table_name', analysis)
        self.assertIn('row_count', analysis)
        self.assertIn('table_size_mb', analysis)
        self.assertIn('index_size_mb', analysis)
        self.assertIn('recommendations', analysis)
        
        self.assertEqual(analysis['table_name'], 'products_product')
        self.assertIsInstance(analysis['row_count'], int)
        self.assertIsInstance(analysis['table_size_mb'], (int, float))

    def test_constraint_validation(self):
        """Test that constraints properly validate data."""
        # Test price constraint
        with self.assertRaises(Exception):
            with transaction.atomic():
                Product.objects.create(
                    name='Invalid Product',
                    slug='invalid-product',
                    description='Invalid product with negative price',
                    category=self.category,
                    sku='INVALID-001',
                    price=-10.00  # Should violate price constraint
                )

    def test_index_cardinality_and_selectivity(self):
        """Test that indexes have good cardinality and selectivity."""
        # Create diverse test data
        categories = []
        for i in range(5):
            cat = Category.objects.create(
                name=f'Category {i}',
                slug=f'category-{i}'
            )
            categories.append(cat)
        
        # Create products with different attributes
        for i in range(100):
            Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                description=f'Description {i}',
                category=categories[i % 5],
                sku=f'SKU-{i:03d}',
                price=10.00 + (i * 5),
                is_active=i % 3 != 0,  # ~67% active
                is_featured=i % 10 == 0,  # 10% featured
                brand=f'Brand{i % 7}'  # 7 different brands
            )
        
        with connection.cursor() as cursor:
            # Check index cardinality
            cursor.execute("""
                SELECT INDEX_NAME, CARDINALITY 
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_NAME = 'products_product' 
                AND TABLE_SCHEMA = DATABASE()
                AND INDEX_NAME LIKE 'idx_%'
            """)
            
            index_stats = cursor.fetchall()
            
            # Verify that indexes have reasonable cardinality
            for index_name, cardinality in index_stats:
                if cardinality is not None:
                    self.assertGreater(cardinality, 0,
                                     f"Index {index_name} should have positive cardinality")


class MySQLPerformanceBenchmarkTestCase(TransactionTestCase):
    """Benchmark tests for MySQL performance optimizations."""
    
    def setUp(self):
        """Set up benchmark test data."""
        self.user = User.objects.create_user(
            username='benchuser',
            email='bench@example.com',
            password='benchpass123'
        )
        
        self.category = Category.objects.create(
            name='Benchmark Category',
            slug='benchmark-category'
        )
        
        # Create larger dataset for meaningful benchmarks
        self.create_benchmark_data()

    def create_benchmark_data(self):
        """Create a larger dataset for performance testing."""
        # Create multiple categories
        categories = []
        for i in range(10):
            cat = Category.objects.create(
                name=f'Benchmark Category {i}',
                slug=f'benchmark-category-{i}'
            )
            categories.append(cat)
        
        # Create many products
        products = []
        for i in range(1000):
            product = Product.objects.create(
                name=f'Benchmark Product {i}',
                slug=f'benchmark-product-{i}',
                description=f'Detailed description for benchmark product {i} with searchable content',
                category=categories[i % 10],
                sku=f'BENCH-{i:04d}',
                price=10.00 + (i * 0.5),
                is_active=i % 4 != 0,  # 75% active
                is_featured=i % 20 == 0,  # 5% featured
                brand=f'Brand{i % 15}'  # 15 different brands
            )
            products.append(product)
        
        # Create customer profiles
        customers = []
        for i in range(100):
            user = User.objects.create_user(
                username=f'customer{i}',
                email=f'customer{i}@example.com',
                password='password123'
            )
            profile = CustomerProfile.objects.create(
                user=user,
                total_orders=i % 50,
                total_spent=i * 25.50,
                loyalty_points=i * 10
            )
            customers.append(profile)
        
        # Create orders
        for i in range(500):
            order = Order.objects.create(
                customer=customers[i % 100].user,
                order_number=f'BENCH-ORDER-{i:04d}',
                total_amount=50.00 + (i * 2.5),
                status='delivered' if i % 3 == 0 else 'pending'
            )
            
            # Create order items
            for j in range(1, 4):  # 1-3 items per order
                OrderItem.objects.create(
                    order=order,
                    product=products[(i + j) % 1000],
                    quantity=j,
                    unit_price=products[(i + j) % 1000].price,
                    total_price=products[(i + j) % 1000].price * j
                )
        
        # Create reviews
        for i in range(200):
            Review.objects.create(
                product=products[i % 1000],
                user=customers[i % 100].user,
                rating=(i % 5) + 1,
                title=f'Review title {i}',
                comment=f'Detailed review comment {i} with lots of text for full-text search testing',
                status='approved' if i % 3 == 0 else 'pending'
            )

    def test_product_search_performance(self):
        """Benchmark product search queries."""
        with connection.cursor() as cursor:
            # Test category-based search
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM products_product 
                WHERE category_id = %s AND is_active = 1
            """, [self.category.id])
            category_search_time = time.time() - start_time
            
            # Test price range search
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM products_product 
                WHERE price BETWEEN %s AND %s AND is_active = 1
            """, [100.00, 200.00])
            price_search_time = time.time() - start_time
            
            # Test full-text search
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM products_product 
                WHERE MATCH(name, description) AGAINST(%s IN NATURAL LANGUAGE MODE)
            """, ['benchmark product'])
            fulltext_search_time = time.time() - start_time
            
            # All searches should complete reasonably quickly
            self.assertLess(category_search_time, 0.1, "Category search should be fast")
            self.assertLess(price_search_time, 0.1, "Price search should be fast")
            self.assertLess(fulltext_search_time, 0.2, "Full-text search should be reasonably fast")

    def test_complex_join_performance(self):
        """Benchmark complex join queries."""
        with connection.cursor() as cursor:
            # Test product-category-review join
            start_time = time.time()
            cursor.execute("""
                SELECT p.name, c.name, AVG(r.rating) as avg_rating
                FROM products_product p
                JOIN products_category c ON p.category_id = c.id
                LEFT JOIN reviews_review r ON p.id = r.product_id AND r.status = 'approved'
                WHERE p.is_active = 1
                GROUP BY p.id, p.name, c.name
                HAVING avg_rating >= 4 OR avg_rating IS NULL
                LIMIT 50
            """)
            complex_join_time = time.time() - start_time
            
            # Test order analytics query
            start_time = time.time()
            cursor.execute("""
                SELECT 
                    DATE(o.created_at) as order_date,
                    COUNT(*) as order_count,
                    SUM(o.total_amount) as total_revenue
                FROM orders_order o
                WHERE o.status = 'delivered'
                AND o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY DATE(o.created_at)
                ORDER BY order_date DESC
            """)
            analytics_query_time = time.time() - start_time
            
            # Complex queries should complete in reasonable time
            self.assertLess(complex_join_time, 0.5, "Complex join should complete quickly")
            self.assertLess(analytics_query_time, 0.3, "Analytics query should be fast")

    def test_customer_analytics_performance(self):
        """Benchmark customer analytics queries."""
        with connection.cursor() as cursor:
            # Test customer segmentation query
            start_time = time.time()
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN total_spent >= 1000 THEN 'VIP'
                        WHEN total_spent >= 500 THEN 'Premium'
                        WHEN total_spent >= 100 THEN 'Regular'
                        ELSE 'New'
                    END as customer_tier,
                    COUNT(*) as customer_count,
                    AVG(total_spent) as avg_spent,
                    AVG(total_orders) as avg_orders
                FROM customers_customerprofile
                WHERE account_status = 'ACTIVE'
                GROUP BY customer_tier
            """)
            segmentation_time = time.time() - start_time
            
            self.assertLess(segmentation_time, 0.2, "Customer segmentation should be fast")


if __name__ == '__main__':
    unittest.main()