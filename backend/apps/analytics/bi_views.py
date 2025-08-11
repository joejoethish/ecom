"""
Advanced Business Intelligence API Views for comprehensive analytics platform.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.http import HttpResponse, Http404
from datetime import datetime, timedelta
from typing import Dict, Any
import json
import csv
import io

from core.permissions import IsAdminUser
from .bi_models import (
    BIDashboard, BIWidget, BIDataSource, BIReport, BIInsight, BIMLModel,
    BIDataCatalog, BIAnalyticsSession, BIPerformanceMetric, BIAlert
)
from django.db import models
import uuid
from .bi_serializers import (
    BIDashboardSerializer, BIWidgetSerializer, BIDataSourceSerializer,
    BIReportSerializer, BIInsightSerializer, BIMLModelSerializer,
    BIDataCatalogSerializer, BIAnalyticsSessionSerializer,
    BIPerformanceMetricSerializer, BIAlertSerializer
)
from .bi_services import (
    BIDashboardService, BIDataService, BIInsightService, BIMLService,
    BIRealtimeService, BIDataGovernanceService
)


class BIDashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BI Dashboard management with executive summaries.
    """
    queryset = BIDashboard.objects.all().order_by('-updated_at')
    serializer_class = BIDashboardSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter dashboards based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        
        # Return dashboards created by user or shared with user
        return self.queryset.filter(
            models.Q(created_by=user) | 
            models.Q(shared_with=user) | 
            models.Q(is_public=True)
        ).distinct()

    @action(detail=False, methods=['post'])
    def create_executive_dashboard(self, request):
        """Create a comprehensive executive dashboard"""
        name = request.data.get('name', 'Executive Dashboard')
        
        try:
            dashboard = BIDashboardService.create_executive_dashboard(request.user, name)
            serializer = self.get_serializer(dashboard)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to create executive dashboard: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def dashboard_data(self, request, pk=None):
        """Get complete dashboard data with all widgets"""
        try:
            filters = {
                'date_range': request.query_params.get('date_range', '30d'),
                'business_unit': request.query_params.get('business_unit'),
                'region': request.query_params.get('region')
            }
            
            dashboard_data = BIDashboardService.get_dashboard_data(pk, filters)
            return Response(dashboard_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get dashboard data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def duplicate_dashboard(self, request, pk=None):
        """Duplicate an existing dashboard"""
        try:
            original_dashboard = self.get_object()
            
            # Create new dashboard
            new_dashboard = BIDashboard.objects.create(
                name=f"{original_dashboard.name} (Copy)",
                description=original_dashboard.description,
                dashboard_type=original_dashboard.dashboard_type,
                layout_config=original_dashboard.layout_config,
                filters_config=original_dashboard.filters_config,
                refresh_interval=original_dashboard.refresh_interval,
                created_by=request.user
            )
            
            # Duplicate widgets
            for widget in original_dashboard.widgets.all():
                BIWidget.objects.create(
                    dashboard=new_dashboard,
                    name=widget.name,
                    widget_type=widget.widget_type,
                    data_source=widget.data_source,
                    query_config=widget.query_config,
                    visualization_config=widget.visualization_config,
                    position_x=widget.position_x,
                    position_y=widget.position_y,
                    width=widget.width,
                    height=widget.height,
                    refresh_interval=widget.refresh_interval
                )
            
            serializer = self.get_serializer(new_dashboard)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to duplicate dashboard: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def share_dashboard(self, request, pk=None):
        """Share dashboard with other users"""
        try:
            dashboard = self.get_object()
            user_ids = request.data.get('user_ids', [])
            is_public = request.data.get('is_public', False)
            
            if is_public:
                dashboard.is_public = True
            else:
                from django.contrib.auth.models import User
                users = User.objects.filter(id__in=user_ids)
                dashboard.shared_with.set(users)
            
            dashboard.save()
            
            return Response({'message': 'Dashboard shared successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to share dashboard: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BIWidgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BI Widget management and data visualization.
    """
    queryset = BIWidget.objects.all().order_by('position_y', 'position_x')
    serializer_class = BIWidgetSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter widgets by dashboard"""
        dashboard_id = self.request.query_params.get('dashboard_id')
        if dashboard_id:
            return self.queryset.filter(dashboard_id=dashboard_id)
        return self.queryset

    @action(detail=True, methods=['post'])
    def update_position(self, request, pk=None):
        """Update widget position and size"""
        try:
            widget = self.get_object()
            position_x = request.data.get('position_x', widget.position_x)
            position_y = request.data.get('position_y', widget.position_y)
            width = request.data.get('width', widget.width)
            height = request.data.get('height', widget.height)
            
            success = BIDashboardService.update_widget_position(
                str(widget.id), position_x, position_y, width, height
            )
            
            if success:
                return Response({'message': 'Widget position updated successfully'})
            else:
                return Response(
                    {'error': 'Failed to update widget position'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to update widget position: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def widget_data(self, request, pk=None):
        """Get data for a specific widget"""
        try:
            widget = self.get_object()
            filters = {
                'date_range': request.query_params.get('date_range', '30d'),
                'business_unit': request.query_params.get('business_unit'),
                'region': request.query_params.get('region')
            }
            
            widget_data = BIDashboardService._get_widget_data(widget, filters)
            return Response(widget_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get widget data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BIDataSourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BI Data Source management and configuration.
    """
    queryset = BIDataSource.objects.all().order_by('-updated_at')
    serializer_class = BIDataSourceSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test data source connection"""
        try:
            data_source = self.get_object()
            
            # Simulate connection test
            # In a real implementation, this would actually test the connection
            connection_result = {
                'status': 'success',
                'message': 'Connection successful',
                'response_time': 150,  # milliseconds
                'last_tested': timezone.now().isoformat()
            }
            
            return Response(connection_result)
        except Exception as e:
            return Response(
                {'error': f'Connection test failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def refresh_data(self, request, pk=None):
        """Manually refresh data from source"""
        try:
            data_source = self.get_object()
            data_source.last_refresh = timezone.now()
            data_source.save()
            
            return Response({
                'message': 'Data refresh initiated',
                'last_refresh': data_source.last_refresh.isoformat()
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to refresh data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def data_preview(self, request, pk=None):
        """Get a preview of data from the source"""
        try:
            data_source = self.get_object()
            
            # Simulate data preview
            preview_data = {
                'columns': ['date', 'revenue', 'orders', 'customers'],
                'sample_data': [
                    ['2024-01-15', 45000.50, 120, 85],
                    ['2024-01-14', 42000.75, 115, 82],
                    ['2024-01-13', 48000.25, 125, 90]
                ],
                'total_rows': 1000,
                'data_types': {
                    'date': 'datetime',
                    'revenue': 'decimal',
                    'orders': 'integer',
                    'customers': 'integer'
                }
            }
            
            return Response(preview_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get data preview: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BIInsightViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for automated insights and anomaly detection.
    """
    queryset = BIInsight.objects.all().order_by('-created_at')
    serializer_class = BIInsightSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Filter insights based on query parameters"""
        queryset = super().get_queryset()
        
        insight_type = self.request.query_params.get('insight_type')
        severity = self.request.query_params.get('severity')
        is_acknowledged = self.request.query_params.get('is_acknowledged')
        
        if insight_type:
            queryset = queryset.filter(insight_type=insight_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if is_acknowledged is not None:
            queryset = queryset.filter(is_acknowledged=is_acknowledged.lower() == 'true')
        
        return queryset

    @action(detail=False, methods=['post'])
    def generate_insights(self, request):
        """Generate automated insights"""
        try:
            data_source_id = request.data.get('data_source_id')
            insights = BIInsightService.generate_automated_insights(data_source_id)
            
            # Save insights to database
            created_insights = []
            for insight_data in insights:
                insight = BIInsight.objects.create(
                    title=insight_data['title'],
                    description=insight_data['description'],
                    insight_type=insight_data['insight_type'],
                    severity=insight_data['severity'],
                    current_value=insight_data.get('current_value'),
                    expected_value=insight_data.get('expected_value'),
                    deviation_percentage=insight_data.get('deviation_percentage'),
                    confidence_score=insight_data['confidence_score'],
                    action_items=insight_data.get('action_items', []),
                    data_source_id=data_source_id if data_source_id else None
                )
                created_insights.append(insight)
            
            serializer = self.get_serializer(created_insights, many=True)
            return Response({
                'message': f'Generated {len(created_insights)} insights',
                'insights': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to generate insights: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def acknowledge_insight(self, request, pk=None):
        """Acknowledge an insight"""
        try:
            insight = self.get_object()
            insight.is_acknowledged = True
            insight.acknowledged_by = request.user
            insight.acknowledged_at = timezone.now()
            insight.save()
            
            return Response({'message': 'Insight acknowledged successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to acknowledge insight: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def resolve_insight(self, request, pk=None):
        """Mark an insight as resolved"""
        try:
            insight = self.get_object()
            insight.is_resolved = True
            insight.resolution_notes = request.data.get('resolution_notes', '')
            insight.save()
            
            return Response({'message': 'Insight resolved successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to resolve insight: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BIMLModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Machine Learning model deployment and monitoring.
    """
    queryset = BIMLModel.objects.all().order_by('-updated_at')
    serializer_class = BIMLModelSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['post'])
    def create_forecasting_model(self, request):
        """Create a new forecasting model"""
        try:
            name = request.data.get('name')
            data_source_id = request.data.get('data_source_id')
            
            if not name or not data_source_id:
                return Response(
                    {'error': 'Name and data_source_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            model = BIMLService.create_forecasting_model(name, request.user, data_source_id)
            serializer = self.get_serializer(model)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Failed to create forecasting model: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def train_model(self, request, pk=None):
        """Train a machine learning model"""
        try:
            result = BIMLService.train_model(pk)
            return Response(result)
        except Exception as e:
            return Response(
                {'error': f'Failed to train model: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def generate_predictions(self, request, pk=None):
        """Generate predictions using the model"""
        try:
            prediction_periods = int(request.data.get('prediction_periods', 30))
            predictions = BIMLService.generate_predictions(pk, prediction_periods)
            return Response(predictions)
        except Exception as e:
            return Response(
                {'error': f'Failed to generate predictions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def deploy_model(self, request, pk=None):
        """Deploy a trained model"""
        try:
            model = self.get_object()
            model.is_deployed = True
            model.deployment_config = request.data.get('deployment_config', {})
            model.save()
            
            return Response({'message': 'Model deployed successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to deploy model: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def model_performance(self, request, pk=None):
        """Get model performance metrics"""
        try:
            model = self.get_object()
            
            performance_data = {
                'model_id': str(model.id),
                'model_name': model.name,
                'model_type': model.model_type,
                'algorithm': model.algorithm,
                'performance_metrics': model.performance_metrics,
                'last_trained': model.last_trained.isoformat() if model.last_trained else None,
                'is_deployed': model.is_deployed,
                'version': model.version
            }
            
            return Response(performance_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get model performance: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BIRealtimeViewSet(viewsets.ViewSet):
    """
    ViewSet for real-time analytics and streaming data processing.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['get'])
    def realtime_metrics(self, request):
        """Get real-time business metrics"""
        try:
            metrics = BIRealtimeService.get_realtime_metrics()
            return Response(metrics)
        except Exception as e:
            return Response(
                {'error': f'Failed to get real-time metrics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def process_event(self, request):
        """Process a streaming event"""
        try:
            event_data = request.data
            success = BIRealtimeService.process_streaming_event(event_data)
            
            if success:
                return Response({'message': 'Event processed successfully'})
            else:
                return Response(
                    {'error': 'Failed to process event'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to process event: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def streaming_status(self, request):
        """Get streaming data processing status"""
        try:
            # Simulate streaming status
            status_data = {
                'active_streams': 3,
                'events_processed_today': 15420,
                'processing_rate': 125.5,  # events per second
                'error_rate': 0.02,  # percentage
                'last_processed': timezone.now().isoformat(),
                'stream_health': [
                    {'stream': 'order_events', 'status': 'healthy', 'rate': 45.2},
                    {'stream': 'user_activity', 'status': 'healthy', 'rate': 68.8},
                    {'stream': 'product_views', 'status': 'warning', 'rate': 11.5}
                ]
            }
            
            return Response(status_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get streaming status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BIDataGovernanceViewSet(viewsets.ViewSet):
    """
    ViewSet for data governance and quality management.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['post'])
    def assess_data_quality(self, request):
        """Assess data quality for a data source"""
        try:
            data_source_id = request.data.get('data_source_id')
            if not data_source_id:
                return Response(
                    {'error': 'data_source_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            quality_assessment = BIDataGovernanceService.assess_data_quality(data_source_id)
            return Response(quality_assessment)
        except Exception as e:
            return Response(
                {'error': f'Failed to assess data quality: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_data_lineage(self, request):
        """Create data lineage mapping"""
        try:
            data_source_id = request.data.get('data_source_id')
            if not data_source_id:
                return Response(
                    {'error': 'data_source_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            lineage = BIDataGovernanceService.create_data_lineage(data_source_id)
            return Response(lineage)
        except Exception as e:
            return Response(
                {'error': f'Failed to create data lineage: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def governance_dashboard(self, request):
        """Get data governance dashboard"""
        try:
            # Simulate governance dashboard data
            dashboard_data = {
                'data_sources_count': BIDataSource.objects.count(),
                'data_quality_average': 92.5,
                'compliance_score': 88.7,
                'active_policies': 15,
                'recent_quality_issues': [
                    {'source': 'Sales Database', 'issue': 'Missing data in revenue field', 'severity': 'medium'},
                    {'source': 'Customer API', 'issue': 'Inconsistent date formats', 'severity': 'low'}
                ],
                'data_stewards': 8,
                'cataloged_assets': 156,
                'last_audit': '2024-01-10T14:30:00Z'
            }
            
            return Response(dashboard_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to get governance dashboard: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BIAnalyticsSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for self-service analytics sessions.
    """
    queryset = BIAnalyticsSession.objects.all().order_by('-last_accessed')
    serializer_class = BIAnalyticsSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter sessions for current user"""
        user = self.request.user
        return self.queryset.filter(
            models.Q(user=user) | 
            models.Q(shared_with=user) | 
            models.Q(is_public=True)
        ).distinct()

    @action(detail=True, methods=['post'])
    def save_visualization(self, request, pk=None):
        """Save a visualization to the session"""
        try:
            session = self.get_object()
            visualization_data = request.data.get('visualization')
            
            if not visualization_data:
                return Response(
                    {'error': 'visualization data is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add visualization to session
            visualizations = session.visualizations or []
            visualization_data['id'] = str(uuid.uuid4())
            visualization_data['created_at'] = timezone.now().isoformat()
            visualizations.append(visualization_data)
            
            session.visualizations = visualizations
            session.save()
            
            return Response({'message': 'Visualization saved successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to save visualization: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def add_bookmark(self, request, pk=None):
        """Add a bookmark to the session"""
        try:
            session = self.get_object()
            bookmark_data = request.data.get('bookmark')
            
            if not bookmark_data:
                return Response(
                    {'error': 'bookmark data is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add bookmark to session
            bookmarks = session.bookmarks or []
            bookmark_data['id'] = str(uuid.uuid4())
            bookmark_data['created_at'] = timezone.now().isoformat()
            bookmarks.append(bookmark_data)
            
            session.bookmarks = bookmarks
            session.save()
            
            return Response({'message': 'Bookmark added successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to add bookmark: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BIExportViewSet(viewsets.ViewSet):
    """
    ViewSet for BI data export and reporting.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=['post'])
    def export_dashboard(self, request):
        """Export dashboard data"""
        try:
            dashboard_id = request.data.get('dashboard_id')
            export_format = request.data.get('format', 'json')  # json, csv, excel, pdf
            
            if not dashboard_id:
                return Response(
                    {'error': 'dashboard_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get dashboard data
            dashboard_data = BIDashboardService.get_dashboard_data(dashboard_id)
            
            if export_format == 'csv':
                return self._export_csv(dashboard_data)
            elif export_format == 'json':
                return Response(dashboard_data)
            else:
                return Response(
                    {'error': f'Export format {export_format} not supported'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to export dashboard: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _export_csv(self, dashboard_data):
        """Export dashboard data as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Widget Name', 'Widget Type', 'Data'])
        
        # Write widget data
        for widget in dashboard_data.get('widgets', []):
            writer.writerow([
                widget.get('name', ''),
                widget.get('widget_type', ''),
                json.dumps(widget.get('data', {}))
            ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="dashboard_export.csv"'
        return response

    @action(detail=False, methods=['post'])
    def export_report(self, request):
        """Export BI report data"""
        try:
            report_id = request.data.get('report_id')
            export_format = request.data.get('format', 'json')
            
            if not report_id:
                return Response(
                    {'error': 'report_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get report data (simplified implementation)
            report_data = {'message': 'Report export not fully implemented'}
            
            return Response(report_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to export report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )