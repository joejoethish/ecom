"""
Django management command to optimize database schema for MySQL.
This command implements comprehensive indexing, foreign key constraints,
and table partitioning for improved performance.
"""
import logging
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
from django.apps import apps

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimize database schema for MySQL with indexes, constraints, and partitioning'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without executing',
        )
        parser.add_argument(
            '--skip-partitioning',
            action='store_true',
            help='Skip table partitioning setup',
        )
        parser.add_argument(
            '--skip-indexes',
            action='store_true',
            help='Skip index creation',
        )
        parser.add_argument(
            '--skip-constraints',
            action='store_true',
            help='Skip foreign key constraint optimization',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.skip_partitioning = options['skip_partitioning']
        self.skip_indexes = options['skip_indexes']
        self.skip_constraints = options['skip_constraints']

        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        try:
            with transaction.atomic():
                self.stdout.write('Starting MySQL schema optimization...')
                
                # 1. Optimize indexes
                if not self.skip_indexes:
                    self.optimize_indexes()
                
                # 2. Optimize foreign key constraints
                if not self.skip_constraints:
                    self.optimize_foreign_keys()
                
                # 3. Set up table partitioning
                if not self.skip_partitioning:
                    self.setup_partitioning()
                
                # 4. Optimize table settings
                self.optimize_table_settings()
                
                self.stdout.write(
                    self.style.SUCCESS('MySQL schema optimization completed successfully!')
                )

        except Exception as e:
            logger.error(f"Schema optimization failed: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Schema optimization failed: {str(e)}')
            )
            raise

    def execute_sql(self, sql, description=""):
        """Execute SQL with proper logging and dry-run support."""
        if description:
            self.stdout.write(f"  {description}")
        
        if self.dry_run:
            self.stdout.write(f"    SQL: {sql}")
            return
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
            logger.info(f"Executed: {sql}")
        except Exception as e:
            logger.error(f"Failed to execute SQL: {sql}, Error: {str(e)}")
            raise

    def optimize_indexes(self):
        """Create comprehensive indexes for better query performance."""
        self.stdout.write(self.style.HTTP_INFO('Optimizing database indexes...'))
        
        # User/Authentication indexes
        user_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_auth_user_email_active ON auth_user(email, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_auth_user_last_login ON auth_user(last_login)",
            "CREATE INDEX IF NOT EXISTS idx_auth_user_date_joined ON auth_user(date_joined)",
        ]
        
        # Product indexes
        product_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_product_category_active ON products_product(category_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_product_price_active ON products_product(price, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_product_featured_active ON products_product(is_featured, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_product_brand_active ON products_product(brand, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_product_status_created ON products_product(status, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_products_product_sku_unique ON products_product(sku)",
            "CREATE FULLTEXT INDEX IF NOT EXISTS idx_products_product_search ON products_product(name, description, short_description)",
            "CREATE INDEX IF NOT EXISTS idx_products_product_tags ON products_product(tags)",
        ]
        
        # Category indexes
        category_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_category_parent_active ON products_category(parent_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_category_sort_order ON products_category(sort_order, name)",
        ]
        
        # Product Image indexes
        product_image_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_productimage_product_primary ON products_productimage(product_id, is_primary)",
            "CREATE INDEX IF NOT EXISTS idx_products_productimage_product_sort ON products_productimage(product_id, sort_order)",
        ]
        
        # Product Rating indexes
        product_rating_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_productrating_avg_rating ON products_productrating(average_rating)",
            "CREATE INDEX IF NOT EXISTS idx_products_productrating_total_reviews ON products_productrating(total_reviews)",
        ]
        
        # Order indexes
        order_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_orders_order_customer_date ON orders_order(customer_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_order_status_date ON orders_order(status, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_order_payment_status ON orders_order(payment_status, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_order_number_unique ON orders_order(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_orders_order_tracking_number ON orders_order(tracking_number)",
            "CREATE INDEX IF NOT EXISTS idx_orders_order_delivery_date ON orders_order(estimated_delivery_date, actual_delivery_date)",
        ]
        
        # Order Item indexes
        order_item_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_orders_orderitem_order_product ON orders_orderitem(order_id, product_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_orderitem_product_status ON orders_orderitem(product_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_orderitem_status_created ON orders_orderitem(status, created_at)",
        ]
        
        # Review indexes
        review_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_reviews_review_product_status ON reviews_review(product_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_review_user_status ON reviews_review(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_review_rating_status ON reviews_review(rating, status)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_review_verified_status ON reviews_review(is_verified_purchase, status)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_review_helpful_count ON reviews_review(helpful_count)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_review_created_status ON reviews_review(created_at, status)",
        ]
        
        # Customer indexes
        customer_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_account_status ON customers_customerprofile(account_status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_verified ON customers_customerprofile(is_verified)",
            "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_total_orders ON customers_customerprofile(total_orders)",
            "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_total_spent ON customers_customerprofile(total_spent)",
            "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_last_login ON customers_customerprofile(last_login_date)",
            "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_loyalty_points ON customers_customerprofile(loyalty_points)",
        ]
        
        # Address indexes
        address_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_customers_address_customer_default ON customers_address(customer_id, is_default)",
            "CREATE INDEX IF NOT EXISTS idx_customers_address_customer_type ON customers_address(customer_id, type)",
            "CREATE INDEX IF NOT EXISTS idx_customers_address_postal_code ON customers_address(postal_code)",
            "CREATE INDEX IF NOT EXISTS idx_customers_address_city_state ON customers_address(city, state)",
            "CREATE INDEX IF NOT EXISTS idx_customers_address_usage_count ON customers_address(usage_count, last_used)",
        ]
        
        # Inventory indexes
        inventory_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_inventory_inventory_product_warehouse ON inventory_inventory(product_id, warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_inventory_stock_level ON inventory_inventory(current_stock, minimum_stock)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_inventory_last_updated ON inventory_inventory(last_updated)",
        ]
        
        # Notification indexes
        notification_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_notifications_notification_user_status ON notifications_notification(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_notification_type_created ON notifications_notification(notification_type, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_notification_scheduled ON notifications_notification(scheduled_at, status)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_notification_priority ON notifications_notification(priority, created_at)",
        ]
        
        # Shipping indexes
        shipping_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_shipping_shipment_order_status ON shipping_shipment(order_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_shipping_shipment_tracking_number ON shipping_shipment(tracking_number)",
            "CREATE INDEX IF NOT EXISTS idx_shipping_shipment_partner_status ON shipping_shipment(shipping_partner_id, status)",
        ]

        # Execute all index creation statements
        all_indexes = (
            user_indexes + product_indexes + category_indexes + 
            product_image_indexes + product_rating_indexes + order_indexes + 
            order_item_indexes + review_indexes + customer_indexes + 
            address_indexes + inventory_indexes + notification_indexes + 
            shipping_indexes
        )
        
        for sql in all_indexes:
            try:
                self.execute_sql(sql, f"Creating index")
            except Exception as e:
                # Log but continue with other indexes
                logger.warning(f"Failed to create index: {sql}, Error: {str(e)}")
                continue

    def optimize_foreign_keys(self):
        """Optimize foreign key constraints with proper cascading rules."""
        self.stdout.write(self.style.HTTP_INFO('Optimizing foreign key constraints...'))
        
        # Foreign key optimizations with cascading rules
        fk_optimizations = [
            # Product related foreign keys
            {
                'table': 'products_product',
                'constraint': 'fk_products_product_category',
                'column': 'category_id',
                'references': 'products_category(id)',
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            {
                'table': 'products_productimage',
                'constraint': 'fk_products_productimage_product',
                'column': 'product_id',
                'references': 'products_product(id)',
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            {
                'table': 'products_productrating',
                'constraint': 'fk_products_productrating_product',
                'column': 'product_id',
                'references': 'products_product(id)',
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            
            # Order related foreign keys
            {
                'table': 'orders_order',
                'constraint': 'fk_orders_order_customer',
                'column': 'customer_id',
                'references': 'auth_user(id)',
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            {
                'table': 'orders_orderitem',
                'constraint': 'fk_orders_orderitem_order',
                'column': 'order_id',
                'references': 'orders_order(id)',
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            {
                'table': 'orders_orderitem',
                'constraint': 'fk_orders_orderitem_product',
                'column': 'product_id',
                'references': 'products_product(id)',
                'on_delete': 'RESTRICT',
                'on_update': 'CASCADE'
            },
            
            # Review related foreign keys
            {
                'table': 'reviews_review',
                'constraint': 'fk_reviews_review_product',
                'column': 'product_id',
                'references': 'products_product(id)',
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            {
                'table': 'reviews_review',
                'constraint': 'fk_reviews_review_user',
                'column': 'user_id',
                'references': 'auth_user(id)',
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            
            # Customer related foreign keys
            {
                'table': 'customers_customerprofile',
                'constraint': 'fk_customers_customerprofile_user',
                'column': 'user_id',
                'references': 'auth_user(id)',
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
            {
                'table': 'customers_address',
                'constraint': 'fk_customers_address_customer',
                'column': 'customer_id',
                'references': 'customers_customerprofile(id)',
                'on_delete': 'CASCADE',
                'on_update': 'CASCADE'
            },
        ]
        
        for fk in fk_optimizations:
            # Drop existing constraint if it exists
            drop_sql = f"""
            ALTER TABLE {fk['table']} 
            DROP FOREIGN KEY IF EXISTS {fk['constraint']}
            """
            
            # Add optimized constraint
            add_sql = f"""
            ALTER TABLE {fk['table']} 
            ADD CONSTRAINT {fk['constraint']} 
            FOREIGN KEY ({fk['column']}) 
            REFERENCES {fk['references']} 
            ON DELETE {fk['on_delete']} 
            ON UPDATE {fk['on_update']}
            """
            
            try:
                self.execute_sql(drop_sql, f"Dropping existing FK constraint {fk['constraint']}")
                self.execute_sql(add_sql, f"Adding optimized FK constraint {fk['constraint']}")
            except Exception as e:
                logger.warning(f"Failed to optimize FK {fk['constraint']}: {str(e)}")
                continue

    def setup_partitioning(self):
        """Set up table partitioning for large datasets."""
        self.stdout.write(self.style.HTTP_INFO('Setting up table partitioning...'))
        
        # Partition orders table by year
        orders_partition_sql = """
        ALTER TABLE orders_order 
        PARTITION BY RANGE (YEAR(created_at)) (
            PARTITION p2023 VALUES LESS THAN (2024),
            PARTITION p2024 VALUES LESS THAN (2025),
            PARTITION p2025 VALUES LESS THAN (2026),
            PARTITION p2026 VALUES LESS THAN (2027),
            PARTITION p_future VALUES LESS THAN MAXVALUE
        )
        """
        
        # Partition notifications by month (for high volume)
        notifications_partition_sql = """
        ALTER TABLE notifications_notification
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
        """
        
        # Partition customer activities by month
        activities_partition_sql = """
        ALTER TABLE customers_customeractivity
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
        """
        
        partitioning_sqls = [
            (orders_partition_sql, "Partitioning orders table by year"),
            (notifications_partition_sql, "Partitioning notifications table by month"),
            (activities_partition_sql, "Partitioning customer activities table by month"),
        ]
        
        for sql, description in partitioning_sqls:
            try:
                self.execute_sql(sql, description)
            except Exception as e:
                # Partitioning might fail if table already has data or is already partitioned
                logger.warning(f"Failed to set up partitioning: {description}, Error: {str(e)}")
                continue

    def optimize_table_settings(self):
        """Optimize MySQL table settings for better performance."""
        self.stdout.write(self.style.HTTP_INFO('Optimizing table settings...'))
        
        # Get all tables from Django models
        tables_to_optimize = [
            'auth_user',
            'products_product',
            'products_category',
            'products_productimage',
            'products_productrating',
            'orders_order',
            'orders_orderitem',
            'reviews_review',
            'customers_customerprofile',
            'customers_address',
            'inventory_inventory',
            'notifications_notification',
            'shipping_shipment',
        ]
        
        for table in tables_to_optimize:
            # Optimize table storage engine and settings
            optimize_sql = f"""
            ALTER TABLE {table} 
            ENGINE=InnoDB 
            ROW_FORMAT=DYNAMIC 
            CHARSET=utf8mb4 
            COLLATE=utf8mb4_unicode_ci
            """
            
            # Analyze table for query optimization
            analyze_sql = f"ANALYZE TABLE {table}"
            
            try:
                self.execute_sql(optimize_sql, f"Optimizing table settings for {table}")
                self.execute_sql(analyze_sql, f"Analyzing table {table}")
            except Exception as e:
                logger.warning(f"Failed to optimize table {table}: {str(e)}")
                continue

    def create_composite_indexes(self):
        """Create composite indexes for complex queries."""
        self.stdout.write(self.style.HTTP_INFO('Creating composite indexes...'))
        
        composite_indexes = [
            # Product search and filtering
            "CREATE INDEX IF NOT EXISTS idx_products_search_filter ON products_product(category_id, is_active, price, is_featured)",
            "CREATE INDEX IF NOT EXISTS idx_products_brand_category ON products_product(brand, category_id, is_active)",
            
            # Order analytics
            "CREATE INDEX IF NOT EXISTS idx_orders_analytics ON orders_order(status, payment_status, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_customer_analytics ON orders_order(customer_id, status, total_amount, created_at)",
            
            # Review analytics
            "CREATE INDEX IF NOT EXISTS idx_reviews_product_analytics ON reviews_review(product_id, status, rating, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_user_analytics ON reviews_review(user_id, status, is_verified_purchase, created_at)",
            
            # Customer behavior analysis
            "CREATE INDEX IF NOT EXISTS idx_customers_behavior ON customers_customerprofile(account_status, total_orders, total_spent, last_login_date)",
            
            # Inventory management
            "CREATE INDEX IF NOT EXISTS idx_inventory_stock_alerts ON inventory_inventory(current_stock, minimum_stock, is_active)",
        ]
        
        for sql in composite_indexes:
            try:
                self.execute_sql(sql, "Creating composite index")
            except Exception as e:
                logger.warning(f"Failed to create composite index: {sql}, Error: {str(e)}")
                continue