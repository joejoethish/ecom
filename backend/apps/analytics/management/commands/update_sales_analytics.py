"""
Management command to update sales analytics data.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.db.models import Sum, Count, Avg, F
from django.db import transaction

from apps.analytics.models import (
    SalesMetrics, ProductSalesAnalytics, CustomerAnalytics, SalesAnomalyDetection
)
from apps.orders.models import Order, OrderItem
from apps.customers.models import CustomerProfile
from apps.products.models import Product


class Command(BaseCommand):
    help = 'Update sales analytics data for reporting and dashboard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to process (YYYY-MM-DD format). Defaults to yesterday.',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1,
            help='Number of days back to process. Defaults to 1.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if data already exists.',
        )

    def handle(self, *args, **options):
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD.')
                )
                return
        else:
            target_date = timezone.now().date() - timedelta(days=1)

        days_back = options['days_back']
        force_update = options['force']

        self.stdout.write(f'Updating sales analytics for {days_back} days starting from {target_date}')

        for i in range(days_back):
            process_date = target_date - timedelta(days=i)
            self.update_sales_metrics(process_date, force_update)
            self.update_product_analytics(process_date, force_update)
            self.update_customer_analytics(process_date, force_update)

        # Run anomaly detection for the latest date
        self.detect_anomalies(target_date)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated sales analytics for {days_back} days')
        )

    def update_sales_metrics(self, target_date: date, force_update: bool = False):
        """Update daily sales metrics."""
        self.stdout.write(f'Updating sales metrics for {target_date}')

        # Check if data already exists
        if not force_update and SalesMetrics.objects.filter(date=target_date).exists():
            self.stdout.write(f'Sales metrics for {target_date} already exist. Skipping.')
            return

        # Get orders for the target date
        orders = Order.objects.filter(
            created_at__date=target_date,
            is_deleted=False
        ).exclude(status='cancelled')

        if not orders.exists():
            self.stdout.write(f'No orders found for {target_date}')
            return

        # Calculate metrics
        metrics = orders.aggregate(
            total_revenue=Sum('total_amount'),
            total_orders=Count('id'),
            average_order_value=Avg('total_amount'),
            gross_margin=Sum(F('total_amount') - F('discount_amount')),
            net_profit=Sum(F('total_amount') - F('discount_amount') - F('tax_amount'))
        )

        # Count customers
        total_customers = orders.values('customer').distinct().count()
        
        # Count new customers (first order on this date)
        new_customers = 0
        for order in orders:
            first_order = Order.objects.filter(
                customer=order.customer,
                is_deleted=False
            ).exclude(status='cancelled').order_by('created_at').first()
            
            if first_order and first_order.created_at.date() == target_date:
                new_customers += 1

        # Calculate conversion rate (simplified)
        total_site_visitors = total_customers * 5  # Assume 5x visitors to customers
        conversion_rate = (total_customers / total_site_visitors * 100) if total_site_visitors > 0 else 0

        # Create or update sales metrics
        sales_metrics, created = SalesMetrics.objects.update_or_create(
            date=target_date,
            defaults={
                'total_revenue': metrics['total_revenue'] or 0,
                'total_orders': metrics['total_orders'] or 0,
                'total_customers': total_customers,
                'new_customers': new_customers,
                'average_order_value': metrics['average_order_value'] or 0,
                'gross_margin': metrics['gross_margin'] or 0,
                'net_profit': metrics['net_profit'] or 0,
                'conversion_rate': Decimal(str(conversion_rate))
            }
        )

        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} sales metrics for {target_date}')

    def update_product_analytics(self, target_date: date, force_update: bool = False):
        """Update product-level sales analytics."""
        self.stdout.write(f'Updating product analytics for {target_date}')

        # Get order items for the target date
        order_items = OrderItem.objects.filter(
            order__created_at__date=target_date,
            order__is_deleted=False
        ).exclude(order__status='cancelled')

        if not order_items.exists():
            self.stdout.write(f'No order items found for {target_date}')
            return

        # Group by product and calculate metrics
        product_data = order_items.values(
            'product_id',
            'product__name',
            'product__category_id',
            'product__category__name'
        ).annotate(
            units_sold=Sum('quantity'),
            revenue=Sum('total_price'),
            avg_unit_price=Avg('unit_price')
        )

        with transaction.atomic():
            for data in product_data:
                # Calculate cost and profit (simplified)
                try:
                    product = Product.objects.get(id=data['product_id'])
                    cost_price = getattr(product, 'cost_price', None) or (data['avg_unit_price'] * Decimal('0.6'))
                    total_cost = cost_price * data['units_sold']
                    profit = data['revenue'] - total_cost
                    profit_margin = (profit / data['revenue'] * 100) if data['revenue'] > 0 else 0
                except Product.DoesNotExist:
                    total_cost = data['revenue'] * Decimal('0.6')  # Assume 60% cost
                    profit = data['revenue'] - total_cost
                    profit_margin = 40.0  # 40% margin

                # Create or update product analytics
                ProductSalesAnalytics.objects.update_or_create(
                    product_id=data['product_id'],
                    date=target_date,
                    defaults={
                        'product_name': data['product__name'] or f'Product {data["product_id"]}',
                        'category_id': data['product__category_id'],
                        'category_name': data['product__category__name'] or 'Uncategorized',
                        'units_sold': data['units_sold'],
                        'revenue': data['revenue'],
                        'cost': total_cost,
                        'profit': profit,
                        'profit_margin': Decimal(str(profit_margin))
                    }
                )

        self.stdout.write(f'Updated product analytics for {len(product_data)} products on {target_date}')

    def update_customer_analytics(self, target_date: date, force_update: bool = False):
        """Update customer analytics."""
        self.stdout.write(f'Updating customer analytics for {target_date}')

        # Get customers who placed orders on target date
        customers_with_orders = Order.objects.filter(
            created_at__date=target_date,
            is_deleted=False
        ).exclude(status='cancelled').values_list('customer_id', flat=True).distinct()

        for customer_id in customers_with_orders:
            try:
                customer_profile = CustomerProfile.objects.get(user_id=customer_id)
                self.update_single_customer_analytics(customer_profile, target_date)
            except CustomerProfile.DoesNotExist:
                # Create basic customer profile if it doesn't exist
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=customer_id)
                    customer_profile = CustomerProfile.objects.create(user=user)
                    self.update_single_customer_analytics(customer_profile, target_date)
                except User.DoesNotExist:
                    continue

        self.stdout.write(f'Updated customer analytics for {len(customers_with_orders)} customers')

    def update_single_customer_analytics(self, customer_profile: CustomerProfile, target_date: date):
        """Update analytics for a single customer."""
        customer_orders = Order.objects.filter(
            customer=customer_profile.user,
            is_deleted=False
        ).exclude(status='cancelled')

        if not customer_orders.exists():
            return

        # Calculate customer metrics
        metrics = customer_orders.aggregate(
            total_orders=Count('id'),
            total_spent=Sum('total_amount'),
            average_order_value=Avg('total_amount')
        )

        # Get acquisition date and channel (simplified)
        first_order = customer_orders.order_by('created_at').first()
        acquisition_date = first_order.created_at.date()
        acquisition_channel = 'organic_search'  # Simplified

        # Calculate lifetime value (simplified)
        days_since_first_order = (target_date - acquisition_date).days
        if days_since_first_order > 0:
            avg_order_frequency = metrics['total_orders'] / (days_since_first_order / 30.0)  # Orders per month
            lifetime_value = metrics['average_order_value'] * avg_order_frequency * 24  # 24 months LTV
        else:
            lifetime_value = metrics['total_spent']

        # Get last order date
        last_order = customer_orders.order_by('-created_at').first()
        last_order_date = last_order.created_at.date()
        days_since_last_order = (target_date - last_order_date).days

        # Calculate churn probability (simplified)
        if days_since_last_order > 90:
            churn_probability = min(90.0, days_since_last_order / 365.0 * 100)
        else:
            churn_probability = max(0.0, days_since_last_order / 90.0 * 30)

        # Determine customer segment
        if metrics['total_orders'] >= 10 and metrics['total_spent'] >= 1000:
            customer_segment = 'vip'
        elif metrics['total_orders'] >= 5 and metrics['total_spent'] >= 500:
            customer_segment = 'loyal'
        elif metrics['total_orders'] >= 2:
            customer_segment = 'repeat'
        else:
            customer_segment = 'new'

        # Create or update customer analytics
        CustomerAnalytics.objects.update_or_create(
            customer_id=customer_profile.user.id,
            defaults={
                'customer_email': customer_profile.user.email,
                'acquisition_date': acquisition_date,
                'acquisition_channel': acquisition_channel,
                'total_orders': metrics['total_orders'],
                'total_spent': metrics['total_spent'] or 0,
                'average_order_value': metrics['average_order_value'] or 0,
                'lifetime_value': Decimal(str(lifetime_value)),
                'last_order_date': last_order_date,
                'days_since_last_order': days_since_last_order,
                'churn_probability': Decimal(str(churn_probability)),
                'customer_segment': customer_segment
            }
        )

    def detect_anomalies(self, target_date: date):
        """Detect sales anomalies for the target date."""
        self.stdout.write(f'Detecting anomalies for {target_date}')

        try:
            # Get current day's metrics
            current_metrics = SalesMetrics.objects.get(date=target_date)
        except SalesMetrics.DoesNotExist:
            self.stdout.write(f'No sales metrics found for {target_date}')
            return

        # Get historical average for the same day of week (last 8 weeks)
        weekday = target_date.weekday()
        historical_dates = []
        for i in range(1, 9):  # Last 8 weeks
            historical_date = target_date - timedelta(weeks=i)
            if historical_date.weekday() == weekday:
                historical_dates.append(historical_date)

        historical_metrics = SalesMetrics.objects.filter(
            date__in=historical_dates
        ).aggregate(
            avg_revenue=Avg('total_revenue'),
            avg_orders=Avg('total_orders'),
            avg_conversion=Avg('conversion_rate'),
            avg_aov=Avg('average_order_value')
        )

        # Check for anomalies
        anomalies = []

        # Revenue anomaly
        if historical_metrics['avg_revenue']:
            revenue_deviation = abs(
                float(current_metrics.total_revenue) - float(historical_metrics['avg_revenue'])
            ) / float(historical_metrics['avg_revenue']) * 100

            if revenue_deviation > 25:  # 25% deviation threshold
                severity = 'high' if revenue_deviation > 50 else 'medium'
                anomalies.append({
                    'metric_type': 'revenue',
                    'actual_value': float(current_metrics.total_revenue),
                    'expected_value': float(historical_metrics['avg_revenue']),
                    'deviation_percentage': Decimal(str(revenue_deviation)),
                    'severity': severity
                })

        # Orders anomaly
        if historical_metrics['avg_orders']:
            orders_deviation = abs(
                current_metrics.total_orders - float(historical_metrics['avg_orders'])
            ) / float(historical_metrics['avg_orders']) * 100

            if orders_deviation > 30:  # 30% deviation threshold
                severity = 'high' if orders_deviation > 60 else 'medium'
                anomalies.append({
                    'metric_type': 'orders',
                    'actual_value': current_metrics.total_orders,
                    'expected_value': float(historical_metrics['avg_orders']),
                    'deviation_percentage': Decimal(str(orders_deviation)),
                    'severity': severity
                })

        # Conversion rate anomaly
        if historical_metrics['avg_conversion']:
            conversion_deviation = abs(
                float(current_metrics.conversion_rate) - float(historical_metrics['avg_conversion'])
            ) / float(historical_metrics['avg_conversion']) * 100

            if conversion_deviation > 20:  # 20% deviation threshold
                severity = 'high' if conversion_deviation > 40 else 'medium'
                anomalies.append({
                    'metric_type': 'conversion',
                    'actual_value': float(current_metrics.conversion_rate),
                    'expected_value': float(historical_metrics['avg_conversion']),
                    'deviation_percentage': Decimal(str(conversion_deviation)),
                    'severity': severity
                })

        # AOV anomaly
        if historical_metrics['avg_aov']:
            aov_deviation = abs(
                float(current_metrics.average_order_value) - float(historical_metrics['avg_aov'])
            ) / float(historical_metrics['avg_aov']) * 100

            if aov_deviation > 25:  # 25% deviation threshold
                severity = 'high' if aov_deviation > 50 else 'medium'
                anomalies.append({
                    'metric_type': 'aov',
                    'actual_value': float(current_metrics.average_order_value),
                    'expected_value': float(historical_metrics['avg_aov']),
                    'deviation_percentage': Decimal(str(aov_deviation)),
                    'severity': severity
                })

        # Create anomaly records
        for anomaly in anomalies:
            SalesAnomalyDetection.objects.create(
                date=target_date,
                **anomaly
            )

        if anomalies:
            self.stdout.write(f'Detected {len(anomalies)} anomalies for {target_date}')
        else:
            self.stdout.write(f'No anomalies detected for {target_date}')