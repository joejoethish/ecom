"""
Comprehensive migration testing suite for SQLite to MySQL migration.
Tests migration scripts, data integrity, and rollback procedures.
"""
import os
import sqlite3
import tempfile
import unittest
import json
import shutil
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

from django.test import TestCase, override_settings
from django.conf import settings
from django.db import connections

from core.migration import (
    DatabaseMigrationService,
    MigrationValidator,
    MigrationProgress,
    ValidationResult,
    create_migration_service
)


class MigrationTestBase(TestCase):
    """Base class for migration tests with common setup"""
    
    def setUp(self):
        """Set up test environment with sample data"""
        # Create temporary SQLite database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create temporary directory for migration logs
        self.temp_log_dir = tempfile.mkdtemp()
        
        # Mock MySQL configuration
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db',
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': False,
            'raise_on_warnings': True
        }
        
        # Create comprehensive test database
        self._create_test_database()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        if os.path.exists(self.temp_log_dir):
            shutil.rmtree(self.temp_log_dir)
    
    def _create_test_database(self):
        """Create comprehensive test database with various data types and relationships"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                date_of_birth DATE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                profile_data TEXT  -- JSON data
            )
        ''')
        
        # Categories table with self-reference
        cursor.execute('''
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                description TEXT,
                parent_id INTEGER,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories (id)
            )
        ''')
        
        # Products table with foreign keys
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                description TEXT,
                short_description TEXT,
                price REAL NOT NULL,
                sale_price REAL,
                sku TEXT UNIQUE,
                stock_quantity INTEGER DEFAULT 0,
                weight REAL,
                dimensions TEXT,
                category_id INTEGER,
                created_by INTEGER,
                is_active BOOLEAN DEFAULT 1,
                featured BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,  -- JSON data
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                total_amount REAL NOT NULL,
                tax_amount REAL DEFAULT 0,
                shipping_amount REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                currency TEXT DEFAULT 'USD',
                payment_method TEXT,
                payment_status TEXT DEFAULT 'pending',
                shipping_address TEXT,  -- JSON data
                billing_address TEXT,   -- JSON data
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Order items table (many-to-many relationship)
        cursor.execute('''
            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                product_snapshot TEXT,  -- JSON data
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Reviews table
        cursor.execute('''
            CREATE TABLE reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                title TEXT,
                content TEXT,
                is_verified BOOLEAN DEFAULT 0,
                helpful_votes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE (product_id, user_id)
            )
        ''')
        
        # Insert comprehensive test data
        self._insert_test_data(cursor)
        
        conn.commit()
        conn.close()
    
    def _insert_test_data(self, cursor):
        """Insert comprehensive test data"""
        # Insert users
        users_data = [
            ('admin', 'admin@example.com', 'hashed_password_1', 'Admin', 'User', '1990-01-01', 1, '{"role": "admin", "preferences": {"theme": "dark"}}'),
            ('john_doe', 'john@example.com', 'hashed_password_2', 'John', 'Doe', '1985-05-15', 1, '{"role": "customer", "preferences": {"newsletter": true}}'),
            ('jane_smith', 'jane@example.com', 'hashed_password_3', 'Jane', 'Smith', '1992-08-22', 1, '{"role": "customer", "preferences": {"newsletter": false}}'),
            ('inactive_user', 'inactive@example.com', 'hashed_password_4', 'Inactive', 'User', '1988-12-10', 0, '{"role": "customer", "status": "suspended"}'),
        ]
        
        cursor.executemany('''
            INSERT INTO users (username, email, password_hash, first_name, last_name, date_of_birth, is_active, profile_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', users_data)
        
        # Insert categories (with parent-child relationships)
        categories_data = [
            ('Electronics', 'electronics', 'Electronic devices and accessories', None, 1),
            ('Computers', 'computers', 'Desktop and laptop computers', 1, 1),
            ('Smartphones', 'smartphones', 'Mobile phones and accessories', 1, 2),
            ('Books', 'books', 'Books and publications', None, 2),
            ('Fiction', 'fiction', 'Fiction books and novels', 4, 1),
            ('Non-Fiction', 'non-fiction', 'Educational and reference books', 4, 2),
            ('Clothing', 'clothing', 'Apparel and accessories', None, 3),
        ]
        
        cursor.executemany('''
            INSERT INTO categories (name, slug, description, parent_id, sort_order)
            VALUES (?, ?, ?, ?, ?)
        ''', categories_data)
        
        # Insert products
        products_data = [
            ('Gaming Laptop', 'gaming-laptop', 'High-performance gaming laptop with RTX graphics', 'Powerful laptop for gaming and work', 1299.99, 1199.99, 'LAPTOP-001', 10, 2.5, '35x25x2 cm', 2, 1, 1, 1, '{"brand": "TechCorp", "warranty": "2 years", "specs": {"cpu": "Intel i7", "ram": "16GB", "storage": "1TB SSD"}}'),
            ('Business Laptop', 'business-laptop', 'Professional laptop for business use', 'Reliable laptop for office work', 899.99, None, 'LAPTOP-002', 15, 2.0, '33x23x1.8 cm', 2, 1, 1, 0, '{"brand": "BizTech", "warranty": "3 years", "specs": {"cpu": "Intel i5", "ram": "8GB", "storage": "512GB SSD"}}'),
            ('Smartphone Pro', 'smartphone-pro', 'Latest flagship smartphone', 'Premium smartphone with advanced features', 999.99, 899.99, 'PHONE-001', 25, 0.2, '15x7x0.8 cm', 3, 1, 1, 1, '{"brand": "PhoneCorp", "warranty": "1 year", "specs": {"screen": "6.7 inch", "camera": "108MP", "battery": "5000mAh"}}'),
            ('Python Programming', 'python-programming', 'Complete guide to Python programming', 'Learn Python from basics to advanced', 49.99, 39.99, 'BOOK-001', 50, 0.8, '23x15x3 cm', 5, 2, 1, 0, '{"author": "John Python", "pages": 500, "isbn": "978-1234567890", "publisher": "TechBooks"}'),
            ('Data Science Handbook', 'data-science-handbook', 'Comprehensive data science reference', 'Essential guide for data scientists', 79.99, None, 'BOOK-002', 30, 1.2, '24x16x4 cm', 6, 2, 1, 1, '{"author": "Jane Data", "pages": 750, "isbn": "978-0987654321", "publisher": "SciencePress"}'),
            ('Cotton T-Shirt', 'cotton-t-shirt', 'Comfortable cotton t-shirt', 'High-quality cotton t-shirt in various colors', 19.99, 14.99, 'SHIRT-001', 100, 0.2, 'Size: M', 7, 3, 1, 0, '{"material": "100% cotton", "colors": ["red", "blue", "green"], "sizes": ["S", "M", "L", "XL"]}'),
        ]
        
        cursor.executemany('''
            INSERT INTO products (name, slug, description, short_description, price, sale_price, sku, stock_quantity, weight, dimensions, category_id, created_by, is_active, featured, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', products_data)
        
        # Insert orders
        orders_data = [
            ('ORD-2024-001', 2, 'completed', 1349.98, 107.99, 15.00, 50.00, 'USD', 'credit_card', 'paid', '{"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"}', '{"street": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"}', 'First order'),
            ('ORD-2024-002', 3, 'processing', 949.98, 75.99, 10.00, 0.00, 'USD', 'paypal', 'paid', '{"street": "456 Oak Ave", "city": "Somewhere", "state": "NY", "zip": "67890"}', '{"street": "456 Oak Ave", "city": "Somewhere", "state": "NY", "zip": "67890"}', None),
            ('ORD-2024-003', 2, 'pending', 39.99, 3.20, 5.00, 10.00, 'USD', 'bank_transfer', 'pending', '{"street": "789 Pine Rd", "city": "Elsewhere", "state": "TX", "zip": "54321"}', '{"street": "789 Pine Rd", "city": "Elsewhere", "state": "TX", "zip": "54321"}', 'Gift order'),
        ]
        
        cursor.executemany('''
            INSERT INTO orders (order_number, user_id, status, total_amount, tax_amount, shipping_amount, discount_amount, currency, payment_method, payment_status, shipping_address, billing_address, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', orders_data)
        
        # Insert order items
        order_items_data = [
            (1, 1, 1, 1199.99, 1199.99, '{"product_name": "Gaming Laptop", "sku": "LAPTOP-001", "price_at_time": 1199.99}'),
            (1, 4, 1, 39.99, 39.99, '{"product_name": "Python Programming", "sku": "BOOK-001", "price_at_time": 39.99}'),
            (2, 3, 1, 899.99, 899.99, '{"product_name": "Smartphone Pro", "sku": "PHONE-001", "price_at_time": 899.99}'),
            (2, 6, 3, 14.99, 44.97, '{"product_name": "Cotton T-Shirt", "sku": "SHIRT-001", "price_at_time": 14.99}'),
            (3, 4, 1, 39.99, 39.99, '{"product_name": "Python Programming", "sku": "BOOK-001", "price_at_time": 39.99}'),
        ]
        
        cursor.executemany('''
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price, product_snapshot)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', order_items_data)
        
        # Insert reviews
        reviews_data = [
            (1, 2, 5, 'Excellent laptop!', 'This gaming laptop exceeded my expectations. Great performance and build quality.', 1, 15),
            (1, 3, 4, 'Good but expensive', 'Great laptop but a bit pricey. Worth it for the performance though.', 0, 8),
            (3, 2, 5, 'Amazing phone!', 'Best smartphone I have ever owned. Camera quality is outstanding.', 1, 22),
            (4, 3, 5, 'Great book for beginners', 'Perfect introduction to Python programming. Well written and easy to follow.', 1, 12),
            (5, 2, 4, 'Comprehensive guide', 'Very detailed book on data science. Some parts are quite advanced.', 1, 7),
            (6, 3, 3, 'Decent quality', 'Good t-shirt for the price. Material is comfortable but could be better.', 0, 3),
        ]
        
        cursor.executemany('''
            INSERT INTO reviews (product_id, user_id, rating, title, content, is_verified, helpful_votes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', reviews_data)


class TestMigrationScriptsUnit(MigrationTestBase):
    """Unit tests for migration scripts and data integrity"""
    
    def test_migration_service_initialization(self):
        """Test migration service initialization with various configurations"""
        # Test default initialization
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        self.assertEqual(service.sqlite_path, self.temp_db.name)
        self.assertEqual(service.mysql_config, self.mysql_config)
        self.assertIsInstance(service.migration_progress, dict)
        self.assertIsInstance(service.validation_results, dict)
        self.assertIsInstance(service.rollback_data, dict)
        self.assertIsNone(service.sqlite_conn)
        self.assertIsNone(service.mysql_conn)
    
    def test_sqlite_table_discovery(self):
        """Test SQLite table discovery and schema analysis"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to SQLite
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            # Test table discovery
            tables = service.get_sqlite_tables()
            expected_tables = ['users', 'categories', 'products', 'orders', 'order_items', 'reviews']
            
            self.assertEqual(len(tables), len(expected_tables))
            for table in expected_tables:
                self.assertIn(table, tables)
            
            # Test schema analysis for each table
            for table_name in tables:
                schema = service.get_table_schema(table_name)
                self.assertIsInstance(schema, list)
                self.assertGreater(len(schema), 0)
                
                # Verify schema structure
                for column in schema:
                    self.assertIn('name', column)
                    self.assertIn('type', column)
                    self.assertIn('notnull', column)
                    self.assertIn('pk', column)
                    self.assertIsInstance(column['notnull'], bool)
                    self.assertIsInstance(column['pk'], bool)
        
        finally:
            service.sqlite_conn.close()
    
    def test_data_type_conversion_comprehensive(self):
        """Test comprehensive SQLite to MySQL data type conversion"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        test_cases = [
            # Basic types
            ('INTEGER', 'INT'),
            ('TEXT', 'TEXT'),
            ('REAL', 'DOUBLE'),
            ('BLOB', 'LONGBLOB'),
            ('NUMERIC', 'DECIMAL(10,2)'),
            
            # Parameterized types
            ('VARCHAR(255)', 'VARCHAR(255)'),
            ('CHAR(10)', 'CHAR(10)'),
            ('VARCHAR(100)', 'VARCHAR(100)'),
            
            # Special types
            ('BOOLEAN', 'TINYINT(1)'),
            ('DATETIME', 'DATETIME'),
            ('DATE', 'DATE'),
            ('TIME', 'TIME'),
            ('TIMESTAMP', 'TIMESTAMP'),
            
            # Case variations
            ('integer', 'INT'),
            ('text', 'TEXT'),
            ('varchar(50)', 'VARCHAR(50)'),
            
            # Unknown types (fallback)
            ('UNKNOWN_TYPE', 'TEXT'),
            ('CUSTOM_TYPE', 'TEXT'),
        ]
        
        for sqlite_type, expected_mysql_type in test_cases:
            with self.subTest(sqlite_type=sqlite_type):
                result = service.convert_sqlite_to_mysql_type(sqlite_type)
                self.assertEqual(result, expected_mysql_type)
    
    @patch('mysql.connector.connect')
    def test_mysql_table_creation_comprehensive(self, mock_mysql_connect):
        """Test comprehensive MySQL table creation with various column types and constraints"""
        # Mock MySQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        service.mysql_conn = mock_conn
        
        # Test complex table schema
        columns = [
            {'name': 'id', 'type': 'INTEGER', 'notnull': True, 'default_value': None, 'pk': True},
            {'name': 'name', 'type': 'VARCHAR(255)', 'notnull': True, 'default_value': None, 'pk': False},
            {'name': 'email', 'type': 'TEXT', 'notnull': False, 'default_value': None, 'pk': False},
            {'name': 'age', 'type': 'INTEGER', 'notnull': False, 'default_value': '0', 'pk': False},
            {'name': 'is_active', 'type': 'BOOLEAN', 'notnull': False, 'default_value': '1', 'pk': False},
            {'name': 'created_at', 'type': 'TIMESTAMP', 'notnull': False, 'default_value': 'CURRENT_TIMESTAMP', 'pk': False},
            {'name': 'price', 'type': 'REAL', 'notnull': True, 'default_value': None, 'pk': False},
        ]
        
        result = service.create_mysql_table('test_table', columns)
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Verify SQL structure
        sql_call = mock_cursor.execute.call_args[0][0]
        
        # Check table creation
        self.assertIn('CREATE TABLE IF NOT EXISTS `test_table`', sql_call)
        
        # Check column definitions
        self.assertIn('`id` INT NOT NULL', sql_call)
        self.assertIn('`name` VARCHAR(255) NOT NULL', sql_call)
        self.assertIn('`email` TEXT', sql_call)
        self.assertIn('`age` INT DEFAULT \'0\'', sql_call)
        self.assertIn('`is_active` TINYINT(1) DEFAULT \'1\'', sql_call)
        self.assertIn('`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP', sql_call)
        self.assertIn('`price` DOUBLE NOT NULL', sql_call)
        
        # Check primary key
        self.assertIn('PRIMARY KEY (`id`)', sql_call)
        
        # Check table options
        self.assertIn('ENGINE=InnoDB', sql_call)
        self.assertIn('DEFAULT CHARSET=utf8mb4', sql_call)
        self.assertIn('COLLATE=utf8mb4_unicode_ci', sql_call)
    
    def test_migration_progress_tracking(self):
        """Test migration progress tracking functionality"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Test progress creation
        start_time = datetime.now()
        progress = MigrationProgress(
            table_name='test_table',
            total_records=1000,
            migrated_records=250,
            start_time=start_time
        )
        
        # Test progress calculations
        self.assertEqual(progress.progress_percentage, 25.0)
        self.assertEqual(progress.status, 'pending')
        self.assertIsNone(progress.end_time)
        self.assertIsNone(progress.duration_seconds)
        
        # Test progress completion
        end_time = start_time + timedelta(seconds=30)
        progress.end_time = end_time
        progress.status = 'completed'
        progress.migrated_records = 1000
        
        self.assertEqual(progress.progress_percentage, 100.0)
        self.assertEqual(progress.status, 'completed')
        self.assertEqual(progress.duration_seconds, 30.0)
        
        # Test edge cases
        empty_progress = MigrationProgress(
            table_name='empty_table',
            total_records=0,
            migrated_records=0,
            start_time=start_time
        )
        self.assertEqual(empty_progress.progress_percentage, 100.0)
    
    def test_validation_result_analysis(self):
        """Test validation result analysis and reporting"""
        validation_time = datetime.now()
        
        # Test successful validation
        success_result = ValidationResult(
            table_name='test_table',
            source_count=100,
            target_count=100,
            is_valid=True,
            missing_records=[],
            extra_records=[],
            data_mismatches=[],
            validation_time=validation_time
        )
        
        self.assertTrue(success_result.is_valid)
        self.assertEqual(success_result.source_count, success_result.target_count)
        self.assertEqual(len(success_result.missing_records), 0)
        self.assertEqual(len(success_result.extra_records), 0)
        self.assertEqual(len(success_result.data_mismatches), 0)
        
        # Test failed validation with issues
        failed_result = ValidationResult(
            table_name='problem_table',
            source_count=100,
            target_count=95,
            is_valid=False,
            missing_records=[1, 2, 3, 4, 5],
            extra_records=[],
            data_mismatches=[
                {'record_id': 10, 'field': 'name', 'source_value': 'John', 'target_value': 'Jon'},
                {'record_id': 15, 'field': 'email', 'source_value': 'test@example.com', 'target_value': None}
            ],
            validation_time=validation_time
        )
        
        self.assertFalse(failed_result.is_valid)
        self.assertNotEqual(failed_result.source_count, failed_result.target_count)
        self.assertEqual(len(failed_result.missing_records), 5)
        self.assertEqual(len(failed_result.data_mismatches), 2)
    
    def test_rollback_data_management(self):
        """Test rollback data management and cleanup"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Test initial state
        self.assertEqual(len(service.rollback_data), 0)
        
        # Test adding rollback data
        timestamp = int(datetime.now().timestamp())
        rollback_info = {
            'backup_table': f'users_rollback_{timestamp}',
            'created_at': datetime.now().isoformat(),
            'original_table': 'users'
        }
        
        service.rollback_data['users'] = rollback_info
        
        self.assertEqual(len(service.rollback_data), 1)
        self.assertIn('users', service.rollback_data)
        self.assertEqual(service.rollback_data['users']['original_table'], 'users')
        
        # Test multiple rollback points
        service.rollback_data['products'] = {
            'backup_table': f'products_rollback_{timestamp + 1}',
            'created_at': datetime.now().isoformat(),
            'original_table': 'products'
        }
        
        self.assertEqual(len(service.rollback_data), 2)
        
        # Test rollback data serialization
        rollback_json = json.dumps(service.rollback_data, default=str)
        restored_data = json.loads(rollback_json)
        
        self.assertEqual(len(restored_data), 2)
        self.assertIn('users', restored_data)
        self.assertIn('products', restored_data)


class TestMigrationIntegration(MigrationTestBase):
    """Integration tests for complete migration workflow"""
    
    @patch('mysql.connector.connect')
    def test_complete_migration_workflow(self, mock_mysql_connect):
        """Test complete migration workflow from start to finish"""
        # Mock MySQL connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        # Mock successful operations
        mock_cursor.fetchone.side_effect = [
            (4,),  # users count
            (7,),  # categories count  
            (6,),  # products count
            (3,),  # orders count
            (5,),  # order_items count
            (6,),  # reviews count
            (4,),  # users validation count
            (7,),  # categories validation count
            (6,),  # products validation count
            (3,),  # orders validation count
            (5,),  # order_items validation count
            (6,),  # reviews validation count
        ]
        
        # Mock table data for migration
        mock_cursor.fetchall.side_effect = [
            # Users data
            [(1, 'admin', 'admin@example.com', 'hash1', 'Admin', 'User', '1990-01-01', 1, '2024-01-01 00:00:00', '2024-01-01 00:00:00', '{"role": "admin"}')],
            # Categories data  
            [(1, 'Electronics', 'electronics', 'Electronic devices', None, 1, 1, '2024-01-01 00:00:00')],
            # Products data
            [(1, 'Laptop', 'laptop', 'Gaming laptop', 'High-performance laptop', 1299.99, 1199.99, 'LAPTOP-001', 10, 2.5, '35x25x2 cm', 1, 1, 1, 1, '2024-01-01 00:00:00', '2024-01-01 00:00:00', '{"brand": "TechCorp"}')],
            # Orders data
            [(1, 'ORD-001', 1, 'completed', 1199.99, 95.99, 15.00, 0.00, 'USD', 'credit_card', 'paid', '{"address": "123 Main St"}', '{"address": "123 Main St"}', None, '2024-01-01 00:00:00', '2024-01-01 00:00:00')],
            # Order items data
            [(1, 1, 1, 1, 1199.99, 1199.99, '{"product": "Laptop"}', '2024-01-01 00:00:00')],
            # Reviews data
            [(1, 1, 1, 5, 'Great!', 'Excellent product', 1, 10, '2024-01-01 00:00:00', '2024-01-01 00:00:00')],
        ]
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Mock the migration log path
        with patch.object(service, 'migration_log_path', Path(self.temp_log_dir)):
            # Run complete migration
            results = service.migrate_all_tables(batch_size=10, create_rollback=True)
            
            # Verify results structure
            self.assertIsInstance(results, dict)
            self.assertIn('total_tables', results)
            self.assertIn('successful_migrations', results)
            self.assertIn('failed_migrations', results)
            self.assertIn('successful_validations', results)
            self.assertIn('failed_validations', results)
            self.assertIn('start_time', results)
            self.assertIn('end_time', results)
            self.assertIn('total_duration', results)
            self.assertIn('tables', results)
            self.assertIn('log_file', results)
            
            # Verify migration success
            self.assertEqual(results['total_tables'], 6)
            self.assertGreaterEqual(results['successful_migrations'], 0)
            self.assertIsInstance(results['total_duration'], float)
            
            # Verify table-specific results
            expected_tables = ['users', 'categories', 'products', 'orders', 'order_items', 'reviews']
            for table_name in expected_tables:
                self.assertIn(table_name, results['tables'])
                table_result = results['tables'][table_name]
                self.assertIn('migration_status', table_result)
                self.assertIn('validation_status', table_result)
            
            # Verify log file creation
            self.assertTrue(os.path.exists(results['log_file']))
            
            # Verify log file content
            with open(results['log_file'], 'r') as f:
                log_data = json.load(f)
                
            self.assertIn('migration_timestamp', log_data)
            self.assertIn('sqlite_path', log_data)
            self.assertIn('mysql_config', log_data)
            self.assertIn('migration_progress', log_data)
            self.assertIn('validation_results', log_data)
            self.assertIn('rollback_data', log_data)
    
    @patch('mysql.connector.connect')
    def test_migration_with_errors_and_recovery(self, mock_mysql_connect):
        """Test migration workflow with errors and recovery mechanisms"""
        # Mock MySQL connection with intermittent failures
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        # Simulate failure on first table, success on others
        mock_cursor.execute.side_effect = [
            Exception("Connection timeout"),  # First table fails
            None,  # Second table succeeds
            None,  # Continue with other operations
        ] + [None] * 50  # Remaining operations succeed
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to databases
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        service.mysql_conn = mock_conn
        
        try:
            # Test individual table migration with error
            tables = service.get_sqlite_tables()
            first_table = tables[0]
            
            # This should fail due to mocked exception
            progress = service.migrate_table_data(first_table, batch_size=10)
            
            self.assertEqual(progress.status, 'failed')
            self.assertIsNotNone(progress.error_message)
            self.assertIn(first_table, service.migration_progress)
            
            # Test recovery by resetting mock
            mock_cursor.execute.side_effect = None
            mock_cursor.fetchone.return_value = (0,)  # Empty table
            
            # Retry migration should succeed
            progress_retry = service.migrate_table_data(first_table, batch_size=10)
            self.assertEqual(progress_retry.status, 'completed')
            
        finally:
            service.disconnect_databases()
    
    @patch('mysql.connector.connect')
    def test_migration_data_integrity_validation(self, mock_mysql_connect):
        """Test comprehensive data integrity validation during migration"""
        # Mock MySQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to databases
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        service.mysql_conn = mock_conn
        
        try:
            # Test validation with matching counts
            mock_cursor.fetchone.side_effect = [
                (4,),  # MySQL count
                (1,), (2,), (3,), (4,)  # Primary key values
            ]
            
            # Mock SQLite data for comparison
            service.sqlite_conn.execute = Mock()
            service.sqlite_conn.execute().fetchone.return_value = (4,)  # SQLite count
            service.sqlite_conn.execute().fetchall.return_value = [(1,), (2,), (3,), (4,)]  # Primary keys
            
            validation = service.validate_migration('users')
            
            self.assertIsInstance(validation, ValidationResult)
            self.assertEqual(validation.table_name, 'users')
            self.assertEqual(validation.source_count, 4)
            self.assertEqual(validation.target_count, 4)
            self.assertTrue(validation.is_valid)
            self.assertEqual(len(validation.missing_records), 0)
            self.assertEqual(len(validation.extra_records), 0)
            
            # Test validation with mismatched counts
            mock_cursor.fetchone.side_effect = [
                (3,),  # MySQL count (missing 1 record)
                (1,), (2,), (4,)  # Primary key values (missing 3)
            ]
            
            validation_failed = service.validate_migration('users')
            
            self.assertFalse(validation_failed.is_valid)
            self.assertEqual(validation_failed.source_count, 4)
            self.assertEqual(validation_failed.target_count, 3)
            self.assertEqual(len(validation_failed.missing_records), 1)
            self.assertIn(3, validation_failed.missing_records)
            
        finally:
            service.disconnect_databases()
    
    def test_migration_performance_monitoring(self):
        """Test migration performance monitoring and metrics collection"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Test performance tracking
        start_time = datetime.now()
        
        # Simulate migration progress over time
        progress = MigrationProgress(
            table_name='performance_test',
            total_records=10000,
            migrated_records=0,
            start_time=start_time
        )
        
        # Simulate batch processing
        batch_sizes = [1000, 2000, 3000, 4000]
        for i, batch_size in enumerate(batch_sizes):
            progress.migrated_records += batch_size
            
            # Verify progress calculations
            expected_percentage = (progress.migrated_records / progress.total_records) * 100
            self.assertEqual(progress.progress_percentage, expected_percentage)
        
        # Complete migration
        progress.end_time = start_time + timedelta(seconds=45)
        progress.status = 'completed'
        
        # Verify final metrics
        self.assertEqual(progress.progress_percentage, 100.0)
        self.assertEqual(progress.duration_seconds, 45.0)
        self.assertEqual(progress.status, 'completed')
        
        # Test performance analysis
        records_per_second = progress.total_records / progress.duration_seconds
        self.assertAlmostEqual(records_per_second, 222.22, places=1)


class TestMigrationRollback(MigrationTestBase):
    """Test rollback testing and recovery procedures"""
    
    @patch('mysql.connector.connect')
    def test_rollback_point_creation(self, mock_mysql_connect):
        """Test creation of rollback points before migration"""
        # Mock MySQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        service.mysql_conn = mock_conn
        
        # Test rollback point creation
        table_name = 'users'
        result = service.create_rollback_point(table_name)
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Verify rollback data was stored
        self.assertIn(table_name, service.rollback_data)
        rollback_info = service.rollback_data[table_name]
        
        self.assertIn('backup_table', rollback_info)
        self.assertIn('created_at', rollback_info)
        self.assertIn('original_table', rollback_info)
        self.assertEqual(rollback_info['original_table'], table_name)
        self.assertTrue(rollback_info['backup_table'].startswith(f'{table_name}_rollback_'))
        
        # Verify SQL command structure
        sql_call = mock_cursor.execute.call_args[0][0]
        self.assertIn('CREATE TABLE', sql_call)
        self.assertIn('AS SELECT * FROM', sql_call)
        self.assertIn(f'`{table_name}`', sql_call)
    
    @patch('mysql.connector.connect')
    def test_rollback_execution(self, mock_mysql_connect):
        """Test rollback execution and data restoration"""
        # Mock MySQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        service.mysql_conn = mock_conn
        
        # Set up rollback data
        table_name = 'users'
        backup_table = f'{table_name}_rollback_1234567890'
        service.rollback_data[table_name] = {
            'backup_table': backup_table,
            'created_at': datetime.now().isoformat(),
            'original_table': table_name
        }
        
        # Test rollback execution
        result = service.rollback_table(table_name)
        
        self.assertTrue(result)
        mock_conn.commit.assert_called_once()
        
        # Verify rollback SQL commands
        expected_calls = [
            call('START TRANSACTION'),
            call(f'DELETE FROM `{table_name}`'),
            call(f'INSERT INTO `{table_name}` SELECT * FROM `{backup_table}`')
        ]
        
        actual_calls = mock_cursor.execute.call_args_list
        for expected_call in expected_calls:
            self.assertIn(expected_call, actual_calls)
    
    @patch('mysql.connector.connect')
    def test_rollback_failure_handling(self, mock_mysql_connect):
        """Test rollback failure handling and error recovery"""
        # Mock MySQL connection with failure
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        # Simulate rollback failure
        mock_cursor.execute.side_effect = Exception("Rollback failed")
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        service.mysql_conn = mock_conn
        
        # Set up rollback data
        table_name = 'users'
        service.rollback_data[table_name] = {
            'backup_table': f'{table_name}_rollback_1234567890',
            'created_at': datetime.now().isoformat(),
            'original_table': table_name
        }
        
        # Test rollback failure
        result = service.rollback_table(table_name)
        
        self.assertFalse(result)
        mock_conn.rollback.assert_called_once()
        
        # Test rollback with missing rollback point
        result_missing = service.rollback_table('nonexistent_table')
        self.assertFalse(result_missing)
    
    @patch('mysql.connector.connect')
    def test_rollback_cleanup(self, mock_mysql_connect):
        """Test rollback point cleanup and maintenance"""
        # Mock MySQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        service.mysql_conn = mock_conn
        
        # Set up multiple rollback points
        tables = ['users', 'products', 'orders']
        for table_name in tables:
            service.rollback_data[table_name] = {
                'backup_table': f'{table_name}_rollback_1234567890',
                'created_at': datetime.now().isoformat(),
                'original_table': table_name
            }
        
        # Test cleanup of specific table
        result = service.cleanup_rollback_points('users')
        
        self.assertTrue(result)
        self.assertNotIn('users', service.rollback_data)
        self.assertIn('products', service.rollback_data)
        self.assertIn('orders', service.rollback_data)
        
        # Verify DROP TABLE command
        drop_calls = [call for call in mock_cursor.execute.call_args_list 
                     if 'DROP TABLE' in str(call)]
        self.assertEqual(len(drop_calls), 1)
        
        # Test cleanup of all tables
        result_all = service.cleanup_rollback_points()
        
        self.assertTrue(result_all)
        self.assertEqual(len(service.rollback_data), 0)
        
        # Verify all backup tables were dropped
        all_drop_calls = [call for call in mock_cursor.execute.call_args_list 
                         if 'DROP TABLE' in str(call)]
        self.assertEqual(len(all_drop_calls), 3)  # 1 from specific + 2 from all
    
    def test_rollback_data_persistence(self):
        """Test rollback data persistence and recovery"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Create rollback data
        rollback_data = {
            'users': {
                'backup_table': 'users_rollback_1234567890',
                'created_at': '2024-01-01T12:00:00',
                'original_table': 'users'
            },
            'products': {
                'backup_table': 'products_rollback_1234567891',
                'created_at': '2024-01-01T12:01:00',
                'original_table': 'products'
            }
        }
        
        service.rollback_data = rollback_data
        
        # Test log saving with rollback data
        with patch.object(service, 'migration_log_path', Path(self.temp_log_dir)):
            log_file = service.save_migration_log()
            
            # Verify log file exists
            self.assertTrue(os.path.exists(log_file))
            
            # Verify rollback data in log
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            
            self.assertIn('rollback_data', log_data)
            self.assertEqual(len(log_data['rollback_data']), 2)
            self.assertIn('users', log_data['rollback_data'])
            self.assertIn('products', log_data['rollback_data'])
            
            # Verify rollback data structure
            for table_name, rollback_info in log_data['rollback_data'].items():
                self.assertIn('backup_table', rollback_info)
                self.assertIn('created_at', rollback_info)
                self.assertIn('original_table', rollback_info)
                self.assertEqual(rollback_info['original_table'], table_name)


class TestMigrationValidator(MigrationTestBase):
    """Test MigrationValidator functionality"""
    
    @patch('mysql.connector.connect')
    def test_schema_compatibility_validation(self, mock_mysql_connect):
        """Test comprehensive schema compatibility validation"""
        # Mock MySQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        # Mock MySQL DESCRIBE result for users table
        mock_cursor.fetchall.return_value = [
            ('id', 'int(11)', 'NO', 'PRI', None, 'auto_increment'),
            ('username', 'text', 'NO', '', None, ''),
            ('email', 'text', 'NO', '', None, ''),
            ('password_hash', 'text', 'NO', '', None, ''),
            ('first_name', 'text', 'YES', '', None, ''),
            ('last_name', 'text', 'YES', '', None, ''),
            ('date_of_birth', 'date', 'YES', '', None, ''),
            ('is_active', 'tinyint(1)', 'YES', '', '1', ''),
            ('created_at', 'timestamp', 'YES', '', 'CURRENT_TIMESTAMP', ''),
            ('updated_at', 'timestamp', 'YES', '', 'CURRENT_TIMESTAMP', ''),
            ('profile_data', 'text', 'YES', '', None, ''),
        ]
        
        # Create migration service and validator
        migration_service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        migration_service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        migration_service.sqlite_conn.row_factory = sqlite3.Row
        migration_service.mysql_conn = mock_conn
        
        validator = MigrationValidator(migration_service)
        
        try:
            result = validator.validate_schema_compatibility('users')
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            self.assertIn('table_name', result)
            self.assertIn('is_compatible', result)
            self.assertIn('issues', result)
            self.assertIn('sqlite_columns', result)
            self.assertIn('mysql_columns', result)
            
            self.assertEqual(result['table_name'], 'users')
            
            # For this test, we expect compatibility since we mocked matching schema
            if result['is_compatible']:
                self.assertEqual(len(result['issues']), 0)
            else:
                # If there are issues, they should be documented
                self.assertIsInstance(result['issues'], list)
                for issue in result['issues']:
                    self.assertIsInstance(issue, str)
                    
        finally:
            migration_service.sqlite_conn.close()
    
    @patch('mysql.connector.connect')
    def test_data_integrity_validation(self, mock_mysql_connect):
        """Test comprehensive data integrity validation"""
        # Mock MySQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        # Create migration service and validator
        migration_service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        migration_service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        migration_service.sqlite_conn.row_factory = sqlite3.Row
        migration_service.mysql_conn = mock_conn
        
        validator = MigrationValidator(migration_service)
        
        try:
            # Mock data for integrity validation
            mock_cursor.fetchall.side_effect = [
                # Sample records from MySQL
                [(1, 'admin', 'admin@example.com'), (2, 'john_doe', 'john@example.com')],
                # Primary key values for comparison
                [(1,), (2,), (3,), (4,)]
            ]
            
            result = validator.validate_data_integrity('users', sample_size=5)
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            self.assertIn('table_name', result)
            self.assertIn('is_valid', result)
            self.assertIn('validated_records', result)
            self.assertIn('total_records', result)
            self.assertIn('error_rate', result)
            self.assertIn('integrity_issues', result)
            
            self.assertEqual(result['table_name'], 'users')
            self.assertIsInstance(result['is_valid'], bool)
            self.assertIsInstance(result['validated_records'], int)
            self.assertIsInstance(result['error_rate'], float)
            self.assertIsInstance(result['integrity_issues'], list)
            
        finally:
            migration_service.sqlite_conn.close()


if __name__ == '__main__':
    unittest.main()