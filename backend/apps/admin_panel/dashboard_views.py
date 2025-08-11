"""
Advanced Dashboard System Views for comprehensive admin panel.
"""
import json
import uuid
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import transaction

from .dashboard_models import (
    DashboardWidget, DashboardLayout, DashboardWidgetPosition,
    DashboardTemplate, DashboardUserPreference, DashboardAlert,
    DashboardUsageAnalytics, DashboardExport, DashboardDataSource
)
from .dashboard_serializers import (
    DashboardWidgetSerializer, DashboardLayoutSerializer, DashboardLayoutCreateSerializer,
    DashboardTemplateSerializer, DashboardUserPreferenceSerializer, DashboardAlertSerializer,
    DashboardUsageAnalyticsSerializer, DashboardExportSerializer, DashboardDataSourceSerializer,
    DashboardStatsSerializer, WidgetDataSerializer, DashboardRealTimeUpdateSerializer
)
from .permissions import AdminPanelPermission
from .models import AdminUser


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dashboard widgets.
    """
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated, AdminPanelPermission]
    filterset_fields = ['widget_type', 'chart_type', 'is_active', 'is_public']
    search_fields = ['name', 'title', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']

    def get_queryset(self):
        """Filter widgets based on user permissions."""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Super admins see all widgets
        if user.is_superuser or user.role == 'super_admin':
            return queryset
        
        # Filter by public widgets and user's allowed roles
        user_roles = [user.role] if hasattr(user, 'role') else []
        return queryset.filter(
            Q(is_public=True) |
            Q(created_by=user) |
            Q(allowed_roles__overlap=user_roles)
        )

    def perform_create(self, serializer):
        """Set the creator when creating a widget."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def data(self, request, pk=None):
        """Get widget data from its data source."""
        widget = self.get_object()
        
        # Check cache first
        cache_key = f"widget_data_{widget.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        try:
            # Fetch data based on widget's data source
            data = self._fetch_widget_data(widget)
            
            # Cache the data
            cache.set(cache_key, data, timeout=widget.refresh_interval)
            
            return Response(data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _fetch_widget_data(self, widget):
        """Fetch data for a specific widget based on its data source."""
        data_source = widget.data_source
        config = widget.data_config
        
        # Mock data generation based on widget type
        # In production, this would connect to actual data sources
        if data_source == 'sales_metrics':
            return self._get_sales_metrics_data(config)
        elif data_source == 'inventory_status':
            return self._get_inventory_status_data(config)
        elif data_source == 'customer_analytics':
            return self._get_customer_analytics_data(config)
        elif data_source == 'order_trends':
            return self._get_order_trends_data(config)
        else:
            return {'data': [], 'last_updated': timezone.now().isoformat()}

    def _get_sales_metrics_data(self, config):
        """Get sales metrics data."""
        # Mock implementation - replace with actual data fetching
        return {
            'total_sales': 125000,
            'sales_growth': 15.5,
            'orders_count': 1250,
            'average_order_value': 100,
            'last_updated': timezone.now().isoformat()
        }

    def _get_inventory_status_data(self, config):
        """Get inventory status data."""
        return {
            'total_products': 5000,
            'low_stock_items': 45,
            'out_of_stock': 12,
            'total_value': 2500000,
            'last_updated': timezone.now().isoformat()
        }

    def _get_customer_analytics_data(self, config):
        """Get customer analytics data."""
        return {
            'total_customers': 15000,
            'new_customers': 150,
            'active_customers': 8500,
            'customer_retention': 85.5,
            'last_updated': timezone.now().isoformat()
        }

    def _get_order_trends_data(self, config):
        """Get order trends data."""
        # Generate mock trend data
        dates = []
        values = []
        for i in range(30):
            date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
            values.append(100 + (i * 5) + (i % 7 * 10))
        
        return {
            'labels': dates[::-1],
            'data': values[::-1],
            'last_updated': timezone.now().isoformat()
        }

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a widget."""
        widget = self.get_object()
        
        # Create a copy
        widget.pk = None
        widget.id = uuid.uuid4()
        widget.name = f"{widget.name} (Copy)"
        widget.created_by = request.user
        widget.save()
        
        serializer = self.get_serializer(widget)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular widgets."""
        # Get widgets with most usage
        popular_widgets = DashboardWidget.objects.annotate(
            usage_count=Count('dashboardusageanalytics')
        ).order_by('-usage_count')[:10]
        
        serializer = self.get_serializer(popular_widgets, many=True)
        return Response(serializer.data)


class DashboardLayoutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dashboard layouts.
    """
    queryset = DashboardLayout.objects.all()
    permission_classes = [IsAuthenticated, AdminPanelPermission]
    filterset_fields = ['is_shared', 'is_template', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return DashboardLayoutCreateSerializer
        return DashboardLayoutSerializer

    def get_queryset(self):
        """Filter layouts based on user permissions."""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Super admins see all layouts
        if user.is_superuser or user.role == 'super_admin':
            return queryset
        
        # Filter by owned layouts, shared layouts, and templates
        user_roles = [user.role] if hasattr(user, 'role') else []
        return queryset.filter(
            Q(owner=user) |
            Q(is_shared=True, shared_with_roles__overlap=user_roles) |
            Q(shared_with_users=user) |
            Q(is_template=True)
        ).distinct()

    def perform_create(self, serializer):
        """Set the owner when creating a layout."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a layout with all its widgets."""
        layout = self.get_object()
        
        with transaction.atomic():
            # Create layout copy
            original_id = layout.id
            layout.pk = None
            layout.id = uuid.uuid4()
            layout.name = f"{layout.name} (Copy)"
            layout.owner = request.user
            layout.is_shared = False
            layout.save()
            
            # Copy widget positions
            original_positions = DashboardWidgetPosition.objects.filter(
                layout_id=original_id
            )
            for position in original_positions:
                position.pk = None
                position.layout = layout
                position.save()
        
        serializer = self.get_serializer(layout)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_widget(self, request, pk=None):
        """Add a widget to the layout."""
        layout = self.get_object()
        widget_id = request.data.get('widget_id')
        
        if not widget_id:
            return Response(
                {'error': 'widget_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            widget = DashboardWidget.objects.get(id=widget_id)
        except DashboardWidget.DoesNotExist:
            return Response(
                {'error': 'Widget not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if widget already exists in layout
        if DashboardWidgetPosition.objects.filter(
            layout=layout, widget=widget
        ).exists():
            return Response(
                {'error': 'Widget already exists in this layout'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create widget position
        position = DashboardWidgetPosition.objects.create(
            layout=layout,
            widget=widget,
            x=request.data.get('x', 0),
            y=request.data.get('y', 0),
            width=request.data.get('width', 2),
            height=request.data.get('height', 2),
            widget_config=request.data.get('config', {}),
            order=request.data.get('order', 0)
        )
        
        from .dashboard_serializers import DashboardWidgetPositionSerializer
        serializer = DashboardWidgetPositionSerializer(position)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_widget(self, request, pk=None):
        """Remove a widget from the layout."""
        layout = self.get_object()
        widget_id = request.data.get('widget_id')
        
        try:
            position = DashboardWidgetPosition.objects.get(
                layout=layout, widget_id=widget_id
            )
            position.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DashboardWidgetPosition.DoesNotExist:
            return Response(
                {'error': 'Widget not found in this layout'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_positions(self, request, pk=None):
        """Update widget positions in bulk."""
        layout = self.get_object()
        positions_data = request.data.get('positions', [])
        
        with transaction.atomic():
            for position_data in positions_data:
                try:
                    position = DashboardWidgetPosition.objects.get(
                        layout=layout,
                        widget_id=position_data['widget_id']
                    )
                    position.x = position_data.get('x', position.x)
                    position.y = position_data.get('y', position.y)
                    position.width = position_data.get('width', position.width)
                    position.height = position_data.get('height', position.height)
                    position.order = position_data.get('order', position.order)
                    position.save()
                except DashboardWidgetPosition.DoesNotExist:
                    continue
        
        serializer = self.get_serializer(layout)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_as_default(self, request, pk=None):
        """Set layout as default for user."""
        layout = self.get_object()
        user = request.user
        
        # Get or create user preferences
        preferences, created = DashboardUserPreference.objects.get_or_create(
            user=user,
            defaults={'default_layout': layout}
        )
        
        if not created:
            preferences.default_layout = layout
            preferences.save()
        
        return Response({'message': 'Layout set as default'})


class DashboardTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dashboard templates.
    """
    queryset = DashboardTemplate.objects.filter(is_active=True)
    serializer_class = DashboardTemplateSerializer
    permission_classes = [IsAuthenticated, AdminPanelPermission]
    filterset_fields = ['template_type', 'is_featured']
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['name', 'usage_count', 'created_at']
    ordering = ['-is_featured', '-usage_count', 'name']

    def get_queryset(self):
        """Filter templates based on user role."""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Filter by target roles
        if hasattr(user, 'role') and user.role:
            return queryset.filter(
                Q(target_roles__contains=[user.role]) |
                Q(target_roles=[])  # Templates for all roles
            )
        
        return queryset

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply template to create a new dashboard layout."""
        template = self.get_object()
        user = request.user
        
        # Increment usage count
        template.usage_count = F('usage_count') + 1
        template.save(update_fields=['usage_count'])
        
        with transaction.atomic():
            # Create layout from template
            layout = DashboardLayout.objects.create(
                name=f"{template.name} - {user.username}",
                description=f"Created from template: {template.name}",
                owner=user,
                layout_config=template.layout_config
            )
            
            # Create widgets from template configuration
            for widget_config in template.widgets_config:
                try:
                    # Create or get widget
                    widget_data = widget_config.get('widget', {})
                    widget, created = DashboardWidget.objects.get_or_create(
                        name=widget_data.get('name'),
                        defaults={
                            'title': widget_data.get('title', widget_data.get('name')),
                            'widget_type': widget_data.get('widget_type', 'metric'),
                            'data_source': widget_data.get('data_source', ''),
                            'data_config': widget_data.get('data_config', {}),
                            'display_config': widget_data.get('display_config', {}),
                            'created_by': user,
                            'is_public': True
                        }
                    )
                    
                    # Create widget position
                    DashboardWidgetPosition.objects.create(
                        layout=layout,
                        widget=widget,
                        x=widget_config.get('x', 0),
                        y=widget_config.get('y', 0),
                        width=widget_config.get('width', 2),
                        height=widget_config.get('height', 2),
                        widget_config=widget_config.get('config', {}),
                        order=widget_config.get('order', 0)
                    )
                except Exception as e:
                    # Log error but continue with other widgets
                    continue
        
        serializer = DashboardLayoutSerializer(layout)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DashboardUserPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user dashboard preferences.
    """
    queryset = DashboardUserPreference.objects.all()
    serializer_class = DashboardUserPreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users can only access their own preferences."""
        return super().get_queryset().filter(user=self.request.user)

    def get_object(self):
        """Get or create user preferences."""
        try:
            return DashboardUserPreference.objects.get(user=self.request.user)
        except DashboardUserPreference.DoesNotExist:
            return DashboardUserPreference.objects.create(user=self.request.user)

    @action(detail=False, methods=['get', 'post'])
    def my_preferences(self, request):
        """Get or update current user's preferences."""
        preferences = self.get_object()
        
        if request.method == 'GET':
            serializer = self.get_serializer(preferences)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = self.get_serializer(preferences, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dashboard alerts.
    """
    queryset = DashboardAlert.objects.all()
    serializer_class = DashboardAlertSerializer
    permission_classes = [IsAuthenticated, AdminPanelPermission]
    filterset_fields = ['alert_type', 'severity', 'status', 'is_enabled']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'severity', 'last_triggered', 'created_at']
    ordering = ['-last_triggered', '-created_at']

    def get_queryset(self):
        """Filter alerts based on user permissions."""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Super admins see all alerts
        if user.is_superuser or user.role == 'super_admin':
            return queryset
        
        # Filter by alerts user is recipient of or created
        user_roles = [user.role] if hasattr(user, 'role') else []
        return queryset.filter(
            Q(recipients=user) |
            Q(recipient_roles__overlap=user_roles) |
            Q(created_by=user)
        ).distinct()

    def perform_create(self, serializer):
        """Set the creator when creating an alert."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.save()
        
        # Log the acknowledgment
        DashboardUsageAnalytics.objects.create(
            user=request.user,
            session_id=request.session.session_key or '',
            action='alert_acknowledge',
            metadata={'alert_id': str(alert.id)},
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        alert = self.get_object()
        alert.status = 'resolved'
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active alerts for current user."""
        user = request.user
        user_roles = [user.role] if hasattr(user, 'role') else []
        
        alerts = self.get_queryset().filter(
            status='active',
            is_enabled=True
        ).filter(
            Q(recipients=user) |
            Q(recipient_roles__overlap=user_roles)
        ).distinct()
        
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)


class DashboardAnalyticsView(APIView):
    """
    View for dashboard analytics and statistics.
    """
    permission_classes = [IsAuthenticated, AdminPanelPermission]

    def get(self, request):
        """Get dashboard analytics and statistics."""
        user = request.user
        
        # Basic statistics
        stats = {
            'total_dashboards': DashboardLayout.objects.filter(
                Q(owner=user) | Q(is_shared=True)
            ).count(),
            'total_widgets': DashboardWidget.objects.filter(
                Q(created_by=user) | Q(is_public=True)
            ).count(),
            'active_users': AdminUser.objects.filter(
                is_active=True,
                last_login__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'total_exports': DashboardExport.objects.filter(
                exported_by=user
            ).count()
        }
        
        # Popular widgets
        popular_widgets = DashboardWidget.objects.annotate(
            usage_count=Count('dashboardusageanalytics')
        ).order_by('-usage_count')[:5]
        
        stats['popular_widgets'] = [
            {
                'id': str(widget.id),
                'name': widget.name,
                'type': widget.widget_type,
                'usage_count': widget.usage_count
            }
            for widget in popular_widgets
        ]
        
        # Usage by role
        role_usage = DashboardUsageAnalytics.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).values('user__role').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['usage_by_role'] = {
            item['user__role'] or 'Unknown': item['count']
            for item in role_usage
        }
        
        # Recent activity
        recent_activity = DashboardUsageAnalytics.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        stats['recent_activity'] = [
            {
                'action': activity.action,
                'dashboard': activity.dashboard_layout.name if activity.dashboard_layout else None,
                'widget': activity.widget.name if activity.widget else None,
                'timestamp': activity.created_at.isoformat()
            }
            for activity in recent_activity
        ]
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)


class DashboardExportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dashboard exports.
    """
    queryset = DashboardExport.objects.all()
    serializer_class = DashboardExportSerializer
    permission_classes = [IsAuthenticated, AdminPanelPermission]
    filterset_fields = ['export_type', 'format', 'status']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Users can only see their own exports."""
        return super().get_queryset().filter(exported_by=self.request.user)

    def perform_create(self, serializer):
        """Set the exporter when creating an export."""
        serializer.save(exported_by=self.request.user)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download exported file."""
        export = self.get_object()
        
        if export.status != 'completed':
            return Response(
                {'error': 'Export not completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not export.file_path:
            return Response(
                {'error': 'Export file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Increment download count
        export.download_count = F('download_count') + 1
        export.save(update_fields=['download_count'])
        
        # In production, serve file through web server
        return Response({
            'download_url': f'/media/exports/{export.file_path}',
            'filename': export.name,
            'size': export.file_size
        })


class DashboardRealTimeView(APIView):
    """
    View for real-time dashboard updates via WebSocket or Server-Sent Events.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get real-time dashboard updates."""
        # This would typically be handled by WebSocket or SSE
        # For now, return current status
        user = request.user
        
        # Get recent updates
        recent_updates = DashboardUsageAnalytics.objects.filter(
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).order_by('-created_at')[:10]
        
        updates = []
        for update in recent_updates:
            updates.append({
                'event_type': 'user_activity',
                'user_id': str(update.user.id),
                'action': update.action,
                'dashboard_id': str(update.dashboard_layout.id) if update.dashboard_layout else None,
                'widget_id': str(update.widget.id) if update.widget else None,
                'timestamp': update.created_at.isoformat()
            })
        
        return Response({
            'updates': updates,
            'timestamp': timezone.now().isoformat()
        })

    def post(self, request):
        """Track user activity for real-time updates."""
        user = request.user
        
        # Create usage analytics record
        DashboardUsageAnalytics.objects.create(
            user=user,
            session_id=request.session.session_key or '',
            action=request.data.get('action', 'view'),
            dashboard_layout_id=request.data.get('dashboard_id'),
            widget_id=request.data.get('widget_id'),
            metadata=request.data.get('metadata', {}),
            duration_seconds=request.data.get('duration'),
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'status': 'recorded'})


class DashboardDataSourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dashboard data sources.
    """
    queryset = DashboardDataSource.objects.all()
    serializer_class = DashboardDataSourceSerializer
    permission_classes = [IsAuthenticated, AdminPanelPermission]
    filterset_fields = ['source_type', 'auth_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'last_sync', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Filter data sources based on user permissions."""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Super admins see all data sources
        if user.is_superuser or user.role == 'super_admin':
            return queryset
        
        # Filter by created or allowed data sources
        return queryset.filter(
            Q(created_by=user) |
            Q(allowed_users=user)
        ).distinct()

    def perform_create(self, serializer):
        """Set the creator when creating a data source."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test data source connection."""
        data_source = self.get_object()
        
        try:
            # Mock connection test - replace with actual implementation
            if data_source.source_type == 'api':
                # Test API connection
                result = {'status': 'success', 'message': 'API connection successful'}
            elif data_source.source_type == 'database':
                # Test database connection
                result = {'status': 'success', 'message': 'Database connection successful'}
            else:
                result = {'status': 'success', 'message': 'Connection test passed'}
            
            # Update sync status
            data_source.sync_status = 'success'
            data_source.last_sync = timezone.now()
            data_source.error_count = 0
            data_source.last_error = ''
            data_source.save()
            
            return Response(result)
            
        except Exception as e:
            # Update error status
            data_source.sync_status = 'error'
            data_source.error_count = F('error_count') + 1
            data_source.last_error = str(e)
            data_source.save()
            
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def sync_data(self, request, pk=None):
        """Manually sync data from source."""
        data_source = self.get_object()
        
        try:
            # Mock data sync - replace with actual implementation
            data_source.sync_status = 'syncing'
            data_source.save()
            
            # Simulate sync process
            # In production, this would be handled by a background task
            
            data_source.sync_status = 'success'
            data_source.last_sync = timezone.now()
            data_source.error_count = 0
            data_source.save()
            
            return Response({'status': 'success', 'message': 'Data sync completed'})
            
        except Exception as e:
            data_source.sync_status = 'error'
            data_source.error_count = F('error_count') + 1
            data_source.last_error = str(e)
            data_source.save()
            
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )