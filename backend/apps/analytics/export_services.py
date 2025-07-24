"""
Report export services for generating downloadable reports.
"""
import csv
import json
import io
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.utils import timezone
from django.db.models import QuerySet
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from .models import (
    DailySalesReport, ProductPerformanceReport, CustomerAnalytics,
    InventoryReport, SystemMetrics, ReportExport
)
from .services import AnalyticsService, ReportGenerationService

class ReportExportService:
    """
    Service for exporting reports in various formats.
    """
    
    @staticmethod
    def export_sales_report(
        user,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        export_format: str = 'csv',
        filters: Dict[str, Any] = None
    ) -> ReportExport:
        """
        Export sales report in specified format.
        """
        if not date_from:
            date_from = timezone.now() - timedelta(days=30)
        if not date_to:
            date_to = timezone.now()
        
        filters = filters or {}
        
        # Generate report data
        report_data = AnalyticsService.generate_sales_report(date_from, date_to, filters)
        
        # Create export record
        export = ReportExport.objects.create(
            report_type='sales',
            export_format=export_format,
            date_from=date_from.date(),
            date_to=date_to.date(),
            filters=filters,
            exported_by=user,
            export_status='processing'
        )
        
        try:
            if export_format == 'csv':
                file_content = ReportExportService._generate_sales_csv(report_data)
                filename = f'sales_report_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.csv'
            elif export_format == 'excel':
                file_content = ReportExportService._generate_sales_excel(report_data)
                filename = f'sales_report_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.xlsx'
            elif export_format == 'pdf':
                file_content = ReportExportService._generate_sales_pdf(report_data)
                filename = f'sales_report_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.pdf'
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Save file
            file_path = f'exports/sales/{filename}'
            export.file_path = file_path
            export.file_size = len(file_content)
            export.export_status = 'completed'
            export.save()
            
            # In a real implementation, save to storage
            # For now, we'll just simulate the file save
            
            return export
            
        except Exception as e:
            export.export_status = 'failed'
            export.save()
            raise e
    
    @staticmethod
    def export_product_performance_report(
        user,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        export_format: str = 'csv',
        filters: Dict[str, Any] = None
    ) -> ReportExport:
        """
        Export product performance report.
        """
        if not date_from:
            date_from = timezone.now() - timedelta(days=30)
        if not date_to:
            date_to = timezone.now()
        
        filters = filters or {}
        
        # Get product performance data
        queryset = ProductPerformanceReport.objects.filter(
            date__range=[date_from.date(), date_to.date()]
        )
        
        if filters.get('product_id'):
            queryset = queryset.filter(product_id=filters['product_id'])
        if filters.get('category_id'):
            queryset = queryset.filter(product__category_id=filters['category_id'])
        
        products = queryset.order_by('-revenue')
        
        # Create export record
        export = ReportExport.objects.create(
            report_type='product_performance',
            export_format=export_format,
            date_from=date_from.date(),
            date_to=date_to.date(),
            filters=filters,
            exported_by=user,
            export_status='processing'
        )
        
        try:
            if export_format == 'csv':
                file_content = ReportExportService._generate_product_performance_csv(products)
                filename = f'product_performance_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.csv'
            elif export_format == 'excel':
                file_content = ReportExportService._generate_product_performance_excel(products)
                filename = f'product_performance_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.xlsx'
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Save file
            file_path = f'exports/products/{filename}'
            export.file_path = file_path
            export.file_size = len(file_content)
            export.export_status = 'completed'
            export.save()
            
            return export
            
        except Exception as e:
            export.export_status = 'failed'
            export.save()
            raise e
    
    @staticmethod
    def export_customer_analytics_report(
        user,
        export_format: str = 'csv',
        filters: Dict[str, Any] = None
    ) -> ReportExport:
        """
        Export customer analytics report.
        """
        filters = filters or {}
        
        # Get customer analytics data
        queryset = CustomerAnalytics.objects.all()
        
        if filters.get('lifecycle_stage'):
            queryset = queryset.filter(lifecycle_stage=filters['lifecycle_stage'])
        if filters.get('customer_segment'):
            queryset = queryset.filter(customer_segment=filters['customer_segment'])
        
        customers = queryset.order_by('-lifetime_value')
        
        # Create export record
        export = ReportExport.objects.create(
            report_type='customer_analytics',
            export_format=export_format,
            filters=filters,
            exported_by=user,
            export_status='processing'
        )
        
        try:
            if export_format == 'csv':
                file_content = ReportExportService._generate_customer_analytics_csv(customers)
                filename = f'customer_analytics_{timezone.now().strftime("%Y%m%d")}.csv'
            elif export_format == 'excel':
                file_content = ReportExportService._generate_customer_analytics_excel(customers)
                filename = f'customer_analytics_{timezone.now().strftime("%Y%m%d")}.xlsx'
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Save file
            file_path = f'exports/customers/{filename}'
            export.file_path = file_path
            export.file_size = len(file_content)
            export.export_status = 'completed'
            export.save()
            
            return export
            
        except Exception as e:
            export.export_status = 'failed'
            export.save()
            raise e
    
    @staticmethod
    def export_inventory_report(
        user,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        export_format: str = 'csv'
    ) -> ReportExport:
        """
        Export inventory report.
        """
        if not date_from:
            date_from = timezone.now() - timedelta(days=30)
        if not date_to:
            date_to = timezone.now()
        
        # Get inventory data
        reports = InventoryReport.objects.filter(
            date__range=[date_from.date(), date_to.date()]
        ).order_by('-date')
        
        # Create export record
        export = ReportExport.objects.create(
            report_type='inventory',
            export_format=export_format,
            date_from=date_from.date(),
            date_to=date_to.date(),
            exported_by=user,
            export_status='processing'
        )
        
        try:
            if export_format == 'csv':
                file_content = ReportExportService._generate_inventory_csv(reports)
                filename = f'inventory_report_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.csv'
            elif export_format == 'excel':
                file_content = ReportExportService._generate_inventory_excel(reports)
                filename = f'inventory_report_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.xlsx'
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Save file
            file_path = f'exports/inventory/{filename}'
            export.file_path = file_path
            export.file_size = len(file_content)
            export.export_status = 'completed'
            export.save()
            
            return export
            
        except Exception as e:
            export.export_status = 'failed'
            export.save()
            raise e
    
    @staticmethod
    def _generate_sales_csv(report_data: Dict[str, Any]) -> bytes:
        """
        Generate CSV content for sales report.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write summary section
        writer.writerow(['Sales Report Summary'])
        writer.writerow(['Metric', 'Value'])
        summary = report_data.get('summary', {})
        for key, value in summary.items():
            writer.writerow([key.replace('_', ' ').title(), value])
        
        writer.writerow([])  # Empty row
        
        # Write daily breakdown
        writer.writerow(['Daily Sales Breakdown'])
        daily_data = report_data.get('daily_breakdown', [])
        if daily_data:
            headers = list(daily_data[0].keys())
            writer.writerow(headers)
            for row in daily_data:
                writer.writerow([row.get(header, '') for header in headers])
        
        writer.writerow([])  # Empty row
        
        # Write top products
        writer.writerow(['Top Products'])
        top_products = report_data.get('top_products', [])
        if top_products:
            headers = list(top_products[0].keys())
            writer.writerow(headers)
            for row in top_products:
                writer.writerow([row.get(header, '') for header in headers])
        
        content = output.getvalue()
        output.close()
        return content.encode('utf-8')
    
    @staticmethod
    def _generate_product_performance_csv(products: QuerySet) -> bytes:
        """
        Generate CSV content for product performance report.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'Product Name', 'SKU', 'Category', 'Date', 'Units Sold',
            'Revenue', 'Profit', 'Page Views', 'Unique Visitors',
            'Add to Cart Count', 'Wishlist Count', 'Conversion Rate',
            'Cart Abandonment Rate', 'New Reviews', 'Average Rating'
        ]
        writer.writerow(headers)
        
        # Write data
        for product in products:
            writer.writerow([
                product.product.name,
                product.product.sku,
                product.product.category.name if product.product.category else '',
                product.date,
                product.units_sold,
                product.revenue,
                product.profit,
                product.page_views,
                product.unique_visitors,
                product.add_to_cart_count,
                product.wishlist_count,
                f"{product.conversion_rate:.2%}" if product.conversion_rate else '',
                f"{product.cart_abandonment_rate:.2%}" if product.cart_abandonment_rate else '',
                product.new_reviews,
                f"{product.average_rating:.1f}" if product.average_rating else ''
            ])
        
        content = output.getvalue()
        output.close()
        return content.encode('utf-8')
    
    @staticmethod
    def _generate_customer_analytics_csv(customers: QuerySet) -> bytes:
        """
        Generate CSV content for customer analytics report.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'Customer Email', 'Customer Name', 'Total Orders', 'Total Spent',
            'Average Order Value', 'Last Order Date', 'Total Sessions',
            'Total Page Views', 'Average Session Duration', 'Last Activity Date',
            'Favorite Categories', 'Favorite Brands', 'Lifecycle Stage',
            'Customer Segment', 'Lifetime Value', 'Predicted Churn Probability'
        ]
        writer.writerow(headers)
        
        # Write data
        for customer in customers:
            user = customer.customer.user
            customer_name = f"{user.first_name} {user.last_name}".strip() or user.email
            
            writer.writerow([
                user.email,
                customer_name,
                customer.total_orders,
                customer.total_spent,
                customer.average_order_value,
                customer.last_order_date,
                customer.total_sessions,
                customer.total_page_views,
                customer.average_session_duration,
                customer.last_activity_date,
                ', '.join(customer.favorite_categories) if customer.favorite_categories else '',
                ', '.join(customer.favorite_brands) if customer.favorite_brands else '',
                customer.lifecycle_stage,
                customer.customer_segment,
                customer.lifetime_value,
                f"{customer.predicted_churn_probability:.2%}" if customer.predicted_churn_probability else ''
            ])
        
        content = output.getvalue()
        output.close()
        return content.encode('utf-8')
    
    @staticmethod
    def _generate_inventory_csv(reports: QuerySet) -> bytes:
        """
        Generate CSV content for inventory report.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'Date', 'Total Products', 'In Stock Products', 'Low Stock Products',
            'Out of Stock Products', 'Total Inventory Value', 'Total Cost Value',
            'Total Stock In', 'Total Stock Out', 'Total Adjustments',
            'Inventory Turnover Rate', 'Dead Stock Value'
        ]
        writer.writerow(headers)
        
        # Write data
        for report in reports:
            writer.writerow([
                report.date,
                report.total_products,
                report.in_stock_products,
                report.low_stock_products,
                report.out_of_stock_products,
                report.total_inventory_value,
                report.total_cost_value,
                report.total_stock_in,
                report.total_stock_out,
                report.total_adjustments,
                f"{report.inventory_turnover_rate:.2f}" if report.inventory_turnover_rate else '',
                report.dead_stock_value
            ])
        
        content = output.getvalue()
        output.close()
        return content.encode('utf-8')
    
    @staticmethod
    def _generate_sales_excel(report_data: Dict[str, Any]) -> bytes:
        """
        Generate Excel content for sales report.
        """
        # This would use openpyxl or xlsxwriter to create Excel files
        # For now, return CSV content as placeholder
        return ReportExportService._generate_sales_csv(report_data)
    
    @staticmethod
    def _generate_product_performance_excel(products: QuerySet) -> bytes:
        """
        Generate Excel content for product performance report.
        """
        # This would use openpyxl or xlsxwriter to create Excel files
        # For now, return CSV content as placeholder
        return ReportExportService._generate_product_performance_csv(products)
    
    @staticmethod
    def _generate_customer_analytics_excel(customers: QuerySet) -> bytes:
        """
        Generate Excel content for customer analytics report.
        """
        # This would use openpyxl or xlsxwriter to create Excel files
        # For now, return CSV content as placeholder
        return ReportExportService._generate_customer_analytics_csv(customers)
    
    @staticmethod
    def _generate_inventory_excel(reports: QuerySet) -> bytes:
        """
        Generate Excel content for inventory report.
        """
        # This would use openpyxl or xlsxwriter to create Excel files
        # For now, return CSV content as placeholder
        return ReportExportService._generate_inventory_csv(reports)
    
    @staticmethod
    def _generate_sales_pdf(report_data: Dict[str, Any]) -> bytes:
        """
        Generate PDF content for sales report.
        """
        # This would use reportlab or weasyprint to create PDF files
        # For now, return a simple text representation
        content = f"Sales Report\\n\\nSummary: {report_data.get('summary', {})}\\n"
        return content.encode('utf-8')