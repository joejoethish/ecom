"""
Performance Monitoring Views

This module provides REST API endpoints for the performance monitoring service.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json

from .performance_monitoring import (
    get_performance_monitoring_service,
    MetricData, ThresholdAlert, OptimizationRecommendation, TrendAnalysis
)
from .models import PerformanceSnapshot, PerformanceThreshold, ErrorLog
from .serializers import (
    PerformanceSnapshotSerializer, PerformanceThresholdSerializer
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health_summary(request):
    """Get comprehensive system health summary"""
    try:
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        summary = service.get_system_health_summary()
        return Response(summary, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting system health summary: {e}")
        return Response(
            {'error': 'Failed to get system health summary', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_metrics(request):
    """Get performance metrics with filtering and pagination"""
    try:
        # Parse query parameters
        layer = request.GET.get('layer')
        component = request.GET.get('component')
        metric_name = request.GET.get('metric_name')
        hours = int(request.GET.get('hours', 24))
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 100))
        
        # Build query filters
        since = timezone.now() - timedelta(hours=hours)
        filters = {'timestamp__gte': since}
        
        if layer:
            filters['layer'] = layer
        if component:
            filters['component'] = component
        if metric_name:
            filters['metric_name'] = metric_name
        
        # Get metrics
        metrics_query = PerformanceSnapshot.objects.filter(**filters).order_by('-timestamp')
        
        # Paginate results
        paginator = Paginator(metrics_query, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = PerformanceSnapshotSerializer(page_obj.object_list, many=True)
        
        return Response({
            'metrics': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'filters': {
                'layer': layer,
                'component': component,
                'metric_name': metric_name,
                'hours': hours
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return Response(
            {'error': 'Failed to get performance metrics', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_trends(request):
    """Get performance trend analysis"""
    try:
        # Parse query parameters
        metric_name = request.GET.get('metric_name')
        layer = request.GET.get('layer')
        component = request.GET.get('component')
        hours = int(request.GET.get('hours', 168))  # Default 7 days
        
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        # Get trend analysis
        trends = service.trend_analyzer.analyze_trends(
            metric_name=metric_name,
            layer=layer,
            component=component,
            hours=hours
        )
        
        # Convert to serializable format
        trends_data = []
        for trend in trends:
            trends_data.append({
                'metric_name': trend.metric_name,
                'layer': trend.layer,
                'component': trend.component,
                'trend_direction': trend.trend_direction,
                'trend_strength': trend.trend_strength,
                'current_average': trend.current_average,
                'historical_average': trend.historical_average,
                'percentage_change': trend.percentage_change,
                'data_points': trend.data_points,
                'analysis_period_hours': trend.analysis_period_hours
            })
        
        # Get trend summary
        trend_summary = service.trend_analyzer.get_trend_summary(hours=hours)
        
        return Response({
            'trends': trends_data,
            'summary': trend_summary,
            'analysis_parameters': {
                'metric_name': metric_name,
                'layer': layer,
                'component': component,
                'hours': hours
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting performance trends: {e}")
        return Response(
            {'error': 'Failed to get performance trends', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def optimization_recommendations(request):
    """Get optimization recommendations"""
    try:
        hours = int(request.GET.get('hours', 24))
        priority = request.GET.get('priority')  # 'high', 'medium', 'low'
        category = request.GET.get('category')  # 'database', 'api', 'frontend', 'system'
        
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        # Get recommendations
        recommendations = service.optimization_engine.analyze_performance_issues(hours=hours)
        
        # Filter by priority if specified
        if priority:
            recommendations = [r for r in recommendations if r.priority == priority]
        
        # Filter by category if specified
        if category:
            recommendations = [r for r in recommendations if r.category == category]
        
        # Convert to serializable format
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'category': rec.category,
                'priority': rec.priority,
                'title': rec.title,
                'description': rec.description,
                'implementation_steps': rec.implementation_steps,
                'expected_improvement': rec.expected_improvement,
                'affected_components': rec.affected_components,
                'confidence_score': rec.confidence_score
            })
        
        return Response({
            'recommendations': recommendations_data,
            'total_count': len(recommendations_data),
            'filters': {
                'hours': hours,
                'priority': priority,
                'category': category
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {e}")
        return Response(
            {'error': 'Failed to get optimization recommendations', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def performance_thresholds(request):
    """Manage performance thresholds"""
    if request.method == 'GET':
        try:
            # Get all thresholds with optional filtering
            layer = request.GET.get('layer')
            metric_name = request.GET.get('metric_name')
            enabled_only = request.GET.get('enabled_only', 'false').lower() == 'true'
            
            filters = {}
            if layer:
                filters['layer'] = layer
            if metric_name:
                filters['metric_name'] = metric_name
            if enabled_only:
                filters['enabled'] = True
            
            thresholds = PerformanceThreshold.objects.filter(**filters).order_by('layer', 'metric_name')
            serializer = PerformanceThresholdSerializer(thresholds, many=True)
            
            return Response({
                'thresholds': serializer.data,
                'total_count': thresholds.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting performance thresholds: {e}")
            return Response(
                {'error': 'Failed to get performance thresholds', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
            
            service = get_performance_monitoring_service()
            if not service._initialized:
                service.initialize()
            
            # Create or update threshold
            threshold = service.threshold_manager.create_threshold(
                metric_name=data['metric_name'],
                layer=data['layer'],
                component=data.get('component', ''),
                warning_threshold=data['warning_threshold'],
                critical_threshold=data['critical_threshold'],
                alert_on_warning=data.get('alert_on_warning', True),
                alert_on_critical=data.get('alert_on_critical', True)
            )
            
            serializer = PerformanceThresholdSerializer(threshold)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating performance threshold: {e}")
            return Response(
                {'error': 'Failed to create performance threshold', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def collect_manual_metric(request):
    """Manually collect a performance metric"""
    try:
        data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
        
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        # Collect the metric
        service.metrics_collector.collect_manual_metric(
            layer=data['layer'],
            component=data['component'],
            metric_name=data['metric_name'],
            metric_value=float(data['metric_value']),
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {})
        )
        
        return Response({
            'message': 'Metric collected successfully',
            'metric': {
                'layer': data['layer'],
                'component': data['component'],
                'metric_name': data['metric_name'],
                'metric_value': data['metric_value']
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error collecting manual metric: {e}")
        return Response(
            {'error': 'Failed to collect metric', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def metrics_summary(request):
    """Get summary of available metrics"""
    try:
        hours = int(request.GET.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        # Get unique combinations of layer, component, and metric_name
        metrics_summary = PerformanceSnapshot.objects.filter(
            timestamp__gte=since
        ).values('layer', 'component', 'metric_name').annotate(
            count=models.Count('id'),
            avg_value=models.Avg('metric_value'),
            min_value=models.Min('metric_value'),
            max_value=models.Max('metric_value'),
            latest_timestamp=models.Max('timestamp')
        ).order_by('layer', 'component', 'metric_name')
        
        # Group by layer
        layers_data = {}
        for metric in metrics_summary:
            layer = metric['layer']
            if layer not in layers_data:
                layers_data[layer] = {
                    'components': {},
                    'total_metrics': 0,
                    'total_data_points': 0
                }
            
            component = metric['component']
            if component not in layers_data[layer]['components']:
                layers_data[layer]['components'][component] = {
                    'metrics': [],
                    'data_points': 0
                }
            
            layers_data[layer]['components'][component]['metrics'].append({
                'name': metric['metric_name'],
                'count': metric['count'],
                'avg_value': metric['avg_value'],
                'min_value': metric['min_value'],
                'max_value': metric['max_value'],
                'latest_timestamp': metric['latest_timestamp'].isoformat()
            })
            
            layers_data[layer]['components'][component]['data_points'] += metric['count']
            layers_data[layer]['total_metrics'] += 1
            layers_data[layer]['total_data_points'] += metric['count']
        
        return Response({
            'summary': layers_data,
            'analysis_period_hours': hours,
            'total_layers': len(layers_data),
            'total_metrics': sum(layer['total_metrics'] for layer in layers_data.values()),
            'total_data_points': sum(layer['total_data_points'] for layer in layers_data.values())
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        return Response(
            {'error': 'Failed to get metrics summary', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_service(request):
    """Initialize the performance monitoring service"""
    try:
        service = get_performance_monitoring_service()
        service.initialize()
        
        return Response({
            'message': 'Performance monitoring service initialized successfully',
            'status': 'initialized'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error initializing performance monitoring service: {e}")
        return Response(
            {'error': 'Failed to initialize service', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shutdown_service(request):
    """Shutdown the performance monitoring service"""
    try:
        service = get_performance_monitoring_service()
        service.shutdown()
        
        return Response({
            'message': 'Performance monitoring service shutdown successfully',
            'status': 'shutdown'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error shutting down performance monitoring service: {e}")
        return Response(
            {'error': 'Failed to shutdown service', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@method_decorator(csrf_exempt, name='dispatch')
class PerformanceMonitoringAPIView(View):
    """Class-based view for performance monitoring operations"""
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests for performance monitoring data"""
        try:
            action = request.GET.get('action', 'health')
            
            if action == 'health':
                return self._get_health_status()
            elif action == 'metrics':
                return self._get_metrics(request)
            elif action == 'trends':
                return self._get_trends(request)
            elif action == 'recommendations':
                return self._get_recommendations(request)
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except Exception as e:
            logger.error(f"Error in PerformanceMonitoringAPIView GET: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests for performance monitoring operations"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'collect_metric':
                return self._collect_metric(data)
            elif action == 'create_threshold':
                return self._create_threshold(data)
            elif action == 'initialize':
                return self._initialize_service()
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except Exception as e:
            logger.error(f"Error in PerformanceMonitoringAPIView POST: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def _get_health_status(self):
        """Get system health status"""
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        summary = service.get_system_health_summary()
        return JsonResponse(summary)
    
    def _get_metrics(self, request):
        """Get performance metrics"""
        layer = request.GET.get('layer')
        component = request.GET.get('component')
        hours = int(request.GET.get('hours', 24))
        
        since = timezone.now() - timedelta(hours=hours)
        filters = {'timestamp__gte': since}
        
        if layer:
            filters['layer'] = layer
        if component:
            filters['component'] = component
        
        metrics = PerformanceSnapshot.objects.filter(**filters).order_by('-timestamp')[:100]
        serializer = PerformanceSnapshotSerializer(metrics, many=True)
        
        return JsonResponse({'metrics': serializer.data})
    
    def _get_trends(self, request):
        """Get performance trends"""
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        hours = int(request.GET.get('hours', 168))
        trends = service.trend_analyzer.analyze_trends(hours=hours)
        
        trends_data = []
        for trend in trends:
            trends_data.append({
                'metric_name': trend.metric_name,
                'layer': trend.layer,
                'component': trend.component,
                'trend_direction': trend.trend_direction,
                'trend_strength': trend.trend_strength,
                'percentage_change': trend.percentage_change
            })
        
        return JsonResponse({'trends': trends_data})
    
    def _get_recommendations(self, request):
        """Get optimization recommendations"""
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        hours = int(request.GET.get('hours', 24))
        recommendations = service.optimization_engine.analyze_performance_issues(hours=hours)
        
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'category': rec.category,
                'priority': rec.priority,
                'title': rec.title,
                'description': rec.description,
                'expected_improvement': rec.expected_improvement,
                'confidence_score': rec.confidence_score
            })
        
        return JsonResponse({'recommendations': recommendations_data})
    
    def _collect_metric(self, data):
        """Collect a manual metric"""
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        service.metrics_collector.collect_manual_metric(
            layer=data['layer'],
            component=data['component'],
            metric_name=data['metric_name'],
            metric_value=float(data['metric_value']),
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {})
        )
        
        return JsonResponse({'message': 'Metric collected successfully'})
    
    def _create_threshold(self, data):
        """Create a performance threshold"""
        service = get_performance_monitoring_service()
        if not service._initialized:
            service.initialize()
        
        threshold = service.threshold_manager.create_threshold(
            metric_name=data['metric_name'],
            layer=data['layer'],
            component=data.get('component', ''),
            warning_threshold=data['warning_threshold'],
            critical_threshold=data['critical_threshold']
        )
        
        serializer = PerformanceThresholdSerializer(threshold)
        return JsonResponse(serializer.data)
    
    def _initialize_service(self):
        """Initialize the performance monitoring service"""
        service = get_performance_monitoring_service()
        service.initialize()
        
        return JsonResponse({'message': 'Service initialized successfully'})