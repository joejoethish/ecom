#!/usr/bin/env python3
"""
Simple test script to verify migration testing suite functionality.
Runs basic tests without Django test runner complications.
"""
import os
import sys
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add Django project to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')

import django
django.setup()

from core.migration import (
    DatabaseMigrationService,
    MigrationProgress,
    ValidationResult
)


class SimpleMigrationTest(unittest.TestCase):
    """Simple migration tests without database dependencies"""
    
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
        
        # Create simple test database
        self._create_simple_test_database()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def _create_simple_test_database(self):
        """Create simple test database"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE test_users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO test_users (name, email) VALUES
            ('John Doe', 'john@example.com'),
            ('Jane Smith', 'jane@example.com'),
            ('Bob Johnson', 'bob@example.com')
        ''')
        
        conn.commit()
        conn.close()
    
    def test_migration_service_initialization(self):
        """Test migration service initialization"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        self.assertEqual(service.sqlite_path, self.temp_db.name)
        self.assertEqual(service.mysql_config, self.mysql_config)
        self.assertIsInstance(service.migration_progress, dict)
        self.assertIsInstance(service.validation_results, dict)
        self.assertIsInstance(service.rollback_data, dict)
    
    def test_sqlite_connection_and_table_discovery(self):
        """Test SQLite connection and table discovery"""
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
            self.assertIn('test_users', tables)
            self.assertEqual(len(tables), 1)
            
            # Test schema analysis
            schema = service.get_table_schema('test_users')
            self.assertIsInstance(schema, list)
            self.assertGreater(len(schema), 0)
            
            # Verify column information
            column_names = [col['name'] for col in schema]
            expected_columns = ['id', 'name', 'email', 'created_at']
            
            for expected_col in expected_columns:
                self.assertIn(expected_col, column_names)
                
        finally:
            service.sqlite_conn.close()
    
    def test_data_type_conversion(self):
        """Test SQLite to MySQL data type conversion"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        test_cases = [
            ('INTEGER', 'INT'),
            ('TEXT', 'TEXT'),
            ('REAL', 'DOUBLE'),
            ('BLOB', 'LONGBLOB'),
            ('VARCHAR(255)', 'VARCHAR(255)'),
            ('BOOLEAN', 'TINYINT(1)'),
            ('DATETIME', 'DATETIME'),
            ('TIMESTAMP', 'TIMESTAMP'),
            ('UNKNOWN_TYPE', 'TEXT')  # Fallback case
        ]
        
        for sqlite_type, expected_mysql_type in test_cases:
            with self.subTest(sqlite_type=sqlite_type):
                result = service.convert_sqlite_to_mysql_type(sqlite_type)
                self.assertEqual(result, expected_mysql_type)
    
    def test_migration_progress_tracking(self):
        """Test migration progress tracking"""
        from datetime import datetime, timedelta
        
        start_time = datetime.now()
        progress = MigrationProgress(
            table_name='test_table',
            total_records=100,
            migrated_records=25,
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
        progress.migrated_records = 100
        
        self.assertEqual(progress.progress_percentage, 100.0)
        self.assertEqual(progress.status, 'completed')
        self.assertEqual(progress.duration_seconds, 30.0)
        
        # Test edge case - zero total records
        empty_progress = MigrationProgress(
            table_name='empty_table',
            total_records=0,
            migrated_records=0,
            start_time=start_time
        )
        self.assertEqual(empty_progress.progress_percentage, 100.0)
    
    def test_validation_result_creation(self):
        """Test validation result creation and analysis"""
        from datetime import datetime
        
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
        
        # Test failed validation
        failed_result = ValidationResult(
            table_name='problem_table',
            source_count=100,
            target_count=95,
            is_valid=False,
            missing_records=[1, 2, 3, 4, 5],
            extra_records=[],
            data_mismatches=[
                {'record_id': 10, 'field': 'name', 'issue': 'value mismatch'}
            ],
            validation_time=validation_time
        )
        
        self.assertFalse(failed_result.is_valid)
        self.assertNotEqual(failed_result.source_count, failed_result.target_count)
        self.assertEqual(len(failed_result.missing_records), 5)
        self.assertEqual(len(failed_result.data_mismatches), 1)
    
    @patch('mysql.connector.connect')
    def test_mysql_table_creation(self, mock_mysql_connect):
        """Test MySQL table creation with mocked connection"""
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
        
        # Test table schema
        columns = [
            {'name': 'id', 'type': 'INTEGER', 'notnull': True, 'default_value': None, 'pk': True},
            {'name': 'name', 'type': 'TEXT', 'notnull': True, 'default_value': None, 'pk': False},
            {'name': 'email', 'type': 'TEXT', 'notnull': False, 'default_value': None, 'pk': False}
        ]
        
        result = service.create_mysql_table('test_table', columns)
        
        # Verify table creation was attempted
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Check that the SQL contains expected elements
        sql_call = mock_cursor.execute.call_args[0][0]
        self.assertIn('CREATE TABLE IF NOT EXISTS `test_table`', sql_call)
        self.assertIn('`id` INT NOT NULL', sql_call)
        self.assertIn('`name` TEXT NOT NULL', sql_call)
        self.assertIn('PRIMARY KEY (`id`)', sql_call)
    
    def test_rollback_data_management(self):
        """Test rollback data management"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Test initial state
        self.assertEqual(len(service.rollback_data), 0)
        
        # Test adding rollback data
        from datetime import datetime
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


def run_simple_tests():
    """Run simple migration tests"""
    print("SIMPLE MIGRATION TESTS")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(SimpleMigrationTest)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    try:
        success = run_simple_tests()
        if success:
            print("\n✅ All simple migration tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)