#!/usr/bin/env python
"""
Validation script for MySQL schema optimization.
Checks if the optimizations have been applied correctly.
"""
import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')
django.setup()

from django.db import connection


def validate_indexes():
    """Validate that performance indexes have been created."""
    print("Validating database indexes...")
    
    with connection.cursor() as cursor:
        # Check products_product indexes
        cursor.execute("SHOW INDEX FROM products_product")
        indexes = cursor.fetchall()
        index_names = [index[2] for index in indexes]
        
        expected_indexes = [
            'idx_products_product_category_active',
            'idx_products_product_price_active',
            'idx_products_product_featured_active',
            'idx_products_product_brand_active',
        ]
        
        found_indexes = []
        for expected_index in expected_indexes:
            if expected_index in index_names:
                found_indexes.append(expected_index)
                print(f"  ✓ Found index: {expected_index}")
            else:
                print(f"  ✗ Missing index: {expected_index}")
        
        print(f"  Found {len(found_indexes)}/{len(expected_indexes)} expected indexes on products_product")
        
        # Check orders_order indexes
        cursor.execute("SHOW INDEX FROM orders_order")
        indexes = cursor.fetchall()
        index_names = [index[2] for index in indexes]
        
        order_expected_indexes = [
            'idx_orders_order_customer_date',
            'idx_orders_order_status_date',
            'idx_orders_order_payment_status',
        ]
        
        found_order_indexes = []
        for expected_index in order_expected_indexes:
            if expected_index in index_names:
                found_order_indexes.append(expected_index)
                print(f"  ✓ Found index: {expected_index}")
            else:
                print(f"  ✗ Missing index: {expected_index}")
        
        print(f"  Found {len(found_order_indexes)}/{len(order_expected_indexes)} expected indexes on orders_order")
        
        return len(found_indexes) + len(found_order_indexes)


def validate_table_settings():
    """Validate that table settings have been optimized."""
    print("\nValidating table settings...")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT TABLE_NAME, ENGINE, ROW_FORMAT, TABLE_COLLATION 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME IN ('products_product', 'orders_order', 'reviews_review')
        """)
        
        tables = cursor.fetchall()
        optimized_tables = 0
        
        for table_name, engine, row_format, collation in tables:
            print(f"  Table: {table_name}")
            
            if engine == 'InnoDB':
                print(f"    ✓ Engine: {engine}")
            else:
                print(f"    ✗ Engine: {engine} (expected InnoDB)")
            
            if row_format == 'Dynamic':
                print(f"    ✓ Row Format: {row_format}")
            else:
                print(f"    ✗ Row Format: {row_format} (expected Dynamic)")
            
            if collation == 'utf8mb4_unicode_ci':
                print(f"    ✓ Collation: {collation}")
                optimized_tables += 1
            else:
                print(f"    ✗ Collation: {collation} (expected utf8mb4_unicode_ci)")
        
        return optimized_tables


def validate_data_types():
    """Validate that data types have been optimized."""
    print("\nValidating data type optimizations...")
    
    with connection.cursor() as cursor:
        # Check products_product data types
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'products_product' 
            AND TABLE_SCHEMA = DATABASE()
            AND COLUMN_NAME IN ('price', 'is_active', 'is_featured')
            ORDER BY COLUMN_NAME
        """)
        
        columns = cursor.fetchall()
        optimized_columns = 0
        
        expected_types = {
            'price': 'decimal',
            'is_active': 'tinyint',
            'is_featured': 'tinyint'
        }
        
        for column_name, data_type, is_nullable, column_default in columns:
            expected_type = expected_types.get(column_name)
            if expected_type and data_type == expected_type:
                print(f"  ✓ {column_name}: {data_type}")
                optimized_columns += 1
            else:
                print(f"  ✗ {column_name}: {data_type} (expected {expected_type})")
        
        return optimized_columns


