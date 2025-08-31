"""
Production Monitoring Dashboard

This module provides a comprehensive dashboard for production system monitoring,
including real-time metrics, alerts, and system status visualization.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import models
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
import logging

from .models import (
    PerformanceSnapshot, PerformanceThreshold, ErrorLog, 
    WorkflowSession, TraceStep
)
from .production_monitoring import (
    production_logger, alerting_system, health_check_service
)
from .performance_monitoring import MetricsCollector, OptimizationEngine

logger = logging.getLogger(__name__)


def is_admin_or_staff(user):
    """Check if user is admin or staff for dashboard access"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_admin_or_staff)
def production_dashboard_view(request):
    """
    Main production monitoring dashboard view.
    Renders the dashboard HTML template with initial data.
    """
    try:
        # Get initial dashboard data
        system_status = health_check_service.run_all_health_checks()
        active_alerts = alerting_system.get_active_alerts()
        
        # Get recent performance summary
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_metrics = PerformanceSnapshot.objects.filter(
            timestamp__gte=one_hour_ago
        ).count()
        
        recent_errors = ErrorLog.objects.filter(
            timestamp__gte=one_hour_ago
        ).count()
        
        context = {
            'system_status': system_status.status,
            'active_alerts_count': len(active_alerts),
            'recent_metrics_count': recent_metrics,
            'recent_errors_count': recent_errors,
            'dashboard_title': 'Production Monitoring Dashboard',
            'refresh_interval': 30,  # seconds
        }
        
        return render(request, 'debugging/production_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Production dashboard view failed: {e}")
        return render(request, 'debugging/dashboard_error.html', {
            'error_message': str(e)
        })


@require_http_methods(["GET"])
@user_passes_test(is_admin_or_staff)
def dashboard_data_api(request):
    """
    API endpoint for dashboard data updates.
    Returns real-time system status and metrics.
    """
    try:
        # Get query parameters
        time_range = request.GET.get('range', '1h')  # 1h, 6h, 24h, 7d
        include_details = request.GET.get('details', 'false').lower() == 'true'
        
        # Parse time range
        time_ranges = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30)
        }
        
        time_delta = time_ranges.get(time_range, timedelta(hours=1))
        start_time = timezone.now() - time_delta
        
        # Get system status
        system_status = health_check_service.run_all_health_checks()
        
        # Get performance metrics
        performance_metrics = _get_performance_metrics(start_time, include_details)
        
        # Get error summary
        error_summary = _get_error_summary(start_time)
        
        # Get workflow summary
        workflow_summary = _get_workflow_summary(start_time)
        
        # Get active alerts
        active_alerts = alerting_system.get_active_alerts()
        
        # Get optimization recommendations
        optimization_engine = OptimizationEngine()
        recommendations = optimization_engine.analyze_performance_issues(
            hours=int(time_delta.total_seconds() / 3600)
        )
        
        response_data = {
            'timestamp': timezone.now().isoformat(),
            'time_range': time_range,
            'system_status': {
                'status': system_status.status,
                'uptime_seconds': system_status.uptime_seconds,
                'health_checks': [
                    {
                        'service': check.service,
                        'status': check.status,
                        'response_time_ms': check.response_time_ms,
                        'details': check.details if include_details else None
                    }
                    for check in system_status.health_checks
                ]
            },
            'performance_metrics': performance_metrics,
            'error_summary': error_summary,
            'workflow_summary': workflow_summary,
            'active_alerts': active_alerts,
            'optimization_recommendations': [
                {
                    'category': rec.category,
                    'priority': rec.priority,
                    'title': rec.title,
                    'description': rec.description,
                    'expected_improvement': rec.expected_improvement,
                    'confidence_score': rec.confidence_score
                }
                for rec in recommendations[:5]  # Top 5 recommendations
            ]
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Dashboard data API failed: {e}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
@user_passes_test(is_admin_or_staff)
def metrics_chart_data_api(request):
    """
    API endpoint for metrics chart data.
    Returns time-series data for dashboard charts.
    """
    try:
        # Get query parameters
        metric_name = request.GET.get('metric', 'response_time')
        layer = request.GET.get('layer', 'api')
        component = request.GET.get('component', '')
        time_range = request.GET.get('range', '1h')
        granularity = request.GET.get('granularity', 'minute')  # minute, hour, day
        
        # Parse time range
        time_ranges = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30)
        }
        
        time_delta = time_ranges.get(time_range, timedelta(hours=1))
        start_time = timezone.now() - time_delta
        
        # Build query
        query = PerformanceSnapshot.objects.filter(
            metric_name=metric_name,
            layer=layer,
            timestamp__gte=start_time
        )
        
        if component:
            query = query.filter(component=component)
        
        # Group by time intervals
        if granularity == 'minute':
            time_format = '%Y-%m-%d %H:%M:00'
            interval_minutes = 1
        elif granularity == 'hour':
            time_format = '%Y-%m-%d %H:00:00'
            interval_minutes = 60
        else:  # day
            time_format = '%Y-%m-%d 00:00:00'
            interval_minutes = 1440
        
        # Get aggregated data
        metrics_data = query.extra(
            select={
                'time_bucket': f"DATE_FORMAT(timestamp, '{time_format}')"
            }
        ).values('time_bucket').annotate(
            avg_value=models.Avg('metric_value'),
            max_value=models.Max('metric_value'),
            min_value=models.Min('metric_value'),
            count=models.Count('id')
        ).order_by('time_bucket')
        
        # Format data for charts
        chart_data = {
            'labels': [],
            'datasets': [
                {
                    'label': f'Average {metric_name}',
                    'data': [],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.1
                },
                {
                    'label': f'Maximum {metric_name}',
                    'data': [],
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'tension': 0.1
                }
            ]
        }
        
        for data_point in metrics_data:
            chart_data['labels'].append(data_point['time_bucket'])
            chart_data['datasets'][0]['data'].append(round(data_point['avg_value'], 2))
            chart_data['datasets'][1]['data'].append(round(data_point['max_value'], 2))
        
        response_data = {
            'chart_data': chart_data,
            'metric_info': {
                'metric_name': metric_name,
                'layer': layer,
                'component': component,
                'time_range': time_range,
                'granularity': granularity,
                'data_points': len(chart_data['labels'])
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Metrics chart data API failed: {e}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
@user_passes_test(is_admin_or_staff)
def error_logs_api(request):
    """
    API endpoint for error logs with pagination and filtering.
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        layer = request.GET.get('layer', '')
        component = request.GET.get('component', '')
        severity = request.GET.get('severity', '')
        time_range = request.GET.get('range', '24h')
        
        # Parse time range
        time_ranges = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30)
        }
        
        time_delta = time_ranges.get(time_range, timedelta(hours=24))
        start_time = timezone.now() - time_delta
        
        # Build query
        query = ErrorLog.objects.filter(timestamp__gte=start_time)
        
        if layer:
            query = query.filter(layer=layer)
        if component:
            query = query.filter(component=component)
        if severity:
            query = query.filter(severity=severity)
        
        # Order by timestamp (newest first)
        query = query.order_by('-timestamp')
        
        # Paginate
        paginator = Paginator(query, page_size)
        page_obj = paginator.get_page(page)
        
        # Format error logs
        error_logs = []
        for error in page_obj:
            error_logs.append({
                'id': error.id,
                'timestamp': error.timestamp.isoformat(),
                'layer': error.layer,
                'component': error.component,
                'severity': error.severity,
                'error_type': error.error_type,
                'error_message': error.error_message,
                'correlation_id': error.correlation_id,
                'metadata': error.metadata
            })
        
        response_data = {
            'error_logs': error_logs,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'page_size': page_size,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'filters': {
                'layer': layer,
                'component': component,
                'severity': severity,
                'time_range': time_range
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error logs API failed: {e}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
@user_passes_test(is_admin_or_staff)
def log_files_api(request):
    """
    API endpoint for log file information and management.
    """
    try:
        # Get log files information
        log_files_info = production_logger.get_log_files_info()
        
        # Get query parameter for cleanup
        cleanup_days = request.GET.get('cleanup_days')
        cleaned_files = []
        
        if cleanup_days:
            try:
                days = int(cleanup_days)
                cleaned_files = production_logger.cleanup_old_logs(days)
            except ValueError:
                return JsonResponse({
                    'error': 'Invalid cleanup_days parameter',
                    'timestamp': timezone.now().isoformat()
                }, status=400)
        
        response_data = {
            'log_files': log_files_info,
            'total_files': len(log_files_info),
            'total_size_mb': sum(info['size_mb'] for info in log_files_info.values()),
            'cleaned_files': cleaned_files,
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Log files API failed: {e}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@user_passes_test(is_admin_or_staff)
def alert_action_api(request):
    """
    API endpoint for alert actions (resolve, acknowledge, etc.).
    """
    try:
        data = json.loads(request.body)
        action = data.get('action')
        alert_id = data.get('alert_id')
        
        if not action or not alert_id:
            return JsonResponse({
                'error': 'action and alert_id are required',
                'timestamp': timezone.now().isoformat()
            }, status=400)
        
        if action == 'resolve':
            success = alerting_system.resolve_alert(alert_id)
            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'Alert {alert_id} resolved successfully',
                    'timestamp': timezone.now().isoformat()
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Alert {alert_id} not found or already resolved',
                    'timestamp': timezone.now().isoformat()
                }, status=404)
        
        else:
            return JsonResponse({
                'error': f'Unknown action: {action}',
                'timestamp': timezone.now().isoformat()
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body',
            'timestamp': timezone.now().isoformat()
        }, status=400)
    except Exception as e:
        logger.error(f"Alert action API failed: {e}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


def _get_performance_metrics(start_time: datetime, include_details: bool = False) -> Dict[str, Any]:
    """Get performance metrics summary"""
    
    # Get metrics by layer
    metrics_by_layer = PerformanceSnapshot.objects.filter(
        timestamp__gte=start_time
    ).values('layer', 'metric_name').annotate(
        avg_value=models.Avg('metric_value'),
        max_value=models.Max('metric_value'),
        min_value=models.Min('metric_value'),
        count=models.Count('id')
    ).order_by('layer', 'metric_name')
    
    # Organize by layer
    performance_data = {}
    for metric in metrics_by_layer:
        layer = metric['layer']
        metric_name = metric['metric_name']
        
        if layer not in performance_data:
            performance_data[layer] = {}
        
        performance_data[layer][metric_name] = {
            'average': round(metric['avg_value'], 2),
            'maximum': round(metric['max_value'], 2),
            'minimum': round(metric['min_value'], 2),
            'sample_count': metric['count']
        }
    
    # Get top slow components if details requested
    if include_details:
        slow_components = PerformanceSnapshot.objects.filter(
            timestamp__gte=start_time,
            metric_name__in=['response_time', 'query_time']
        ).values('layer', 'component').annotate(
            avg_time=models.Avg('metric_value')
        ).order_by('-avg_time')[:10]
        
        performance_data['slow_components'] = [
            {
                'layer': comp['layer'],
                'component': comp['component'],
                'average_time_ms': round(comp['avg_time'], 2)
            }
            for comp in slow_components
        ]
    
    return performance_data


def _get_error_summary(start_time: datetime) -> Dict[str, Any]:
    """Get error summary"""
    
    # Get errors by layer and severity
    errors_by_layer = ErrorLog.objects.filter(
        timestamp__gte=start_time
    ).values('layer', 'severity').annotate(
        count=models.Count('id')
    ).order_by('layer', 'severity')
    
    # Get errors by component
    errors_by_component = ErrorLog.objects.filter(
        timestamp__gte=start_time
    ).values('layer', 'component').annotate(
        count=models.Count('id')
    ).order_by('-count')[:10]
    
    # Get recent error types
    recent_error_types = ErrorLog.objects.filter(
        timestamp__gte=start_time
    ).values('error_type').annotate(
        count=models.Count('id')
    ).order_by('-count')[:10]
    
    # Organize data
    error_data = {
        'by_layer_severity': {},
        'by_component': [
            {
                'layer': error['layer'],
                'component': error['component'],
                'count': error['count']
            }
            for error in errors_by_component
        ],
        'by_error_type': [
            {
                'error_type': error['error_type'],
                'count': error['count']
            }
            for error in recent_error_types
        ],
        'total_errors': ErrorLog.objects.filter(timestamp__gte=start_time).count()
    }
    
    for error in errors_by_layer:
        layer = error['layer']
        severity = error['severity']
        
        if layer not in error_data['by_layer_severity']:
            error_data['by_layer_severity'][layer] = {}
        
        error_data['by_layer_severity'][layer][severity] = error['count']
    
    return error_data


def _get_workflow_summary(start_time: datetime) -> Dict[str, Any]:
    """Get workflow summary"""
    
    # Get workflows by type and status
    workflows_by_type = WorkflowSession.objects.filter(
        start_time__gte=start_time
    ).values('workflow_type', 'status').annotate(
        count=models.Count('id')
    ).order_by('workflow_type', 'status')
    
    # Get average workflow duration
    completed_workflows = WorkflowSession.objects.filter(
        start_time__gte=start_time,
        status='completed',
        end_time__isnull=False
    )
    
    workflow_durations = []
    for workflow in completed_workflows:
        duration = (workflow.end_time - workflow.start_time).total_seconds() * 1000
        workflow_durations.append(duration)
    
    # Organize data
    workflow_data = {
        'by_type_status': {},
        'total_workflows': WorkflowSession.objects.filter(start_time__gte=start_time).count(),
        'active_workflows': WorkflowSession.objects.filter(status='in_progress').count(),
        'average_duration_ms': round(sum(workflow_durations) / len(workflow_durations), 2) if workflow_durations else 0,
        'completed_workflows': len(workflow_durations)
    }
    
    for workflow in workflows_by_type:
        workflow_type = workflow['workflow_type']
        status = workflow['status']
        
        if workflow_type not in workflow_data['by_type_status']:
            workflow_data['by_type_status'][workflow_type] = {}
        
        workflow_data['by_type_status'][workflow_type][status] = workflow['count']
    
    return workflow_data