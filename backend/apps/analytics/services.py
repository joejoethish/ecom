"""
Analytics services for data processing and report generation.
"""
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import json

from .models import (
    DailySalesReport, ProductPerformanceReport, CustomerAnalytics,
    InventoryReport, SystemMetrics, ReportExport
)


class AnalyticsService:
    """
    Core analytics service for generating insights and reports.
    """

    @staticmethod
    def generate_dashboard_metrics(date_from: datetime = None, date_to: datetime = None) -> Dict:
        """
        Generate key metrics for admin dashboard.
        """
        if not date_from:
            date_from = timezone.now() - timedelta(days=30)
        if not date_to:
            date_to = timezone.now()

        from apps.orders.models import Order
        from apps.customers.models import Customer
        from apps.products.models import Product
        from apps.inventory.models import Inventory

        # Sales metrics
        orders = Order.objects.filter(
            created_at__range=[date_from, date_to],
            is_deleted=False
        ).exclude(status='cancelled')

        sales_data = orders.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_amount'),
            average_order_value=Avg('total_amount')
        )

        # Customer metrics
        customers = Customer.objects.filter(
            user__date_joined__range=[date_from, date_to],
            is_deleted=False
        )
        
        customer_data = {
            'new_customers': customers.count(),
            'total_customers': Customer.objects.filter(is_deleted=False).count(),
            'returning_customers': orders.values('user').distinct().count() - customers.count()
        }

        # Product metrics
        products = Product.objects.filter(is_active=True, is_deleted=False)
        inventory_data = Inventory.objects.filter(
            product__in=products
        ).aggregate(
            total_products=Count('id'),
            low_stock_products=Count('id', filter=Q(quantity__lte=F('minimum_stock_level'))),
            out_of_stock_products=Count('id', filter=Q(quantity=0)),
            total_inventory_value=Sum(F('quantity') * F('product__price'))
        )

        # Order status breakdown
        order_status_data = {}
        for status, _ in Order.ORDER_STATUS_CHOICES:
            order_status_data[status.lower()] = orders.filter(status=status).count()

        # Growth calculations (compare with previous period)
        previous_period_start = date_from - (date_to - date_from)
        previous_orders = Order.objects.filter(
            created_at__range=[previous_period_start, date_from],
            is_deleted=False
        ).exclude(status='cancelled')

        previous_revenue = previous_orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        current_revenue = sales_data['total_revenue'] or 0
        revenue_growth = 0
        if previous_revenue > 0:
            revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100

        return {
            'sales': {
                **sales_data,
                'revenue_growth': round(revenue_growth, 2)
            },
            'customers': customer_data,
            'inventory': inventory_data,
            'orders_by_status': order_status_data,
            'period': {
                'from': date_from.isoformat(),
                'to': date_to.isoformat()
            }
        }

    @staticmethod
    def generate_sales_report(date_from: datetime, date_to: datetime, 
                            filters: Dict = None) -> Dict:
        """
        Generate comprehensive sales report.
        """
        from apps.orders.models import Order, OrderItem
        
        filters = filters or {}
        
        # Base queryset
        orders = Order.objects.filter(
            created_at__range=[date_from, date_to],
            is_deleted=False
        ).exclude(status='cancelled')
        
        # Apply additional filters
        if filters.get('category'):
            orders = orders.filter(
                items__product__category_id=filters['category']
            ).distinct()
        
        if filters.get('product'):
            orders = orders.filter(
                items__product_id=filters['product']
            ).distinct()

        # Sales summary
        sales_summary = orders.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_amount'),
            total_discount=Sum('discount_amount'),
            total_tax=Sum('tax_amount'),
            total_shipping=Sum('shipping_amount'),
            average_order_value=Avg('total_amount')
        )

        # Daily breakdown
        daily_sales = orders.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            orders=Count('id'),
            revenue=Sum('total_amount')
        ).order_by('day')

        # Top products
        top_products = OrderItem.objects.filter(
            order__in=orders
        ).values(
            'product__name', 'product__id'
        ).annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum('total_price')
        ).order_by('-revenue')[:10]

        # Payment method breakdown
        payment_methods = orders.values('payment_method').annotate(
            count=Count('id'),
            revenue=Sum('total_amount')
        ).order_by('-revenue')

        return {
            'summary': sales_summary,
            'daily_breakdown': list(daily_sales),
            'top_products': list(top_products),
            'payment_methods': list(payment_methods),
            'filters_applied': filters,
            'period': {
                'from': date_from.isoformat(),
                'to': date_to.isoformat()
            }
        }

    @staticmethod
    def generate_profit_loss_report(date_from: datetime, date_to: datetime) -> Dict:
        """
        Generate profit and loss report.
        """
        from apps.orders.models import Order, OrderItem
        from apps.inventory.models import Inventory
        
        orders = Order.objects.filter(
            created_at__range=[date_from, date_to],
            is_deleted=False,
            status='delivered'  # Only count delivered orders for P&L
        )

        # Revenue calculation
        revenue_data = orders.aggregate(
            gross_revenue=Sum('total_amount'),
            total_discount=Sum('discount_amount'),
            total_tax=Sum('tax_amount'),
            total_shipping=Sum('shipping_amount')
        )

        net_revenue = (revenue_data['gross_revenue'] or 0) - (revenue_data['total_discount'] or 0)

        # Cost calculation
        total_cost = Decimal('0')
        order_items = OrderItem.objects.filter(order__in=orders)
        
        for item in order_items:
            try:
                cost_price = item.product.inventory.cost_price or 0
                total_cost += cost_price * item.quantity
            except:
                continue

        # Calculate profit
        gross_profit = net_revenue - total_cost
        
        # Operating expenses (simplified - could be expanded)
        operating_expenses = {
            'shipping_costs': revenue_data['total_shipping'] or 0,
            'payment_processing': net_revenue * Decimal('0.025'),  # 2.5% processing fee
            'platform_costs': net_revenue * Decimal('0.05'),  # 5% platform costs
        }
        
        total_operating_expenses = sum(operating_expenses.values())
        net_profit = gross_profit - total_operating_expenses

        # Profit margins
        gross_margin = (gross_profit / net_revenue * 100) if net_revenue > 0 else 0
        net_margin = (net_profit / net_revenue * 100) if net_revenue > 0 else 0

        return {
            'revenue': {
                'gross_revenue': float(revenue_data['gross_revenue'] or 0),
                'discounts': float(revenue_data['total_discount'] or 0),
                'net_revenue': float(net_revenue),
            },
            'costs': {
                'cost_of_goods_sold': float(total_cost),
                'operating_expenses': {k: float(v) for k, v in operating_expenses.items()},
                'total_operating_expenses': float(total_operating_expenses),
            },
            'profit': {
                'gross_profit': float(gross_profit),
                'net_profit': float(net_profit),
                'gross_margin_percent': round(float(gross_margin), 2),
                'net_margin_percent': round(float(net_margin), 2),
            },
            'period': {
                'from': date_from.isoformat(),
                'to': date_to.isoformat()
            }
        }

    @staticmethod
    def get_top_selling_products(date_from: datetime = None, date_to: datetime = None, 
                               limit: int = 10) -> List[Dict]:
        """
        Get top-selling products by quantity and revenue.
        """
        from apps.orders.models import OrderItem
        
        if not date_from:
            date_from = timezone.now() - timedelta(days=30)
        if not date_to:
            date_to = timezone.now()

        top_products = OrderItem.objects.filter(
            order__created_at__range=[date_from, date_to],
            order__is_deleted=False
        ).exclude(
            order__status='cancelled'
        ).values(
            'product__id',
            'product__name',
            'product__sku',
            'product__price',
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price'),
            order_count=Count('order', distinct=True)
        ).order_by('-total_revenue')[:limit]

        return list(top_products)

    @staticmethod
    def get_customer_analytics_summary() -> Dict:
        """
        Get customer analytics summary.
        """
        from apps.customers.models import Customer
        
        # Lifecycle stage distribution
        lifecycle_distribution = CustomerAnalytics.objects.values(
            'lifecycle_stage'
        ).annotate(
            count=Count('id')
        ).order_by('lifecycle_stage')

        # Top customers by lifetime value
        top_customers = CustomerAnalytics.objects.select_related(
            'customer__user'
        ).order_by('-lifetime_value')[:10]

        # Customer segments
        segments = CustomerAnalytics.objects.exclude(
            customer_segment=''
        ).values('customer_segment').annotate(
            count=Count('id'),
            avg_lifetime_value=Avg('lifetime_value')
        ).order_by('-avg_lifetime_value')

        return {
            'lifecycle_distribution': list(lifecycle_distribution),
            'top_customers': [
                {
                    'customer_id': ca.customer.id,
                    'email': ca.customer.user.email,
                    'lifetime_value': float(ca.lifetime_value),
                    'total_orders': ca.total_orders,
                    'lifecycle_stage': ca.lifecycle_stage
                }
                for ca in top_customers
            ],
            'segments': list(segments)
        }


