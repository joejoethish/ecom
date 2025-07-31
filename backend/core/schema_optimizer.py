"""
MySQL Schema Optimizer
Handles conversion from SQLite schema to MySQL-optimized structure
with proper data types, constraints, and performance optimizations.
"""
import logging
from django.db import connection
from django.conf import settings
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class MySQLSchemaOptimizer:
    """
    Optimizes database schema for MySQL with proper data types,
    indexes, constraints, and partitioning.
    """
    
    def __init__(self):
        self.connection = connection
        
    def get_sqlite_to_mysql_type_mapping(self) -> Dict[str, str]:
        """
        Map SQLite data types to optimized MySQL data types.
        """
        return {
            # Text types
            'TEXT': 'TEXT',
            'VARCHAR': 'VARCHAR',
            'CHAR': 'CHAR',
            'CLOB': 'LONGTEXT',
            
            # Numeric types
            'INTEGER': 'INT',
            'BIGINT': 'BIGINT',
            'SMALLINT': 'SMALLINT',
            'TINYINT': 'TINYINT',
            'DECIMAL': 'DECIMAL',
            'NUMERIC': 'DECIMAL',
            'REAL': 'DOUBLE',
            'DOUBLE': 'DOUBLE',
            'FLOAT': 'FLOAT',
            
            # Date/Time types
            'DATE': 'DATE',
            'TIME': 'TIME',
            'DATETIME': 'DATETIME',
            'TIMESTAMP': 'TIMESTAMP',
            
            # Binary types
            'BLOB': 'LONGBLOB',
            'BINARY': 'BINARY',
            'VARBINARY': 'VARBINARY',
            
            # Boolean
            'BOOLEAN': 'TINYINT(1)',
            
            # JSON
            'JSON': 'JSON',
        }
    
    def get_optimized_column_definitions(self) -> Dict[str, Dict[str, str]]:
        """
        Get optimized column definitions for specific tables and columns.
        """
        return {
            'auth_user': {
                'email': 'VARCHAR(254) NOT NULL',
                'username': 'VARCHAR(150) NOT NULL',
                'first_name': 'VARCHAR(150) NOT NULL DEFAULT ""',
                'last_name': 'VARCHAR(150) NOT NULL DEFAULT ""',
                'password': 'VARCHAR(128) NOT NULL',
                'is_active': 'TINYINT(1) NOT NULL DEFAULT 1',
                'is_staff': 'TINYINT(1) NOT NULL DEFAULT 0',
                'is_superuser': 'TINYINT(1) NOT NULL DEFAULT 0',
                'date_joined': 'DATETIME(6) NOT NULL',
                'last_login': 'DATETIME(6) NULL',
            },
            'products_product': {
                'name': 'VARCHAR(200) NOT NULL',
                'slug': 'VARCHAR(200) NOT NULL UNIQUE',
                'description': 'TEXT NOT NULL',
                'short_description': 'VARCHAR(500) NOT NULL DEFAULT ""',
                'brand': 'VARCHAR(100) NOT NULL DEFAULT ""',
                'sku': 'VARCHAR(100) NOT NULL UNIQUE',
                'price': 'DECIMAL(10,2) NOT NULL',
                'discount_price': 'DECIMAL(10,2) NULL',
                'weight': 'DECIMAL(8,2) NULL',
                'dimensions': 'JSON NULL',
                'is_active': 'TINYINT(1) NOT NULL DEFAULT 1',
                'is_featured': 'TINYINT(1) NOT NULL DEFAULT 0',
                'meta_title': 'VARCHAR(200) NOT NULL DEFAULT ""',
                'meta_description': 'VARCHAR(500) NOT NULL DEFAULT ""',
                'tags': 'VARCHAR(500) NOT NULL DEFAULT ""',
                'status': 'VARCHAR(20) NOT NULL DEFAULT "draft"',
                'created_at': 'DATETIME(6) NOT NULL',
                'updated_at': 'DATETIME(6) NOT NULL',
            },
            'products_category': {
                'name': 'VARCHAR(100) NOT NULL',
                'slug': 'VARCHAR(100) NOT NULL UNIQUE',
                'description': 'TEXT NOT NULL DEFAULT ""',
                'is_active': 'TINYINT(1) NOT NULL DEFAULT 1',
                'sort_order': 'INT UNSIGNED NOT NULL DEFAULT 0',
                'created_at': 'DATETIME(6) NOT NULL',
                'updated_at': 'DATETIME(6) NOT NULL',
            },
            'orders_order': {
                'order_number': 'VARCHAR(50) NOT NULL UNIQUE',
                'status': 'VARCHAR(20) NOT NULL DEFAULT "pending"',
                'payment_status': 'VARCHAR(20) NOT NULL DEFAULT "pending"',
                'total_amount': 'DECIMAL(10,2) NOT NULL',
                'shipping_amount': 'DECIMAL(10,2) NOT NULL DEFAULT 0.00',
                'tax_amount': 'DECIMAL(10,2) NOT NULL DEFAULT 0.00',
                'discount_amount': 'DECIMAL(10,2) NOT NULL DEFAULT 0.00',
                'shipping_address': 'JSON NULL',
                'billing_address': 'JSON NULL',
                'shipping_method': 'VARCHAR(50) NOT NULL DEFAULT ""',
                'payment_method': 'VARCHAR(50) NOT NULL DEFAULT ""',
                'estimated_delivery_date': 'DATE NULL',
                'actual_delivery_date': 'DATE NULL',
                'tracking_number': 'VARCHAR(100) NOT NULL DEFAULT ""',
                'invoice_number': 'VARCHAR(50) NOT NULL DEFAULT ""',
                'notes': 'TEXT NOT NULL DEFAULT ""',
                'created_at': 'DATETIME(6) NOT NULL',
                'updated_at': 'DATETIME(6) NOT NULL',
            },
            'reviews_review': {
                'rating': 'TINYINT UNSIGNED NOT NULL',
                'title': 'VARCHAR(200) NOT NULL',
                'comment': 'TEXT NOT NULL',
                'is_verified_purchase': 'TINYINT(1) NOT NULL DEFAULT 0',
                'status': 'VARCHAR(20) NOT NULL DEFAULT "pending"',
                'moderated_at': 'DATETIME(6) NULL',
                'moderation_notes': 'TEXT NOT NULL DEFAULT ""',
                'helpful_count': 'INT UNSIGNED NOT NULL DEFAULT 0',
                'not_helpful_count': 'INT UNSIGNED NOT NULL DEFAULT 0',
                'pros': 'TEXT NOT NULL DEFAULT ""',
                'cons': 'TEXT NOT NULL DEFAULT ""',
                'created_at': 'DATETIME(6) NOT NULL',
                'updated_at': 'DATETIME(6) NOT NULL',
            },
            'customers_customerprofile': {
                'date_of_birth': 'DATE NULL',
                'gender': 'CHAR(1) NOT NULL DEFAULT ""',
                'phone_number': 'VARCHAR(17) NOT NULL DEFAULT ""',
                'alternate_phone': 'VARCHAR(17) NOT NULL DEFAULT ""',
                'account_status': 'VARCHAR(20) NOT NULL DEFAULT "ACTIVE"',
                'is_verified': 'TINYINT(1) NOT NULL DEFAULT 0',
                'verification_date': 'DATETIME(6) NULL',
                'newsletter_subscription': 'TINYINT(1) NOT NULL DEFAULT 1',
                'sms_notifications': 'TINYINT(1) NOT NULL DEFAULT 1',
                'email_notifications': 'TINYINT(1) NOT NULL DEFAULT 1',
                'push_notifications': 'TINYINT(1) NOT NULL DEFAULT 1',
                'total_orders': 'INT UNSIGNED NOT NULL DEFAULT 0',
                'total_spent': 'DECIMAL(12,2) NOT NULL DEFAULT 0.00',
                'loyalty_points': 'INT UNSIGNED NOT NULL DEFAULT 0',
                'last_login_date': 'DATETIME(6) NULL',
                'last_order_date': 'DATETIME(6) NULL',
                'notes': 'TEXT NOT NULL DEFAULT ""',
                'created_at': 'DATETIME(6) NOT NULL',
                'updated_at': 'DATETIME(6) NOT NULL',
            },
        }
    
    def get_table_constraints(self) -> Dict[str, List[str]]:
        """
        Get table-specific constraints for MySQL optimization.
        """
        return {
            'auth_user': [
                'CONSTRAINT chk_user_email_format CHECK (email REGEXP "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")',
                'CONSTRAINT chk_user_username_length CHECK (CHAR_LENGTH(username) >= 3)',
            ],
            'products_product': [
                'CONSTRAINT chk_product_price_positive CHECK (price >= 0)',
                'CONSTRAINT chk_product_discount_valid CHECK (discount_price IS NULL OR discount_price >= 0)',
                'CONSTRAINT chk_product_weight_positive CHECK (weight IS NULL OR weight >= 0)',
                'CONSTRAINT chk_product_status_valid CHECK (status IN ("draft", "active", "inactive", "out_of_stock"))',
            ],
            'products_category': [
                'CONSTRAINT chk_category_sort_order_positive CHECK (sort_order >= 0)',
            ],
            'orders_order': [
                'CONSTRAINT chk_order_amounts_positive CHECK (total_amount >= 0 AND shipping_amount >= 0 AND tax_amount >= 0 AND discount_amount >= 0)',
                'CONSTRAINT chk_order_status_valid CHECK (status IN ("pending", "confirmed", "processing", "shipped", "out_for_delivery", "delivered", "cancelled", "returned", "refunded", "partially_returned", "partially_refunded"))',
                'CONSTRAINT chk_order_payment_status_valid CHECK (payment_status IN ("pending", "paid", "failed", "refunded", "partially_refunded"))',
            ],
            'reviews_review': [
                'CONSTRAINT chk_review_rating_valid CHECK (rating BETWEEN 1 AND 5)',
                'CONSTRAINT chk_review_status_valid CHECK (status IN ("pending", "approved", "rejected", "flagged"))',
                'CONSTRAINT chk_review_helpful_counts_positive CHECK (helpful_count >= 0 AND not_helpful_count >= 0)',
            ],
            'customers_customerprofile': [
                'CONSTRAINT chk_customer_gender_valid CHECK (gender IN ("", "M", "F", "O", "N"))',
                'CONSTRAINT chk_customer_account_status_valid CHECK (account_status IN ("ACTIVE", "SUSPENDED", "BLOCKED", "PENDING_VERIFICATION"))',
                'CONSTRAINT chk_customer_metrics_positive CHECK (total_orders >= 0 AND total_spent >= 0 AND loyalty_points >= 0)',
            ],
        }
    
    def get_performance_indexes(self) -> Dict[str, List[str]]:
        """
        Get performance-optimized indexes for each table.
        """
        return {
            'auth_user': [
                'CREATE INDEX idx_auth_user_email_active ON auth_user(email, is_active)',
                'CREATE INDEX idx_auth_user_username_active ON auth_user(username, is_active)',
                'CREATE INDEX idx_auth_user_last_login ON auth_user(last_login)',
                'CREATE INDEX idx_auth_user_date_joined ON auth_user(date_joined)',
            ],
            'products_product': [
                'CREATE INDEX idx_products_product_category_active ON products_product(category_id, is_active)',
                'CREATE INDEX idx_products_product_price_active ON products_product(price, is_active)',
                'CREATE INDEX idx_products_product_featured_active ON products_product(is_featured, is_active)',
                'CREATE INDEX idx_products_product_brand_active ON products_product(brand, is_active)',
                'CREATE INDEX idx_products_product_status_created ON products_product(status, created_at)',
                'CREATE INDEX idx_products_product_sku ON products_product(sku)',
                'CREATE FULLTEXT INDEX idx_products_product_search ON products_product(name, description, short_description)',
                'CREATE INDEX idx_products_product_tags ON products_product(tags)',
                'CREATE INDEX idx_products_product_price_range ON products_product(price, discount_price, is_active)',
            ],
            'products_category': [
                'CREATE INDEX idx_products_category_parent_active ON products_category(parent_id, is_active)',
                'CREATE INDEX idx_products_category_sort_order ON products_category(sort_order, name)',
                'CREATE INDEX idx_products_category_slug ON products_category(slug)',
            ],
            'orders_order': [
                'CREATE INDEX idx_orders_order_customer_date ON orders_order(customer_id, created_at)',
                'CREATE INDEX idx_orders_order_status_date ON orders_order(status, created_at)',
                'CREATE INDEX idx_orders_order_payment_status ON orders_order(payment_status, created_at)',
                'CREATE INDEX idx_orders_order_number ON orders_order(order_number)',
                'CREATE INDEX idx_orders_order_tracking_number ON orders_order(tracking_number)',
                'CREATE INDEX idx_orders_order_delivery_dates ON orders_order(estimated_delivery_date, actual_delivery_date)',
                'CREATE INDEX idx_orders_order_analytics ON orders_order(status, payment_status, total_amount, created_at)',
            ],
            'orders_orderitem': [
                'CREATE INDEX idx_orders_orderitem_order_product ON orders_orderitem(order_id, product_id)',
                'CREATE INDEX idx_orders_orderitem_product_status ON orders_orderitem(product_id, status)',
                'CREATE INDEX idx_orders_orderitem_status_created ON orders_orderitem(status, created_at)',
            ],
            'reviews_review': [
                'CREATE INDEX idx_reviews_review_product_status ON reviews_review(product_id, status)',
                'CREATE INDEX idx_reviews_review_user_status ON reviews_review(user_id, status)',
                'CREATE INDEX idx_reviews_review_rating_status ON reviews_review(rating, status)',
                'CREATE INDEX idx_reviews_review_verified_status ON reviews_review(is_verified_purchase, status)',
                'CREATE INDEX idx_reviews_review_helpful_count ON reviews_review(helpful_count)',
                'CREATE INDEX idx_reviews_review_created_status ON reviews_review(created_at, status)',
                'CREATE INDEX idx_reviews_review_moderated ON reviews_review(moderated_at, status)',
            ],
            'customers_customerprofile': [
                'CREATE INDEX idx_customers_customerprofile_account_status ON customers_customerprofile(account_status)',
                'CREATE INDEX idx_customers_customerprofile_verified ON customers_customerprofile(is_verified)',
                'CREATE INDEX idx_customers_customerprofile_total_orders ON customers_customerprofile(total_orders)',
                'CREATE INDEX idx_customers_customerprofile_total_spent ON customers_customerprofile(total_spent)',
                'CREATE INDEX idx_customers_customerprofile_last_login ON customers_customerprofile(last_login_date)',
                'CREATE INDEX idx_customers_customerprofile_loyalty_points ON customers_customerprofile(loyalty_points)',
                'CREATE INDEX idx_customers_customerprofile_tier_analysis ON customers_customerprofile(total_spent, total_orders, account_status)',
            ],
            'customers_address': [
                'CREATE INDEX idx_customers_address_customer_default ON customers_address(customer_id, is_default)',
                'CREATE INDEX idx_customers_address_customer_type ON customers_address(customer_id, type)',
                'CREATE INDEX idx_customers_address_postal_code ON customers_address(postal_code)',
                'CREATE INDEX idx_customers_address_city_state ON customers_address(city, state)',
                'CREATE INDEX idx_customers_address_usage_count ON customers_address(usage_count, last_used)',
            ],
        }
    
    def get_table_partitioning_config(self) -> Dict[str, str]:
        """
        Get partitioning configuration for large tables.
        """
        return {
            'orders_order': """
                PARTITION BY RANGE (YEAR(created_at)) (
                    PARTITION p2023 VALUES LESS THAN (2024),
                    PARTITION p2024 VALUES LESS THAN (2025),
                    PARTITION p2025 VALUES LESS THAN (2026),
                    PARTITION p2026 VALUES LESS THAN (2027),
                    PARTITION p_future VALUES LESS THAN MAXVALUE
                )
            """,
            'notifications_notification': """
                PARTITION BY RANGE (TO_DAYS(created_at)) (
                    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
                    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
                    PARTITION p202403 VALUES LESS THAN (TO_DAYS('2024-04-01')),
                    PARTITION p202404 VALUES LESS THAN (TO_DAYS('2024-05-01')),
                    PARTITION p202405 VALUES LESS THAN (TO_DAYS('2024-06-01')),
                    PARTITION p202406 VALUES LESS THAN (TO_DAYS('2024-07-01')),
                    PARTITION p202407 VALUES LESS THAN (TO_DAYS('2024-08-01')),
                    PARTITION p202408 VALUES LESS THAN (TO_DAYS('2024-09-01')),
                    PARTITION p202409 VALUES LESS THAN (TO_DAYS('2024-10-01')),
                    PARTITION p202410 VALUES LESS THAN (TO_DAYS('2024-11-01')),
                    PARTITION p202411 VALUES LESS THAN (TO_DAYS('2024-12-01')),
                    PARTITION p202412 VALUES LESS THAN (TO_DAYS('2025-01-01')),
                    PARTITION p_future VALUES LESS THAN MAXVALUE
                )
            """,
            'customers_customeractivity': """
                PARTITION BY RANGE (TO_DAYS(created_at)) (
                    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
                    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
                    PARTITION p202403 VALUES LESS THAN (TO_DAYS('2024-04-01')),
                    PARTITION p202404 VALUES LESS THAN (TO_DAYS('2024-05-01')),
                    PARTITION p202405 VALUES LESS THAN (TO_DAYS('2024-06-01')),
                    PARTITION p202406 VALUES LESS THAN (TO_DAYS('2024-07-01')),
                    PARTITION p202407 VALUES LESS THAN (TO_DAYS('2024-08-01')),
                    PARTITION p202408 VALUES LESS THAN (TO_DAYS('2024-09-01')),
                    PARTITION p202409 VALUES LESS THAN (TO_DAYS('2024-10-01')),
                    PARTITION p202410 VALUES LESS THAN (TO_DAYS('2024-11-01')),
                    PARTITION p202411 VALUES LESS THAN (TO_DAYS('2024-12-01')),
                    PARTITION p202412 VALUES LESS THAN (TO_DAYS('2025-01-01')),
                    PARTITION p_future VALUES LESS THAN MAXVALUE
                )
            """,
        }
    
    def optimize_table_structure(self, table_name: str, dry_run: bool = False) -> List[str]:
        """
        Optimize a specific table structure for MySQL.
        """
        executed_statements = []
        
        # Get optimized column definitions
        column_definitions = self.get_optimized_column_definitions().get(table_name, {})
        
        # Modify columns to use optimized data types
        for column_name, definition in column_definitions.items():
            sql = f"ALTER TABLE {table_name} MODIFY COLUMN {column_name} {definition}"
            
            if not dry_run:
                try:
                    with self.connection.cursor() as cursor:
                        cursor.execute(sql)
                    executed_statements.append(sql)
                    logger.info(f"Optimized column {table_name}.{column_name}")
                except Exception as e:
                    logger.warning(f"Failed to optimize column {table_name}.{column_name}: {str(e)}")
            else:
                executed_statements.append(sql)
        
        # Add table constraints
        constraints = self.get_table_constraints().get(table_name, [])
        for constraint in constraints:
            sql = f"ALTER TABLE {table_name} ADD {constraint}"
            
            if not dry_run:
                try:
                    with self.connection.cursor() as cursor:
                        cursor.execute(sql)
                    executed_statements.append(sql)
                    logger.info(f"Added constraint to {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to add constraint to {table_name}: {str(e)}")
            else:
                executed_statements.append(sql)
        
        # Create performance indexes
        indexes = self.get_performance_indexes().get(table_name, [])
        for index_sql in indexes:
            if not dry_run:
                try:
                    with self.connection.cursor() as cursor:
                        cursor.execute(index_sql)
                    executed_statements.append(index_sql)
                    logger.info(f"Created index for {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to create index for {table_name}: {str(e)}")
            else:
                executed_statements.append(index_sql)
        
        # Set up partitioning if configured
        partitioning_config = self.get_table_partitioning_config().get(table_name)
        if partitioning_config:
            sql = f"ALTER TABLE {table_name} {partitioning_config}"
            
            if not dry_run:
                try:
                    with self.connection.cursor() as cursor:
                        cursor.execute(sql)
                    executed_statements.append(sql)
                    logger.info(f"Set up partitioning for {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to set up partitioning for {table_name}: {str(e)}")
            else:
                executed_statements.append(sql)
        
        # Optimize table settings
        optimize_sql = f"""
        ALTER TABLE {table_name} 
        ENGINE=InnoDB 
        ROW_FORMAT=DYNAMIC 
        CHARSET=utf8mb4 
        COLLATE=utf8mb4_unicode_ci
        """
        
        if not dry_run:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(optimize_sql)
                executed_statements.append(optimize_sql)
                logger.info(f"Optimized table settings for {table_name}")
            except Exception as e:
                logger.warning(f"Failed to optimize table settings for {table_name}: {str(e)}")
        else:
            executed_statements.append(optimize_sql)
        
        return executed_statements
    
    def analyze_table_performance(self, table_name: str) -> Dict[str, any]:
        """
        Analyze table performance and provide optimization recommendations.
        """
        analysis = {
            'table_name': table_name,
            'row_count': 0,
            'table_size_mb': 0,
            'index_size_mb': 0,
            'recommendations': []
        }
        
        try:
            with self.connection.cursor() as cursor:
                # Get table statistics
                cursor.execute(f"""
                    SELECT 
                        table_rows,
                        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS table_size_mb,
                        ROUND((data_length / 1024 / 1024), 2) AS data_size_mb,
                        ROUND((index_length / 1024 / 1024), 2) AS index_size_mb
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = %s
                """, [table_name])
                
                result = cursor.fetchone()
                if result:
                    analysis['row_count'] = result[0] or 0
                    analysis['table_size_mb'] = result[1] or 0
                    analysis['data_size_mb'] = result[2] or 0
                    analysis['index_size_mb'] = result[3] or 0
                
                # Analyze index usage
                cursor.execute(f"SHOW INDEX FROM {table_name}")
                indexes = cursor.fetchall()
                
                # Generate recommendations based on analysis
                if analysis['row_count'] > 100000:
                    analysis['recommendations'].append("Consider partitioning for large dataset")
                
                if analysis['index_size_mb'] > analysis['data_size_mb']:
                    analysis['recommendations'].append("Review index usage - index size exceeds data size")
                
                if len(indexes) < 3:
                    analysis['recommendations'].append("Consider adding more indexes for query optimization")
                
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {str(e)}")
            analysis['error'] = str(e)
        
        return analysis