"""
Database Connection Management for QA Testing Framework

Handles MySQL/PostgreSQL database connections, connection pooling,
and transaction management for testing purposes.
"""

import mysql.connector
import psycopg2
from psycopg2 import pool
import pymysql
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Union
import logging
import time
from datetime import datetime

from ..core.interfaces import Environment
from ..core.config import ConfigManager


class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors"""
    pass


class DatabaseConnection:
    """Database connection manager with support for MySQL and PostgreSQL"""
    
    def __init__(self, config: Dict[str, Any], db_type: str = "mysql"):
        """
        Initialize database connection
        
        Args:
            config: Database configuration dictionary
            db_type: Database type ('mysql' or 'postgresql')
        """
        self.config = config
        self.db_type = db_type.lower()
        self.engine = None
        self.session_factory = None
        self.connection_pool = None
        self.logger = logging.getLogger(__name__)
        
        # Validate database type
        if self.db_type not in ['mysql', 'postgresql']:
            raise ValueError("Database type must be 'mysql' or 'postgresql'")
        
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection and session factory"""
        try:
            # Build connection string based on database type
            if self.db_type == 'mysql':
                connection_string = self._build_mysql_connection_string()
            else:
                connection_string = self._build_postgresql_connection_string()
            
            # Create SQLAlchemy engine with connection pooling
            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=self.config.get('pool_size', 5),
                max_overflow=self.config.get('max_overflow', 10),
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.config.get('echo_sql', False)
            )
            
            # Create session factory
            self.session_factory = sessionmaker(bind=self.engine)
            
            # Test connection
            self._test_connection()
            
            self.logger.info(f"Database connection initialized successfully ({self.db_type})")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database connection: {str(e)}")
            raise DatabaseConnectionError(f"Database connection failed: {str(e)}")
    
    def _build_mysql_connection_string(self) -> str:
        """Build MySQL connection string"""
        host = self.config['host']
        port = self.config.get('port', 3306)
        database = self.config['name']
        user = self.config['user']
        password = self.config['password']
        charset = self.config.get('charset', 'utf8mb4')
        
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"
    
    def _build_postgresql_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        host = self.config['host']
        port = self.config.get('port', 5432)
        database = self.config['name']
        user = self.config['user']
        password = self.config['password']
        
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    
    def _test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                if self.db_type == 'mysql':
                    result = conn.execute(text("SELECT 1"))
                else:
                    result = conn.execute(text("SELECT 1"))
                
                result.fetchone()
                self.logger.debug("Database connection test successful")
                
        except Exception as e:
            raise DatabaseConnectionError(f"Connection test failed: {str(e)}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager"""
        connection = None
        try:
            connection = self.engine.connect()
            yield connection
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()
    
    @contextmanager
    def get_session(self):
        """Get database session context manager"""
        session = None
        try:
            session = self.session_factory()
            yield session
            session.commit()
        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            if session:
                session.close()
    
    @contextmanager
    def get_transaction(self):
        """Get database transaction context manager"""
        connection = None
        transaction = None
        try:
            connection = self.engine.connect()
            transaction = connection.begin()
            yield connection
            transaction.commit()
        except Exception as e:
            if transaction:
                transaction.rollback()
            self.logger.error(f"Database transaction error: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        try:
            with self.get_connection() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                # Convert result to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute non-query SQL statement (INSERT, UPDATE, DELETE)
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self.get_connection() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                conn.commit()
                return result.rowcount
                
        except Exception as e:
            self.logger.error(f"Non-query execution failed: {str(e)}")
            raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get table information including columns, constraints, and indexes
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary containing table information
        """
        try:
            inspector = inspect(self.engine)
            
            # Get table columns
            columns = inspector.get_columns(table_name)
            
            # Get primary keys
            primary_keys = inspector.get_pk_constraint(table_name)
            
            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            # Get indexes
            indexes = inspector.get_indexes(table_name)
            
            # Get unique constraints
            unique_constraints = inspector.get_unique_constraints(table_name)
            
            # Get check constraints (if supported)
            check_constraints = []
            try:
                check_constraints = inspector.get_check_constraints(table_name)
            except NotImplementedError:
                # Some databases don't support check constraints inspection
                pass
            
            return {
                'table_name': table_name,
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys,
                'indexes': indexes,
                'unique_constraints': unique_constraints,
                'check_constraints': check_constraints
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get table info for {table_name}: {str(e)}")
            raise
    
    def get_all_tables(self) -> List[str]:
        """
        Get list of all tables in the database
        
        Returns:
            List of table names
        """
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
            
        except Exception as e:
            self.logger.error(f"Failed to get table list: {str(e)}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists in the database
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            inspector = inspect(self.engine)
            return table_name in inspector.get_table_names()
            
        except Exception as e:
            self.logger.error(f"Failed to check table existence for {table_name}: {str(e)}")
            return False
    
    def get_row_count(self, table_name: str, where_clause: Optional[str] = None) -> int:
        """
        Get row count for a table
        
        Args:
            table_name: Name of the table
            where_clause: Optional WHERE clause
            
        Returns:
            Number of rows
        """
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            result = self.execute_query(query)
            return result[0]['count'] if result else 0
            
        except Exception as e:
            self.logger.error(f"Failed to get row count for {table_name}: {str(e)}")
            raise
    
    def validate_data_integrity(self, table_name: str) -> Dict[str, Any]:
        """
        Validate data integrity for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary containing integrity validation results
        """
        try:
            results = {
                'table_name': table_name,
                'total_rows': 0,
                'null_violations': [],
                'constraint_violations': [],
                'data_type_violations': [],
                'is_valid': True
            }
            
            # Get table info
            table_info = self.get_table_info(table_name)
            
            # Get total row count
            results['total_rows'] = self.get_row_count(table_name)
            
            # Check for NULL violations in NOT NULL columns
            for column in table_info['columns']:
                if not column.get('nullable', True):
                    null_count = self.get_row_count(
                        table_name, 
                        f"{column['name']} IS NULL"
                    )
                    if null_count > 0:
                        results['null_violations'].append({
                            'column': column['name'],
                            'null_count': null_count
                        })
                        results['is_valid'] = False
            
            # Check foreign key constraints
            for fk in table_info['foreign_keys']:
                # Check for orphaned records
                fk_column = fk['constrained_columns'][0]
                ref_table = fk['referred_table']
                ref_column = fk['referred_columns'][0]
                
                orphaned_query = f"""
                    SELECT COUNT(*) as count 
                    FROM {table_name} t1 
                    LEFT JOIN {ref_table} t2 ON t1.{fk_column} = t2.{ref_column}
                    WHERE t1.{fk_column} IS NOT NULL AND t2.{ref_column} IS NULL
                """
                
                orphaned_result = self.execute_query(orphaned_query)
                orphaned_count = orphaned_result[0]['count'] if orphaned_result else 0
                
                if orphaned_count > 0:
                    results['constraint_violations'].append({
                        'type': 'foreign_key',
                        'column': fk_column,
                        'referenced_table': ref_table,
                        'referenced_column': ref_column,
                        'violation_count': orphaned_count
                    })
                    results['is_valid'] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Data integrity validation failed for {table_name}: {str(e)}")
            raise
    
    def close(self):
        """Close database connection"""
        try:
            if self.engine:
                self.engine.dispose()
                self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database connection: {str(e)}")


class DatabaseConnectionManager:
    """Manages multiple database connections for different environments"""
    
    def __init__(self):
        self.connections: Dict[str, DatabaseConnection] = {}
        self.config_manager = ConfigManager()
        self.logger = logging.getLogger(__name__)
    
    def get_connection(self, environment: Environment) -> DatabaseConnection:
        """
        Get database connection for specified environment
        
        Args:
            environment: Target environment
            
        Returns:
            DatabaseConnection instance
        """
        env_name = environment.value
        
        if env_name not in self.connections:
            # Load configuration for environment
            config = self.config_manager.get_config(environment)
            db_config = config.get('database', {})
            
            # Determine database type from configuration
            db_type = db_config.get('type', 'mysql')
            
            # Create connection
            self.connections[env_name] = DatabaseConnection(db_config, db_type)
            
            self.logger.info(f"Created database connection for environment: {env_name}")
        
        return self.connections[env_name]
    
    def close_all_connections(self):
        """Close all database connections"""
        for env_name, connection in self.connections.items():
            try:
                connection.close()
                self.logger.info(f"Closed database connection for environment: {env_name}")
            except Exception as e:
                self.logger.error(f"Error closing connection for {env_name}: {str(e)}")
        
        self.connections.clear()
    
    def test_all_connections(self) -> Dict[str, bool]:
        """
        Test all database connections
        
        Returns:
            Dictionary mapping environment names to connection status
        """
        results = {}
        
        for env in Environment:
            try:
                connection = self.get_connection(env)
                connection._test_connection()
                results[env.value] = True
                self.logger.info(f"Database connection test passed for {env.value}")
            except Exception as e:
                results[env.value] = False
                self.logger.error(f"Database connection test failed for {env.value}: {str(e)}")
        
        return results