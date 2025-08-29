"""
Views for the logging and monitoring system.
"""
import json
import datetime
from django.views.generic import TemplateView, View
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg, Max, Min, Sum, F, Q
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import SystemLog, BusinessMetric, PerformanceMetric, SecurityEvent
from backend.logs.monitoring import system_monitor
from .aggregation import log_aggregation_service, log_frontend_entry, log_backend_entry
import logging

logger = logging.getLogger(__name__)


@method_decorator(staff_member_required, name='dispatch')
class MonitoringDashboardView(TemplateView):
    """
    Main monitoring dashboard view.
    """
    template_name = 'logs/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get time range from request or default to last 24 hours
        time_range = self.request.GET.get('time_range', '24h')
        
        # Calculate start time based on time range
        now = timezone.now()
        if time_range == '1h':
            start_time = now - datetime.timedelta(hours=1)
        elif time_range == '6h':
            start_time = now - datetime.timedelta(hours=6)
        elif time_range == '24h':
            start_time = now - datetime.timedelta(hours=24)
        elif time_range == '7d':
            start_time = now - datetime.timedelta(days=7)
        elif time_range == '30d':
            start_time = now - datetime.timedelta(days=30)
        else:
            start_time = now - datetime.timedelta(hours=24)
        
        # Get system health metrics
        context['system_health'] = self.get_system_health_metrics(start_time)
        
        # Get error metrics
        context['error_metrics'] = self.get_error_metrics(start_time)
        
        # Get performance metrics
        context['performance_metrics'] = self.get_performance_metrics(start_time)
        
        # Get security metrics
        context['security_metrics'] = self.get_security_metrics(start_time)
        
        # Get business metrics
        context['business_metrics'] = self.get_business_metrics(start_time)
        
        # Add time range for the template
        context['time_range'] = time_range
        context['available_time_ranges'] = [
            {'value': '1h', 'label': 'Last Hour'},
            {'value': '6h', 'label': 'Last 6 Hours'},
            {'value': '24h', 'label': 'Last 24 Hours'},
            {'value': '7d', 'label': 'Last 7 Days'},
            {'value': '30d', 'label': 'Last 30 Days'},
        ]
        
        return context
    
    def get_system_health_metrics(self, start_time):
        """
        Get system health metrics.
        """
        # Get the latest system metrics
        system_metrics = PerformanceMetric.objects.filter(
            name='system_metrics',
            timestamp__gte=start_time
        ).order_by('-timestamp')[:100]
        
        # Calculate average CPU and memory usage
        avg_cpu = system_metrics.aggregate(Avg('value'))['value__avg'] or 0
        
        # Get the latest system metric
        latest_metric = system_metrics.first()
        
        return {
            'avg_cpu_usage': round(avg_cpu, 2),
            'current_cpu_usage': round(latest_metric.value if latest_metric else 0, 2),
            'memory_usage': latest_metric.response_time if latest_metric else 0,
            'disk_usage': 0,  # We'll need to add this to the metrics
            'system_metrics': list(system_metrics.values('timestamp', 'value', 'response_time')),
        }
    
    def get_error_metrics(self, start_time):
        """
        Get error metrics.
        """
        # Count errors by level
        error_counts = SystemLog.objects.filter(
            created_at__gte=start_time,
            level__in=['ERROR', 'CRITICAL']
        ).values('level').annotate(count=Count('id')).order_by('level')
        
        # Get recent errors
        recent_errors = SystemLog.objects.filter(
            level__in=['ERROR', 'CRITICAL'],
            created_at__gte=start_time
        ).order_by('-created_at')[:10]
        
        # Count errors by source
        error_by_source = SystemLog.objects.filter(
            created_at__gte=start_time,
            level__in=['ERROR', 'CRITICAL']
        ).values('source').annotate(count=Count('id')).order_by('-count')[:5]
        
        return {
            'error_counts': list(error_counts),
            'recent_errors': list(recent_errors.values('created_at', 'level', 'source', 'message')),
            'error_by_source': list(error_by_source),
            'total_errors': sum(item['count'] for item in error_counts),
        }
    
    def get_performance_metrics(self, start_time):
        """
        Get performance metrics.
        """
        # Get response time metrics
        response_times = PerformanceMetric.objects.filter(
            timestamp__gte=start_time,
            name='request_duration'
        ).order_by('-timestamp')
        
        # Calculate average response time
        avg_response_time = response_times.aggregate(Avg('value'))['value__avg'] or 0
        
        # Get slow requests
        slow_requests = PerformanceMetric.objects.filter(
            timestamp__gte=start_time,
            name='slow_request'
        ).order_by('-timestamp')[:10]
        
        # Get top 5 slowest endpoints
        slowest_endpoints = PerformanceMetric.objects.filter(
            timestamp__gte=start_time,
            endpoint__isnull=False
        ).values('endpoint').annotate(
            avg_time=Avg('value'),
            count=Count('id')
        ).order_by('-avg_time')[:5]
        
        return {
            'avg_response_time': round(avg_response_time, 2),
            'slow_requests': list(slow_requests.values('timestamp', 'endpoint', 'value', 'method')),
            'slowest_endpoints': list(slowest_endpoints),
            'response_time_data': list(response_times.values('timestamp', 'value')[:100]),
        }
    
    def get_security_metrics(self, start_time):
        """
        Get security metrics.
        """
        # Count security events by type
        security_events = SecurityEvent.objects.filter(
            timestamp__gte=start_time
        ).values('event_type').annotate(count=Count('id')).order_by('-count')
        
        # Get recent security events
        recent_events = SecurityEvent.objects.filter(
            timestamp__gte=start_time
        ).order_by('-timestamp')[:10]
        
        # Count security events by IP address
        events_by_ip = SecurityEvent.objects.filter(
            timestamp__gte=start_time
        ).values('ip_address').annotate(count=Count('id')).order_by('-count')[:5]
        
        return {
            'security_events': list(security_events),
            'recent_events': list(recent_events.values('timestamp', 'event_type', 'username', 'ip_address')),
            'events_by_ip': list(events_by_ip),
            'total_events': SecurityEvent.objects.filter(timestamp__gte=start_time).count(),
        }
    
    def get_business_metrics(self, start_time):
        """
        Get business metrics.
        """
        # Get business metrics
        metrics = BusinessMetric.objects.filter(
            timestamp__gte=start_time
        ).values('name').annotate(
            avg_value=Avg('value'),
            max_value=Max('value'),
            min_value=Min('value'),
            count=Count('id')
        ).order_by('name')
        
        # Get recent business metrics
        recent_metrics = BusinessMetric.objects.filter(
            timestamp__gte=start_time
        ).order_by('-timestamp')[:10]
        
        return {
            'metrics': list(metrics),
            'recent_metrics': list(recent_metrics.values('timestamp', 'name', 'value')),
        }


@method_decorator(staff_member_required, name='dispatch')
class SystemHealthAPIView(View):
    """
    API view for system health metrics.
    """
    def get(self, request):
        """
        Get current system health metrics.
        """
        # Trigger a metrics collection
        system_monitor._collect_and_log_metrics()
        
        # Get the latest system metrics
        latest_metrics = PerformanceMetric.objects.filter(
            name='system_metrics'
        ).order_by('-timestamp').first()
        
        if latest_metrics:
            return JsonResponse({
                'status': 'ok',
                'timestamp': latest_metrics.timestamp.isoformat(),
                'cpu_usage': latest_metrics.value,
                'memory_usage': latest_metrics.response_time,
                'updated': timezone.now().isoformat(),
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'No system metrics available',
                'updated': timezone.now().isoformat(),
            })


@method_decorator(staff_member_required, name='dispatch')
class ErrorMetricsAPIView(View):
    """
    API view for error metrics.
    """
    def get(self, request):
        """
        Get error metrics for the specified time range.
        """
        # Get time range from request or default to last 24 hours
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - datetime.timedelta(hours=hours)
        
        # Count errors by level and hour
        errors_by_hour = SystemLog.objects.filter(
            created_at__gte=start_time,
            level__in=['ERROR', 'CRITICAL']
        ).annotate(
            hour=TruncHour('created_at')
        ).values('hour', 'level').annotate(
            count=Count('id')
        ).order_by('hour', 'level')
        
        # Format the data for charting
        data = {}
        for entry in errors_by_hour:
            hour_str = entry['hour'].isoformat()
            if hour_str not in data:
                data[hour_str] = {'ERROR': 0, 'CRITICAL': 0}
            data[hour_str][entry['level']] = entry['count']
        
        # Convert to list format for the frontend
        result = [
            {
                'timestamp': ts,
                'ERROR': values['ERROR'],
                'CRITICAL': values['CRITICAL']
            }
            for ts, values in data.items()
        ]
        
        return JsonResponse({
            'status': 'ok',
            'data': result,
            'updated': timezone.now().isoformat(),
        })


