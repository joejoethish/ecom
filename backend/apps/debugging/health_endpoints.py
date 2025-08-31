"""
Health Check Endpoints for Production Monitoring

This module provides HTTP endpoints for system health monitoring,
designed to be used by load balancers, monitoring systems, and operations teams.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging

from .production_monitoring import health_check_service, alerting_system
from .models import PerformanceSnapshot, ErrorLog, WorkflowSession

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@never_cache
def health_check_basic(request):
    """
    Basic health check endpoint for load balancers.
    Returns 200 OK if system is operational, 503 if not.
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Quick cache check
        cache.set('health_check', 'ok', 10)
        cache_result = cache.get('health_check')
        
        if cache_result == 'ok':
            return HttpResponse("OK", status=200, content_type="text/plain")
        else:
            return HttpResponse("Cache Error", status=503, content_type="text/plain")
            
    except Exception as e:
        logger.error(f"Basic health check failed: {e}")
        return HttpResponse("Service Unavailable", status=503, content_type="text/plain")


@require_http_methods(["GET"])
@never_cache
def health_check_detailed(request):
    """
    Detailed health check endpoint with comprehensive system status.
    Returns detailed JSON response with all system components.
    """
    try:
        # Run comprehensive health checks
        system_status = health_check_service.run_all_health_checks()
        
        # Convert to JSON-serializable format
        response_data = {
            'status': system_status.status,
            'timestamp': system_status.timestamp.isoformat(),
            'uptime_seconds': system_status.uptime_seconds,
            'health_checks': [
                {
                    'service': check.service,
                    'status': check.status,
                    'response_time_ms': check.response_time_ms,
                    'details': check.details,
                    'timestamp': check.timestamp.isoformat(),
                    'error_message': check.error_message
                }
                for check in system_status.health_checks
            ],
            'active_alerts': [
                {
                    'alert_id': alert.alert_id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'component': alert.component,
                    'layer': alert.layer,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in system_status.active_alerts
            ],
            'performance_summary': system_status.performance_summary
        }
        
        # Set HTTP status based on system status
        if system_status.status == 'healthy':
            http_status = 200
        elif system_status.status == 'degraded':
            http_status = 200  # Still operational but with warnings
        else:
            http_status = 503  # Service unavailable
        
        return JsonResponse(response_data, status=http_status)
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
@never_cache
def health_check_readiness(request):
    """
    Readiness probe endpoint for Kubernetes/container orchestration.
    Checks if the application is ready to serve traffic.
    """
    try:
        # Check critical dependencies
        checks = {
            'database': False,
            'cache': False,
            'migrations': False
        }
        
        # Database readiness
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                migration_count = cursor.fetchone()[0]
                checks['database'] = True
                checks['migrations'] = migration_count > 0
        except Exception as e:
            logger.error(f"Database readiness check failed: {e}")
        
        # Cache readiness
        try:
            cache.set('readiness_check', 'ready', 10)
            cache_result = cache.get('readiness_check')
            checks['cache'] = cache_result == 'ready'
        except Exception as e:
            logger.error(f"Cache readiness check failed: {e}")
        
        # Determine readiness
        is_ready = all(checks.values())
        
        response_data = {
            'ready': is_ready,
            'timestamp': timezone.now().isoformat(),
            'checks': checks
        }
        
        return JsonResponse(response_data, status=200 if is_ready else 503)
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({
            'ready': False,
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
@never_cache
def health_check_liveness(request):
    """
    Liveness probe endpoint for Kubernetes/container orchestration.
    Checks if the application process is alive and responsive.
    """
    try:
        # Simple liveness check - if we can respond, we're alive
        start_time = time.time()
        
        # Minimal processing to ensure the application is responsive
        current_time = timezone.now()
        response_time_ms = (time.time() - start_time) * 1000
        
        response_data = {
            'alive': True,
            'timestamp': current_time.isoformat(),
            'response_time_ms': round(response_time_ms, 2),
            'process_id': os.getpid() if hasattr(os, 'getpid') else None
        }
        
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JsonResponse({
            'alive': False,
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
@never_cache
def metrics_endpoint(request):
    """
    Metrics endpoint for monitoring systems (Prometheus-compatible format).
    Returns key system metrics in a format suitable for scraping.
    """
    try:
        # Get recent metrics (last 5 minutes)
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        
        # Database metrics
        db_metrics = PerformanceSnapshot.objects.filter(
            layer='database',
            timestamp__gte=five_minutes_ago
        ).values('metric_name').annotate(
            avg_value=models.Avg('metric_value'),
            max_value=models.Max('metric_value')
        )
        
        # API metrics
        api_metrics = PerformanceSnapshot.objects.filter(
            layer='api',
            timestamp__gte=five_minutes_ago
        ).values('metric_name').annotate(
            avg_value=models.Avg('metric_value'),
            max_value=models.Max('metric_value')
        )
        
        # System metrics
        system_metrics = PerformanceSnapshot.objects.filter(
            layer='system',
            timestamp__gte=five_minutes_ago
        ).values('metric_name').annotate(
            avg_value=models.Avg('metric_value'),
            max_value=models.Max('metric_value')
        )
        
        # Error metrics
        error_count = ErrorLog.objects.filter(
            timestamp__gte=five_minutes_ago
        ).count()
        
        # Active workflows
        active_workflows = WorkflowSession.objects.filter(
            status='in_progress'
        ).count()
        
        # Build Prometheus-style metrics
        metrics_lines = []
        
        # Add help and type information
        metrics_lines.extend([
            "# HELP ecommerce_database_query_time_ms Database query execution time in milliseconds",
            "# TYPE ecommerce_database_query_time_ms gauge",
            "# HELP ecommerce_api_response_time_ms API response time in milliseconds", 
            "# TYPE ecommerce_api_response_time_ms gauge",
            "# HELP ecommerce_system_cpu_usage_percent System CPU usage percentage",
            "# TYPE ecommerce_system_cpu_usage_percent gauge",
            "# HELP ecommerce_error_count_total Total number of errors",
            "# TYPE ecommerce_error_count_total counter",
            "# HELP ecommerce_active_workflows_total Number of active workflows",
            "# TYPE ecommerce_active_workflows_total gauge",
        ])
        
        # Database metrics
        for metric in db_metrics:
            metric_name = metric['metric_name'].replace(' ', '_').lower()
            avg_value = metric['avg_value'] or 0
            max_value = metric['max_value'] or 0
            
            metrics_lines.extend([
                f'ecommerce_database_{metric_name}_avg {avg_value}',
                f'ecommerce_database_{metric_name}_max {max_value}'
            ])
        
        # API metrics
        for metric in api_metrics:
            metric_name = metric['metric_name'].replace(' ', '_').lower()
            avg_value = metric['avg_value'] or 0
            max_value = metric['max_value'] or 0
            
            metrics_lines.extend([
                f'ecommerce_api_{metric_name}_avg {avg_value}',
                f'ecommerce_api_{metric_name}_max {max_value}'
            ])
        
        # System metrics
        for metric in system_metrics:
            metric_name = metric['metric_name'].replace(' ', '_').lower()
            avg_value = metric['avg_value'] or 0
            max_value = metric['max_value'] or 0
            
            metrics_lines.extend([
                f'ecommerce_system_{metric_name}_avg {avg_value}',
                f'ecommerce_system_{metric_name}_max {max_value}'
            ])
        
        # Error and workflow metrics
        metrics_lines.extend([
            f'ecommerce_error_count_total {error_count}',
            f'ecommerce_active_workflows_total {active_workflows}'
        ])
        
        # Add timestamp
        timestamp = int(timezone.now().timestamp() * 1000)
        metrics_lines = [f"{line} {timestamp}" if not line.startswith('#') else line 
                        for line in metrics_lines]
        
        metrics_text = '\n'.join(metrics_lines)
        
        return HttpResponse(metrics_text, content_type='text/plain; version=0.0.4; charset=utf-8')
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return HttpResponse(f"# Error generating metrics: {e}", 
                          content_type='text/plain', status=500)


@require_http_methods(["GET"])
@never_cache
def alerts_endpoint(request):
    """
    Alerts endpoint for monitoring systems.
    Returns current active alerts and recent alert history.
    """
    try:
        # Get query parameters
        include_history = request.GET.get('history', 'false').lower() == 'true'
        hours = int(request.GET.get('hours', '24'))
        
        # Get active alerts
        active_alerts = alerting_system.get_active_alerts()
        
        response_data = {
            'active_alerts': active_alerts,
            'active_count': len(active_alerts),
            'timestamp': timezone.now().isoformat()
        }
        
        # Include history if requested
        if include_history:
            alert_history = alerting_system.get_alert_history(hours=hours)
            response_data['alert_history'] = alert_history
            response_data['history_count'] = len(alert_history)
            response_data['history_hours'] = hours
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Alerts endpoint failed: {e}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def resolve_alert_endpoint(request):
    """
    Endpoint to manually resolve alerts.
    Accepts POST requests with alert_id to resolve.
    """
    try:
        data = json.loads(request.body)
        alert_id = data.get('alert_id')
        
        if not alert_id:
            return JsonResponse({
                'error': 'alert_id is required',
                'timestamp': timezone.now().isoformat()
            }, status=400)
        
        # Resolve the alert
        resolved = alerting_system.resolve_alert(alert_id)
        
        if resolved:
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
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body',
            'timestamp': timezone.now().isoformat()
        }, status=400)
    except Exception as e:
        logger.error(f"Resolve alert endpoint failed: {e}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
@never_cache
def system_info_endpoint(request):
    """
    System information endpoint for operations teams.
    Returns detailed system configuration and status.
    """
    try:
        import platform
        import sys
        import django
        
        # Get system information
        system_info = {
            'application': {
                'name': 'E-Commerce Platform',
                'version': getattr(settings, 'VERSION', '1.0.0'),
                'environment': 'production' if not settings.DEBUG else 'development',
                'debug_mode': settings.DEBUG,
                'django_version': django.get_version(),
                'python_version': sys.version,
            },
            'system': {
                'platform': platform.platform(),
                'architecture': platform.architecture(),
                'processor': platform.processor(),
                'hostname': platform.node(),
            },
            'database': {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
                'host': settings.DATABASES['default']['HOST'],
                'port': settings.DATABASES['default']['PORT'],
            },
            'cache': {
                'backend': settings.CACHES['default']['BACKEND'],
                'location': settings.CACHES['default'].get('LOCATION', 'N/A'),
            },
            'features': {
                'debugging_enabled': getattr(settings, 'DEBUGGING_SYSTEM_ENABLED', False),
                'performance_monitoring': getattr(settings, 'PERFORMANCE_MONITORING_ENABLED', False),
                'alerting_enabled': getattr(settings, 'ALERTING_ENABLED', False),
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(system_info)
        
    except Exception as e:
        logger.error(f"System info endpoint failed: {e}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


@require_http_methods(["GET"])
@never_cache
def performance_summary_endpoint(request):
    """
    Performance summary endpoint for monitoring dashboards.
    Returns key performance indicators and trends.
    """
    try:
        # Get query parameters
        hours = int(request.GET.get('hours', '1'))
        
        # Calculate time range
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get performance metrics
        metrics = PerformanceSnapshot.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).values('layer', 'metric_name').annotate(
            avg_value=models.Avg('metric_value'),
            max_value=models.Max('metric_value'),
            min_value=models.Min('metric_value'),
            count=models.Count('id')
        ).order_by('layer', 'metric_name')
        
        # Get error summary
        errors = ErrorLog.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).values('layer', 'severity').annotate(
            count=models.Count('id')
        ).order_by('layer', 'severity')
        
        # Get workflow summary
        workflows = WorkflowSession.objects.filter(
            start_time__gte=start_time
        ).values('workflow_type', 'status').annotate(
            count=models.Count('id')
        ).order_by('workflow_type', 'status')
        
        # Organize data
        performance_data = {}
        for metric in metrics:
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
        
        error_data = {}
        for error in errors:
            layer = error['layer']
            severity = error['severity']
            
            if layer not in error_data:
                error_data[layer] = {}
            
            error_data[layer][severity] = error['count']
        
        workflow_data = {}
        for workflow in workflows:
            workflow_type = workflow['workflow_type']
            status = workflow['status']
            
            if workflow_type not in workflow_data:
                workflow_data[workflow_type] = {}
            
            workflow_data[workflow_type][status] = workflow['count']
        
        response_data = {
            'time_range': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'hours': hours
            },
            'performance_metrics': performance_data,
            'error_summary': error_data,
            'workflow_summary': workflow_data,
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Performance summary endpoint failed: {e}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)