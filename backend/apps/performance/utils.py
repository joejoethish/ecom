import uuid
import time
import hashlib
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Max, Min, Count, Q
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def generate_transaction_id():
    """Generate unique transaction ID for APM"""
    return str(uuid.uuid4())

def calculate_percentile(values, percentile):
    """Calculate percentile for a list of values"""
    if not values:
        return 0
    
    values = sorted(values)
    k = (len(values) - 1) * percentile / 100
    f = int(k)
    c = k - f
    
    if f == len(values) - 1:
        return values[f]
    else:
        return values[f] * (1 - c) + values[f + 1] * c

class PerformanceAnalyzer:
    """Utility class for performance analysis"""
    
    @staticmethod
    def analyze_response_times(start_date, end_date, endpoint=None):
        """Analyze response times for given period"""
        from .models import PerformanceMetric
        
        filters = {
            'metric_type': 'response_time',
            'timestamp__gte': start_date,
            'timestamp__lte': end_date,
        }
        
        if endpoint:
            filters['endpoint'] = endpoint
        
        metrics = PerformanceMetric.objects.filter(**filters)
        
        if not metrics.exists():
            return None
        
        values = list(metrics.values_list('value', flat=True))
        
        return {
            'count': len(values),
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'p50': calculate_percentile(values, 50),
            'p95': calculate_percentile(values, 95),
            'p99': calculate_percentile(values, 99),
        }
    
    @staticmethod
    def detect_anomalies(metric_type, lookback_hours=24, threshold_multiplier=2):
        """Detect performance anomalies using statistical analysis"""
        from .models import PerformanceMetric
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        # Get historical data
        metrics = PerformanceMetric.objects.filter(
            metric_type=metric_type,
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).values_list('value', flat=True)
        
        if len(metrics) < 10:  # Need minimum data points
            return []
        
        values = list(metrics)
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Find anomalies (values beyond threshold * standard deviation)
        threshold = avg + (threshold_multiplier * std_dev)
        
        anomalies = PerformanceMetric.objects.filter(
            metric_type=metric_type,
            timestamp__gte=start_time,
            timestamp__lte=end_time,
            value__gt=threshold
        )
        
        return list(anomalies)
    
    @staticmethod
    def generate_performance_insights(start_date, end_date):
        """Generate performance insights and recommendations"""
        from .models import PerformanceMetric, DatabasePerformanceLog
        
        insights = []
        
        # Analyze response times
        response_analysis = PerformanceAnalyzer.analyze_response_times(start_date, end_date)
        if response_analysis and response_analysis['p95'] > 2000:
            insights.append({
                'type': 'warning',
                'category': 'response_time',
                'message': f"95th percentile response time is {response_analysis['p95']:.0f}ms, which exceeds recommended 2000ms threshold",
                'recommendation': "Consider optimizing slow endpoints and database queries"
            })
        
        # Analyze slow queries
        slow_queries = DatabasePerformanceLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            is_slow_query=True
        ).count()
        
        if slow_queries > 100:
            insights.append({
                'type': 'critical',
                'category': 'database',
                'message': f"Found {slow_queries} slow database queries",
                'recommendation': "Review and optimize database queries, consider adding indexes"
            })
        
        # Analyze error rates
        error_count = PerformanceMetric.objects.filter(
            metric_type='error_rate',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).count()
        
        total_requests = PerformanceMetric.objects.filter(
            metric_type='response_time',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).count()
        
        if total_requests > 0:
            error_rate = (error_count / total_requests) * 100
            if error_rate > 5:
                insights.append({
                    'type': 'critical',
                    'category': 'errors',
                    'message': f"Error rate is {error_rate:.2f}%, which exceeds recommended 5% threshold",
                    'recommendation': "Investigate and fix application errors"
                })
        
        return insights

class PerformanceOptimizer:
    """Utility class for performance optimization recommendations"""
    
    @staticmethod
    def analyze_database_performance():
        """Analyze database performance and provide optimization suggestions"""
        from .models import DatabasePerformanceLog
        
        # Find most frequent slow queries
        slow_queries = DatabasePerformanceLog.objects.filter(
            is_slow_query=True,
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).values('query_hash').annotate(
            count=Count('id'),
            avg_time=Avg('execution_time'),
            max_time=Max('execution_time')
        ).order_by('-count')[:10]
        
        recommendations = []
        
        for query in slow_queries:
            recommendations.append({
                'type': 'database_optimization',
                'query_hash': query['query_hash'],
                'frequency': query['count'],
                'avg_execution_time': query['avg_time'],
                'max_execution_time': query['max_time'],
                'recommendation': 'Consider adding database indexes or optimizing query structure'
            })
        
        return recommendations
    
    @staticmethod
    def analyze_endpoint_performance():
        """Analyze endpoint performance and provide optimization suggestions"""
        from .models import PerformanceMetric
        
        # Find slowest endpoints
        slow_endpoints = PerformanceMetric.objects.filter(
            metric_type='response_time',
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).values('endpoint').annotate(
            avg_time=Avg('value'),
            max_time=Max('value'),
            count=Count('id')
        ).filter(avg_time__gt=1000).order_by('-avg_time')[:10]
        
        recommendations = []
        
        for endpoint in slow_endpoints:
            recommendations.append({
                'type': 'endpoint_optimization',
                'endpoint': endpoint['endpoint'],
                'avg_response_time': endpoint['avg_time'],
                'max_response_time': endpoint['max_time'],
                'request_count': endpoint['count'],
                'recommendation': 'Consider caching, database optimization, or code optimization'
            })
        
        return recommendations

class AlertManager:
    """Utility class for managing performance alerts"""
    
    @staticmethod
    def check_thresholds():
        """Check performance metrics against defined thresholds"""
        from .models import PerformanceMetric, PerformanceAlert
        
        # Define thresholds
        thresholds = {
            'response_time': {'critical': 5000, 'high': 2000, 'medium': 1000},
            'cpu_usage': {'critical': 90, 'high': 80, 'medium': 70},
            'memory_usage': {'critical': 95, 'high': 85, 'medium': 75},
            'disk_usage': {'critical': 95, 'high': 90, 'medium': 80},
            'error_rate': {'critical': 10, 'high': 5, 'medium': 2},
        }
        
        alerts_created = []
        
        for metric_type, levels in thresholds.items():
            # Get recent metrics
            recent_metrics = PerformanceMetric.objects.filter(
                metric_type=metric_type,
                timestamp__gte=timezone.now() - timedelta(minutes=5)
            )
            
            if recent_metrics.exists():
                avg_value = recent_metrics.aggregate(Avg('value'))['value__avg']
                
                # Determine severity
                severity = 'low'
                threshold_value = 0
                
                for level, threshold in levels.items():
                    if avg_value >= threshold:
                        severity = level
                        threshold_value = threshold
                        break
                
                # Create alert if severity is medium or higher
                if severity in ['medium', 'high', 'critical']:
                    # Check if similar alert already exists
                    existing_alert = PerformanceAlert.objects.filter(
                        metric_type=metric_type,
                        status='active',
                        triggered_at__gte=timezone.now() - timedelta(hours=1)
                    ).first()
                    
                    if not existing_alert:
                        alert = PerformanceAlert.objects.create(
                            alert_type='threshold',
                            name=f"{metric_type.replace('_', ' ').title()} Alert",
                            description=f"{metric_type} exceeded threshold",
                            metric_type=metric_type,
                            threshold_value=threshold_value,
                            current_value=avg_value,
                            severity=severity,
                            metadata={
                                'metric_count': recent_metrics.count(),
                                'time_window': '5 minutes'
                            }
                        )
                        alerts_created.append(alert)
        
        return alerts_created
    
    @staticmethod
    def send_alert_notifications(alert):
        """Send alert notifications via email/SMS/Slack"""
        # This would integrate with notification services
        # For now, just log the alert
        logger.warning(f"Performance Alert: {alert.name} - {alert.description}")
        
        # Mark notification as sent
        alert.notification_sent = True
        alert.save()

class CapacityPlanner:
    """Utility class for capacity planning and forecasting"""
    
    @staticmethod
    def forecast_resource_usage(metric_type, days_ahead=30):
        """Forecast resource usage based on historical trends"""
        from .models import PerformanceMetric
        
        # Get historical data for the past 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        daily_averages = []
        current_date = start_date
        
        while current_date < end_date:
            next_date = current_date + timedelta(days=1)
            
            daily_avg = PerformanceMetric.objects.filter(
                metric_type=metric_type,
                timestamp__gte=current_date,
                timestamp__lt=next_date
            ).aggregate(Avg('value'))['value__avg']
            
            if daily_avg:
                daily_averages.append(daily_avg)
            
            current_date = next_date
        
        if len(daily_averages) < 7:  # Need minimum data
            return None
        
        # Simple linear regression for forecasting
        n = len(daily_averages)
        x_sum = sum(range(n))
        y_sum = sum(daily_averages)
        xy_sum = sum(i * daily_averages[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        intercept = (y_sum - slope * x_sum) / n
        
        # Forecast future values
        forecast = []
        for i in range(days_ahead):
            future_day = n + i
            predicted_value = slope * future_day + intercept
            forecast.append(max(0, predicted_value))  # Ensure non-negative
        
        return {
            'historical_data': daily_averages,
            'forecast': forecast,
            'trend': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
            'slope': slope,
            'confidence': min(100, max(0, 100 - abs(slope) * 10))  # Simple confidence metric
        }
    
    @staticmethod
    def generate_capacity_recommendations():
        """Generate capacity planning recommendations"""
        recommendations = []
        
        # Analyze CPU usage trend
        cpu_forecast = CapacityPlanner.forecast_resource_usage('cpu_usage')
        if cpu_forecast and max(cpu_forecast['forecast']) > 80:
            recommendations.append({
                'type': 'capacity',
                'resource': 'cpu',
                'message': 'CPU usage is forecasted to exceed 80% in the coming weeks',
                'recommendation': 'Consider scaling up server resources or optimizing CPU-intensive operations',
                'urgency': 'high' if max(cpu_forecast['forecast']) > 90 else 'medium'
            })
        
        # Analyze memory usage trend
        memory_forecast = CapacityPlanner.forecast_resource_usage('memory_usage')
        if memory_forecast and max(memory_forecast['forecast']) > 85:
            recommendations.append({
                'type': 'capacity',
                'resource': 'memory',
                'message': 'Memory usage is forecasted to exceed 85% in the coming weeks',
                'recommendation': 'Consider increasing server memory or optimizing memory usage',
                'urgency': 'high' if max(memory_forecast['forecast']) > 95 else 'medium'
            })
        
        # Analyze disk usage trend
        disk_forecast = CapacityPlanner.forecast_resource_usage('disk_usage')
        if disk_forecast and max(disk_forecast['forecast']) > 90:
            recommendations.append({
                'type': 'capacity',
                'resource': 'disk',
                'message': 'Disk usage is forecasted to exceed 90% in the coming weeks',
                'recommendation': 'Consider adding more storage or implementing data archival policies',
                'urgency': 'critical' if max(disk_forecast['forecast']) > 95 else 'high'
            })
        
        return recommendations