class ReportGenerationService:
    """
    Service for generating and exporting reports.
    """

    @staticmethod
    def schedule_daily_reports():
        """
        Schedule generation of daily reports (to be called by Celery).
        """
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Generate daily sales report
        DailySalesReport.generate_report(yesterday)
        
        # Generate inventory report
        InventoryReport.generate_report(yesterday)
        
        # Update customer analytics
        from apps.customers.models import Customer
        customers = Customer.objects.filter(is_deleted=False)
        
        for customer in customers:
            analytics, created = CustomerAnalytics.objects.get_or_create(
                customer=customer
            )
            analytics.update_analytics()

    @staticmethod
    def export_report(report_type: str, export_format: str, user, 
                     date_from: datetime = None, date_to: datetime = None,
                     filters: Dict = None) -> ReportExport:
        """
        Create a report export job.
        """
        export = ReportExport.objects.create(
            report_type=report_type,
            export_format=export_format,
            exported_by=user,
            date_from=date_from.date() if date_from else None,
            date_to=date_to.date() if date_to else None,
            filters=filters or {},
            expires_at=timezone.now() + timedelta(days=7)  # Expire after 7 days
        )
        
        # In a real implementation, this would trigger a background task
        # to generate the actual file
        
        return export

    @staticmethod
    def get_stock_maintenance_report() -> Dict:
        """
        Generate stock maintenance report.
        """
        from apps.inventory.models import Inventory
        from apps.products.models import Product
        
        # Low stock products
        low_stock = Inventory.objects.filter(
            quantity__lte=F('minimum_stock_level'),
            quantity__gt=0,
            product__is_active=True
        ).select_related('product').order_by('quantity')

        # Out of stock products
        out_of_stock = Inventory.objects.filter(
            quantity=0,
            product__is_active=True
        ).select_related('product')

        # Overstock products (quantity > maximum_stock_level)
        overstock = Inventory.objects.filter(
            quantity__gt=F('maximum_stock_level'),
            product__is_active=True
        ).select_related('product').order_by('-quantity')

        # Dead stock (no sales in last 90 days)
        ninety_days_ago = timezone.now() - timedelta(days=90)
        from apps.orders.models import OrderItem
        
        products_with_recent_sales = OrderItem.objects.filter(
            order__created_at__gte=ninety_days_ago,
            order__is_deleted=False
        ).values_list('product_id', flat=True).distinct()

        dead_stock = Inventory.objects.filter(
            product__is_active=True,
            quantity__gt=0
        ).exclude(
            product_id__in=products_with_recent_sales
        ).select_related('product')

        return {
            'low_stock': [
                {
                    'product_id': inv.product.id,
                    'product_name': inv.product.name,
                    'sku': inv.product.sku,
                    'current_quantity': inv.quantity,
                    'minimum_level': inv.minimum_stock_level,
                    'reorder_point': inv.reorder_point
                }
                for inv in low_stock[:50]  # Limit to 50 items
            ],
            'out_of_stock': [
                {
                    'product_id': inv.product.id,
                    'product_name': inv.product.name,
                    'sku': inv.product.sku,
                    'last_restocked': inv.last_restocked.isoformat() if inv.last_restocked else None
                }
                for inv in out_of_stock[:50]
            ],
            'overstock': [
                {
                    'product_id': inv.product.id,
                    'product_name': inv.product.name,
                    'sku': inv.product.sku,
                    'current_quantity': inv.quantity,
                    'maximum_level': inv.maximum_stock_level,
                    'excess_quantity': inv.quantity - inv.maximum_stock_level
                }
                for inv in overstock[:50]
            ],
            'dead_stock': [
                {
                    'product_id': inv.product.id,
                    'product_name': inv.product.name,
                    'sku': inv.product.sku,
                    'current_quantity': inv.quantity,
                    'inventory_value': float(inv.quantity * inv.product.price)
                }
                for inv in dead_stock[:50]
            ],
            'summary': {
                'low_stock_count': low_stock.count(),
                'out_of_stock_count': out_of_stock.count(),
                'overstock_count': overstock.count(),
                'dead_stock_count': dead_stock.count()
            }
        }


