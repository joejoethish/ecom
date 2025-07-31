#!/usr/bin/env python3
"""
Integration test script for database migration utilities.
Tests the migration process with a small sample database.
"""
import os
import sys
import sqlite3
import tempfile
import logging
from pathlib import Path
from datetime import datetime

# Add Django project to path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')

import django
django.setup()

from core.migration import DatabaseMigrationService, MigrationValidator


def create_test_sqlite_db(db_path: str):
    """Create a test SQLite database with sample data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create test tables
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES categories (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category_id INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Insert sample data
    cursor.execute('''
        INSERT INTO users (username, email) VALUES
        ('admin', 'admin@example.com'),
        ('user1', 'user1@example.com'),
        ('user2', 'user2@example.com')
    ''')
    
    cursor.execute('''
        INSERT INTO categories (name, description) VALUES
        ('Electronics', 'Electronic devices and accessories'),
        ('Books', 'Books and publications'),
        ('Clothing', 'Apparel and accessories')
    ''')
    
    cursor.execute('''
        INSERT INTO products (name, description, price, category_id, created_by) VALUES
        ('Laptop', 'High-performance laptop', 999.99, 1, 1),
        ('Python Book', 'Learn Python programming', 29.99, 2, 1),
        ('T-Shirt', 'Cotton t-shirt', 19.99, 3, 2),
        ('Smartphone', 'Latest smartphone model', 699.99, 1, 1),
        ('Novel', 'Bestselling fiction novel', 14.99, 2, 2)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Created test SQLite database: {db_path}")


def test_migration_service():
    """Test the DatabaseMigrationService functionality"""
    print("\n" + "="*60)
    print("TESTING DATABASE MIGRATION SERVICE")
    print("="*60)
    
    # Create temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Create test database
        create_test_sqlite_db(temp_db_path)
        
        # Create migration service
        migration_service = DatabaseMigrationService(sqlite_path=temp_db_path)
        
        print(f"SQLite database: {temp_db_path}")
        print(f"MySQL config: {migration_service.mysql_config}")
        
        # Test database connections
        print("\n1. Testing database connections...")
        if migration_service.connect_databases():
            print("✓ Successfully connected to both databases")
        else:
            print("✗ Failed to connect to databases")
            return False
        
        try:
            # Test getting SQLite tables
            print("\n2. Testing SQLite table discovery...")
            tables = migration_service.get_sqlite_tables()
            print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
            
            # Test schema analysis
            print("\n3. Testing schema analysis...")
            for table_name in tables:
                schema = migration_service.get_table_schema(table_name)
                print(f"✓ {table_name}: {len(schema)} columns")
                
                # Test type conversion
                for col in schema:
                    mysql_type = migration_service.convert_sqlite_to_mysql_type(col['type'])
                    print(f"  - {col['name']}: {col['type']} → {mysql_type}")
            
            # Test MySQL table creation
            print("\n4. Testing MySQL table creation...")
            for table_name in tables:
                schema = migration_service.get_table_schema(table_name)
                if migration_service.create_mysql_table(table_name, schema):
                    print(f"✓ Created MySQL table: {table_name}")
                else:
                    print(f"✗ Failed to create MySQL table: {table_name}")
            
            # Test data migration (small batch for testing)
            print("\n5. Testing data migration...")
            for table_name in tables:
                print(f"Migrating {table_name}...")
                progress = migration_service.migrate_table_data(table_name, batch_size=10)
                
                if progress.status == 'completed':
                    print(f"✓ {table_name}: {progress.migrated_records} records migrated "
                          f"({progress.progress_percentage:.1f}%)")
                else:
                    print(f"✗ {table_name}: Migration failed - {progress.error_message}")
            
            # Test validation
            print("\n6. Testing migration validation...")
            for table_name in tables:
                validation = migration_service.validate_migration(table_name)
                
                if validation.is_valid:
                    print(f"✓ {table_name}: Validation passed "
                          f"(Source: {validation.source_count}, Target: {validation.target_count})")
                else:
                    print(f"✗ {table_name}: Validation failed "
                          f"(Missing: {len(validation.missing_records)}, "
                          f"Extra: {len(validation.extra_records)})")
            
            # Test rollback functionality
            print("\n7. Testing rollback functionality...")
            test_table = tables[0] if tables else None
            if test_table:
                if migration_service.create_rollback_point(test_table):
                    print(f"✓ Created rollback point for {test_table}")
                    
                    if migration_service.rollback_table(test_table):
                        print(f"✓ Successfully rolled back {test_table}")
                    else:
                        print(f"✗ Failed to rollback {test_table}")
                else:
                    print(f"✗ Failed to create rollback point for {test_table}")
            
            # Test migration log
            print("\n8. Testing migration log...")
            log_file = migration_service.save_migration_log()
            if os.path.exists(log_file):
                print(f"✓ Migration log saved: {log_file}")
            else:
                print("✗ Failed to save migration log")
            
            print("\n✓ All migration service tests completed successfully!")
            return True
            
        finally:
            migration_service.disconnect_databases()
    
    finally:
        # Clean up temporary database
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_migration_validator():
    """Test the MigrationValidator functionality"""
    print("\n" + "="*60)
    print("TESTING MIGRATION VALIDATOR")
    print("="*60)
    
    # Create temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Create test database
        create_test_sqlite_db(temp_db_path)
        
        # Create migration service and validator
        migration_service = DatabaseMigrationService(sqlite_path=temp_db_path)
        validator = MigrationValidator(migration_service)
        
        if not migration_service.connect_databases():
            print("✗ Failed to connect to databases")
            return False
        
        try:
            tables = migration_service.get_sqlite_tables()
            
            # Test schema compatibility validation
            print("\n1. Testing schema compatibility validation...")
            for table_name in tables:
                # First create the MySQL table
                schema = migration_service.get_table_schema(table_name)
                migration_service.create_mysql_table(table_name, schema)
                
                # Then validate compatibility
                result = validator.validate_schema_compatibility(table_name)
                
                if result['is_compatible']:
                    print(f"✓ {table_name}: Schema compatible")
                else:
                    print(f"✗ {table_name}: Schema issues found:")
                    for issue in result['issues']:
                        print(f"  - {issue}")
            
            # Test data integrity validation
            print("\n2. Testing data integrity validation...")
            for table_name in tables:
                # Migrate some data first
                migration_service.migrate_table_data(table_name, batch_size=10)
                
                # Then validate data integrity
                result = validator.validate_data_integrity(table_name, sample_size=5)
                
                if result['is_valid']:
                    print(f"✓ {table_name}: Data integrity validated "
                          f"({result['validated_records']} records checked)")
                else:
                    print(f"✗ {table_name}: Data integrity issues found:")
                    print(f"  - Error rate: {result['error_rate']:.2%}")
                    for issue in result['integrity_issues'][:3]:  # Show first 3 issues
                        print(f"  - {issue}")
            
            print("\n✓ All validator tests completed successfully!")
            return True
            
        finally:
            migration_service.disconnect_databases()
    
    finally:
        # Clean up temporary database
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_full_migration_workflow():
    """Test the complete migration workflow"""
    print("\n" + "="*60)
    print("TESTING FULL MIGRATION WORKFLOW")
    print("="*60)
    
    # Create temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Create test database
        create_test_sqlite_db(temp_db_path)
        
        # Create migration service
        migration_service = DatabaseMigrationService(sqlite_path=temp_db_path)
        
        print("Running complete migration workflow...")
        
        # Run full migration
        results = migration_service.migrate_all_tables(batch_size=10, create_rollback=True)
        
        print(f"\nMigration Results:")
        print(f"  Total tables: {results['total_tables']}")
        print(f"  Successful migrations: {results['successful_migrations']}")
        print(f"  Failed migrations: {results['failed_migrations']}")
        print(f"  Successful validations: {results['successful_validations']}")
        print(f"  Failed validations: {results['failed_validations']}")
        print(f"  Duration: {results['total_duration']:.2f} seconds")
        
        # Show table details
        print(f"\nTable Details:")
        for table_name, table_info in results['tables'].items():
            status_symbol = "✓" if table_info['migration_status'] == 'completed' else "✗"
            print(f"  {status_symbol} {table_name}: {table_info['migration_status']}")
            if 'records_migrated' in table_info:
                print(f"    Records: {table_info['records_migrated']}")
            if 'duration_seconds' in table_info:
                print(f"    Duration: {table_info['duration_seconds']:.2f}s")
        
        # Check if log file was created
        if 'log_file' in results and os.path.exists(results['log_file']):
            print(f"\n✓ Migration log saved: {results['log_file']}")
        
        success_rate = (results['successful_migrations'] / results['total_tables']) * 100
        print(f"\n✓ Full migration workflow completed with {success_rate:.1f}% success rate!")
        
        return success_rate == 100.0
        
    finally:
        # Clean up temporary database
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def main():
    """Main test runner"""
    print("DATABASE MIGRATION UTILITIES - INTEGRATION TESTS")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress some verbose logging
    logging.getLogger('mysql.connector').setLevel(logging.WARNING)
    
    test_results = []
    
    try:
        # Run tests
        test_results.append(("Migration Service", test_migration_service()))
        test_results.append(("Migration Validator", test_migration_validator()))
        test_results.append(("Full Migration Workflow", test_full_migration_workflow()))
        
    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        return 1
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Migration utilities are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())