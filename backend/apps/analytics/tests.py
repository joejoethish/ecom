"""
Tests for analytics app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from apps.customers.models import Customer
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem
from .models import (
    DailySalesReport, ProductPerformanceReport, CustomerAnalytics,
    InventoryReport, SystemMetrics, ReportExport
)
from .services import AnalyticsService, ReportGenerationService
from .export_services import ReportExportService

User = get_user_model()

class DailySalesReportModelTest(TestCase):
    """
    Test cases for DailySalesReport model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.report_date = timezone.now().date()
    
    def test_create_daily_sales_report(self):
        """Test creating a daily sales report."""
        report = DailySalesReport.objects.create(
            date=self.report_date,
            total_orders=100,
            total_revenue=Decimal('10000.00'),
            total_profit=Decimal('2000.00'),
            new_customers=25,
            returning_customers=75
        )
        
        self.assertEqual(report.date, self.report_date)
        self.assertEqual(report.total_orders, 100)
        self.assertEqual(report.total_revenue, Decimal('10000.00'))
        self.assertEqual(report.total_profit, Decimal('2000.00'))
        self.assertEqual(report.new_customers, 25)
        self.assertEqual(report.returning_customers, 75)
    
    def test_generate_report_method(self):
        """Test the generate_report class method."""
        # This would require setting up orders and other data
        # For now, test that the method exists and can be called
        with patch('apps.orders.models.Order.objects') as mock_orders:
            mock_orders.filter.return_value.count.return_value = 10
            mock_orders.filter.return_value.aggregate.return_value = {
                'total_revenue': Decimal('1000.00'),
                'total_profit': Decimal('200.00')
            }
            
            report = DailySalesReport.generate_report(self.report_date)
            self.assertIsInstance(report, DailySalesReport)
            self.assertEqual(report.date, self.report_date)

class ProductPerformanceReportModelTest(TestCase):
    """
    Test cases for ProductPerformanceReport model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            sku='TEST001',
            price=Decimal('100.00'),
            category=self.category
        )
        self.report_date = timezone.now().date()
    
    def test_create_product_performance_report(self):
        """Test creating a product performance report."""
        report = ProductPerformanceReport.objects.create(
            product=self.product,
            date=self.report_date,
            units_sold=50,
            revenue=Decimal('5000.00'),
            profit=Decimal('1000.00'),
            page_views=1000,
            unique_visitors=500,
            conversion_rate=0.05
        )
        
        self.assertEqual(report.product, self.product)
        self.assertEqual(report.date, self.report_date)
        self.assertEqual(report.units_sold, 50)
        self.assertEqual(report.revenue, Decimal('5000.00'))
        self.assertEqual(report.conversion_rate, 0.05)

class CustomerAnalyticsModelTest(TestCase):
    """
    Test cases for CustomerAnalytics model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.customer = Customer.objects.create(user=self.user)
    
    def test_create_customer_analytics(self):
        """Test creating customer analytics."""
        analytics = CustomerAnalytics.objects.create(
            customer=self.customer,
            total_orders=10,
            total_spent=Decimal('1000.00'),
            average_order_value=Decimal('100.00'),
            lifecycle_stage='active',
            customer_segment='regular'
        )
        
        self.assertEqual(analytics.customer, self.customer)
        self.assertEqual(analytics.total_orders, 10)
        self.assertEqual(analytics.total_spent, Decimal('1000.00'))
        self.assertEqual(analytics.lifecycle_stage, 'active')
    
    def test_update_analytics_method(self):
        """Test the update_analytics method."""
        analytics = CustomerAnalytics.objects.create(
            customer=self.customer,
            total_orders=0,
            total_spent=Decimal('0.00')
        )
        
        # Mock order data
        with patch('apps.orders.models.Order.objects') as mock_orders:
            mock_orders.filter.return_value.count.return_value = 5
            mock_orders.filter.return_value.aggregate.return_value = {
                'total_spent': Decimal('500.00')
            }
            
            analytics.update_analytics()
            analytics.refresh_from_db()
            
            # Verify analytics were updated
            self.assertEqual(analytics.total_orders, 5)
            self.assertEqual(analytics.total_spent, Decimal('500.00'))

