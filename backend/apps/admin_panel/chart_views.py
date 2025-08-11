"""
Chart views for advanced data visualization API
"""
import json
import uuid
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .chart_models import (
    Chart, ChartTemplate, ChartVersion, ChartAnnotation,
    ChartComment, ChartShare, ChartExport, ChartPerformanceMetric
)
from .chart_serializers import (
    ChartSerializer, ChartListSerializer, ChartTemplateSerializer,
    ChartVersionSerializer, ChartAnnotationSerializer, ChartCommentSerializer,
    ChartShareSerializer, ChartExportSerializer, ChartDataSerializer,
    ChartExportRequestSerializer, ChartFilterSerializer, ChartDrillDownSerializer
)
# from .chart_services import (
#     ChartDataService, ChartExportService, ChartPerformanceService,
#     ChartAnalyticsService
# )

class ChartTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for chart templates"""
    queryset = ChartTemplate.objects.all()
    serializer_class = ChartTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by chart type
        chart_type = self.request.query_params.get('chart_type')
        if chart_type:
            queryset = queryset.filter(chart_type=chart_type)
        
        # Filter public templates or user's own templates
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(is_public=True) | Q(created_by=self.request.user)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available template categories"""
        categories = ChartTemplate.objects.values_list('category', flat=True).distinct()
        return Response({'categories': list(categories)})

class ChartViewSet(viewsets.ModelViewSet):
    """ViewSet for charts with advanced features"""
    queryset = Chart.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ChartListSerializer
        return ChartSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by chart type
        chart_type = self.request.query_params.get('chart_type')
        if chart_type:
            queryset = queryset.filter(chart_type=chart_type)
        
        # Filter by real-time capability
        is_real_time = self.request.query_params.get('is_real_time')
        if is_real_time is not None:
            queryset = queryset.filter(is_real_time=is_real_time.lower() == 'true')
        
        # Search by title
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # Filter by access permissions
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(is_public=True) | 
                Q(created_by=self.request.user) |
                Q(allowed_users=self.request.user)
            )
        
        return queryset.distinct()
    
    def perform_create(self, serializer):
        chart = serializer.save(created_by=self.request.user)
        
        # Create initial version
        ChartVersion.objects.create(
            chart=chart,
            version_number=1,
            title=chart.title,
            config=chart.config,
            changes_summary="Initial version",
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        old_chart = self.get_object()
        chart = serializer.save()
        
        # Create new version if config changed
        if old_chart.config != chart.config or old_chart.title != chart.title:
            latest_version = chart.versions.first()
            new_version_number = (latest_version.version_number + 1) if latest_version else 1
            
            ChartVersion.objects.create(
                chart=chart,
                version_number=new_version_number,
                title=chart.title,
                config=chart.config,
                changes_summary=self.request.data.get('changes_summary', 'Updated chart'),
                created_by=self.request.user
            )
    
    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """Get chart data with filtering and caching"""
        chart = self.get_object()
        
        # Update access tracking
        chart.access_count += 1
        chart.last_accessed = timezone.now()
        chart.save(update_fields=['access_count', 'last_accessed'])
        
        # Parse filters
        filter_serializer = ChartFilterSerializer(data=request.query_params)
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data
        else:
            filters = {}
        
        # Get data
        data_service = ChartDataService()
        start_time = datetime.now()
        
        try:
            chart_data = data_service.get_chart_data(chart, filters)
            load_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Record performance metrics
            perf_service = ChartPerformanceService()
            perf_service.record_performance(
                chart=chart,
                load_time=load_time,
                data_size=len(json.dumps(chart_data)),
                render_time=0,  # Will be updated from frontend
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            # Add timestamp and cache info
            chart_data['timestamp'] = timezone.now()
            chart_data['cache_info'] = {
                'cached': False,  # This would be set by the service
                'expires_at': timezone.now() + timedelta(seconds=chart.refresh_interval)
            }
            
            return Response(chart_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch chart data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def drill_down(self, request, pk=None):
        """Drill down into chart data"""
        chart = self.get_object()
        
        drill_serializer = ChartDrillDownSerializer(data=request.data)
        if not drill_serializer.is_valid():
            return Response(drill_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        drill_data = drill_serializer.validated_data
        
        # Get drill-down data (implementation depends on data source)
        data_service = ChartDataService()
        
        # Create filters for drill-down
        filters = {
            'drill_dimension': drill_data['dimension'],
            'drill_value': drill_data['value'],
            'drill_level': drill_data['level'],
            **drill_data.get('filters', {})
        }
        
        try:
            drill_down_data = data_service.get_chart_data(chart, filters)
            return Response(drill_down_data)
        except Exception as e:
            return Response(
                {'error': f'Failed to drill down: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """Export chart in various formats"""
        chart = self.get_object()
        
        export_serializer = ChartExportRequestSerializer(data=request.data)
        if not export_serializer.is_valid():
            return Response(export_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        export_data = export_serializer.validated_data
        
        try:
            export_service = ChartExportService()
            file_path = export_service.export_chart(
                chart=chart,
                format=export_data['format'],
                options=export_data
            )
            
            # Create export record
            chart_export = ChartExport.objects.create(
                chart=chart,
                export_format=export_data['format'],
                file_path=file_path,
                file_size=0,  # Would be calculated
                export_settings=export_data,
                created_by=request.user
            )
            
            serializer = ChartExportSerializer(chart_export)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to export chart: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download_export(self, request, pk=None):
        """Download exported chart file"""
        export_id = request.query_params.get('export_id')
        if not export_id:
            return Response(
                {'error': 'export_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            chart_export = ChartExport.objects.get(id=export_id, chart_id=pk)
            return FileResponse(
                open(chart_export.file_path, 'rb'),
                as_attachment=True,
                filename=f"{chart_export.chart.title}.{chart_export.export_format}"
            )
        except ChartExport.DoesNotExist:
            return Response(
                {'error': 'Export not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Create chart share link"""
        chart = self.get_object()
        
        share_data = request.data
        share_type = share_data.get('share_type', 'public_link')
        expires_at = share_data.get('expires_at')
        
        if expires_at:
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        # Generate unique share token
        share_token = str(uuid.uuid4())
        
        chart_share = ChartShare.objects.create(
            chart=chart,
            share_type=share_type,
            share_token=share_token,
            expires_at=expires_at,
            settings=share_data.get('settings', {}),
            created_by=request.user
        )
        
        serializer = ChartShareSerializer(chart_share)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def embed_code(self, request, pk=None):
        """Get embed code for chart"""
        chart = self.get_object()
        share_token = request.query_params.get('share_token')
        
        if not share_token:
            return Response(
                {'error': 'share_token parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify share token
        try:
            chart_share = ChartShare.objects.get(
                chart=chart,
                share_token=share_token,
                is_active=True
            )
            
            if chart_share.expires_at and chart_share.expires_at < timezone.now():
                return Response(
                    {'error': 'Share link has expired'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
        except ChartShare.DoesNotExist:
            return Response(
                {'error': 'Invalid share token'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate embed code
        embed_url = f"{request.build_absolute_uri('/')[:-1]}/api/charts/{pk}/embed/?token={share_token}"
        embed_code = f'''<iframe 
            src="{embed_url}" 
            width="800" 
            height="600" 
            frameborder="0">
        </iframe>'''
        
        return Response({
            'embed_code': embed_code,
            'embed_url': embed_url
        })
    
    @action(detail=True, methods=['get'])
    def embed(self, request, pk=None):
        """Embedded chart view"""
        token = request.query_params.get('token')
        if not token:
            return Response(
                {'error': 'Token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            chart_share = ChartShare.objects.get(
                chart_id=pk,
                share_token=token,
                is_active=True
            )
            
            if chart_share.expires_at and chart_share.expires_at < timezone.now():
                return Response(
                    {'error': 'Share link has expired'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Update access count
            chart_share.access_count += 1
            chart_share.save(update_fields=['access_count'])
            
            # Get chart data
            chart = chart_share.chart
            data_service = ChartDataService()
            chart_data = data_service.get_chart_data(chart)
            
            # Return embedded chart data
            return Response({
                'chart': {
                    'id': str(chart.id),
                    'title': chart.title,
                    'type': chart.chart_type,
                    'config': chart.config,
                    'theme': chart.theme,
                    'colors': chart.colors
                },
                'data': chart_data,
                'settings': chart_share.settings
            })
            
        except ChartShare.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get chart performance metrics"""
        chart = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        perf_service = ChartPerformanceService()
        stats = perf_service.get_performance_stats(chart, days)
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """Get chart insights and recommendations"""
        chart = self.get_object()
        
        analytics_service = ChartAnalyticsService()
        insights = analytics_service.get_chart_insights(chart)
        
        return Response(insights)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a chart"""
        original_chart = self.get_object()
        
        # Create duplicate
        duplicate_chart = Chart.objects.create(
            title=f"{original_chart.title} (Copy)",
            description=original_chart.description,
            chart_type=original_chart.chart_type,
            template=original_chart.template,
            config=original_chart.config,
            data_source=original_chart.data_source,
            refresh_interval=original_chart.refresh_interval,
            theme=original_chart.theme,
            colors=original_chart.colors,
            custom_css=original_chart.custom_css,
            is_public=False,  # Duplicates are private by default
            status='draft',
            is_real_time=original_chart.is_real_time,
            created_by=request.user
        )
        
        # Create initial version
        ChartVersion.objects.create(
            chart=duplicate_chart,
            version_number=1,
            title=duplicate_chart.title,
            config=duplicate_chart.config,
            changes_summary="Duplicated from original chart",
            created_by=request.user
        )
        
        serializer = ChartSerializer(duplicate_chart)
        return Response(serializer.data)

class ChartAnnotationViewSet(viewsets.ModelViewSet):
    """ViewSet for chart annotations"""
    queryset = ChartAnnotation.objects.all()
    serializer_class = ChartAnnotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        chart_id = self.request.query_params.get('chart_id')
        if chart_id:
            return self.queryset.filter(chart_id=chart_id)
        return self.queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ChartCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for chart comments"""
    queryset = ChartComment.objects.all()
    serializer_class = ChartCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        chart_id = self.request.query_params.get('chart_id')
        if chart_id:
            return self.queryset.filter(chart_id=chart_id, parent__isnull=True)
        return self.queryset.filter(parent__isnull=True)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ChartRealTimeDataView(APIView):
    """WebSocket-like real-time data updates for charts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, chart_id):
        """Get real-time data for a chart"""
        try:
            chart = Chart.objects.get(id=chart_id, is_real_time=True)
        except Chart.DoesNotExist:
            return Response(
                {'error': 'Chart not found or not real-time enabled'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if not (chart.is_public or chart.created_by == request.user or 
                request.user in chart.allowed_users.all()):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get latest data
        data_service = ChartDataService()
        chart_data = data_service.get_chart_data(chart, use_cache=False)
        
        return Response({
            'chart_id': str(chart.id),
            'data': chart_data,
            'timestamp': timezone.now(),
            'refresh_interval': chart.refresh_interval
        })
    
    def post(self, request, chart_id):
        """Subscribe to real-time updates"""
        try:
            chart = Chart.objects.get(id=chart_id, is_real_time=True)
        except Chart.DoesNotExist:
            return Response(
                {'error': 'Chart not found or not real-time enabled'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Add user to real-time subscribers (would use WebSocket in production)
        channel_layer = get_channel_layer()
        group_name = f"chart_{chart_id}"
        
        # This would typically be handled by WebSocket consumer
        return Response({
            'subscribed': True,
            'group': group_name,
            'refresh_interval': chart.refresh_interval
        })

class ChartAnalyticsView(APIView):
    """Chart analytics and usage statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get overall chart analytics"""
        user_charts = Chart.objects.filter(created_by=request.user)
        
        analytics = {
            'total_charts': user_charts.count(),
            'active_charts': user_charts.filter(status='active').count(),
            'real_time_charts': user_charts.filter(is_real_time=True).count(),
            'total_views': sum(chart.access_count for chart in user_charts),
            'chart_types': {},
            'recent_activity': []
        }
        
        # Chart type distribution
        for chart_type, _ in Chart.CHART_TYPES:
            count = user_charts.filter(chart_type=chart_type).count()
            if count > 0:
                analytics['chart_types'][chart_type] = count
        
        # Recent activity
        recent_charts = user_charts.order_by('-last_accessed')[:5]
        for chart in recent_charts:
            analytics['recent_activity'].append({
                'chart_id': str(chart.id),
                'title': chart.title,
                'last_accessed': chart.last_accessed,
                'access_count': chart.access_count
            })
        
        return Response(analytics)