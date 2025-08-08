"""
Analytics admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    SalesMetrics, ProductSalesAnalytics, CustomerAnalytics,
    SalesForecast, SalesGoal, SalesCommission, SalesTerritory,
    SalesPipeline, SalesReport, SalesAnomalyDetection
)

@admin.register(SalesMetrics)
class SalesMetricsAdmin(admin.ModelAdmin):
    """
    Admin interface for sales metrics.
    """
    list_display = [
        'date', 'total_orders', 'total_revenue', 'net_profit',
        'new_customers', 'average_order_value', 'created_at'
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
                'total_orders', 'total_revenue', 'net_profit',
                'gross_margin', 'average_order_value', 'conversion_rate'
            )
        }),
        ('Customer Metrics', {
            'fields': ('total_customers', 'new_customers')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProductSalesAnalytics)
class ProductSalesAnalyticsAdmin(admin.ModelAdmin):
    """
    Admin interface for product sales analytics.
    """
    list_display = [
        'product_name', 'date', 'units_sold', 'revenue',
        'profit', 'profit_margin', 'category_name'
    ]
    list_filter = ['date', 'category_name', 'created_at']
    search_fields = ['product_name', 'category_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    ordering = ['-date', '-revenue']
    
    fieldsets = (
        ('Product & Date', {
            'fields': ('product_id', 'product_name', 'category_id', 'category_name', 'date')
        }),
        ('Sales Metrics', {
            'fields': ('units_sold', 'revenue', 'cost', 'profit', 'profit_margin')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
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
        'average_order_value', 'customer_segment', 'churn_probability'
    ]
    list_filter = [
        'customer_segment', 'last_order_date', 'acquisition_date', 'created_at'
    ]
    search_fields = ['customer_email', 'customer_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-total_spent', '-total_orders']
    
    fieldsets = (
        ('Customer', {
            'fields': ('customer_id', 'customer_email')
        }),
        ('Acquisition', {
            'fields': ('acquisition_date', 'acquisition_channel')
        }),
        ('Order Metrics', {
            'fields': (
                'total_orders', 'total_spent', 'average_order_value',
                'lifetime_value', 'last_order_date', 'days_since_last_order'
            )
        }),
        ('Segmentation', {
            'fields': ('customer_segment', 'churn_probability')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SalesForecast)
class SalesForecastAdmin(admin.ModelAdmin):
    """
    Admin interface for sales forecasts.
    """
    list_display = [
        'forecast_date', 'forecast_type', 'predicted_revenue',
        'predicted_orders', 'model_accuracy', 'created_at'
    ]
    list_filter = ['forecast_type', 'forecast_date', 'created_at']
    search_fields = ['forecast_date']
    readonly_fields = ['created_at']
    date_hierarchy = 'forecast_date'
    ordering = ['-forecast_date']
    
    fieldsets = (
        ('Forecast Details', {
            'fields': ('forecast_date', 'forecast_type')
        }),
        ('Predictions', {
            'fields': (
                'predicted_revenue', 'predicted_orders',
                'confidence_interval_lower', 'confidence_interval_upper'
            )
        }),
        ('Model Performance', {
            'fields': ('model_accuracy', 'seasonal_factor', 'trend_factor')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(SalesGoal)
class SalesGoalAdmin(admin.ModelAdmin):
    """
    Admin interface for sales goals.
    """
    list_display = [
        'name', 'goal_type', 'target_value', 'current_value',
        'progress_percentage', 'is_achieved', 'end_date'
    ]
    list_filter = ['goal_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['name', 'department', 'region']
    readonly_fields = ['created_at', 'updated_at', 'progress_percentage', 'is_achieved']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']

@admin.register(SalesCommission)
class SalesCommissionAdmin(admin.ModelAdmin):
    """
    Admin interface for sales commissions.
    """
    list_display = [
        'sales_rep', 'period_start', 'period_end', 'total_sales',
        'commission_amount', 'status', 'created_at'
    ]
    list_filter = ['status', 'period_start', 'period_end']
    search_fields = ['sales_rep__username', 'sales_rep__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'period_start'
    ordering = ['-period_start']

@admin.register(SalesTerritory)
class SalesTerritoryAdmin(admin.ModelAdmin):
    """
    Admin interface for sales territories.
    """
    list_display = [
        'name', 'region', 'country', 'assigned_rep',
        'target_revenue', 'current_revenue', 'revenue_achievement'
    ]
    list_filter = ['region', 'country', 'is_active']
    search_fields = ['name', 'region', 'country']
    readonly_fields = ['created_at', 'updated_at', 'revenue_achievement']

@admin.register(SalesPipeline)
class SalesPipelineAdmin(admin.ModelAdmin):
    """
    Admin interface for sales pipeline.
    """
    list_display = [
        'opportunity_name', 'customer_name', 'sales_rep', 'stage',
        'estimated_value', 'probability', 'expected_close_date'
    ]
    list_filter = ['stage', 'sales_rep', 'expected_close_date']
    search_fields = ['opportunity_name', 'customer_name']
    readonly_fields = ['created_at', 'updated_at', 'weighted_value', 'is_overdue']

@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    """
    Admin interface for sales reports.
    """
    list_display = [
        'name', 'report_type', 'schedule', 'last_sent',
        'next_send', 'is_active', 'created_by'
    ]
    list_filter = ['report_type', 'schedule', 'is_active']
    search_fields = ['name', 'created_by__username']
    readonly_fields = ['created_at']

@admin.register(SalesAnomalyDetection)
class SalesAnomalyDetectionAdmin(admin.ModelAdmin):
    """
    Admin interface for sales anomaly detection.
    """
    list_display = [
        'date', 'metric_type', 'actual_value', 'expected_value',
        'deviation_percentage', 'severity', 'is_resolved'
    ]
    list_filter = ['metric_type', 'severity', 'is_resolved', 'date']
    search_fields = ['date']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    ordering = ['-date', '-severity']