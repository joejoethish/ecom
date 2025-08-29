"""
Performance Monitoring Service

This module provides comprehensive performance monitoring capabilities including:
- Metrics collection from all system layers
- Threshold management for performance alerting
- Optimization engine with improvement suggestions
- Trend analysis for historical performance tracking
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from django.utils import timezone
from django.db import connection, transaction, models
from django.core.cache import cache
from django.conf import settings
import psutil
import time
import threading
from collections import defaultdict, deque

from .models import (
    PerformanceSnapshot, PerformanceThreshold, 
    WorkflowSession, TraceStep, ErrorLog
)
from .utils import PerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """Data structure for performance metrics"""
    layer: str
    component: str
    metric_name: str
    metric_value: float
    timestamp: datetime
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ThresholdAlert:
    """Data structure for threshold alerts"""
    metric_name: str
    layer: str
    component: str
    current_value: float
    threshold_value: float
    threshold_type: str  # 'warning' or 'critical'
    timestamp: datetime
    correlation_id: Optional[str] = None


@dataclass
class OptimizationRecommendation:
    """Data structure for optimization recommendations"""
    category: str  # 'database', 'api', 'frontend', 'system'
    priority: str  # 'high', 'medium', 'low'
    title: str
    description: str
    implementation_steps: List[str]
    expected_improvement: str
    affected_components: List[str]
    confidence_score: float  # 0.0 to 1.0


@dataclass
class TrendAnalysis:
    """Data structure for trend analysis results"""
    metric_name: str
    layer: str
    component: str
    trend_direction: str  # 'improving', 'degrading', 'stable'
    trend_strength: float  # 0.0 to 1.0
    current_average: float
    historical_average: float
    percentage_change: float
    data_points: int
    analysis_period_hours: int


class MetricsCollector:
    """Collects performance metrics from all system layers"""
    
    def __init__(self):
        self.collection_interval = getattr(settings, 'PERFORMANCE_COLLECTION_INTERVAL', 30)  # seconds
        self.is_collecting = False
        self._collection_thread = None
        self._metrics_buffer = deque(maxlen=1000)  # Buffer for batch processing
    
    def start_collection(self):
        """Start continuous metrics collection"""
        if self.is_collecting:
            logger.warning("Metrics collection already running")
            return
        
        self.is_collecting = True
        self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        logger.info("Started performance metrics collection")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        logger.info("Stopped performance metrics collection")
    
    def _collection_loop(self):
        """Main collection loop"""
        while self.is_collecting:
            try:
                self._collect_all_metrics()
                self._flush_metrics_buffer()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _collect_all_metrics(self):
        """Collect metrics from all layers"""
        timestamp = timezone.now()
        
        # Collect system metrics
        self._collect_system_metrics(timestamp)
        
        # Collect database metrics
        self._collect_database_metrics(timestamp)
        
        # Collect cache metrics
        self._collect_cache_metrics(timestamp)
        
        # Collect API metrics from recent traces
        self._collect_api_metrics(timestamp)
    
    def _collect_system_metrics(self, timestamp: datetime):
        """Collect system-level performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._add_metric('system', 'cpu', 'cpu_usage', cpu_percent, timestamp)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_mb = memory.used / (1024 * 1024)
            self._add_metric('system', 'memory', 'memory_usage', memory_percent, timestamp)
            self._add_metric('system', 'memory', 'memory_usage_mb', memory_mb, timestamp)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self._add_metric('system', 'disk', 'disk_usage', disk_percent, timestamp)
            
            # Network I/O
            network = psutil.net_io_counters()
            self._add_metric('system', 'network', 'bytes_sent', network.bytes_sent, timestamp)
            self._add_metric('system', 'network', 'bytes_recv', network.bytes_recv, timestamp)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_database_metrics(self, timestamp: datetime):
        """Collect database performance metrics"""
        try:
            # Query execution metrics from Django connection
            queries = connection.queries_log
            if queries:
                recent_queries = [q for q in queries if 'time' in q]
                if recent_queries:
                    query_times = [float(q['time']) for q in recent_queries[-10:]]  # Last 10 queries
                    avg_query_time = statistics.mean(query_times) * 1000  # Convert to ms
                    max_query_time = max(query_times) * 1000
                    
                    self._add_metric('database', 'mysql', 'avg_query_time', avg_query_time, timestamp)
                    self._add_metric('database', 'mysql', 'max_query_time', max_query_time, timestamp)
                    self._add_metric('database', 'mysql', 'query_count', len(recent_queries), timestamp)
            
            # Connection pool metrics (if available)
            if hasattr(connection, 'pool'):
                pool = connection.pool
                if hasattr(pool, 'size') and hasattr(pool, 'checked_out'):
                    pool_usage = (pool.checked_out() / pool.size()) * 100
                    self._add_metric('database', 'connection_pool', 'pool_usage', pool_usage, timestamp)
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
    
    def _collect_cache_metrics(self, timestamp: datetime):
        """Collect cache performance metrics"""
        try:
            # Redis cache metrics (if using Redis)
            if hasattr(cache, '_cache') and hasattr(cache._cache, '_client'):
                redis_client = cache._cache._client
                if hasattr(redis_client, 'info'):
                    info = redis_client.info()
                    
                    # Memory usage
                    used_memory = info.get('used_memory', 0) / (1024 * 1024)  # MB
                    self._add_metric('cache', 'redis', 'memory_usage_mb', used_memory, timestamp)
                    
                    # Hit rate
                    hits = info.get('keyspace_hits', 0)
                    misses = info.get('keyspace_misses', 0)
                    if hits + misses > 0:
                        hit_rate = (hits / (hits + misses)) * 100
                        self._add_metric('cache', 'redis', 'cache_hit_rate', hit_rate, timestamp)
                    
                    # Connected clients
                    connected_clients = info.get('connected_clients', 0)
                    self._add_metric('cache', 'redis', 'connected_clients', connected_clients, timestamp)
            
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
    
    def _collect_api_metrics(self, timestamp: datetime):
        """Collect API performance metrics from recent traces"""
        try:
            # Get recent API trace steps (last 5 minutes)
            five_minutes_ago = timestamp - timedelta(minutes=5)
            recent_steps = TraceStep.objects.filter(
                layer='api',
                start_time__gte=five_minutes_ago,
                duration_ms__isnull=False
            ).values('component', 'duration_ms')
            
            if recent_steps:
                # Group by component
                component_metrics = defaultdict(list)
                for step in recent_steps:
                    component_metrics[step['component']].append(step['duration_ms'])
                
                # Calculate metrics for each component
                for component, durations in component_metrics.items():
                    avg_response_time = statistics.mean(durations)
                    max_response_time = max(durations)
                    throughput = len(durations) / 5  # requests per minute / 5 = req/sec
                    
                    self._add_metric('api', component, 'response_time', avg_response_time, timestamp)
                    self._add_metric('api', component, 'max_response_time', max_response_time, timestamp)
                    self._add_metric('api', component, 'throughput', throughput, timestamp)
            
            # Error rate from recent error logs
            recent_errors = ErrorLog.objects.filter(
                layer='api',
                timestamp__gte=five_minutes_ago
            ).values('component').annotate(error_count=models.Count('id'))
            
            for error_data in recent_errors:
                component = error_data['component']
                error_count = error_data['error_count']
                # Estimate error rate (errors per minute)
                error_rate = error_count / 5
                self._add_metric('api', component, 'error_rate', error_rate, timestamp)
            
        except Exception as e:
            logger.error(f"Error collecting API metrics: {e}")
    
    def _add_metric(self, layer: str, component: str, metric_name: str, 
                   metric_value: float, timestamp: datetime, 
                   correlation_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Add metric to buffer"""
        metric = MetricData(
            layer=layer,
            component=component,
            metric_name=metric_name,
            metric_value=metric_value,
            timestamp=timestamp,
            correlation_id=correlation_id,
            metadata=metadata
        )
        self._metrics_buffer.append(metric)
    
    def _flush_metrics_buffer(self):
        """Flush metrics buffer to database"""
        if not self._metrics_buffer:
            return
        
        try:
            with transaction.atomic():
                snapshots = []
                for metric in self._metrics_buffer:
                    # Get threshold values
                    threshold = PerformanceThreshold.objects.filter(
                        metric_name=metric.metric_name,
                        layer=metric.layer,
                        component=metric.component,
                        enabled=True
                    ).first()
                    
                    snapshot = PerformanceSnapshot(
                        correlation_id=metric.correlation_id,
                        timestamp=metric.timestamp,
                        layer=metric.layer,
                        component=metric.component,
                        metric_name=metric.metric_name,
                        metric_value=metric.metric_value,
                        threshold_warning=threshold.warning_threshold if threshold else None,
                        threshold_critical=threshold.critical_threshold if threshold else None,
                        metadata=metric.metadata or {}
                    )
                    snapshots.append(snapshot)
                
                PerformanceSnapshot.objects.bulk_create(snapshots, batch_size=100)
                self._metrics_buffer.clear()
                
        except Exception as e:
            logger.error(f"Error flushing metrics buffer: {e}")
    
    def collect_manual_metric(self, layer: str, component: str, metric_name: str, 
                            metric_value: float, correlation_id: Optional[str] = None,
                            metadata: Optional[Dict] = None):
        """Manually collect a specific metric"""
        timestamp = timezone.now()
        self._add_metric(layer, component, metric_name, metric_value, 
                        timestamp, correlation_id, metadata)
        
        # Immediately flush if not in continuous collection mode
        if not self.is_collecting:
            self._flush_metrics_buffer()


class ThresholdManager:
    """Manages performance thresholds and alerting rules"""
    
    def __init__(self):
        self._threshold_cache = {}
        self._cache_expiry = timezone.now()
        self._cache_duration = timedelta(minutes=5)
    
    def get_threshold(self, metric_name: str, layer: str, component: str) -> Optional[PerformanceThreshold]:
        """Get threshold for specific metric"""
        cache_key = f"{layer}.{component}.{metric_name}"
        
        # Check cache
        if (timezone.now() < self._cache_expiry and 
            cache_key in self._threshold_cache):
            return self._threshold_cache[cache_key]
        
        # Refresh cache if expired
        if timezone.now() >= self._cache_expiry:
            self._refresh_threshold_cache()
        
        return self._threshold_cache.get(cache_key)
    
    def _refresh_threshold_cache(self):
        """Refresh threshold cache"""
        self._threshold_cache.clear()
        
        thresholds = PerformanceThreshold.objects.filter(enabled=True)
        for threshold in thresholds:
            cache_key = f"{threshold.layer}.{threshold.component or ''}.{threshold.metric_name}"
            self._threshold_cache[cache_key] = threshold
        
        self._cache_expiry = timezone.now() + self._cache_duration
    
    def check_threshold_violations(self, metrics: List[MetricData]) -> List[ThresholdAlert]:
        """Check metrics against thresholds and return violations"""
        alerts = []
        
        for metric in metrics:
            threshold = self.get_threshold(metric.metric_name, metric.layer, metric.component)
            if not threshold:
                continue
            
            # Check critical threshold
            if (threshold.critical_threshold and 
                metric.metric_value >= threshold.critical_threshold and
                threshold.alert_on_critical):
                alerts.append(ThresholdAlert(
                    metric_name=metric.metric_name,
                    layer=metric.layer,
                    component=metric.component,
                    current_value=metric.metric_value,
                    threshold_value=threshold.critical_threshold,
                    threshold_type='critical',
                    timestamp=metric.timestamp,
                    correlation_id=metric.correlation_id
                ))
            
            # Check warning threshold
            elif (threshold.warning_threshold and 
                  metric.metric_value >= threshold.warning_threshold and
                  threshold.alert_on_warning):
                alerts.append(ThresholdAlert(
                    metric_name=metric.metric_name,
                    layer=metric.layer,
                    component=metric.component,
                    current_value=metric.metric_value,
                    threshold_value=threshold.warning_threshold,
                    threshold_type='warning',
                    timestamp=metric.timestamp,
                    correlation_id=metric.correlation_id
                ))
        
        return alerts
    
    def create_threshold(self, metric_name: str, layer: str, component: str,
                        warning_threshold: float, critical_threshold: float,
                        alert_on_warning: bool = True, alert_on_critical: bool = True) -> PerformanceThreshold:
        """Create a new performance threshold"""
        threshold, created = PerformanceThreshold.objects.get_or_create(
            metric_name=metric_name,
            layer=layer,
            component=component,
            defaults={
                'warning_threshold': warning_threshold,
                'critical_threshold': critical_threshold,
                'alert_on_warning': alert_on_warning,
                'alert_on_critical': alert_on_critical,
                'enabled': True
            }
        )
        
        if not created:
            # Update existing threshold
            threshold.warning_threshold = warning_threshold
            threshold.critical_threshold = critical_threshold
            threshold.alert_on_warning = alert_on_warning
            threshold.alert_on_critical = alert_on_critical
            threshold.save()
        
        # Clear cache to force refresh
        self._cache_expiry = timezone.now()
        
        return threshold
    
    def get_default_thresholds(self) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """Get default threshold values for different metrics"""
        return {
            'response_time': {
                'api': (200.0, 500.0),  # warning, critical in ms
                'database': (50.0, 200.0),
                'frontend': (100.0, 300.0)
            },
            'memory_usage': {
                'system': (80.0, 95.0),  # warning, critical in %
                'cache': (85.0, 95.0)
            },
            'cpu_usage': {
                'system': (80.0, 95.0)  # warning, critical in %
            },
            'error_rate': {
                'api': (1.0, 5.0),  # warning, critical in errors/min
                'frontend': (0.5, 2.0)
            },
            'cache_hit_rate': {
                'cache': (80.0, 60.0)  # warning, critical in % (lower is worse)
            }
        }
    
    def initialize_default_thresholds(self):
        """Initialize default thresholds if they don't exist"""
        defaults = self.get_default_thresholds()
        
        for metric_name, layer_thresholds in defaults.items():
            for layer, (warning, critical) in layer_thresholds.items():
                # Check if threshold already exists
                if not PerformanceThreshold.objects.filter(
                    metric_name=metric_name,
                    layer=layer,
                    component=''
                ).exists():
                    self.create_threshold(
                        metric_name=metric_name,
                        layer=layer,
                        component='',
                        warning_threshold=warning,
                        critical_threshold=critical
                    )
        
        logger.info("Initialized default performance thresholds")


class OptimizationEngine:
    """Analyzes performance data and suggests improvements"""
    
    def __init__(self):
        self.analysis_window_hours = 24  # Analyze last 24 hours by default
    
    def analyze_performance_issues(self, hours: int = None) -> List[OptimizationRecommendation]:
        """Analyze performance data and generate optimization recommendations"""
        analysis_hours = hours or self.analysis_window_hours
        since = timezone.now() - timedelta(hours=analysis_hours)
        
        recommendations = []
        
        # Analyze database performance
        recommendations.extend(self._analyze_database_performance(since))
        
        # Analyze API performance
        recommendations.extend(self._analyze_api_performance(since))
        
        # Analyze system performance
        recommendations.extend(self._analyze_system_performance(since))
        
        # Analyze cache performance
        recommendations.extend(self._analyze_cache_performance(since))
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}[x.priority],
            x.confidence_score
        ), reverse=True)
        
        return recommendations
    
    def _analyze_database_performance(self, since: datetime) -> List[OptimizationRecommendation]:
        """Analyze database performance issues"""
        recommendations = []
        
        # Check for slow queries
        slow_query_snapshots = PerformanceSnapshot.objects.filter(
            layer='database',
            metric_name='avg_query_time',
            timestamp__gte=since,
            metric_value__gt=100  # > 100ms
        ).values('component').annotate(
            avg_time=models.Avg('metric_value'),
            max_time=models.Max('metric_value'),
            count=models.Count('id')
        )
        
        for snapshot in slow_query_snapshots:
            if snapshot['avg_time'] > 200:  # Average > 200ms
                recommendations.append(OptimizationRecommendation(
                    category='database',
                    priority='high',
                    title=f"Slow queries detected in {snapshot['component']}",
                    description=f"Average query time is {snapshot['avg_time']:.1f}ms, which exceeds recommended thresholds.",
                    implementation_steps=[
                        "Analyze slow query log to identify problematic queries",
                        "Add appropriate database indexes for frequently queried columns",
                        "Consider query optimization or restructuring",
                        "Implement query result caching for expensive operations"
                    ],
                    expected_improvement="30-70% reduction in query response times",
                    affected_components=[snapshot['component']],
                    confidence_score=0.9
                ))
        
        # Check connection pool usage
        pool_usage_snapshots = PerformanceSnapshot.objects.filter(
            layer='database',
            component='connection_pool',
            metric_name='pool_usage',
            timestamp__gte=since,
            metric_value__gt=80  # > 80%
        )
        
        if pool_usage_snapshots.exists():
            avg_usage = pool_usage_snapshots.aggregate(avg=models.Avg('metric_value'))['avg']
            recommendations.append(OptimizationRecommendation(
                category='database',
                priority='medium',
                title="High database connection pool usage",
                description=f"Connection pool usage averaging {avg_usage:.1f}% may cause connection bottlenecks.",
                implementation_steps=[
                    "Increase database connection pool size",
                    "Implement connection pooling optimization",
                    "Review and optimize long-running database operations",
                    "Consider read replicas for read-heavy operations"
                ],
                expected_improvement="Reduced connection wait times and improved concurrency",
                affected_components=['connection_pool'],
                confidence_score=0.8
            ))
        
        return recommendations
    
    def _analyze_api_performance(self, since: datetime) -> List[OptimizationRecommendation]:
        """Analyze API performance issues"""
        recommendations = []
        
        # Check for slow API endpoints
        slow_api_snapshots = PerformanceSnapshot.objects.filter(
            layer='api',
            metric_name='response_time',
            timestamp__gte=since,
            metric_value__gt=500  # > 500ms
        ).values('component').annotate(
            avg_time=models.Avg('metric_value'),
            max_time=models.Max('metric_value'),
            count=models.Count('id')
        )
        
        for snapshot in slow_api_snapshots:
            recommendations.append(OptimizationRecommendation(
                category='api',
                priority='high',
                title=f"Slow API endpoint: {snapshot['component']}",
                description=f"Average response time is {snapshot['avg_time']:.1f}ms, exceeding performance targets.",
                implementation_steps=[
                    "Profile the endpoint to identify bottlenecks",
                    "Optimize database queries using select_related/prefetch_related",
                    "Implement response caching for cacheable data",
                    "Consider pagination for large result sets",
                    "Add database indexes for query optimization"
                ],
                expected_improvement="50-80% reduction in response times",
                affected_components=[snapshot['component']],
                confidence_score=0.85
            ))
        
        # Check for high error rates
        error_rate_snapshots = PerformanceSnapshot.objects.filter(
            layer='api',
            metric_name='error_rate',
            timestamp__gte=since,
            metric_value__gt=2  # > 2 errors/min
        ).values('component').annotate(
            avg_rate=models.Avg('metric_value'),
            max_rate=models.Max('metric_value')
        )
        
        for snapshot in error_rate_snapshots:
            recommendations.append(OptimizationRecommendation(
                category='api',
                priority='high',
                title=f"High error rate in {snapshot['component']}",
                description=f"Error rate averaging {snapshot['avg_rate']:.1f} errors/minute indicates stability issues.",
                implementation_steps=[
                    "Review error logs to identify common error patterns",
                    "Implement proper input validation and error handling",
                    "Add circuit breakers for external service calls",
                    "Improve error monitoring and alerting",
                    "Consider implementing retry logic with exponential backoff"
                ],
                expected_improvement="Reduced error rates and improved system stability",
                affected_components=[snapshot['component']],
                confidence_score=0.9
            ))
        
        return recommendations
    
    def _analyze_system_performance(self, since: datetime) -> List[OptimizationRecommendation]:
        """Analyze system performance issues"""
        recommendations = []
        
        # Check CPU usage
        high_cpu_snapshots = PerformanceSnapshot.objects.filter(
            layer='system',
            component='cpu',
            metric_name='cpu_usage',
            timestamp__gte=since,
            metric_value__gt=80  # > 80%
        )
        
        if high_cpu_snapshots.exists():
            avg_cpu = high_cpu_snapshots.aggregate(avg=models.Avg('metric_value'))['avg']
            recommendations.append(OptimizationRecommendation(
                category='system',
                priority='medium',
                title="High CPU usage detected",
                description=f"CPU usage averaging {avg_cpu:.1f}% may impact system performance.",
                implementation_steps=[
                    "Profile application to identify CPU-intensive operations",
                    "Optimize algorithms and data processing logic",
                    "Consider horizontal scaling or upgrading hardware",
                    "Implement caching to reduce computational overhead",
                    "Review and optimize background tasks"
                ],
                expected_improvement="Reduced CPU load and improved response times",
                affected_components=['cpu'],
                confidence_score=0.7
            ))
        
        # Check memory usage
        high_memory_snapshots = PerformanceSnapshot.objects.filter(
            layer='system',
            component='memory',
            metric_name='memory_usage',
            timestamp__gte=since,
            metric_value__gt=85  # > 85%
        )
        
        if high_memory_snapshots.exists():
            avg_memory = high_memory_snapshots.aggregate(avg=models.Avg('metric_value'))['avg']
            recommendations.append(OptimizationRecommendation(
                category='system',
                priority='high',
                title="High memory usage detected",
                description=f"Memory usage averaging {avg_memory:.1f}% may cause performance degradation.",
                implementation_steps=[
                    "Profile application memory usage to identify memory leaks",
                    "Optimize data structures and object lifecycle management",
                    "Implement proper garbage collection tuning",
                    "Consider increasing available memory or optimizing usage",
                    "Review caching strategies to balance memory vs performance"
                ],
                expected_improvement="Reduced memory pressure and improved stability",
                affected_components=['memory'],
                confidence_score=0.8
            ))
        
        return recommendations
    
    def _analyze_cache_performance(self, since: datetime) -> List[OptimizationRecommendation]:
        """Analyze cache performance issues"""
        recommendations = []
        
        # Check cache hit rate
        low_hit_rate_snapshots = PerformanceSnapshot.objects.filter(
            layer='cache',
            metric_name='cache_hit_rate',
            timestamp__gte=since,
            metric_value__lt=70  # < 70%
        )
        
        if low_hit_rate_snapshots.exists():
            avg_hit_rate = low_hit_rate_snapshots.aggregate(avg=models.Avg('metric_value'))['avg']
            recommendations.append(OptimizationRecommendation(
                category='cache',
                priority='medium',
                title="Low cache hit rate",
                description=f"Cache hit rate averaging {avg_hit_rate:.1f}% indicates suboptimal caching strategy.",
                implementation_steps=[
                    "Review caching strategy and identify frequently accessed data",
                    "Optimize cache key patterns and expiration times",
                    "Implement cache warming for critical data",
                    "Consider increasing cache memory allocation",
                    "Review cache invalidation patterns"
                ],
                expected_improvement="Improved cache efficiency and reduced database load",
                affected_components=['redis'],
                confidence_score=0.75
            ))
        
        return recommendations


