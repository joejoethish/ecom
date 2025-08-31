"""
Database Connection and Setup Utilities for QA Testing Framework

Provides database connection management, schema setup/teardown, transaction management,
and backup/restore utilities for PostgreSQL testing environments.
"""

import os
import json
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error as MySQLError
import pymysql

from .interfaces import Environment, TestModule
from .config import get_config, get_value
from .logging_utils import get_logger
import logging


class DatabaseManager:
    """Manages database connections and operations for testing framework"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        # Use standard Python logger for database operations
        self.logger = logging.getLogger(f"qa_framework.database.{environment.value}")
        self._setup_logger()
        self.connection = None
        self.transaction_stack = []
        self._backup_files = {}
        
        # Load database configuration
        self.config = get_config("database", environment)
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 3307)
        self.database = self.config.get("name", f"qa_test_{environment.value}")
        self.user = self.config.get("user", "qa_user")
        self.password = self.config.get("password", "qa_password")
        self.charset = self.config.get("charset", "utf8mb4")
        
        # Connection parameters
        self.connection_params = {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "charset": self.charset,
            "autocommit": False
        }
    
    def _setup_logger(self) -> None:
        """Setup standard logger for database operations"""
        if self.logger.handlers:
            return  # Already configured
        
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            if self.connection and self.connection.is_connected():
                return True
            
            self.connection = mysql.connector.connect(**self.connection_params)
            self.logger.info(f"Connected to database: {self.database}")
            return True
            
        except MySQLError as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Close database connection"""
        try:
            if self.connection and self.connection.is_connected():
                # Rollback any pending transactions
                if self.transaction_stack:
                    self.connection.rollback()
                    self.transaction_stack.clear()
                
                self.connection.close()
                self.logger.info("Database connection closed")
                
        except MySQLError as e:
            self.logger.error(f"Error closing database connection: {str(e)}")
    
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        try:
            if not self.connection or not self.connection.is_connected():
                return False
            
            # Test connection with a simple query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
                
        except MySQLError:
            return False
    
    def create_database(self, database_name: Optional[str] = None) -> bool:
        """Create test database if it doesn't exist"""
        try:
            db_name = database_name or self.database
            
            # Connect without specifying database to create new database
            temp_params = self.connection_params.copy()
            temp_params.pop("database", None)
            
            with mysql.connector.connect(**temp_params) as conn:
                cursor = conn.cursor()
                
                # Check if database exists
                cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
                
                if not cursor.fetchone():
                    # Create database
                    cursor.execute(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    self.logger.info(f"Created database: {db_name}")
                else:
                    self.logger.info(f"Database already exists: {db_name}")
                
                cursor.close()
            
            return True
            
        except MySQLError as e:
            self.logger.error(f"Failed to create database {db_name}: {str(e)}")
            return False
    
    def drop_database(self, database_name: Optional[str] = None) -> bool:
        """Drop test database"""
        try:
            db_name = database_name or self.database
            
            # Disconnect from target database first
            if self.connection and self.connection.is_connected():
                self.disconnect()
            
            # Connect without specifying database to drop target database
            temp_params = self.connection_params.copy()
            temp_params.pop("database", None)
            
            with mysql.connector.connect(**temp_params) as conn:
                cursor = conn.cursor()
                
                # Drop database
                cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
                self.logger.info(f"Dropped database: {db_name}")
                
                cursor.close()
            
            return True
            
        except MySQLError as e:
            self.logger.error(f"Failed to drop database {db_name}: {str(e)}")
            return False
    
    def setup_test_schema(self) -> bool:
        """Setup test database schema"""
        try:
            if not self.connect():
                return False
            
            schema_sql = self._get_test_schema_sql()
            
            cursor = self.connection.cursor()
            # Execute each statement separately for MySQL
            for statement in schema_sql.split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            
            self.connection.commit()
            cursor.close()
                
            self.logger.info("Test schema setup completed")
            return True
            
        except MySQLError as e:
            self.logger.error(f"Failed to setup test schema: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def teardown_test_schema(self) -> bool:
        """Teardown test database schema"""
        try:
            if not self.connect():
                return False
            
            # Get all tables in the current database
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            # Disable foreign key checks temporarily
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # Drop all tables
            for (table_name,) in tables:
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            self.connection.commit()
            cursor.close()
                
            self.logger.info("Test schema teardown completed")
            return True
            
        except MySQLError as e:
            self.logger.error(f"Failed to teardown test schema: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    @contextmanager
    def transaction(self, isolation_level: Optional[str] = None):
        """Context manager for database transactions with isolation"""
        if not self.connect():
            raise MySQLError("Failed to connect to database")
        
        # Set isolation level if specified
        old_isolation = None
        if isolation_level:
            cursor = self.connection.cursor()
            cursor.execute("SELECT @@transaction_isolation")
            old_isolation = cursor.fetchone()[0]
            cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation_level.upper().replace('_', ' ')}")
            cursor.close()
        
        # Start transaction
        savepoint_name = f"sp_{len(self.transaction_stack)}"
        self.transaction_stack.append(savepoint_name)
        
        cursor = self.connection.cursor()
        
        try:
            if len(self.transaction_stack) > 1:
                # Use savepoint for nested transactions
                cursor.execute(f"SAVEPOINT {savepoint_name}")
            
            yield cursor
            
            if len(self.transaction_stack) > 1:
                cursor.execute(f"RELEASE SAVEPOINT {savepoint_name}")
            else:
                self.connection.commit()
                
        except Exception as e:
            if len(self.transaction_stack) > 1:
                cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
            else:
                self.connection.rollback()
            raise e
            
        finally:
            cursor.close()
            self.transaction_stack.pop()
            
            # Restore isolation level
            if isolation_level and old_isolation:
                cursor = self.connection.cursor()
                cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {old_isolation}")
                cursor.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """Execute SELECT query and return results"""
        try:
            if not self.connect():
                return []
            
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
                
        except MySQLError as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            return []
    
    def execute_command(self, command: str, params: Optional[Tuple] = None) -> bool:
        """Execute INSERT/UPDATE/DELETE command"""
        try:
            if not self.connect():
                return False
            
            cursor = self.connection.cursor()
            cursor.execute(command, params)
            self.connection.commit()
            cursor.close()
            return True
                
        except MySQLError as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def backup_database(self, backup_name: Optional[str] = None) -> str:
        """Create database backup and return backup file path"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{self.database}_backup_{timestamp}"
            
            # Create temporary backup file
            backup_file = os.path.join(tempfile.gettempdir(), f"{backup_name}.sql")
            
            # Use mysqldump to create backup
            dump_command = [
                "mysqldump",
                "-h", self.host,
                "-P", str(self.port),
                "-u", self.user,
                f"-p{self.password}",
                "--single-transaction",
                "--routines",
                "--triggers",
                self.database
            ]
            
            result = subprocess.run(
                dump_command,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                self._backup_files[backup_name] = backup_file
                self.logger.info(f"Database backup created: {backup_file}")
                return backup_file
            else:
                self.logger.error(f"Backup failed: {result.stderr}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Failed to create database backup: {str(e)}")
            return ""
    
    def restore_database(self, backup_file: str, target_database: Optional[str] = None) -> bool:
        """Restore database from backup file"""
        try:
            target_db = target_database or self.database
            
            # Ensure backup file exists
            if not os.path.exists(backup_file):
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Drop and recreate target database
            if not self.drop_database(target_db):
                return False
            
            if not self.create_database(target_db):
                return False
            
            # Use mysql to restore backup
            restore_command = [
                "mysql",
                "-h", self.host,
                "-P", str(self.port),
                "-u", self.user,
                f"-p{self.password}",
                target_db
            ]
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                result = subprocess.run(
                    restore_command,
                    stdin=f,
                    capture_output=True,
                    text=True
                )
            
            if result.returncode == 0:
                self.logger.info(f"Database restored from: {backup_file}")
                return True
            else:
                self.logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to restore database: {str(e)}")
            return False
    
    def cleanup_backups(self) -> None:
        """Clean up temporary backup files"""
        for backup_name, backup_file in self._backup_files.items():
            try:
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                    self.logger.info(f"Cleaned up backup file: {backup_file}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup backup {backup_file}: {str(e)}")
        
        self._backup_files.clear()
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table"""
        try:
            if not self.connect():
                return {}
            
            cursor = self.connection.cursor()
            
            # Get table columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = %s
                ORDER BY ordinal_position
            """, (table_name, self.database))
            
            columns = cursor.fetchall()
            
            # Get table row count
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2] == "YES",
                        "default": col[3]
                    }
                    for col in columns
                ],
                "row_count": row_count
            }
                
        except MySQLError as e:
            self.logger.error(f"Failed to get table info for {table_name}: {str(e)}")
            return {}
    
    def truncate_tables(self, table_names: List[str]) -> bool:
        """Truncate specified tables"""
        try:
            if not self.connect():
                return False
            
            cursor = self.connection.cursor()
            
            # Disable foreign key checks temporarily
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            for table_name in table_names:
                cursor.execute(f"TRUNCATE TABLE `{table_name}`")
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            self.connection.commit()
            cursor.close()
            self.logger.info(f"Truncated tables: {', '.join(table_names)}")
            return True
                
        except MySQLError as e:
            self.logger.error(f"Failed to truncate tables: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _get_test_schema_sql(self) -> str:
        """Get SQL for creating test database schema"""
        return """
        -- Test Users Table
        CREATE TABLE IF NOT EXISTS test_users (
            id VARCHAR(50) PRIMARY KEY,
            user_type VARCHAR(20) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            phone VARCHAR(20),
            profile_data JSON,
            is_active BOOLEAN DEFAULT TRUE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        -- Test User Addresses Table
        CREATE TABLE IF NOT EXISTS test_user_addresses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50),
            street VARCHAR(255) NOT NULL,
            city VARCHAR(100) NOT NULL,
            state VARCHAR(100) NOT NULL,
            postal_code VARCHAR(20) NOT NULL,
            country VARCHAR(100) NOT NULL,
            address_type VARCHAR(20) DEFAULT 'shipping',
            FOREIGN KEY (user_id) REFERENCES test_users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        -- Test User Payment Methods Table
        CREATE TABLE IF NOT EXISTS test_user_payment_methods (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50),
            type VARCHAR(20) NOT NULL,
            details JSON NOT NULL,
            is_default BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES test_users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        -- Test Products Table
        CREATE TABLE IF NOT EXISTS test_products (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(100) NOT NULL,
            subcategory VARCHAR(100),
            price DECIMAL(10,2) NOT NULL,
            stock_quantity INT DEFAULT 0,
            seller_id VARCHAR(50),
            status VARCHAR(20) DEFAULT 'active',
            images JSON,
            attributes JSON,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        -- Test Product Variants Table
        CREATE TABLE IF NOT EXISTS test_product_variants (
            id VARCHAR(50) PRIMARY KEY,
            product_id VARCHAR(50),
            name VARCHAR(255) NOT NULL,
            sku VARCHAR(100) UNIQUE NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            attributes JSON,
            stock_quantity INT DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES test_products(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        -- Test Cases Table
        CREATE TABLE IF NOT EXISTS test_cases (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            module VARCHAR(50) NOT NULL,
            priority VARCHAR(20) NOT NULL,
            user_role VARCHAR(20) NOT NULL,
            expected_result TEXT NOT NULL,
            prerequisites JSON,
            tags JSON,
            estimated_duration INT DEFAULT 0,
            requirements JSON,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by VARCHAR(100) DEFAULT 'qa_framework'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        -- Test Steps Table
        CREATE TABLE IF NOT EXISTS test_steps (
            id INT AUTO_INCREMENT PRIMARY KEY,
            test_case_id VARCHAR(50),
            step_number INT NOT NULL,
            description TEXT NOT NULL,
            action TEXT NOT NULL,
            expected_result TEXT NOT NULL,
            actual_result TEXT,
            status VARCHAR(20),
            screenshot_path VARCHAR(500),
            duration DECIMAL(10,3),
            FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        -- Test Executions Table
        CREATE TABLE IF NOT EXISTS test_executions (
            id VARCHAR(50) PRIMARY KEY,
            test_case_id VARCHAR(50),
            environment VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NULL,
            actual_result TEXT,
            screenshots JSON,
            logs JSON,
            defects JSON,
            browser_info JSON,
            device_info JSON,
            executed_by VARCHAR(100) DEFAULT 'qa_framework',
            FOREIGN KEY (test_case_id) REFERENCES test_cases(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        -- Test Defects Table
        CREATE TABLE IF NOT EXISTS test_defects (
            id VARCHAR(50) PRIMARY KEY,
            test_case_id VARCHAR(50),
            test_execution_id VARCHAR(50),
            severity VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'open',
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            reproduction_steps JSON,
            environment VARCHAR(20),
            browser_info JSON,
            device_info JSON,
            screenshots JSON,
            logs JSON,
            assigned_to VARCHAR(100),
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_date TIMESTAMP NULL,
            created_by VARCHAR(100) DEFAULT 'qa_framework',
            tags JSON,
            FOREIGN KEY (test_case_id) REFERENCES test_cases(id),
            FOREIGN KEY (test_execution_id) REFERENCES test_executions(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        
        -- Create indexes for better performance
        CREATE INDEX idx_test_users_email ON test_users(email);
        CREATE INDEX idx_test_users_type ON test_users(user_type);
        CREATE INDEX idx_test_products_category ON test_products(category);
        CREATE INDEX idx_test_products_status ON test_products(status);
        CREATE INDEX idx_test_cases_module ON test_cases(module);
        CREATE INDEX idx_test_cases_priority ON test_cases(priority);
        CREATE INDEX idx_test_executions_status ON test_executions(status);
        CREATE INDEX idx_test_executions_environment ON test_executions(environment);
        CREATE INDEX idx_test_defects_severity ON test_defects(severity);
        CREATE INDEX idx_test_defects_status ON test_defects(status);
        """
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        self.cleanup_backups()


# Global database manager instances for different environments
_db_managers = {}

def get_database_manager(environment: Environment = Environment.DEVELOPMENT) -> DatabaseManager:
    """Get database manager instance for specified environment"""
    if environment not in _db_managers:
        _db_managers[environment] = DatabaseManager(environment)
    return _db_managers[environment]