from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from datetime import timedelta

from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, DebugConfiguration, PerformanceThreshold,
    FrontendRoute, APICallDiscovery, RouteDiscoverySession, RouteDependency
)
from .route_discovery import RouteDiscoveryService
from .serializers import (
    WorkflowSessionSerializer, WorkflowSessionCreateSerializer,
    TraceStepSerializer, PerformanceSnapshotSerializer,
    ErrorLogSerializer, ErrorLogCreateSerializer,
    DebugConfigurationSerializer, PerformanceThresholdSerializer,
    SystemHealthSerializer, WorkflowStatsSerializer,
    FrontendRouteSerializer, APICallDiscoverySerializer,
    RouteDiscoverySessionSerializer, RouteDependencySerializer,
    RouteDiscoveryResultSerializer, DependencyMapSerializer,
    RouteValidationResultSerializer
)
from .services import WorkflowTracingEngine, TimingAnalyzer, ErrorTracker
from .database_monitor import DatabaseHealthMonitor
from .utils import PerformanceMonitor, ErrorLogger


class WorkflowSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing workflow sessions"""
    queryset = WorkflowSession.objects.all().select_related('user').prefetch_related('trace_steps')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['workflow_type', 'status', 'user']
    ordering_fields = ['start_time', 'end_time', 'workflow_type']
    ordering = ['-start_time']
    search_fields = ['correlation_id', 'workflow_type']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WorkflowSessionCreateSerializer
        return WorkflowSessionSerializer
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a workflow session as completed"""
        workflow = self.get_object()
        workflow.status = 'completed'
        workflow.end_time = timezone.now()
        workflow.save()
        
        serializer = self.get_serializer(workflow)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Mark a workflow session as failed"""
        workflow = self.get_object()
        workflow.status = 'failed'
        workflow.end_time = timezone.now()
        if 'error_message' in request.data:
            workflow.metadata['error_message'] = request.data['error_message']
        workflow.save()
        
        serializer = self.get_serializer(workflow)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get workflow statistics"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        total_workflows = self.queryset.count()
        completed_workflows = self.queryset.filter(status='completed').count()
        failed_workflows = self.queryset.filter(status='failed').count()
        
        # Average duration for completed workflows
        avg_duration = self.queryset.filter(
            status='completed',
            end_time__isnull=False
        ).aggregate(
            avg_duration=Avg('end_time') - Avg('start_time')
        )['avg_duration']
        
        avg_duration_ms = int(avg_duration.total_seconds() * 1000) if avg_duration else 0
        
        # Workflow types distribution
        workflow_types = dict(
            self.queryset.values('workflow_type').annotate(
                count=Count('id')
            ).values_list('workflow_type', 'count')
        )
        
        # Recent activity (last 24 hours)
        recent_activity = list(
            self.queryset.filter(start_time__gte=last_24h).values(
                'correlation_id', 'workflow_type', 'status', 'start_time'
            )[:10]
        )
        
        stats_data = {
            'total_workflows': total_workflows,
            'completed_workflows': completed_workflows,
            'failed_workflows': failed_workflows,
            'average_duration_ms': avg_duration_ms,
            'workflow_types': workflow_types,
            'recent_activity': recent_activity
        }
        
        serializer = WorkflowStatsSerializer(stats_data)
        return Response(serializer.data)


class TraceStepViewSet(viewsets.ModelViewSet):
    """ViewSet for managing trace steps"""
    queryset = TraceStep.objects.all().select_related('workflow_session')
    serializer_class = TraceStepSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['workflow_session', 'layer', 'component', 'status']
    ordering_fields = ['start_time', 'duration_ms']
    ordering = ['start_time']
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a trace step as completed"""
        trace_step = self.get_object()
        trace_step.status = 'completed'
        trace_step.end_time = timezone.now()
        
        # Calculate duration
        if trace_step.start_time:
            delta = trace_step.end_time - trace_step.start_time
            trace_step.duration_ms = int(delta.total_seconds() * 1000)
        
        trace_step.save()
        
        serializer = self.get_serializer(trace_step)
        return Response(serializer.data)


class PerformanceSnapshotViewSet(viewsets.ModelViewSet):
    """ViewSet for managing performance snapshots"""
    queryset = PerformanceSnapshot.objects.all()
    serializer_class = PerformanceSnapshotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['layer', 'component', 'metric_name', 'correlation_id']
    ordering_fields = ['timestamp', 'metric_value']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Get performance alerts (metrics exceeding thresholds)"""
        alerts = []
        
        # Get metrics that exceed warning thresholds
        warning_metrics = self.queryset.filter(
            threshold_warning__isnull=False,
            metric_value__gte=F('threshold_warning')
        ).order_by('-timestamp')[:50]
        
        # Get metrics that exceed critical thresholds
        critical_metrics = self.queryset.filter(
            threshold_critical__isnull=False,
            metric_value__gte=F('threshold_critical')
        ).order_by('-timestamp')[:50]
        
        for metric in warning_metrics:
            alerts.append({
                'type': 'warning',
                'metric': self.get_serializer(metric).data
            })
        
        for metric in critical_metrics:
            alerts.append({
                'type': 'critical',
                'metric': self.get_serializer(metric).data
            })
        
        return Response({'alerts': alerts})


class ErrorLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing error logs"""
    queryset = ErrorLog.objects.all().select_related('user')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['layer', 'component', 'severity', 'error_type', 'resolved', 'correlation_id']
    ordering_fields = ['timestamp', 'severity']
    ordering = ['-timestamp']
    search_fields = ['error_message', 'error_type', 'component']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ErrorLogCreateSerializer
        return ErrorLogSerializer
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark an error as resolved"""
        error_log = self.get_object()
        error_log.resolved = True
        error_log.resolution_notes = request.data.get('resolution_notes', '')
        error_log.save()
        
        serializer = self.get_serializer(error_log)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get error summary statistics"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        total_errors = self.queryset.count()
        recent_errors = self.queryset.filter(timestamp__gte=last_24h).count()
        unresolved_errors = self.queryset.filter(resolved=False).count()
        
        # Error distribution by severity
        severity_distribution = dict(
            self.queryset.values('severity').annotate(
                count=Count('id')
            ).values_list('severity', 'count')
        )
        
        # Error distribution by layer
        layer_distribution = dict(
            self.queryset.values('layer').annotate(
                count=Count('id')
            ).values_list('layer', 'count')
        )
        
        # Top error types
        top_error_types = list(
            self.queryset.values('error_type').annotate(
                count=Count('id')
            ).order_by('-count')[:10].values_list('error_type', 'count')
        )
        
        summary_data = {
            'total_errors': total_errors,
            'recent_errors': recent_errors,
            'unresolved_errors': unresolved_errors,
            'severity_distribution': severity_distribution,
            'layer_distribution': layer_distribution,
            'top_error_types': dict(top_error_types)
        }
        
        return Response(summary_data)


class DebugConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing debug configuration"""
    queryset = DebugConfiguration.objects.all()
    serializer_class = DebugConfigurationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['config_type', 'enabled']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class PerformanceThresholdViewSet(viewsets.ModelViewSet):
    """ViewSet for managing performance thresholds"""
    queryset = PerformanceThreshold.objects.all()
    serializer_class = PerformanceThresholdSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['metric_name', 'layer', 'component', 'enabled']
    ordering_fields = ['layer', 'metric_name']
    ordering = ['layer', 'metric_name']


class SystemHealthViewSet(viewsets.ViewSet):
    """ViewSet for system health monitoring"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get overall system health status"""
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        
        # Active workflows
        active_workflows = WorkflowSession.objects.filter(
            status='in_progress'
        ).count()
        
        # Recent errors
        recent_errors = ErrorLog.objects.filter(
            timestamp__gte=last_hour,
            severity__in=['error', 'critical']
        ).count()
        
        # Performance alerts
        performance_alerts = PerformanceSnapshot.objects.filter(
            timestamp__gte=last_hour,
            metric_value__gte=F('threshold_warning')
        ).count()
        
        # Layer-specific health
        layers = {}
        for layer in ['frontend', 'api', 'database', 'cache']:
            layer_errors = ErrorLog.objects.filter(
                layer=layer,
                timestamp__gte=last_hour,
                severity__in=['error', 'critical']
            ).count()
            
            layer_performance_issues = PerformanceSnapshot.objects.filter(
                layer=layer,
                timestamp__gte=last_hour,
                metric_value__gte=F('threshold_warning')
            ).count()
            
            layers[layer] = {
                'status': 'healthy' if layer_errors == 0 and layer_performance_issues == 0 else 'degraded',
                'errors': layer_errors,
                'performance_issues': layer_performance_issues
            }
        
        # Overall status
        overall_status = 'healthy'
        if recent_errors > 0 or performance_alerts > 0:
            overall_status = 'degraded'
        if recent_errors > 10 or performance_alerts > 5:
            overall_status = 'critical'
        
        health_data = {
            'overall_status': overall_status,
            'active_workflows': active_workflows,
            'recent_errors': recent_errors,
            'performance_alerts': performance_alerts,
            'layers': layers,
            'timestamp': now
        }
        
        serializer = SystemHealthSerializer(health_data)
        return Response(serializer.data)


