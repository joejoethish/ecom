"""
Performance Monitoring Dashboard Views

Provides web-based dashboard for performance monitoring and optimization:
- Real-time metrics display
- Optimization recommendations
- Capacity planning
- Performance regression alerts
"""

import json
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db import connections

from .performance_monitor import get_performance_monitor
from .database_monitor import get_database_monitor


@staff_member_required
def performance_dashboard(request):
    """Main performance monitoring dashboard"""
    monitor = get_performance_monitor()
    
    # Get summary data
    context = {
        'databases': list(connections.databases.keys()),
        'monitoring_enabled': monitor.monitoring_enabled,
        'monitoring_interval': monitor.monitoring_interval,
        'total_recommendations': len(monitor.optimization_recommendations),
        'total_capacity_recommendations': len(monitor.capacity_recommendations),
        'total_regressions': len(monitor.regressions),
        'baselines_count': len(monitor.baselines)
    }
    
    return render(request, 'admin/performance_dashboard.html', context)


@staff_member_required
def performance_metrics_api(request):
    """API endpoint for current performance metrics"""
    monitor = get_performance_monitor()
    db_alias = request.GET.get('database', 'default')
    
    try:
        metrics = monitor.get_current_performance_metrics(db_alias)
        
        # Add timestamp
        response_data = {
            'timestamp': datetime.now().isoformat(),
            'database': db_alias,
            'metrics': metrics,
            'status': 'success'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@staff_member_required
def optimization_recommendations_api(request):
    """API endpoint for optimization recommendations"""
    monitor = get_performance_monitor()
    
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        priority_filter = request.GET.get('priority')
        
        recommendations = monitor.get_optimization_recommendations(limit * page)
        
        # Filter by priority if specified
        if priority_filter:
            recommendations = [r for r in recommendations if r['priority'] == priority_filter]
        
        # Paginate
        paginator = Paginator(recommendations, limit)
        page_obj = paginator.get_page(page)
        
        response_data = {
            'recommendations': list(page_obj),
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_count': len(recommendations),
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'status': 'success'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@staff_member_required
def capacity_recommendations_api(request):
    """API endpoint for capacity recommendations"""
    monitor = get_performance_monitor()
    
    try:
        limit = int(request.GET.get('limit', 20))
        urgency_filter = request.GET.get('urgency')
        
        recommendations = monitor.get_capacity_recommendations(limit)
        
        # Filter by urgency if specified
        if urgency_filter:
            recommendations = [r for r in recommendations if r['urgency'] == urgency_filter]
        
        response_data = {
            'recommendations': recommendations,
            'status': 'success'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@staff_member_required
def performance_regressions_api(request):
    """API endpoint for performance regressions"""
    monitor = get_performance_monitor()
    
    try:
        limit = int(request.GET.get('limit', 50))
        severity_filter = request.GET.get('severity')
        
        regressions = monitor.get_performance_regressions(limit)
        
        # Filter by severity if specified
        if severity_filter:
            regressions = [r for r in regressions if r['severity'] == severity_filter]
        
        response_data = {
            'regressions': regressions,
            'status': 'success'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@staff_member_required
def performance_baselines_api(request):
    """API endpoint for performance baselines"""
    monitor = get_performance_monitor()
    
    try:
        baselines = monitor.get_performance_baselines()
        
        response_data = {
            'baselines': baselines,
            'status': 'success'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def reset_baseline_api(request):
    """API endpoint to reset performance baseline"""
    monitor = get_performance_monitor()
    
    try:
        data = json.loads(request.body)
        metric_key = data.get('metric_key')
        
        if not metric_key:
            return JsonResponse({
                'status': 'error',
                'message': 'metric_key is required'
            }, status=400)
        
        monitor.reset_baseline(metric_key)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Baseline reset for {metric_key}'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def update_thresholds_api(request):
    """API endpoint to update monitoring thresholds"""
    monitor = get_performance_monitor()
    
    try:
        data = json.loads(request.body)
        
        regression_threshold = data.get('regression_threshold')
        capacity_warning = data.get('capacity_warning')
        capacity_critical = data.get('capacity_critical')
        
        monitor.update_thresholds(
            regression_threshold=regression_threshold,
            capacity_warning=capacity_warning,
            capacity_critical=capacity_critical
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Thresholds updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@staff_member_required
def performance_report_api(request):
    """API endpoint for comprehensive performance report"""
    monitor = get_performance_monitor()
    db_alias = request.GET.get('database', 'default')
    
    try:
        # Collect all data
        metrics = monitor.get_current_performance_metrics(db_alias)
        recommendations = monitor.get_optimization_recommendations(20)
        capacity_recs = monitor.get_capacity_recommendations(10)
        regressions = monitor.get_performance_regressions(20)
        baselines = monitor.get_performance_baselines()
        
        # Calculate summary statistics
        high_priority_recs = [r for r in recommendations if r['priority'] in ['high', 'critical']]
        capacity_issues = [c for c in capacity_recs if c['urgency'] in ['high', 'critical']]
        critical_regressions = [r for r in regressions if r['severity'] == 'critical']
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'database': db_alias,
            'current_metrics': metrics,
            'optimization_recommendations': recommendations,
            'capacity_recommendations': capacity_recs,
            'performance_regressions': regressions,
            'baselines_count': len(baselines),
            'summary': {
                'total_recommendations': len(recommendations),
                'high_priority_recommendations': len(high_priority_recs),
                'capacity_issues': len(capacity_issues),
                'active_regressions': len(regressions),
                'critical_regressions': len(critical_regressions),
                'health_status': 'critical' if critical_regressions or capacity_issues else 
                               'warning' if high_priority_recs or regressions else 'healthy'
            }
        }
        
        return JsonResponse(report)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@staff_member_required
def performance_history_api(request):
    """API endpoint for performance history data"""
    monitor = get_performance_monitor()
    db_alias = request.GET.get('database', 'default')
    metric_type = request.GET.get('metric', 'cpu')
    hours = int(request.GET.get('hours', 24))
    
    try:
        history_key = f"{db_alias}_{metric_type}"
        history = monitor.performance_history.get(history_key, [])
        
        # Filter by time range
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_history = [
            {
                'timestamp': point['timestamp'].isoformat(),
                'value': point['value']
            }
            for point in history
            if point['timestamp'] > cutoff_time
        ]
        
        response_data = {
            'database': db_alias,
            'metric': metric_type,
            'hours': hours,
            'data_points': len(filtered_history),
            'history': filtered_history,
            'status': 'success'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


class PerformanceMonitoringView(View):
    """Class-based view for performance monitoring operations"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        """Handle GET requests for monitoring status"""
        monitor = get_performance_monitor()
        
        status_data = {
            'monitoring_enabled': monitor.monitoring_enabled,
            'monitoring_interval': monitor.monitoring_interval,
            'regression_threshold': monitor.regression_threshold,
            'capacity_warning_threshold': monitor.capacity_warning_threshold,
            'capacity_critical_threshold': monitor.capacity_critical_threshold,
            'databases': list(connections.databases.keys()),
            'statistics': {
                'total_recommendations': len(monitor.optimization_recommendations),
                'total_capacity_recommendations': len(monitor.capacity_recommendations),
                'total_regressions': len(monitor.regressions),
                'baselines_count': len(monitor.baselines)
            }
        }
        
        return JsonResponse(status_data)
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Handle POST requests for monitoring control"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            monitor = get_performance_monitor()
            
            if action == 'start':
                interval = data.get('interval', 60)
                monitor.monitoring_interval = interval
                monitor.start_monitoring()
                message = f'Monitoring started with {interval}s interval'
                
            elif action == 'stop':
                monitor.stop_monitoring()
                message = 'Monitoring stopped'
                
            elif action == 'restart':
                monitor.stop_monitoring()
                interval = data.get('interval', monitor.monitoring_interval)
                monitor.monitoring_interval = interval
                monitor.start_monitoring()
                message = f'Monitoring restarted with {interval}s interval'
                
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid action. Use: start, stop, or restart'
                }, status=400)
            
            return JsonResponse({
                'status': 'success',
                'message': message,
                'monitoring_enabled': monitor.monitoring_enabled
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


@staff_member_required
def export_performance_data(request):
    """Export performance data in various formats"""
    monitor = get_performance_monitor()
    export_format = request.GET.get('format', 'json')
    data_type = request.GET.get('type', 'all')
    
    try:
        export_data = {}
        
        if data_type in ['all', 'metrics']:
            export_data['metrics'] = {}
            for db_alias in connections.databases.keys():
                export_data['metrics'][db_alias] = monitor.get_current_performance_metrics(db_alias)
        
        if data_type in ['all', 'recommendations']:
            export_data['recommendations'] = monitor.get_optimization_recommendations(100)
        
        if data_type in ['all', 'capacity']:
            export_data['capacity'] = monitor.get_capacity_recommendations(50)
        
        if data_type in ['all', 'regressions']:
            export_data['regressions'] = monitor.get_performance_regressions(100)
        
        if data_type in ['all', 'baselines']:
            export_data['baselines'] = monitor.get_performance_baselines()
        
        # Add metadata
        export_data['metadata'] = {
            'exported_at': datetime.now().isoformat(),
            'export_format': export_format,
            'data_type': data_type,
            'monitoring_enabled': monitor.monitoring_enabled,
            'monitoring_interval': monitor.monitoring_interval
        }
        
        if export_format == 'json':
            response = JsonResponse(export_data)
            response['Content-Disposition'] = f'attachment; filename="performance_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            return response
        
        elif export_format == 'csv':
            # Convert to CSV format (simplified)
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers and data based on data type
            if data_type == 'recommendations':
                writer.writerow(['Query Hash', 'Priority', 'Estimated Improvement', 'Implementation Effort', 'Timestamp'])
                for rec in export_data.get('recommendations', []):
                    writer.writerow([
                        rec['query_hash'],
                        rec['priority'],
                        rec['estimated_improvement'],
                        rec['implementation_effort'],
                        rec['timestamp']
                    ])
            
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="performance_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            return response
        
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Unsupported export format'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)