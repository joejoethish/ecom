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
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .interfaces import Environment, TestModule
from .config import get_config, get_value
from .logging_utils import get_logger


class DatabaseManager:
    """Manages database connections and operations for testing framework"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.logger = get_logger("database", TestModule.DATABASE)
        self.connection = None
        self.transaction_stack = []
        self._backup_files = {}
        
        # Load database configuration
        self.config = get_config("database", environment)
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 5432)
        self.database = self.config.get("name", f"qa_test_{environment.value}")
        self.user = self.config.get("user", "qa_user")
        self.password = self.config.get("password", "qa_password")
        
        # Connection parameters
        self.connection_params = {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password
        }
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            if self.connection and not self.connection.closed:
                return True
            
            self.connection = psycopg2.connect(**self.connection_params)
            self.logger.info(f"Connected to database: {self.database}")
            return True
            
        except psycopg2.Error as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Close database connection"""
        try:
            if self.connection and not self.connection.closed:
                # Rollback any pending transactions
                if self.transaction_stack:
                    self.connection.rollback()
                    self.transaction_stack.clear()
                
                self.connection.close()
                self.logger.info("Database connection closed")
                
        except psycopg2.Error as e:
            self.logger.error(f"Error closing database connection: {str(e)}")
    
    def is_connected(self) -> bool:
        """Check if database connection is active"""
        try:
            if not self.connection or self.connection.closed:
                return False
            
            # Test connection with a simple query
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
                
        except psycopg2.Error:
            return False
    
    def create_database(self, database_name: Optional[str] = None) -> bool:
        """Create test database if it doesn't exist"""
        try:
            db_name = database_name or self.database
            
            # Connect to default postgres database to create new database
            temp_params = self.connection_params.copy()
            temp_params["database"] = "postgres"
            
            with psycopg2.connect(**temp_params) as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                
                with conn.cursor() as cursor:
                    # Check if database exists
                    cursor.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s",
                        (db_name,)
                    )
                    
                    if not cursor.fetchone():
                        # Create database
                        cursor.execute(
                            sql.SQL("CREATE DATABASE {}").format(
                                sql.Identifier(db_name)
                            )
                        )
                        self.logger.info(f"Created database: {db_name}")
                    else:
                        self.logger.info(f"Database already exists: {db_name}")
            
            return True
            
        except psycopg2.Error as e:
            self.logger.error(f"Failed to create database {db_name}: {str(e)}")
            return False
    
    def drop_database(self, database_name: Optional[str] = None) -> bool:
        """Drop test database"""
        try:
            db_name = database_name or self.database
            
            # Disconnect from target database first
            if self.connection and not self.connection.closed:
                self.disconnect()
            
            # Connect to default postgres database to drop target database
            temp_params = self.connection_params.copy()
            temp_params["database"] = "postgres"
            
            with psycopg2.connect(**temp_params) as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                
                with conn.cursor() as cursor:
                    # Terminate existing connections to the database
                    cursor.execute("""
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = %s AND pid <> pg_backend_pid()
                    """, (db_name,))
                    
                    # Drop database
                    cursor.execute(
                        sql.SQL("DROP DATABASE IF EXISTS {}").format(
                            sql.Identifier(db_name)
                        )
                    )
                    self.logger.info(f"Dropped database: {db_name}")
            
            return True
            
        except psycopg2.Error as e:
            self.logger.error(f"Failed to drop database {db_name}: {str(e)}")
            return False
    
    def setup_test_schema(self) -> bool:
        """Setup test database schema"""
        try:
            if not self.connect():
                return False
            
            schema_sql = self._get_test_schema_sql()
            
            with self.connection.cursor() as cursor:
                cursor.execute(schema_sql)
                self.connection.commit()
                
            self.logger.info("Test schema setup completed")
            return True
            
        except psycopg2.Error as e:
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
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                    AND tablename NOT LIKE 'pg_%'
                    AND tablename NOT LIKE 'sql_%'
                """)
                
                tables = cursor.fetchall()
                
                # Drop all tables
                for (table_name,) in tables:
                    cursor.execute(
                        sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                            sql.Identifier(table_name)
                        )
                    )
                
                self.connection.commit()
                
            self.logger.info("Test schema teardown completed")
            return True
            
        except psycopg2.Error as e:
            self.logger.error(f"Failed to teardown test schema: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    @contextmanager
    def transaction(self, isolation_level: Optional[str] = None):
        """Context manager for database transactions with isolation"""
        if not self.connect():
            raise psycopg2.Error("Failed to connect to database")
        
        # Set isolation level if specified
        if isolation_level:
            old_isolation = self.connection.isolation_level
            self.connection.set_isolation_level(
                getattr(psycopg2.extensions, f"ISOLATION_LEVEL_{isolation_level.upper()}")
            )
        
        # Start transaction
        savepoint_name = f"sp_{len(self.transaction_stack)}"
        self.transaction_stack.append(savepoint_name)
        
        try:
            with self.connection.cursor() as cursor:
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
                with self.connection.cursor() as cursor:
                    cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
            else:
                self.connection.rollback()
            raise e
            
        finally:
            self.transaction_stack.pop()
            
            # Restore isolation level
            if isolation_level:
                self.connection.set_isolation_level(old_isolation)
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """Execute SELECT query and return results"""
        try:
            if not self.connect():
                return []
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except psycopg2.Error as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            return []
    
    def execute_command(self, command: str, params: Optional[Tuple] = None) -> bool:
        """Execute INSERT/UPDATE/DELETE command"""
        try:
            if not self.connect():
                return False
            
            with self.connection.cursor() as cursor:
                cursor.execute(command, params)
                self.connection.commit()
                return True
                
        except psycopg2.Error as e:
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
            
            # Use pg_dump to create backup
            dump_command = [
                "pg_dump",
                "-h", self.host,
                "-p", str(self.port),
                "-U", self.user,
                "-d", self.database,
                "-f", backup_file,
                "--no-password"
            ]
            
            # Set password via environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.password
            
            result = subprocess.run(
                dump_command,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
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
            
            # Use psql to restore backup
            restore_command = [
                "psql",
                "-h", self.host,
                "-p", str(self.port),
                "-U", self.user,
                "-d", target_db,
                "-f", backup_file,
                "--no-password"
            ]
            
            # Set password via environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.password
            
            result = subprocess.run(
                restore_command,
                env=env,
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
            
            with self.connection.cursor() as cursor:
                # Get table columns
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = cursor.fetchall()
                
                # Get table row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
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
                
        except psycopg2.Error as e:
            self.logger.error(f"Failed to get table info for {table_name}: {str(e)}")
            return {}
    
    def truncate_tables(self, table_names: List[str]) -> bool:
        """Truncate specified tables"""
        try:
            if not self.connect():
                return False
            
            with self.connection.cursor() as cursor:
                for table_name in table_names:
                    cursor.execute(
                        sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                            sql.Identifier(table_name)
                        )
                    )
                
                self.connection.commit()
                self.logger.info(f"Truncated tables: {', '.join(table_names)}")
                return True
                
        except psycopg2.Error as e:
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
            profile_data JSONB,
            is_active BOOLEAN DEFAULT TRUE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Test User Addresses Table
        CREATE TABLE IF NOT EXISTS test_user_addresses (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) REFERENCES test_users(id) ON DELETE CASCADE,
            street VARCHAR(255) NOT NULL,
            city VARCHAR(100) NOT NULL,
            state VARCHAR(100) NOT NULL,
            postal_code VARCHAR(20) NOT NULL,
            country VARCHAR(100) NOT NULL,
            address_type VARCHAR(20) DEFAULT 'shipping'
        );
        
        -- Test User Payment Methods Table
        CREATE TABLE IF NOT EXISTS test_user_payment_methods (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) REFERENCES test_users(id) ON DELETE CASCADE,
            type VARCHAR(20) NOT NULL,
            details JSONB NOT NULL,
            is_default BOOLEAN DEFAULT FALSE
        );
        
        -- Test Products Table
        CREATE TABLE IF NOT EXISTS test_products (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(100) NOT NULL,
            subcategory VARCHAR(100),
            price DECIMAL(10,2) NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            seller_id VARCHAR(50),
            status VARCHAR(20) DEFAULT 'active',
            images JSONB,
            attributes JSONB,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Test Product Variants Table
        CREATE TABLE IF NOT EXISTS test_product_variants (
            id VARCHAR(50) PRIMARY KEY,
            product_id VARCHAR(50) REFERENCES test_products(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            sku VARCHAR(100) UNIQUE NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            attributes JSONB,
            stock_quantity INTEGER DEFAULT 0
        );
        
        -- Test Cases Table
        CREATE TABLE IF NOT EXISTS test_cases (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            module VARCHAR(50) NOT NULL,
            priority VARCHAR(20) NOT NULL,
            user_role VARCHAR(20) NOT NULL,
            expected_result TEXT NOT NULL,
            prerequisites JSONB,
            tags JSONB,
            estimated_duration INTEGER DEFAULT 0,
            requirements JSONB,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(100) DEFAULT 'qa_framework'
        );
        
        -- Test Steps Table
        CREATE TABLE IF NOT EXISTS test_steps (
            id SERIAL PRIMARY KEY,
            test_case_id VARCHAR(50) REFERENCES test_cases(id) ON DELETE CASCADE,
            step_number INTEGER NOT NULL,
            description TEXT NOT NULL,
            action TEXT NOT NULL,
            expected_result TEXT NOT NULL,
            actual_result TEXT,
            status VARCHAR(20),
            screenshot_path VARCHAR(500),
            duration DECIMAL(10,3)
        );
        
        -- Test Executions Table
        CREATE TABLE IF NOT EXISTS test_executions (
            id VARCHAR(50) PRIMARY KEY,
            test_case_id VARCHAR(50) REFERENCES test_cases(id),
            environment VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            actual_result TEXT,
            screenshots JSONB,
            logs JSONB,
            defects JSONB,
            browser_info JSONB,
            device_info JSONB,
            executed_by VARCHAR(100) DEFAULT 'qa_framework'
        );
        
        -- Test Defects Table
        CREATE TABLE IF NOT EXISTS test_defects (
            id VARCHAR(50) PRIMARY KEY,
            test_case_id VARCHAR(50) REFERENCES test_cases(id),
            test_execution_id VARCHAR(50) REFERENCES test_executions(id),
            severity VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'open',
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            reproduction_steps JSONB,
            environment VARCHAR(20),
            browser_info JSONB,
            device_info JSONB,
            screenshots JSONB,
            logs JSONB,
            assigned_to VARCHAR(100),
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_date TIMESTAMP,
            created_by VARCHAR(100) DEFAULT 'qa_framework',
            tags JSONB
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_test_users_email ON test_users(email);
        CREATE INDEX IF NOT EXISTS idx_test_users_type ON test_users(user_type);
        CREATE INDEX IF NOT EXISTS idx_test_products_category ON test_products(category);
        CREATE INDEX IF NOT EXISTS idx_test_products_status ON test_products(status);
        CREATE INDEX IF NOT EXISTS idx_test_cases_module ON test_cases(module);
        CREATE INDEX IF NOT EXISTS idx_test_cases_priority ON test_cases(priority);
        CREATE INDEX IF NOT EXISTS idx_test_executions_status ON test_executions(status);
        CREATE INDEX IF NOT EXISTS idx_test_executions_environment ON test_executions(environment);
        CREATE INDEX IF NOT EXISTS idx_test_defects_severity ON test_defects(severity);
        CREATE INDEX IF NOT EXISTS idx_test_defects_status ON test_defects(status);
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