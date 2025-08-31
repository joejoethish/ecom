"""
Integration tests for complete migration workflow.
Tests end-to-end migration scenarios with real database operations.
"""
import os
import sqlite3
import tempfile
import unittest
import json
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

from django.test import TestCase, TransactionTestCase
from django.conf import settings
from django.db import connections

from core.migration import (
    DatabaseMigrationService,
    MigrationValidator,
    create_migration_service
)
from scripts.batch_migration import BatchMigrationManager


class MigrationWorkflowIntegrationTest(TransactionTestCase):
    """Integration tests for complete migration workflow"""
    
    def setUp(self):
        """Set up integration test environment"""
        # Create temporary SQLite database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create temporary directories
        self.temp_log_dir = tempfile.mkdtemp()
        self.temp_config_dir = tempfile.mkdtemp()
        
        # Create comprehensive test database
        self._create_comprehensive_test_database()
        
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
    
    def tearDown(self):
        """Clean up integration test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        if os.path.exists(self.temp_log_dir):
            shutil.rmtree(self.temp_log_dir)
            
        if os.path.exists(self.temp_config_dir):
            shutil.rmtree(self.temp_config_dir)
    
    def _create_comprehensive_test_database(self):
        """Create comprehensive test database with realistic data"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create realistic e-commerce schema
        
        # Users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                date_of_birth DATE,
                is_active BOOLEAN DEFAULT 1,
                is_staff BOOLEAN DEFAULT 0,
                date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                profile_data TEXT  -- JSON
            )
        ''')
        
        # Categories table with hierarchy
        cursor.execute('''
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                description TEXT,
                parent_id INTEGER,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                image_url TEXT,
                meta_title TEXT,
                meta_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories (id)
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                description TEXT,
                short_description TEXT,
                price REAL NOT NULL,
                sale_price REAL,
                cost_price REAL,
                sku TEXT UNIQUE,
                barcode TEXT,
                stock_quantity INTEGER DEFAULT 0,
                min_stock_level INTEGER DEFAULT 0,
                weight REAL,
                dimensions TEXT,
                category_id INTEGER,
                brand_id INTEGER,
                created_by INTEGER,
                is_active BOOLEAN DEFAULT 1,
                is_featured BOOLEAN DEFAULT 0,
                is_digital BOOLEAN DEFAULT 0,
                requires_shipping BOOLEAN DEFAULT 1,
                tax_class TEXT DEFAULT 'standard',
                meta_title TEXT,
                meta_description TEXT,
                search_keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                attributes TEXT,  -- JSON
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT NOT NULL UNIQUE,
                user_id INTEGER,
                guest_email TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                payment_status TEXT DEFAULT 'pending',
                fulfillment_status TEXT DEFAULT 'unfulfilled',
                currency TEXT DEFAULT 'USD',
                subtotal REAL NOT NULL,
                tax_amount REAL DEFAULT 0,
                shipping_amount REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                total_amount REAL NOT NULL,
                payment_method TEXT,
                payment_reference TEXT,
                shipping_method TEXT,
                tracking_number TEXT,
                notes TEXT,
                internal_notes TEXT,
                billing_address TEXT,   -- JSON
                shipping_address TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                shipped_at TIMESTAMP,
                delivered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Order items table
        cursor.execute('''
            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_variant_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                tax_amount REAL DEFAULT 0,
                product_snapshot TEXT,  -- JSON
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
                user_id INTEGER,
                guest_name TEXT,
                guest_email TEXT,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                title TEXT,
                content TEXT,
                pros TEXT,
                cons TEXT,
                is_verified BOOLEAN DEFAULT 0,
                is_approved BOOLEAN DEFAULT 0,
                helpful_votes INTEGER DEFAULT 0,
                unhelpful_votes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Inventory movements table
        cursor.execute('''
            CREATE TABLE inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,  -- 'in', 'out', 'adjustment'
                quantity INTEGER NOT NULL,
                reference_type TEXT,  -- 'order', 'return', 'adjustment', 'restock'
                reference_id INTEGER,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Insert comprehensive test data
        self._insert_comprehensive_test_data(cursor)
        
        conn.commit()
        conn.close()
    
    def _insert_comprehensive_test_data(self, cursor):
        """Insert comprehensive test data"""
        # Insert users (50 users)
        users_data = []
        for i in range(50):
            users_data.append((
                f'user_{i:03d}',
                f'user{i:03d}@example.com',
                f'hashed_password_{i}',
                f'FirstName{i}',
                f'LastName{i}',
                f'+1-555-{i:04d}',
                f'199{i % 10}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
                1 if i % 10 != 0 else 0,  # 90% active users
                1 if i < 5 else 0,  # First 5 are staff
                f'2024-01-{(i % 30) + 1:02d} 10:00:00',
                f'2024-07-{(i % 30) + 1:02d} 15:30:00' if i % 3 == 0 else None,
                json.dumps({
                    'preferences': {'newsletter': i % 2 == 0, 'theme': 'light' if i % 2 == 0 else 'dark'},
                    'address': {'country': 'US', 'state': f'State{i % 50}'},
                    'loyalty_points': i * 10
                })
            ))
        
        cursor.executemany('''
            INSERT INTO users (username, email, password_hash, first_name, last_name, phone, 
                             date_of_birth, is_active, is_staff, date_joined, last_login, profile_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', users_data)
        
        # Insert categories (20 categories with hierarchy)
        categories_data = [
            ('Electronics', 'electronics', 'Electronic devices and accessories', None, 1, 1, '/images/electronics.jpg', 'Electronics', 'Shop electronics'),
            ('Computers', 'computers', 'Desktop and laptop computers', 1, 1, 1, '/images/computers.jpg', 'Computers', 'Shop computers'),
            ('Laptops', 'laptops', 'Portable computers', 2, 1, 1, '/images/laptops.jpg', 'Laptops', 'Shop laptops'),
            ('Desktops', 'desktops', 'Desktop computers', 2, 2, 1, '/images/desktops.jpg', 'Desktops', 'Shop desktops'),
            ('Mobile Devices', 'mobile-devices', 'Smartphones and tablets', 1, 2, 1, '/images/mobile.jpg', 'Mobile Devices', 'Shop mobile devices'),
            ('Smartphones', 'smartphones', 'Mobile phones', 5, 1, 1, '/images/smartphones.jpg', 'Smartphones', 'Shop smartphones'),
            ('Tablets', 'tablets', 'Tablet computers', 5, 2, 1, '/images/tablets.jpg', 'Tablets', 'Shop tablets'),
            ('Books', 'books', 'Books and publications', None, 2, 1, '/images/books.jpg', 'Books', 'Shop books'),
            ('Fiction', 'fiction', 'Fiction books and novels', 8, 1, 1, '/images/fiction.jpg', 'Fiction', 'Shop fiction books'),
            ('Non-Fiction', 'non-fiction', 'Educational and reference books', 8, 2, 1, '/images/non-fiction.jpg', 'Non-Fiction', 'Shop non-fiction'),
            ('Clothing', 'clothing', 'Apparel and accessories', None, 3, 1, '/images/clothing.jpg', 'Clothing', 'Shop clothing'),
            ('Men\'s Clothing', 'mens-clothing', 'Men\'s apparel', 11, 1, 1, '/images/mens.jpg', 'Men\'s Clothing', 'Shop men\'s clothing'),
            ('Women\'s Clothing', 'womens-clothing', 'Women\'s apparel', 11, 2, 1, '/images/womens.jpg', 'Women\'s Clothing', 'Shop women\'s clothing'),
            ('Home & Garden', 'home-garden', 'Home and garden products', None, 4, 1, '/images/home.jpg', 'Home & Garden', 'Shop home products'),
            ('Furniture', 'furniture', 'Home furniture', 14, 1, 1, '/images/furniture.jpg', 'Furniture', 'Shop furniture'),
            ('Sports', 'sports', 'Sports and outdoor equipment', None, 5, 1, '/images/sports.jpg', 'Sports', 'Shop sports equipment'),
            ('Fitness', 'fitness', 'Fitness equipment', 16, 1, 1, '/images/fitness.jpg', 'Fitness', 'Shop fitness equipment'),
            ('Outdoor', 'outdoor', 'Outdoor equipment', 16, 2, 1, '/images/outdoor.jpg', 'Outdoor', 'Shop outdoor equipment'),
            ('Toys', 'toys', 'Toys and games', None, 6, 1, '/images/toys.jpg', 'Toys', 'Shop toys'),
            ('Board Games', 'board-games', 'Board games and puzzles', 19, 1, 1, '/images/board-games.jpg', 'Board Games', 'Shop board games'),
        ]
        
        cursor.executemany('''
            INSERT INTO categories (name, slug, description, parent_id, sort_order, is_active, 
                                  image_url, meta_title, meta_description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', categories_data)
        
        # Insert products (100 products)
        products_data = []
        for i in range(100):
            category_id = (i % 20) + 1
            price = round(10 + (i * 5.99), 2)
            sale_price = round(price * 0.9, 2) if i % 5 == 0 else None
            
            products_data.append((
                f'Product {i:03d}',
                f'product-{i:03d}',
                f'Detailed description for product {i}. This is a high-quality product with excellent features.',
                f'Short description for product {i}',
                price,
                sale_price,
                round(price * 0.6, 2),  # cost_price
                f'SKU-{i:05d}',
                f'BAR{i:010d}',
                (i % 50) + 10,  # stock_quantity
                5,  # min_stock_level
                round(0.5 + (i * 0.1), 2),  # weight
                f'{10 + i}x{5 + i}x{2 + (i % 5)} cm',
                category_id,
                None,  # brand_id
                (i % 5) + 1,  # created_by
                1 if i % 10 != 9 else 0,  # is_active
                1 if i % 20 == 0 else 0,  # is_featured
                1 if i % 25 == 0 else 0,  # is_digital
                0 if i % 25 == 0 else 1,  # requires_shipping
                'standard',  # tax_class
                f'Product {i:03d} - Best Quality',
                f'Buy Product {i:03d} at the best price. High quality guaranteed.',
                f'product{i}, quality, best price',
                f'2024-01-{(i % 30) + 1:02d} 09:00:00',
                f'2024-07-{(i % 30) + 1:02d} 14:00:00',
                json.dumps({
                    'color': ['red', 'blue', 'green'][i % 3],
                    'size': ['S', 'M', 'L', 'XL'][i % 4],
                    'material': 'cotton' if i % 2 == 0 else 'polyester',
                    'warranty': f'{(i % 3) + 1} years'
                })
            ))
        
        cursor.executemany('''
            INSERT INTO products (name, slug, description, short_description, price, sale_price, 
                                cost_price, sku, barcode, stock_quantity, min_stock_level, weight, 
                                dimensions, category_id, brand_id, created_by, is_active, is_featured, 
                                is_digital, requires_shipping, tax_class, meta_title, meta_description, 
                                search_keywords, created_at, updated_at, attributes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', products_data)
        
        # Insert orders (30 orders)
        orders_data = []
        for i in range(30):
            user_id = (i % 40) + 1  # Some users have multiple orders
            subtotal = round(50 + (i * 25.99), 2)
            tax_amount = round(subtotal * 0.08, 2)
            shipping_amount = 10.00 if i % 3 != 0 else 0.00
            discount_amount = round(subtotal * 0.1, 2) if i % 7 == 0 else 0.00
            total_amount = subtotal + tax_amount + shipping_amount - discount_amount
            
            orders_data.append((
                f'ORD-2024-{i+1:05d}',
                user_id,
                None,  # guest_email
                ['pending', 'processing', 'shipped', 'delivered', 'cancelled'][i % 5],
                ['pending', 'paid', 'failed', 'refunded'][i % 4],
                ['unfulfilled', 'partial', 'fulfilled'][i % 3],
                'USD',
                subtotal,
                tax_amount,
                shipping_amount,
                discount_amount,
                total_amount,
                ['credit_card', 'paypal', 'bank_transfer', 'cash_on_delivery'][i % 4],
                f'PAY-REF-{i+1:08d}',
                ['standard', 'express', 'overnight'][i % 3],
                f'TRACK-{i+1:010d}' if i % 3 == 0 else None,
                f'Customer note for order {i+1}' if i % 5 == 0 else None,
                f'Internal note for order {i+1}' if i % 7 == 0 else None,
                json.dumps({
                    'first_name': f'FirstName{user_id}',
                    'last_name': f'LastName{user_id}',
                    'company': f'Company {user_id}' if i % 3 == 0 else '',
                    'address_1': f'{100 + i} Main Street',
                    'address_2': f'Apt {i+1}' if i % 4 == 0 else '',
                    'city': f'City{i % 20}',
                    'state': f'State{i % 50}',
                    'postcode': f'{10000 + i:05d}',
                    'country': 'US'
                }),
                json.dumps({
                    'first_name': f'FirstName{user_id}',
                    'last_name': f'LastName{user_id}',
                    'company': f'Company {user_id}' if i % 3 == 0 else '',
                    'address_1': f'{200 + i} Shipping Avenue',
                    'address_2': f'Unit {i+1}' if i % 4 == 0 else '',
                    'city': f'ShipCity{i % 15}',
                    'state': f'State{i % 50}',
                    'postcode': f'{20000 + i:05d}',
                    'country': 'US'
                }),
                f'2024-{(i % 6) + 1:02d}-{(i % 28) + 1:02d} {10 + (i % 12)}:00:00',
                f'2024-{(i % 6) + 1:02d}-{(i % 28) + 1:02d} {11 + (i % 12)}:00:00',
                f'2024-{(i % 6) + 1:02d}-{(i % 28) + 3:02d} 10:00:00' if i % 3 == 0 else None,
                f'2024-{(i % 6) + 1:02d}-{(i % 28) + 5:02d} 15:00:00' if i % 5 == 0 else None,
            ))
        
        cursor.executemany('''
            INSERT INTO orders (order_number, user_id, guest_email, status, payment_status, 
                              fulfillment_status, currency, subtotal, tax_amount, shipping_amount, 
                              discount_amount, total_amount, payment_method, payment_reference, 
                              shipping_method, tracking_number, notes, internal_notes, 
                              billing_address, shipping_address, created_at, updated_at, 
                              shipped_at, delivered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', orders_data)
        
        # Insert order items (80 order items)
        order_items_data = []
        for i in range(80):
            order_id = (i % 30) + 1
            product_id = (i % 100) + 1
            quantity = (i % 5) + 1
            unit_price = round(10 + (i * 3.99), 2)
            total_price = unit_price * quantity
            tax_amount = round(total_price * 0.08, 2)
            
            order_items_data.append((
                order_id,
                product_id,
                None,  # product_variant_id
                quantity,
                unit_price,
                total_price,
                tax_amount,
                json.dumps({
                    'product_name': f'Product {product_id:03d}',
                    'sku': f'SKU-{product_id:05d}',
                    'price_at_time': unit_price,
                    'attributes': {
                        'color': ['red', 'blue', 'green'][i % 3],
                        'size': ['S', 'M', 'L', 'XL'][i % 4]
                    }
                }),
                f'2024-{(i % 6) + 1:02d}-{(i % 28) + 1:02d} {10 + (i % 12)}:00:00'
            ))
        
        cursor.executemany('''
            INSERT INTO order_items (order_id, product_id, product_variant_id, quantity, 
                                   unit_price, total_price, tax_amount, product_snapshot, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', order_items_data)
        
        # Insert reviews (60 reviews)
        reviews_data = []
        for i in range(60):
            product_id = (i % 100) + 1
            user_id = (i % 40) + 1 if i % 5 != 0 else None
            rating = (i % 5) + 1
            
            reviews_data.append((
                product_id,
                user_id,
                f'Guest User {i}' if user_id is None else None,
                f'guest{i}@example.com' if user_id is None else None,
                rating,
                f'Review title {i}',
                f'This is a detailed review for product {product_id}. Rating: {rating}/5. ' + 
                f'I {"highly recommend" if rating >= 4 else "do not recommend"} this product.',
                f'Good quality, fast shipping' if rating >= 4 else None,
                f'Price could be better' if rating <= 3 else None,
                1 if i % 3 == 0 else 0,  # is_verified
                1 if i % 4 != 3 else 0,  # is_approved
                i % 20,  # helpful_votes
                i % 5,   # unhelpful_votes
                f'2024-{(i % 6) + 2:02d}-{(i % 28) + 1:02d} {14 + (i % 8)}:00:00',
                f'2024-{(i % 6) + 2:02d}-{(i % 28) + 1:02d} {14 + (i % 8)}:30:00'
            ))
        
        cursor.executemany('''
            INSERT INTO reviews (product_id, user_id, guest_name, guest_email, rating, title, 
                               content, pros, cons, is_verified, is_approved, helpful_votes, 
                               unhelpful_votes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', reviews_data)
        
        # Insert inventory movements (40 movements)
        inventory_data = []
        for i in range(40):
            product_id = (i % 100) + 1
            movement_type = ['in', 'out', 'adjustment'][i % 3]
            quantity = (i % 20) + 1 if movement_type == 'in' else -((i % 10) + 1)
            reference_type = ['order', 'return', 'adjustment', 'restock'][i % 4]
            
            inventory_data.append((
                product_id,
                movement_type,
                quantity,
                reference_type,
                (i % 30) + 1 if reference_type in ['order', 'return'] else None,
                f'Inventory movement {i}: {movement_type} {abs(quantity)} units',
                (i % 5) + 1,  # created_by
                f'2024-{(i % 6) + 1:02d}-{(i % 28) + 1:02d} {9 + (i % 14)}:00:00'
            ))
        
        cursor.executemany('''
            INSERT INTO inventory_movements (product_id, movement_type, quantity, reference_type, 
                                           reference_id, notes, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', inventory_data)
    
    @patch('mysql.connector.connect')
    def test_complete_migration_workflow_integration(self, mock_mysql_connect):
        """Test complete migration workflow with realistic data"""
        # Mock MySQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        # Mock successful table creation and data insertion
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None
        
        # Mock record counts for validation
        table_counts = {
            'users': 50,
            'categories': 20,
            'products': 100,
            'orders': 30,
            'order_items': 80,
            'reviews': 60,
            'inventory_movements': 40
        }
        
        # Set up mock responses for count queries
        count_responses = []
        for table_name in table_counts:
            count_responses.extend([
                (table_counts[table_name],),  # SQLite count
                (table_counts[table_name],),  # MySQL count for validation
            ])
        
        mock_cursor.fetchone.side_effect = count_responses
        
        # Create migration service
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Mock migration log path
        with patch.object(service, 'migration_log_path', Path(self.temp_log_dir)):
            # Run complete migration
            results = service.migrate_all_tables(batch_size=50, create_rollback=True)
            
            # Verify migration results
            self.assertIsInstance(results, dict)
            self.assertEqual(results['total_tables'], 7)
            self.assertGreaterEqual(results['successful_migrations'], 0)
            self.assertIsInstance(results['total_duration'], float)
            
            # Verify all expected tables are present
            expected_tables = list(table_counts.keys())
            for table_name in expected_tables:
                self.assertIn(table_name, results['tables'])
                
                table_result = results['tables'][table_name]
                self.assertIn('migration_status', table_result)
                self.assertIn('validation_status', table_result)
            
            # Verify log file creation
            self.assertIn('log_file', results)
            self.assertTrue(os.path.exists(results['log_file']))
            
            # Verify log file content
            with open(results['log_file'], 'r') as f:
                log_data = json.load(f)
            
            self.assertIn('migration_timestamp', log_data)
            self.assertIn('migration_progress', log_data)
            self.assertIn('validation_results', log_data)
            self.assertIn('rollback_data', log_data)
            
            # Verify migration progress data
            for table_name in expected_tables:
                if table_name in log_data['migration_progress']:
                    progress_data = log_data['migration_progress'][table_name]
                    self.assertIn('table_name', progress_data)
                    self.assertIn('total_records', progress_data)
                    self.assertIn('migrated_records', progress_data)
                    self.assertIn('status', progress_data)
    
    @patch('mysql.connector.connect')
    def test_migration_with_rollback_recovery(self, mock_mysql_connect):
        """Test migration workflow with rollback and recovery"""
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
            # Test rollback point creation for all tables
            tables = service.get_sqlite_tables()
            
            for table_name in tables:
                result = service.create_rollback_point(table_name)
                self.assertTrue(result)
                self.assertIn(table_name, service.rollback_data)
            
            # Verify rollback data structure
            for table_name, rollback_info in service.rollback_data.items():
                self.assertIn('backup_table', rollback_info)
                self.assertIn('created_at', rollback_info)
                self.assertIn('original_table', rollback_info)
                self.assertEqual(rollback_info['original_table'], table_name)
            
            # Test rollback execution
            first_table = tables[0]
            rollback_result = service.rollback_table(first_table)
            self.assertTrue(rollback_result)
            
            # Test cleanup
            cleanup_result = service.cleanup_rollback_points()
            self.assertTrue(cleanup_result)
            self.assertEqual(len(service.rollback_data), 0)
            
        finally:
            service.disconnect_databases()
    
    def test_batch_migration_manager_integration(self):
        """Test BatchMigrationManager integration"""
        # Create configuration file
        config_file = os.path.join(self.temp_config_dir, 'migration_config.json')
        config_data = {
            'batch_size': 25,
            'create_rollback': True,
            'max_retries': 2,
            'retry_delay': 1,
            'validation_sample_size': 10,
            'skip_tables': ['inventory_movements'],  # Skip one table for testing
            'priority_tables': ['users', 'categories'],
            'log_level': 'INFO',
            'save_progress': True,
            'progress_file': os.path.join(self.temp_config_dir, 'progress.json')
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Create batch migration manager
        manager = BatchMigrationManager(config_file)
        
        # Verify configuration loading
        self.assertEqual(manager.config['batch_size'], 25)
        self.assertEqual(manager.config['max_retries'], 2)
        self.assertIn('inventory_movements', manager.config['skip_tables'])
        self.assertIn('users', manager.config['priority_tables'])
        
        # Test migration order determination
        all_tables = ['users', 'categories', 'products', 'orders', 'order_items', 'reviews', 'inventory_movements']
        ordered_tables = manager.get_migration_order(all_tables)
        
        # Verify priority tables come first
        self.assertEqual(ordered_tables[0], 'users')
        self.assertEqual(ordered_tables[1], 'categories')
        
        # Verify skipped tables are not included
        self.assertNotIn('inventory_movements', ordered_tables)
        
        # Test progress saving and loading
        progress_data = {
            'completed_tables': ['users', 'categories'],
            'total_tables': 6,
            'successful_migrations': 2
        }
        
        manager.save_progress(progress_data)
        loaded_progress = manager.load_progress()
        
        self.assertEqual(loaded_progress['completed_tables'], ['users', 'categories'])
        self.assertEqual(loaded_progress['successful_migrations'], 2)
    
    @patch('mysql.connector.connect')
    def test_migration_validator_integration(self, mock_mysql_connect):
        """Test MigrationValidator integration with real data"""
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
            # Test schema compatibility validation for users table
            mock_cursor.fetchall.return_value = [
                ('id', 'int(11)', 'NO', 'PRI', None, 'auto_increment'),
                ('username', 'text', 'NO', 'UNI', None, ''),
                ('email', 'text', 'NO', 'UNI', None, ''),
                ('password_hash', 'text', 'NO', '', None, ''),
                ('first_name', 'text', 'YES', '', None, ''),
                ('last_name', 'text', 'YES', '', None, ''),
                ('phone', 'text', 'YES', '', None, ''),
                ('date_of_birth', 'date', 'YES', '', None, ''),
                ('is_active', 'tinyint(1)', 'YES', '', '1', ''),
                ('is_staff', 'tinyint(1)', 'YES', '', '0', ''),
                ('date_joined', 'timestamp', 'YES', '', 'CURRENT_TIMESTAMP', ''),
                ('last_login', 'timestamp', 'YES', '', None, ''),
                ('profile_data', 'text', 'YES', '', None, ''),
            ]
            
            schema_result = validator.validate_schema_compatibility('users')
            
            self.assertIsInstance(schema_result, dict)
            self.assertEqual(schema_result['table_name'], 'users')
            self.assertIn('is_compatible', schema_result)
            self.assertIn('issues', schema_result)
            
            # Test data integrity validation
            mock_cursor.fetchall.side_effect = [
                # Sample records from MySQL (first 5 users)
                [(1, 'user_000', 'user000@example.com'), (2, 'user_001', 'user001@example.com'),
                 (3, 'user_002', 'user002@example.com'), (4, 'user_003', 'user003@example.com'),
                 (5, 'user_004', 'user004@example.com')],
                # Primary key values for comparison
                [(i,) for i in range(1, 51)]  # All 50 user IDs
            ]
            
            integrity_result = validator.validate_data_integrity('users', sample_size=10)
            
            self.assertIsInstance(integrity_result, dict)
            self.assertEqual(integrity_result['table_name'], 'users')
            self.assertIn('is_valid', integrity_result)
            self.assertIn('validated_records', integrity_result)
            self.assertIn('error_rate', integrity_result)
            
        finally:
            migration_service.sqlite_conn.close()
    
    def test_migration_performance_monitoring(self):
        """Test migration performance monitoring with realistic data"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to SQLite
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            # Test performance monitoring for each table
            tables = service.get_sqlite_tables()
            performance_metrics = {}
            
            for table_name in tables:
                start_time = datetime.now()
                
                # Get table record count
                cursor = service.sqlite_conn.cursor()
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                record_count = cursor.fetchone()[0]
                
                # Simulate data processing
                cursor.execute(f'SELECT * FROM {table_name}')
                records = cursor.fetchall()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                performance_metrics[table_name] = {
                    'record_count': record_count,
                    'processing_time': duration,
                    'records_per_second': record_count / duration if duration > 0 else 0,
                    'actual_records_fetched': len(records)
                }
                
                # Verify data consistency
                self.assertEqual(record_count, len(records))
            
            # Verify performance metrics
            expected_counts = {
                'users': 50,
                'categories': 20,
                'products': 100,
                'orders': 30,
                'order_items': 80,
                'reviews': 60,
                'inventory_movements': 40
            }
            
            for table_name, expected_count in expected_counts.items():
                self.assertIn(table_name, performance_metrics)
                metrics = performance_metrics[table_name]
                self.assertEqual(metrics['record_count'], expected_count)
                self.assertEqual(metrics['actual_records_fetched'], expected_count)
                self.assertGreaterEqual(metrics['records_per_second'], 0)
                
        finally:
            service.sqlite_conn.close()


if __name__ == '__main__':
    unittest.main()