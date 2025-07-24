"""
Analytics API views for admin reporting and dashboard.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.http import HttpResponse, Http404
from datetime import datetime, timedelta
from typing import Dict, Any
import io
import csv
import json

from core.permissions import IsAdminUser
from .models import (
    DailySalesReport, ProductPerformanceReport, CustomerAnalytics,
    InventoryReport, SystemMetrics, ReportExport
)
from .serializers import (
    DailySalesReportSerializer, ProductPerformanceReportSerializer,
    CustomerAnalyticsSerializer, InventoryReportSerializer,
    SystemMetricsSerializer, ReportExportSerializer,
    DashboardMetricsSerializer, SalesReportSerializer,
    ProfitLossReportSerializer, TopSellingProductSerializer,
    CustomerAnalyticsSummarySerializer, StockMaintenanceReportSerializer,
    SystemHealthSummarySerializer, ReportExportRequestSerializer,
    ReportFilterSerializer
)
from .services import (
    AnalyticsService, ReportGenerationService, SystemMonitoringService
)


class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for analytics and reporting endpoints.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'])
    def dashboard_metrics(self, request):
        """
        Get key metrics for admin dashboard.
        """
        # Parse date parameters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        if date_to:
            date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))

        try:
            metrics = AnalyticsService.generate_dashboard_metrics(date_from, date_to)
            serializer = DashboardMetricsSerializer(metrics)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate dashboard metrics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sales_report(self, request):
        """
        Generate comprehensive sales report.
        """
        filter_serializer = ReportFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filters = filter_serializer.validated_data
        date_from = filters.get('date_from', timezone.now() - timedelta(days=30))
        date_to = filters.get('date_to', timezone.now())

        # Extract additional filters
        report_filters = {
            'category': filters.get('category'),
            'product': filters.get('product'),
            'order_status': filters.get('order_status'),
            'payment_method': filters.get('payment_method'),
        }
        # Remove None values
        report_filters = {k: v for k, v in report_filters.items() if v is not None}

        try:
            report = AnalyticsService.generate_sales_report(date_from, date_to, report_filters)
            serializer = SalesReportSerializer(report)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate sales report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def profit_loss_report(self, request):
        """
        Generate profit and loss report.
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if not date_from or not date_to:
            return Response(
                {'error': 'date_from and date_to parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use ISO format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            report = AnalyticsService.generate_profit_loss_report(date_from, date_to)
            serializer = ProfitLossReportSerializer(report)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate profit/loss report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def top_selling_products(self, request):
        """
        Get top-selling products report.
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        limit = int(request.query_params.get('limit', 10))

        if date_from:
            date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        if date_to:
            date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))

        try:
            products = AnalyticsService.get_top_selling_products(date_from, date_to, limit)
            serializer = TopSellingProductSerializer(products, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get top-selling products: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def daily_sales_reports(self, request):
        """
        Get daily sales reports with filtering.
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = DailySalesReport.objects.all()
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        queryset = queryset.order_by('-date')[:30]  # Limit to 30 days
        serializer = DailySalesReportSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stock_maintenance_report(self, request):
        """
        Generate stock maintenance report.
        """
        try:
            report = ReportGenerationService.get_stock_maintenance_report()
            serializer = StockMaintenanceReportSerializer(report)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate stock maintenance report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def customer_analytics_summary(self, request):
        """
        Get customer analytics summary.
        """
        try:
            summary = AnalyticsService.get_customer_analytics_summary()
            serializer = CustomerAnalyticsSummarySerializer(summary)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get customer analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def system_health(self, request):
        """
        Get system health and monitoring summary.
        """
        hours = int(request.query_params.get('hours', 24))
        
        try:
            health = SystemMonitoringService.get_system_health_summary(hours)
            serializer = SystemHealthSummarySerializer(health)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get system health: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def export_report(self, request):
        """
        Create a report export job.
        """
        serializer = ReportExportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        
        try:
            export = ReportGenerationService.export_report(
                report_type=data['report_type'],
                export_format=data['export_format'],
                user=request.user,
                date_from=data.get('date_from'),
                date_to=data.get('date_to'),
                filters=data.get('filters', {})
            )
            
            export_serializer = ReportExportSerializer(export)
            return Response(export_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to create export: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def export_history(self, request):
        """
        Get user's export history.
        """
        exports = ReportExport.objects.filter(
            exported_by=request.user
        ).order_by('-created_at')[:20]
        
        serializer = ReportExportSerializer(exports, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def download_export(self, request):
        """
        Download an exported report file.
        """
        export_id = request.query_params.get('export_id')
        if not export_id:
            return Response(
                {'error': 'export_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            export = ReportExport.objects.get(
                id=export_id,
                exported_by=request.user,
                export_status='completed'
            )
            
            if export.is_expired:
                return Response(
                    {'error': 'Export has expired'},
                    status=status.HTTP_410_GONE
                )

            # In a real implementation, this would serve the actual file
            # For now, return a placeholder response
            export.increment_download_count()
            
            return Response({
                'message': 'File download would start here',
                'file_path': export.file_path,
                'file_size': export.file_size_human
            })
            
        except ReportExport.DoesNotExist:
            raise Http404("Export not found")

    @action(detail=False, methods=['post'])
    def generate_daily_reports(self, request):
        """
        Manually trigger daily report generation.
        """
        date_str = request.data.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = timezone.now().date() - timedelta(days=1)

        try:
            # Generate daily sales report
            sales_report = DailySalesReport.generate_report(target_date)
            
            # Generate inventory report
            inventory_report = InventoryReport.generate_report(target_date)
            
            return Response({
                'message': f'Daily reports generated for {target_date}',
                'sales_report_id': sales_report.id,
                'inventory_report_id': inventory_report.id
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to generate daily reports: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DailySalesReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for daily sales reports.
    """
    queryset = DailySalesReport.objects.all().order_by('-date')
    serializer_class = DailySalesReportSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset


class ProductPerformanceReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for product performance reports.
    """
    queryset = ProductPerformanceReport.objects.all().order_by('-date', '-revenue')
    serializer_class = ProductPerformanceReportSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        product_id = self.request.query_params.get('product_id')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset


class CustomerAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for customer analytics.
    """
    queryset = CustomerAnalytics.objects.all().order_by('-lifetime_value')
    serializer_class = CustomerAnalyticsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        lifecycle_stage = self.request.query_params.get('lifecycle_stage')
        customer_segment = self.request.query_params.get('customer_segment')
        
        if lifecycle_stage:
            queryset = queryset.filter(lifecycle_stage=lifecycle_stage)
        if customer_segment:
            queryset = queryset.filter(customer_segment=customer_segment)
            
        return queryset

    @action(detail=True, methods=['post'])
    def update_analytics(self, request, pk=None):
        """
        Manually update analytics for a specific customer.
        """
        analytics = self.get_object()
        try:
            analytics.update_analytics()
            serializer = self.get_serializer(analytics)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to update analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for inventory reports.
    """
    queryset = InventoryReport.objects.all().order_by('-date')
    serializer_class = InventoryReportSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset


class SystemMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for system metrics.
    """
    queryset = SystemMetrics.objects.all().order_by('-timestamp')
    serializer_class = SystemMetricsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        
        hours = int(self.request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        return queryset.filter(timestamp__gte=since)

    @action(detail=False, methods=['post'])
    def record_metrics(self, request):
        """
        Record new system metrics.
        """
        serializer = SystemMetricsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportExportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for report exports.
    """
    serializer_class = ReportExportSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Get exports for current user."""
        return ReportExport.objects.filter(
            exported_by=self.request.user
        ).order_by('-created_at')

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download exported report file.
        """
        export = self.get_object()
        
        if export.export_status != 'completed':
            return Response(
                {'error': 'Export is not ready for download'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if export.is_expired:
            return Response(
                {'error': 'Export has expired'},
                status=status.HTTP_410_GONE
            )

        # In a real implementation, this would serve the actual file
        export.increment_download_count()
        
        return Response({
            'message': 'File download would start here',
            'file_path': export.file_path,
            'file_size': export.file_size_human
        })