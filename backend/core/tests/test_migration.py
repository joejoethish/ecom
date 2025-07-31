"""
Unit tests for database migration utilities.
"""
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from django.test import TestCase, override_settings
from django.conf import settings

from core.migration import (
    DatabaseMigrationService,
    MigrationValidator,
    MigrationProgress,
    ValidationResult,
    create_migration_service
)


class TestMigrationProgress(TestCase):
    """Test MigrationProgress dataclass"""
    
    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation"""
        progress = MigrationProgress(
            table_name='test_table',
            total_records=100,
            migrated_records=25,
            start_time=datetime.now()
        )
        
        self.assertEqual(progress.progress_percentage, 25.0)
    
    def test_progress_percentage_zero_total(self):
        """Test progress percentage with zero total records"""
        progress = MigrationProgress(
            table_name='test_table',
            total_records=0,
            migrated_records=0,
            start_time=datetime.now()
        )
        
        self.assertEqual(progress.progress_percentage, 100.0)
    
    def test_duration_calculation(self):
        """Test duration calculation"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        progress = MigrationProgress(
            table_name='test_table',
            total_records=100,
            migrated_records=100,
            start_time=start_time,
            end_time=end_time
        )
        
        self.assertIsNotNone(progress.duration_seconds)
        self.assertGreaterEqual(progress.duration_seconds, 0)


class TestDatabaseMigrationService(TestCase):
    """Test DatabaseMigrationService class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary SQLite database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create test table with sample data
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO test_table (name, email, age) VALUES
            ('John Doe', 'john@example.com', 30),
            ('Jane Smith', 'jane@example.com', 25),
            ('Bob Johnson', 'bob@example.com', 35)
        ''')
        
        conn.commit()
        conn.close()
        
        # Mock MySQL configuration
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
    
    def test_sqlite_type_conversion(self):
        """Test SQLite to MySQL type conversion"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        test_cases = [
            ('INTEGER', 'INT'),
            ('TEXT', 'TEXT'),
            ('REAL', 'DOUBLE'),
            ('BLOB', 'LONGBLOB'),
            ('VARCHAR(100)', 'VARCHAR(100)'),
            ('BOOLEAN', 'TINYINT(1)'),
            ('DATETIME', 'DATETIME'),
            ('UNKNOWN_TYPE', 'TEXT')  # Fallback case
        ]
        
        for sqlite_type, expected_mysql_type in test_cases:
            with self.subTest(sqlite_type=sqlite_type):
                result = service.convert_sqlite_to_mysql_type(sqlite_type)
                self.assertEqual(result, expected_mysql_type)
    
    def test_get_sqlite_tables(self):
        """Test getting SQLite table list"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to SQLite
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            tables = service.get_sqlite_tables()
            self.assertIn('test_table', tables)
            self.assertEqual(len(tables), 1)
        finally:
            service.sqlite_conn.close()
    
    def test_get_table_schema(self):
        """Test getting table schema information"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Connect to SQLite
        service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        try:
            schema = service.get_table_schema('test_table')
            
            # Check that we got the expected columns
            column_names = [col['name'] for col in schema]
            expected_columns = ['id', 'name', 'email', 'age', 'created_at']
            
            for expected_col in expected_columns:
                self.assertIn(expected_col, column_names)
            
            # Check primary key
            pk_columns = [col['name'] for col in schema if col['pk']]
            self.assertEqual(pk_columns, ['id'])
            
        finally:
            service.sqlite_conn.close()
    
    @patch('mysql.connector.connect')
    def test_create_mysql_table(self, mock_mysql_connect):
        """Test MySQL table creation"""
        # Mock MySQL connection and cursor
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
    
    def test_migration_log_path_creation(self):
        """Test that migration log directory is created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock settings.BASE_DIR
            with patch.object(settings, 'BASE_DIR', Path(temp_dir)):
                service = DatabaseMigrationService(
                    sqlite_path=self.temp_db.name,
                    mysql_config=self.mysql_config
                )
                
                # Check that migration_logs directory was created
                expected_log_path = Path(temp_dir) / 'migration_logs'
                self.assertTrue(expected_log_path.exists())
                self.assertEqual(service.migration_log_path, expected_log_path)
    
    def test_rollback_data_management(self):
        """Test rollback data management"""
        service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Test initial state
        self.assertEqual(len(service.rollback_data), 0)
        
        # Add rollback data
        service.rollback_data['test_table'] = {
            'backup_table': 'test_table_rollback_123456',
            'created_at': datetime.now().isoformat(),
            'original_table': 'test_table'
        }
        
        self.assertEqual(len(service.rollback_data), 1)
        self.assertIn('test_table', service.rollback_data)


class TestMigrationValidator(TestCase):
    """Test MigrationValidator class"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create test database
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value REAL
            )
        ''')
        conn.commit()
        conn.close()
        
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db'
        }
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    @patch('mysql.connector.connect')
    def test_schema_compatibility_validation(self, mock_mysql_connect):
        """Test schema compatibility validation"""
        # Mock MySQL connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        # Mock MySQL DESCRIBE result
        mock_cursor.fetchall.return_value = [
            ('id', 'int(11)', 'NO', 'PRI', None, 'auto_increment'),
            ('name', 'text', 'NO', '', None, ''),
            ('value', 'double', 'YES', '', None, '')
        ]
        
        # Create migration service and validator
        migration_service = DatabaseMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        migration_service.sqlite_conn = sqlite3.connect(self.temp_db.name)
        migration_service.mysql_conn = mock_conn
        
        validator = MigrationValidator(migration_service)
        
        try:
            result = validator.validate_schema_compatibility('test_table')
            
            self.assertIsInstance(result, dict)
            self.assertIn('table_name', result)
            self.assertIn('is_compatible', result)
            self.assertIn('issues', result)
            self.assertEqual(result['table_name'], 'test_table')
            
        finally:
            migration_service.sqlite_conn.close()


class TestUtilityFunctions(TestCase):
    """Test utility functions"""
    
    def test_create_migration_service(self):
        """Test migration service factory function"""
        service = create_migration_service()
        
        self.assertIsInstance(service, DatabaseMigrationService)
        self.assertIsNotNone(service.sqlite_path)
        self.assertIsNotNone(service.mysql_config)
    
    def test_create_migration_service_with_params(self):
        """Test migration service factory with custom parameters"""
        custom_sqlite_path = '/custom/path/db.sqlite3'
        custom_mysql_config = {'host': 'custom_host'}
        
        service = create_migration_service(
            sqlite_path=custom_sqlite_path,
            mysql_config=custom_mysql_config
        )
        
        self.assertEqual(service.sqlite_path, custom_sqlite_path)
        self.assertEqual(service.mysql_config, custom_mysql_config)


class TestValidationResult(TestCase):
    """Test ValidationResult dataclass"""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation and attributes"""
        validation_time = datetime.now()
        
        result = ValidationResult(
            table_name='test_table',
            source_count=100,
            target_count=100,
            is_valid=True,
            missing_records=[],
            extra_records=[],
            data_mismatches=[],
            validation_time=validation_time
        )
        
        self.assertEqual(result.table_name, 'test_table')
        self.assertEqual(result.source_count, 100)
        self.assertEqual(result.target_count, 100)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.missing_records), 0)
        self.assertEqual(len(result.extra_records), 0)
        self.assertEqual(len(result.data_mismatches), 0)
        self.assertEqual(result.validation_time, validation_time)
    
    def test_validation_result_with_issues(self):
        """Test ValidationResult with validation issues"""
        result = ValidationResult(
            table_name='test_table',
            source_count=100,
            target_count=95,
            is_valid=False,
            missing_records=[1, 2, 3, 4, 5],
            extra_records=[],
            data_mismatches=[{'record_id': 10, 'field': 'name', 'issue': 'value mismatch'}],
            validation_time=datetime.now()
        )
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.missing_records), 5)
        self.assertEqual(len(result.data_mismatches), 1)


if __name__ == '__main__':
    unittest.main()