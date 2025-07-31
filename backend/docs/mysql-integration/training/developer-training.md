# Developer Training Guide

## Overview

This training guide is designed for application developers who will be working with the MySQL database in the ecommerce platform. It covers database integration, query optimization, and best practices for application development.

## Training Prerequisites

### Required Knowledge
- Python programming fundamentals
- Django framework basics
- SQL query language
- Object-Relational Mapping (ORM) concepts
- Web application development principles

### Recommended Experience
- Previous experience with relational databases
- Understanding of database design principles
- Basic knowledge of performance optimization
- Familiarity with version control systems

## Module 1: Django MySQL Integration

### 1.1 Database Configuration

#### Django Settings Configuration
```python
# settings/mysql_production.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'ecommerce_db'),
        'USER': os.getenv('DB_USER', 'ecommerce_app'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
            'ssl': {
                'ca': '/path/to/ca-cert.pem',
                'cert': '/path/to/client-cert.pem',
                'key': '/path/to/client-key.pem',
            },
        },
        'CONN_MAX_AGE': 3600,
        'CONN_HEALTH_CHECKS': True,
    },
    'read_replica': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'ecommerce_db'),
        'USER': os.getenv('DB_READ_USER', 'ecommerce_readonly'),
        'PASSWORD': os.getenv('DB_READ_PASSWORD'),
        'HOST': os.getenv('DB_READ_HOST', 'mysql-replica.company.com'),
        'PORT': os.getenv('DB_READ_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Database routing for read/write splitting
DATABASE_ROUTERS = ['core.routers.DatabaseRouter']

# Connection pooling settings
DATABASES['default']['CONN_MAX_AGE'] = 3600
DATABASES['default']['CONN_HEALTH_CHECKS'] = True
```

#### Database Router Implementation
```python
# core/routers.py

class DatabaseRouter:
    """
    A router to control all database operations on models
    """
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from."""
        # Route read operations for specific apps to read replica
        if model._meta.app_label in ['analytics', 'reports']:
            return 'read_replica'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Suggest the database to write to."""
        # All writes go to primary database
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same app."""
        db_set = {'default', 'read_replica'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that certain apps' models get created on the right database."""
        return db == 'default'
```

#### Hands-on Exercise 1.1
```python
# Practice: Configure Django for MySQL
# 1. Set up database configuration
# 2. Implement database router
# 3. Test connection to both primary and replica
# 4. Verify SSL connection

# Test database connectivity
from django.db import connections
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Test primary database
        primary_db = connections['default']
        with primary_db.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.stdout.write(f"Primary DB: {result}")
        
        # Test read replica
        replica_db = connections['read_replica']
        with replica_db.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.stdout.write(f"Replica DB: {result}")
```

### 1.2 Model Design for MySQL

#### Optimized Model Definitions
```python
# models.py - Optimized for MySQL

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products_category'
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['name']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products',
        db_index=True
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        db_index=True
    )
    stock_quantity = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products_product'
        indexes = [
            # Composite indexes for common query patterns
            models.Index(fields=['category', 'is_active', 'price']),
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['price', 'is_active']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name='orders',
        db_index=True
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        db_index=True
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders_order'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.id} - {self.user.username}"
```

#### Migration Best Practices
```python
# migrations/0001_initial.py - Optimized migration

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'products_category',
                'ordering': ['name'],
            },
        ),
        # Add indexes after table creation for better performance
        migrations.RunSQL(
            "CREATE INDEX idx_category_active_created ON products_category(is_active, created_at);",
            reverse_sql="DROP INDEX idx_category_active_created ON products_category;"
        ),
    ]
```

