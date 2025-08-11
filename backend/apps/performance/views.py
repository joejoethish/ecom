from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min, Q
from django.core.cache import cache
from datetime import datetime, timedelta
import json

from .models import (
    PerformanceMetric, ApplicationPerformanceMonitor, DatabasePerformanceLog,
    ServerMetrics, UserExperienceMetrics, PerformanceAlert, PerformanceBenchmark,
    PerformanceReport, PerformanceIncident
)
from .serializers import (
    PerformanceMetricSerializer, ApplicationPerformanceMonitorSerializer,
    DatabasePerformanceLogSerializer, ServerMetricsSerializer,
    UserExperienceMetricsSerializer, PerformanceAlertSerializer,
    PerformanceBenchmarkSerializer, PerformanceReportSerializer,
    PerformanceIncidentSerializer
)
from .utils import PerformanceAnalyzer, PerformanceOptimizer, AlertManager, CapacityPlanner

class PerformanceMetricViewSet(viewsets.ModelViewSet):
    """Performance metrics CRUD and analytics"""
    queryset = PerformanceMetric.objects.all()
    serializer_class = PerformanceMetricSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Filter by metric type
        metric_type = self.request.query_params.get('metric_type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        # Filter by endpoint
        endpoint = self.request.query_params.get('endpoint')
        if endpoint:
            queryset = queryset.filter(endpoint=endpoint)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get real-time dashboard statistics"""
        cache_key = 'performance_dashboard_stats'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)
        
        # Response time statistics
        response_times = PerformanceMetric.objects.filter(
            metric_type='response_time',
            timestamp__gte=start_time
        ).aggregate(
            avg=Avg('value'),
            max=Max('value'),
            min=Min('value'),
            count=Count('id')
        )
        
        # Error rate
        error_count = PerformanceMetric.objects.filter(
            metric_type='error_rate',
            timestamp__gte=start_time
        ).count()
        
        total_requests = response_times['count'] or 1
        error_rate = (error_count / total_requests) * 100
        
        # System metrics
        latest_cpu = PerformanceMetric.objects.filter(
            metric_type='cpu_usage'
        ).order_by('-timestamp').first()
        
        latest_memory = PerformanceMetric.objects.filter(
            metric_type='memory_usage'
        ).order_by('-timestamp').first()
        
        # Active alerts
        active_alerts = PerformanceAlert.objects.filter(
            status='active'
        ).count()
        
        # Database performance
        slow_queries = DatabasePerformanceLog.objects.filter(
            is_slow_query=True,
            timestamp__gte=start_time
        ).count()
        
        stats = {
            'response_time': {
                'avg': round(response_times['avg'] or 0, 2),
                'max': round(response_times['max'] or 0, 2),
                'min': round(response_times['min'] or 0, 2),
                'count': response_times['count']
            },
            'error_rate': round(error_rate, 2),
            'cpu_usage': latest_cpu.value if latest_cpu else 0,
            'memory_usage': latest_memory.value if latest_memory else 0,
            'active_alerts': active_alerts,
            'slow_queries': slow_queries,
            'timestamp': end_time.isoformat()
        }
        
        # Cache for 1 minute
        cache.set(cache_key, stats, 60)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def time_series(self, request):
        """Get time series data for charts"""
        metric_type = request.query_params.get('metric_type', 'response_time')
        hours = int(request.query_params.get('hours', 24))
        interval = request.query_params.get('interval', 'hour')  # hour, minute
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Group by time interval
        if interval == 'minute':
            time_format = '%Y-%m-%d %H:%M'
            delta = timedelta(minutes=1)
        else:
            time_format = '%Y-%m-%d %H'
            delta = timedelta(hours=1)
        
        data_points = []
        current_time = start_time
        
        while current_time < end_time:
            next_time = current_time + delta
            
            metrics = PerformanceMetric.objects.filter(
                metric_type=metric_type,
                timestamp__gte=current_time,
                timestamp__lt=next_time
            )
            
            if metrics.exists():
                avg_value = metrics.aggregate(Avg('value'))['value__avg']
                data_points.append({
                    'timestamp': current_time.strftime(time_format),
                    'value': round(avg_value, 2)
                })
            else:
                data_points.append({
                    'timestamp': current_time.strftime(time_format),
                    'value': 0
                })
            
            current_time = next_time
        
        return Response({
            'metric_type': metric_type,
            'interval': interval,
            'data': data_points
        })
    
    @action(detail=False, methods=['get'])
    def top_endpoints(self, request):
        """Get top performing/slowest endpoints"""
        hours = int(request.query_params.get('hours', 24))
        limit = int(request.query_params.get('limit', 10))
        sort_by = request.query_params.get('sort_by', 'slowest')  # slowest, fastest, most_requests
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        endpoints = PerformanceMetric.objects.filter(
            metric_type='response_time',
            timestamp__gte=start_time,
            endpoint__isnull=False
        ).values('endpoint').annotate(
            avg_time=Avg('value'),
            max_time=Max('value'),
            min_time=Min('value'),
            request_count=Count('id')
        )
        
        if sort_by == 'slowest':
            endpoints = endpoints.order_by('-avg_time')
        elif sort_by == 'fastest':
            endpoints = endpoints.order_by('avg_time')
        elif sort_by == 'most_requests':
            endpoints = endpoints.order_by('-request_count')
        
        return Response(list(endpoints[:limit]))
    
    @action(detail=False, methods=['get'])
    def anomalies(self, request):
        """Detect performance anomalies"""
        metric_type = request.query_params.get('metric_type', 'response_time')
        hours = int(request.query_params.get('hours', 24))
        
        anomalies = PerformanceAnalyzer.detect_anomalies(metric_type, hours)
        serializer = self.get_serializer(anomalies, many=True)
        
        return Response({
            'metric_type': metric_type,
            'anomalies_count': len(anomalies),
            'anomalies': serializer.data
        })

class ApplicationPerformanceMonitorViewSet(viewsets.ModelViewSet):
    """APM transactions and traces"""
    queryset = ApplicationPerformanceMonitor.objects.all()
    serializer_class = ApplicationPerformanceMonitorSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_time__lte=end_date)
        
        return queryset.order_by('-start_time')
    
    @action(detail=False, methods=['get'])
    def transaction_stats(self, request):
        """Get transaction statistics"""
        hours = int(request.query_params.get('hours', 24))
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        stats = ApplicationPerformanceMonitor.objects.filter(
            start_time__gte=start_time
        ).aggregate(
            total_transactions=Count('id'),
            avg_duration=Avg('duration'),
            max_duration=Max('duration'),
            error_count=Count('id', filter=Q(status_code__gte=400))
        )
        
        # Transaction types breakdown
        transaction_types = ApplicationPerformanceMonitor.objects.filter(
            start_time__gte=start_time
        ).values('transaction_type').annotate(
            count=Count('id'),
            avg_duration=Avg('duration')
        ).order_by('-count')
        
        return Response({
            'stats': stats,
            'transaction_types': list(transaction_types)
        })

class DatabasePerformanceLogViewSet(viewsets.ModelViewSet):
    """Database performance monitoring"""
    queryset = DatabasePerformanceLog.objects.all()
    serializer_class = DatabasePerformanceLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter slow queries only
        slow_only = self.request.query_params.get('slow_only')
        if slow_only == 'true':
            queryset = queryset.filter(is_slow_query=True)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def slow_queries(self, request):
        """Get slow query analysis"""
        hours = int(request.query_params.get('hours', 24))
        limit = int(request.query_params.get('limit', 20))
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        slow_queries = DatabasePerformanceLog.objects.filter(
            is_slow_query=True,
            timestamp__gte=start_time
        ).values('query_hash').annotate(
            count=Count('id'),
            avg_time=Avg('execution_time'),
            max_time=Max('execution_time'),
            query_sample=Max('query')  # Get a sample query
        ).order_by('-count')[:limit]
        
        return Response(list(slow_queries))

class PerformanceAlertViewSet(viewsets.ModelViewSet):
    """Performance alerts management"""
    queryset = PerformanceAlert.objects.all()
    serializer_class = PerformanceAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-triggered_at')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert"""
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.save()
        
        return Response({'status': 'acknowledged'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        alert = self.get_object()
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        
        return Response({'status': 'resolved'})
    
    @action(detail=False, methods=['post'])
    def check_thresholds(self, request):
        """Manually trigger threshold checking"""
        alerts = AlertManager.check_thresholds()
        
        return Response({
            'alerts_created': len(alerts),
            'alerts': [alert.id for alert in alerts]
        })

class PerformanceReportViewSet(viewsets.ModelViewSet):
    """Performance reports and analytics"""
    queryset = PerformanceReport.objects.all()
    serializer_class = PerformanceReportSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate a custom performance report"""
        report_type = request.data.get('report_type', 'custom')
        start_date = datetime.fromisoformat(request.data.get('start_date'))
        end_date = datetime.fromisoformat(request.data.get('end_date'))
        metrics_included = request.data.get('metrics_included', [])
        
        # Generate report data
        report_data = {}
        
        if 'response_time' in metrics_included:
            report_data['response_time'] = PerformanceAnalyzer.analyze_response_times(
                start_date, end_date
            )
        
        if 'database' in metrics_included:
            report_data['database'] = {
                'slow_queries': DatabasePerformanceLog.objects.filter(
                    is_slow_query=True,
                    timestamp__gte=start_date,
                    timestamp__lte=end_date
                ).count(),
                'total_queries': DatabasePerformanceLog.objects.filter(
                    timestamp__gte=start_date,
                    timestamp__lte=end_date
                ).count()
            }
        
        # Generate insights
        insights = PerformanceAnalyzer.generate_performance_insights(start_date, end_date)
        
        # Generate recommendations
        db_recommendations = PerformanceOptimizer.analyze_database_performance()
        endpoint_recommendations = PerformanceOptimizer.analyze_endpoint_performance()
        
        # Create report
        report = PerformanceReport.objects.create(
            name=f"{report_type.title()} Report - {start_date.date()} to {end_date.date()}",
            report_type=report_type,
            date_range_start=start_date,
            date_range_end=end_date,
            metrics_included=metrics_included,
            report_data=report_data,
            insights=json.dumps(insights),
            recommendations=json.dumps(db_recommendations + endpoint_recommendations),
            generated_by=request.user
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def capacity_planning(self, request):
        """Get capacity planning analysis"""
        days_ahead = int(request.query_params.get('days_ahead', 30))
        
        # Forecast different metrics
        forecasts = {}
        metrics = ['cpu_usage', 'memory_usage', 'disk_usage']
        
        for metric in metrics:
            forecast = CapacityPlanner.forecast_resource_usage(metric, days_ahead)
            if forecast:
                forecasts[metric] = forecast
        
        # Generate recommendations
        recommendations = CapacityPlanner.generate_capacity_recommendations()
        
        return Response({
            'forecasts': forecasts,
            'recommendations': recommendations,
            'days_ahead': days_ahead
        })

class PerformanceIncidentViewSet(viewsets.ModelViewSet):
    """Performance incident management"""
    queryset = PerformanceIncident.objects.all()
    serializer_class = PerformanceIncidentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Generate incident ID
        incident_count = PerformanceIncident.objects.count() + 1
        incident_id = f"PERF-{incident_count:04d}"
        
        serializer.save(
            incident_id=incident_id,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update incident status"""
        incident = self.get_object()
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')
        
        if new_status in dict(PerformanceIncident.STATUS_CHOICES):
            old_status = incident.status
            incident.status = new_status
            
            if new_status == 'resolved':
                incident.resolved_at = timezone.now()
            
            # Add to timeline
            timeline_entry = {
                'timestamp': timezone.now().isoformat(),
                'action': 'status_change',
                'old_status': old_status,
                'new_status': new_status,
                'user': request.user.username,
                'comment': comment
            }
            
            incident.timeline.append(timeline_entry)
            incident.save()
            
            return Response({'status': 'updated'})
        
        return Response(
            {'error': 'Invalid status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def add_timeline_entry(self, request, pk=None):
        """Add entry to incident timeline"""
        incident = self.get_object()
        
        timeline_entry = {
            'timestamp': timezone.now().isoformat(),
            'action': request.data.get('action', 'comment'),
            'user': request.user.username,
            'comment': request.data.get('comment', ''),
            'metadata': request.data.get('metadata', {})
        }
        
        incident.timeline.append(timeline_entry)
        incident.save()
        
        return Response({'status': 'timeline_updated'})

class PerformanceBenchmarkViewSet(viewsets.ModelViewSet):
    """Performance benchmarking"""
    queryset = PerformanceBenchmark.objects.all()
    serializer_class = PerformanceBenchmarkSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def run_benchmark(self, request):
        """Run a performance benchmark test"""
        benchmark_type = request.data.get('benchmark_type')
        test_config = request.data.get('test_configuration', {})
        
        # This would integrate with actual benchmarking tools
        # For now, return mock results
        mock_results = {
            'response_time': {
                'avg': 150.5,
                'p95': 250.0,
                'p99': 400.0
            },
            'throughput': {
                'requests_per_second': 1000,
                'concurrent_users': 100
            },
            'resource_usage': {
                'cpu_avg': 45.2,
                'memory_avg': 62.1
            }
        }
        
        # Create benchmark record
        benchmark = PerformanceBenchmark.objects.create(
            name=f"Benchmark - {benchmark_type}",
            description=f"Performance benchmark for {benchmark_type}",
            benchmark_type=benchmark_type,
            baseline_value=0,  # Would be set from previous benchmarks
            current_value=mock_results['response_time']['avg'],
            target_value=100,  # Target response time
            unit='ms',
            test_configuration=test_config,
            test_results=mock_results,
            created_by=request.user
        )
        
        serializer = self.get_serializer(benchmark)
        return Response(serializer.data, status=status.HTTP_201_CREATED)