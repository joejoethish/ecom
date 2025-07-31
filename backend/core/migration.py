"""
Database migration utilities for SQLite to MySQL migration.
Provides comprehensive migration, validation, and rollback capabilities.
"""
import os
import sqlite3
import logging
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import mysql.connector
from mysql.connector import Error as MySQLError
from django.conf import settings
from django.db import connections, transaction
from django.core.management import call_command
from django.apps import apps

logger = logging.getLogger(__name__)


@dataclass
class MigrationProgress:
    """Track migration progress and statistics"""
    table_name: str
    total_records: int
    migrated_records: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = 'pending'  # pending, in_progress, completed, failed
    error_message: Optional[str] = None
    data_hash: Optional[str] = None
    
    @property
    def progress_percentage(self) -> float:
        if self.total_records == 0:
            return 100.0
        return (self.migrated_records / self.total_records) * 100
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class ValidationResult:
    """Results of data integrity validation"""
    table_name: str
    source_count: int
    target_count: int
    is_valid: bool
    missing_records: List[Any]
    extra_records: List[Any]
    data_mismatches: List[Dict[str, Any]]
    validation_time: datetime


class DatabaseMigrationService:
    """
    Comprehensive database migration service for SQLite to MySQL migration.
    Handles schema conversion, data transfer, validation, and rollback.
    """
    
    def __init__(self, sqlite_path: str = None, mysql_config: Dict[str, Any] = None):
        """
        Initialize migration service with database configurations.
        
        Args:
            sqlite_path: Path to SQLite database file
            mysql_config: MySQL connection configuration
        """
        self.sqlite_path = sqlite_path or str(settings.BASE_DIR / 'db.sqlite3')
        self.mysql_config = mysql_config or self._get_mysql_config()
        self.migration_log_path = settings.BASE_DIR / 'migration_logs'
        self.migration_log_path.mkdir(exist_ok=True)
        
        # Migration state tracking
        self.migration_progress: Dict[str, MigrationProgress] = {}
        self.validation_results: Dict[str, ValidationResult] = {}
        self.rollback_data: Dict[str, Any] = {}
        
        # Database connections
        self.sqlite_conn: Optional[sqlite3.Connection] = None
        self.mysql_conn: Optional[mysql.connector.MySQLConnection] = None
        
    def _get_mysql_config(self) -> Dict[str, Any]:
        """Extract MySQL configuration from Django settings"""
        db_config = settings.DATABASES['default']
        return {
            'host': db_config['HOST'],
            'port': int(db_config['PORT']),
            'user': db_config['USER'],
            'password': db_config['PASSWORD'],
            'database': db_config['NAME'],
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': False,
            'raise_on_warnings': True
        }
    
    def connect_databases(self) -> bool:
        """
        Establish connections to both SQLite and MySQL databases.
        
        Returns:
            bool: True if both connections successful
        """
        try:
            # Connect to SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {self.sqlite_path}")
            
            # Connect to MySQL
            self.mysql_conn = mysql.connector.connect(**self.mysql_config)
            logger.info(f"Connected to MySQL database: {self.mysql_config['database']}")
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            return False
        except MySQLError as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to databases: {e}")
            return False
    
    def disconnect_databases(self):
        """Close database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            self.sqlite_conn = None
            logger.info("Disconnected from SQLite")
            
        if self.mysql_conn:
            self.mysql_conn.close()
            self.mysql_conn = None
            logger.info("Disconnected from MySQL")
    
    def get_sqlite_tables(self) -> List[str]:
        """
        Get list of tables from SQLite database.
        
        Returns:
            List[str]: Table names
        """
        if not self.sqlite_conn:
            raise RuntimeError("SQLite connection not established")
            
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(tables)} tables in SQLite database")
        return tables
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get table schema information from SQLite.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List[Dict]: Column information
        """
        if not self.sqlite_conn:
            raise RuntimeError("SQLite connection not established")
            
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'cid': row[0],
                'name': row[1],
                'type': row[2],
                'notnull': bool(row[3]),
                'default_value': row[4],
                'pk': bool(row[5])
            })
        
        return columns
    
    def convert_sqlite_to_mysql_type(self, sqlite_type: str) -> str:
        """
        Convert SQLite data type to MySQL equivalent.
        
        Args:
            sqlite_type: SQLite data type
            
        Returns:
            str: MySQL data type
        """
        type_mapping = {
            'INTEGER': 'INT',
            'TEXT': 'TEXT',
            'REAL': 'DOUBLE',
            'BLOB': 'LONGBLOB',
            'NUMERIC': 'DECIMAL(10,2)',
            'VARCHAR': 'VARCHAR(255)',
            'CHAR': 'CHAR(255)',
            'BOOLEAN': 'TINYINT(1)',
            'DATETIME': 'DATETIME',
            'TIMESTAMP': 'TIMESTAMP',  # Put TIMESTAMP before TIME to avoid prefix matching issues
            'DATE': 'DATE',
            'TIME': 'TIME'
        }
        
        # Handle parameterized types
        sqlite_type_upper = sqlite_type.upper()
        for sqlite_key, mysql_type in type_mapping.items():
            if sqlite_type_upper.startswith(sqlite_key):
                if '(' in sqlite_type_upper:
                    # Preserve parameters like VARCHAR(100)
                    params = sqlite_type_upper[sqlite_type_upper.find('('):]
                    if sqlite_key in ['VARCHAR', 'CHAR']:
                        return f"{type_mapping[sqlite_key].split('(')[0]}{params}"
                return mysql_type
        
        # Default fallback
        logger.warning(f"Unknown SQLite type '{sqlite_type}', using TEXT")
        return 'TEXT'
    
    def create_mysql_table(self, table_name: str, columns: List[Dict[str, Any]]) -> bool:
        """
        Create MySQL table based on SQLite schema.
        
        Args:
            table_name: Name of the table to create
            columns: Column definitions from SQLite
            
        Returns:
            bool: True if table created successfully
        """
        if not self.mysql_conn:
            raise RuntimeError("MySQL connection not established")
        
        try:
            cursor = self.mysql_conn.cursor()
            
            # Build CREATE TABLE statement
            column_definitions = []
            primary_keys = []
            
            for col in columns:
                mysql_type = self.convert_sqlite_to_mysql_type(col['type'])
                definition = f"`{col['name']}` {mysql_type}"
                
                if col['notnull']:
                    definition += " NOT NULL"
                
                if col['default_value'] is not None:
                    if col['default_value'].upper() in ['CURRENT_TIMESTAMP', 'NOW()']:
                        definition += " DEFAULT CURRENT_TIMESTAMP"
                    else:
                        definition += f" DEFAULT '{col['default_value']}'"
                
                if col['pk']:
                    primary_keys.append(col['name'])
                
                column_definitions.append(definition)
            
            # Add primary key constraint
            if primary_keys:
                pk_constraint = f"PRIMARY KEY (`{'`, `'.join(primary_keys)}`)"
                column_definitions.append(pk_constraint)
            
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS `{table_name}` (
                    {', '.join(column_definitions)}
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_sql)
            self.mysql_conn.commit()
            logger.info(f"Created MySQL table: {table_name}")
            return True
            
        except MySQLError as e:
            logger.error(f"Failed to create MySQL table {table_name}: {e}")
            self.mysql_conn.rollback()
            return False
    
    def migrate_table_data(self, table_name: str, batch_size: int = 1000) -> MigrationProgress:
        """
        Migrate data from SQLite table to MySQL with batch processing and progress tracking.
        
        Args:
            table_name: Name of the table to migrate
            batch_size: Number of records to process in each batch
            
        Returns:
            MigrationProgress: Migration progress information
        """
        if not self.sqlite_conn or not self.mysql_conn:
            raise RuntimeError("Database connections not established")
        
        start_time = datetime.now()
        
        try:
            # Get total record count
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            total_records = sqlite_cursor.fetchone()[0]
            
            # Initialize progress tracking
            progress = MigrationProgress(
                table_name=table_name,
                total_records=total_records,
                migrated_records=0,
                start_time=start_time,
                status='in_progress'
            )
            self.migration_progress[table_name] = progress
            
            if total_records == 0:
                progress.status = 'completed'
                progress.end_time = datetime.now()
                logger.info(f"Table {table_name} is empty, migration completed")
                return progress
            
            # Get column names
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in sqlite_cursor.fetchall()]
            
            # Prepare MySQL insert statement
            mysql_cursor = self.mysql_conn.cursor()
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO `{table_name}` (`{'`, `'.join(columns)}`) VALUES ({placeholders})"
            
            # Migrate data in batches
            offset = 0
            data_hash = hashlib.md5()
            
            while offset < total_records:
                # Fetch batch from SQLite
                sqlite_cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {batch_size} OFFSET {offset}")
                batch_data = sqlite_cursor.fetchall()
                
                if not batch_data:
                    break
                
                # Convert SQLite rows to tuples for MySQL
                mysql_data = []
                for row in batch_data:
                    row_tuple = tuple(row)
                    mysql_data.append(row_tuple)
                    # Update hash for data integrity verification
                    data_hash.update(str(row_tuple).encode('utf-8'))
                
                # Insert batch into MySQL
                mysql_cursor.executemany(insert_sql, mysql_data)
                self.mysql_conn.commit()
                
                # Update progress
                progress.migrated_records += len(batch_data)
                offset += batch_size
                
                logger.info(f"Migrated {progress.migrated_records}/{total_records} records from {table_name} "
                           f"({progress.progress_percentage:.1f}%)")
            
            # Finalize migration
            progress.status = 'completed'
            progress.end_time = datetime.now()
            progress.data_hash = data_hash.hexdigest()
            
            logger.info(f"Successfully migrated {progress.migrated_records} records from {table_name} "
                       f"in {progress.duration_seconds:.2f} seconds")
            
            return progress
            
        except Exception as e:
            progress.status = 'failed'
            progress.error_message = str(e)
            progress.end_time = datetime.now()
            logger.error(f"Failed to migrate table {table_name}: {e}")
            self.mysql_conn.rollback()
            return progress
    
    def validate_migration(self, table_name: str) -> ValidationResult:
        """
        Validate data integrity after migration.
        
        Args:
            table_name: Name of the table to validate
            
        Returns:
            ValidationResult: Validation results
        """
        if not self.sqlite_conn or not self.mysql_conn:
            raise RuntimeError("Database connections not established")
        
        validation_time = datetime.now()
        
        try:
            # Get record counts
            sqlite_cursor = self.sqlite_conn.cursor()
            mysql_cursor = self.mysql_conn.cursor()
            
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            source_count = sqlite_cursor.fetchone()[0]
            
            mysql_cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            target_count = mysql_cursor.fetchone()[0]
            
            # Basic count validation
            is_valid = source_count == target_count
            missing_records = []
            extra_records = []
            data_mismatches = []
            
            if not is_valid:
                logger.warning(f"Record count mismatch for {table_name}: "
                             f"SQLite={source_count}, MySQL={target_count}")
            
            # Sample data validation for smaller tables
            if source_count <= 10000:  # Only for smaller tables to avoid performance issues
                # Get primary key column
                sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
                pk_columns = [row[1] for row in sqlite_cursor.fetchall() if row[5]]  # pk flag
                
                if pk_columns:
                    pk_column = pk_columns[0]  # Use first primary key column
                    
                    # Get all primary keys from both databases
                    sqlite_cursor.execute(f"SELECT `{pk_column}` FROM `{table_name}` ORDER BY `{pk_column}`")
                    sqlite_pks = set(row[0] for row in sqlite_cursor.fetchall())
                    
                    mysql_cursor.execute(f"SELECT `{pk_column}` FROM `{table_name}` ORDER BY `{pk_column}`")
                    mysql_pks = set(row[0] for row in mysql_cursor.fetchall())
                    
                    # Find missing and extra records
                    missing_records = list(sqlite_pks - mysql_pks)
                    extra_records = list(mysql_pks - sqlite_pks)
                    
                    if missing_records or extra_records:
                        is_valid = False
            
            result = ValidationResult(
                table_name=table_name,
                source_count=source_count,
                target_count=target_count,
                is_valid=is_valid,
                missing_records=missing_records,
                extra_records=extra_records,
                data_mismatches=data_mismatches,
                validation_time=validation_time
            )
            
            self.validation_results[table_name] = result
            
            if is_valid:
                logger.info(f"Validation passed for table {table_name}")
            else:
                logger.error(f"Validation failed for table {table_name}: "
                           f"missing={len(missing_records)}, extra={len(extra_records)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed for table {table_name}: {e}")
            return ValidationResult(
                table_name=table_name,
                source_count=0,
                target_count=0,
                is_valid=False,
                missing_records=[],
                extra_records=[],
                data_mismatches=[],
                validation_time=validation_time
            )
    
    def create_rollback_point(self, table_name: str) -> bool:
        """
        Create a rollback point by backing up current MySQL table data.
        
        Args:
            table_name: Name of the table to backup
            
        Returns:
            bool: True if rollback point created successfully
        """
        if not self.mysql_conn:
            raise RuntimeError("MySQL connection not established")
        
        try:
            backup_table = f"{table_name}_rollback_{int(datetime.now().timestamp())}"
            cursor = self.mysql_conn.cursor()
            
            # Create backup table
            cursor.execute(f"CREATE TABLE `{backup_table}` AS SELECT * FROM `{table_name}`")
            self.mysql_conn.commit()
            
            # Store rollback information
            self.rollback_data[table_name] = {
                'backup_table': backup_table,
                'created_at': datetime.now().isoformat(),
                'original_table': table_name
            }
            
            logger.info(f"Created rollback point for {table_name} as {backup_table}")
            return True
            
        except MySQLError as e:
            logger.error(f"Failed to create rollback point for {table_name}: {e}")
            return False
    
    def rollback_table(self, table_name: str) -> bool:
        """
        Rollback table to previous state using backup.
        
        Args:
            table_name: Name of the table to rollback
            
        Returns:
            bool: True if rollback successful
        """
        if not self.mysql_conn:
            raise RuntimeError("MySQL connection not established")
        
        if table_name not in self.rollback_data:
            logger.error(f"No rollback point found for table {table_name}")
            return False
        
        try:
            backup_table = self.rollback_data[table_name]['backup_table']
            cursor = self.mysql_conn.cursor()
            
            # Start transaction
            cursor.execute("START TRANSACTION")
            
            # Clear current table
            cursor.execute(f"DELETE FROM `{table_name}`")
            
            # Restore from backup
            cursor.execute(f"INSERT INTO `{table_name}` SELECT * FROM `{backup_table}`")
            
            # Commit transaction
            self.mysql_conn.commit()
            
            logger.info(f"Successfully rolled back table {table_name}")
            return True
            
        except MySQLError as e:
            logger.error(f"Failed to rollback table {table_name}: {e}")
            self.mysql_conn.rollback()
            return False
    
    def cleanup_rollback_points(self, table_name: str = None) -> bool:
        """
        Clean up rollback backup tables.
        
        Args:
            table_name: Specific table to clean up, or None for all
            
        Returns:
            bool: True if cleanup successful
        """
        if not self.mysql_conn:
            raise RuntimeError("MySQL connection not established")
        
        try:
            cursor = self.mysql_conn.cursor()
            
            tables_to_clean = [table_name] if table_name else list(self.rollback_data.keys())
            
            for table in tables_to_clean:
                if table in self.rollback_data:
                    backup_table = self.rollback_data[table]['backup_table']
                    cursor.execute(f"DROP TABLE IF EXISTS `{backup_table}`")
                    del self.rollback_data[table]
                    logger.info(f"Cleaned up rollback point for {table}")
            
            self.mysql_conn.commit()
            return True
            
        except MySQLError as e:
            logger.error(f"Failed to cleanup rollback points: {e}")
            return False
    
    def save_migration_log(self) -> str:
        """
        Save migration progress and results to log file.
        
        Returns:
            str: Path to the log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.migration_log_path / f"migration_log_{timestamp}.json"
        
        log_data = {
            'migration_timestamp': timestamp,
            'sqlite_path': self.sqlite_path,
            'mysql_config': {k: v for k, v in self.mysql_config.items() if k != 'password'},
            'migration_progress': {k: asdict(v) for k, v in self.migration_progress.items()},
            'validation_results': {k: asdict(v) for k, v in self.validation_results.items()},
            'rollback_data': self.rollback_data
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        logger.info(f"Migration log saved to {log_file}")
        return str(log_file)
    
    def migrate_all_tables(self, batch_size: int = 1000, create_rollback: bool = True) -> Dict[str, Any]:
        """
        Migrate all tables from SQLite to MySQL.
        
        Args:
            batch_size: Batch size for data migration
            create_rollback: Whether to create rollback points
            
        Returns:
            Dict: Migration summary
        """
        if not self.connect_databases():
            raise RuntimeError("Failed to connect to databases")
        
        try:
            tables = self.get_sqlite_tables()
            migration_summary = {
                'total_tables': len(tables),
                'successful_migrations': 0,
                'failed_migrations': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'start_time': datetime.now(),
                'tables': {}
            }
            
            for table_name in tables:
                logger.info(f"Starting migration for table: {table_name}")
                
                try:
                    # Create rollback point if requested
                    if create_rollback:
                        self.create_rollback_point(table_name)
                    
                    # Get table schema and create MySQL table
                    columns = self.get_table_schema(table_name)
                    if not self.create_mysql_table(table_name, columns):
                        raise Exception(f"Failed to create MySQL table {table_name}")
                    
                    # Migrate data
                    progress = self.migrate_table_data(table_name, batch_size)
                    
                    # Validate migration
                    validation = self.validate_migration(table_name)
                    
                    # Update summary
                    if progress.status == 'completed':
                        migration_summary['successful_migrations'] += 1
                    else:
                        migration_summary['failed_migrations'] += 1
                    
                    if validation.is_valid:
                        migration_summary['successful_validations'] += 1
                    else:
                        migration_summary['failed_validations'] += 1
                    
                    migration_summary['tables'][table_name] = {
                        'migration_status': progress.status,
                        'validation_status': 'passed' if validation.is_valid else 'failed',
                        'records_migrated': progress.migrated_records,
                        'duration_seconds': progress.duration_seconds
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to migrate table {table_name}: {e}")
                    migration_summary['failed_migrations'] += 1
                    migration_summary['tables'][table_name] = {
                        'migration_status': 'failed',
                        'validation_status': 'not_run',
                        'error': str(e)
                    }
            
            migration_summary['end_time'] = datetime.now()
            migration_summary['total_duration'] = (
                migration_summary['end_time'] - migration_summary['start_time']
            ).total_seconds()
            
            # Save migration log
            log_file = self.save_migration_log()
            migration_summary['log_file'] = log_file
            
            logger.info(f"Migration completed: {migration_summary['successful_migrations']}/{migration_summary['total_tables']} tables successful")
            
            return migration_summary
            
        finally:
            self.disconnect_databases()


class MigrationValidator:
    """
    Advanced validation utilities for database migration.
    """
    
    def __init__(self, migration_service: DatabaseMigrationService):
        self.migration_service = migration_service
    
    def validate_schema_compatibility(self, table_name: str) -> Dict[str, Any]:
        """
        Validate schema compatibility between SQLite and MySQL.
        
        Args:
            table_name: Name of the table to validate
            
        Returns:
            Dict: Schema compatibility results
        """
        if not self.migration_service.sqlite_conn or not self.migration_service.mysql_conn:
            raise RuntimeError("Database connections not established")
        
        try:
            # Get SQLite schema
            sqlite_columns = self.migration_service.get_table_schema(table_name)
            
            # Get MySQL schema
            mysql_cursor = self.migration_service.mysql_conn.cursor()
            mysql_cursor.execute(f"DESCRIBE `{table_name}`")
            mysql_schema = mysql_cursor.fetchall()
            
            mysql_columns = {}
            for row in mysql_schema:
                mysql_columns[row[0]] = {
                    'type': row[1],
                    'null': row[2] == 'YES',
                    'key': row[3],
                    'default': row[4],
                    'extra': row[5]
                }
            
            # Compare schemas
            compatibility_issues = []
            
            for sqlite_col in sqlite_columns:
                col_name = sqlite_col['name']
                if col_name not in mysql_columns:
                    compatibility_issues.append(f"Column '{col_name}' missing in MySQL table")
                    continue
                
                mysql_col = mysql_columns[col_name]
                
                # Check data type compatibility
                expected_mysql_type = self.migration_service.convert_sqlite_to_mysql_type(sqlite_col['type'])
                if not mysql_col['type'].upper().startswith(expected_mysql_type.upper()):
                    compatibility_issues.append(
                        f"Column '{col_name}' type mismatch: "
                        f"expected {expected_mysql_type}, got {mysql_col['type']}"
                    )
                
                # Check null constraints
                if sqlite_col['notnull'] and mysql_col['null']:
                    compatibility_issues.append(f"Column '{col_name}' null constraint mismatch")
            
            return {
                'table_name': table_name,
                'is_compatible': len(compatibility_issues) == 0,
                'issues': compatibility_issues,
                'sqlite_columns': len(sqlite_columns),
                'mysql_columns': len(mysql_columns)
            }
            
        except Exception as e:
            logger.error(f"Schema validation failed for {table_name}: {e}")
            return {
                'table_name': table_name,
                'is_compatible': False,
                'issues': [f"Validation error: {str(e)}"],
                'sqlite_columns': 0,
                'mysql_columns': 0
            }
    
    def validate_data_integrity(self, table_name: str, sample_size: int = 100) -> Dict[str, Any]:
        """
        Perform detailed data integrity validation.
        
        Args:
            table_name: Name of the table to validate
            sample_size: Number of records to sample for detailed validation
            
        Returns:
            Dict: Data integrity results
        """
        if not self.migration_service.sqlite_conn or not self.migration_service.mysql_conn:
            raise RuntimeError("Database connections not established")
        
        try:
            sqlite_cursor = self.migration_service.sqlite_conn.cursor()
            mysql_cursor = self.migration_service.mysql_conn.cursor()
            
            # Get sample data from both databases
            sqlite_cursor.execute(f"SELECT * FROM `{table_name}` ORDER BY RANDOM() LIMIT {sample_size}")
            sqlite_sample = sqlite_cursor.fetchall()
            
            # Get column names
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in sqlite_cursor.fetchall()]
            
            integrity_issues = []
            validated_records = 0
            
            for sqlite_row in sqlite_sample:
                # Find corresponding MySQL record (assuming first column is primary key)
                pk_value = sqlite_row[0]
                mysql_cursor.execute(f"SELECT * FROM `{table_name}` WHERE `{columns[0]}` = %s", (pk_value,))
                mysql_row = mysql_cursor.fetchone()
                
                if not mysql_row:
                    integrity_issues.append(f"Record with PK {pk_value} missing in MySQL")
                    continue
                
                # Compare field values
                for i, (sqlite_val, mysql_val) in enumerate(zip(sqlite_row, mysql_row)):
                    if sqlite_val != mysql_val:
                        # Handle type conversions and null values
                        if sqlite_val is None and mysql_val is None:
                            continue
                        if str(sqlite_val) != str(mysql_val):
                            integrity_issues.append(
                                f"Data mismatch in record PK {pk_value}, column '{columns[i]}': "
                                f"SQLite='{sqlite_val}', MySQL='{mysql_val}'"
                            )
                
                validated_records += 1
            
            return {
                'table_name': table_name,
                'sample_size': sample_size,
                'validated_records': validated_records,
                'integrity_issues': integrity_issues,
                'is_valid': len(integrity_issues) == 0,
                'error_rate': len(integrity_issues) / max(validated_records, 1)
            }
            
        except Exception as e:
            logger.error(f"Data integrity validation failed for {table_name}: {e}")
            return {
                'table_name': table_name,
                'sample_size': sample_size,
                'validated_records': 0,
                'integrity_issues': [f"Validation error: {str(e)}"],
                'is_valid': False,
                'error_rate': 1.0
            }


# Utility functions for migration management
def create_migration_service(sqlite_path: str = None, mysql_config: Dict[str, Any] = None) -> DatabaseMigrationService:
    """
    Factory function to create a configured DatabaseMigrationService.
    
    Args:
        sqlite_path: Path to SQLite database
        mysql_config: MySQL configuration
        
    Returns:
        DatabaseMigrationService: Configured migration service
    """
    return DatabaseMigrationService(sqlite_path, mysql_config)


def run_full_migration(batch_size: int = 1000, create_rollback: bool = True) -> Dict[str, Any]:
    """
    Run a complete migration from SQLite to MySQL.
    
    Args:
        batch_size: Batch size for data migration
        create_rollback: Whether to create rollback points
        
    Returns:
        Dict: Migration results
    """
    migration_service = create_migration_service()
    return migration_service.migrate_all_tables(batch_size, create_rollback)


def validate_migration_results(table_names: List[str] = None) -> Dict[str, Any]:
    """
    Validate migration results for specified tables.
    
    Args:
        table_names: List of table names to validate, or None for all
        
    Returns:
        Dict: Validation results
    """
    migration_service = create_migration_service()
    
    if not migration_service.connect_databases():
        raise RuntimeError("Failed to connect to databases")
    
    try:
        if table_names is None:
            table_names = migration_service.get_sqlite_tables()
        
        validation_results = {}
        for table_name in table_names:
            validation_results[table_name] = migration_service.validate_migration(table_name)
        
        return validation_results
        
    finally:
        migration_service.disconnect_databases()