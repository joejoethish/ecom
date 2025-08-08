from django.db.models import Sum, Count, Avg, Q, F, Max, Min, StdDev, Variance
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
import json
from django.db import models, transaction
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    SalesMetrics, ProductSalesAnalytics, CustomerAnalytics, SalesForecast,
    SalesGoal, SalesCommission, SalesTerritory, SalesPipeline, SalesReport,
    SalesAnomalyDetection
)


class SalesAnalyticsService:
    """
    Comprehensive sales analytics service with advanced reporting capabilities.
    """

    @staticmethod
    def generate_sales_dashboard(date_from: datetime = None, date_to: datetime = None) -> Dict:
        """
        Generate comprehensive sales dashboard with KPIs and trend analysis.
        """
        if not date_from:
            date_from = timezone.now() - timedelta(days=30)
        if not date_to:
            date_to = timezone.now()

        from apps.orders.models import Order, OrderItem
        from apps.customers.models import CustomerProfile

        # Base orders queryset
        orders = Order.objects.filter(
            created_at__range=[date_from, date_to],
            is_deleted=False
        ).exclude(status='cancelled')

        # Core metrics
        sales_metrics = orders.aggregate(
            total_revenue=Sum('total_amount') or 0,
            total_orders=Count('id'),
            average_order_value=Avg('total_amount') or 0,
            total_customers=Count('customer', distinct=True),
            gross_margin=Sum(F('total_amount') - F('discount_amount')) or 0
        )

        # Calculate conversion rate (orders / unique visitors)
        # For now, using a simplified calculation
        unique_customers = orders.values('customer').distinct().count()
        total_customers = CustomerProfile.objects.filter(is_deleted=False).count()
        conversion_rate = (unique_customers / total_customers * 100) if total_customers > 0 else 0

        # Growth calculations
        previous_period_start = date_from - (date_to - date_from)
        previous_orders = Order.objects.filter(
            created_at__range=[previous_period_start, date_from],
            is_deleted=False
        ).exclude(status='cancelled')

        previous_metrics = previous_orders.aggregate(
            revenue=Sum('total_amount') or 0,
            orders=Count('id')
        )

        revenue_growth = SalesAnalyticsService._calculate_growth(
            sales_metrics['total_revenue'], previous_metrics['revenue']
        )
        order_growth = SalesAnalyticsService._calculate_growth(
            sales_metrics['total_orders'], previous_metrics['orders']
        )

        # Top performing products
        top_products = ProductSalesAnalytics.objects.filter(
            date__range=[date_from.date(), date_to.date()]
        ).values(
            'product_id', 'product_name', 'category_name'
        ).annotate(
            total_revenue=Sum('revenue'),
            total_units=Sum('units_sold'),
            total_profit=Sum('profit')
        ).order_by('-total_revenue')[:10]

        # Recent anomalies
        recent_anomalies = SalesAnomalyDetection.objects.filter(
            date__range=[date_from.date(), date_to.date()],
            is_resolved=False
        ).order_by('-severity', '-date')[:5]

        # Active goals
        active_goals = SalesGoal.objects.filter(
            is_active=True,
            start_date__lte=date_to.date(),
            end_date__gte=date_from.date()
        ).order_by('-created_at')[:5]

        return {
            'total_revenue': sales_metrics['total_revenue'],
            'total_orders': sales_metrics['total_orders'],
            'average_order_value': sales_metrics['average_order_value'],
            'conversion_rate': round(conversion_rate, 2),
            'revenue_growth': revenue_growth,
            'order_growth': order_growth,
            'top_products': list(top_products),
            'recent_anomalies': list(recent_anomalies),
            'active_goals': list(active_goals),
            'period': {
                'from': date_from.isoformat(),
                'to': date_to.isoformat()
            }
        }

    @staticmethod
    def _calculate_growth(current: float, previous: float) -> float:
        """Calculate percentage growth between two values."""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    @staticmethod
    def generate_revenue_analysis(date_from: datetime, date_to: datetime, 
                                group_by: str = 'day') -> List[Dict]:
        """
        Generate detailed revenue analysis with grouping options.
        """
        from apps.orders.models import Order, OrderItem

        orders = Order.objects.filter(
            created_at__range=[date_from, date_to],
            is_deleted=False
        ).exclude(status='cancelled')

        # Group by period
        if group_by == 'day':
            date_trunc = 'day'
        elif group_by == 'week':
            date_trunc = 'week'
        elif group_by == 'month':
            date_trunc = 'month'
        else:
            date_trunc = 'day'

        # Aggregate by period
        revenue_data = orders.extra(
            select={
                'period': f"DATE_TRUNC('{date_trunc}', created_at)"
            }
        ).values('period').annotate(
            revenue=Sum('total_amount'),
            orders=Count('id'),
            customers=Count('customer', distinct=True),
            average_order_value=Avg('total_amount'),
            gross_margin=Sum(F('total_amount') - F('discount_amount')),
            net_profit=Sum(F('total_amount') - F('discount_amount') - F('tax_amount'))
        ).order_by('period')

        # Calculate profit margins
        result = []
        for item in revenue_data:
            profit_margin = 0
            if item['revenue'] and item['revenue'] > 0:
                profit_margin = (item['net_profit'] / item['revenue']) * 100

            result.append({
                'period': item['period'].strftime('%Y-%m-%d'),
                'revenue': float(item['revenue'] or 0),
                'orders': item['orders'],
                'customers': item['customers'],
                'average_order_value': float(item['average_order_value'] or 0),
                'gross_margin': float(item['gross_margin'] or 0),
                'net_profit': float(item['net_profit'] or 0),
                'profit_margin_percentage': round(profit_margin, 2)
            })

        return result

    @staticmethod
    def generate_customer_cohort_analysis(months_back: int = 12) -> List[Dict]:
        """
        Generate customer cohort analysis for retention tracking.
        """
        from apps.orders.models import Order
        from apps.customers.models import CustomerProfile

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=months_back * 30)

        # Get customer acquisition cohorts
        cohorts = CustomerProfile.objects.filter(
            user__date_joined__gte=start_date,
            is_deleted=False
        ).extra(
            select={
                'cohort_month': "DATE_TRUNC('month', user.date_joined)"
            }
        ).values('cohort_month').annotate(
            customers_count=Count('id')
        ).order_by('cohort_month')

        result = []
        for cohort in cohorts:
            cohort_month = cohort['cohort_month']
            customers_in_cohort = CustomerProfile.objects.filter(
                user__date_joined__gte=cohort_month,
                user__date_joined__lt=cohort_month + timedelta(days=32),
                is_deleted=False
            )

            # Calculate retention rates for each subsequent month
            retention_rates = {}
            revenue_per_cohort = {}

            for month_offset in range(12):  # Track 12 months
                period_start = cohort_month + timedelta(days=month_offset * 30)
                period_end = period_start + timedelta(days=30)

                # Count customers who made orders in this period
                active_customers = Order.objects.filter(
                    customer__in=customers_in_cohort.values_list('user', flat=True),
                    created_at__range=[period_start, period_end],
                    is_deleted=False
                ).exclude(status='cancelled').values('customer').distinct().count()

                retention_rate = (active_customers / cohort['customers_count'] * 100) if cohort['customers_count'] > 0 else 0
                retention_rates[f'month_{month_offset}'] = round(retention_rate, 2)

                # Calculate revenue for this cohort in this period
                cohort_revenue = Order.objects.filter(
                    customer__in=customers_in_cohort.values_list('user', flat=True),
                    created_at__range=[period_start, period_end],
                    is_deleted=False
                ).exclude(status='cancelled').aggregate(
                    total=Sum('total_amount')
                )['total'] or 0

                revenue_per_cohort[f'month_{month_offset}'] = float(cohort_revenue)

            result.append({
                'cohort_month': cohort_month.strftime('%Y-%m'),
                'customers_count': cohort['customers_count'],
                'retention_rates': retention_rates,
                'revenue_per_cohort': revenue_per_cohort
            })

        return result

    @staticmethod
    def generate_sales_funnel_analysis(date_from: datetime, date_to: datetime) -> List[Dict]:
        """
        Generate sales funnel analysis with conversion tracking.
        """
        from apps.orders.models import Order
        from apps.customers.models import CustomerProfile

        # Define funnel stages (simplified)
        stages = [
            {'name': 'Visitors', 'count': 0, 'conversion_rate': 100.0},
            {'name': 'Registered Users', 'count': 0, 'conversion_rate': 0.0},
            {'name': 'Cart Created', 'count': 0, 'conversion_rate': 0.0},
            {'name': 'Checkout Started', 'count': 0, 'conversion_rate': 0.0},
            {'name': 'Order Placed', 'count': 0, 'conversion_rate': 0.0},
            {'name': 'Payment Completed', 'count': 0, 'conversion_rate': 0.0}
        ]

        # For this implementation, we'll use simplified metrics
        # In a real system, you'd track these events separately

        # Total registered users (proxy for visitors)
        total_users = CustomerProfile.objects.filter(
            user__date_joined__range=[date_from, date_to],
            is_deleted=False
        ).count()

        # Users who placed orders
        users_with_orders = Order.objects.filter(
            created_at__range=[date_from, date_to],
            is_deleted=False
        ).values('customer').distinct().count()

        # Orders placed
        orders_placed = Order.objects.filter(
            created_at__range=[date_from, date_to],
            is_deleted=False
        ).count()

        # Completed orders (paid)
        completed_orders = Order.objects.filter(
            created_at__range=[date_from, date_to],
            payment_status='paid',
            is_deleted=False
        ).count()

        # Update stage counts
        stages[0]['count'] = total_users * 10  # Assume 10x visitors to registrations
        stages[1]['count'] = total_users
        stages[2]['count'] = int(total_users * 0.7)  # 70% create carts
        stages[3]['count'] = int(total_users * 0.5)  # 50% start checkout
        stages[4]['count'] = orders_placed
        stages[5]['count'] = completed_orders

        # Calculate conversion rates and drop-off rates
        for i, stage in enumerate(stages):
            if i > 0 and stages[i-1]['count'] > 0:
                stage['conversion_rate'] = round((stage['count'] / stages[i-1]['count']) * 100, 2)
                stage['drop_off_rate'] = round(100 - stage['conversion_rate'], 2)
            else:
                stage['drop_off_rate'] = 0.0

        return stages

    @staticmethod
    def generate_sales_attribution_analysis(date_from: datetime, date_to: datetime) -> List[Dict]:
        """
        Generate sales attribution analysis across marketing channels.
        """
        from apps.orders.models import Order

        # For this implementation, we'll use simplified channel attribution
        # In a real system, you'd track UTM parameters and referral sources

        channels = [
            'organic_search', 'paid_search', 'social_media', 'email_marketing',
            'direct', 'referral', 'affiliate', 'display_ads'
        ]

        result = []
        total_orders = Order.objects.filter(
            created_at__range=[date_from, date_to],
            is_deleted=False
        ).exclude(status='cancelled')

        total_revenue = total_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_order_count = total_orders.count()

        for channel in channels:
            # Simulate channel attribution (in real implementation, this would come from tracking data)
            channel_weight = {
                'organic_search': 0.25,
                'paid_search': 0.20,
                'social_media': 0.15,
                'email_marketing': 0.12,
                'direct': 0.10,
                'referral': 0.08,
                'affiliate': 0.06,
                'display_ads': 0.04
            }.get(channel, 0.05)

            channel_revenue = float(total_revenue) * channel_weight
            channel_orders = int(total_order_count * channel_weight)
            channel_customers = int(channel_orders * 0.8)  # Assume some repeat customers

            # Simulate costs (in real implementation, this would come from ad spend data)
            cost_per_acquisition = {
                'organic_search': 5.0,
                'paid_search': 25.0,
                'social_media': 15.0,
                'email_marketing': 2.0,
                'direct': 0.0,
                'referral': 10.0,
                'affiliate': 20.0,
                'display_ads': 30.0
            }.get(channel, 10.0)

            total_cost = channel_customers * cost_per_acquisition
            roi = ((channel_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0

            conversion_rate = (channel_orders / (channel_customers * 2)) * 100 if channel_customers > 0 else 0

            result.append({
                'channel': channel.replace('_', ' ').title(),
                'revenue': round(channel_revenue, 2),
                'orders': channel_orders,
                'customers': channel_customers,
                'conversion_rate': round(conversion_rate, 2),
                'cost_per_acquisition': cost_per_acquisition,
                'return_on_investment': round(roi, 2)
            })

        return sorted(result, key=lambda x: x['revenue'], reverse=True)

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
                     filters: Dict = None) -> Dict:
        """
        Create a report export job.
        """
        try:
            # Generate report data based on type
            if report_type == 'sales':
                if not date_from:
                    date_from = timezone.now() - timedelta(days=30)
                if not date_to:
                    date_to = timezone.now()
                data = AnalyticsService.generate_sales_report(date_from, date_to, filters)
            elif report_type == 'inventory':
                data = ReportGenerationService.get_stock_maintenance_report()
            elif report_type == 'customer':
                data = AnalyticsService.get_customer_analytics_summary()
            elif report_type == 'profit_loss':
                if not date_from:
                    date_from = timezone.now() - timedelta(days=30)
                if not date_to:
                    date_to = timezone.now()
                data = AnalyticsService.generate_profit_loss_report(date_from, date_to)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
            
            # Generate filename
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{report_type}_report_{timestamp}.{export_format}"
            
            return {
                'status': 'completed',
                'filename': filename,
                'data': data,
                'message': 'Report generated successfully'
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'message': 'Report generation failed'
            }

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


class SalesForecastingService:
    """
    Advanced sales forecasting service with machine learning algorithms.
    """

    @staticmethod
    def generate_sales_forecast(forecast_type: str = 'monthly', periods: int = 12) -> List[Dict]:
        """
        Generate sales forecast using simple statistical methods.
        """
        # Get historical sales data
        historical_data = SalesMetrics.objects.all().order_by('date')
        
        if not historical_data.exists():
            return []
        
        # Calculate simple moving averages and trends
        recent_data = list(historical_data.order_by('-date')[:30])  # Last 30 records
        
        if len(recent_data) < 3:
            return []
        
        # Calculate averages
        avg_revenue = sum(float(record.total_revenue) for record in recent_data) / len(recent_data)
        avg_orders = sum(record.total_orders for record in recent_data) / len(recent_data)
        
        # Calculate simple trend (difference between recent and older averages)
        if len(recent_data) >= 10:
            recent_avg_revenue = sum(float(record.total_revenue) for record in recent_data[:5]) / 5
            older_avg_revenue = sum(float(record.total_revenue) for record in recent_data[-5:]) / 5
            trend_factor = recent_avg_revenue / older_avg_revenue if older_avg_revenue > 0 else 1.0
        else:
            trend_factor = 1.0
        
        # Generate forecasts
        forecasts = []
        last_date = recent_data[0].date
        
        for i in range(1, periods + 1):
            # Calculate forecast date based on type
            if forecast_type == 'daily':
                forecast_date = last_date + timedelta(days=i)
            elif forecast_type == 'weekly':
                forecast_date = last_date + timedelta(weeks=i)
            elif forecast_type == 'monthly':
                forecast_date = last_date + timedelta(days=30 * i)
            elif forecast_type == 'quarterly':
                forecast_date = last_date + timedelta(days=90 * i)
            else:
                forecast_date = last_date + timedelta(days=i)
            
            # Simple prediction with trend
            predicted_revenue = avg_revenue * (trend_factor ** (i * 0.1))  # Gradual trend application
            predicted_orders = int(avg_orders * (trend_factor ** (i * 0.1)))
            
            # Simple confidence intervals (±20%)
            confidence_lower = max(0, predicted_revenue * 0.8)
            confidence_upper = predicted_revenue * 1.2
            
            # Apply seasonal factor (simplified)
            seasonal_factor = SalesForecastingService._calculate_seasonal_factor(
                forecast_date, historical_data
            )
            
            # Adjust predictions
            predicted_revenue *= seasonal_factor
            confidence_lower *= seasonal_factor
            confidence_upper *= seasonal_factor
            
            forecasts.append({
                'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                'forecast_type': forecast_type,
                'predicted_revenue': round(predicted_revenue, 2),
                'predicted_orders': max(1, predicted_orders),
                'confidence_interval_lower': round(confidence_lower, 2),
                'confidence_interval_upper': round(confidence_upper, 2),
                'model_accuracy': 75.0,  # Fixed accuracy for simple model
                'seasonal_factor': round(seasonal_factor, 2),
                'trend_factor': round(trend_factor, 2)
            })
        
        return forecasts

    @staticmethod
    def _calculate_seasonal_factor(forecast_date: date, historical_data) -> float:
        """Calculate simple seasonal factor based on month."""
        month = forecast_date.month
        
        # Simple seasonal factors (higher in Nov-Dec, lower in Jan-Feb)
        seasonal_factors = {
            1: 0.85,   # January
            2: 0.90,   # February
            3: 0.95,   # March
            4: 1.00,   # April
            5: 1.05,   # May
            6: 1.10,   # June
            7: 1.15,   # July
            8: 1.10,   # August
            9: 1.05,   # September
            10: 1.10,  # October
            11: 1.25,  # November
            12: 1.30,  # December
        }
        
        return seasonal_factors.get(month, 1.0)

    @staticmethod
    def update_forecast_accuracy():
        """Update forecast accuracy based on actual vs predicted values."""
        today = timezone.now().date()
        
        # Get forecasts from the past month
        past_forecasts = SalesForecast.objects.filter(
            forecast_date__range=[today - timedelta(days=30), today]
        )

        for forecast in past_forecasts:
            # Get actual sales for the forecast date
            actual_data = Order.objects.filter(
                created_at__date=forecast.forecast_date,
                is_deleted=False
            ).exclude(status='cancelled').aggregate(
                actual_revenue=Sum('total_amount'),
                actual_orders=Count('id')
            )

            actual_revenue = float(actual_data['actual_revenue'] or 0)
            actual_orders = actual_data['actual_orders'] or 0

            if actual_revenue > 0:
                # Calculate accuracy
                revenue_error = abs(actual_revenue - float(forecast.predicted_revenue)) / actual_revenue
                accuracy = max(0, (1 - revenue_error) * 100)
                
                forecast.model_accuracy = round(accuracy, 2)
                forecast.save()


class SalesCommissionService:
    """
    Service for managing sales commissions and automated payout processing.
    """

    @staticmethod
    def calculate_commissions(period_start: date, period_end: date) -> List[Dict]:
        """
        Calculate sales commissions for all sales representatives.
        """
        from apps.orders.models import Order
        from django.contrib.auth.models import User

        # Get all sales reps (users with sales role)
        sales_reps = User.objects.filter(
            groups__name='Sales',
            is_active=True
        )

        commissions = []

        for rep in sales_reps:
            # Get sales for this rep in the period
            rep_orders = Order.objects.filter(
                # Assuming we have a sales_rep field or similar tracking
                created_at__date__range=[period_start, period_end],
                status='delivered',
                is_deleted=False
            )

            total_sales = rep_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0

            # Calculate commission (simplified tiered structure)
            commission_rate = SalesCommissionService._get_commission_rate(float(total_sales))
            commission_amount = float(total_sales) * (commission_rate / 100)

            # Calculate bonus (if applicable)
            bonus_amount = SalesCommissionService._calculate_bonus(float(total_sales), rep)

            total_payout = commission_amount + bonus_amount

            commission_data = {
                'sales_rep': rep,
                'period_start': period_start,
                'period_end': period_end,
                'total_sales': total_sales,
                'commission_rate': commission_rate,
                'commission_amount': commission_amount,
                'bonus_amount': bonus_amount,
                'total_payout': total_payout,
                'status': 'pending'
            }

            # Create or update commission record
            commission, created = SalesCommission.objects.update_or_create(
                sales_rep=rep,
                period_start=period_start,
                period_end=period_end,
                defaults=commission_data
            )

            commissions.append({
                'id': commission.id,
                'sales_rep_name': rep.get_full_name(),
                'total_sales': float(total_sales),
                'commission_rate': commission_rate,
                'commission_amount': commission_amount,
                'bonus_amount': bonus_amount,
                'total_payout': total_payout,
                'status': commission.status
            })

        return commissions

    @staticmethod
    def _get_commission_rate(total_sales: float) -> float:
        """Get commission rate based on sales volume (tiered structure)."""
        if total_sales >= 100000:
            return 8.0  # 8% for sales over $100k
        elif total_sales >= 50000:
            return 6.0  # 6% for sales over $50k
        elif total_sales >= 25000:
            return 4.0  # 4% for sales over $25k
        else:
            return 2.0  # 2% base rate

    @staticmethod
    def _calculate_bonus(total_sales: float, rep) -> float:
        """Calculate bonus based on performance and goals."""
        # Check if rep has active goals
        active_goals = SalesGoal.objects.filter(
            assigned_to=rep,
            is_active=True,
            end_date__gte=timezone.now().date()
        )

        bonus = 0.0
        for goal in active_goals:
            if goal.is_achieved:
                # 10% bonus of commission for achieved goals
                bonus += total_sales * 0.001  # 0.1% bonus

        return bonus

    @staticmethod
    def process_commission_payouts(commission_ids: List[int], approved_by) -> Dict:
        """
        Process commission payouts (automated payout processing).
        """
        commissions = SalesCommission.objects.filter(
            id__in=commission_ids,
            status='approved'
        )

        processed_count = 0
        total_amount = 0

        with transaction.atomic():
            for commission in commissions:
                # In a real implementation, this would integrate with payment processing
                # For now, we'll just update the status
                commission.status = 'paid'
                commission.paid_date = timezone.now().date()
                commission.save()

                processed_count += 1
                total_amount += float(commission.total_payout)

                # Send notification to sales rep
                SalesCommissionService._send_payout_notification(commission)

        return {
            'processed_count': processed_count,
            'total_amount': total_amount,
            'message': f'Processed {processed_count} commission payouts totaling ${total_amount:,.2f}'
        }

    @staticmethod
    def _send_payout_notification(commission: SalesCommission):
        """Send payout notification to sales representative."""
        if hasattr(settings, 'EMAIL_BACKEND') and commission.sales_rep.email:
            subject = f'Commission Payout Processed - ${commission.total_payout:,.2f}'
            message = f"""
            Dear {commission.sales_rep.get_full_name()},

            Your commission payout has been processed:

            Period: {commission.period_start} to {commission.period_end}
            Total Sales: ${commission.total_sales:,.2f}
            Commission Rate: {commission.commission_rate}%
            Commission Amount: ${commission.commission_amount:,.2f}
            Bonus Amount: ${commission.bonus_amount:,.2f}
            Total Payout: ${commission.total_payout:,.2f}

            The payment will be reflected in your next payroll.

            Best regards,
            Sales Team
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [commission.sales_rep.email],
                fail_silently=True
            )


class SalesTerritoryService:
    """
    Service for sales territory management with geographic analysis.
    """

    @staticmethod
    def analyze_territory_performance() -> List[Dict]:
        """
        Analyze performance of all sales territories with geographic insights.
        """
        territories = SalesTerritory.objects.filter(is_active=True)
        
        performance_data = []
        
        for territory in territories:
            # Get orders from this territory (simplified - would use geographic matching)
            territory_orders = SalesTerritoryService._get_territory_orders(territory)
            
            current_revenue = territory_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            customer_count = territory_orders.values('customer').distinct().count()
            
            # Update territory metrics
            territory.current_revenue = current_revenue
            territory.customer_count = customer_count
            territory.save()
            
            # Calculate performance metrics
            revenue_achievement = territory.revenue_achievement
            avg_order_value = float(current_revenue) / territory_orders.count() if territory_orders.count() > 0 else 0
            
            performance_data.append({
                'territory_id': territory.id,
                'name': territory.name,
                'region': territory.region,
                'assigned_rep': territory.assigned_rep.get_full_name() if territory.assigned_rep else 'Unassigned',
                'target_revenue': float(territory.target_revenue),
                'current_revenue': float(current_revenue),
                'revenue_achievement': round(revenue_achievement, 2),
                'customer_count': customer_count,
                'avg_order_value': round(avg_order_value, 2),
                'performance_status': SalesTerritoryService._get_performance_status(revenue_achievement)
            })
        
        return sorted(performance_data, key=lambda x: x['revenue_achievement'], reverse=True)

    @staticmethod
    def _get_territory_orders(territory: SalesTerritory):
        """Get orders for a specific territory (simplified implementation)."""
        from apps.orders.models import Order
        
        # In a real implementation, this would match orders based on shipping address
        # For now, we'll use a simplified approach
        return Order.objects.filter(
            is_deleted=False,
            # This would be replaced with geographic matching logic
            shipping_address__icontains=territory.region
        ).exclude(status='cancelled')

    @staticmethod
    def _get_performance_status(achievement_percentage: float) -> str:
        """Get performance status based on achievement percentage."""
        if achievement_percentage >= 100:
            return 'Excellent'
        elif achievement_percentage >= 80:
            return 'Good'
        elif achievement_percentage >= 60:
            return 'Fair'
        else:
            return 'Needs Improvement'

    @staticmethod
    def optimize_territory_assignments() -> Dict:
        """
        Optimize territory assignments based on performance and workload.
        """
        territories = SalesTerritory.objects.filter(is_active=True)
        sales_reps = User.objects.filter(groups__name='Sales', is_active=True)
        
        # Calculate workload for each rep
        rep_workloads = {}
        for rep in sales_reps:
            assigned_territories = territories.filter(assigned_rep=rep)
            total_customers = sum(t.customer_count for t in assigned_territories)
            total_revenue_target = sum(float(t.target_revenue) for t in assigned_territories)
            
            rep_workloads[rep.id] = {
                'rep': rep,
                'territory_count': assigned_territories.count(),
                'customer_count': total_customers,
                'revenue_target': total_revenue_target,
                'workload_score': total_customers + (total_revenue_target / 10000)  # Simplified scoring
            }
        
        # Find optimization opportunities
        recommendations = []
        avg_workload = sum(data['workload_score'] for data in rep_workloads.values()) / len(rep_workloads)
        
        for rep_id, data in rep_workloads.items():
            if data['workload_score'] > avg_workload * 1.2:  # 20% above average
                recommendations.append({
                    'type': 'redistribute',
                    'rep_name': data['rep'].get_full_name(),
                    'current_workload': round(data['workload_score'], 2),
                    'recommendation': 'Consider redistributing some territories to balance workload'
                })
            elif data['workload_score'] < avg_workload * 0.8:  # 20% below average
                recommendations.append({
                    'type': 'assign_more',
                    'rep_name': data['rep'].get_full_name(),
                    'current_workload': round(data['workload_score'], 2),
                    'recommendation': 'Can handle additional territories'
                })
        
        return {
            'average_workload': round(avg_workload, 2),
            'recommendations': recommendations,
            'total_territories': territories.count(),
            'total_reps': sales_reps.count()
        }


class SalesPipelineService:
    """
    Service for sales pipeline management and opportunity tracking.
    """

    @staticmethod
    def get_pipeline_overview() -> Dict:
        """
        Get comprehensive sales pipeline overview with forecasting.
        """
        opportunities = SalesPipeline.objects.filter(
            stage__in=['lead', 'qualified', 'proposal', 'negotiation']
        )
        
        # Pipeline by stage
        pipeline_by_stage = opportunities.values('stage').annotate(
            count=Count('id'),
            total_value=Sum('estimated_value'),
            weighted_value=Sum(F('estimated_value') * F('probability') / 100),
            avg_probability=Avg('probability')
        ).order_by('stage')
        
        # Overdue opportunities
        overdue_opportunities = opportunities.filter(
            expected_close_date__lt=timezone.now().date()
        ).count()
        
        # This month's expected closes
        month_start = timezone.now().replace(day=1).date()
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        expected_closes = opportunities.filter(
            expected_close_date__range=[month_start, month_end]
        ).aggregate(
            count=Count('id'),
            total_value=Sum('estimated_value'),
            weighted_value=Sum(F('estimated_value') * F('probability') / 100)
        )
        
        # Top opportunities
        top_opportunities = opportunities.order_by('-weighted_value')[:10]
        
        # Sales rep performance
        rep_performance = opportunities.values(
            'sales_rep__first_name', 'sales_rep__last_name'
        ).annotate(
            opportunity_count=Count('id'),
            total_pipeline_value=Sum('estimated_value'),
            weighted_pipeline_value=Sum(F('estimated_value') * F('probability') / 100)
        ).order_by('-weighted_pipeline_value')[:10]
        
        return {
            'pipeline_by_stage': list(pipeline_by_stage),
            'total_opportunities': opportunities.count(),
            'total_pipeline_value': float(opportunities.aggregate(Sum('estimated_value'))['estimated_value__sum'] or 0),
            'weighted_pipeline_value': float(opportunities.aggregate(
                weighted=Sum(F('estimated_value') * F('probability') / 100)
            )['weighted'] or 0),
            'overdue_opportunities': overdue_opportunities,
            'expected_closes_this_month': expected_closes,
            'top_opportunities': [
                {
                    'id': opp.id,
                    'name': opp.opportunity_name,
                    'customer': opp.customer_name,
                    'value': float(opp.estimated_value),
                    'weighted_value': float(opp.weighted_value),
                    'probability': float(opp.probability),
                    'stage': opp.stage,
                    'close_date': opp.expected_close_date.strftime('%Y-%m-%d')
                }
                for opp in top_opportunities
            ],
            'rep_performance': list(rep_performance)
        }

    @staticmethod
    def forecast_pipeline_conversion(months_ahead: int = 3) -> List[Dict]:
        """
        Forecast pipeline conversion based on historical data and current opportunities.
        """
        # Get historical conversion rates by stage
        closed_won = SalesPipeline.objects.filter(stage='closed_won')
        closed_lost = SalesPipeline.objects.filter(stage='closed_lost')
        
        # Calculate conversion rates (simplified)
        total_closed = closed_won.count() + closed_lost.count()
        win_rate = (closed_won.count() / total_closed * 100) if total_closed > 0 else 50
        
        # Get current pipeline
        current_pipeline = SalesPipeline.objects.filter(
            stage__in=['lead', 'qualified', 'proposal', 'negotiation']
        )
        
        forecasts = []
        
        for month in range(1, months_ahead + 1):
            forecast_date = timezone.now().date() + timedelta(days=month * 30)
            
            # Opportunities expected to close in this month
            month_opportunities = current_pipeline.filter(
                expected_close_date__year=forecast_date.year,
                expected_close_date__month=forecast_date.month
            )
            
            total_value = month_opportunities.aggregate(Sum('estimated_value'))['estimated_value__sum'] or 0
            weighted_value = month_opportunities.aggregate(
                weighted=Sum(F('estimated_value') * F('probability') / 100)
            )['weighted'] or 0
            
            # Apply historical win rate
            forecasted_revenue = float(weighted_value) * (win_rate / 100)
            forecasted_deals = int(month_opportunities.count() * (win_rate / 100))
            
            forecasts.append({
                'month': forecast_date.strftime('%Y-%m'),
                'opportunities_count': month_opportunities.count(),
                'total_pipeline_value': float(total_value),
                'weighted_pipeline_value': float(weighted_value),
                'forecasted_revenue': round(forecasted_revenue, 2),
                'forecasted_deals': forecasted_deals,
                'win_rate_applied': round(win_rate, 2)
            })
        
        return forecasts


class SalesReportingService:
    """
    Service for automated sales reporting and alert notifications.
    """

    @staticmethod
    def generate_scheduled_reports():
        """
        Generate and send scheduled sales reports.
        """
        today = timezone.now().date()
        
        # Get reports that need to be sent today
        due_reports = SalesReport.objects.filter(
            is_active=True,
            next_send__lte=timezone.now()
        )
        
        for report in due_reports:
            try:
                # Generate report data
                report_data = SalesReportingService._generate_report_data(report)
                
                # Send report to recipients
                SalesReportingService._send_report_email(report, report_data)
                
                # Update next send date
                report.last_sent = timezone.now()
                if report.schedule == 'daily':
                    report.next_send = timezone.now() + timedelta(days=1)
                elif report.schedule == 'weekly':
                    report.next_send = timezone.now() + timedelta(weeks=1)
                elif report.schedule == 'monthly':
                    report.next_send = timezone.now() + timedelta(days=30)
                elif report.schedule == 'quarterly':
                    report.next_send = timezone.now() + timedelta(days=90)
                
                report.save()
                
            except Exception as e:
                # Log error (in production, use proper logging)
                print(f"Failed to send report {report.name}: {str(e)}")

    @staticmethod
    def _generate_report_data(report: SalesReport) -> Dict:
        """Generate report data based on report type and filters."""
        filters = report.filters
        
        if report.report_type == 'daily':
            date_from = timezone.now() - timedelta(days=1)
            date_to = timezone.now()
        elif report.report_type == 'weekly':
            date_from = timezone.now() - timedelta(weeks=1)
            date_to = timezone.now()
        elif report.report_type == 'monthly':
            date_from = timezone.now() - timedelta(days=30)
            date_to = timezone.now()
        elif report.report_type == 'quarterly':
            date_from = timezone.now() - timedelta(days=90)
            date_to = timezone.now()
        else:
            # Custom report - use filters
            date_from = filters.get('date_from', timezone.now() - timedelta(days=30))
            date_to = filters.get('date_to', timezone.now())
        
        # Generate sales dashboard data
        return SalesAnalyticsService.generate_sales_dashboard(date_from, date_to)

    @staticmethod
    def _send_report_email(report: SalesReport, report_data: Dict):
        """Send report via email to recipients."""
        if not hasattr(settings, 'EMAIL_BACKEND'):
            return
        
        subject = f"Sales Report: {report.name} - {timezone.now().strftime('%Y-%m-%d')}"
        
        # Create email content
        message = f"""
        Sales Report: {report.name}
        Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}
        
        Key Metrics:
        - Total Revenue: ${report_data.get('total_revenue', 0):,.2f}
        - Total Orders: {report_data.get('total_orders', 0):,}
        - Average Order Value: ${report_data.get('average_order_value', 0):,.2f}
        - Conversion Rate: {report_data.get('conversion_rate', 0)}%
        - Revenue Growth: {report_data.get('revenue_growth', 0)}%
        
        Period: {report_data.get('period', {}).get('from', '')} to {report_data.get('period', {}).get('to', '')}
        
        For detailed analysis, please log into the admin dashboard.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            report.recipients,
            fail_silently=True
        )

    @staticmethod
    def detect_sales_anomalies():
        """
        Detect sales anomalies and create alerts.
        """
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get yesterday's sales data
        from apps.orders.models import Order
        
        yesterday_orders = Order.objects.filter(
            created_at__date=yesterday,
            is_deleted=False
        ).exclude(status='cancelled')
        
        yesterday_metrics = yesterday_orders.aggregate(
            revenue=Sum('total_amount') or 0,
            orders=Count('id'),
            aov=Avg('total_amount') or 0
        )
        
        # Get historical average for the same day of week
        same_weekday_orders = Order.objects.filter(
            created_at__week_day=yesterday.weekday() + 1,  # Django uses 1-7 for weekdays
            created_at__date__gte=today - timedelta(days=90),  # Last 90 days
            created_at__date__lt=yesterday,
            is_deleted=False
        ).exclude(status='cancelled')
        
        historical_avg = same_weekday_orders.aggregate(
            avg_revenue=Avg('total_amount') or 0,
            avg_orders=Avg('id') or 0,
            avg_aov=Avg('total_amount') or 0
        )
        
        # Detect anomalies
        anomalies = []
        
        # Revenue anomaly
        if historical_avg['avg_revenue'] > 0:
            revenue_deviation = abs(float(yesterday_metrics['revenue']) - float(historical_avg['avg_revenue'])) / float(historical_avg['avg_revenue']) * 100
            if revenue_deviation > 25:  # 25% deviation threshold
                severity = 'high' if revenue_deviation > 50 else 'medium'
                anomalies.append({
                    'metric_type': 'revenue',
                    'actual_value': float(yesterday_metrics['revenue']),
                    'expected_value': float(historical_avg['avg_revenue']),
                    'deviation_percentage': round(revenue_deviation, 2),
                    'severity': severity
                })
        
        # Orders anomaly
        if historical_avg['avg_orders'] > 0:
            orders_deviation = abs(yesterday_metrics['orders'] - float(historical_avg['avg_orders'])) / float(historical_avg['avg_orders']) * 100
            if orders_deviation > 30:  # 30% deviation threshold
                severity = 'high' if orders_deviation > 60 else 'medium'
                anomalies.append({
                    'metric_type': 'orders',
                    'actual_value': yesterday_metrics['orders'],
                    'expected_value': float(historical_avg['avg_orders']),
                    'deviation_percentage': round(orders_deviation, 2),
                    'severity': severity
                })
        
        # Create anomaly records
        for anomaly in anomalies:
            SalesAnomalyDetection.objects.create(
                date=yesterday,
                **anomaly
            )
        
        # Send alerts for high severity anomalies
        high_severity_anomalies = [a for a in anomalies if a['severity'] == 'high']
        if high_severity_anomalies:
            SalesReportingService._send_anomaly_alerts(high_severity_anomalies, yesterday)
        
        return anomalies

    @staticmethod
    def _send_anomaly_alerts(anomalies: List[Dict], date: date):
        """Send anomaly alerts to administrators."""
        if not hasattr(settings, 'EMAIL_BACKEND'):
            return
        
        subject = f"Sales Anomaly Alert - {date.strftime('%Y-%m-%d')}"
        
        message = f"""
        Sales Anomaly Detected for {date.strftime('%Y-%m-%d')}
        
        The following high-severity anomalies were detected:
        
        """
        
        for anomaly in anomalies:
            message += f"""
        {anomaly['metric_type'].title()} Anomaly:
        - Actual Value: {anomaly['actual_value']:,.2f}
        - Expected Value: {anomaly['expected_value']:,.2f}
        - Deviation: {anomaly['deviation_percentage']}%
        - Severity: {anomaly['severity'].title()}
        
        """
        
        message += """
        Please review the sales data and investigate potential causes.
        
        Sales Analytics Team
        """
        
        # Send to administrators
        admin_emails = User.objects.filter(
            is_staff=True,
            is_active=True,
            email__isnull=False
        ).values_list('email', flat=True)
        
        if admin_emails:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                list(admin_emails),
                fail_silently=True
            )