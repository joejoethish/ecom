"""
Dashboard API views for the E2E Workflow Debugging System.

This module provides REST API endpoints for the interactive debugging dashboard,
including real-time data retrieval, system health monitoring, and manual testing tools.
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

from django.utils import timezone
from django.db.models import Count, Avg, Q, F, Max
from django.db import models
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, DebugConfiguration, PerformanceThreshold,
    FrontendRoute, APICallDiscovery, RouteDiscoverySession
)
from .serializers import (
    WorkflowSessionSerializer, TraceStepSerializer, PerformanceSnapshotSerializer,
    ErrorLogSerializer, SystemHealthSerializer, DashboardDataSerializer,
    RealtimeUpdateSerializer, DebugReportSerializer, APITestRequestSerializer,
    APITestResponseSerializer
)
from .services import WorkflowTracingEngine, TimingAnalyzer, ErrorTracker
from .utils import PerformanceMonitor, ErrorLogger
from .testing_framework import APITestingFramework


class DashboardDataViewSet(viewsets.ViewSet):
    """
    ViewSet for retrieving comprehensive dashboard data.
    Provides aggregated data for the debugging dashboard interface.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get comprehensive dashboard data"""
        try:
            now = timezone.now()
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(hours=24)
            
            # System Health Overview
            system_health = self._get_system_health(now, last_hour)
            
            # Active Workflows
            active_workflows = self._get_active_workflows()
            
            # Recent Errors
            recent_errors = self._get_recent_errors(last_24h)
            
            # Performance Metrics
            performance_metrics = self._get_performance_metrics(last_hour)
            
            # Optimization Recommendations
            optimization_recommendations = self._get_optimization_recommendations()
            
            # Workflow Statistics
            workflow_stats = self._get_workflow_statistics(last_24h)
            
            # Route Discovery Status
            route_discovery_status = self._get_route_discovery_status()
            
            dashboard_data = {
                'timestamp': now,
                'system_health': system_health,
                'active_workflows': active_workflows,
                'recent_errors': recent_errors,
                'performance_metrics': performance_metrics,
                'optimization_recommendations': optimization_recommendations,
                'workflow_stats': workflow_stats,
                'route_discovery_status': route_discovery_status
            }
            
            serializer = DashboardDataSerializer(dashboard_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve dashboard data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_system_health(self, now: datetime, last_hour: datetime) -> Dict[str, Any]:
        """Get system health overview"""
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
        
        return {
            'overall_status': overall_status,
            'active_workflows': active_workflows,
            'recent_errors': recent_errors,
            'performance_alerts': performance_alerts,
            'layers': layers,
            'timestamp': now
        }
    
    def _get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get currently active workflows"""
        active_workflows = WorkflowSession.objects.filter(
            status='in_progress'
        ).select_related('user').prefetch_related('trace_steps')[:10]
        
        return WorkflowSessionSerializer(active_workflows, many=True).data
    
    def _get_recent_errors(self, since: datetime) -> List[Dict[str, Any]]:
        """Get recent errors"""
        recent_errors = ErrorLog.objects.filter(
            timestamp__gte=since
        ).select_related('user').order_by('-timestamp')[:20]
        
        return ErrorLogSerializer(recent_errors, many=True).data
    
    def _get_performance_metrics(self, since: datetime) -> Dict[str, Any]:
        """Get performance metrics summary"""
        metrics = PerformanceSnapshot.objects.filter(
            timestamp__gte=since
        ).values('layer', 'metric_name').annotate(
            avg_value=Avg('metric_value'),
            max_value=Max('metric_value'),
            count=Count('id')
        )
        
        # Group by layer
        layer_metrics = {}
        for metric in metrics:
            layer = metric['layer']
            if layer not in layer_metrics:
                layer_metrics[layer] = {}
            
            layer_metrics[layer][metric['metric_name']] = {
                'average': round(metric['avg_value'], 2),
                'maximum': round(metric['max_value'], 2),
                'count': metric['count']
            }
        
        return layer_metrics
    
    def _get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on performance data"""
        recommendations = []
        
        # Check for slow API responses
        slow_apis = PerformanceSnapshot.objects.filter(
            layer='api',
            metric_name='response_time',
            metric_value__gt=1000  # > 1 second
        ).values('component').annotate(
            avg_time=Avg('metric_value')
        ).order_by('-avg_time')[:5]
        
        for api in slow_apis:
            recommendations.append({
                'category': 'api',
                'priority': 'high',
                'description': f"API endpoint {api['component']} has slow response times",
                'implementation_steps': [
                    'Review database queries for N+1 problems',
                    'Add database indexes for frequently queried fields',
                    'Consider caching for read-heavy operations',
                    'Optimize serializer performance'
                ],
                'expected_improvement': f"Reduce response time from {api['avg_time']:.0f}ms to <500ms"
            })
        
        # Check for high error rates
        error_prone_components = ErrorLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).values('layer', 'component').annotate(
            error_count=Count('id')
        ).filter(error_count__gt=5).order_by('-error_count')[:3]
        
        for component in error_prone_components:
            recommendations.append({
                'category': 'reliability',
                'priority': 'medium',
                'description': f"{component['layer']}.{component['component']} has high error rate",
                'implementation_steps': [
                    'Review error logs for common patterns',
                    'Add input validation and error handling',
                    'Implement circuit breaker pattern',
                    'Add monitoring and alerting'
                ],
                'expected_improvement': f"Reduce error count from {component['error_count']} to <2 per day"
            })
        
        return recommendations
    
    def _get_workflow_statistics(self, since: datetime) -> Dict[str, Any]:
        """Get workflow statistics"""
        workflows = WorkflowSession.objects.filter(start_time__gte=since)
        
        total_workflows = workflows.count()
        completed_workflows = workflows.filter(status='completed').count()
        failed_workflows = workflows.filter(status='failed').count()
        
        # Average duration for completed workflows
        completed_with_duration = workflows.filter(
            status='completed',
            end_time__isnull=False
        )
        
        avg_duration_ms = 0
        if completed_with_duration.exists():
            durations = []
            for workflow in completed_with_duration:
                delta = workflow.end_time - workflow.start_time
                durations.append(delta.total_seconds() * 1000)
            avg_duration_ms = sum(durations) / len(durations)
        
        # Workflow types distribution
        workflow_types = dict(
            workflows.values('workflow_type').annotate(
                count=Count('id')
            ).values_list('workflow_type', 'count')
        )
        
        return {
            'total_workflows': total_workflows,
            'completed_workflows': completed_workflows,
            'failed_workflows': failed_workflows,
            'success_rate': round((completed_workflows / total_workflows * 100) if total_workflows > 0 else 0, 1),
            'average_duration_ms': round(avg_duration_ms, 0),
            'workflow_types': workflow_types
        }
    
    def _get_route_discovery_status(self) -> Dict[str, Any]:
        """Get route discovery status"""
        latest_session = RouteDiscoverySession.objects.order_by('-start_time').first()
        
        total_routes = FrontendRoute.objects.count()
        total_api_calls = APICallDiscovery.objects.count()
        
        return {
            'total_routes': total_routes,
            'total_api_calls': total_api_calls,
            'last_scan': latest_session.start_time if latest_session else None,
            'last_scan_status': latest_session.status if latest_session else None,
            'last_scan_duration_ms': latest_session.scan_duration_ms if latest_session else None
        }
    
    @action(detail=False, methods=['get'])
    def realtime_updates(self, request):
        """Get real-time updates for dashboard"""
        try:
            # Get timestamp from query params for incremental updates
            since_param = request.query_params.get('since')
            if since_param:
                since = datetime.fromisoformat(since_param.replace('Z', '+00:00'))
            else:
                since = timezone.now() - timedelta(minutes=5)
            
            # Get updates since timestamp
            new_workflows = WorkflowSession.objects.filter(
                start_time__gte=since
            ).select_related('user')[:10]
            
            new_errors = ErrorLog.objects.filter(
                timestamp__gte=since
            ).select_related('user')[:10]
            
            new_metrics = PerformanceSnapshot.objects.filter(
                timestamp__gte=since
            )[:20]
            
            updates = {
                'timestamp': timezone.now(),
                'new_workflows': WorkflowSessionSerializer(new_workflows, many=True).data,
                'new_errors': ErrorLogSerializer(new_errors, many=True).data,
                'new_metrics': PerformanceSnapshotSerializer(new_metrics, many=True).data,
                'has_updates': new_workflows.exists() or new_errors.exists() or new_metrics.exists()
            }
            
            serializer = RealtimeUpdateSerializer(updates)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get realtime updates: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportGenerationViewSet(viewsets.ViewSet):
    """
    ViewSet for generating debugging reports and summaries.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate_workflow_report(self, request):
        """Generate a comprehensive workflow analysis report"""
        try:
            correlation_id = request.data.get('correlation_id')
            if not correlation_id:
                return Response(
                    {'error': 'correlation_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get workflow session
            try:
                workflow = WorkflowSession.objects.get(correlation_id=correlation_id)
            except WorkflowSession.DoesNotExist:
                return Response(
                    {'error': f'Workflow not found: {correlation_id}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Generate comprehensive report
            report = self._generate_workflow_analysis_report(workflow)
            
            serializer = DebugReportSerializer(report)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate workflow report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def generate_system_health_report(self, request):
        """Generate a system health summary report"""
        try:
            time_range = request.data.get('time_range', '24h')
            
            # Parse time range
            if time_range == '1h':
                since = timezone.now() - timedelta(hours=1)
            elif time_range == '24h':
                since = timezone.now() - timedelta(hours=24)
            elif time_range == '7d':
                since = timezone.now() - timedelta(days=7)
            else:
                since = timezone.now() - timedelta(hours=24)
            
            # Generate system health report
            report = self._generate_system_health_report(since)
            
            serializer = DebugReportSerializer(report)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate system health report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def generate_performance_report(self, request):
        """Generate a performance analysis report"""
        try:
            layer = request.data.get('layer')
            component = request.data.get('component')
            time_range = request.data.get('time_range', '24h')
            
            # Parse time range
            if time_range == '1h':
                since = timezone.now() - timedelta(hours=1)
            elif time_range == '24h':
                since = timezone.now() - timedelta(hours=24)
            elif time_range == '7d':
                since = timezone.now() - timedelta(days=7)
            else:
                since = timezone.now() - timedelta(hours=24)
            
            # Generate performance report
            report = self._generate_performance_report(since, layer, component)
            
            serializer = DebugReportSerializer(report)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate performance report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_workflow_analysis_report(self, workflow: WorkflowSession) -> Dict[str, Any]:
        """Generate detailed workflow analysis report"""
        # Get trace steps
        trace_steps = workflow.trace_steps.all().order_by('start_time')
        
        # Get related errors
        errors = ErrorLog.objects.filter(
            correlation_id=workflow.correlation_id
        ).order_by('timestamp')
        
        # Get performance metrics
        metrics = PerformanceSnapshot.objects.filter(
            correlation_id=workflow.correlation_id
        ).order_by('timestamp')
        
        # Calculate timing analysis
        timing_analyzer = TimingAnalyzer(workflow.correlation_id)
        timing_analysis = timing_analyzer.analyze_workflow_timing()
        
        # Generate summary
        duration_ms = 0
        if workflow.end_time and workflow.start_time:
            delta = workflow.end_time - workflow.start_time
            duration_ms = int(delta.total_seconds() * 1000)
        
        return {
            'report_type': 'workflow_analysis',
            'generated_at': timezone.now(),
            'workflow': {
                'correlation_id': str(workflow.correlation_id),
                'workflow_type': workflow.workflow_type,
                'status': workflow.status,
                'start_time': workflow.start_time,
                'end_time': workflow.end_time,
                'duration_ms': duration_ms,
                'user': workflow.user.username if workflow.user else None
            },
            'trace_steps': TraceStepSerializer(trace_steps, many=True).data,
            'errors': ErrorLogSerializer(errors, many=True).data,
            'performance_metrics': PerformanceSnapshotSerializer(metrics, many=True).data,
            'timing_analysis': timing_analysis,
            'summary': {
                'total_steps': trace_steps.count(),
                'completed_steps': trace_steps.filter(status='completed').count(),
                'failed_steps': trace_steps.filter(status='failed').count(),
                'total_errors': errors.count(),
                'critical_errors': errors.filter(severity='critical').count(),
                'performance_issues': metrics.filter(
                    metric_value__gte=F('threshold_warning')
                ).count()
            }
        }
    
    def _generate_system_health_report(self, since: datetime) -> Dict[str, Any]:
        """Generate system health report"""
        # Workflow statistics
        workflows = WorkflowSession.objects.filter(start_time__gte=since)
        workflow_stats = {
            'total': workflows.count(),
            'completed': workflows.filter(status='completed').count(),
            'failed': workflows.filter(status='failed').count(),
            'in_progress': workflows.filter(status='in_progress').count()
        }
        
        # Error statistics
        errors = ErrorLog.objects.filter(timestamp__gte=since)
        error_stats = {
            'total': errors.count(),
            'critical': errors.filter(severity='critical').count(),
            'error': errors.filter(severity='error').count(),
            'warning': errors.filter(severity='warning').count(),
            'by_layer': dict(errors.values('layer').annotate(count=Count('id')).values_list('layer', 'count'))
        }
        
        # Performance statistics
        metrics = PerformanceSnapshot.objects.filter(timestamp__gte=since)
        performance_stats = {
            'total_metrics': metrics.count(),
            'alerts': metrics.filter(metric_value__gte=F('threshold_warning')).count(),
            'critical_alerts': metrics.filter(metric_value__gte=F('threshold_critical')).count(),
            'by_layer': dict(metrics.values('layer').annotate(count=Count('id')).values_list('layer', 'count'))
        }
        
        return {
            'report_type': 'system_health',
            'generated_at': timezone.now(),
            'time_range': {
                'since': since,
                'duration_hours': (timezone.now() - since).total_seconds() / 3600
            },
            'workflow_stats': workflow_stats,
            'error_stats': error_stats,
            'performance_stats': performance_stats,
            'overall_health': self._calculate_overall_health(workflow_stats, error_stats, performance_stats)
        }
    
    def _generate_performance_report(self, since: datetime, layer: str = None, component: str = None) -> Dict[str, Any]:
        """Generate performance analysis report"""
        # Filter metrics
        metrics_query = PerformanceSnapshot.objects.filter(timestamp__gte=since)
        if layer:
            metrics_query = metrics_query.filter(layer=layer)
        if component:
            metrics_query = metrics_query.filter(component=component)
        
        metrics = metrics_query.order_by('timestamp')
        
        # Calculate statistics
        metric_stats = {}
        for metric_name in ['response_time', 'memory_usage', 'cpu_usage', 'query_count']:
            metric_data = metrics.filter(metric_name=metric_name)
            if metric_data.exists():
                metric_stats[metric_name] = {
                    'count': metric_data.count(),
                    'average': metric_data.aggregate(avg=Avg('metric_value'))['avg'],
                    'maximum': metric_data.aggregate(max=Max('metric_value'))['max'],
                    'minimum': metric_data.aggregate(min=models.Min('metric_value'))['min'],
                    'alerts': metric_data.filter(metric_value__gte=F('threshold_warning')).count()
                }
        
        return {
            'report_type': 'performance_analysis',
            'generated_at': timezone.now(),
            'filters': {
                'layer': layer,
                'component': component,
                'since': since
            },
            'metric_statistics': metric_stats,
            'total_metrics': metrics.count(),
            'performance_alerts': metrics.filter(metric_value__gte=F('threshold_warning')).count(),
            'recommendations': self._get_performance_recommendations(metrics)
        }
    
    def _calculate_overall_health(self, workflow_stats: Dict, error_stats: Dict, performance_stats: Dict) -> str:
        """Calculate overall system health score"""
        # Simple health calculation based on error rates and performance alerts
        total_workflows = workflow_stats['total']
        failed_workflows = workflow_stats['failed']
        total_errors = error_stats['total']
        critical_errors = error_stats['critical']
        performance_alerts = performance_stats['alerts']
        
        if total_workflows == 0:
            return 'unknown'
        
        failure_rate = failed_workflows / total_workflows
        
        if critical_errors > 0 or failure_rate > 0.1 or performance_alerts > 10:
            return 'critical'
        elif total_errors > 5 or failure_rate > 0.05 or performance_alerts > 5:
            return 'degraded'
        else:
            return 'healthy'
    
    def _get_performance_recommendations(self, metrics) -> List[Dict[str, Any]]:
        """Get performance recommendations based on metrics"""
        recommendations = []
        
        # Check for high response times
        slow_responses = metrics.filter(
            metric_name='response_time',
            metric_value__gt=1000
        ).values('component').annotate(
            avg_time=Avg('metric_value')
        ).order_by('-avg_time')[:3]
        
        for response in slow_responses:
            recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'description': f"Component {response['component']} has slow response times",
                'suggestion': f"Average response time is {response['avg_time']:.0f}ms, consider optimization"
            })
        
        return recommendations


class ManualAPITestingViewSet(viewsets.ViewSet):
    """
    ViewSet for manual API testing from the dashboard.
    Allows testing API endpoints with custom payloads and headers.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def test_endpoint(self, request):
        """Test a specific API endpoint with custom parameters"""
        try:
            # Validate request data
            serializer = APITestRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid request data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            test_data = serializer.validated_data
            
            # Create testing framework instance
            testing_framework = APITestingFramework()
            
            # Execute the test
            test_result = testing_framework.test_single_endpoint(
                method=test_data['method'],
                endpoint=test_data['endpoint'],
                payload=test_data.get('payload'),
                headers=test_data.get('headers', {}),
                expected_status=test_data.get('expected_status')
            )
            
            # Format response
            response_data = {
                'test_id': str(uuid.uuid4()),
                'timestamp': timezone.now(),
                'request': test_data,
                'response': test_result,
                'success': test_result.get('success', False)
            }
            
            response_serializer = APITestResponseSerializer(response_data)
            return Response(response_serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'API test failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def test_workflow(self, request):
        """Test a complete workflow sequence"""
        try:
            workflow_type = request.data.get('workflow_type')
            test_data = request.data.get('test_data', {})
            
            if not workflow_type:
                return Response(
                    {'error': 'workflow_type is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create testing framework instance
            testing_framework = APITestingFramework()
            
            # Execute workflow test
            test_result = testing_framework.test_workflow_sequence(
                workflow_type=workflow_type,
                test_data=test_data,
                user=request.user
            )
            
            response_data = {
                'test_id': str(uuid.uuid4()),
                'timestamp': timezone.now(),
                'workflow_type': workflow_type,
                'test_data': test_data,
                'result': test_result,
                'success': test_result.get('success', False)
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {'error': f'Workflow test failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def available_endpoints(self, request):
        """Get list of available API endpoints for testing"""
        try:
            # Get discovered API endpoints
            api_calls = APICallDiscovery.objects.filter(
                is_valid=True
            ).values('method', 'endpoint', 'requires_authentication').distinct()
            
            # Group by endpoint
            endpoints = {}
            for call in api_calls:
                endpoint = call['endpoint']
                if endpoint not in endpoints:
                    endpoints[endpoint] = {
                        'endpoint': endpoint,
                        'methods': [],
                        'requires_authentication': call['requires_authentication']
                    }
                endpoints[endpoint]['methods'].append(call['method'])
            
            return Response({
                'endpoints': list(endpoints.values()),
                'total_count': len(endpoints)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get available endpoints: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def test_history(self, request):
        """Get history of manual API tests"""
        try:
            # This would typically be stored in a database table
            # For now, return a placeholder response
            return Response({
                'test_history': [],
                'message': 'Test history feature will be implemented with persistent storage'
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get test history: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_health_check(request):
    """Simple health check endpoint for dashboard backend"""
    try:
        # Check database connectivity
        WorkflowSession.objects.count()
        
        # Check basic functionality
        now = timezone.now()
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': now,
            'version': '1.0.0',
            'services': {
                'database': 'connected',
                'api': 'operational',
                'dashboard': 'ready'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now()
        }, status=500)


class DashboardConfigurationViewSet(viewsets.ViewSet):
    """
    ViewSet for managing dashboard configuration and settings.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get dashboard configuration"""
        try:
            # Get dashboard-specific configurations
            dashboard_configs = DebugConfiguration.objects.filter(
                config_type='dashboard_settings',
                enabled=True
            )
            
            config_data = {}
            for config in dashboard_configs:
                config_data[config.name] = config.config_data
            
            # Default configuration if none exists
            if not config_data:
                config_data = {
                    'refresh_interval': 30,  # seconds
                    'max_workflow_display': 10,
                    'max_error_display': 20,
                    'performance_chart_points': 50,
                    'enable_realtime_updates': True,
                    'enable_notifications': True
                }
            
            return Response({
                'configuration': config_data,
                'last_updated': timezone.now()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get dashboard configuration: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def update_configuration(self, request):
        """Update dashboard configuration"""
        try:
            config_name = request.data.get('name', 'dashboard_settings')
            config_data = request.data.get('config_data', {})
            
            # Update or create configuration
            config, created = DebugConfiguration.objects.update_or_create(
                name=config_name,
                config_type='dashboard_settings',
                defaults={
                    'config_data': config_data,
                    'enabled': True,
                    'description': 'Dashboard configuration settings'
                }
            )
            
            return Response({
                'success': True,
                'config_id': config.id,
                'created': created,
                'updated_at': config.updated_at
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to update dashboard configuration: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )