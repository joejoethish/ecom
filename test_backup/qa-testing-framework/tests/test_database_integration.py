"""
Integration Tests for Database Operations

Tests actual database operations with PostgreSQL to verify connection management,
schema setup/teardown, transaction handling, and backup/restore functionality.
"""

import unittest
import os
import tempfile
import time
from unittest.mock import patch
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from core.database import DatabaseManager, get_database_manager
from core.interfaces import Environment


class DatabaseIntegrationTests(unittest.TestCase):
    """Integration test cases for DatabaseManager with actual PostgreSQL"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with test database"""
        cls.test_db_name = "qa_test_integration"
        cls.db_manager = DatabaseManager(Environment.DEVELOPMENT)
        
        # Override database name for integration tests
        cls.db_manager.database = cls.test_db_name
        cls.db_manager.connection_params["database"] = cls.test_db_name
        
        # Create test database
        cls._create_test_database()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        cls._drop_test_database()
    
    @classmethod
    def _create_test_database(cls):
        """Create test database for integration tests"""
        try:
            # Connect to default postgres database
            temp_params = cls.db_manager.connection_params.copy()
            temp_params["database"] = "postgres"
            
            with psycopg2.connect(**temp_params) as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                
                with conn.cursor() as cursor:
                    # Drop database if exists
                    cursor.execute(f"DROP DATABASE IF EXISTS {cls.test_db_name}")
                    # Create test database
                    cursor.execute(f"CREATE DATABASE {cls.test_db_name}")
                    
        except psycopg2.Error as e:
            print(f"Failed to create test database: {e}")
            raise
    
    @classmethod
    def _drop_test_database(cls):
        """Drop test database after tests"""
        try:
            # Disconnect from test database
            if hasattr(cls.db_manager, 'connection') and cls.db_manager.connection:
                cls.db_manager.disconnect()
            
            # Connect to default postgres database
            temp_params = cls.db_manager.connection_params.copy()
            temp_params["database"] = "postgres"
            
            with psycopg2.connect(**temp_params) as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                
                with conn.cursor() as cursor:
                    # Terminate connections to test database
                    cursor.execute(f"""
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = '{cls.test_db_name}' AND pid <> pg_backend_pid()
                    """)
                    # Drop test database
                    cursor.execute(f"DROP DATABASE IF EXISTS {cls.test_db_name}")
                    
        except psycopg2.Error as e:
            print(f"Failed to drop test database: {e}")
    
    def setUp(self):
        """Set up each test"""
        self.db_manager.connect()
    
    def tearDown(self):
        """Clean up after each test"""
        # Clean up any test data
        try:
            if self.db_manager.is_connected():
                # Drop all tables to clean state
                with self.db_manager.connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public'
                        AND tablename NOT LIKE 'pg_%'
                        AND tablename NOT LIKE 'sql_%'
                    """)
                    tables = cursor.fetchall()
                    
                    for (table_name,) in tables:
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                    
                    self.db_manager.connection.commit()
        except psycopg2.Error:
            pass  # Ignore cleanup errors
        
        self.db_manager.disconnect()
    
    def test_database_connection_lifecycle(self):
        """Test complete database connection lifecycle"""
        # Test initial connection
        self.assertTrue(self.db_manager.connect())
        self.assertTrue(self.db_manager.is_connected())
        
        # Test reconnection
        self.db_manager.disconnect()
        self.assertFalse(self.db_manager.is_connected())
        
        self.assertTrue(self.db_manager.connect())
        self.assertTrue(self.db_manager.is_connected())
    
    def test_schema_setup_and_teardown(self):
        """Test complete schema setup and teardown"""
        # Setup test schema
        self.assertTrue(self.db_manager.setup_test_schema())
        
        # Verify tables were created
        tables = self.db_manager.execute_query("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename LIKE 'test_%'
        """)
        
        expected_tables = [
            'test_users', 'test_user_addresses', 'test_user_payment_methods',
            'test_products', 'test_product_variants', 'test_cases',
            'test_steps', 'test_executions', 'test_defects'
        ]
        
        table_names = [table[0] for table in tables]
        for expected_table in expected_tables:
            self.assertIn(expected_table, table_names)
        
        # Test teardown
        self.assertTrue(self.db_manager.teardown_test_schema())
        
        # Verify tables were dropped
        tables_after = self.db_manager.execute_query("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename LIKE 'test_%'
        """)
        
        self.assertEqual(len(tables_after), 0)
    
    def test_crud_operations_with_schema(self):
        """Test CRUD operations with actual schema"""
        # Setup schema
        self.assertTrue(self.db_manager.setup_test_schema())
        
        # Test INSERT
        insert_result = self.db_manager.execute_command("""
            INSERT INTO test_users (id, user_type, email, password, first_name, last_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ("user_001", "registered", "test@example.com", "password123", "Test", "User"))
        
        self.assertTrue(insert_result)
        
        # Test SELECT
        users = self.db_manager.execute_query("""
            SELECT id, user_type, email, first_name, last_name
            FROM test_users WHERE id = %s
        """, ("user_001",))
        
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0][0], "user_001")
        self.assertEqual(users[0][1], "registered")
        self.assertEqual(users[0][2], "test@example.com")
        
        # Test UPDATE
        update_result = self.db_manager.execute_command("""
            UPDATE test_users SET first_name = %s WHERE id = %s
        """, ("Updated", "user_001"))
        
        self.assertTrue(update_result)
        
        # Verify update
        updated_users = self.db_manager.execute_query("""
            SELECT first_name FROM test_users WHERE id = %s
        """, ("user_001",))
        
        self.assertEqual(updated_users[0][0], "Updated")
        
        # Test DELETE
        delete_result = self.db_manager.execute_command("""
            DELETE FROM test_users WHERE id = %s
        """, ("user_001",))
        
        self.assertTrue(delete_result)
        
        # Verify deletion
        deleted_users = self.db_manager.execute_query("""
            SELECT id FROM test_users WHERE id = %s
        """, ("user_001",))
        
        self.assertEqual(len(deleted_users), 0)
    
    def test_transaction_management(self):
        """Test transaction management with rollback scenarios"""
        # Setup schema
        self.assertTrue(self.db_manager.setup_test_schema())
        
        # Test successful transaction
        try:
            with self.db_manager.transaction() as cursor:
                cursor.execute("""
                    INSERT INTO test_users (id, user_type, email, password)
                    VALUES (%s, %s, %s, %s)
                """, ("user_tx_001", "registered", "tx1@example.com", "password"))
                
                cursor.execute("""
                    INSERT INTO test_products (id, name, category, price)
                    VALUES (%s, %s, %s, %s)
                """, ("prod_tx_001", "Test Product", "electronics", 99.99))
            
            # Verify both records were committed
            users = self.db_manager.execute_query("SELECT id FROM test_users WHERE id = %s", ("user_tx_001",))
            products = self.db_manager.execute_query("SELECT id FROM test_products WHERE id = %s", ("prod_tx_001",))
            
            self.assertEqual(len(users), 1)
            self.assertEqual(len(products), 1)
            
        except Exception as e:
            self.fail(f"Transaction should have succeeded: {e}")
        
        # Test transaction rollback
        try:
            with self.db_manager.transaction() as cursor:
                cursor.execute("""
                    INSERT INTO test_users (id, user_type, email, password)
                    VALUES (%s, %s, %s, %s)
                """, ("user_tx_002", "registered", "tx2@example.com", "password"))
                
                # This should cause a rollback due to duplicate key
                cursor.execute("""
                    INSERT INTO test_users (id, user_type, email, password)
                    VALUES (%s, %s, %s, %s)
                """, ("user_tx_002", "registered", "tx2_dup@example.com", "password"))
                
        except psycopg2.Error:
            pass  # Expected error
        
        # Verify rollback - no user should exist
        users_after_rollback = self.db_manager.execute_query(
            "SELECT id FROM test_users WHERE id = %s", ("user_tx_002",)
        )
        self.assertEqual(len(users_after_rollback), 0)
    
    def test_nested_transactions(self):
        """Test nested transaction handling with savepoints"""
        # Setup schema
        self.assertTrue(self.db_manager.setup_test_schema())
        
        try:
            with self.db_manager.transaction() as outer_cursor:
                # Insert in outer transaction
                outer_cursor.execute("""
                    INSERT INTO test_users (id, user_type, email, password)
                    VALUES (%s, %s, %s, %s)
                """, ("user_nested_001", "registered", "nested1@example.com", "password"))
                
                try:
                    with self.db_manager.transaction() as inner_cursor:
                        # Insert in inner transaction
                        inner_cursor.execute("""
                            INSERT INTO test_users (id, user_type, email, password)
                            VALUES (%s, %s, %s, %s)
                        """, ("user_nested_002", "registered", "nested2@example.com", "password"))
                        
                        # Force error in inner transaction
                        inner_cursor.execute("SELECT * FROM non_existent_table")
                        
                except psycopg2.Error:
                    pass  # Expected error in inner transaction
                
                # Outer transaction should still be valid
                outer_cursor.execute("""
                    INSERT INTO test_users (id, user_type, email, password)
                    VALUES (%s, %s, %s, %s)
                """, ("user_nested_003", "registered", "nested3@example.com", "password"))
        
        except Exception as e:
            self.fail(f"Outer transaction should have succeeded: {e}")
        
        # Verify results
        users = self.db_manager.execute_query("""
            SELECT id FROM test_users WHERE id IN (%s, %s, %s)
        """, ("user_nested_001", "user_nested_002", "user_nested_003"))
        
        user_ids = [user[0] for user in users]
        
        # Outer transaction users should exist
        self.assertIn("user_nested_001", user_ids)
        self.assertIn("user_nested_003", user_ids)
        
        # Inner transaction user should not exist (rolled back)
        self.assertNotIn("user_nested_002", user_ids)
    
    def test_table_operations(self):
        """Test table-specific operations"""
        # Setup schema
        self.assertTrue(self.db_manager.setup_test_schema())
        
        # Insert test data
        self.db_manager.execute_command("""
            INSERT INTO test_users (id, user_type, email, password)
            VALUES (%s, %s, %s, %s)
        """, ("user_table_001", "registered", "table1@example.com", "password"))
        
        self.db_manager.execute_command("""
            INSERT INTO test_products (id, name, category, price)
            VALUES (%s, %s, %s, %s)
        """, ("prod_table_001", "Test Product", "electronics", 99.99))
        
        # Test get_table_info
        user_info = self.db_manager.get_table_info("test_users")
        self.assertEqual(user_info["table_name"], "test_users")
        self.assertEqual(user_info["row_count"], 1)
        self.assertGreater(len(user_info["columns"]), 0)
        
        # Verify column information
        column_names = [col["name"] for col in user_info["columns"]]
        expected_columns = ["id", "user_type", "email", "password", "first_name", "last_name"]
        for col in expected_columns:
            self.assertIn(col, column_names)
        
        # Test truncate_tables
        self.assertTrue(self.db_manager.truncate_tables(["test_users", "test_products"]))
        
        # Verify tables are empty
        user_count = self.db_manager.execute_query("SELECT COUNT(*) FROM test_users")[0][0]
        product_count = self.db_manager.execute_query("SELECT COUNT(*) FROM test_products")[0][0]
        
        self.assertEqual(user_count, 0)
        self.assertEqual(product_count, 0)
    
    def test_context_manager_usage(self):
        """Test DatabaseManager as context manager"""
        with DatabaseManager(Environment.DEVELOPMENT) as db:
            # Override database name for test
            db.database = self.test_db_name
            db.connection_params["database"] = self.test_db_name
            
            # Test connection within context
            self.assertTrue(db.connect())
            self.assertTrue(db.is_connected())
            
            # Test basic operation
            result = db.execute_query("SELECT 1 as test_value")
            self.assertEqual(result[0][0], 1)
        
        # Connection should be closed after context
        self.assertFalse(db.is_connected())
    
    def test_isolation_levels(self):
        """Test different transaction isolation levels"""
        # Setup schema
        self.assertTrue(self.db_manager.setup_test_schema())
        
        # Test with READ_COMMITTED isolation
        try:
            with self.db_manager.transaction(isolation_level="READ_COMMITTED") as cursor:
                cursor.execute("""
                    INSERT INTO test_users (id, user_type, email, password)
                    VALUES (%s, %s, %s, %s)
                """, ("user_iso_001", "registered", "iso1@example.com", "password"))
            
            # Verify insertion
            users = self.db_manager.execute_query("SELECT id FROM test_users WHERE id = %s", ("user_iso_001",))
            self.assertEqual(len(users), 1)
            
        except Exception as e:
            self.fail(f"Transaction with READ_COMMITTED should have succeeded: {e}")
        
        # Test with SERIALIZABLE isolation
        try:
            with self.db_manager.transaction(isolation_level="SERIALIZABLE") as cursor:
                cursor.execute("""
                    INSERT INTO test_users (id, user_type, email, password)
                    VALUES (%s, %s, %s, %s)
                """, ("user_iso_002", "registered", "iso2@example.com", "password"))
            
            # Verify insertion
            users = self.db_manager.execute_query("SELECT id FROM test_users WHERE id = %s", ("user_iso_002",))
            self.assertEqual(len(users), 1)
            
        except Exception as e:
            self.fail(f"Transaction with SERIALIZABLE should have succeeded: {e}")
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        # Setup schema
        self.assertTrue(self.db_manager.setup_test_schema())
        
        # Test handling of invalid SQL
        result = self.db_manager.execute_query("SELECT * FROM non_existent_table")
        self.assertEqual(result, [])  # Should return empty list on error
        
        # Test handling of invalid command
        result = self.db_manager.execute_command("INSERT INTO non_existent_table VALUES (1)")
        self.assertFalse(result)  # Should return False on error
        
        # Test connection recovery after error
        self.assertTrue(self.db_manager.is_connected())
        
        # Test valid operation after error
        valid_result = self.db_manager.execute_query("SELECT 1 as recovery_test")
        self.assertEqual(valid_result[0][0], 1)
    
    @unittest.skipIf(os.name == 'nt', "pg_dump/psql not available in Windows test environment")
    def test_backup_and_restore_operations(self):
        """Test backup and restore functionality (requires pg_dump/psql)"""
        # Setup schema and test data
        self.assertTrue(self.db_manager.setup_test_schema())
        
        # Insert test data
        self.db_manager.execute_command("""
            INSERT INTO test_users (id, user_type, email, password, first_name)
            VALUES (%s, %s, %s, %s, %s)
        """, ("user_backup_001", "registered", "backup@example.com", "password", "Backup"))
        
        # Create backup
        backup_file = self.db_manager.backup_database("integration_test_backup")
        
        if backup_file:  # Only test if backup was successful
            self.assertTrue(os.path.exists(backup_file))
            
            # Modify data
            self.db_manager.execute_command("""
                UPDATE test_users SET first_name = %s WHERE id = %s
            """, ("Modified", "user_backup_001"))
            
            # Restore from backup
            restore_result = self.db_manager.restore_database(backup_file, self.test_db_name)
            
            if restore_result:  # Only verify if restore was successful
                # Reconnect after restore
                self.db_manager.disconnect()
                self.db_manager.connect()
                
                # Verify original data is restored
                users = self.db_manager.execute_query("""
                    SELECT first_name FROM test_users WHERE id = %s
                """, ("user_backup_001",))
                
                if users:  # Only check if user exists
                    self.assertEqual(users[0][0], "Backup")
            
            # Cleanup backup file
            self.db_manager.cleanup_backups()


if __name__ == '__main__':
    # Check if PostgreSQL is available before running integration tests
    try:
        test_params = {
            "host": "localhost",
            "port": 5432,
            "database": "postgres",
            "user": "qa_user",
            "password": "qa_password"
        }
        
        with psycopg2.connect(**test_params) as conn:
            pass  # Connection successful
        
        unittest.main()
        
    except psycopg2.Error as e:
        print(f"PostgreSQL not available for integration tests: {e}")
        print("Skipping integration tests. Run unit tests instead:")
        print("python -m pytest tests/test_database.py -v")