class TrendAnalyzer:
    """Analyzes historical performance trends"""
    
    def __init__(self):
        self.default_analysis_hours = 168  # 7 days
        self.comparison_hours = 24  # Compare with last 24 hours
    
    def analyze_trends(self, metric_name: str = None, layer: str = None, 
                      component: str = None, hours: int = None) -> List[TrendAnalysis]:
        """Analyze performance trends for specified metrics"""
        analysis_hours = hours or self.default_analysis_hours
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=analysis_hours)
        comparison_start = end_time - timedelta(hours=self.comparison_hours)
        
        # Build query filters
        filters = {
            'timestamp__gte': start_time,
            'timestamp__lte': end_time
        }
        
        if metric_name:
            filters['metric_name'] = metric_name
        if layer:
            filters['layer'] = layer
        if component:
            filters['component'] = component
        
        # Get metrics grouped by layer, component, and metric_name
        metrics_query = PerformanceSnapshot.objects.filter(**filters).values(
            'layer', 'component', 'metric_name'
        ).annotate(
            avg_value=models.Avg('metric_value'),
            count=models.Count('id')
        ).filter(count__gte=10)  # Require at least 10 data points
        
        trends = []
        
        for metric_group in metrics_query:
            trend = self._analyze_single_metric_trend(
                metric_group['metric_name'],
                metric_group['layer'],
                metric_group['component'],
                start_time,
                end_time,
                comparison_start,
                analysis_hours
            )
            if trend:
                trends.append(trend)
        
        return trends
    
    def _analyze_single_metric_trend(self, metric_name: str, layer: str, component: str,
                                   start_time: datetime, end_time: datetime,
                                   comparison_start: datetime, analysis_hours: int) -> Optional[TrendAnalysis]:
        """Analyze trend for a single metric"""
        try:
            # Get all data points for the metric
            all_snapshots = PerformanceSnapshot.objects.filter(
                metric_name=metric_name,
                layer=layer,
                component=component,
                timestamp__gte=start_time,
                timestamp__lte=end_time
            ).order_by('timestamp').values('metric_value', 'timestamp')
            
            if len(all_snapshots) < 10:
                return None
            
            # Get recent data points for comparison
            recent_snapshots = PerformanceSnapshot.objects.filter(
                metric_name=metric_name,
                layer=layer,
                component=component,
                timestamp__gte=comparison_start,
                timestamp__lte=end_time
            ).values('metric_value')
            
            if not recent_snapshots:
                return None
            
            # Calculate averages
            all_values = [s['metric_value'] for s in all_snapshots]
            recent_values = [s['metric_value'] for s in recent_snapshots]
            
            historical_average = statistics.mean(all_values)
            current_average = statistics.mean(recent_values)
            
            # Calculate trend direction and strength
            trend_direction, trend_strength = self._calculate_trend(all_snapshots)
            
            # Calculate percentage change
            if historical_average != 0:
                percentage_change = ((current_average - historical_average) / historical_average) * 100
            else:
                percentage_change = 0
            
            return TrendAnalysis(
                metric_name=metric_name,
                layer=layer,
                component=component,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                current_average=current_average,
                historical_average=historical_average,
                percentage_change=percentage_change,
                data_points=len(all_snapshots),
                analysis_period_hours=analysis_hours
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trend for {layer}.{component}.{metric_name}: {e}")
            return None
    
    def _calculate_trend(self, snapshots: List[Dict]) -> Tuple[str, float]:
        """Calculate trend direction and strength using linear regression"""
        if len(snapshots) < 2:
            return 'stable', 0.0
        
        try:
            # Convert timestamps to numeric values (seconds since first timestamp)
            first_timestamp = snapshots[0]['timestamp']
            x_values = []
            y_values = []
            
            for snapshot in snapshots:
                if isinstance(snapshot['timestamp'], str):
                    # Parse ISO format timestamp
                    timestamp = datetime.fromisoformat(snapshot['timestamp'].replace('Z', '+00:00'))
                else:
                    timestamp = snapshot['timestamp']
                
                x = (timestamp - first_timestamp).total_seconds()
                y = snapshot['metric_value']
                x_values.append(x)
                y_values.append(y)
            
            # Simple linear regression
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            # Calculate slope
            denominator = n * sum_x2 - sum_x * sum_x
            if denominator == 0:
                return 'stable', 0.0
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            
            # Calculate correlation coefficient for trend strength
            mean_x = sum_x / n
            mean_y = sum_y / n
            
            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
            sum_x_diff_sq = sum((x - mean_x) ** 2 for x in x_values)
            sum_y_diff_sq = sum((y - mean_y) ** 2 for y in y_values)
            
            if sum_x_diff_sq == 0 or sum_y_diff_sq == 0:
                return 'stable', 0.0
            
            correlation = numerator / (sum_x_diff_sq * sum_y_diff_sq) ** 0.5
            trend_strength = abs(correlation)
            
            # Determine trend direction
            if abs(slope) < 0.001:  # Very small slope
                trend_direction = 'stable'
            elif slope > 0:
                trend_direction = 'degrading'  # Assuming higher values are worse for most metrics
            else:
                trend_direction = 'improving'
            
            # For metrics where lower is worse (like cache hit rate), reverse the logic
            if 'hit_rate' in snapshots[0].get('metric_name', ''):
                if slope > 0:
                    trend_direction = 'improving'
                elif slope < 0:
                    trend_direction = 'degrading'
            
            return trend_direction, min(trend_strength, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return 'stable', 0.0
    
    def get_trend_summary(self, hours: int = None) -> Dict[str, Any]:
        """Get a summary of all performance trends"""
        trends = self.analyze_trends(hours=hours)
        
        summary = {
            'total_metrics': len(trends),
            'improving_trends': 0,
            'degrading_trends': 0,
            'stable_trends': 0,
            'high_confidence_trends': 0,
            'critical_degradations': [],
            'significant_improvements': []
        }
        
        for trend in trends:
            # Count trend directions
            if trend.trend_direction == 'improving':
                summary['improving_trends'] += 1
            elif trend.trend_direction == 'degrading':
                summary['degrading_trends'] += 1
            else:
                summary['stable_trends'] += 1
            
            # Count high confidence trends
            if trend.trend_strength > 0.7:
                summary['high_confidence_trends'] += 1
            
            # Identify critical degradations
            if (trend.trend_direction == 'degrading' and 
                trend.trend_strength > 0.6 and 
                abs(trend.percentage_change) > 20):
                summary['critical_degradations'].append({
                    'metric': f"{trend.layer}.{trend.component}.{trend.metric_name}",
                    'percentage_change': trend.percentage_change,
                    'trend_strength': trend.trend_strength
                })
            
            # Identify significant improvements
            if (trend.trend_direction == 'improving' and 
                trend.trend_strength > 0.6 and 
                abs(trend.percentage_change) > 15):
                summary['significant_improvements'].append({
                    'metric': f"{trend.layer}.{trend.component}.{trend.metric_name}",
                    'percentage_change': trend.percentage_change,
                    'trend_strength': trend.trend_strength
                })
        
        return summary


class PerformanceMonitoringService:
    """Main service that coordinates all performance monitoring components"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.threshold_manager = ThresholdManager()
        self.optimization_engine = OptimizationEngine()
        self.trend_analyzer = TrendAnalyzer()
        self._initialized = False
    
    def initialize(self):
        """Initialize the performance monitoring service"""
        if self._initialized:
            return
        
        # Initialize default thresholds
        self.threshold_manager.initialize_default_thresholds()
        
        # Start metrics collection
        self.metrics_collector.start_collection()
        
        self._initialized = True
        logger.info("Performance monitoring service initialized")
    
    def shutdown(self):
        """Shutdown the performance monitoring service"""
        self.metrics_collector.stop_collection()
        self._initialized = False
        logger.info("Performance monitoring service shutdown")
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive system health summary"""
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Get recent performance snapshots
        recent_snapshots = PerformanceSnapshot.objects.filter(
            timestamp__gte=one_hour_ago
        ).values('layer', 'metric_name').annotate(
            avg_value=models.Avg('metric_value'),
            max_value=models.Max('metric_value'),
            count=models.Count('id')
        )
        
        # Get recent errors
        recent_errors = ErrorLog.objects.filter(
            timestamp__gte=one_hour_ago
        ).values('layer', 'severity').annotate(
            count=models.Count('id')
        )
        
        # Get trend summary
        trend_summary = self.trend_analyzer.get_trend_summary(hours=24)
        
        # Get optimization recommendations
        recommendations = self.optimization_engine.analyze_performance_issues(hours=24)
        high_priority_recommendations = [r for r in recommendations if r.priority == 'high']
        
        return {
            'timestamp': now.isoformat(),
            'overall_health': self._calculate_overall_health_score(recent_snapshots, recent_errors),
            'performance_metrics': {
                'total_metrics_collected': sum(s['count'] for s in recent_snapshots),
                'layers_monitored': len(set(s['layer'] for s in recent_snapshots)),
                'metrics_by_layer': {
                    layer: [s for s in recent_snapshots if s['layer'] == layer]
                    for layer in set(s['layer'] for s in recent_snapshots)
                }
            },
            'error_summary': {
                'total_errors': sum(e['count'] for e in recent_errors),
                'errors_by_layer': {
                    layer: sum(e['count'] for e in recent_errors if e['layer'] == layer)
                    for layer in set(e['layer'] for e in recent_errors)
                },
                'critical_errors': sum(e['count'] for e in recent_errors if e['severity'] == 'critical')
            },
            'trends': trend_summary,
            'recommendations': {
                'total_recommendations': len(recommendations),
                'high_priority_count': len(high_priority_recommendations),
                'top_recommendations': high_priority_recommendations[:5]
            }
        }
    
    def _calculate_overall_health_score(self, snapshots, errors) -> Dict[str, Any]:
        """Calculate overall system health score (0-100)"""
        score = 100
        issues = []
        
        # Penalize for high error rates
        total_errors = sum(e['count'] for e in errors)
        if total_errors > 10:
            penalty = min(30, total_errors * 2)
            score -= penalty
            issues.append(f"High error rate: {total_errors} errors in last hour")
        
        # Penalize for performance issues
        for snapshot in snapshots:
            if snapshot['metric_name'] == 'response_time' and snapshot['avg_value'] > 500:
                score -= 10
                issues.append(f"Slow response times in {snapshot['layer']}")
            elif snapshot['metric_name'] == 'cpu_usage' and snapshot['avg_value'] > 90:
                score -= 15
                issues.append("High CPU usage")
            elif snapshot['metric_name'] == 'memory_usage' and snapshot['avg_value'] > 90:
                score -= 15
                issues.append("High memory usage")
        
        # Determine health status
        if score >= 90:
            status = 'excellent'
        elif score >= 75:
            status = 'good'
        elif score >= 60:
            status = 'fair'
        elif score >= 40:
            status = 'poor'
        else:
            status = 'critical'
        
        return {
            'score': max(0, score),
            'status': status,
            'issues': issues
        }


# Global instance
_performance_monitoring_service = None


def get_performance_monitoring_service() -> PerformanceMonitoringService:
    """Get the global performance monitoring service instance"""
    global _performance_monitoring_service
    if _performance_monitoring_service is None:
        _performance_monitoring_service = PerformanceMonitoringService()
    return _performance_monitoring_service