class SystemMonitoringService:
    """
    Service for system monitoring and health metrics.
    """

    @staticmethod
    def record_system_metrics(response_time_avg: float = 0, error_rate: float = 0,
                            active_users: int = 0, **kwargs):
        """
        Record system performance metrics.
        """
        SystemMetrics.objects.create(
            response_time_avg=response_time_avg,
            error_rate=error_rate,
            active_users=active_users,
            **kwargs
        )

    @staticmethod
    def get_system_health_summary(hours: int = 24) -> Dict:
        """
        Get system health summary for the last N hours.
        """
        since = timezone.now() - timedelta(hours=hours)
        
        metrics = SystemMetrics.objects.filter(
            timestamp__gte=since
        ).aggregate(
            avg_response_time=Avg('response_time_avg'),
            max_response_time=models.Max('response_time_avg'),
            avg_error_rate=Avg('error_rate'),
            max_error_rate=models.Max('error_rate'),
            avg_active_users=Avg('active_users'),
            max_active_users=models.Max('active_users')
        )

        # Get latest metrics
        latest = SystemMetrics.objects.first()

        return {
            'period_summary': metrics,
            'current_metrics': {
                'response_time': float(latest.response_time_avg) if latest else 0,
                'error_rate': float(latest.error_rate) if latest else 0,
                'active_users': latest.active_users if latest else 0,
                'memory_usage': float(latest.memory_usage_percent) if latest else 0,
                'cpu_usage': float(latest.cpu_usage_percent) if latest else 0,
            } if latest else {},
            'health_status': 'healthy' if (
                (latest and latest.error_rate < 5 and latest.response_time_avg < 1000) 
                or not latest
            ) else 'warning'
        }