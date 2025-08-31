"""
Edge case tests for database migration utilities.
Tests unusual scenarios, error conditions, and boundary cases.
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

from django.test import TestCase
from django.conf import settings

from core.migration import (
    DatabaseMigrationService,
    MigrationValidator,
    MigrationProgress,
    ValidationResult
)


class TestMigrationEdgeCases(TestCase):
    """Test edge cases and unusual scenarios in migration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db',
            'charset': 'utf8mb4'
        }
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_empty_database_migration(self):
        """Test migration of completely empty database"""
        # Create empty SQLite database
        conn = sqlite3.connect(self.temp_db.name)
        conn.close()
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to SQLite
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            tables = service.get_sqlite_tables()
            self.assertEqual(len(tables), 0)
            
        finally:
            service.sqlite_conn.close()
    
    def test_tables_with_special_characters(self):
        """Test migration of tables with special characters in names and data"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create table with special characters
        cursor.execute('''
            CREATE TABLE "special-table_name" (
                id INTEGER PRIMARY KEY,
                "field-with-dashes" TEXT,
                "field_with_underscores" TEXT,
                "field with spaces" TEXT,
                "unicode_field" TEXT,
                "json_data" TEXT
            )
        ''')
        
        # Insert data with special characters
        cursor.execute('''
            INSERT INTO "special-table_name" 
            ("field-with-dashes", "field_with_underscores", "field with spaces", "unicode_field", "json_data")
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'value-with-dashes',
            'value_with_underscores', 
            'value with spaces',
            'Unicode: café, naïve, résumé, 中文, العربية, русский',
            '{"key": "value", "nested": {"array": [1, 2, 3]}, "unicode": "测试"}'
        ))
        
        conn.commit()
        conn.close()
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to SQLite
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            tables = service.get_sqlite_tables()
            self.assertIn('special-table_name', tables)
            
            # Test schema extraction
            schema = service.get_table_schema('special-table_name')
            column_names = [col['name'] for col in schema]
            
            expected_columns = [
                'id', 'field-with-dashes', 'field_with_underscores', 
                'field with spaces', 'unicode_field', 'json_data'
            ]
            
            for expected_col in expected_columns:
                self.assertIn(expected_col, column_names)
                
        finally:
            service.sqlite_conn.close()
    
    def test_large_data_types_and_null_values(self):
        """Test migration of large data types and NULL values"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create table with various data types
        cursor.execute('''
            CREATE TABLE data_types_test (
                id INTEGER PRIMARY KEY,
                tiny_text TEXT,
                large_text TEXT,
                blob_data BLOB,
                null_text TEXT,
                null_integer INTEGER,
                null_real REAL,
                zero_integer INTEGER,
                zero_real REAL,
                empty_string TEXT,
                whitespace_string TEXT
            )
        ''')
        
        # Create large text content
        large_text = 'A' * 10000  # 10KB text
        large_blob = b'Binary data: ' + b'\x00\x01\x02\x03' * 1000  # Binary data with null bytes
        
        # Insert test data with various edge cases
        cursor.execute('''
            INSERT INTO data_types_test 
            (tiny_text, large_text, blob_data, null_text, null_integer, null_real, 
             zero_integer, zero_real, empty_string, whitespace_string)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'small',
            large_text,
            large_blob,
            None,  # NULL text
            None,  # NULL integer
            None,  # NULL real
            0,     # Zero integer
            0.0,   # Zero real
            '',    # Empty string
            '   '  # Whitespace string
        ))
        
        conn.commit()
        conn.close()
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to SQLite
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            # Test data extraction
            cursor = service.sqlite_conn.cursor()
            cursor.execute('SELECT * FROM data_types_test')
            row = cursor.fetchone()
            
            self.assertEqual(row['tiny_text'], 'small')
            self.assertEqual(len(row['large_text']), 10000)
            self.assertIsNone(row['null_text'])
            self.assertIsNone(row['null_integer'])
            self.assertIsNone(row['null_real'])
            self.assertEqual(row['zero_integer'], 0)
            self.assertEqual(row['zero_real'], 0.0)
            self.assertEqual(row['empty_string'], '')
            self.assertEqual(row['whitespace_string'], '   ')
            
        finally:
            service.sqlite_conn.close()
    
    def test_circular_foreign_key_references(self):
        """Test migration of tables with circular foreign key references"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create tables with circular references
        cursor.execute('''
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                manager_id INTEGER,
                FOREIGN KEY (manager_id) REFERENCES employees (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department_id INTEGER,
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        ''')
        
        # Insert data with circular references
        cursor.execute('INSERT INTO departments (id, name) VALUES (1, "Engineering")')
        cursor.execute('INSERT INTO employees (id, name, department_id) VALUES (1, "John Doe", 1)')
        cursor.execute('UPDATE departments SET manager_id = 1 WHERE id = 1')
        
        conn.commit()
        conn.close()
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to SQLite
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            tables = service.get_sqlite_tables()
            self.assertIn('departments', tables)
            self.assertIn('employees', tables)
            
            # Test that both tables can be analyzed
            for table_name in ['departments', 'employees']:
                schema = service.get_table_schema(table_name)
                self.assertGreater(len(schema), 0)
                
        finally:
            service.sqlite_conn.close()
    
    def test_migration_with_database_corruption(self):
        """Test migration behavior with corrupted database"""
        # Create a corrupted SQLite file
        with open(self.temp_db.name, 'wb') as f:
            f.write(b'This is not a valid SQLite database file')
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Attempt to connect should fail gracefully
        result = service.connect_databases()
        self.assertFalse(result)
    
    def test_migration_with_locked_database(self):
        """Test migration behavior with locked database"""
        # Create valid database
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
        cursor.execute('INSERT INTO test (id) VALUES (1)')
        
        # Start a transaction but don't commit (locks the database)
        cursor.execute('BEGIN EXCLUSIVE TRANSACTION')
        cursor.execute('INSERT INTO test (id) VALUES (2)')
        # Don't commit or close - this locks the database
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        try:
            # This should handle the locked database gracefully
            service.sqlite_conn = sqlite3.connect(self.temp_db.name, timeout=1.0)
            service.sqlite_conn.row_factory = sqlite3.Row
            
            # Attempt to read from locked database
            try:
                tables = service.get_sqlite_tables()
                # If we get here, the lock was released or handled
                self.assertIsInstance(tables, list)
            except sqlite3.OperationalError as e:
                # Expected behavior for locked database
                self.assertIn('locked', str(e).lower())
                
        finally:
            if service.sqlite_conn:
                service.sqlite_conn.close()
            conn.rollback()  # Release the lock
            conn.close()
    
    @patch('mysql.connector.connect')
    def test_mysql_connection_failures(self, mock_mysql_connect):
        """Test various MySQL connection failure scenarios"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Test connection timeout
        mock_mysql_connect.side_effect = Exception("Connection timeout")
        result = service.connect_databases()
        self.assertFalse(result)
        
        # Test authentication failure
        mock_mysql_connect.side_effect = Exception("Access denied for user")
        result = service.connect_databases()
        self.assertFalse(result)
        
        # Test database not found
        mock_mysql_connect.side_effect = Exception("Unknown database")
        result = service.connect_databases()
        self.assertFalse(result)
    
    def test_migration_progress_edge_cases(self):
        """Test migration progress tracking edge cases"""
        # Test progress with zero total records
        progress = MigrationProgress(
            table_name='empty_table',
            total_records=0,
            migrated_records=0,
            start_time=datetime.now()
        )
        
        self.assertEqual(progress.progress_percentage, 100.0)
        
        # Test progress with more migrated than total (shouldn't happen but handle gracefully)
        progress_overflow = MigrationProgress(
            table_name='overflow_table',
            total_records=100,
            migrated_records=150,
            start_time=datetime.now()
        )
        
        self.assertEqual(progress_overflow.progress_percentage, 150.0)
        
        # Test duration calculation with same start/end time
        now = datetime.now()
        progress_instant = MigrationProgress(
            table_name='instant_table',
            total_records=1,
            migrated_records=1,
            start_time=now,
            end_time=now
        )
        
        self.assertEqual(progress_instant.duration_seconds, 0.0)
    
    def test_validation_with_data_type_mismatches(self):
        """Test validation when data types don't match between databases"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create table with ambiguous data types
        cursor.execute('''
            CREATE TABLE type_mismatch_test (
                id INTEGER PRIMARY KEY,
                numeric_as_text TEXT,
                date_as_text TEXT,
                boolean_as_integer INTEGER,
                json_as_text TEXT
            )
        ''')
        
        # Insert data that could be interpreted differently
        cursor.execute('''
            INSERT INTO type_mismatch_test 
            (numeric_as_text, date_as_text, boolean_as_integer, json_as_text)
            VALUES (?, ?, ?, ?)
        ''', (
            '123.45',  # Number stored as text
            '2024-01-01',  # Date stored as text
            1,  # Boolean stored as integer
            '{"key": "value"}'  # JSON stored as text
        ))
        
        conn.commit()
        conn.close()
        
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Test type conversion
        test_cases = [
            ('TEXT', 'TEXT'),  # Should match
            ('INTEGER', 'INT'),  # Should match
            ('REAL', 'DOUBLE'),  # Should match
        ]
        
        for sqlite_type, expected_mysql_type in test_cases:
            result = service.convert_sqlite_to_mysql_type(sqlite_type)
            self.assertEqual(result, expected_mysql_type)
    
    def test_migration_log_edge_cases(self):
        """Test migration logging edge cases"""
        temp_log_dir = tempfile.mkdtemp()
        
        try:
            service = DatabaseMigrationService(
                sqlite_path=self.temp_db.name,
                mysql_config=self.mysql_config
            )
            
            # Mock migration log path
            service.migration_log_path = Path(temp_log_dir)
            
            # Test logging with no migration data
            log_file = service.save_migration_log()
            self.assertTrue(os.path.exists(log_file))
            
            # Verify log content
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            
            self.assertIn('migration_timestamp', log_data)
            self.assertIn('sqlite_path', log_data)
            self.assertIn('mysql_config', log_data)
            self.assertIn('migration_progress', log_data)
            self.assertIn('validation_results', log_data)
            self.assertIn('rollback_data', log_data)
            
            # Verify password is not logged
            self.assertNotIn('password', str(log_data['mysql_config']))
            
            # Test logging with complex data structures
            service.migration_progress['test_table'] = MigrationProgress(
                table_name='test_table',
                total_records=100,
                migrated_records=100,
                start_time=datetime.now(),
                end_time=datetime.now(),
                status='completed'
            )
            
            log_file_2 = service.save_migration_log()
            self.assertTrue(os.path.exists(log_file_2))
            
        finally:
            shutil.rmtree(temp_log_dir)
    
    def test_rollback_edge_cases(self):
        """Test rollback functionality edge cases"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Test rollback without rollback data
        result = service.rollback_table('nonexistent_table')
        self.assertFalse(result)
        
        # Test cleanup without rollback data
        result = service.cleanup_rollback_points('nonexistent_table')
        self.assertTrue(result)  # Should succeed even if nothing to clean
        
        # Test cleanup of all rollback points when none exist
        result = service.cleanup_rollback_points()
        self.assertTrue(result)


class TestMigrationPerformance(TestCase):
    """Test migration performance and resource usage"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db',
            'charset': 'utf8mb4'
        }
        
        # Create database with large dataset
        self._create_large_test_database()
    
    def tearDown(self):
        """Clean up performance test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def _create_large_test_database(self):
        """Create database with large dataset for performance testing"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create table for performance testing
        cursor.execute('''
            CREATE TABLE performance_test (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert large dataset (1000 records for testing)
        test_data = []
        for i in range(1000):
            test_data.append((
                f'user_{i:04d}',
                f'user_{i:04d}@example.com',
                f'Large data content for user {i} ' + 'x' * 100,  # ~120 chars per record
            ))
        
        cursor.executemany('''
            INSERT INTO performance_test (name, email, data)
            VALUES (?, ?, ?)
        ''', test_data)
        
        conn.commit()
        conn.close()
    
    def test_batch_size_performance(self):
        """Test migration performance with different batch sizes"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to SQLite
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            # Test different batch sizes
            batch_sizes = [10, 50, 100, 500]
            performance_results = {}
            
            for batch_size in batch_sizes:
                start_time = datetime.now()
                
                # Simulate batch processing
                cursor = service.sqlite_conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM performance_test')
                total_records = cursor.fetchone()[0]
                
                processed_records = 0
                offset = 0
                
                while offset < total_records:
                    cursor.execute(f'SELECT * FROM performance_test LIMIT {batch_size} OFFSET {offset}')
                    batch_data = cursor.fetchall()
                    
                    if not batch_data:
                        break
                    
                    # Simulate processing time
                    processed_records += len(batch_data)
                    offset += batch_size
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                performance_results[batch_size] = {
                    'duration': duration,
                    'records_per_second': processed_records / duration if duration > 0 else 0,
                    'processed_records': processed_records
                }
            
            # Verify all batch sizes processed the same number of records
            record_counts = [result['processed_records'] for result in performance_results.values()]
            self.assertTrue(all(count == record_counts[0] for count in record_counts))
            
            # Verify performance metrics are reasonable
            for batch_size, result in performance_results.items():
                self.assertGreater(result['records_per_second'], 0)
                self.assertEqual(result['processed_records'], 1000)
                
        finally:
            service.sqlite_conn.close()
    
    def test_memory_usage_monitoring(self):
        """Test memory usage during migration"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Test progress tracking memory usage
        progress_objects = []
        
        # Create multiple progress objects to test memory usage
        for i in range(100):
            progress = MigrationProgress(
                table_name=f'table_{i}',
                total_records=1000,
                migrated_records=i * 10,
                start_time=datetime.now()
            )
            progress_objects.append(progress)
        
        # Verify all objects are created correctly
        self.assertEqual(len(progress_objects), 100)
        
        # Test that progress calculations work for all objects
        for i, progress in enumerate(progress_objects):
            expected_percentage = (i * 10 / 1000) * 100
            self.assertEqual(progress.progress_percentage, expected_percentage)
    
    def test_concurrent_migration_simulation(self):
        """Test simulation of concurrent migration operations"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Simulate multiple table migrations
        table_names = ['table_1', 'table_2', 'table_3', 'table_4', 'table_5']
        migration_results = {}
        
        for table_name in table_names:
            start_time = datetime.now()
            
            # Simulate migration progress
            progress = MigrationProgress(
                table_name=table_name,
                total_records=200,
                migrated_records=0,
                start_time=start_time
            )
            
            # Simulate batch processing
            for batch in range(0, 200, 50):
                progress.migrated_records = min(batch + 50, 200)
                
                # Simulate processing time
                import time
                time.sleep(0.001)  # 1ms per batch
            
            progress.end_time = datetime.now()
            progress.status = 'completed'
            
            migration_results[table_name] = progress
        
        # Verify all migrations completed
        for table_name, progress in migration_results.items():
            self.assertEqual(progress.status, 'completed')
            self.assertEqual(progress.progress_percentage, 100.0)
            self.assertIsNotNone(progress.duration_seconds)
            self.assertGreater(progress.duration_seconds, 0)


if __name__ == '__main__':
    unittest.main()