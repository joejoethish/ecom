"""
Analytics admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    DailySalesReport, ProductPerformanceReport, CustomerAnalytics,
    InventoryReport, SystemMetrics, ReportExport
)

@admin.register(DailySalesReport)
class DailySalesReportAdmin(admin.ModelAdmin):
    """
    Admin interface for daily sales reports.
    """
    list_display = [
        'date', 'total_orders', 'total_revenue', 'total_profit',
        'new_customers', 'returning_customers', 'created_at'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    fieldsets = (
        ('Report Date', {
            'fields': ('date',)
        }),
        ('Sales Metrics', {
            'fields': (
                'total_orders', 'total_revenue', 'total_profit',
                'total_discount', 'total_tax', 'total_shipping'
            )
        }),
        ('Order Status', {
            'fields': (
                'pending_orders', 'confirmed_orders', 'shipped_orders',
                'delivered_orders', 'cancelled_orders', 'returned_orders'
            )
        }),
        ('Customer Metrics', {
            'fields': ('new_customers', 'returning_customers')
        }),
        ('Product Metrics', {
            'fields': ('total_products_sold', 'unique_products_sold')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProductPerformanceReport)
class ProductPerformanceReportAdmin(admin.ModelAdmin):
    """
    Admin interface for product performance reports.
    """
    list_display = [
        'product_name', 'date', 'units_sold', 'revenue',
        'profit', 'conversion_rate', 'average_rating'
    ]
    list_filter = ['date', 'product__category', 'created_at']
    search_fields = ['product__name', 'product__sku']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date', '-revenue']
    
    def product_name(self, obj):
        """Display product name."""
        return obj.product.name
    product_name.short_description = 'Product'
    
    fieldsets = (
        ('Product & Date', {
            'fields': ('product', 'date')
        }),
        ('Sales Metrics', {
            'fields': ('units_sold', 'revenue', 'profit')
        }),
        ('Engagement Metrics', {
            'fields': (
                'page_views', 'unique_visitors', 'add_to_cart_count',
                'wishlist_count', 'conversion_rate', 'cart_abandonment_rate'
            )
        }),
        ('Review Metrics', {
            'fields': ('new_reviews', 'average_rating')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(CustomerAnalytics)
class CustomerAnalyticsAdmin(admin.ModelAdmin):
    """
    Admin interface for customer analytics.
    """
    list_display = [
        'customer_email', 'total_orders', 'total_spent',
        'average_order_value', 'lifecycle_stage', 'customer_segment'
    ]
    list_filter = [
        'lifecycle_stage', 'customer_segment', 'last_order_date',
        'last_activity_date', 'created_at'
    ]
    search_fields = ['customer__user__email', 'customer__user__first_name', 'customer__user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-total_spent', '-total_orders']
    
    def customer_email(self, obj):
        """Display customer email."""
        return obj.customer.user.email
    customer_email.short_description = 'Customer Email'
    
    fieldsets = (
        ('Customer', {
            'fields': ('customer',)
        }),
        ('Order Metrics', {
            'fields': (
                'total_orders', 'total_spent', 'average_order_value',
                'last_order_date'
            )
        }),
        ('Activity Metrics', {
            'fields': (
                'total_sessions', 'total_page_views', 'average_session_duration',
                'last_activity_date'
            )
        }),
        ('Preferences', {
            'fields': ('favorite_categories', 'favorite_brands')
        }),
        ('Segmentation', {
            'fields': (
                'lifecycle_stage', 'customer_segment', 'lifetime_value',
                'predicted_churn_probability'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(InventoryReport)
class InventoryReportAdmin(admin.ModelAdmin):
    """
    Admin interface for inventory reports.
    """
    list_display = [
        'date', 'total_products', 'in_stock_products',
        'low_stock_products', 'out_of_stock_products',
        'total_inventory_value', 'inventory_turnover_rate'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    fieldsets = (
        ('Report Date', {
            'fields': ('date',)
        }),
        ('Stock Levels', {
            'fields': (
                'total_products', 'in_stock_products', 'low_stock_products',
                'out_of_stock_products'
            )
        }),
        ('Inventory Value', {
            'fields': ('total_inventory_value', 'total_cost_value', 'dead_stock_value')
        }),
        ('Stock Movement', {
            'fields': ('total_stock_in', 'total_stock_out', 'total_adjustments')
        }),
        ('Performance', {
            'fields': ('inventory_turnover_rate',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    """
    Admin interface for system metrics.
    """
    list_display = [
        'timestamp', 'response_time_avg', 'requests_per_minute',
        'error_rate', 'memory_usage_percent', 'cpu_usage_percent',
        'active_users'
    ]
    list_filter = ['timestamp', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
        ('Performance Metrics', {
            'fields': (
                'response_time_avg', 'response_time_95th', 'requests_per_minute',
                'error_rate', 'total_errors'
            )
        }),
        ('Database Metrics', {
            'fields': ('db_connections', 'db_query_time_avg')
        }),
        ('System Resources', {
            'fields': ('memory_usage_percent', 'cpu_usage_percent')
        }),
        ('User Activity', {
            'fields': ('active_users', 'concurrent_sessions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    """
    Admin interface for report exports.
    """
    list_display = [
        'report_type', 'export_format', 'exported_by_email',
        'export_status', 'file_size_human', 'download_count',
        'created_at'
    ]
    list_filter = [
        'report_type', 'export_format', 'export_status',
        'created_at', 'expires_at'
    ]
    search_fields = ['exported_by__email', 'report_type']
    readonly_fields = [
        'file_path', 'file_size', 'file_size_human', 'download_count',
        'is_expired', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    
    def exported_by_email(self, obj):
        """Display exported by email."""
        return obj.exported_by.email
    exported_by_email.short_description = 'Exported By'
    
    def download_link(self, obj):
        """Display download link if available."""
        if obj.export_status == 'completed' and not obj.is_expired:
            url = reverse('analytics:report-exports-download', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Download</a>', url)
        return '-'
    download_link.short_description = 'Download'
    
    fieldsets = (
        ('Export Details', {
            'fields': ('report_type', 'export_format', 'exported_by')
        }),
        ('Date Range', {
            'fields': ('date_from', 'date_to')
        }),
        ('Filters', {
            'fields': ('filters',)
        }),
        ('File Information', {
            'fields': (
                'file_path', 'file_size', 'file_size_human',
                'export_status', 'download_count'
            )
        }),
        ('Expiration', {
            'fields': ('expires_at', 'is_expired')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )