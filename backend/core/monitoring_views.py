"""
Database Monitoring API Views

This module provides REST API endpoints for accessing database monitoring data:
- Current metrics and health status
- Historical metrics and trends
- Slow query analysis
- Alert management
- System health dashboard
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.conf import settings

from .database_monitor import get_database_monitor
from .database_alerting import get_database_alerting

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(30)  # Cache for 30 seconds
def get_current_metrics(request):
    """
    Get current database metrics for all databases or a specific database
    
    Query Parameters:
    - database: Optional database alias to filter results
    """
    try:
        monitor = get_database_monitor()
        database = request.GET.get('database')
        
        metrics = monitor.get_current_metrics(database)
        
        return Response({
            'status': 'success',
            'data': metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_metrics_history(request, database):
    """
    Get historical metrics for a specific database
    
    Path Parameters:
    - database: Database alias
    
    Query Parameters:
    - hours: Number of hours of history to retrieve (default: 24)
    """
    try:
        monitor = get_database_monitor()
        hours = int(request.GET.get('hours', 24))
        
        history = monitor.get_metrics_history(database, hours)
        
        return Response({
            'status': 'success',
            'data': {
                'database': database,
                'hours': hours,
                'metrics': history
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError:
        return Response({
            'status': 'error',
            'message': 'Invalid hours parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_health_summary(request):
    """
    Get overall health summary of all databases
    """
    try:
        monitor = get_database_monitor()
        summary = monitor.get_health_summary()
        
        return Response({
            'status': 'success',
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting health summary: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_slow_queries(request):
    """
    Get slow query analysis
    
    Query Parameters:
    - database: Optional database alias to filter results
    - limit: Maximum number of queries to return (default: 50)
    - severity: Filter by severity (low, medium, high, critical)
    """
    try:
        monitor = get_database_monitor()
        database = request.GET.get('database')
        limit = int(request.GET.get('limit', 50))
        severity = request.GET.get('severity')
        
        slow_queries = monitor.get_slow_queries(database, limit)
        
        # Filter by severity if specified
        if severity:
            slow_queries = [q for q in slow_queries if q.get('severity') == severity]
        
        return Response({
            'status': 'success',
            'data': {
                'slow_queries': slow_queries,
                'total_count': len(slow_queries),
                'filters': {
                    'database': database,
                    'severity': severity,
                    'limit': limit
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError:
        return Response({
            'status': 'error',
            'message': 'Invalid limit parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_alerts(request):
    """
    Get active database alerts
    
    Query Parameters:
    - database: Optional database alias to filter results
    - severity: Filter by severity (warning, critical)
    """
    try:
        monitor = get_database_monitor()
        database = request.GET.get('database')
        severity = request.GET.get('severity')
        
        alerts = monitor.get_active_alerts(database)
        
        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a.get('severity') == severity]
        
        return Response({
            'status': 'success',
            'data': {
                'active_alerts': alerts,
                'total_count': len(alerts),
                'filters': {
                    'database': database,
                    'severity': severity
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_alert_history(request):
    """
    Get alert history
    
    Query Parameters:
    - hours: Number of hours of history to retrieve (default: 24)
    - severity: Filter by severity (warning, critical)
    """
    try:
        monitor = get_database_monitor()
        hours = int(request.GET.get('hours', 24))
        severity = request.GET.get('severity')
        
        history = monitor.get_alert_history(hours)
        
        # Filter by severity if specified
        if severity:
            history = [a for a in history if a.get('severity') == severity]
        
        return Response({
            'status': 'success',
            'data': {
                'alert_history': history,
                'total_count': len(history),
                'hours': hours,
                'filters': {
                    'severity': severity
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError:
        return Response({
            'status': 'error',
            'message': 'Invalid hours parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def acknowledge_alert(request):
    """
    Acknowledge an alert
    
    Request Body:
    - alert_id: Alert ID to acknowledge
    - acknowledged_by: Optional user who acknowledged the alert
    """
    try:
        alert_id = request.data.get('alert_id')
        acknowledged_by = request.data.get('acknowledged_by', request.user.username)
        
        if not alert_id:
            return Response({
                'status': 'error',
                'message': 'alert_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        alerting = get_database_alerting()
        alerting.acknowledge_alert(alert_id, acknowledged_by)
        
        return Response({
            'status': 'success',
            'message': f'Alert {alert_id} acknowledged by {acknowledged_by}',
            'data': {
                'alert_id': alert_id,
                'acknowledged_by': acknowledged_by,
                'acknowledged_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def suppress_alert(request):
    """
    Suppress alerts for a specific metric
    
    Request Body:
    - database: Database alias
    - metric_name: Metric name to suppress
    - duration_minutes: Duration in minutes (default: 60)
    """
    try:
        database = request.data.get('database')
        metric_name = request.data.get('metric_name')
        duration_minutes = int(request.data.get('duration_minutes', 60))
        
        if not database or not metric_name:
            return Response({
                'status': 'error',
                'message': 'database and metric_name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        alerting = get_database_alerting()
        alerting.suppress_alert(database, metric_name, duration_minutes)
        
        return Response({
            'status': 'success',
            'message': f'Alerts suppressed for {database}.{metric_name} for {duration_minutes} minutes',
            'data': {
                'database': database,
                'metric_name': metric_name,
                'duration_minutes': duration_minutes,
                'suppressed_until': (datetime.now() + timedelta(minutes=duration_minutes)).isoformat()
            }
        })
        
    except ValueError:
        return Response({
            'status': 'error',
            'message': 'Invalid duration_minutes parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error suppressing alert: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_monitoring_config(request):
    """
    Get current monitoring configuration
    """
    try:
        monitor = get_database_monitor()
        alerting = get_database_alerting()
        
        config = {
            'monitoring': {
                'enabled': monitor.monitoring_enabled,
                'interval_seconds': monitor.monitoring_interval,
                'recovery_enabled': monitor.recovery_enabled,
                'alerting_enabled': monitor.alerting_enabled
            },
            'thresholds': {
                name: {
                    'warning_threshold': threshold.warning_threshold,
                    'critical_threshold': threshold.critical_threshold,
                    'enabled': threshold.enabled,
                    'duration_seconds': threshold.duration_seconds
                }
                for name, threshold in monitor.alert_thresholds.items()
            },
            'alert_channels': [
                {
                    'name': channel.name,
                    'type': channel.type,
                    'enabled': channel.enabled,
                    'severity_filter': channel.severity_filter
                }
                for channel in alerting.channels
            ],
            'suppressed_alerts': alerting.get_suppressed_alerts(),
            'acknowledged_alerts': alerting.get_acknowledged_alerts()
        }
        
        return Response({
            'status': 'success',
            'data': config
        })
        
    except Exception as e:
        logger.error(f"Error getting monitoring config: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def update_threshold(request):
    """
    Update alert threshold configuration
    
    Request Body:
    - metric_name: Metric name to update
    - warning_threshold: Optional warning threshold value
    - critical_threshold: Optional critical threshold value
    - enabled: Optional boolean to enable/disable threshold
    """
    try:
        metric_name = request.data.get('metric_name')
        warning_threshold = request.data.get('warning_threshold')
        critical_threshold = request.data.get('critical_threshold')
        enabled = request.data.get('enabled')
        
        if not metric_name:
            return Response({
                'status': 'error',
                'message': 'metric_name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        monitor = get_database_monitor()
        
        # Convert string values to appropriate types
        if warning_threshold is not None:
            warning_threshold = float(warning_threshold)
        if critical_threshold is not None:
            critical_threshold = float(critical_threshold)
        if enabled is not None:
            enabled = bool(enabled)
        
        monitor.update_threshold(metric_name, warning_threshold, critical_threshold, enabled)
        
        # Get updated threshold
        updated_threshold = monitor.alert_thresholds.get(metric_name)
        if updated_threshold:
            threshold_data = {
                'metric_name': metric_name,
                'warning_threshold': updated_threshold.warning_threshold,
                'critical_threshold': updated_threshold.critical_threshold,
                'enabled': updated_threshold.enabled,
                'duration_seconds': updated_threshold.duration_seconds
            }
        else:
            threshold_data = None
        
        return Response({
            'status': 'success',
            'message': f'Threshold updated for {metric_name}',
            'data': threshold_data
        })
        
    except ValueError as e:
        return Response({
            'status': 'error',
            'message': f'Invalid parameter value: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error updating threshold: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def test_alert_channels(request):
    """
    Test all configured alert channels
    """
    try:
        alerting = get_database_alerting()
        results = alerting.test_channels()
        
        return Response({
            'status': 'success',
            'message': 'Alert channel tests completed',
            'data': {
                'test_results': results,
                'total_channels': len(results),
                'successful_channels': sum(1 for success in results.values() if success),
                'failed_channels': sum(1 for success in results.values() if not success)
            }
        })
        
    except Exception as e:
        logger.error(f"Error testing alert channels: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request):
    """
    Get comprehensive dashboard data for monitoring UI
    """
    try:
        monitor = get_database_monitor()
        
        # Get current metrics for all databases
        current_metrics = monitor.get_current_metrics()
        
        # Get health summary
        health_summary = monitor.get_health_summary()
        
        # Get recent alerts
        recent_alerts = monitor.get_active_alerts()
        
        # Get top slow queries
        slow_queries = monitor.get_slow_queries(limit=10)
        
        # Calculate summary statistics
        total_connections = sum(
            metrics.get('active_connections', 0) 
            for metrics in current_metrics.values() 
            if metrics
        )
        
        avg_query_time = sum(
            metrics.get('average_query_time', 0) 
            for metrics in current_metrics.values() 
            if metrics
        ) / len(current_metrics) if current_metrics else 0
        
        total_slow_queries = sum(
            metrics.get('slow_queries', 0) 
            for metrics in current_metrics.values() 
            if metrics
        )
        
        dashboard_data = {
            'summary': {
                'overall_status': health_summary.get('overall_status', 'unknown'),
                'total_databases': len(current_metrics),
                'total_connections': total_connections,
                'average_query_time': round(avg_query_time, 3),
                'total_slow_queries': total_slow_queries,
                'active_alerts': len(recent_alerts)
            },
            'databases': current_metrics,
            'health_summary': health_summary,
            'recent_alerts': recent_alerts[:5],  # Top 5 recent alerts
            'top_slow_queries': slow_queries[:5],  # Top 5 slow queries
            'timestamp': datetime.now().isoformat()
        }
        
        return Response({
            'status': 'success',
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def control_monitoring(request):
    """
    Control monitoring system (start/stop/restart)
    
    Request Body:
    - action: 'start', 'stop', 'restart', 'enable_alerting', 'disable_alerting', 'enable_recovery', 'disable_recovery'
    """
    try:
        action = request.data.get('action')
        
        if not action:
            return Response({
                'status': 'error',
                'message': 'action is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        monitor = get_database_monitor()
        
        if action == 'start':
            monitor.enable_monitoring()
            message = 'Monitoring started'
        elif action == 'stop':
            monitor.disable_monitoring()
            message = 'Monitoring stopped'
        elif action == 'restart':
            monitor.stop_monitoring()
            monitor.start_monitoring()
            message = 'Monitoring restarted'
        elif action == 'enable_alerting':
            monitor.enable_alerting()
            message = 'Alerting enabled'
        elif action == 'disable_alerting':
            monitor.disable_alerting()
            message = 'Alerting disabled'
        elif action == 'enable_recovery':
            monitor.enable_recovery()
            message = 'Automatic recovery enabled'
        elif action == 'disable_recovery':
            monitor.disable_recovery()
            message = 'Automatic recovery disabled'
        else:
            return Response({
                'status': 'error',
                'message': f'Invalid action: {action}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'message': message,
            'data': {
                'action': action,
                'monitoring_enabled': monitor.monitoring_enabled,
                'alerting_enabled': monitor.alerting_enabled,
                'recovery_enabled': monitor.recovery_enabled
            }
        })
        
    except Exception as e:
        logger.error(f"Error controlling monitoring: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)