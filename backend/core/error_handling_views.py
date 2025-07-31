"""
Views for database error handling monitoring and management
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import render

from .database_error_handler import get_error_handler
from .connection_pool import get_pool_manager


@staff_member_required
def error_handling_dashboard(request):
    """
    Main dashboard for database error handling monitoring
    """
    error_handler = get_error_handler()
    
    # Get statistics for all databases
    all_stats = {}
    for db_alias in settings.DATABASES.keys():
        all_stats[db_alias] = error_handler.get_error_statistics(db_alias)
    
    # Get connection pool status
    try:
        pool_manager = get_pool_manager()
        pool_status = pool_manager.get_pool_status()
    except Exception:
        pool_status = {}
    
    # Get recent errors (last 24 hours)
    recent_errors = [
        error.to_dict() for error in error_handler.error_history
        if error.timestamp > datetime.now() - timedelta(hours=24)
    ]
    
    context = {
        'database_stats': all_stats,
        'pool_status': pool_status,
        'recent_errors': recent_errors[:50],  # Limit to 50 most recent
        'degradation_mode': error_handler.degradation_mode,
        'degradation_start_time': error_handler.degradation_start_time,
    }
    
    return render(request, 'admin/database_error_dashboard.html', context)


@staff_member_required
@require_http_methods(["GET"])
def error_statistics_api(request):
    """
    API endpoint for error statistics
    """
    database_alias = request.GET.get('database', None)
    error_handler = get_error_handler()
    
    if database_alias:
        stats = error_handler.get_error_statistics(database_alias)
    else:
        # Get stats for all databases
        stats = {}
        for db_alias in settings.DATABASES.keys():
            stats[db_alias] = error_handler.get_error_statistics(db_alias)
    
    return JsonResponse({
        'success': True,
        'data': stats,
        'timestamp': datetime.now().isoformat()
    })


@staff_member_required
@require_http_methods(["GET"])
def recent_errors_api(request):
    """
    API endpoint for recent errors
    """
    database_alias = request.GET.get('database', None)
    limit = int(request.GET.get('limit', 100))
    hours = int(request.GET.get('hours', 24))
    
    error_handler = get_error_handler()
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    # Filter errors
    filtered_errors = []
    for error in error_handler.error_history:
        if error.timestamp < cutoff_time:
            continue
        
        if database_alias and error.database_alias != database_alias:
            continue
        
        filtered_errors.append(error.to_dict())
        
        if len(filtered_errors) >= limit:
            break
    
    return JsonResponse({
        'success': True,
        'data': filtered_errors,
        'total_count': len(filtered_errors),
        'timestamp': datetime.now().isoformat()
    })


@staff_member_required
@require_http_methods(["GET"])
def connection_pool_status_api(request):
    """
    API endpoint for connection pool status
    """
    try:
        pool_manager = get_pool_manager()
        pool_status = pool_manager.get_pool_status()
        pool_metrics = pool_manager.get_pool_metrics()
        
        # Convert metrics to serializable format
        serializable_metrics = {}
        for pool_name, metrics in pool_metrics.items():
            if metrics:
                serializable_metrics[pool_name] = {
                    'pool_name': metrics.pool_name,
                    'pool_size': metrics.pool_size,
                    'active_connections': metrics.active_connections,
                    'total_requests': metrics.total_requests,
                    'failed_requests': metrics.failed_requests,
                    'average_response_time': metrics.average_response_time,
                    'peak_connections': metrics.peak_connections,
                    'last_updated': metrics.last_updated.isoformat()
                }
        
        return JsonResponse({
            'success': True,
            'data': {
                'pool_status': pool_status,
                'pool_metrics': serializable_metrics
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def reset_degradation_mode_api(request):
    """
    API endpoint to reset degradation mode
    """
    try:
        data = json.loads(request.body)
        database_alias = data.get('database', None)
        
        error_handler = get_error_handler()
        error_handler.reset_degradation_mode(database_alias)
        
        return JsonResponse({
            'success': True,
            'message': f'Degradation mode reset for {database_alias or "all databases"}',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)


@staff_member_required
@require_http_methods(["GET"])
def deadlock_analysis_api(request):
    """
    API endpoint for deadlock analysis
    """
    error_handler = get_error_handler()
    deadlock_stats = error_handler.deadlock_detector.get_deadlock_statistics()
    
    # Get recent deadlock history
    recent_deadlocks = [
        dl for dl in error_handler.deadlock_detector.deadlock_history
        if datetime.fromisoformat(dl['timestamp']) > datetime.now() - timedelta(hours=24)
    ]
    
    return JsonResponse({
        'success': True,
        'data': {
            'statistics': deadlock_stats,
            'recent_deadlocks': recent_deadlocks
        },
        'timestamp': datetime.now().isoformat()
    })


@staff_member_required
@require_http_methods(["GET"])
def circuit_breaker_status_api(request):
    """
    API endpoint for circuit breaker status
    """
    error_handler = get_error_handler()
    
    circuit_status = {}
    for db_alias, circuit_breaker in error_handler.circuit_breakers.items():
        circuit_status[db_alias] = {
            'state': circuit_breaker.state.value,
            'failure_count': circuit_breaker.failure_count,
            'last_failure_time': circuit_breaker.last_failure_time,
            'config': {
                'failure_threshold': circuit_breaker.config.failure_threshold,
                'recovery_timeout': circuit_breaker.config.recovery_timeout,
                'name': circuit_breaker.config.name
            }
        }
    
    return JsonResponse({
        'success': True,
        'data': circuit_status,
        'timestamp': datetime.now().isoformat()
    })


@staff_member_required
@require_http_methods(["GET"])
def health_check_api(request):
    """
    API endpoint for overall database health check
    """
    error_handler = get_error_handler()
    health_data = {}
    
    for db_alias in settings.DATABASES.keys():
        # Check if database is degraded
        is_degraded = error_handler.is_degraded(db_alias)
        
        # Get recent error count
        recent_errors = [
            error for error in error_handler.error_history
            if (error.database_alias == db_alias and
                error.timestamp > datetime.now() - timedelta(minutes=5))
        ]
        
        # Get cached health check status
        health_check_failed = cache.get(f"db_health_check_failed_{db_alias}", False)
        health_check_success = cache.get(f"db_health_check_success_{db_alias}", False)
        
        # Determine overall health status
        if is_degraded or health_check_failed:
            status = 'critical'
        elif len(recent_errors) > 5:
            status = 'warning'
        elif health_check_success:
            status = 'healthy'
        else:
            status = 'unknown'
        
        health_data[db_alias] = {
            'status': status,
            'is_degraded': is_degraded,
            'recent_error_count': len(recent_errors),
            'health_check_failed': health_check_failed,
            'health_check_success': health_check_success
        }
    
    # Overall system health
    all_statuses = [data['status'] for data in health_data.values()]
    if 'critical' in all_statuses:
        overall_status = 'critical'
    elif 'warning' in all_statuses:
        overall_status = 'warning'
    elif all(status == 'healthy' for status in all_statuses):
        overall_status = 'healthy'
    else:
        overall_status = 'unknown'
    
    return JsonResponse({
        'success': True,
        'data': {
            'overall_status': overall_status,
            'databases': health_data
        },
        'timestamp': datetime.now().isoformat()
    })


@staff_member_required
@require_http_methods(["GET"])
def error_trends_api(request):
    """
    API endpoint for error trends analysis
    """
    hours = int(request.GET.get('hours', 24))
    database_alias = request.GET.get('database', None)
    
    error_handler = get_error_handler()
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    # Filter errors
    filtered_errors = []
    for error in error_handler.error_history:
        if error.timestamp < cutoff_time:
            continue
        
        if database_alias and error.database_alias != database_alias:
            continue
        
        filtered_errors.append(error)
    
    # Group errors by hour
    hourly_counts = {}
    error_type_counts = {}
    severity_counts = {}
    
    for error in filtered_errors:
        # Hour grouping
        hour_key = error.timestamp.strftime('%Y-%m-%d %H:00')
        hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
        
        # Error type grouping
        error_type_counts[error.error_type] = error_type_counts.get(error.error_type, 0) + 1
        
        # Severity grouping
        severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
    
    return JsonResponse({
        'success': True,
        'data': {
            'hourly_counts': hourly_counts,
            'error_type_counts': error_type_counts,
            'severity_counts': severity_counts,
            'total_errors': len(filtered_errors)
        },
        'timestamp': datetime.now().isoformat()
    })


@require_http_methods(["GET"])
def error_handling_metrics(request):
    """
    Prometheus-style metrics endpoint for monitoring systems
    """
    error_handler = get_error_handler()
    
    metrics = []
    
    # Error counts by database and type
    for db_alias in settings.DATABASES.keys():
        stats = error_handler.get_error_statistics(db_alias)
        
        # Total errors
        metrics.append(f'database_errors_total{{database="{db_alias}"}} {stats["total_errors"]}')
        
        # Recent errors
        metrics.append(f'database_errors_recent_24h{{database="{db_alias}"}} {stats["recent_errors_24h"]}')
        
        # Degradation mode
        degradation_value = 1 if stats["degradation_mode"] else 0
        metrics.append(f'database_degradation_mode{{database="{db_alias}"}} {degradation_value}')
        
        # Error types
        for error_type, count in stats["error_types"].items():
            metrics.append(f'database_errors_by_type{{database="{db_alias}",type="{error_type}"}} {count}')
        
        # Severity counts
        for severity, count in stats["severity_counts"].items():
            metrics.append(f'database_errors_by_severity{{database="{db_alias}",severity="{severity}"}} {count}')
    
    # Deadlock metrics
    deadlock_stats = error_handler.deadlock_detector.get_deadlock_statistics()
    metrics.append(f'database_deadlocks_total {deadlock_stats["total_deadlocks"]}')
    metrics.append(f'database_deadlocks_recent_24h {deadlock_stats["recent_deadlocks_24h"]}')
    
    # Circuit breaker states
    for db_alias, circuit_breaker in error_handler.circuit_breakers.items():
        state_value = {'closed': 0, 'open': 1, 'half_open': 2}.get(circuit_breaker.state.value, -1)
        metrics.append(f'database_circuit_breaker_state{{database="{db_alias}"}} {state_value}')
        metrics.append(f'database_circuit_breaker_failures{{database="{db_alias}"}} {circuit_breaker.failure_count}')
    
    response = HttpResponse('\n'.join(metrics), content_type='text/plain')
    return response