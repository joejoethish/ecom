#!/usr/bin/env python
"""
MySQL Schema Optimization Script
Optimizes the database schema for MySQL with proper indexes, constraints, and partitioning.
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

import logging
from django.db import connection, transaction
from django.core.management import call_command
from core.schema_optimizer import MySQLSchemaOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mysql_schema_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run schema optimization."""
    print("=" * 60)
    print("MySQL Schema Optimization")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = MySQLSchemaOptimizer()
    
    # Tables to optimize (in order of dependencies)
    tables_to_optimize = [
        'auth_user',
        'products_category',
        'products_product',
        'products_productimage',
        'products_productrating',
        'customers_customerprofile',
        'customers_address',
        'customers_wishlist',
        'customers_wishlistitem',
        'customers_customeractivity',
        'orders_order',
        'orders_orderitem',
        'orders_ordertracking',
        'orders_returnrequest',
        'orders_replacement',
        'orders_invoice',
        'reviews_review',
        'reviews_reviewhelpfulness',
        'reviews_reviewimage',
        'reviews_reviewreport',
        'inventory_supplier',
        'inventory_warehouse',
        'inventory_inventory',
        'inventory_inventorytransaction',
        'inventory_purchaseorder',
        'inventory_purchaseorderitem',
        'notifications_notificationtemplate',
        'notifications_notificationpreference',
        'notifications_notification',
        'notifications_notificationlog',
        'notifications_notificationbatch',
        'notifications_notificationanalytics',
        'shipping_shippingpartner',
        'shipping_serviceablearea',
        'shipping_deliveryslot',
        'shipping_shipment',
        'shipping_shipmenttracking',
        'shipping_shippingrate',
    ]
    
    try:
        with transaction.atomic():
            print("\n1. Analyzing current schema...")
            analyze_current_schema(optimizer, tables_to_optimize)
            
            print("\n2. Optimizing table structures...")
            optimize_table_structures(optimizer, tables_to_optimize)
            
            print("\n3. Creating performance indexes...")
            create_performance_indexes(optimizer, tables_to_optimize)
            
            print("\n4. Setting up table partitioning...")
            setup_table_partitioning(optimizer)
            
            print("\n5. Optimizing MySQL settings...")
            optimize_mysql_settings()
            
            print("\n6. Running final analysis...")
            final_analysis(optimizer, tables_to_optimize)
            
            print("\n" + "=" * 60)
            print("Schema optimization completed successfully!")
            print("=" * 60)
            
    except Exception as e:
        logger.error(f"Schema optimization failed: {str(e)}")
        print(f"ERROR: {str(e)}")
        sys.exit(1)


def analyze_current_schema(optimizer, tables):
    """Analyze current schema and provide recommendations."""
    print("Analyzing current database schema...")
    
    total_size = 0
    total_rows = 0
    
    for table in tables:
        try:
            analysis = optimizer.analyze_table_performance(table)
            total_size += analysis.get('table_size_mb', 0)
            total_rows += analysis.get('row_count', 0)
            
            if analysis.get('recommendations'):
                print(f"  {table}: {', '.join(analysis['recommendations'])}")
                
        except Exception as e:
            logger.warning(f"Could not analyze table {table}: {str(e)}")
            continue
    
    print(f"Total database size: {total_size:.2f} MB")
    print(f"Total rows: {total_rows:,}")


def optimize_table_structures(optimizer, tables):
    """Optimize table structures with proper data types and constraints."""
    print("Optimizing table structures...")
    
    for table in tables:
        try:
            print(f"  Optimizing {table}...")
            statements = optimizer.optimize_table_structure(table, dry_run=False)
            logger.info(f"Optimized {table} with {len(statements)} statements")
            
        except Exception as e:
            logger.warning(f"Failed to optimize table {table}: {str(e)}")
            continue


def create_performance_indexes(optimizer, tables):
    """Create performance-optimized indexes."""
    print("Creating performance indexes...")
    
    # Additional composite indexes for complex queries
    composite_indexes = [
        # E-commerce specific composite indexes
        "CREATE INDEX IF NOT EXISTS idx_product_search_composite ON products_product(category_id, is_active, price, is_featured, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_product_brand_category_price ON products_product(brand, category_id, price, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_order_customer_status_date ON orders_order(customer_id, status, payment_status, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_order_analytics_composite ON orders_order(status, payment_status, total_amount, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_review_product_rating_status ON reviews_review(product_id, rating, status, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_customer_behavior_analysis ON customers_customerprofile(account_status, total_orders, total_spent, last_login_date)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_stock_management ON inventory_inventory(product_id, warehouse_id, current_stock, minimum_stock)",
        "CREATE INDEX IF NOT EXISTS idx_notification_delivery_composite ON notifications_notification(user_id, status, priority, scheduled_at)",
        
        # Full-text search indexes
        "CREATE FULLTEXT INDEX IF NOT EXISTS idx_product_fulltext_search ON products_product(name, description, short_description, tags)",
        "CREATE FULLTEXT INDEX IF NOT EXISTS idx_category_fulltext_search ON products_category(name, description)",
        "CREATE FULLTEXT INDEX IF NOT EXISTS idx_review_fulltext_search ON reviews_review(title, comment, pros, cons)",
        
        # JSON field indexes (MySQL 5.7+)
        "CREATE INDEX IF NOT EXISTS idx_product_dimensions_json ON products_product((CAST(dimensions->>'$.length' AS DECIMAL(8,2))))",
        "CREATE INDEX IF NOT EXISTS idx_order_shipping_address_city ON orders_order((CAST(shipping_address->>'$.city' AS CHAR(100))))",
        "CREATE INDEX IF NOT EXISTS idx_order_billing_address_city ON orders_order((CAST(billing_address->>'$.city' AS CHAR(100))))",
    ]
    
    for index_sql in composite_indexes:
        try:
            with connection.cursor() as cursor:
                cursor.execute(index_sql)
            print(f"  Created composite index")
            logger.info(f"Created index: {index_sql}")
            
        except Exception as e:
            logger.warning(f"Failed to create index: {index_sql}, Error: {str(e)}")
            continue


def setup_table_partitioning(optimizer):
    """Set up table partitioning for large datasets."""
    print("Setting up table partitioning...")
    
    partitioning_configs = optimizer.get_table_partitioning_config()
    
    for table_name, partition_config in partitioning_configs.items():
        try:
            # Check if table exists and has data
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                if row_count > 0:
                    print(f"  Skipping partitioning for {table_name} (contains data)")
                    logger.info(f"Skipped partitioning for {table_name} - table contains {row_count} rows")
                    continue
                
                # Apply partitioning
                sql = f"ALTER TABLE {table_name} {partition_config}"
                cursor.execute(sql)
                print(f"  Set up partitioning for {table_name}")
                logger.info(f"Partitioned table {table_name}")
                
        except Exception as e:
            logger.warning(f"Failed to partition table {table_name}: {str(e)}")
            continue


def optimize_mysql_settings():
    """Optimize MySQL server settings for better performance."""
    print("Optimizing MySQL settings...")
    
    # MySQL optimization queries
    optimization_queries = [
        # Enable query cache
        "SET GLOBAL query_cache_type = ON",
        "SET GLOBAL query_cache_size = 268435456",  # 256MB
        
        # Optimize InnoDB settings
        "SET GLOBAL innodb_buffer_pool_size = 2147483648",  # 2GB
        "SET GLOBAL innodb_log_file_size = 268435456",  # 256MB
        "SET GLOBAL innodb_flush_log_at_trx_commit = 2",
        
        # Connection settings
        "SET GLOBAL max_connections = 500",
        "SET GLOBAL connect_timeout = 60",
        "SET GLOBAL wait_timeout = 28800",
        
        # Enable slow query log
        "SET GLOBAL slow_query_log = ON",
        "SET GLOBAL long_query_time = 2",
        "SET GLOBAL log_queries_not_using_indexes = ON",
    ]
    
    for query in optimization_queries:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
            logger.info(f"Applied MySQL setting: {query}")
            
        except Exception as e:
            logger.warning(f"Failed to apply MySQL setting: {query}, Error: {str(e)}")
            continue
    
    print("  Applied MySQL performance optimizations")


def final_analysis(optimizer, tables):
    """Run final analysis and provide performance report."""
    print("Running final performance analysis...")
    
    total_size_after = 0
    total_rows_after = 0
    optimized_tables = 0
    
    for table in tables:
        try:
            analysis = optimizer.analyze_table_performance(table)
            total_size_after += analysis.get('table_size_mb', 0)
            total_rows_after += analysis.get('row_count', 0)
            optimized_tables += 1
            
        except Exception as e:
            logger.warning(f"Could not analyze table {table}: {str(e)}")
            continue
    
    print(f"\nOptimization Summary:")
    print(f"  Tables optimized: {optimized_tables}")
    print(f"  Total database size: {total_size_after:.2f} MB")
    print(f"  Total rows: {total_rows_after:,}")
    
    # Generate optimization report
    generate_optimization_report(optimizer, tables)


def generate_optimization_report(optimizer, tables):
    """Generate a detailed optimization report."""
    report_file = "mysql_optimization_report.txt"
    
    with open(report_file, 'w') as f:
        f.write("MySQL Schema Optimization Report\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("Optimized Tables:\n")
        f.write("-" * 20 + "\n")
        
        for table in tables:
            try:
                analysis = optimizer.analyze_table_performance(table)
                f.write(f"\n{table}:\n")
                f.write(f"  Rows: {analysis.get('row_count', 0):,}\n")
                f.write(f"  Size: {analysis.get('table_size_mb', 0):.2f} MB\n")
                f.write(f"  Index Size: {analysis.get('index_size_mb', 0):.2f} MB\n")
                
                if analysis.get('recommendations'):
                    f.write(f"  Recommendations: {', '.join(analysis['recommendations'])}\n")
                    
            except Exception as e:
                f.write(f"\n{table}: Analysis failed - {str(e)}\n")
                continue
        
        f.write(f"\nOptimization completed successfully!\n")
        f.write(f"Report generated: {report_file}\n")
    
    print(f"  Detailed report saved to: {report_file}")


if __name__ == "__main__":
    main()