#### Hands-on Exercise 1.2
```python
# Practice: Design optimized models
# 1. Create models with appropriate indexes
# 2. Write efficient migrations
# 3. Test model relationships
# 4. Verify index creation in MySQL

# Test model performance
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from .models import Product, Category

class ModelPerformanceTest(TestCase):
    def test_query_performance(self):
        # Create test data
        category = Category.objects.create(name="Electronics", slug="electronics")
        for i in range(1000):
            Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                category=category,
                price=10.00 + i,
                description="Test product"
            )
        
        # Test query performance
        with self.assertNumQueries(1):
            products = list(Product.objects.filter(
                category=category,
                is_active=True,
                price__gte=100
            )[:10])
        
        # Verify index usage
        with connection.cursor() as cursor:
            cursor.execute("EXPLAIN SELECT * FROM products_product WHERE category_id = %s AND is_active = 1 AND price >= 100 LIMIT 10", [category.id])
            explain_result = cursor.fetchall()
            self.assertIn('index', str(explain_result).lower())
```

## Module 2: Query Optimization

### 2.1 Django ORM Best Practices

#### Efficient QuerySets
```python
# Efficient query patterns

# Good: Use select_related for foreign keys
products = Product.objects.select_related('category').filter(is_active=True)

# Good: Use prefetch_related for reverse foreign keys and many-to-many
orders = Order.objects.prefetch_related('items__product').filter(user=user)

# Good: Use only() to limit fields
products = Product.objects.only('name', 'price', 'category_id').filter(is_active=True)

# Good: Use values() for specific fields
product_prices = Product.objects.values('name', 'price').filter(category_id=1)

# Good: Use exists() instead of len() or count() for boolean checks
has_orders = Order.objects.filter(user=user).exists()

# Good: Use bulk operations for multiple inserts/updates
Product.objects.bulk_create([
    Product(name=f"Product {i}", category=category, price=10.00)
    for i in range(100)
])

# Good: Use iterator() for large datasets
for product in Product.objects.filter(is_active=True).iterator():
    process_product(product)
```

#### Query Optimization Examples
```python
# views.py - Optimized views

from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, Count, Avg, Q
from django.core.paginator import Paginator
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class ProductListView(ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category').filter(is_active=True)
        
        # Filter by category if provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Order by
        order_by = self.request.GET.get('order_by', '-created_at')
        if order_by in ['name', '-name', 'price', '-price', 'created_at', '-created_at']:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add categories for filter dropdown
        context['categories'] = Category.objects.filter(is_active=True).only('name', 'slug')
        
        # Add search parameters to context for form persistence
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')
        
        return context

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.select_related('category').filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related products efficiently
        context['related_products'] = Product.objects.filter(
            category=self.object.category,
            is_active=True
        ).exclude(id=self.object.id).only('name', 'price', 'slug')[:4]
        
        return context

# API views with optimized queries
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend

class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Product.objects.select_related('category').filter(is_active=True)
```

#### Hands-on Exercise 2.1
```python
# Practice: Write optimized queries
# 1. Create efficient QuerySets
# 2. Use select_related and prefetch_related appropriately
# 3. Implement search and filtering
# 4. Measure query performance

# Performance testing utility
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection, reset_queries

class QueryPerformanceTest(TestCase):
    def setUp(self):
        # Create test data
        self.category = Category.objects.create(name="Test Category", slug="test")
        for i in range(100):
            Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                category=self.category,
                price=10.00 + i,
                description="Test product"
            )
    
    def test_query_count(self):
        reset_queries()
        
        # Test efficient query
        products = Product.objects.select_related('category').filter(is_active=True)[:10]
        list(products)  # Force evaluation
        
        query_count = len(connection.queries)
        self.assertEqual(query_count, 1, f"Expected 1 query, got {query_count}")
    
    def test_n_plus_one_problem(self):
        reset_queries()
        
        # Bad: N+1 queries
        products = Product.objects.filter(is_active=True)[:5]
        for product in products:
            print(product.category.name)  # This causes additional queries
        
        bad_query_count = len(connection.queries)
        
        reset_queries()
        
        # Good: Single query with select_related
        products = Product.objects.select_related('category').filter(is_active=True)[:5]
        for product in products:
            print(product.category.name)  # No additional queries
        
        good_query_count = len(connection.queries)
        
        self.assertLess(good_query_count, bad_query_count)
```

### 2.2 Raw SQL and Custom Queries