@method_decorator(staff_member_required, name='dispatch')
class PerformanceMetricsAPIView(View):
    """
    API view for performance metrics.
    """
    def get(self, request):
        """
        Get performance metrics for the specified time range.
        """
        # Get time range from request or default to last 24 hours
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - datetime.timedelta(hours=hours)
        
        # Get response time metrics by hour
        response_times = PerformanceMetric.objects.filter(
            timestamp__gte=start_time,
            name='request_duration'
        ).annotate(
            hour=TruncHour('timestamp')
        ).values('hour').annotate(
            avg_time=Avg('value'),
            max_time=Max('value'),
            count=Count('id')
        ).order_by('hour')
        
        # Format the data for charting
        result = [
            {
                'timestamp': entry['hour'].isoformat(),
                'avg_time': round(entry['avg_time'], 2),
                'max_time': round(entry['max_time'], 2),
                'count': entry['count']
            }
            for entry in response_times
        ]
        
        return JsonResponse({
            'status': 'ok',
            'data': result,
            'updated': timezone.now().isoformat(),
        })


@method_decorator(staff_member_required, name='dispatch')
class SecurityMetricsAPIView(View):
    """
    API view for security metrics.
    """
    def get(self, request):
        """
        Get security metrics for the specified time range.
        """
        # Get time range from request or default to last 24 hours
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - datetime.timedelta(hours=hours)
        
        # Get security events by hour and type
        security_events = SecurityEvent.objects.filter(
            timestamp__gte=start_time
        ).annotate(
            hour=TruncHour('timestamp')
        ).values('hour', 'event_type').annotate(
            count=Count('id')
        ).order_by('hour', 'event_type')
        
        # Get unique event types
        event_types = SecurityEvent.objects.filter(
            timestamp__gte=start_time
        ).values_list('event_type', flat=True).distinct()
        
        # Format the data for charting
        data = {}
        for entry in security_events:
            hour_str = entry['hour'].isoformat()
            if hour_str not in data:
                data[hour_str] = {event_type: 0 for event_type in event_types}
            data[hour_str][entry['event_type']] = entry['count']
        
        # Convert to list format for the frontend
        result = [
            {
                'timestamp': ts,
                **values
            }
            for ts, values in data.items()
        ]
        
        return JsonResponse({
            'status': 'ok',
            'data': result,
            'event_types': list(event_types),
            'updated': timezone.now().isoformat(),
        })


@method_decorator(staff_member_required, name='dispatch')
class LogAnalysisView(TemplateView):
    """
    Log analysis view.
    """
    template_name = 'logs/analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get time range from request or default to last 24 hours
        time_range = self.request.GET.get('time_range', '24h')
        
        # Calculate start time based on time range
        now = timezone.now()
        if time_range == '1h':
            start_time = now - datetime.timedelta(hours=1)
        elif time_range == '6h':
            start_time = now - datetime.timedelta(hours=6)
        elif time_range == '24h':
            start_time = now - datetime.timedelta(hours=24)
        elif time_range == '7d':
            start_time = now - datetime.timedelta(days=7)
        elif time_range == '30d':
            start_time = now - datetime.timedelta(days=30)
        else:
            start_time = now - datetime.timedelta(hours=24)
        
        # Get log statistics
        context['log_stats'] = self.get_log_statistics(start_time)
        
        # Get log levels distribution
        context['log_levels'] = self.get_log_levels(start_time)
        
        # Get log sources distribution
        context['log_sources'] = self.get_log_sources(start_time)
        
        # Get recent logs
        context['recent_logs'] = self.get_recent_logs(start_time)
        
        # Add time range for the template
        context['time_range'] = time_range
        context['available_time_ranges'] = [
            {'value': '1h', 'label': 'Last Hour'},
            {'value': '6h', 'label': 'Last 6 Hours'},
            {'value': '24h', 'label': 'Last 24 Hours'},
            {'value': '7d', 'label': 'Last 7 Days'},
            {'value': '30d', 'label': 'Last 30 Days'},
        ]
        
        return context
    
    def get_log_statistics(self, start_time):
        """
        Get log statistics.
        """
        # Count logs by level
        log_counts = SystemLog.objects.filter(
            created_at__gte=start_time
        ).values('level').annotate(count=Count('id')).order_by('level')
        
        # Count logs by source
        source_counts = SystemLog.objects.filter(
            created_at__gte=start_time
        ).values('source').annotate(count=Count('id')).order_by('-count')[:10]
        
        # Count logs by event type
        event_counts = SystemLog.objects.filter(
            created_at__gte=start_time
        ).values('event_type').annotate(count=Count('id')).order_by('-count')[:10]
        
        return {
            'total_logs': SystemLog.objects.filter(created_at__gte=start_time).count(),
            'log_counts': list(log_counts),
            'source_counts': list(source_counts),
            'event_counts': list(event_counts),
        }
    
    def get_log_levels(self, start_time):
        """
        Get log levels distribution.
        """
        # Count logs by level and hour
        logs_by_hour = SystemLog.objects.filter(
            created_at__gte=start_time
        ).annotate(
            hour=TruncHour('created_at')
        ).values('hour', 'level').annotate(
            count=Count('id')
        ).order_by('hour', 'level')
        
        # Get unique levels
        levels = SystemLog.objects.filter(
            created_at__gte=start_time
        ).values_list('level', flat=True).distinct()
        
        # Format the data for charting
        data = {}
        for entry in logs_by_hour:
            hour_str = entry['hour'].isoformat()
            if hour_str not in data:
                data[hour_str] = {level: 0 for level in levels}
            data[hour_str][entry['level']] = entry['count']
        
        # Convert to list format for the frontend
        result = [
            {
                'timestamp': ts,
                **values
            }
            for ts, values in data.items()
        ]
        
        return {
            'data': result,
            'levels': list(levels),
        }
    
    def get_log_sources(self, start_time):
        """
        Get log sources distribution.
        """
        # Count logs by source
        sources = SystemLog.objects.filter(
            created_at__gte=start_time
        ).values('source').annotate(count=Count('id')).order_by('-count')[:10]
        
        return list(sources)
    
    def get_recent_logs(self, start_time):
        """
        Get recent logs.
        """
        # Get recent logs
        recent_logs = SystemLog.objects.filter(
            created_at__gte=start_time
        ).order_by('-created_at')[:100]
        
        return list(recent_logs.values('created_at', 'level', 'source', 'event_type', 'message'))


@method_decorator(staff_member_required, name='dispatch')
class AlertConfigView(TemplateView):
    """
    Alert configuration view.
    """
    template_name = 'logs/alerts.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add alert configurations
        from backend.logs.alerts import get_alert_configs
        context['alert_configs'] = get_alert_configs()
        
        return context


