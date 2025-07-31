"""
Comprehensive Database Monitoring and Alerting System for MySQL Integration

This module provides advanced database monitoring capabilities including:
- Real-time performance metrics collection
- Slow query analysis and optimization recommendations
- Replication monitoring and lag detection
- Intelligent alerting system with automatic recovery
- Health checks and capacity planning
"""

import logging
import threading
import time
import json
import smtplib
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.core.cache import cache
from django.core.mail import send_mail
from django.db import connections, connection
from django.db.utils import OperationalError, DatabaseError
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class DatabaseMetrics:
    """Comprehensive database metrics data structure"""
    database_alias: str
    timestamp: datetime
    
    # Connection metrics
    active_connections: int
    idle_connections: int
    total_connections: int
    max_connections: int
    connection_usage_percent: float
    failed_connections: int
    connection_errors: int
    
    # Query performance metrics
    queries_per_second: float
    average_query_time: float
    slow_queries: int
    slow_query_rate: float
    total_queries: int
    
    # Replication metrics
    replication_lag: float
    replication_status: str
    slave_io_running: bool
    slave_sql_running: bool
    
    # System resource metrics
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    disk_io_read: float
    disk_io_write: float
    network_io: float
    
    # MySQL specific metrics
    innodb_buffer_pool_hit_rate: float
    innodb_buffer_pool_usage: float
    table_locks_waited: int
    thread_cache_hit_rate: float
    query_cache_hit_rate: float
    
    # Health indicators
    health_score: float
    status: str  # healthy, warning, critical
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class SlowQuery:
    """Slow query analysis data structure"""
    query_hash: str
    query_text: str
    execution_time: float
    lock_time: float
    rows_sent: int
    rows_examined: int
    timestamp: datetime
    database: str
    user: str
    host: str
    
    # Analysis results
    optimization_suggestions: List[str]
    severity: str  # low, medium, high, critical
    frequency: int
    
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
    duration_seconds: int = 60
    enabled: bool = True
    alert_frequency: int = 300  # Minimum seconds between alerts
    escalation_threshold: int = 3  # Number of consecutive alerts before escalation


@dataclass
class Alert:
    """Database alert data structure"""
    alert_id: str
    database_alias: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str  # warning, critical
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    escalated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if data['resolution_time']:
            data['resolution_time'] = self.resolution_time.isoformat()
        return data


class SlowQueryAnalyzer:
    """Advanced slow query analysis and optimization recommendations"""
    
    def __init__(self):
        self.query_patterns = {}
        self.optimization_rules = self._load_optimization_rules()
    
    def _load_optimization_rules(self) -> Dict[str, List[str]]:
        """Load query optimization rules"""
        return {
            'missing_index': [
                "Consider adding an index on frequently queried columns",
                "Use EXPLAIN to analyze query execution plan",
                "Check for table scans in WHERE clauses"
            ],
            'inefficient_join': [
                "Optimize JOIN conditions with proper indexing",
                "Consider using EXISTS instead of IN for subqueries",
                "Ensure JOIN columns have matching data types"
            ],
            'large_result_set': [
                "Add LIMIT clause to reduce result set size",
                "Consider pagination for large datasets",
                "Use appropriate WHERE conditions to filter results"
            ],
            'subquery_optimization': [
                "Convert correlated subqueries to JOINs where possible",
                "Use EXISTS instead of IN for better performance",
                "Consider using temporary tables for complex subqueries"
            ],
            'function_in_where': [
                "Avoid using functions in WHERE clauses",
                "Create functional indexes if functions are necessary",
                "Rewrite queries to use sargable predicates"
            ]
        }
    
    def analyze_slow_query(self, query_text: str, execution_time: float, 
                          rows_examined: int, rows_sent: int) -> SlowQuery:
        """Analyze a slow query and provide optimization suggestions"""
        query_hash = self._generate_query_hash(query_text)
        suggestions = []
        severity = self._calculate_severity(execution_time, rows_examined, rows_sent)
        
        # Analyze query patterns
        if self._has_missing_index_pattern(query_text):
            suggestions.extend(self.optimization_rules['missing_index'])
        
        if self._has_inefficient_join_pattern(query_text):
            suggestions.extend(self.optimization_rules['inefficient_join'])
        
        if rows_examined > 10000:
            suggestions.extend(self.optimization_rules['large_result_set'])
        
        if self._has_subquery_pattern(query_text):
            suggestions.extend(self.optimization_rules['subquery_optimization'])
        
        if self._has_function_in_where_pattern(query_text):
            suggestions.extend(self.optimization_rules['function_in_where'])
        
        # Track query frequency
        frequency = self.query_patterns.get(query_hash, 0) + 1
        self.query_patterns[query_hash] = frequency
        
        return SlowQuery(
            query_hash=query_hash,
            query_text=query_text[:1000],  # Truncate for storage
            execution_time=execution_time,
            lock_time=0.0,  # Would need to be extracted from slow log
            rows_sent=rows_sent,
            rows_examined=rows_examined,
            timestamp=datetime.now(),
            database='',  # Would be set by caller
            user='',  # Would be set by caller
            host='',  # Would be set by caller
            optimization_suggestions=list(set(suggestions)),  # Remove duplicates
            severity=severity,
            frequency=frequency
        )
    
    def _generate_query_hash(self, query_text: str) -> str:
        """Generate a hash for query pattern matching"""
        import hashlib
        # Normalize query by removing literals and whitespace
        normalized = ' '.join(query_text.upper().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _calculate_severity(self, execution_time: float, rows_examined: int, rows_sent: int) -> str:
        """Calculate query severity based on metrics"""
        if execution_time > 10 or rows_examined > 100000:
            return 'critical'
        elif execution_time > 5 or rows_examined > 50000:
            return 'high'
        elif execution_time > 2 or rows_examined > 10000:
            return 'medium'
        else:
            return 'low'
    
    def _has_missing_index_pattern(self, query: str) -> bool:
        """Check if query might benefit from indexing"""
        query_upper = query.upper()
        return ('WHERE' in query_upper and 
                ('LIKE' in query_upper or '=' in query_upper or '>' in query_upper or '<' in query_upper))
    
    def _has_inefficient_join_pattern(self, query: str) -> bool:
        """Check for potentially inefficient JOIN patterns"""
        query_upper = query.upper()
        return 'JOIN' in query_upper and ('ON' not in query_upper or 'WHERE' not in query_upper)
    
    def _has_subquery_pattern(self, query: str) -> bool:
        """Check for subquery patterns"""
        query_upper = query.upper()
        return 'IN (' in query_upper and 'SELECT' in query_upper
    
    def _has_function_in_where_pattern(self, query: str) -> bool:
        """Check for functions in WHERE clauses"""
        query_upper = query.upper()
        functions = ['UPPER(', 'LOWER(', 'SUBSTRING(', 'DATE(', 'YEAR(', 'MONTH(']
        return 'WHERE' in query_upper and any(func in query_upper for func in functions)


class DatabaseMonitor:
    """
    Comprehensive database monitoring system with real-time metrics,
    intelligent alerting, and automatic recovery capabilities
    """
    
    def __init__(self, monitoring_interval: int = 30):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=2000))
        self.slow_queries: deque = deque(maxlen=1000)
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        
        # Components
        self.slow_query_analyzer = SlowQueryAnalyzer()
        self.alert_thresholds = self._get_default_thresholds()
        self.alert_callbacks: List[Callable] = []
        
        # Configuration
        self.monitoring_enabled = True
        self.recovery_enabled = True
        self.alerting_enabled = True
        
        # Threading
        self._lock = threading.RLock()
        self._monitoring_thread = None
        self._alert_thread = None
        
        # Performance tracking
        self.query_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Start monitoring
        self.start_monitoring()
    
    def _get_default_thresholds(self) -> Dict[str, AlertThreshold]:
        """Get default alert thresholds from settings or defaults"""
        return {
            'connection_usage': AlertThreshold(
                metric_name='connection_usage',
                warning_threshold=getattr(settings, 'DB_ALERT_CONNECTION_WARNING', 80.0),
                critical_threshold=getattr(settings, 'DB_ALERT_CONNECTION_CRITICAL', 95.0),
                duration_seconds=60
            ),
            'query_response_time': AlertThreshold(
                metric_name='query_response_time',
                warning_threshold=getattr(settings, 'DB_ALERT_QUERY_TIME_WARNING', 2.0),
                critical_threshold=getattr(settings, 'DB_ALERT_QUERY_TIME_CRITICAL', 5.0),
                duration_seconds=30
            ),
            'slow_queries': AlertThreshold(
                metric_name='slow_queries',
                warning_threshold=getattr(settings, 'DB_ALERT_SLOW_QUERIES_WARNING', 10.0),
                critical_threshold=getattr(settings, 'DB_ALERT_SLOW_QUERIES_CRITICAL', 50.0),
                duration_seconds=60
            ),
            'replication_lag': AlertThreshold(
                metric_name='replication_lag',
                warning_threshold=getattr(settings, 'DB_ALERT_REPLICATION_WARNING', 5.0),
                critical_threshold=getattr(settings, 'DB_ALERT_REPLICATION_CRITICAL', 30.0),
                duration_seconds=30
            ),
            'cpu_usage': AlertThreshold(
                metric_name='cpu_usage',
                warning_threshold=getattr(settings, 'DB_ALERT_CPU_WARNING', 80.0),
                critical_threshold=getattr(settings, 'DB_ALERT_CPU_CRITICAL', 95.0),
                duration_seconds=120
            ),
            'memory_usage': AlertThreshold(
                metric_name='memory_usage',
                warning_threshold=getattr(settings, 'DB_ALERT_MEMORY_WARNING', 85.0),
                critical_threshold=getattr(settings, 'DB_ALERT_MEMORY_CRITICAL', 95.0),
                duration_seconds=120
            ),
            'disk_usage': AlertThreshold(
                metric_name='disk_usage',
                warning_threshold=getattr(settings, 'DB_ALERT_DISK_WARNING', 85.0),
                critical_threshold=getattr(settings, 'DB_ALERT_DISK_CRITICAL', 95.0),
                duration_seconds=300
            ),
            'health_score': AlertThreshold(
                metric_name='health_score',
                warning_threshold=getattr(settings, 'DB_ALERT_HEALTH_WARNING', 70.0),
                critical_threshold=getattr(settings, 'DB_ALERT_HEALTH_CRITICAL', 50.0),
                duration_seconds=60
            )
        }
    
    def start_monitoring(self):
        """Start the monitoring threads"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self.monitoring_enabled = True
        
        # Start metrics collection thread
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="DatabaseMonitor"
        )
        self._monitoring_thread.start()
        
        # Start alerting thread
        self._alert_thread = threading.Thread(
            target=self._alert_loop,
            daemon=True,
            name="DatabaseAlerting"
        )
        self._alert_thread.start()
        
        logger.info("Database monitoring and alerting started")
    
    def stop_monitoring(self):
        """Stop the monitoring threads"""
        self.monitoring_enabled = False
        
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        
        if self._alert_thread:
            self._alert_thread.join(timeout=5)
        
        logger.info("Database monitoring and alerting stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop for metrics collection"""
        while self.monitoring_enabled:
            try:
                self._collect_all_metrics()
                self._analyze_slow_queries()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Short delay before retry
    
    def _alert_loop(self):
        """Separate loop for alert processing"""
        while self.monitoring_enabled:
            try:
                if self.alerting_enabled:
                    self._check_all_alerts()
                    self._cleanup_resolved_alerts()
                time.sleep(10)  # Check alerts more frequently
            except Exception as e:
                logger.error(f"Error in alert loop: {e}")
                time.sleep(5)
    
    def _collect_all_metrics(self):
        """Collect metrics from all configured databases"""
        for db_alias in settings.DATABASES.keys():
            try:
                metrics = self._collect_database_metrics(db_alias)
                if metrics:
                    with self._lock:
                        self.metrics_history[db_alias].append(metrics)
                    
                    # Cache latest metrics
                    cache.set(f"db_metrics_{db_alias}", metrics.to_dict(), 300)
                    
                    # Log metrics for external monitoring systems
                    self._log_metrics(metrics)
                    
            except Exception as e:
                logger.error(f"Failed to collect metrics for {db_alias}: {e}")
    
    def _collect_database_metrics(self, db_alias: str) -> Optional[DatabaseMetrics]:
        """Collect comprehensive metrics for a specific database"""
        try:
            db_connection = connections[db_alias]
            
            with db_connection.cursor() as cursor:
                # Test connection
                cursor.execute("SELECT 1")
                
                # Collect MySQL-specific metrics
                if 'mysql' in db_connection.settings_dict.get('ENGINE', ''):
                    return self._collect_mysql_metrics(cursor, db_alias)
                else:
                    return self._collect_generic_metrics(cursor, db_alias)
                    
        except (OperationalError, DatabaseError) as e:
            logger.error(f"Database connection failed for {db_alias}: {e}")
            return self._create_error_metrics(db_alias, str(e))
        except Exception as e:
            logger.error(f"Unexpected error collecting metrics for {db_alias}: {e}")
            return None
    
    def _collect_mysql_metrics(self, cursor, db_alias: str) -> DatabaseMetrics:
        """Collect comprehensive MySQL-specific metrics"""
        metrics_data = {}
        
        # Connection metrics
        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        active_connections = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Max_used_connections'")
        max_used_connections = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
        max_connections = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Connection_errors_internal'")
        connection_errors = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Aborted_connects'")
        failed_connections = int(cursor.fetchone()[1])
        
        # Query performance metrics
        cursor.execute("SHOW STATUS LIKE 'Queries'")
        total_queries = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Uptime'")
        uptime = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
        slow_queries = int(cursor.fetchone()[1])
        
        queries_per_second = total_queries / uptime if uptime > 0 else 0
        slow_query_rate = (slow_queries / total_queries * 100) if total_queries > 0 else 0
        
        # InnoDB metrics
        cursor.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests'")
        buffer_pool_reads = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_reads'")
        buffer_pool_disk_reads = int(cursor.fetchone()[1])
        
        buffer_pool_hit_rate = ((buffer_pool_reads - buffer_pool_disk_reads) / buffer_pool_reads * 100) if buffer_pool_reads > 0 else 0
        
        cursor.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_pages_total'")
        buffer_pool_total = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Innodb_buffer_pool_pages_free'")
        buffer_pool_free = int(cursor.fetchone()[1])
        
        buffer_pool_usage = ((buffer_pool_total - buffer_pool_free) / buffer_pool_total * 100) if buffer_pool_total > 0 else 0
        
        # Thread cache metrics
        cursor.execute("SHOW STATUS LIKE 'Threads_created'")
        threads_created = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Connections'")
        total_connections = int(cursor.fetchone()[1])
        
        thread_cache_hit_rate = ((total_connections - threads_created) / total_connections * 100) if total_connections > 0 else 0
        
        # Query cache metrics
        cursor.execute("SHOW STATUS LIKE 'Qcache_hits'")
        qcache_hits = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Com_select'")
        com_select = int(cursor.fetchone()[1])
        
        query_cache_hit_rate = (qcache_hits / (qcache_hits + com_select) * 100) if (qcache_hits + com_select) > 0 else 0
        
        # Table locks
        cursor.execute("SHOW STATUS LIKE 'Table_locks_waited'")
        table_locks_waited = int(cursor.fetchone()[1])
        
        # Replication metrics
        replication_lag, replication_status, slave_io_running, slave_sql_running = self._get_replication_metrics(cursor)
        
        # System metrics
        cpu_usage, memory_usage, disk_usage, disk_io_read, disk_io_write, network_io = self._get_system_metrics()
        
        # Calculate connection usage percentage
        connection_usage_percent = (active_connections / max_connections * 100) if max_connections > 0 else 0
        
        # Calculate average query time from recent queries
        recent_times = list(self.query_times[db_alias])
        average_query_time = sum(recent_times) / len(recent_times) if recent_times else 0.0
        
        # Calculate health score
        health_score = self._calculate_health_score(
            connection_usage_percent, average_query_time, slow_query_rate,
            replication_lag, cpu_usage, memory_usage, disk_usage,
            buffer_pool_hit_rate, thread_cache_hit_rate
        )
        
        # Determine status
        status = self._determine_status(health_score, connection_usage_percent, replication_lag)
        
        return DatabaseMetrics(
            database_alias=db_alias,
            timestamp=datetime.now(),
            active_connections=active_connections,
            idle_connections=max(0, max_used_connections - active_connections),
            total_connections=max_used_connections,
            max_connections=max_connections,
            connection_usage_percent=connection_usage_percent,
            failed_connections=failed_connections,
            connection_errors=connection_errors,
            queries_per_second=queries_per_second,
            average_query_time=average_query_time,
            slow_queries=slow_queries,
            slow_query_rate=slow_query_rate,
            total_queries=total_queries,
            replication_lag=replication_lag,
            replication_status=replication_status,
            slave_io_running=slave_io_running,
            slave_sql_running=slave_sql_running,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            network_io=network_io,
            innodb_buffer_pool_hit_rate=buffer_pool_hit_rate,
            innodb_buffer_pool_usage=buffer_pool_usage,
            table_locks_waited=table_locks_waited,
            thread_cache_hit_rate=thread_cache_hit_rate,
            query_cache_hit_rate=query_cache_hit_rate,
            health_score=health_score,
            status=status
        )    

    def _collect_generic_metrics(self, cursor, db_alias: str) -> DatabaseMetrics:
        """Collect generic database metrics for non-MySQL databases"""
        recent_times = list(self.query_times[db_alias])
        average_query_time = sum(recent_times) / len(recent_times) if recent_times else 0.0
        
        # System metrics
        cpu_usage, memory_usage, disk_usage, disk_io_read, disk_io_write, network_io = self._get_system_metrics()
        
        # Basic health score for non-MySQL databases
        health_score = max(0, 100 - cpu_usage - memory_usage/2 - disk_usage/2)
        status = 'healthy' if health_score > 70 else 'warning' if health_score > 50 else 'critical'
        
        return DatabaseMetrics(
            database_alias=db_alias,
            timestamp=datetime.now(),
            active_connections=1,
            idle_connections=0,
            total_connections=1,
            max_connections=100,  # Default assumption
            connection_usage_percent=1.0,
            failed_connections=0,
            connection_errors=0,
            queries_per_second=0.0,
            average_query_time=average_query_time,
            slow_queries=0,
            slow_query_rate=0.0,
            total_queries=0,
            replication_lag=0.0,
            replication_status='N/A',
            slave_io_running=False,
            slave_sql_running=False,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            network_io=network_io,
            innodb_buffer_pool_hit_rate=0.0,
            innodb_buffer_pool_usage=0.0,
            table_locks_waited=0,
            thread_cache_hit_rate=0.0,
            query_cache_hit_rate=0.0,
            health_score=health_score,
            status=status
        )
    
    def _create_error_metrics(self, db_alias: str, error: str) -> DatabaseMetrics:
        """Create metrics object for database errors"""
        cpu_usage, memory_usage, disk_usage, disk_io_read, disk_io_write, network_io = self._get_system_metrics()
        
        return DatabaseMetrics(
            database_alias=db_alias,
            timestamp=datetime.now(),
            active_connections=0,
            idle_connections=0,
            total_connections=0,
            max_connections=0,
            connection_usage_percent=0.0,
            failed_connections=1,
            connection_errors=1,
            queries_per_second=0.0,
            average_query_time=0.0,
            slow_queries=0,
            slow_query_rate=0.0,
            total_queries=0,
            replication_lag=0.0,
            replication_status='ERROR',
            slave_io_running=False,
            slave_sql_running=False,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            disk_io_read=disk_io_read,
            disk_io_write=disk_io_write,
            network_io=network_io,
            innodb_buffer_pool_hit_rate=0.0,
            innodb_buffer_pool_usage=0.0,
            table_locks_waited=0,
            thread_cache_hit_rate=0.0,
            query_cache_hit_rate=0.0,
            health_score=0.0,
            status='critical'
        )
    
    def _get_replication_metrics(self, cursor) -> Tuple[float, str, bool, bool]:
        """Get MySQL replication metrics"""
        try:
            cursor.execute("SHOW SLAVE STATUS")
            slave_status = cursor.fetchone()
            
            if slave_status:
                # Parse slave status (column positions may vary by MySQL version)
                slave_io_running = slave_status[10] == 'Yes' if len(slave_status) > 10 else False
                slave_sql_running = slave_status[11] == 'Yes' if len(slave_status) > 11 else False
                seconds_behind_master = slave_status[32] if len(slave_status) > 32 and slave_status[32] is not None else 0
                
                replication_lag = float(seconds_behind_master)
                
                if slave_io_running and slave_sql_running:
                    replication_status = 'Running'
                elif not slave_io_running and not slave_sql_running:
                    replication_status = 'Stopped'
                else:
                    replication_status = 'Partial'
                
                return replication_lag, replication_status, slave_io_running, slave_sql_running
            else:
                return 0.0, 'Master', False, False
                
        except Exception as e:
            logger.debug(f"Could not get replication status: {e}")
            return 0.0, 'Unknown', False, False
    
    def _get_system_metrics(self) -> Tuple[float, float, float, float, float, float]:
        """Get system-level metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_read = disk_io.read_bytes / (1024 * 1024) if disk_io else 0  # MB
            disk_io_write = disk_io.write_bytes / (1024 * 1024) if disk_io else 0  # MB
            
            # Network I/O
            network_io_counters = psutil.net_io_counters()
            network_io = (network_io_counters.bytes_sent + network_io_counters.bytes_recv) / (1024 * 1024) if network_io_counters else 0  # MB
            
            return cpu_usage, memory_usage, disk_usage, disk_io_read, disk_io_write, network_io
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    
    def _calculate_health_score(self, connection_usage: float, avg_query_time: float,
                               slow_query_rate: float, replication_lag: float,
                               cpu_usage: float, memory_usage: float, disk_usage: float,
                               buffer_pool_hit_rate: float, thread_cache_hit_rate: float) -> float:
        """Calculate overall database health score (0-100)"""
        score = 100.0
        
        # Connection usage penalty
        if connection_usage > 90:
            score -= 20
        elif connection_usage > 80:
            score -= 10
        elif connection_usage > 70:
            score -= 5
        
        # Query performance penalty
        if avg_query_time > 5:
            score -= 15
        elif avg_query_time > 2:
            score -= 8
        elif avg_query_time > 1:
            score -= 3
        
        # Slow query penalty
        if slow_query_rate > 10:
            score -= 15
        elif slow_query_rate > 5:
            score -= 8
        elif slow_query_rate > 2:
            score -= 3
        
        # Replication lag penalty
        if replication_lag > 30:
            score -= 20
        elif replication_lag > 10:
            score -= 10
        elif replication_lag > 5:
            score -= 5
        
        # System resource penalties
        if cpu_usage > 95:
            score -= 15
        elif cpu_usage > 80:
            score -= 8
        
        if memory_usage > 95:
            score -= 15
        elif memory_usage > 85:
            score -= 8
        
        if disk_usage > 95:
            score -= 10
        elif disk_usage > 85:
            score -= 5
        
        # Buffer pool efficiency bonus/penalty
        if buffer_pool_hit_rate < 95:
            score -= (95 - buffer_pool_hit_rate) * 0.2
        
        # Thread cache efficiency
        if thread_cache_hit_rate < 90:
            score -= (90 - thread_cache_hit_rate) * 0.1
        
        return max(0.0, min(100.0, score))
    
    def _determine_status(self, health_score: float, connection_usage: float, replication_lag: float) -> str:
        """Determine overall database status"""
        if health_score < 50 or connection_usage > 95 or replication_lag > 60:
            return 'critical'
        elif health_score < 70 or connection_usage > 80 or replication_lag > 10:
            return 'warning'
        else:
            return 'healthy'
    
    def _log_metrics(self, metrics: DatabaseMetrics):
        """Log metrics for external monitoring systems"""
        logger.info(
            f"DB Metrics [{metrics.database_alias}]: "
            f"Health={metrics.health_score:.1f}, "
            f"Connections={metrics.active_connections}/{metrics.max_connections}, "
            f"QPS={metrics.queries_per_second:.1f}, "
            f"AvgQueryTime={metrics.average_query_time:.3f}s, "
            f"SlowQueries={metrics.slow_queries}, "
            f"RepLag={metrics.replication_lag:.1f}s"
        )
    
    def _analyze_slow_queries(self):
        """Analyze slow queries from MySQL slow query log"""
        try:
            for db_alias in settings.DATABASES.keys():
                if 'mysql' not in settings.DATABASES[db_alias].get('ENGINE', ''):
                    continue
                
                slow_queries = self._parse_slow_query_log(db_alias)
                for slow_query in slow_queries:
                    analyzed_query = self.slow_query_analyzer.analyze_slow_query(
                        slow_query['query_text'],
                        slow_query['execution_time'],
                        slow_query['rows_examined'],
                        slow_query['rows_sent']
                    )
                    analyzed_query.database = db_alias
                    
                    with self._lock:
                        self.slow_queries.append(analyzed_query)
                    
                    # Cache for API access
                    cache.set(f"slow_queries_{db_alias}", 
                             [sq.to_dict() for sq in list(self.slow_queries)[-50:]], 300)
                    
        except Exception as e:
            logger.error(f"Error analyzing slow queries: {e}")
    
    def _parse_slow_query_log(self, db_alias: str) -> List[Dict[str, Any]]:
        """Parse MySQL slow query log (simplified implementation)"""
        # In a real implementation, this would parse the actual slow query log file
        # For now, we'll simulate with recent slow queries from performance_schema
        try:
            db_connection = connections[db_alias]
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        DIGEST_TEXT as query_text,
                        AVG_TIMER_WAIT/1000000000 as execution_time,
                        SUM_ROWS_EXAMINED as rows_examined,
                        SUM_ROWS_SENT as rows_sent
                    FROM performance_schema.events_statements_summary_by_digest 
                    WHERE AVG_TIMER_WAIT/1000000000 > 1
                    ORDER BY AVG_TIMER_WAIT DESC 
                    LIMIT 10
                """)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'query_text': row[0] or '',
                        'execution_time': float(row[1] or 0),
                        'rows_examined': int(row[2] or 0),
                        'rows_sent': int(row[3] or 0)
                    })
                
                return results
                
        except Exception as e:
            logger.debug(f"Could not parse slow query log for {db_alias}: {e}")
            return []
    
    def _check_all_alerts(self):
        """Check all metrics against alert thresholds"""
        for db_alias, metrics_queue in self.metrics_history.items():
            if not metrics_queue:
                continue
            
            latest_metrics = metrics_queue[-1]
            
            for threshold_name, threshold in self.alert_thresholds.items():
                if not threshold.enabled:
                    continue
                
                self._check_metric_threshold(latest_metrics, threshold)
    
    def _check_metric_threshold(self, metrics: DatabaseMetrics, threshold: AlertThreshold):
        """Check a specific metric against its threshold"""
        metric_value = getattr(metrics, threshold.metric_name, 0)
        
        # Determine alert level
        alert_level = None
        threshold_value = 0
        
        if metric_value >= threshold.critical_threshold:
            alert_level = 'critical'
            threshold_value = threshold.critical_threshold
        elif metric_value >= threshold.warning_threshold:
            alert_level = 'warning'
            threshold_value = threshold.warning_threshold
        
        alert_key = f"{metrics.database_alias}_{threshold.metric_name}"
        
        if alert_level:
            # Check if we should suppress this alert due to frequency limits
            if self._should_suppress_alert(alert_key, threshold):
                return
            
            # Create or update alert
            if alert_key not in self.active_alerts:
                alert = Alert(
                    alert_id=f"{alert_key}_{int(time.time())}",
                    database_alias=metrics.database_alias,
                    metric_name=threshold.metric_name,
                    current_value=metric_value,
                    threshold_value=threshold_value,
                    severity=alert_level,
                    message=self._generate_alert_message(metrics, threshold.metric_name, metric_value, alert_level),
                    timestamp=datetime.now()
                )
                
                self.active_alerts[alert_key] = alert
                self.alert_history.append(alert)
                self.last_alert_times[alert_key] = datetime.now()
                
                # Trigger alert actions
                self._trigger_alert(alert)
                
                # Attempt recovery for critical alerts
                if alert_level == 'critical' and self.recovery_enabled:
                    self._attempt_recovery(metrics.database_alias, threshold.metric_name, metric_value)
            
        else:
            # Resolve existing alert if metric is back to normal
            if alert_key in self.active_alerts:
                alert = self.active_alerts[alert_key]
                alert.resolved = True
                alert.resolution_time = datetime.now()
                
                logger.info(f"Alert resolved: {alert.message}")
                del self.active_alerts[alert_key]
    
    def _should_suppress_alert(self, alert_key: str, threshold: AlertThreshold) -> bool:
        """Check if alert should be suppressed due to frequency limits"""
        if alert_key not in self.last_alert_times:
            return False
        
        time_since_last = datetime.now() - self.last_alert_times[alert_key]
        return time_since_last.total_seconds() < threshold.alert_frequency
    
    def _generate_alert_message(self, metrics: DatabaseMetrics, metric_name: str, 
                               value: float, level: str) -> str:
        """Generate human-readable alert message"""
        messages = {
            'connection_usage': f"High connection usage: {value:.1f}% of max connections",
            'query_response_time': f"Slow query response time: {value:.2f}s average",
            'slow_queries': f"High slow query rate: {value:.1f}% of queries",
            'replication_lag': f"High replication lag: {value:.1f} seconds behind master",
            'cpu_usage': f"High CPU usage: {value:.1f}%",
            'memory_usage': f"High memory usage: {value:.1f}%",
            'disk_usage': f"High disk usage: {value:.1f}%",
            'health_score': f"Low database health score: {value:.1f}/100"
        }
        
        base_message = messages.get(metric_name, f"Alert for {metric_name}: {value}")
        return f"[{level.upper()}] {metrics.database_alias}: {base_message}"
    
    def _trigger_alert(self, alert: Alert):
        """Trigger alert notifications"""
        logger.warning(f"Database Alert: {alert.message}")
        
        # Call registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert.to_dict())
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        # Send email alerts if configured
        self._send_email_alert(alert)
        
        # Store alert in cache for API access
        cache.set(f"latest_alert_{alert.database_alias}", alert.to_dict(), 3600)
    
    def _send_email_alert(self, alert: Alert):
        """Send email alert if configured"""
        try:
            recipients = getattr(settings, 'DB_ALERT_EMAIL_RECIPIENTS', [])
            if not recipients:
                return
            
            subject = f"Database Alert: {alert.database_alias} - {alert.severity.upper()}"
            message = f"""
Database Alert Details:

Database: {alert.database_alias}
Metric: {alert.metric_name}
Current Value: {alert.current_value}
Threshold: {alert.threshold_value}
Severity: {alert.severity.upper()}
Time: {alert.timestamp}

Message: {alert.message}

Please investigate this issue promptly.
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=recipients,
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _attempt_recovery(self, db_alias: str, metric_name: str, value: float):
        """Attempt automatic recovery for critical issues"""
        logger.info(f"Attempting recovery for {db_alias} - {metric_name} = {value}")
        
        try:
            if metric_name == 'connection_usage':
                self._recover_connection_exhaustion(db_alias)
            elif metric_name == 'slow_queries':
                self._recover_slow_queries(db_alias)
            elif metric_name == 'replication_lag':
                self._recover_replication_lag(db_alias)
            elif metric_name == 'memory_usage':
                self._recover_memory_issues(db_alias)
            elif metric_name == 'disk_usage':
                self._recover_disk_issues(db_alias)
                
        except Exception as e:
            logger.error(f"Recovery attempt failed for {db_alias}: {e}")
    
    def _recover_connection_exhaustion(self, db_alias: str):
        """Recover from connection pool exhaustion"""
        try:
            db_connection = connections[db_alias]
            
            # Close idle connections
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT ID FROM INFORMATION_SCHEMA.PROCESSLIST 
                    WHERE COMMAND = 'Sleep' AND TIME > 300
                    LIMIT 10
                """)
                
                idle_connections = cursor.fetchall()
                for conn_id in idle_connections:
                    try:
                        cursor.execute(f"KILL {conn_id[0]}")
                        logger.info(f"Killed idle connection {conn_id[0]}")
                    except:
                        pass
            
            # Reset connection pool
            db_connection.close()
            logger.info(f"Reset connection pool for {db_alias}")
            
        except Exception as e:
            logger.error(f"Failed to recover from connection exhaustion: {e}")
    
    def _recover_slow_queries(self, db_alias: str):
        """Recover from slow query issues"""
        try:
            db_connection = connections[db_alias]
            with db_connection.cursor() as cursor:
                # Kill long-running queries
                cursor.execute("""
                    SELECT ID, TIME, INFO FROM INFORMATION_SCHEMA.PROCESSLIST 
                    WHERE COMMAND != 'Sleep' AND TIME > 30
                    ORDER BY TIME DESC
                    LIMIT 5
                """)
                
                long_queries = cursor.fetchall()
                for query_id, query_time, query_info in long_queries:
                    try:
                        cursor.execute(f"KILL QUERY {query_id}")
                        logger.info(f"Killed long-running query {query_id} (running for {query_time}s)")
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Failed to recover from slow queries: {e}")
    
    def _recover_replication_lag(self, db_alias: str):
        """Recover from replication lag issues"""
        logger.critical(f"High replication lag detected on {db_alias} - manual intervention may be required")
        # In a real implementation, this might restart replication or switch to a different replica
    
    def _recover_memory_issues(self, db_alias: str):
        """Recover from memory issues"""
        try:
            db_connection = connections[db_alias]
            with db_connection.cursor() as cursor:
                # Flush query cache to free memory
                cursor.execute("FLUSH QUERY CACHE")
                cursor.execute("RESET QUERY CACHE")
                logger.info(f"Flushed query cache for {db_alias}")
                
        except Exception as e:
            logger.error(f"Failed to recover from memory issues: {e}")
    
    def _recover_disk_issues(self, db_alias: str):
        """Recover from disk space issues"""
        logger.critical(f"High disk usage detected - manual intervention required to free disk space")
        # In a real implementation, this might clean up old logs or temporary files
    
    def _cleanup_resolved_alerts(self):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Remove old alerts from history
        while self.alert_history and self.alert_history[0].timestamp < cutoff_time:
            self.alert_history.popleft()
    
    # Public API methods
    
    def record_query_time(self, db_alias: str, query_time: float):
        """Record query execution time for metrics"""
        with self._lock:
            self.query_times[db_alias].append(query_time)
    
    def get_current_metrics(self, db_alias: str = None) -> Dict[str, Any]:
        """Get current metrics for specified database or all databases"""
        if db_alias:
            cached_metrics = cache.get(f"db_metrics_{db_alias}")
            return {db_alias: cached_metrics} if cached_metrics else {}
        
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
    
    def get_slow_queries(self, db_alias: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent slow queries"""
        with self._lock:
            queries = list(self.slow_queries)
            
            if db_alias:
                queries = [q for q in queries if q.database == db_alias]
            
            # Sort by severity and execution time
            queries.sort(key=lambda x: (x.severity == 'critical', x.severity == 'high', x.execution_time), reverse=True)
            
            return [q.to_dict() for q in queries[:limit]]
    
    def get_active_alerts(self, db_alias: str = None) -> List[Dict[str, Any]]:
        """Get active alerts"""
        with self._lock:
            alerts = list(self.active_alerts.values())
            
            if db_alias:
                alerts = [a for a in alerts if a.database_alias == db_alias]
            
            return [a.to_dict() for a in alerts]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            history = [a for a in self.alert_history if a.timestamp >= cutoff_time]
            return [a.to_dict() for a in history]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of all databases"""
        summary = {
            'overall_status': 'healthy',
            'databases': {},
            'active_alerts': len(self.active_alerts),
            'total_slow_queries': len(self.slow_queries),
            'timestamp': datetime.now().isoformat()
        }
        
        critical_count = 0
        warning_count = 0
        
        for db_alias in settings.DATABASES.keys():
            metrics = cache.get(f"db_metrics_{db_alias}")
            if metrics:
                db_status = metrics.get('status', 'unknown')
                
                summary['databases'][db_alias] = {
                    'status': db_status,
                    'health_score': metrics.get('health_score', 0),
                    'active_connections': metrics.get('active_connections', 0),
                    'connection_usage_percent': metrics.get('connection_usage_percent', 0),
                    'queries_per_second': metrics.get('queries_per_second', 0),
                    'average_query_time': metrics.get('average_query_time', 0),
                    'slow_queries': metrics.get('slow_queries', 0),
                    'replication_lag': metrics.get('replication_lag', 0),
                    'replication_status': metrics.get('replication_status', 'Unknown')
                }
                
                if db_status == 'critical':
                    critical_count += 1
                elif db_status == 'warning':
                    warning_count += 1
            else:
                summary['databases'][db_alias] = {'status': 'unknown'}
                warning_count += 1
        
        # Determine overall status
        if critical_count > 0:
            summary['overall_status'] = 'critical'
        elif warning_count > 0:
            summary['overall_status'] = 'warning'
        
        return summary
    
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
    
    def enable_monitoring(self):
        """Enable monitoring"""
        self.monitoring_enabled = True
        if not self._monitoring_thread or not self._monitoring_thread.is_alive():
            self.start_monitoring()
    
    def disable_monitoring(self):
        """Disable monitoring"""
        self.monitoring_enabled = False
    
    def enable_alerting(self):
        """Enable alerting"""
        self.alerting_enabled = True
    
    def disable_alerting(self):
        """Disable alerting"""
        self.alerting_enabled = False
    
    def enable_recovery(self):
        """Enable automatic recovery"""
        self.recovery_enabled = True
    
    def disable_recovery(self):
        """Disable automatic recovery"""
        self.recovery_enabled = False


# Global monitor instance
_database_monitor = None


def get_database_monitor() -> DatabaseMonitor:
    """Get the global database monitor instance"""
    global _database_monitor
    if _database_monitor is None:
        monitoring_interval = getattr(settings, 'DB_MONITORING_INTERVAL', 30)
        _database_monitor = DatabaseMonitor(monitoring_interval)
    return _database_monitor


def initialize_database_monitoring(monitoring_interval: int = 30) -> DatabaseMonitor:
    """Initialize database monitoring with custom interval"""
    global _database_monitor
    if _database_monitor:
        _database_monitor.stop_monitoring()
    
    _database_monitor = DatabaseMonitor(monitoring_interval)
    return _database_monitor