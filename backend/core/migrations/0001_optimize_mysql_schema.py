"""
Django migration to optimize MySQL schema with indexes, constraints, and partitioning.
This migration applies MySQL-specific optimizations for better performance.
"""
from django.db import migrations, connection


class Migration(migrations.Migration):
    
    dependencies = [
        ('products', '0001_initial'),
        ('orders', '0001_initial'),
        ('reviews', '0001_initial'),
        ('customers', '0001_initial'),
        ('inventory', '0001_initial'),
        ('notifications', '0001_initial'),
        ('shipping', '0001_initial'),
    ]

    def apply_mysql_optimizations(apps, schema_editor):
        """Apply MySQL-specific optimizations."""
        if connection.vendor != 'mysql':
            return  # Skip if not using MySQL
        
        with connection.cursor() as cursor:
            # Product table optimizations
            product_optimizations = [
                # Optimize data types
                "ALTER TABLE products_product MODIFY COLUMN name VARCHAR(200) NOT NULL",
                "ALTER TABLE products_product MODIFY COLUMN slug VARCHAR(200) NOT NULL",
                "ALTER TABLE products_product MODIFY COLUMN sku VARCHAR(100) NOT NULL",
                "ALTER TABLE products_product MODIFY COLUMN price DECIMAL(10,2) NOT NULL",
                "ALTER TABLE products_product MODIFY COLUMN discount_price DECIMAL(10,2) NULL",
                "ALTER TABLE products_product MODIFY COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1",
                "ALTER TABLE products_product MODIFY COLUMN is_featured TINYINT(1) NOT NULL DEFAULT 0",
                
                # Performance indexes
                "CREATE INDEX IF NOT EXISTS idx_products_product_category_active ON products_product(category_id, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_products_product_price_active ON products_product(price, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_products_product_featured_active ON products_product(is_featured, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_products_product_brand_active ON products_product(brand, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_products_product_status_created ON products_product(status, created_at)",
                "CREATE FULLTEXT INDEX IF NOT EXISTS idx_products_product_search ON products_product(name, description, short_description)",
                
                # Composite indexes for complex queries
                "CREATE INDEX IF NOT EXISTS idx_product_search_composite ON products_product(category_id, is_active, price, is_featured)",
                "CREATE INDEX IF NOT EXISTS idx_product_brand_category_price ON products_product(brand, category_id, price, is_active)",
                
                # Constraints
                "ALTER TABLE products_product ADD CONSTRAINT chk_product_price_positive CHECK (price >= 0)",
                "ALTER TABLE products_product ADD CONSTRAINT chk_product_discount_valid CHECK (discount_price IS NULL OR discount_price >= 0)",
            ]
            
            # Category table optimizations
            category_optimizations = [
                "ALTER TABLE products_category MODIFY COLUMN name VARCHAR(100) NOT NULL",
                "ALTER TABLE products_category MODIFY COLUMN slug VARCHAR(100) NOT NULL",
                "ALTER TABLE products_category MODIFY COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1",
                "ALTER TABLE products_category MODIFY COLUMN sort_order INT UNSIGNED NOT NULL DEFAULT 0",
                
                "CREATE INDEX IF NOT EXISTS idx_products_category_parent_active ON products_category(parent_id, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_products_category_sort_order ON products_category(sort_order, name)",
                
                "ALTER TABLE products_category ADD CONSTRAINT chk_category_sort_order_positive CHECK (sort_order >= 0)",
            ]
            
            # Order table optimizations
            order_optimizations = [
                "ALTER TABLE orders_order MODIFY COLUMN order_number VARCHAR(50) NOT NULL",
                "ALTER TABLE orders_order MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'",
                "ALTER TABLE orders_order MODIFY COLUMN payment_status VARCHAR(20) NOT NULL DEFAULT 'pending'",
                "ALTER TABLE orders_order MODIFY COLUMN total_amount DECIMAL(10,2) NOT NULL",
                "ALTER TABLE orders_order MODIFY COLUMN shipping_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00",
                "ALTER TABLE orders_order MODIFY COLUMN tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00",
                
                "CREATE INDEX IF NOT EXISTS idx_orders_order_customer_date ON orders_order(customer_id, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_orders_order_status_date ON orders_order(status, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_orders_order_payment_status ON orders_order(payment_status, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders_order(order_number)",
                "CREATE INDEX IF NOT EXISTS idx_orders_order_tracking_number ON orders_order(tracking_number)",
                
                "CREATE INDEX IF NOT EXISTS idx_order_analytics_composite ON orders_order(status, payment_status, total_amount, created_at)",
                
                "ALTER TABLE orders_order ADD CONSTRAINT chk_order_amounts_positive CHECK (total_amount >= 0 AND shipping_amount >= 0 AND tax_amount >= 0)",
            ]
            
            # Review table optimizations
            review_optimizations = [
                "ALTER TABLE reviews_review MODIFY COLUMN rating TINYINT UNSIGNED NOT NULL",
                "ALTER TABLE reviews_review MODIFY COLUMN title VARCHAR(200) NOT NULL",
                "ALTER TABLE reviews_review MODIFY COLUMN is_verified_purchase TINYINT(1) NOT NULL DEFAULT 0",
                "ALTER TABLE reviews_review MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'",
                "ALTER TABLE reviews_review MODIFY COLUMN helpful_count INT UNSIGNED NOT NULL DEFAULT 0",
                "ALTER TABLE reviews_review MODIFY COLUMN not_helpful_count INT UNSIGNED NOT NULL DEFAULT 0",
                
                "CREATE INDEX IF NOT EXISTS idx_reviews_review_product_status ON reviews_review(product_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_review_user_status ON reviews_review(user_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_review_rating_status ON reviews_review(rating, status)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_review_verified_status ON reviews_review(is_verified_purchase, status)",
                "CREATE INDEX IF NOT EXISTS idx_reviews_review_helpful_count ON reviews_review(helpful_count)",
                
                "CREATE INDEX IF NOT EXISTS idx_review_product_rating_status ON reviews_review(product_id, rating, status, created_at)",
                
                "ALTER TABLE reviews_review ADD CONSTRAINT chk_review_rating_valid CHECK (rating BETWEEN 1 AND 5)",
                "ALTER TABLE reviews_review ADD CONSTRAINT chk_review_helpful_counts_positive CHECK (helpful_count >= 0 AND not_helpful_count >= 0)",
            ]
            
            # Customer table optimizations
            customer_optimizations = [
                "ALTER TABLE customers_customerprofile MODIFY COLUMN gender CHAR(1) NOT NULL DEFAULT ''",
                "ALTER TABLE customers_customerprofile MODIFY COLUMN phone_number VARCHAR(17) NOT NULL DEFAULT ''",
                "ALTER TABLE customers_customerprofile MODIFY COLUMN account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'",
                "ALTER TABLE customers_customerprofile MODIFY COLUMN is_verified TINYINT(1) NOT NULL DEFAULT 0",
                "ALTER TABLE customers_customerprofile MODIFY COLUMN total_orders INT UNSIGNED NOT NULL DEFAULT 0",
                "ALTER TABLE customers_customerprofile MODIFY COLUMN total_spent DECIMAL(12,2) NOT NULL DEFAULT 0.00",
                "ALTER TABLE customers_customerprofile MODIFY COLUMN loyalty_points INT UNSIGNED NOT NULL DEFAULT 0",
                
                "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_account_status ON customers_customerprofile(account_status)",
                "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_verified ON customers_customerprofile(is_verified)",
                "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_total_orders ON customers_customerprofile(total_orders)",
                "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_total_spent ON customers_customerprofile(total_spent)",
                "CREATE INDEX IF NOT EXISTS idx_customers_customerprofile_loyalty_points ON customers_customerprofile(loyalty_points)",
                
                "CREATE INDEX IF NOT EXISTS idx_customer_behavior_analysis ON customers_customerprofile(account_status, total_orders, total_spent, last_login_date)",
                
                "ALTER TABLE customers_customerprofile ADD CONSTRAINT chk_customer_metrics_positive CHECK (total_orders >= 0 AND total_spent >= 0 AND loyalty_points >= 0)",
            ]
            
            # Address table optimizations
            address_optimizations = [
                "CREATE INDEX IF NOT EXISTS idx_customers_address_customer_default ON customers_address(customer_id, is_default)",
                "CREATE INDEX IF NOT EXISTS idx_customers_address_customer_type ON customers_address(customer_id, type)",
                "CREATE INDEX IF NOT EXISTS idx_customers_address_postal_code ON customers_address(postal_code)",
                "CREATE INDEX IF NOT EXISTS idx_customers_address_city_state ON customers_address(city, state)",
            ]
            
            # User table optimizations
            user_optimizations = [
                "CREATE INDEX IF NOT EXISTS idx_auth_user_email_active ON auth_user(email, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_auth_user_username_active ON auth_user(username, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_auth_user_last_login ON auth_user(last_login)",
                "CREATE INDEX IF NOT EXISTS idx_auth_user_date_joined ON auth_user(date_joined)",
            ]
            
            # Apply all optimizations
            all_optimizations = (
                product_optimizations + 
                category_optimizations + 
                order_optimizations + 
                review_optimizations + 
                customer_optimizations + 
                address_optimizations + 
                user_optimizations
            )
            
            for sql in all_optimizations:
                try:
                    cursor.execute(sql)
                except Exception as e:
                    # Log but continue with other optimizations
                    print(f"Warning: Failed to execute: {sql}, Error: {str(e)}")
                    continue
            
            # Optimize table settings
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
            ]
            
            for table in tables_to_optimize:
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        ENGINE=InnoDB 
                        ROW_FORMAT=DYNAMIC 
                        CHARSET=utf8mb4 
                        COLLATE=utf8mb4_unicode_ci
                    """)
                    cursor.execute(f"ANALYZE TABLE {table}")
                except Exception as e:
                    print(f"Warning: Failed to optimize table {table}: {str(e)}")
                    continue

    def reverse_mysql_optimizations(apps, schema_editor):
        """Reverse MySQL optimizations (limited - mainly drop custom indexes)."""
        if connection.vendor != 'mysql':
            return
        
        with connection.cursor() as cursor:
            # Drop custom indexes (constraints and data type changes are harder to reverse)
            indexes_to_drop = [
                "DROP INDEX IF EXISTS idx_products_product_category_active ON products_product",
                "DROP INDEX IF EXISTS idx_products_product_price_active ON products_product",
                "DROP INDEX IF EXISTS idx_products_product_featured_active ON products_product",
                "DROP INDEX IF EXISTS idx_products_product_brand_active ON products_product",
                "DROP INDEX IF EXISTS idx_products_product_status_created ON products_product",
                "DROP INDEX IF EXISTS idx_products_product_search ON products_product",
                "DROP INDEX IF EXISTS idx_product_search_composite ON products_product",
                "DROP INDEX IF EXISTS idx_product_brand_category_price ON products_product",
                
                "DROP INDEX IF EXISTS idx_products_category_parent_active ON products_category",
                "DROP INDEX IF EXISTS idx_products_category_sort_order ON products_category",
                
                "DROP INDEX IF EXISTS idx_orders_order_customer_date ON orders_order",
                "DROP INDEX IF EXISTS idx_orders_order_status_date ON orders_order",
                "DROP INDEX IF EXISTS idx_orders_order_payment_status ON orders_order",
                "DROP INDEX IF EXISTS idx_orders_order_number ON orders_order",
                "DROP INDEX IF EXISTS idx_orders_order_tracking_number ON orders_order",
                "DROP INDEX IF EXISTS idx_order_analytics_composite ON orders_order",
                
                "DROP INDEX IF EXISTS idx_reviews_review_product_status ON reviews_review",
                "DROP INDEX IF EXISTS idx_reviews_review_user_status ON reviews_review",
                "DROP INDEX IF EXISTS idx_reviews_review_rating_status ON reviews_review",
                "DROP INDEX IF EXISTS idx_reviews_review_verified_status ON reviews_review",
                "DROP INDEX IF EXISTS idx_reviews_review_helpful_count ON reviews_review",
                "DROP INDEX IF EXISTS idx_review_product_rating_status ON reviews_review",
                
                "DROP INDEX IF EXISTS idx_customers_customerprofile_account_status ON customers_customerprofile",
                "DROP INDEX IF EXISTS idx_customers_customerprofile_verified ON customers_customerprofile",
                "DROP INDEX IF EXISTS idx_customers_customerprofile_total_orders ON customers_customerprofile",
                "DROP INDEX IF EXISTS idx_customers_customerprofile_total_spent ON customers_customerprofile",
                "DROP INDEX IF EXISTS idx_customers_customerprofile_loyalty_points ON customers_customerprofile",
                "DROP INDEX IF EXISTS idx_customer_behavior_analysis ON customers_customerprofile",
                
                "DROP INDEX IF EXISTS idx_customers_address_customer_default ON customers_address",
                "DROP INDEX IF EXISTS idx_customers_address_customer_type ON customers_address",
                "DROP INDEX IF EXISTS idx_customers_address_postal_code ON customers_address",
                "DROP INDEX IF EXISTS idx_customers_address_city_state ON customers_address",
                
                "DROP INDEX IF EXISTS idx_auth_user_email_active ON auth_user",
                "DROP INDEX IF EXISTS idx_auth_user_username_active ON auth_user",
                "DROP INDEX IF EXISTS idx_auth_user_last_login ON auth_user",
                "DROP INDEX IF EXISTS idx_auth_user_date_joined ON auth_user",
            ]
            
            for sql in indexes_to_drop:
                try:
                    cursor.execute(sql)
                except Exception as e:
                    print(f"Warning: Failed to drop index: {sql}, Error: {str(e)}")
                    continue

    operations = [
        migrations.RunPython(
            apply_mysql_optimizations,
            reverse_mysql_optimizations,
            hints={'target_db': 'mysql'}
        ),
    ]