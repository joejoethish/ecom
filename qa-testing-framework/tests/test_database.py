"""
Integration Tests for Database Utilities

Tests database connection management, schema setup/teardown, transaction management,
and backup/restore functionality.
"""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock, call
import psycopg2

from core.database import DatabaseManager, get_database_manager
from core.interfaces import Environment


class DatabaseManagerTests(unittest.TestCase):
    """Test cases for DatabaseManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.environment = Environment.DEVELOPMENT
        self.db_manager = DatabaseManager(self.environment)
        
        # Mock database configuration
        self.mock_config = {
            "host": "localhost",
            "port": 5432,
            "name": "test_qa_framework",
            "user": "test_user",
            "password": "test_password"
        }
    
    def test_initialization(self):
        """Test DatabaseManager initialization"""
        self.assertEqual(self.db_manager.environment, self.environment)
        self.assertIsNone(self.db_manager.connection)
        self.assertEqual(self.db_manager.transaction_stack, [])
        self.assertIsInstance(self.db_manager._backup_files, dict)
    
    @patch('core.database.get_config')
    def test_initialization_with_config(self, mock_get_config):
        """Test DatabaseManager initialization with configuration"""
        mock_get_config.return_value = self.mock_config
        
        db_manager = DatabaseManager(Environment.STAGING)
        
        self.assertEqual(db_manager.host, "localhost")
        self.assertEqual(db_manager.port, 5432)
        self.assertEqual(db_manager.database, "test_qa_framework")
        self.assertEqual(db_manager.user, "test_user")
        self.assertEqual(db_manager.password, "test_password")
    
    @patch('psycopg2.connect')
    def test_connect_success(self, mock_connect):
        """Test successful database connection"""
        mock_connection = MagicMock()
        mock_connection.closed = 0
        mock_connect.return_value = mock_connection
        
        result = self.db_manager.connect()
        
        self.assertTrue(result)
        self.assertEqual(self.db_manager.connection, mock_connection)
        mock_connect.assert_called_once_with(**self.db_manager.connection_params)
    
    @patch('psycopg2.connect')
    def test_connect_failure(self, mock_connect):
        """Test database connection failure"""
        mock_connect.side_effect = psycopg2.Error("Connection failed")
        
        result = self.db_manager.connect()
        
        self.assertFalse(result)
        self.assertIsNone(self.db_manager.connection)
    
    @patch('psycopg2.connect')
    def test_connect_already_connected(self, mock_connect):
        """Test connection when already connected"""
        mock_connection = MagicMock()
        mock_connection.closed = 0
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.connect()
        
        self.assertTrue(result)
        mock_connect.assert_not_called()
    
    def test_disconnect_success(self):
        """Test successful database disconnection"""
        mock_connection = MagicMock()
        mock_connection.closed = 0
        self.db_manager.connection = mock_connection
        
        self.db_manager.disconnect()
        
        mock_connection.close.assert_called_once()
    
    def test_disconnect_with_transactions(self):
        """Test disconnection with pending transactions"""
        mock_connection = MagicMock()
        mock_connection.closed = 0
        self.db_manager.connection = mock_connection
        self.db_manager.transaction_stack = ["sp_0", "sp_1"]
        
        self.db_manager.disconnect()
        
        mock_connection.rollback.assert_called_once()
        self.assertEqual(self.db_manager.transaction_stack, [])
        mock_connection.close.assert_called_once()
    
    def test_is_connected_true(self):
        """Test is_connected when connected"""
        mock_connection = MagicMock()
        mock_connection.closed = 0
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.is_connected()
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once_with("SELECT 1")
    
    def test_is_connected_false_no_connection(self):
        """Test is_connected when no connection"""
        self.db_manager.connection = None
        
        result = self.db_manager.is_connected()
        
        self.assertFalse(result)
    
    def test_is_connected_false_closed_connection(self):
        """Test is_connected when connection is closed"""
        mock_connection = MagicMock()
        mock_connection.closed = 1
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.is_connected()
        
        self.assertFalse(result)
    
    @patch('psycopg2.connect')
    def test_create_database_success(self, mock_connect):
        """Test successful database creation"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_connection
        
        # Mock database doesn't exist
        mock_cursor.fetchone.return_value = None
        
        result = self.db_manager.create_database("test_db")
        
        self.assertTrue(result)
        mock_cursor.execute.assert_any_call(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            ("test_db",)
        )
    
    @patch('psycopg2.connect')
    def test_create_database_already_exists(self, mock_connect):
        """Test database creation when database already exists"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_connection
        
        # Mock database exists
        mock_cursor.fetchone.return_value = (1,)
        
        result = self.db_manager.create_database("test_db")
        
        self.assertTrue(result)
        # Should not execute CREATE DATABASE
        create_calls = [call for call in mock_cursor.execute.call_args_list 
                       if "CREATE DATABASE" in str(call)]
        self.assertEqual(len(create_calls), 0)
    
    @patch('psycopg2.connect')
    def test_drop_database_success(self, mock_connect):
        """Test successful database drop"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_connection
        
        # Mock existing connection
        self.db_manager.connection = MagicMock()
        
        result = self.db_manager.drop_database("test_db")
        
        self.assertTrue(result)
        # Should terminate connections and drop database
        self.assertEqual(mock_cursor.execute.call_count, 2)
    
    @patch('core.database.DatabaseManager.connect')
    def test_setup_test_schema_success(self, mock_connect):
        """Test successful test schema setup"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.setup_test_schema()
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
    
    @patch('core.database.DatabaseManager.connect')
    def test_setup_test_schema_failure(self, mock_connect):
        """Test test schema setup failure"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("Schema setup failed")
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.setup_test_schema()
        
        self.assertFalse(result)
        mock_connection.rollback.assert_called_once()
    
    @patch('core.database.DatabaseManager.connect')
    def test_teardown_test_schema_success(self, mock_connect):
        """Test successful test schema teardown"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        # Mock table list
        mock_cursor.fetchall.return_value = [("test_users",), ("test_products",)]
        
        result = self.db_manager.teardown_test_schema()
        
        self.assertTrue(result)
        # Should execute SELECT for tables and DROP for each table
        self.assertGreaterEqual(mock_cursor.execute.call_count, 3)
        mock_connection.commit.assert_called_once()
    
    @patch('core.database.DatabaseManager.connect')
    def test_execute_query_success(self, mock_connect):
        """Test successful query execution"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, "test"), (2, "data")]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.execute_query("SELECT * FROM test_table", ("param",))
        
        self.assertEqual(result, [(1, "test"), (2, "data")])
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table", ("param",))
    
    @patch('core.database.DatabaseManager.connect')
    def test_execute_query_failure(self, mock_connect):
        """Test query execution failure"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("Query failed")
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.execute_query("SELECT * FROM test_table")
        
        self.assertEqual(result, [])
    
    @patch('core.database.DatabaseManager.connect')
    def test_execute_command_success(self, mock_connect):
        """Test successful command execution"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.execute_command("INSERT INTO test_table VALUES (%s)", ("value",))
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once_with("INSERT INTO test_table VALUES (%s)", ("value",))
        mock_connection.commit.assert_called_once()
    
    @patch('core.database.DatabaseManager.connect')
    def test_execute_command_failure(self, mock_connect):
        """Test command execution failure"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("Command failed")
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.execute_command("INSERT INTO test_table VALUES (%s)", ("value",))
        
        self.assertFalse(result)
        mock_connection.rollback.assert_called_once()
    
    @patch('core.database.DatabaseManager.connect')
    def test_transaction_context_manager_success(self, mock_connect):
        """Test transaction context manager success"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        with self.db_manager.transaction() as cursor:
            cursor.execute("INSERT INTO test_table VALUES (%s)", ("value",))
        
        mock_connection.commit.assert_called_once()
        self.assertEqual(len(self.db_manager.transaction_stack), 0)
    
    @patch('core.database.DatabaseManager.connect')
    def test_transaction_context_manager_failure(self, mock_connect):
        """Test transaction context manager with exception"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("Transaction failed")
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        with self.assertRaises(psycopg2.Error):
            with self.db_manager.transaction() as cursor:
                cursor.execute("INSERT INTO test_table VALUES (%s)", ("value",))
        
        mock_connection.rollback.assert_called_once()
        self.assertEqual(len(self.db_manager.transaction_stack), 0)
    
    @patch('subprocess.run')
    @patch('tempfile.gettempdir')
    def test_backup_database_success(self, mock_tempdir, mock_subprocess):
        """Test successful database backup"""
        mock_tempdir.return_value = "/tmp"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        backup_file = self.db_manager.backup_database("test_backup")
        
        self.assertTrue(backup_file.endswith("test_backup.sql"))
        self.assertIn("test_backup", self.db_manager._backup_files)
        mock_subprocess.assert_called_once()
    
    @patch('subprocess.run')
    def test_backup_database_failure(self, mock_subprocess):
        """Test database backup failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Backup failed"
        mock_subprocess.return_value = mock_result
        
        backup_file = self.db_manager.backup_database("test_backup")
        
        self.assertEqual(backup_file, "")
        self.assertNotIn("test_backup", self.db_manager._backup_files)
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('core.database.DatabaseManager.drop_database')
    @patch('core.database.DatabaseManager.create_database')
    def test_restore_database_success(self, mock_create, mock_drop, mock_exists, mock_subprocess):
        """Test successful database restore"""
        mock_exists.return_value = True
        mock_drop.return_value = True
        mock_create.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = self.db_manager.restore_database("/tmp/backup.sql", "target_db")
        
        self.assertTrue(result)
        mock_drop.assert_called_once_with("target_db")
        mock_create.assert_called_once_with("target_db")
        mock_subprocess.assert_called_once()
    
    @patch('os.path.exists')
    def test_restore_database_file_not_found(self, mock_exists):
        """Test database restore with missing backup file"""
        mock_exists.return_value = False
        
        result = self.db_manager.restore_database("/tmp/nonexistent.sql")
        
        self.assertFalse(result)
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_cleanup_backups(self, mock_remove, mock_exists):
        """Test backup cleanup"""
        mock_exists.return_value = True
        self.db_manager._backup_files = {
            "backup1": "/tmp/backup1.sql",
            "backup2": "/tmp/backup2.sql"
        }
        
        self.db_manager.cleanup_backups()
        
        self.assertEqual(mock_remove.call_count, 2)
        self.assertEqual(len(self.db_manager._backup_files), 0)
    
    @patch('core.database.DatabaseManager.connect')
    def test_get_table_info_success(self, mock_connect):
        """Test successful table info retrieval"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        # Mock column info and row count
        mock_cursor.fetchall.return_value = [
            ("id", "varchar", "NO", None),
            ("name", "varchar", "YES", "default_name")
        ]
        mock_cursor.fetchone.return_value = (100,)
        
        result = self.db_manager.get_table_info("test_table")
        
        self.assertEqual(result["table_name"], "test_table")
        self.assertEqual(len(result["columns"]), 2)
        self.assertEqual(result["row_count"], 100)
        self.assertEqual(result["columns"][0]["name"], "id")
        self.assertFalse(result["columns"][0]["nullable"])
        self.assertTrue(result["columns"][1]["nullable"])
    
    @patch('core.database.DatabaseManager.connect')
    def test_truncate_tables_success(self, mock_connect):
        """Test successful table truncation"""
        mock_connect.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.db_manager.connection = mock_connection
        
        result = self.db_manager.truncate_tables(["table1", "table2"])
        
        self.assertTrue(result)
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_connection.commit.assert_called_once()
    
    def test_context_manager(self):
        """Test DatabaseManager as context manager"""
        with patch.object(self.db_manager, 'connect') as mock_connect, \
             patch.object(self.db_manager, 'disconnect') as mock_disconnect, \
             patch.object(self.db_manager, 'cleanup_backups') as mock_cleanup:
            
            with self.db_manager as db:
                self.assertEqual(db, self.db_manager)
            
            mock_connect.assert_called_once()
            mock_disconnect.assert_called_once()
            mock_cleanup.assert_called_once()
    
    def test_get_database_manager_singleton(self):
        """Test get_database_manager returns singleton instances"""
        manager1 = get_database_manager(Environment.DEVELOPMENT)
        manager2 = get_database_manager(Environment.DEVELOPMENT)
        manager3 = get_database_manager(Environment.STAGING)
        
        self.assertIs(manager1, manager2)
        self.assertIsNot(manager1, manager3)
        self.assertEqual(manager1.environment, Environment.DEVELOPMENT)
        self.assertEqual(manager3.environment, Environment.STAGING)


if __name__ == '__main__':
    unittest.main()