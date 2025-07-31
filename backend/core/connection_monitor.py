"""
Connection monitoring and metrics collection for MySQL database optimization
"""
import logging
import threading
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Connection metrics data structure"""
    database_alias: str
    timestamp: datetime
    active_connections: int
    idle_connections: int
    total_connections: int
    queries_per_second: float
    average_query_time: float
    slow_queries: int
    failed_connections: int
    connection_errors: int
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_io: float
    replication_lag: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    duration_seconds: int = 60  # How long threshold must be exceeded
    enabled: bool = True


class ConnectionMonitor:
    """
    Advanced connection monitoring system with real-time metrics,
    alerting, and automatic recovery capabilities
    """
    
    def __init__(self, monitoring_interval: int = 30):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alert_thresholds = self._get_default_thresholds()
        self.alert_callbacks: List[Callable] = []
        self.monitoring_enabled = True
        self.recovery_enabled = True
        self._lock = threading.RLock()
        self._monitoring_thread = None
        
        # Performance tracking
        self.query_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.connection_pools = {}
        
        # Start monitoring
        self.start_monitoring()
    
    def _get_default_thresholds(self) -> Dict[str, AlertThreshold]:
        """Get default alert thresholds"""
        return {
            'connection_usage': AlertThreshold(
                metric_name='connection_usage',
                warning_threshold=80.0,
                critical_threshold=95.0,
                duration_seconds=60
            ),
            'query_response_time': AlertThreshold(
                metric_name='query_response_time',
                warning_threshold=2.0,
                critical_threshold=5.0,
                duration_seconds=30
            ),
            'slow_queries': AlertThreshold(
                metric_name='slow_queries',
                warning_threshold=10.0,
                critical_threshold=50.0,
                duration_seconds=60
            ),
            'replication_lag': AlertThreshold(
                metric_name='replication_lag',
                warning_threshold=5.0,
                critical_threshold=30.0,
                duration_seconds=30
            ),
            'failed_connections': AlertThreshold(
                metric_name='failed_connections',
                warning_threshold=5.0,
                critical_threshold=20.0,
                duration_seconds=60
            ),
            'cpu_usage': AlertThreshold(
                metric_name='cpu_usage',
                warning_threshold=80.0,
                critical_threshold=95.0,
                duration_seconds=120
            ),
            'memory_usage': AlertThreshold(
                metric_name='memory_usage',
                warning_threshold=85.0,
                critical_threshold=95.0,
                duration_seconds=120
            )
        }
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self.monitoring_enabled = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="ConnectionMonitor"
        )
        self._monitoring_thread.start()
        logger.info("Connection monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring_enabled = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("Connection monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_enabled:
            try:
                self._collect_metrics()
                self._check_alerts()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Short delay before retry
    
    def _collect_metrics(self):
        """Collect metrics from all configured databases"""
        for db_alias in settings.DATABASES.keys():
            try:
                metrics = self._collect_database_metrics(db_alias)
                if metrics:
                    with self._lock:
                        self.metrics_history[db_alias].append(metrics)
                    
                    # Cache latest metrics
                    cache.set(f"db_metrics_{db_alias}", metrics.to_dict(), 300)
                    
            except Exception as e:
                logger.error(f"Failed to collect metrics for {db_alias}: {e}")
    
    def _collect_database_metrics(self, db_alias: str) -> Optional[ConnectionMetrics]:
        """Collect metrics for a specific database"""
        try:
            connection = connections[db_alias]
            
            # Basic connection test
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                
                # MySQL specific metrics
                if 'mysql' in connection.settings_dict.get('ENGINE', ''):
                    return self._collect_mysql_metrics(cursor, db_alias)
                else:
                    # Generic metrics for other databases
                    return self._collect_generic_metrics(cursor, db_alias)
                    
        except OperationalError as e:
            logger.error(f"Database connection failed for {db_alias}: {e}")
            return self._create_error_metrics(db_alias, str(e))
        except Exception as e:
            logger.error(f"Unexpected error collecting metrics for {db_alias}: {e}")
            return None
    
    def _collect_mysql_metrics(self, cursor, db_alias: str) -> ConnectionMetrics:
        """Collect MySQL-specific metrics"""
        metrics_data = {}
        
        # Connection statistics
        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        result = cursor.fetchone()
        active_connections = int(result[1]) if result else 0
        
        cursor.execute("SHOW STATUS LIKE 'Max_used_connections'")
        result = cursor.fetchone()
        max_connections = int(result[1]) if result else 0
        
        cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
        result = cursor.fetchone()
        max_allowed = int(result[1]) if result else 0
        
        # Query statistics
        cursor.execute("SHOW STATUS LIKE 'Queries'")
        result = cursor.fetchone()
        total_queries = int(result[1]) if result else 0
        
        cursor.execute("SHOW STATUS LIKE 'Uptime'")
        result = cursor.fetchone()
        uptime = int(result[1]) if result else 1
        
        queries_per_second = total_queries / uptime if uptime > 0 else 0
        
        # Slow queries
        cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
        result = cursor.fetchone()
        slow_queries = int(result[1]) if result else 0
        
        # Connection errors
        cursor.execute("SHOW STATUS LIKE 'Connection_errors_internal'")
        result = cursor.fetchone()
        connection_errors = int(result[1]) if result else 0
        
        cursor.execute("SHOW STATUS LIKE 'Aborted_connects'")
        result = cursor.fetchone()
        failed_connections = int(result[1]) if result else 0
        
        # Replication lag (if slave)
        replication_lag = 0.0
        try:
            cursor.execute("SHOW SLAVE STATUS")
            slave_status = cursor.fetchone()
            if slave_status and len(slave_status) > 32:
                replication_lag = float(slave_status[32] or 0)
        except:
            pass  # Not a slave or no replication
        
        # Calculate average query time from recent queries
        recent_times = list(self.query_times[db_alias])
        avg_query_time = sum(recent_times) / len(recent_times) if recent_times else 0.0
        
        return ConnectionMetrics(
            database_alias=db_alias,
            timestamp=datetime.now(),
            active_connections=active_connections,
            idle_connections=max(0, max_connections - active_connections),
            total_connections=max_connections,
            queries_per_second=queries_per_second,
            average_query_time=avg_query_time,
            slow_queries=slow_queries,
            failed_connections=failed_connections,
            connection_errors=connection_errors,
            cpu_usage=0.0,  # Would need system-level monitoring
            memory_usage=0.0,  # Would need system-level monitoring
            disk_io=0.0,  # Would need system-level monitoring
            network_io=0.0,  # Would need system-level monitoring
            replication_lag=replication_lag
        )
    
    def _collect_generic_metrics(self, cursor, db_alias: str) -> ConnectionMetrics:
        """Collect generic database metrics"""
        # Basic metrics for non-MySQL databases
        recent_times = list(self.query_times[db_alias])
        avg_query_time = sum(recent_times) / len(recent_times) if recent_times else 0.0
        
        return ConnectionMetrics(
            database_alias=db_alias,
            timestamp=datetime.now(),
            active_connections=1,  # At least one (current)
            idle_connections=0,
            total_connections=1,
            queries_per_second=0.0,
            average_query_time=avg_query_time,
            slow_queries=0,
            failed_connections=0,
            connection_errors=0,
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_io=0.0,
            network_io=0.0,
            replication_lag=0.0
        )
    
    def _create_error_metrics(self, db_alias: str, error: str) -> ConnectionMetrics:
        """Create metrics object for database errors"""
        return ConnectionMetrics(
            database_alias=db_alias,
            timestamp=datetime.now(),
            active_connections=0,
            idle_connections=0,
            total_connections=0,
            queries_per_second=0.0,
            average_query_time=0.0,
            slow_queries=0,
            failed_connections=1,
            connection_errors=1,
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_io=0.0,
            network_io=0.0,
            replication_lag=0.0
        )
    
    def _check_alerts(self):
        """Check metrics against alert thresholds"""
        for db_alias, metrics_queue in self.metrics_history.items():
            if not metrics_queue:
                continue
            
            latest_metrics = metrics_queue[-1]
            
            for threshold_name, threshold in self.alert_thresholds.items():
                if not threshold.enabled:
                    continue
                
                self._check_metric_threshold(latest_metrics, threshold)
    
    def _check_metric_threshold(self, metrics: ConnectionMetrics, threshold: AlertThreshold):
        """Check a specific metric against its threshold"""
        metric_value = getattr(metrics, threshold.metric_name, 0)
        
        # Special handling for percentage metrics
        if threshold.metric_name == 'connection_usage':
            if metrics.total_connections > 0:
                metric_value = (metrics.active_connections / metrics.total_connections) * 100
            else:
                metric_value = 0
        
        # Check thresholds
        alert_level = None
        if metric_value >= threshold.critical_threshold:
            alert_level = 'critical'
        elif metric_value >= threshold.warning_threshold:
            alert_level = 'warning'
        
        if alert_level:
            self._trigger_alert(metrics.database_alias, threshold.metric_name, 
                             metric_value, alert_level, threshold)
    
    def _trigger_alert(self, db_alias: str, metric_name: str, value: float, 
                      level: str, threshold: AlertThreshold):
        """Trigger an alert and attempt recovery if enabled"""
        alert_data = {
            'database': db_alias,
            'metric': metric_name,
            'value': value,
            'level': level,
            'threshold': threshold.warning_threshold if level == 'warning' else threshold.critical_threshold,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.warning(f"Database alert [{level.upper()}]: {db_alias} - {metric_name} = {value}")
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        # Attempt automatic recovery for critical alerts
        if level == 'critical' and self.recovery_enabled:
            self._attempt_recovery(db_alias, metric_name, value)
    
    def _attempt_recovery(self, db_alias: str, metric_name: str, value: float):
        """Attempt automatic recovery for critical issues"""
        logger.info(f"Attempting recovery for {db_alias} - {metric_name}")
        
        try:
            if metric_name == 'connection_usage':
                self._recover_connection_exhaustion(db_alias)
            elif metric_name == 'slow_queries':
                self._recover_slow_queries(db_alias)
            elif metric_name == 'replication_lag':
                self._recover_replication_lag(db_alias)
            elif metric_name == 'failed_connections':
                self._recover_failed_connections(db_alias)
                
        except Exception as e:
            logger.error(f"Recovery attempt failed for {db_alias}: {e}")
    
    def _recover_connection_exhaustion(self, db_alias: str):
        """Recover from connection pool exhaustion"""
        # Close old connections
        connection = connections[db_alias]
        connection.close()
        
        # Force connection pool reset
        if hasattr(connection, 'pool'):
            connection.pool.clear()
        
        logger.info(f"Reset connection pool for {db_alias}")
    
    def _recover_slow_queries(self, db_alias: str):
        """Recover from slow query issues"""
        # Kill long-running queries (MySQL specific)
        try:
            connection = connections[db_alias]
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT ID FROM INFORMATION_SCHEMA.PROCESSLIST 
                    WHERE COMMAND != 'Sleep' AND TIME > 30
                """)
                
                long_queries = cursor.fetchall()
                for query_id in long_queries[:5]:  # Kill max 5 queries
                    try:
                        cursor.execute(f"KILL {query_id[0]}")
                        logger.info(f"Killed long-running query {query_id[0]}")
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Failed to kill slow queries: {e}")
    
    def _recover_replication_lag(self, db_alias: str):
        """Recover from replication lag issues"""
        # Log the issue for manual intervention
        logger.critical(f"High replication lag detected on {db_alias} - manual intervention may be required")
    
    def _recover_failed_connections(self, db_alias: str):
        """Recover from connection failures"""
        # Reset connection
        connection = connections[db_alias]
        connection.close()
        
        # Test new connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            logger.info(f"Successfully recovered connection for {db_alias}")
        except Exception as e:
            logger.error(f"Failed to recover connection for {db_alias}: {e}")
    
    def record_query_time(self, db_alias: str, query_time: float):
        """Record query execution time for metrics"""
        with self._lock:
            self.query_times[db_alias].append(query_time)
    
    def get_current_metrics(self, db_alias: str = None) -> Dict[str, Any]:
        """Get current metrics for specified database or all databases"""
        if db_alias:
            cached_metrics = cache.get(f"db_metrics_{db_alias}")
            return {db_alias: cached_metrics} if cached_metrics else {}
        
        # Get all databases
        all_metrics = {}
        for db_alias in settings.DATABASES.keys():
            cached_metrics = cache.get(f"db_metrics_{db_alias}")
            if cached_metrics:
                all_metrics[db_alias] = cached_metrics
        
        return all_metrics
    
    def get_metrics_history(self, db_alias: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics for a database"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            if db_alias not in self.metrics_history:
                return []
            
            history = []
            for metrics in self.metrics_history[db_alias]:
                if metrics.timestamp >= cutoff_time:
                    history.append(metrics.to_dict())
            
            return history
    
    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def update_threshold(self, metric_name: str, warning: float = None, 
                        critical: float = None, enabled: bool = None):
        """Update alert threshold configuration"""
        if metric_name in self.alert_thresholds:
            threshold = self.alert_thresholds[metric_name]
            if warning is not None:
                threshold.warning_threshold = warning
            if critical is not None:
                threshold.critical_threshold = critical
            if enabled is not None:
                threshold.enabled = enabled
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of all databases"""
        summary = {
            'overall_status': 'healthy',
            'databases': {},
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for db_alias in settings.DATABASES.keys():
            metrics = cache.get(f"db_metrics_{db_alias}")
            if metrics:
                db_status = 'healthy'
                
                # Check for critical issues
                if metrics.get('failed_connections', 0) > 0:
                    db_status = 'critical'
                elif metrics.get('connection_errors', 0) > 5:
                    db_status = 'warning'
                elif metrics.get('replication_lag', 0) > 10:
                    db_status = 'warning'
                
                summary['databases'][db_alias] = {
                    'status': db_status,
                    'active_connections': metrics.get('active_connections', 0),
                    'queries_per_second': metrics.get('queries_per_second', 0),
                    'average_query_time': metrics.get('average_query_time', 0),
                    'replication_lag': metrics.get('replication_lag', 0)
                }
                
                if db_status != 'healthy':
                    summary['overall_status'] = 'degraded'
            else:
                summary['databases'][db_alias] = {'status': 'unknown'}
                summary['overall_status'] = 'degraded'
        
        return summary


# Global monitor instance
_connection_monitor = None


def get_connection_monitor() -> ConnectionMonitor:
    """Get the global connection monitor instance"""
    global _connection_monitor
    if _connection_monitor is None:
        _connection_monitor = ConnectionMonitor()
    return _connection_monitor


def initialize_monitoring(monitoring_interval: int = 30) -> ConnectionMonitor:
    """Initialize connection monitoring with custom interval"""
    global _connection_monitor
    if _connection_monitor:
        _connection_monitor.stop_monitoring()
    
    _connection_monitor = ConnectionMonitor(monitoring_interval)
    return _connection_monitor