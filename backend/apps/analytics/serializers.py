"""
Analytics serializers for API responses.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    DailySalesReport, ProductPerformanceReport, CustomerAnalytics,
    InventoryReport, SystemMetrics, ReportExport
)

User = get_user_model()


class DailySalesReportSerializer(serializers.ModelSerializer):
    """
    Serializer for daily sales reports.
    """
    class Meta:
        model = DailySalesReport
        fields = [
            'id', 'date', 'total_orders', 'total_revenue', 'total_profit',
            'total_discount', 'total_tax', 'total_shipping', 'pending_orders',
            'confirmed_orders', 'shipped_orders', 'delivered_orders',
            'cancelled_orders', 'returned_orders', 'new_customers',
            'returning_customers', 'total_products_sold', 'unique_products_sold',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductPerformanceReportSerializer(serializers.ModelSerializer):
    """
    Serializer for product performance reports.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    category_name = serializers.CharField(source='product.category.name', read_only=True)

    class Meta:
        model = ProductPerformanceReport
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'category_name',
            'date', 'units_sold', 'revenue', 'profit', 'page_views',
            'unique_visitors', 'add_to_cart_count', 'wishlist_count',
            'conversion_rate', 'cart_abandonment_rate', 'new_reviews',
            'average_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'product_name', 'product_sku', 'category_name', 'created_at', 'updated_at']


class CustomerAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for customer analytics.
    """
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomerAnalytics
        fields = [
            'id', 'customer', 'customer_email', 'customer_name', 'total_orders',
            'total_spent', 'average_order_value', 'last_order_date',
            'total_sessions', 'total_page_views', 'average_session_duration',
            'last_activity_date', 'favorite_categories', 'favorite_brands',
            'lifecycle_stage', 'customer_segment', 'lifetime_value',
            'predicted_churn_probability', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'customer_email', 'customer_name', 'created_at', 'updated_at']

    def get_customer_name(self, obj):
        """Get customer full name."""
        user = obj.customer.user
        if user.first_name or user.last_name:
            return f"{user.first_name} {user.last_name}".strip()
        return user.email


class InventoryReportSerializer(serializers.ModelSerializer):
    """
    Serializer for inventory reports.
    """
    class Meta:
        model = InventoryReport
        fields = [
            'id', 'date', 'total_products', 'in_stock_products',
            'low_stock_products', 'out_of_stock_products', 'total_inventory_value',
            'total_cost_value', 'total_stock_in', 'total_stock_out',
            'total_adjustments', 'inventory_turnover_rate', 'dead_stock_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SystemMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for system metrics.
    """
    class Meta:
        model = SystemMetrics
        fields = [
            'id', 'timestamp', 'response_time_avg', 'response_time_95th',
            'requests_per_minute', 'error_rate', 'total_errors',
            'db_connections', 'db_query_time_avg', 'memory_usage_percent',
            'cpu_usage_percent', 'active_users', 'concurrent_sessions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReportExportSerializer(serializers.ModelSerializer):
    """
    Serializer for report exports.
    """
    exported_by_email = serializers.CharField(source='exported_by.email', read_only=True)
    file_size_human = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ReportExport
        fields = [
            'id', 'report_type', 'export_format', 'file_path', 'file_size',
            'file_size_human', 'date_from', 'date_to', 'filters',
            'exported_by', 'exported_by_email', 'export_status',
            'download_count', 'expires_at', 'is_expired',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_path', 'file_size', 'file_size_human', 'exported_by',
            'exported_by_email', 'export_status', 'download_count', 'is_expired',
            'created_at', 'updated_at'
        ]


class DashboardMetricsSerializer(serializers.Serializer):
    """
    Serializer for dashboard metrics response.
    """
    sales = serializers.DictField()
    customers = serializers.DictField()
    inventory = serializers.DictField()
    orders_by_status = serializers.DictField()
    period = serializers.DictField()


class SalesReportSerializer(serializers.Serializer):
    """
    Serializer for sales report response.
    """
    summary = serializers.DictField()
    daily_breakdown = serializers.ListField()
    top_products = serializers.ListField()
    payment_methods = serializers.ListField()
    filters_applied = serializers.DictField()
    period = serializers.DictField()


class ProfitLossReportSerializer(serializers.Serializer):
    """
    Serializer for profit and loss report response.
    """
    revenue = serializers.DictField()
    costs = serializers.DictField()
    profit = serializers.DictField()
    period = serializers.DictField()


class TopSellingProductSerializer(serializers.Serializer):
    """
    Serializer for top-selling products.
    """
    product__id = serializers.IntegerField()
    product__name = serializers.CharField()
    product__sku = serializers.CharField()
    product__price = serializers.DecimalField(max_digits=10, decimal_places=2)
    product__category__name = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    order_count = serializers.IntegerField()


class CustomerAnalyticsSummarySerializer(serializers.Serializer):
    """
    Serializer for customer analytics summary.
    """
    lifecycle_distribution = serializers.ListField()
    top_customers = serializers.ListField()
    segments = serializers.ListField()


class StockMaintenanceReportSerializer(serializers.Serializer):
    """
    Serializer for stock maintenance report.
    """
    low_stock = serializers.ListField()
    out_of_stock = serializers.ListField()
    overstock = serializers.ListField()
    dead_stock = serializers.ListField()
    summary = serializers.DictField()


class SystemHealthSummarySerializer(serializers.Serializer):
    """
    Serializer for system health summary.
    """
    period_summary = serializers.DictField()
    current_metrics = serializers.DictField()
    health_status = serializers.CharField()


class ReportExportRequestSerializer(serializers.Serializer):
    """
    Serializer for report export requests.
    """
    report_type = serializers.ChoiceField(choices=ReportExport.REPORT_TYPES)
    export_format = serializers.ChoiceField(choices=ReportExport.EXPORT_FORMATS)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    filters = serializers.JSONField(required=False, default=dict)

    def validate(self, data):
        """Validate date range."""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("date_from must be before date_to")
        
        return data


class ReportFilterSerializer(serializers.Serializer):
    """
    Serializer for report filtering parameters.
    """
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    category = serializers.IntegerField(required=False)
    product = serializers.IntegerField(required=False)
    customer_segment = serializers.CharField(required=False)
    order_status = serializers.CharField(required=False)
    payment_method = serializers.CharField(required=False)

    def validate(self, data):
        """Validate date range."""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("date_from must be before date_to")
        
        return data