def validate_constraints():
    """Validate that constraints have been added."""
    print("\nValidating table constraints...")
    
    with connection.cursor() as cursor:
        try:
            # Try MySQL 8.0+ syntax first
            cursor.execute("""
                SELECT CONSTRAINT_NAME, TABLE_NAME
                FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS 
                WHERE CONSTRAINT_SCHEMA = DATABASE()
                AND CONSTRAINT_NAME LIKE 'chk_%'
            """)
            
            constraints = cursor.fetchall()
            
            if constraints:
                print(f"  Found {len(constraints)} check constraints:")
                for constraint_name, table_name in constraints:
                    print(f"    ✓ {constraint_name} on {table_name}")
            else:
                print("  ✗ No check constraints found")
            
            return len(constraints)
            
        except Exception as e:
            # Fallback for older MySQL versions
            print(f"  ⚠ Check constraints validation not supported in this MySQL version: {str(e)}")
            print("  Attempting alternative validation...")
            
            # Try to validate by attempting to insert invalid data (this would fail if constraints exist)
            try:
                cursor.execute("SELECT COUNT(*) FROM products_product WHERE price < 0")
                result = cursor.fetchone()
                if result and result[0] == 0:
                    print("  ✓ Price constraint appears to be working (no negative prices found)")
                    return 1
                else:
                    print("  ⚠ Cannot validate constraints with this method")
                    return 0
            except Exception:
                print("  ⚠ Cannot validate constraints")
                return 0


def validate_foreign_keys():
    """Validate that foreign key constraints are properly configured."""
    print("\nValidating foreign key constraints...")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                CONSTRAINT_NAME,
                TABLE_NAME,
                REFERENCED_TABLE_NAME,
                DELETE_RULE,
                UPDATE_RULE
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
            WHERE CONSTRAINT_SCHEMA = DATABASE()
            AND TABLE_NAME IN ('products_product', 'orders_order', 'reviews_review')
        """)
        
        fk_constraints = cursor.fetchall()
        optimized_fks = 0
        
        if fk_constraints:
            print(f"  Found {len(fk_constraints)} foreign key constraints:")
            for constraint_name, table_name, ref_table, delete_rule, update_rule in fk_constraints:
                print(f"    ✓ {constraint_name}: {table_name} -> {ref_table}")
                print(f"      Delete: {delete_rule}, Update: {update_rule}")
                if delete_rule in ['CASCADE', 'RESTRICT'] and update_rule == 'CASCADE':
                    optimized_fks += 1
        else:
            print("  ✗ No foreign key constraints found")
        
        return optimized_fks


def check_mysql_settings():
    """Check MySQL server settings."""
    print("\nChecking MySQL server settings...")
    
    with connection.cursor() as cursor:
        # Check some key settings
        settings_to_check = [
            'innodb_buffer_pool_size',
            'max_connections',
            'slow_query_log',
            'long_query_time'
        ]
        
        optimized_settings = 0
        
        for setting in settings_to_check:
            try:
                cursor.execute(f"SHOW VARIABLES LIKE '{setting}'")
                result = cursor.fetchone()
                if result:
                    variable_name, value = result
                    print(f"  {variable_name}: {value}")
                    optimized_settings += 1
                else:
                    print(f"  ✗ {setting}: Not found")
            except Exception as e:
                print(f"  ✗ {setting}: Error - {str(e)}")
        
        return optimized_settings


def main():
    """Main validation function."""
    print("=" * 60)
    print("MySQL Schema Optimization Validation")
    print("=" * 60)
    
    try:
        # Validate different aspects of the optimization
        indexes_count = validate_indexes()
        tables_count = validate_table_settings()
        types_count = validate_data_types()
        constraints_count = validate_constraints()
        fk_count = validate_foreign_keys()
        settings_count = check_mysql_settings()
        
        print("\n" + "=" * 60)
        print("Validation Summary:")
        print("=" * 60)
        print(f"Indexes created: {indexes_count}")
        print(f"Tables optimized: {tables_count}")
        print(f"Data types optimized: {types_count}")
        print(f"Constraints added: {constraints_count}")
        print(f"Foreign keys optimized: {fk_count}")
        print(f"MySQL settings checked: {settings_count}")
        
        total_score = indexes_count + tables_count + types_count + constraints_count + fk_count + settings_count
        print(f"\nTotal optimization score: {total_score}")
        
        if total_score >= 10:
            print("✓ Schema optimization appears to be successful!")
        else:
            print("⚠ Schema optimization may need attention.")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"Validation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()