class AnalyticsServiceTest(TestCase):
    """
    Test cases for AnalyticsService.
    """
    
    def setUp(self):
        """Set up test data."""
        self.date_from = timezone.now() - timedelta(days=7)
        self.date_to = timezone.now()
    
    @patch('apps.analytics.services.DailySalesReport.objects')
    def test_generate_dashboard_metrics(self, mock_reports):
        """Test generating dashboard metrics."""
        # Mock report data
        mock_report = MagicMock()
        mock_report.total_revenue = Decimal('10000.00')
        mock_report.total_orders = 100
        mock_report.new_customers = 25
        mock_reports.filter.return_value = [mock_report]
        
        metrics = AnalyticsService.generate_dashboard_metrics(
            self.date_from, self.date_to
        )
        
        self.assertIn('sales', metrics)
        self.assertIn('customers', metrics)
        self.assertIn('period', metrics)
    
    @patch('apps.analytics.services.DailySalesReport.objects')
    def test_generate_sales_report(self, mock_reports):
        """Test generating sales report."""
        # Mock report data
        mock_reports.filter.return_value.aggregate.return_value = {
            'total_revenue': Decimal('10000.00'),
            'total_orders': 100
        }
        mock_reports.filter.return_value.values.return_value = []
        
        report = AnalyticsService.generate_sales_report(
            self.date_from, self.date_to
        )
        
        self.assertIn('summary', report)
        self.assertIn('daily_breakdown', report)
        self.assertIn('period', report)
    
    @patch('apps.analytics.services.ProductPerformanceReport.objects')
    def test_get_top_selling_products(self, mock_reports):
        """Test getting top-selling products."""
        # Mock product data
        mock_reports.filter.return_value.values.return_value.annotate.return_value.order_by.return_value = []
        
        products = AnalyticsService.get_top_selling_products(
            self.date_from, self.date_to, limit=10
        )
        
        self.assertIsInstance(products, list)