#### When to Use Raw SQL
```python
# Complex aggregations that are difficult with ORM
from django.db import connection

def get_sales_report(start_date, end_date):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                c.name as category_name,
                COUNT(oi.id) as items_sold,
                SUM(oi.quantity * oi.price) as total_revenue,
                AVG(oi.price) as avg_price
            FROM orders_orderitem oi
            JOIN products_product p ON oi.product_id = p.id
            JOIN products_category c ON p.category_id = c.id
            JOIN orders_order o ON oi.order_id = o.id
            WHERE o.created_at BETWEEN %s AND %s
            AND o.status = 'delivered'
            GROUP BY c.id, c.name
            ORDER BY total_revenue DESC
        """, [start_date, end_date])
        
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Using raw() method for complex queries
def get_top_selling_products(limit=10):
    return Product.objects.raw("""
        SELECT p.*, 
               COALESCE(SUM(oi.quantity), 0) as total_sold
        FROM products_product p
        LEFT JOIN orders_orderitem oi ON p.id = oi.product_id
        LEFT JOIN orders_order o ON oi.order_id = o.id
        WHERE p.is_active = 1
        AND (o.status = 'delivered' OR o.status IS NULL)
        GROUP BY p.id
        ORDER BY total_sold DESC
        LIMIT %s
    """, [limit])

# Custom manager with optimized queries
class ProductManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)
    
    def by_category(self, category_slug):
        return self.select_related('category').filter(
            category__slug=category_slug,
            is_active=True
        )
    
    def search(self, query):
        return self.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query),
            is_active=True
        ).select_related('category')
    
    def with_stock(self):
        return self.filter(stock_quantity__gt=0, is_active=True)

# Add to Product model
class Product(models.Model):
    # ... existing fields ...
    
    objects = ProductManager()
    
    # Custom methods
    def get_related_products(self, limit=4):
        return Product.objects.filter(
            category=self.category,
            is_active=True
        ).exclude(id=self.id)[:limit]
```

#### Hands-on Exercise 2.2
```python
# Practice: Write custom queries
# 1. Create complex aggregation queries
# 2. Use raw SQL when appropriate
# 3. Implement custom managers
# 4. Test query performance

# Example: Sales analytics
def test_sales_analytics():
    # Create test data
    category = Category.objects.create(name="Electronics", slug="electronics")
    product = Product.objects.create(
        name="Laptop",
        slug="laptop",
        category=category,
        price=1000.00
    )
    
    user = User.objects.create_user(username="testuser", password="testpass")
    order = Order.objects.create(user=user, total_amount=1000.00, status='delivered')
    OrderItem.objects.create(order=order, product=product, quantity=1, price=1000.00)
    
    # Test sales report
    report = get_sales_report(
        start_date=timezone.now() - timedelta(days=30),
        end_date=timezone.now()
    )
    
    assert len(report) > 0
    assert report[0]['category_name'] == 'Electronics'
    assert report[0]['total_revenue'] == 1000.00
```

## Module 3: Performance Optimization

### 3.1 Database Connection Management

#### Connection Pooling Configuration
```python
# settings/production.py

# Connection pooling settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
        },
        # Connection pooling
        'CONN_MAX_AGE': 3600,  # Keep connections alive for 1 hour
        'CONN_HEALTH_CHECKS': True,  # Enable connection health checks
    }
}

# Custom database backend for connection pooling (if needed)
# You can also use django-db-pool or similar packages
```

#### Connection Monitoring
```python
# utils/db_monitor.py

from django.db import connections
from django.core.management.base import BaseCommand
import time

class Command(BaseCommand):
    help = 'Monitor database connections'
    
    def handle(self, *args, **options):
        while True:
            for alias in connections:
                connection = connections[alias]
                
                # Check connection status
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        status = "Connected"
                except Exception as e:
                    status = f"Error: {e}"
                
                # Get connection info
                queries_count = len(connection.queries)
                
                self.stdout.write(
                    f"Database: {alias}, Status: {status}, Queries: {queries_count}"
                )
            
            time.sleep(30)  # Check every 30 seconds
```

#### Hands-on Exercise 3.1
```python
# Practice: Optimize database connections
# 1. Configure connection pooling
# 2. Monitor connection usage
# 3. Test connection health checks
# 4. Implement connection retry logic

# Connection testing utility
from django.test import TestCase
from django.db import connections, connection
from django.core.management import call_command

class ConnectionTest(TestCase):
    def test_connection_pooling(self):
        # Test that connections are reused
        conn1 = connection
        conn2 = connection
        self.assertEqual(id(conn1), id(conn2))
    
    def test_connection_health(self):
        # Test connection health check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
```

### 3.2 Caching Strategies

#### Django Caching Configuration
```python
# settings/production.py

# Redis cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'ecommerce',
        'TIMEOUT': 300,  # 5 minutes default
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'sessions',
    }
}

# Use Redis for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

# Cache middleware
MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    # ... other middleware ...
    'django.middleware.cache.FetchFromCacheMiddleware',
]

# Cache settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'ecommerce'
```

#### Caching Implementation
```python
# utils/cache.py

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from functools import wraps
import hashlib

def cache_result(timeout=300, key_prefix=''):
    """
    Decorator to cache function results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            
            cache_key = hashlib.md5(':'.join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

# Cached model methods
class Product(models.Model):
    # ... existing fields ...
    
    @cache_result(timeout=600, key_prefix='product_related')
    def get_related_products(self, limit=4):
        return list(Product.objects.filter(
            category=self.category,
            is_active=True
        ).exclude(id=self.id).only('id', 'name', 'slug', 'price')[:limit])
    
    @cache_result(timeout=300, key_prefix='product_reviews')
    def get_review_summary(self):
        from django.db.models import Avg, Count
        return self.reviews.aggregate(
            avg_rating=Avg('rating'),
            review_count=Count('id')
        )

# Cached views
@method_decorator(cache_page(60 * 15), name='dispatch')
class CategoryListView(ListView):
    model = Category
    template_name = 'categories/list.html'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).only('name', 'slug')

# Cache invalidation
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    # Invalidate related product caches
    cache_keys = [
        f'product_related:{instance.category_id}:*',
        f'category_products:{instance.category.slug}',
    ]
    
    for pattern in cache_keys:
        cache.delete_many(cache.keys(pattern))
```

#### Hands-on Exercise 3.2
```python
# Practice: Implement caching strategies
# 1. Configure Redis caching
# 2. Cache expensive queries
# 3. Implement cache invalidation
# 4. Monitor cache hit rates

# Cache testing
from django.test import TestCase
from django.core.cache import cache
from django.test.utils import override_settings

class CacheTest(TestCase):
    def setUp(self):
        cache.clear()
    
    def test_query_caching(self):
        # Test that expensive queries are cached
        category = Category.objects.create(name="Test", slug="test")
        
        # First call should hit database
        with self.assertNumQueries(1):
            products = get_category_products(category.slug)
        
        # Second call should use cache
        with self.assertNumQueries(0):
            cached_products = get_category_products(category.slug)
        
        self.assertEqual(products, cached_products)
    
    def test_cache_invalidation(self):
        category = Category.objects.create(name="Test", slug="test")
        
        # Cache the result
        products = get_category_products(category.slug)
        
        # Modify data
        Product.objects.create(
            name="New Product",
            slug="new-product",
            category=category,
            price=10.00
        )
        
        # Cache should be invalidated
        new_products = get_category_products(category.slug)
        self.assertNotEqual(len(products), len(new_products))
```

## Module 4: Error Handling and Debugging

### 4.1 Database Error Handling

#### Common Database Errors
```python
# utils/db_exceptions.py

from django.db import IntegrityError, OperationalError, DatabaseError
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class DatabaseErrorHandler:
    @staticmethod
    def handle_integrity_error(e, operation="database operation"):
        """Handle database integrity errors"""
        error_msg = str(e).lower()
        
        if 'duplicate entry' in error_msg:
            logger.warning(f"Duplicate entry error during {operation}: {e}")
            return "This record already exists."
        elif 'foreign key constraint' in error_msg:
            logger.warning(f"Foreign key constraint error during {operation}: {e}")
            return "Referenced record does not exist."
        else:
            logger.error(f"Integrity error during {operation}: {e}")
            return "Data integrity error occurred."
    
    @staticmethod
    def handle_operational_error(e, operation="database operation"):
        """Handle database operational errors"""
        error_msg = str(e).lower()
        
        if 'mysql server has gone away' in error_msg:
            logger.error(f"MySQL connection lost during {operation}: {e}")
            return "Database connection lost. Please try again."
        elif 'lock wait timeout' in error_msg:
            logger.warning(f"Lock timeout during {operation}: {e}")
            return "Operation timed out. Please try again."
        else:
            logger.error(f"Operational error during {operation}: {e}")
            return "Database operation failed."

# Error handling in views
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction

def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    product = form.save()
                    messages.success(request, 'Product created successfully.')
                    return redirect('product_detail', slug=product.slug)
            except IntegrityError as e:
                error_msg = DatabaseErrorHandler.handle_integrity_error(e, "product creation")
                messages.error(request, error_msg)
            except OperationalError as e:
                error_msg = DatabaseErrorHandler.handle_operational_error(e, "product creation")
                messages.error(request, error_msg)
            except Exception as e:
                logger.error(f"Unexpected error creating product: {e}")
                messages.error(request, "An unexpected error occurred.")
    else:
        form = ProductForm()
    
    return render(request, 'products/create.html', {'form': form})

# Retry decorator for database operations
import time
from functools import wraps

def retry_db_operation(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Database operation failed (attempt {attempt + 1}): {e}")
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

@retry_db_operation(max_retries=3)
def get_product_with_retry(product_id):
    return Product.objects.get(id=product_id)
```

#### Hands-on Exercise 4.1
```python
# Practice: Implement error handling
# 1. Handle common database errors
# 2. Implement retry logic
# 3. Add proper logging
# 4. Test error scenarios

# Error handling tests
from django.test import TestCase
from django.db import IntegrityError

class ErrorHandlingTest(TestCase):
    def test_duplicate_entry_handling(self):
        # Create initial product
        Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            price=10.00
        )
        
        # Try to create duplicate
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="Another Product",
                slug="test-product",  # Duplicate slug
                category=self.category,
                price=20.00
            )
    
    def test_foreign_key_constraint(self):
        # Try to create product with non-existent category
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="Test Product",
                slug="test-product",
                category_id=999,  # Non-existent category
                price=10.00
            )
```

### 4.2 Query Debugging and Profiling

#### Django Debug Toolbar Integration
```python
# settings/development.py

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    
    # Debug toolbar configuration
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'SHOW_COLLAPSED': True,
    }
    
    # Show SQL queries in console
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }
```

#### Custom Query Profiling
```python
# utils/profiling.py

from django.db import connection, reset_queries
from django.conf import settings
import time
from functools import wraps

def profile_queries(func):
    """Decorator to profile database queries"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        reset_queries()
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        query_count = len(connection.queries)
        total_time = sum(float(q['time']) for q in connection.queries)
        
        print(f"\n=== Query Profile for {func.__name__} ===")
        print(f"Execution time: {end_time - start_time:.4f}s")
        print(f"Query count: {query_count}")
        print(f"Query time: {total_time:.4f}s")
        
        if query_count > 10:
            print("⚠️  High query count detected!")
        
        # Show slowest queries
        slow_queries = sorted(connection.queries, key=lambda x: float(x['time']), reverse=True)[:3]
        for i, query in enumerate(slow_queries, 1):
            print(f"\nSlow Query #{i} ({query['time']}s):")
            print(query['sql'][:200] + "..." if len(query['sql']) > 200 else query['sql'])
        
        return result
    return wrapper

# Usage in views
@profile_queries
def product_list_view(request):
    products = Product.objects.select_related('category').filter(is_active=True)
    return render(request, 'products/list.html', {'products': products})

# Query analysis utility
class QueryAnalyzer:
    @staticmethod
    def analyze_queryset(queryset, description="QuerySet"):
        """Analyze a queryset for potential issues"""
        print(f"\n=== Analyzing {description} ===")
        
        # Show the SQL query
        print(f"SQL: {queryset.query}")
        
        # Check for potential N+1 problems
        if hasattr(queryset, 'select_related_fields'):
            if not queryset.select_related_fields:
                print("⚠️  Consider using select_related() for foreign keys")
        
        if hasattr(queryset, 'prefetch_related_lookups'):
            if not queryset.prefetch_related_lookups:
                print("⚠️  Consider using prefetch_related() for reverse foreign keys")
        
        # Estimate query cost
        count = queryset.count()
        print(f"Result count: {count}")
        
        if count > 1000:
            print("⚠️  Large result set - consider pagination")

# Example usage
def debug_product_queries():
    # Analyze different query patterns
    QueryAnalyzer.analyze_queryset(
        Product.objects.filter(is_active=True),
        "Basic product query"
    )
    
    QueryAnalyzer.analyze_queryset(
        Product.objects.select_related('category').filter(is_active=True),
        "Optimized product query"
    )
```

#### Hands-on Exercise 4.2
```python
# Practice: Debug and profile queries
# 1. Set up Django Debug Toolbar
# 2. Profile query performance
# 3. Identify N+1 query problems
# 4. Optimize slow queries

# Profiling tests
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection, reset_queries

class QueryProfilingTest(TestCase):
    def test_query_optimization(self):
        # Create test data
        category = Category.objects.create(name="Test", slug="test")
        for i in range(10):
            Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                category=category,
                price=10.00
            )
        
        # Test unoptimized query
        reset_queries()
        products = Product.objects.filter(is_active=True)
        for product in products:
            print(product.category.name)  # N+1 problem
        
        unoptimized_count = len(connection.queries)
        
        # Test optimized query
        reset_queries()
        products = Product.objects.select_related('category').filter(is_active=True)
        for product in products:
            print(product.category.name)  # Single query
        
        optimized_count = len(connection.queries)
        
        self.assertLess(optimized_count, unoptimized_count)
        self.assertEqual(optimized_count, 1)
```

## Module 5: Testing and Quality Assurance

### 5.1 Database Testing Strategies

#### Test Database Configuration
```python
# settings/test.py

# Use in-memory SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# For MySQL-specific testing
if os.getenv('TEST_WITH_MYSQL'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'test_ecommerce_db',
            'USER': 'test_user',
            'PASSWORD': 'test_password',
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {
                'charset': 'utf8mb4',
            },
            'TEST': {
                'CHARSET': 'utf8mb4',
                'COLLATION': 'utf8mb4_unicode_ci',
            }
        }
    }

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

if not os.getenv('TEST_WITH_MIGRATIONS'):
    MIGRATION_MODULES = DisableMigrations()
```

#### Model Testing
```python
# tests/test_models.py

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from products.models import Category, Product

class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )
    
    def test_product_creation(self):
        """Test basic product creation"""
        product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            description="Test description",
            category=self.category,
            price=Decimal('99.99'),
            stock_quantity=10
        )
        
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.price, Decimal('99.99'))
        self.assertTrue(product.is_active)
    
    def test_product_slug_uniqueness(self):
        """Test that product slugs must be unique"""
        Product.objects.create(
            name="Product 1",
            slug="test-product",
            category=self.category,
            price=Decimal('10.00')
        )
        
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="Product 2",
                slug="test-product",  # Duplicate slug
                category=self.category,
                price=Decimal('20.00')
            )
    
    def test_product_price_validation(self):
        """Test product price validation"""
        with self.assertRaises(ValidationError):
            product = Product(
                name="Invalid Product",
                slug="invalid-product",
                category=self.category,
                price=Decimal('-10.00')  # Negative price
            )
            product.full_clean()
    
    def test_product_str_method(self):
        """Test product string representation"""
        product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            price=Decimal('99.99')
        )
        
        self.assertEqual(str(product), "Test Product")
    
    def test_product_manager_methods(self):
        """Test custom manager methods"""
        # Create test products
        active_product = Product.objects.create(
            name="Active Product",
            slug="active-product",
            category=self.category,
            price=Decimal('10.00'),
            is_active=True
        )
        
        inactive_product = Product.objects.create(
            name="Inactive Product",
            slug="inactive-product",
            category=self.category,
            price=Decimal('20.00'),
            is_active=False
        )
        
        # Test active() method
        active_products = Product.objects.active()
        self.assertIn(active_product, active_products)
        self.assertNotIn(inactive_product, active_products)
        
        # Test by_category() method
        category_products = Product.objects.by_category(self.category.slug)
        self.assertIn(active_product, category_products)
        self.assertNotIn(inactive_product, category_products)
```

#### API Testing
```python
# tests/test_api.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from products.models import Category, Product

class ProductAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            category=self.category,
            price=99.99,
            description="Test description"
        )
    
    def test_product_list_api(self):
        """Test product list API endpoint"""
        url = '/api/products/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Product')
    
    def test_product_detail_api(self):
        """Test product detail API endpoint"""
        url = f'/api/products/{self.product.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product')
        self.assertEqual(response.data['category']['name'], 'Electronics')
    
    def test_product_filtering(self):
        """Test product filtering"""
        # Create another category and product
        other_category = Category.objects.create(
            name="Books",
            slug="books"
        )
        Product.objects.create(
            name="Test Book",
            slug="test-book",
            category=other_category,
            price=19.99
        )
        
        # Filter by category
        url = '/api/products/?category=electronics'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['category']['slug'], 'electronics')
    
    def test_product_search(self):
        """Test product search functionality"""
        url = '/api/products/?search=Test'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Product')
```

#### Hands-on Exercise 5.1
```python
# Practice: Write comprehensive tests
# 1. Create model tests with edge cases
# 2. Test API endpoints thoroughly
# 3. Test database constraints
# 4. Implement performance tests

# Performance testing example
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection, reset_queries
import time

class PerformanceTest(TestCase):
    def test_query_performance(self):
        """Test that queries perform within acceptable limits"""
        # Create test data
        category = Category.objects.create(name="Test", slug="test")
        for i in range(100):
            Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}",
                category=category,
                price=10.00 + i
            )
        
        # Test query performance
        reset_queries()
        start_time = time.time()
        
        products = list(Product.objects.select_related('category').filter(
            is_active=True,
            price__gte=50
        )[:20])
        
        end_time = time.time()
        query_count = len(connection.queries)
        execution_time = end_time - start_time
        
        # Assertions
        self.assertLessEqual(query_count, 1, "Should use only 1 query")
        self.assertLessEqual(execution_time, 0.1, "Query should complete in under 100ms")
        self.assertEqual(len(products), 20, "Should return 20 products")
```

## Assessment and Practical Exercises

### Final Project: E-commerce Product Catalog

#### Project Requirements
Create a complete product catalog system with the following features:

1. **Models and Database Design**
   - Category hierarchy with nested categories
   - Product variants (size, color, etc.)
   - Inventory tracking
   - Product reviews and ratings

2. **API Development**
   - RESTful API for products and categories
   - Search and filtering capabilities
   - Pagination and sorting
   - Rate limiting and authentication

3. **Performance Optimization**
   - Efficient database queries
   - Caching implementation
   - Database indexing strategy
   - Query optimization

4. **Testing and Quality Assurance**
   - Comprehensive test suite
   - Performance benchmarks
   - Error handling
   - Documentation

#### Implementation Example
```python
# Final project structure
ecommerce_catalog/
├── models/
│   ├── __init__.py
│   ├── category.py
│   ├── product.py
│   ├── variant.py
│   └── review.py
├── serializers/
│   ├── __init__.py
│   ├── category.py
│   ├── product.py
│   └── review.py
├── views/
│   ├── __init__.py
│   ├── category.py
│   ├── product.py
│   └── search.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_api.py
│   └── test_performance.py
└── utils/
    ├── __init__.py
    ├── cache.py
    ├── search.py
    └── pagination.py
```

This comprehensive developer training guide provides the knowledge and practical skills needed to effectively work with MySQL databases in Django applications, focusing on performance, reliability, and best practices.