@method_decorator(staff_member_required, name='dispatch')
class AlertAPIView(View):
    """
    API view for alert management.
    """
    def get(self, request):
        """
        Get alert configurations.
        """
        from backend.logs.alerts import get_alert_configs
        
        return JsonResponse({
            'status': 'ok',
            'alerts': get_alert_configs(),
            'updated': timezone.now().isoformat(),
        })
    
    def post(self, request):
        """
        Update alert configuration.
        """
        try:
            data = json.loads(request.body)
            alert_id = data.get('id')
            enabled = data.get('enabled')
            threshold = data.get('threshold')
            
            from backend.logs.alerts import update_alert_config
            
            success = update_alert_config(alert_id, enabled=enabled, threshold=threshold)
            
            if success:
                return JsonResponse({
                    'status': 'ok',
                    'message': 'Alert configuration updated successfully',
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to update alert configuration',
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e),
            }, status=400)
# Ne
w API endpoints for log aggregation and frontend integration

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow frontend to send logs without authentication
@csrf_exempt
def receive_frontend_logs(request):
    """
    Receive log entries from the frontend.
    """
    try:
        data = request.data
        logs = data.get('logs', [])
        correlation_id = request.headers.get('X-Correlation-ID')
        
        for log_entry in logs:
            # Extract frontend-specific fields
            user_action = log_entry.get('action')
            component = log_entry.get('component')
            page_url = log_entry.get('pageUrl')
            user_agent = log_entry.get('userAgent')
            
            # Log the frontend entry
            log_frontend_entry(
                correlation_id=log_entry.get('correlationId') or correlation_id or 'unknown',
                level=log_entry.get('level', 'info'),
                message=log_entry.get('message', ''),
                user_id=log_entry.get('userId'),
                session_id=log_entry.get('sessionId'),
                context=log_entry.get('context'),
                user_action=user_action,
                component=component,
                page_url=page_url,
                user_agent=user_agent
            )
        
        return Response({
            'status': 'success', 
            'processed_logs': len(logs)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing frontend logs: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_log_entry(request):
    """
    Create a new log entry.
    """
    try:
        data = request.data
        correlation_id = getattr(request, 'correlation_id', None) or data.get('correlation_id')
        
        # Log the backend entry
        log_backend_entry(
            correlation_id=correlation_id or 'unknown',
            level=data.get('level', 'info'),
            message=data.get('message', ''),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
            context=data.get('context', {}),
            request_method=request.method,
            request_url=request.get_full_path(),
            response_status=200
        )
        
        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating log entry: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_aggregated_logs(request):
    """
    Retrieve logs based on filters using the aggregation service.
    """
    try:
        correlation_id = request.GET.get('correlation_id')
        level = request.GET.get('level')
        source = request.GET.get('source')
        limit = int(request.GET.get('limit', 100))
        
        if correlation_id:
            # Get logs for specific correlation ID
            logs = log_aggregation_service.get_logs_by_correlation_id(correlation_id)
        else:
            # Search logs
            query = request.GET.get('query', '')
            logs = log_aggregation_service.search_logs(
                query=query,
                level=level,
                source=source,
                limit=limit
            )
        
        return Response({'logs': logs, 'count': len(logs)}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_workflow_trace(request, correlation_id):
    """
    Get complete workflow trace for a correlation ID.
    """
    try:
        trace = log_aggregation_service.get_workflow_trace(correlation_id)
        return Response(trace, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving workflow trace: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_error_patterns(request):
    """
    Get error patterns analysis.
    """
    try:
        hours = int(request.GET.get('hours', 24))
        patterns = log_aggregation_service.get_error_patterns(hours)
        return Response(patterns, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving error patterns: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_old_logs(request):
    """
    Clean up old log entries.
    """
    try:
        hours = int(request.data.get('hours', 24))
        cleaned_count = log_aggregation_service.cleanup_old_logs(hours)
        return Response({
            'status': 'success',
            'cleaned_entries': cleaned_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error cleaning up logs: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)