class RouteDiscoveryViewSet(viewsets.ViewSet):
    """ViewSet for frontend route discovery operations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def scan(self, request):
        """Trigger a new route discovery scan"""
        try:
            service = RouteDiscoveryService()
            session = service.run_discovery()
            
            serializer = RouteDiscoverySessionSerializer(session)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': f'Route discovery failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def results(self, request):
        """Get the latest route discovery results"""
        try:
            service = RouteDiscoveryService()
            results = service.get_discovery_results()
            
            serializer = RouteDiscoveryResultSerializer(results)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': f'Failed to get discovery results: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def dependencies(self, request):
        """Get dependency mapping between frontend routes and API endpoints"""
        try:
            # Get all routes with their API calls
            routes = FrontendRoute.objects.prefetch_related('api_calls').all()
            
            # Get unique API endpoints
            api_endpoints = list(
                APICallDiscovery.objects.values_list('endpoint', flat=True).distinct()
            )
            
            # Get dependencies
            dependencies = []
            for route in routes:
                for api_call in route.api_calls.all():
                    dependencies.append({
                        'frontend_route': route.path,
                        'api_endpoint': api_call.endpoint,
                        'method': api_call.method,
                        'component': route.component_name
                    })
            
            data = {
                'frontend_routes': routes,
                'api_endpoints': api_endpoints,
                'dependencies': dependencies
            }
            
            serializer = DependencyMapSerializer(data)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': f'Failed to get dependency map: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def routes(self, request):
        """Get routes filtered by type"""
        route_type = request.query_params.get('type')
        
        queryset = FrontendRoute.objects.prefetch_related('api_calls').all()
        
        if route_type:
            queryset = queryset.filter(route_type=route_type)
        
        serializer = FrontendRouteSerializer(queryset, many=True)
        return Response({'results': serializer.data})
    
    @action(detail=False, methods=['get'], url_path='routes/(?P<route_path>.+)/api-calls')
    def route_api_calls(self, request, route_path=None):
        """Get API calls for a specific route"""
        try:
            # Decode the route path
            import urllib.parse
            decoded_path = urllib.parse.unquote(route_path)
            
            route = FrontendRoute.objects.get(path=decoded_path)
            api_calls = APICallDiscovery.objects.filter(frontend_route=route)
            
            serializer = APICallDiscoverySerializer(api_calls, many=True)
            return Response(serializer.data)
        
        except FrontendRoute.DoesNotExist:
            return Response(
                {'error': f'Route not found: {route_path}'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to get API calls: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Validate route discovery accuracy"""
        try:
            service = RouteDiscoveryService()
            results = service.validate_discovery_accuracy()
            
            serializer = RouteValidationResultSerializer(results)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': f'Validation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FrontendRouteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing frontend routes"""
    queryset = FrontendRoute.objects.all().prefetch_related('api_calls')
    serializer_class = FrontendRouteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['route_type', 'is_dynamic', 'is_valid']
    ordering_fields = ['path', 'discovered_at', 'route_type']
    ordering = ['path']
    search_fields = ['path', 'component_name']


class APICallDiscoveryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing discovered API calls"""
    queryset = APICallDiscovery.objects.all().select_related('frontend_route')
    serializer_class = APICallDiscoverySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['method', 'requires_authentication', 'is_valid', 'frontend_route']
    ordering_fields = ['endpoint', 'discovered_at', 'method']
    ordering = ['endpoint']
    search_fields = ['endpoint', 'component_file', 'function_name']


class RouteDiscoverySessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing route discovery sessions"""
    queryset = RouteDiscoverySession.objects.all()
    serializer_class = RouteDiscoverySessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['start_time', 'scan_duration_ms']
    ordering = ['-start_time']



class WorkflowTracingViewSet(viewsets.ViewSet):
    """ViewSet for workflow tracing operations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def start_workflow(self, request):
        """Start a new workflow trace"""
        try:
            workflow_type = request.data.get('workflow_type')
            metadata = request.data.get('metadata', {})
            correlation_id = request.data.get('correlation_id')
            
            if not workflow_type:
                return Response(
                    {'error': 'workflow_type is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create tracing engine
            engine = WorkflowTracingEngine(
                correlation_id=uuid.UUID(correlation_id) if correlation_id else None
            )
            
            # Start workflow
            session = engine.start_workflow(
                workflow_type=workflow_type,
                user=request.user,
                metadata=metadata
            )
            
            return Response({
                'correlation_id': str(session.correlation_id),
                'workflow_type': session.workflow_type,
                'status': session.status,
                'start_time': session.start_time.isoformat()
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to start workflow: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def complete_workflow(self, request):
        """Complete a workflow trace"""
        try:
            correlation_id = request.data.get('correlation_id')
            metadata = request.data.get('metadata', {})
            
            if not correlation_id:
                return Response(
                    {'error': 'correlation_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create tracing engine
            engine = WorkflowTracingEngine(correlation_id=uuid.UUID(correlation_id))
            
            # Complete workflow
            analysis = engine.complete_workflow(metadata=metadata)
            
            return Response(analysis)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to complete workflow: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def fail_workflow(self, request):
        """Fail a workflow trace"""
        try:
            correlation_id = request.data.get('correlation_id')
            error_message = request.data.get('error_message')
            metadata = request.data.get('metadata', {})
            
            if not correlation_id or not error_message:
                return Response(
                    {'error': 'correlation_id and error_message are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create tracing engine
            engine = WorkflowTracingEngine(correlation_id=uuid.UUID(correlation_id))
            
            # Fail workflow
            analysis = engine.fail_workflow(error_message=error_message, metadata=metadata)
            
            return Response(analysis)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to fail workflow: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def trace_events(self, request):
        """Handle trace events from frontend"""
        try:
            event_type = request.data.get('event_type')
            correlation_id = request.data.get('correlation_id')
            
            if not event_type or not correlation_id:
                return Response(
                    {'error': 'event_type and correlation_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Handle different event types
            if event_type == 'workflow_started':
                # Workflow already started, just acknowledge
                pass
            elif event_type == 'workflow_completed':
                # Update workflow metadata
                try:
                    session = WorkflowSession.objects.get(correlation_id=correlation_id)
                    session.metadata.update(request.data.get('metadata', {}))
                    session.save()
                except WorkflowSession.DoesNotExist:
                    pass
            elif event_type == 'workflow_failed':
                # Update workflow with failure info
                try:
                    session = WorkflowSession.objects.get(correlation_id=correlation_id)
                    session.status = 'failed'
                    session.end_time = timezone.now()
                    session.metadata.update(request.data.get('metadata', {}))
                    session.save()
                except WorkflowSession.DoesNotExist:
                    pass
            
            return Response({'status': 'acknowledged'})
            
        except Exception as e:
            return Response(
                {'error': f'Failed to handle trace event: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def errors(self, request):
        """Handle error events from frontend"""
        try:
            correlation_id = request.data.get('correlation_id')
            layer = request.data.get('layer', 'frontend')
            component = request.data.get('component')
            error_type = request.data.get('error_type')
            error_message = request.data.get('error_message')
            metadata = request.data.get('metadata', {})
            
            if not all([correlation_id, component, error_type, error_message]):
                return Response(
                    {'error': 'correlation_id, component, error_type, and error_message are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Log the error
            error_log = ErrorLogger.log_error(
                layer=layer,
                component=component,
                error_type=error_type,
                error_message=error_message,
                correlation_id=uuid.UUID(correlation_id),
                severity='error',
                metadata=metadata
            )
            
            return Response({
                'error_id': error_log.id,
                'status': 'logged'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to log error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def metrics(self, request):
        """Handle performance metrics from frontend"""
        try:
            correlation_id = request.data.get('correlation_id')
            layer = request.data.get('layer', 'frontend')
            component = request.data.get('component')
            metric_name = request.data.get('metric_name')
            metric_value = request.data.get('metric_value')
            metadata = request.data.get('metadata', {})
            
            if not all([correlation_id, component, metric_name, metric_value is not None]):
                return Response(
                    {'error': 'correlation_id, component, metric_name, and metric_value are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Record the metric
            snapshot = PerformanceMonitor.record_metric(
                layer=layer,
                component=component,
                metric_name=metric_name,
                metric_value=float(metric_value),
                correlation_id=uuid.UUID(correlation_id),
                metadata=metadata
            )
            
            return Response({
                'metric_id': snapshot.id,
                'status': 'recorded'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to record metric: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def analyze_timing(self, request):
        """Analyze timing for a specific workflow"""
        try:
            correlation_id = request.query_params.get('correlation_id')
            
            if not correlation_id:
                return Response(
                    {'error': 'correlation_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create timing analyzer
            analyzer = TimingAnalyzer(uuid.UUID(correlation_id))
            
            # Get timing analysis
            analysis = analyzer.analyze_workflow_timing()
            
            return Response(analysis)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to analyze timing: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                
    
    @action(detail=False, methods=['get'])
    def analyze_errors(self, request):
        """Analyze errors for a specific workflow"""
        try:
            correlation_id = request.query_params.get('correlation_id')
            
            if not correlation_id:
                return Response(
                    {'error': 'correlation_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create error tracker
            tracker = ErrorTracker(uuid.UUID(correlation_id))
            
            # Get error analysis
            analysis = tracker.analyze_error_patterns()
            
            return Response(analysis)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to analyze errors: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DatabaseMonitoringViewSet(viewsets.ViewSet):
    """ViewSet for database monitoring operations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Get database health status"""
        try:
            monitor = DatabaseHealthMonitor()
            health_status = monitor.check_database_health()
            
            return Response(health_status)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to check database health: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def performance_summary(self, request):
        """Get database performance summary"""
        try:
            hours = int(request.query_params.get('hours', 24))
            
            monitor = DatabaseHealthMonitor()
            summary = monitor.get_performance_summary(hours=hours)
            
            return Response(summary)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get performance summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

import uuid


class DatabaseHealthViewSet(viewsets.ViewSet):
    """ViewSet for database health monitoring"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get database health status"""
        try:
            monitor = DatabaseHealthMonitor()
            health_status = monitor.check_database_health()
            
            return Response(health_status)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to check database health: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def performance_summary(self, request):
        """Get database performance summary"""
        try:
            hours = int(request.query_params.get('hours', 24))
            
            monitor = DatabaseHealthMonitor()
            summary = monitor.get_performance_summary(hours=hours)
            
            return Response(summary)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get performance summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestingFrameworkViewSet(viewsets.ViewSet):
    """ViewSet for comprehensive testing framework operations"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def run_tests(self, request):
        """Run comprehensive tests"""
        try:
            from .testing_framework import ComprehensiveTestingFramework
            
            test_type = request.data.get('test_type', 'all')
            target_url = request.data.get('target_url')
            
            framework = ComprehensiveTestingFramework()
            
            if test_type == 'api':
                results = framework.run_api_tests(target_url)
            elif test_type == 'frontend':
                results = framework.run_frontend_tests(target_url)
            elif test_type == 'database':
                results = framework.run_database_tests()
            elif test_type == 'integration':
                results = framework.run_integration_tests(target_url)
            else:
                results = framework.run_all_tests(target_url)
            
            return Response(results, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to run tests: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def test_status(self, request):
        """Get current test execution status"""
        try:
            from .testing_framework import ComprehensiveTestingFramework
            
            framework = ComprehensiveTestingFramework()
            status_info = framework.get_test_status()
            
            return Response(status_info)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get test status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def test_history(self, request):
        """Get test execution history"""
        try:
            from .testing_framework import ComprehensiveTestingFramework
            
            limit = int(request.query_params.get('limit', 10))
            test_type = request.query_params.get('test_type')
            
            framework = ComprehensiveTestingFramework()
            history = framework.get_test_history(limit=limit, test_type=test_type)
            
            return Response(history)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get test history: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )