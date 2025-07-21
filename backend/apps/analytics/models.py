"""
Analytics and reporting models for comprehensive business intelligence.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from decimal import Decimal
from core.models import BaseModel

User = get_user_model()


class DailySalesReport(BaseModel):
    """
    Daily aggregated sales data for reporting and analytics.
    """
    date = models.DateField(unique=True)
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Order status breakdown
    pending_orders = models.PositiveIntegerField(default=0)
    confirmed_orders = models.PositiveIntegerField(default=0)
    shipped_orders = models.PositiveIntegerField(default=0)
    delivered_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)
    returned_orders = models.PositiveIntegerField(default=0)
    
    # Customer metrics
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    
    # Product metrics
    total_products_sold = models.PositiveIntegerField(default=0)
    unique_products_sold = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"Sales Report - {self.date}"

    @classmethod
    def generate_report(cls, date):
        """Generate daily sales report for a specific date."""
        from apps.orders.models import Order
        from apps.customers.models import Customer
        
        # Get orders for the date
        orders = Order.objects.filter(
            created_at__date=date,
            is_deleted=False
        )
        
        # Calculate metrics
        total_orders = orders.count()
        revenue_data = orders.aggregate(
            total_revenue=Sum('total_amount'),
            total_discount=Sum('discount_amount'),
            total_tax=Sum('tax_amount'),
            total_shipping=Sum('shipping_amount')
        )
        
        # Order status breakdown
        status_counts = {}
        for status, _ in Order.ORDER_STATUS_CHOICES:
            status_counts[f"{status.lower()}_orders"] = orders.filter(status=status).count()
        
        # Customer metrics
        order_user_ids = orders.values_list('user_id', flat=True).distinct()
        new_customers = Customer.objects.filter(
            user__date_joined__date=date,
            user_id__in=order_user_ids
        ).count()
        returning_customers = len(order_user_ids) - new_customers
        
        # Product metrics
        from apps.orders.models import OrderItem
        order_items = OrderItem.objects.filter(order__in=orders)
        total_products_sold = order_items.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        unique_products_sold = order_items.values('product').distinct().count()
        
        # Calculate profit (simplified - revenue minus cost)
        total_profit = Decimal('0')
        for item in order_items:
            if hasattr(item.product, 'inventory') and item.product.inventory.cost_price:
                item_profit = (item.unit_price - item.product.inventory.cost_price) * item.quantity
                total_profit += item_profit
        
        # Create or update report
        report, created = cls.objects.get_or_create(
            date=date,
            defaults={
                'total_orders': total_orders,
                'total_revenue': revenue_data['total_revenue'] or 0,
                'total_profit': total_profit,
                'total_discount': revenue_data['total_discount'] or 0,
                'total_tax': revenue_data['total_tax'] or 0,
                'total_shipping': revenue_data['total_shipping'] or 0,
                'new_customers': new_customers,
                'returning_customers': returning_customers,
                'total_products_sold': total_products_sold,
                'unique_products_sold': unique_products_sold,
                **status_counts
            }
        )
        
        if not created:
            # Update existing report
            for field, value in {
                'total_orders': total_orders,
                'total_revenue': revenue_data['total_revenue'] or 0,
                'total_profit': total_profit,
                'total_discount': revenue_data['total_discount'] or 0,
                'total_tax': revenue_data['total_tax'] or 0,
                'total_shipping': revenue_data['total_shipping'] or 0,
                'new_customers': new_customers,
                'returning_customers': returning_customers,
                'total_products_sold': total_products_sold,
                'unique_products_sold': unique_products_sold,
                **status_counts
            }.items():
                setattr(report, field, value)
            report.save()
        
        return report


class ProductPerformanceReport(BaseModel):
    """
    Product performance analytics and reporting.
    """
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='performance_reports'
    )
    date = models.DateField()
    
    # Sales metrics
    units_sold = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Engagement metrics
    page_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    add_to_cart_count = models.PositiveIntegerField(default=0)
    wishlist_count = models.PositiveIntegerField(default=0)
    
    # Conversion metrics
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cart_abandonment_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Review metrics
    new_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    class Meta:
        unique_together = ['product', 'date']
        ordering = ['-date', '-revenue']
        indexes = [
            models.Index(fields=['product', 'date']),
            models.Index(fields=['date', '-revenue']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.date}"


class CustomerAnalytics(BaseModel):
    """
    Customer behavior and analytics data.
    """
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    
    # Purchase behavior
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_order_date = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    total_sessions = models.PositiveIntegerField(default=0)
    total_page_views = models.PositiveIntegerField(default=0)
    average_session_duration = models.DurationField(null=True, blank=True)
    last_activity_date = models.DateTimeField(null=True, blank=True)
    
    # Preferences
    favorite_categories = models.JSONField(default=list, blank=True)
    favorite_brands = models.JSONField(default=list, blank=True)
    
    # Lifecycle stage
    LIFECYCLE_STAGES = [
        ('new', 'New Customer'),
        ('active', 'Active Customer'),
        ('at_risk', 'At Risk'),
        ('dormant', 'Dormant'),
        ('churned', 'Churned'),
        ('vip', 'VIP Customer'),
    ]
    lifecycle_stage = models.CharField(max_length=20, choices=LIFECYCLE_STAGES, default='new')
    
    # Segmentation
    customer_segment = models.CharField(max_length=50, blank=True)
    lifetime_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    predicted_churn_probability = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=['lifecycle_stage']),
            models.Index(fields=['customer_segment']),
            models.Index(fields=['lifetime_value']),
        ]

    def __str__(self):
        return f"Analytics - {self.customer.user.email}"

    def update_analytics(self):
        """Update customer analytics based on current data."""
        from apps.orders.models import Order
        from django.db.models import Sum, Avg, Count
        
        orders = Order.objects.filter(
            user=self.customer.user,
            is_deleted=False
        ).exclude(status='cancelled')
        
        if orders.exists():
            order_stats = orders.aggregate(
                total_orders=Count('id'),
                total_spent=Sum('total_amount'),
                avg_order_value=Avg('total_amount')
            )
            
            self.total_orders = order_stats['total_orders'] or 0
            self.total_spent = order_stats['total_spent'] or 0
            self.average_order_value = order_stats['avg_order_value'] or 0
            self.last_order_date = orders.latest('created_at').created_at
            self.lifetime_value = self.total_spent
            
            # Update lifecycle stage based on behavior
            self._update_lifecycle_stage()
        
        self.save()

    def _update_lifecycle_stage(self):
        """Update customer lifecycle stage based on behavior."""
        days_since_last_order = None
        if self.last_order_date:
            days_since_last_order = (timezone.now() - self.last_order_date).days
        
        if self.total_orders == 0:
            self.lifecycle_stage = 'new'
        elif self.total_spent >= 10000:  # VIP threshold
            self.lifecycle_stage = 'vip'
        elif days_since_last_order and days_since_last_order > 180:
            self.lifecycle_stage = 'churned'
        elif days_since_last_order and days_since_last_order > 90:
            self.lifecycle_stage = 'dormant'
        elif days_since_last_order and days_since_last_order > 60:
            self.lifecycle_stage = 'at_risk'
        else:
            self.lifecycle_stage = 'active'


class InventoryReport(BaseModel):
    """
    Inventory analytics and stock maintenance reporting.
    """
    date = models.DateField()
    
    # Stock levels
    total_products = models.PositiveIntegerField(default=0)
    in_stock_products = models.PositiveIntegerField(default=0)
    low_stock_products = models.PositiveIntegerField(default=0)
    out_of_stock_products = models.PositiveIntegerField(default=0)
    
    # Inventory value
    total_inventory_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Movement metrics
    total_stock_in = models.PositiveIntegerField(default=0)
    total_stock_out = models.PositiveIntegerField(default=0)
    total_adjustments = models.IntegerField(default=0)
    
    # Performance metrics
    inventory_turnover_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    dead_stock_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ['date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"Inventory Report - {self.date}"

    @classmethod
    def generate_report(cls, date):
        """Generate inventory report for a specific date."""
        from apps.inventory.models import Inventory, InventoryTransaction
        from apps.products.models import Product
        
        # Get all active products
        products = Product.objects.filter(is_active=True, is_deleted=False)
        total_products = products.count()
        
        # Stock level analysis
        inventories = Inventory.objects.filter(product__in=products)
        in_stock = inventories.filter(quantity__gt=0).count()
        low_stock = inventories.filter(
            quantity__lte=models.F('minimum_stock_level'),
            quantity__gt=0
        ).count()
        out_of_stock = inventories.filter(quantity=0).count()
        
        # Inventory value calculation
        inventory_value = inventories.aggregate(
            total_value=Sum(
                models.F('quantity') * models.F('product__price')
            ),
            total_cost=Sum(
                models.F('quantity') * models.F('cost_price')
            )
        )
        
        # Movement analysis for the date
        transactions = InventoryTransaction.objects.filter(
            created_at__date=date
        )
        
        stock_in = transactions.filter(
            transaction_type='IN'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        stock_out = transactions.filter(
            transaction_type='OUT'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        adjustments = transactions.filter(
            transaction_type='ADJUSTMENT'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Create or update report
        report, created = cls.objects.get_or_create(
            date=date,
            defaults={
                'total_products': total_products,
                'in_stock_products': in_stock,
                'low_stock_products': low_stock,
                'out_of_stock_products': out_of_stock,
                'total_inventory_value': inventory_value['total_value'] or 0,
                'total_cost_value': inventory_value['total_cost'] or 0,
                'total_stock_in': stock_in,
                'total_stock_out': stock_out,
                'total_adjustments': adjustments,
            }
        )
        
        return report


class SystemMetrics(BaseModel):
    """
    System performance and health metrics.
    """
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Performance metrics
    response_time_avg = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    response_time_95th = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    requests_per_minute = models.PositiveIntegerField(default=0)
    
    # Error metrics
    error_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_errors = models.PositiveIntegerField(default=0)
    
    # Database metrics
    db_connections = models.PositiveIntegerField(default=0)
    db_query_time_avg = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Memory and CPU
    memory_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cpu_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Business metrics
    active_users = models.PositiveIntegerField(default=0)
    concurrent_sessions = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"System Metrics - {self.timestamp}"


class ReportExport(BaseModel):
    """
    Track report exports and provide download links.
    """
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('customer', 'Customer Report'),
        ('product', 'Product Performance Report'),
        ('profit_loss', 'Profit & Loss Report'),
    ]

    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    file_path = models.CharField(max_length=500)
    file_size = models.PositiveIntegerField(default=0)  # in bytes
    
    # Parameters used for the report
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    
    # Export metadata
    exported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    export_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    download_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['exported_by', 'report_type']),
            models.Index(fields=['export_status']),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.get_export_format_display()}"

    def increment_download_count(self):
        """Increment download count."""
        self.download_count += 1
        self.save(update_fields=['download_count'])

    @property
    def is_expired(self):
        """Check if export has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def file_size_human(self):
        """Return human-readable file size."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"