class AnalyticsAPITest(APITestCase):
    """
    Test cases for Analytics API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123'
        )
    
    def test_dashboard_metrics_requires_admin(self):
        """Test that dashboard metrics requires admin access."""
        url = reverse('analytics:analytics-dashboard-metrics')
        
        # Test unauthenticated access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test regular user access
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test admin access
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @patch('apps.analytics.services.AnalyticsService.generate_dashboard_metrics')
    def test_dashboard_metrics_success(self, mock_generate):
        """Test successful dashboard metrics retrieval."""
        mock_generate.return_value = {
            'sales': {'total_revenue': 10000},
            'customers': {'total_customers': 100},
            'period': {'from': '2023-01-01', 'to': '2023-01-31'}
        }
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:analytics-dashboard-metrics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sales', response.data)
        self.assertIn('customers', response.data)
    
    @patch('apps.analytics.services.AnalyticsService.generate_sales_report')
    def test_sales_report_success(self, mock_generate):
        """Test successful sales report generation."""
        mock_generate.return_value = {
            'summary': {'total_revenue': 10000},
            'daily_breakdown': [],
            'top_products': []
        }
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:analytics-sales-report')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
    
    def test_export_report_creation(self):
        """Test report export creation."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analytics:analytics-export-report')
        
        data = {
            'report_type': 'sales',
            'export_format': 'csv',
            'date_from': '2023-01-01',
            'date_to': '2023-01-31'
        }
        
        with patch('apps.analytics.services.ReportGenerationService.export_report') as mock_export:
            mock_export.return_value = ReportExport(
                id=1,
                report_type='sales',
                export_format='csv',
                export_status='processing'
            )
            
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class ReportExportServiceTest(TestCase):
    """
    Test cases for ReportExportService.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.date_from = timezone.now() - timedelta(days=7)
        self.date_to = timezone.now()
    
    @patch('apps.analytics.services.AnalyticsService.generate_sales_report')
    def test_export_sales_report_csv(self, mock_generate):
        """Test exporting sales report as CSV."""
        mock_generate.return_value = {
            'summary': {'total_revenue': 10000, 'total_orders': 100},
            'daily_breakdown': [
                {'date': '2023-01-01', 'revenue': 1000, 'orders': 10}
            ],
            'top_products': [
                {'name': 'Product 1', 'revenue': 500}
            ]
        }
        
        export = ReportExportService.export_sales_report(
            user=self.user,
            date_from=self.date_from,
            date_to=self.date_to,
            export_format='csv'
        )
        
        self.assertEqual(export.report_type, 'sales')
        self.assertEqual(export.export_format, 'csv')
        self.assertEqual(export.exported_by, self.user)
        self.assertEqual(export.export_status, 'completed')
    
    def test_generate_sales_csv_content(self):
        """Test generating CSV content for sales report."""
        report_data = {
            'summary': {'total_revenue': 10000, 'total_orders': 100},
            'daily_breakdown': [
                {'date': '2023-01-01', 'revenue': 1000, 'orders': 10}
            ],
            'top_products': [
                {'name': 'Product 1', 'revenue': 500}
            ]
        }
        
        csv_content = ReportExportService._generate_sales_csv(report_data)
        
        self.assertIsInstance(csv_content, bytes)
        content_str = csv_content.decode('utf-8')
        self.assertIn('Sales Report Summary', content_str)
        self.assertIn('Daily Sales Breakdown', content_str)
        self.assertIn('Top Products', content_str)

class SystemMetricsTest(TestCase):
    """
    Test cases for SystemMetrics model.
    """
    
    def test_create_system_metrics(self):
        """Test creating system metrics."""
        timestamp = timezone.now()
        metrics = SystemMetrics.objects.create(
            timestamp=timestamp,
            response_time_avg=150.5,
            requests_per_minute=1000,
            error_rate=0.01,
            memory_usage_percent=75.5,
            cpu_usage_percent=45.2,
            active_users=250
        )
        
        self.assertEqual(metrics.timestamp, timestamp)
        self.assertEqual(metrics.response_time_avg, 150.5)
        self.assertEqual(metrics.requests_per_minute, 1000)
        self.assertEqual(metrics.error_rate, 0.01)
        self.assertEqual(metrics.memory_usage_percent, 75.5)
        self.assertEqual(metrics.cpu_usage_percent, 45.2)
        self.assertEqual(metrics.active_users, 250)

class ReportExportModelTest(TestCase):
    """
    Test cases for ReportExport model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_report_export(self):
        """Test creating a report export."""
        export = ReportExport.objects.create(
            report_type='sales',
            export_format='csv',
            exported_by=self.user,
            export_status='processing'
        )
        
        self.assertEqual(export.report_type, 'sales')
        self.assertEqual(export.export_format, 'csv')
        self.assertEqual(export.exported_by, self.user)
        self.assertEqual(export.export_status, 'processing')
    
    def test_file_size_human_property(self):
        """Test the file_size_human property."""
        export = ReportExport.objects.create(
            report_type='sales',
            export_format='csv',
            exported_by=self.user,
            file_size=1024
        )
        
        # This would test the human-readable file size formatting
        # Implementation depends on the actual property logic
        self.assertIsNotNone(export.file_size_human)
    
    def test_is_expired_property(self):
        """Test the is_expired property."""
        # Create expired export
        expired_export = ReportExport.objects.create(
            report_type='sales',
            export_format='csv',
            exported_by=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        # Create non-expired export
        active_export = ReportExport.objects.create(
            report_type='sales',
            export_format='csv',
            exported_by=self.user,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.assertTrue(expired_export.is_expired)
        self.assertFalse(active_export.is_expired)
    
    def test_increment_download_count(self):
        """Test incrementing download count."""
        export = ReportExport.objects.create(
            report_type='sales',
            export_format='csv',
            exported_by=self.user,
            download_count=0
        )
        
        export.increment_download_count()
        export.refresh_from_db()
        
        self.assertEqual(export.download_count, 1)