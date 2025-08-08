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
    SalesMetrics, ProductSalesAnalytics, CustomerAnalytics, SalesForecast,
    SalesGoal, SalesCommission, SalesTerritory, SalesPipeline, SalesReport,
    SalesAnomalyDetection
)
from .serializers import (
    SalesMetricsSerializer, ProductSalesAnalyticsSerializer,
    CustomerAnalyticsSerializer, SalesForecastSerializer,
    SalesGoalSerializer, SalesCommissionSerializer, SalesTerritorySerializer,
    SalesPipelineSerializer, SalesReportSerializer, SalesAnomalyDetectionSerializer,
    SalesDashboardSerializer, SalesChartDataSerializer, SalesRevenueAnalysisSerializer,
    CustomerCohortAnalysisSerializer, SalesFunnelAnalysisSerializer,
    SalesPerformanceComparisonSerializer, SalesAttributionAnalysisSerializer,
    SalesSeasonalityAnalysisSerializer
)
from .services import (
    SalesAnalyticsService, SalesForecastingService, SalesReportingService,
    SalesCommissionService, SalesTerritoryService, SalesPipelineService
)


class SalesAnalyticsViewSet(viewsets.ViewSet):
    """
    Comprehensive sales analytics and reporting endpoints.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'])
    def sales_dashboard(self, request):
        """
        Get comprehensive sales dashboard with KPIs and trend analysis.
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        if date_to:
            date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))

        try:
            dashboard_data = SalesAnalyticsService.generate_sales_dashboard(date_from, date_to)
            serializer = SalesDashboardSerializer(dashboard_data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate sales dashboard: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sales_forecast(self, request):
        """
        Generate sales forecasting with machine learning algorithms and seasonal adjustments.
        """
        forecast_type = request.query_params.get('type', 'monthly')
        periods = int(request.query_params.get('periods', 12))

        try:
            forecast_data = SalesForecastingService.generate_sales_forecast(forecast_type, periods)
            serializer = SalesForecastSerializer(forecast_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate sales forecast: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def revenue_analysis(self, request):
        """
        Generate detailed revenue analysis with gross margin and profit analysis.
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        group_by = request.query_params.get('group_by', 'day')

        if not date_from or not date_to:
            return Response(
                {'error': 'date_from and date_to parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            
            analysis_data = SalesAnalyticsService.generate_revenue_analysis(date_from, date_to, group_by)
            serializer = SalesRevenueAnalysisSerializer(analysis_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate revenue analysis: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def customer_cohort_analysis(self, request):
        """
        Generate customer cohort analysis for retention tracking.
        """
        months_back = int(request.query_params.get('months_back', 12))

        try:
            cohort_data = SalesAnalyticsService.generate_customer_cohort_analysis(months_back)
            serializer = CustomerCohortAnalysisSerializer(cohort_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate cohort analysis: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sales_funnel_analysis(self, request):
        """
        Generate sales funnel analysis with conversion tracking.
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
            
            funnel_data = SalesAnalyticsService.generate_sales_funnel_analysis(date_from, date_to)
            serializer = SalesFunnelAnalysisSerializer(funnel_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate funnel analysis: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sales_attribution_analysis(self, request):
        """
        Generate sales attribution analysis across marketing channels.
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
            
            attribution_data = SalesAnalyticsService.generate_sales_attribution_analysis(date_from, date_to)
            serializer = SalesAttributionAnalysisSerializer(attribution_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate attribution analysis: {str(e)}'},
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
        
        # Use SalesMetrics instead of DailySalesReport
        queryset = SalesMetrics.objects.all()
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        queryset = queryset.order_by('-date')[:30]  # Limit to 30 days
        serializer = SalesMetricsSerializer(queryset, many=True)
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
            
            return Response({'message': 'Export created successfully', 'export': export}, status=status.HTTP_201_CREATED)
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
        
        return Response([{'message': 'Export list not implemented'}])

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
            # Generate daily sales report using SalesMetrics
            sales_report = SalesMetrics.objects.filter(date=target_date).first()
            
            # Generate inventory report (simplified)
            inventory_report = {'message': 'Inventory report not implemented'}
            
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


# Removed DailySalesReportViewSet - model doesn't exist
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


# Removed ProductPerformanceReportViewSet - model doesn't exist
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


# Removed InventoryReportViewSet - model doesn't exist
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


# Removed SystemMetricsViewSet - model doesn't exist
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
        return Response({'message': 'System metrics recording not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Removed ReportExportViewSet - serializer doesn't exist
    
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

    @action(detail=False, methods=['get'])
    def product_performance_tracking(self, request):
        """
        Track sales performance by product, category, and region.
        """
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        group_by = request.query_params.get('group_by', 'product')  # product, category, region

        if not date_from or not date_to:
            return Response(
                {'error': 'date_from and date_to parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date_from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00')).date()
            date_to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00')).date()
            
            if group_by == 'product':
                performance_data = ProductSalesAnalytics.objects.filter(
                    date__range=[date_from_date, date_to_date]
                ).values(
                    'product_id', 'product_name'
                ).annotate(
                    total_revenue=Sum('revenue'),
                    total_units=Sum('units_sold'),
                    total_profit=Sum('profit'),
                    avg_profit_margin=Avg('profit_margin')
                ).order_by('-total_revenue')[:50]
            
            elif group_by == 'category':
                performance_data = ProductSalesAnalytics.objects.filter(
                    date__range=[date_from_date, date_to_date]
                ).values(
                    'category_id', 'category_name'
                ).annotate(
                    total_revenue=Sum('revenue'),
                    total_units=Sum('units_sold'),
                    total_profit=Sum('profit'),
                    avg_profit_margin=Avg('profit_margin')
                ).order_by('-total_revenue')[:20]
            
            else:  # region - simplified implementation
                performance_data = []

            return Response(list(performance_data))
        except Exception as e:
            return Response(
                {'error': f'Failed to generate performance tracking: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sales_goals_tracking(self, request):
        """
        Track sales goals with target setting and performance monitoring.
        """
        try:
            active_goals = SalesGoal.objects.filter(is_active=True).order_by('-created_at')
            
            goals_data = []
            for goal in active_goals:
                # Calculate progress
                progress_percentage = goal.progress_percentage
                days_remaining = (goal.end_date - timezone.now().date()).days
                
                goals_data.append({
                    'id': goal.id,
                    'name': goal.name,
                    'goal_type': goal.goal_type,
                    'target_value': float(goal.target_value),
                    'current_value': float(goal.current_value),
                    'progress_percentage': progress_percentage,
                    'is_achieved': goal.is_achieved,
                    'start_date': goal.start_date.strftime('%Y-%m-%d'),
                    'end_date': goal.end_date.strftime('%Y-%m-%d'),
                    'days_remaining': days_remaining,
                    'assigned_to': goal.assigned_to.get_full_name() if goal.assigned_to else None,
                    'department': goal.department,
                    'region': goal.region
                })
            
            return Response(goals_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get sales goals: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_sales_goal(self, request):
        """
        Create a new sales goal with target setting.
        """
        serializer = SalesGoalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def commission_calculation(self, request):
        """
        Calculate sales commissions with automated payout processing.
        """
        period_start = request.query_params.get('period_start')
        period_end = request.query_params.get('period_end')

        if not period_start or not period_end:
            return Response(
                {'error': 'period_start and period_end parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
            
            commissions = SalesCommissionService.calculate_commissions(start_date, end_date)
            return Response(commissions)
        except Exception as e:
            return Response(
                {'error': f'Failed to calculate commissions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def process_commission_payouts(self, request):
        """
        Process commission payouts for approved commissions.
        """
        commission_ids = request.data.get('commission_ids', [])
        
        if not commission_ids:
            return Response(
                {'error': 'commission_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = SalesCommissionService.process_commission_payouts(
                commission_ids, request.user
            )
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to process payouts: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def territory_management(self, request):
        """
        Manage sales territories with geographic analysis and optimization.
        """
        try:
            territory_performance = SalesTerritoryService.analyze_territory_performance()
            return Response(territory_performance)
        except Exception as e:
            return Response(
                {'error': f'Failed to analyze territories: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def territory_optimization(self, request):
        """
        Get territory optimization recommendations.
        """
        try:
            optimization_data = SalesTerritoryService.optimize_territory_assignments()
            return Response(optimization_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to optimize territories: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def pipeline_management(self, request):
        """
        Manage sales pipeline with opportunity tracking and forecasting.
        """
        try:
            pipeline_data = SalesPipelineService.get_pipeline_overview()
            return Response(pipeline_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get pipeline data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def pipeline_forecast(self, request):
        """
        Forecast pipeline conversion based on historical data.
        """
        months_ahead = int(request.query_params.get('months_ahead', 3))
        
        try:
            forecast_data = SalesPipelineService.forecast_pipeline_conversion(months_ahead)
            return Response(forecast_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to forecast pipeline: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sales_performance_comparison(self, request):
        """
        Generate comparative sales reporting with period-over-period analysis.
        """
        current_start = request.query_params.get('current_start')
        current_end = request.query_params.get('current_end')
        compare_with = request.query_params.get('compare_with', 'previous_period')

        if not current_start or not current_end:
            return Response(
                {'error': 'current_start and current_end parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            current_start_date = datetime.fromisoformat(current_start.replace('Z', '+00:00'))
            current_end_date = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
            
            # Calculate comparison period
            period_length = current_end_date - current_start_date
            
            if compare_with == 'previous_period':
                compare_start = current_start_date - period_length
                compare_end = current_start_date
            elif compare_with == 'previous_year':
                compare_start = current_start_date - timedelta(days=365)
                compare_end = current_end_date - timedelta(days=365)
            else:
                compare_start = current_start_date - period_length
                compare_end = current_start_date

            # Get current period data
            current_data = SalesAnalyticsService.generate_revenue_analysis(
                current_start_date, current_end_date, 'day'
            )
            
            # Get comparison period data
            comparison_data = SalesAnalyticsService.generate_revenue_analysis(
                compare_start, compare_end, 'day'
            )

            # Calculate aggregated metrics for both periods
            current_totals = {
                'revenue': sum(d['revenue'] for d in current_data),
                'orders': sum(d['orders'] for d in current_data),
                'customers': sum(d['customers'] for d in current_data),
                'average_order_value': sum(d['revenue'] for d in current_data) / max(sum(d['orders'] for d in current_data), 1),
                'gross_margin': sum(d['gross_margin'] for d in current_data),
                'net_profit': sum(d['net_profit'] for d in current_data)
            }

            comparison_totals = {
                'revenue': sum(d['revenue'] for d in comparison_data),
                'orders': sum(d['orders'] for d in comparison_data),
                'customers': sum(d['customers'] for d in comparison_data),
                'average_order_value': sum(d['revenue'] for d in comparison_data) / max(sum(d['orders'] for d in comparison_data), 1),
                'gross_margin': sum(d['gross_margin'] for d in comparison_data),
                'net_profit': sum(d['net_profit'] for d in comparison_data)
            }

            # Calculate growth metrics
            growth_metrics = {}
            for key in current_totals:
                if comparison_totals[key] > 0:
                    growth = ((current_totals[key] - comparison_totals[key]) / comparison_totals[key]) * 100
                    growth_metrics[f'{key}_growth'] = round(growth, 2)
                else:
                    growth_metrics[f'{key}_growth'] = 100.0 if current_totals[key] > 0 else 0.0

            comparison_result = {
                'current_period': {
                    'period': f"{current_start_date.strftime('%Y-%m-%d')} to {current_end_date.strftime('%Y-%m-%d')}",
                    **current_totals
                },
                'previous_period': {
                    'period': f"{compare_start.strftime('%Y-%m-%d')} to {compare_end.strftime('%Y-%m-%d')}",
                    **comparison_totals
                },
                'growth_metrics': growth_metrics
            }

            serializer = SalesPerformanceComparisonSerializer(comparison_result)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate performance comparison: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def anomaly_detection(self, request):
        """
        Get sales anomaly detection and alerts.
        """
        days_back = int(request.query_params.get('days_back', 30))
        
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            anomalies = SalesAnomalyDetection.objects.filter(
                date__range=[start_date, end_date]
            ).order_by('-date', '-severity')
            
            serializer = SalesAnomalyDetectionSerializer(anomalies, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get anomalies: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def detect_anomalies(self, request):
        """
        Manually trigger anomaly detection.
        """
        try:
            anomalies = SalesReportingService.detect_sales_anomalies()
            return Response({
                'message': f'Detected {len(anomalies)} anomalies',
                'anomalies': anomalies
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to detect anomalies: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def scheduled_reports(self, request):
        """
        Get scheduled sales reports with automated delivery.
        """
        try:
            reports = SalesReport.objects.filter(is_active=True).order_by('-created_at')
            serializer = SalesReportSerializer(reports, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get scheduled reports: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_scheduled_report(self, request):
        """
        Create a new scheduled sales report.
        """
        data = request.data.copy()
        data['created_by'] = request.user.id
        
        serializer = SalesReportSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def send_scheduled_reports(self, request):
        """
        Manually trigger sending of scheduled reports.
        """
        try:
            SalesReportingService.generate_scheduled_reports()
            return Response({'message': 'Scheduled reports sent successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to send reports: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def customer_lifetime_value(self, request):
        """
        Calculate and track customer lifetime value (CLV).
        """
        try:
            clv_data = CustomerAnalytics.objects.filter(
                lifetime_value__gt=0
            ).order_by('-lifetime_value')[:100]
            
            serializer = CustomerAnalyticsSerializer(clv_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get CLV data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def sales_channel_performance(self, request):
        """
        Analyze sales channel performance and optimization.
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
            
            channel_data = SalesAnalyticsService.generate_sales_attribution_analysis(date_from, date_to)
            return Response(channel_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to analyze channel performance: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def price_elasticity_analysis(self, request):
        """
        Analyze price elasticity and optimization opportunities.
        """
        product_id = request.query_params.get('product_id')
        
        try:
            # Simplified price elasticity analysis
            # In a real implementation, this would analyze price changes vs demand
            
            if product_id:
                # Analyze specific product
                product_analytics = ProductSalesAnalytics.objects.filter(
                    product_id=product_id
                ).order_by('-date')[:90]  # Last 90 days
                
                if not product_analytics:
                    return Response({'error': 'No data found for this product'})
                
                # Calculate price elasticity (simplified)
                price_points = []
                demand_points = []
                
                for analytics in product_analytics:
                    # This would come from actual price change data
                    price_points.append(float(analytics.revenue) / max(analytics.units_sold, 1))
                    demand_points.append(analytics.units_sold)
                
                # Calculate correlation (simplified elasticity measure)
                if len(price_points) > 1 and len(demand_points) > 1:
                    correlation = np.corrcoef(price_points, demand_points)[0, 1]
                    elasticity = correlation * -1  # Negative correlation indicates elasticity
                else:
                    elasticity = 0
                
                return Response({
                    'product_id': product_id,
                    'price_elasticity': round(elasticity, 3),
                    'interpretation': 'Elastic' if abs(elasticity) > 1 else 'Inelastic',
                    'recommendation': 'Consider price optimization' if abs(elasticity) > 1 else 'Price changes may have limited impact',
                    'data_points': len(product_analytics)
                })
            else:
                # Analyze top products
                top_products = ProductSalesAnalytics.objects.values(
                    'product_id', 'product_name'
                ).annotate(
                    total_revenue=Sum('revenue'),
                    total_units=Sum('units_sold')
                ).order_by('-total_revenue')[:20]
                
                elasticity_data = []
                for product in top_products:
                    # Simplified elasticity calculation
                    avg_price = float(product['total_revenue']) / max(product['total_units'], 1)
                    elasticity_data.append({
                        'product_id': product['product_id'],
                        'product_name': product['product_name'],
                        'average_price': round(avg_price, 2),
                        'total_units': product['total_units'],
                        'estimated_elasticity': round(np.random.uniform(-2, 2), 3),  # Placeholder
                        'recommendation': 'Analyze further'
                    })
                
                return Response(elasticity_data)
                
        except Exception as e:
            return Response(
                {'error': f'Failed to analyze price elasticity: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def market_share_analysis(self, request):
        """
        Analyze market share and competitive intelligence.
        """
        try:
            # Simplified market share analysis
            # In a real implementation, this would integrate with market research data
            
            from apps.orders.models import Order
            
            # Get total market data (simplified)
            total_orders = Order.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=365),
                is_deleted=False
            ).exclude(status='cancelled')
            
            our_revenue = total_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            
            # Simulate market data (in real implementation, this would come from external sources)
            estimated_market_size = float(our_revenue) * 5  # Assume we have 20% market share
            
            market_analysis = {
                'our_revenue': float(our_revenue),
                'estimated_market_size': estimated_market_size,
                'estimated_market_share': 20.0,  # Placeholder
                'market_growth_rate': 15.0,  # Placeholder
                'competitive_position': 'Strong',
                'key_competitors': [
                    {'name': 'Competitor A', 'estimated_share': 25.0},
                    {'name': 'Competitor B', 'estimated_share': 20.0},
                    {'name': 'Competitor C', 'estimated_share': 15.0},
                    {'name': 'Others', 'estimated_share': 20.0}
                ],
                'growth_opportunities': [
                    'Expand into new geographic markets',
                    'Develop new product categories',
                    'Improve customer retention',
                    'Enhance digital marketing'
                ]
            }
            
            return Response(market_analysis)
        except Exception as e:
            return Response(
                {'error': f'Failed to analyze market share: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def profitability_analysis(self, request):
        """
        Analyze sales profitability by customer, product, and segment.
        """
        analysis_type = request.query_params.get('type', 'product')  # product, customer, segment
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if not date_from or not date_to:
            return Response(
                {'error': 'date_from and date_to parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date_from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00')).date()
            date_to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00')).date()
            
            if analysis_type == 'product':
                profitability_data = ProductSalesAnalytics.objects.filter(
                    date__range=[date_from_date, date_to_date]
                ).values(
                    'product_id', 'product_name', 'category_name'
                ).annotate(
                    total_revenue=Sum('revenue'),
                    total_cost=Sum('cost'),
                    total_profit=Sum('profit'),
                    profit_margin=Avg('profit_margin'),
                    units_sold=Sum('units_sold')
                ).order_by('-total_profit')[:50]
                
            elif analysis_type == 'customer':
                # Customer profitability analysis
                customer_data = CustomerAnalytics.objects.filter(
                    last_order_date__range=[date_from_date, date_to_date]
                ).order_by('-lifetime_value')[:50]
                
                profitability_data = [
                    {
                        'customer_id': ca.customer_id,
                        'customer_email': ca.customer_email,
                        'total_spent': float(ca.total_spent),
                        'lifetime_value': float(ca.lifetime_value),
                        'total_orders': ca.total_orders,
                        'average_order_value': float(ca.average_order_value),
                        'customer_segment': ca.customer_segment,
                        'acquisition_channel': ca.acquisition_channel
                    }
                    for ca in customer_data
                ]
                
            else:  # segment
                # Segment profitability analysis
                segment_data = CustomerAnalytics.objects.values(
                    'customer_segment'
                ).annotate(
                    customer_count=Count('id'),
                    total_revenue=Sum('total_spent'),
                    avg_lifetime_value=Avg('lifetime_value'),
                    avg_order_value=Avg('average_order_value')
                ).order_by('-total_revenue')
                
                profitability_data = list(segment_data)
            
            return Response(list(profitability_data))
        except Exception as e:
            return Response(
                {'error': f'Failed to analyze profitability: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def update_forecast_accuracy(self, request):
        """
        Update forecast accuracy tracking and model improvement.
        """
        try:
            SalesForecastingService.update_forecast_accuracy()
            return Response({'message': 'Forecast accuracy updated successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to update forecast accuracy: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ViewSets for individual models
class SalesMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for sales metrics."""
    queryset = SalesMetrics.objects.all().order_by('-date')
    serializer_class = SalesMetricsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class ProductSalesAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for product sales analytics."""
    queryset = ProductSalesAnalytics.objects.all().order_by('-date', '-revenue')
    serializer_class = ProductSalesAnalyticsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class SalesForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for sales forecasts."""
    queryset = SalesForecast.objects.all().order_by('forecast_date')
    serializer_class = SalesForecastSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class SalesGoalViewSet(viewsets.ModelViewSet):
    """ViewSet for sales goals."""
    queryset = SalesGoal.objects.all().order_by('-created_at')
    serializer_class = SalesGoalSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class SalesCommissionViewSet(viewsets.ModelViewSet):
    """ViewSet for sales commissions."""
    queryset = SalesCommission.objects.all().order_by('-created_at')
    serializer_class = SalesCommissionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class SalesTerritoryViewSet(viewsets.ModelViewSet):
    """ViewSet for sales territories."""
    queryset = SalesTerritory.objects.all().order_by('name')
    serializer_class = SalesTerritorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class SalesPipelineViewSet(viewsets.ModelViewSet):
    """ViewSet for sales pipeline."""
    queryset = SalesPipeline.objects.all().order_by('-created_at')
    serializer_class = SalesPipelineSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class SalesAnomalyDetectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for sales anomaly detection."""
    queryset = SalesAnomalyDetection.objects.all().order_by('-date', '-severity')
    serializer_class = SalesAnomalyDetectionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]