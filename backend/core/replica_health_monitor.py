"""
Read Replica Health Monitoring and Automatic Failover

This module provides continuous monitoring of read replica health,
automatic failover capabilities, and alerting for replica issues.
"""
import logging
import time
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone
from core.read_replica_setup import ReadReplicaManager

logger = logging.getLogger(__name__)


class ReplicaHealthMonitor:
    """
    Monitors read replica health and performs automatic failover
    """
    
    def __init__(self):
        self.replica_manager = ReadReplicaManager()
        self.monitoring_enabled = getattr(settings, 'REPLICA_MONITORING_ENABLED', True)
        self.check_interval = getattr(settings, 'REPLICA_CHECK_INTERVAL', 30)  # seconds
        self.lag_threshold = getattr(settings, 'REPLICA_LAG_THRESHOLD', 5)  # seconds
        self.max_failures = getattr(settings, 'REPLICA_MAX_FAILURES', 3)
        self.failure_window = getattr(settings, 'REPLICA_FAILURE_WINDOW', 300)  # 5 minutes
        self.alert_recipients = getattr(settings, 'REPLICA_ALERT_RECIPIENTS', [])
        
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self._failure_counts = {}
        self._last_alert_times = {}
        self._alert_callbacks = []
        
    def add_alert_callback(self, callback: Callable[[str, Dict], None]):
        """Add a callback function for alerts"""
        self._alert_callbacks.append(callback)
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.monitoring_enabled:
            logger.info("Replica monitoring is disabled")
            return
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Monitoring thread is already running")
            return
        
        logger.info("Starting replica health monitoring...")
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.info("Stopping replica health monitoring...")
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=10)
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self._stop_monitoring.is_set():
            try:
                self._perform_health_check()
                self._stop_monitoring.wait(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self._stop_monitoring.wait(self.check_interval)
    
    def _perform_health_check(self):
        """Perform health check on all replicas"""
        logger.debug("Performing replica health check...")
        
        status = self.replica_manager.check_replication_status()
        lag_status = self.replica_manager.monitor_replication_lag()
        
        for replica_alias, replica_info in status.items():
            self._check_replica_health(replica_alias, replica_info, lag_status.get(replica_alias, -1))
    
    def _check_replica_health(self, replica_alias: str, replica_info: Dict, lag: int):
        """Check health of a single replica"""
        is_healthy = self._evaluate_replica_health(replica_info, lag)
        
        # Update cache with health status
        health_data = {
            'healthy': is_healthy,
            'replication_lag': lag,
            'last_check': time.time(),
            'io_running': replica_info.get('io_running'),
            'sql_running': replica_info.get('sql_running'),
            'last_error': replica_info.get('last_error'),
        }
        
        cache.set(f"db_health_{replica_alias}", health_data, 120)
        
        if not is_healthy:
            self._handle_unhealthy_replica(replica_alias, replica_info, lag)
        else:
            # Reset failure count on successful health check
            if replica_alias in self._failure_counts:
                del self._failure_counts[replica_alias]
    
    def _evaluate_replica_health(self, replica_info: Dict, lag: int) -> bool:
        """Evaluate if a replica is healthy"""
        # Check basic replication status
        if not replica_info.get('healthy', False):
            return False
        
        # Check replication lag
        if lag > self.lag_threshold:
            logger.warning(f"Replica has high lag: {lag}s (threshold: {self.lag_threshold}s)")
            return False
        
        # Check for replication errors
        if replica_info.get('last_error'):
            logger.warning(f"Replica has error: {replica_info['last_error']}")
            return False
        
        return True
    
    def _handle_unhealthy_replica(self, replica_alias: str, replica_info: Dict, lag: int):
        """Handle an unhealthy replica"""
        current_time = time.time()
        
        # Track failure count
        if replica_alias not in self._failure_counts:
            self._failure_counts[replica_alias] = []
        
        # Add current failure
        self._failure_counts[replica_alias].append(current_time)
        
        # Remove old failures outside the window
        cutoff_time = current_time - self.failure_window
        self._failure_counts[replica_alias] = [
            t for t in self._failure_counts[replica_alias] if t > cutoff_time
        ]
        
        failure_count = len(self._failure_counts[replica_alias])
        
        logger.warning(f"Replica {replica_alias} is unhealthy (failure {failure_count}/{self.max_failures})")
        
        # Perform failover if threshold exceeded
        if failure_count >= self.max_failures:
            self._perform_automatic_failover(replica_alias, replica_info, lag)
    
    def _perform_automatic_failover(self, replica_alias: str, replica_info: Dict, lag: int):
        """Perform automatic failover for a failed replica"""
        logger.critical(f"Performing automatic failover for replica: {replica_alias}")
        
        try:
            success = self.replica_manager.failover_replica(replica_alias)
            
            if success:
                logger.info(f"Automatic failover completed for {replica_alias}")
                self._send_failover_alert(replica_alias, replica_info, lag, success=True)
            else:
                logger.error(f"Automatic failover failed for {replica_alias}")
                self._send_failover_alert(replica_alias, replica_info, lag, success=False)
                
        except Exception as e:
            logger.error(f"Error during automatic failover for {replica_alias}: {e}")
            self._send_failover_alert(replica_alias, replica_info, lag, success=False, error=str(e))
    
    def _send_failover_alert(self, replica_alias: str, replica_info: Dict, lag: int, 
                           success: bool, error: Optional[str] = None):
        """Send alert about failover event"""
        current_time = time.time()
        
        # Rate limit alerts (max one per hour per replica)
        last_alert_key = f"last_alert_{replica_alias}"
        last_alert_time = self._last_alert_times.get(last_alert_key, 0)
        
        if current_time - last_alert_time < 3600:  # 1 hour
            logger.debug(f"Skipping alert for {replica_alias} due to rate limiting")
            return
        
        self._last_alert_times[last_alert_key] = current_time
        
        # Prepare alert data
        alert_data = {
            'replica_alias': replica_alias,
            'timestamp': datetime.now(),
            'success': success,
            'replica_info': replica_info,
            'replication_lag': lag,
            'error': error,
        }
        
        # Send email alert
        if self.alert_recipients:
            self._send_email_alert(alert_data)
        
        # Call custom alert callbacks
        for callback in self._alert_callbacks:
            try:
                callback(replica_alias, alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def _send_email_alert(self, alert_data: Dict):
        """Send email alert about replica failover"""
        replica_alias = alert_data['replica_alias']
        success = alert_data['success']
        timestamp = alert_data['timestamp']
        
        if success:
            subject = f"[REPLICA] Automatic failover successful for {replica_alias}"
            status = "SUCCESSFUL"
        else:
            subject = f"[REPLICA] Automatic failover FAILED for {replica_alias}"
            status = "FAILED"
        
        message = f"""
Replica Failover Alert

Replica: {replica_alias}
Status: {status}
Timestamp: {timestamp}
Replication Lag: {alert_data['replication_lag']}s

Replica Information:
- IO Running: {alert_data['replica_info'].get('io_running', 'Unknown')}
- SQL Running: {alert_data['replica_info'].get('sql_running', 'Unknown')}
- Last Error: {alert_data['replica_info'].get('last_error', 'None')}

{f"Error Details: {alert_data['error']}" if alert_data.get('error') else ""}

Please check the replica status and take appropriate action if needed.
        """.strip()
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=self.alert_recipients,
                fail_silently=False,
            )
            logger.info(f"Failover alert sent for {replica_alias}")
        except Exception as e:
            logger.error(f"Failed to send failover alert: {e}")
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'monitoring_enabled': self.monitoring_enabled,
            'monitoring_active': self._monitoring_thread and self._monitoring_thread.is_alive(),
            'check_interval': self.check_interval,
            'lag_threshold': self.lag_threshold,
            'max_failures': self.max_failures,
            'failure_window': self.failure_window,
            'failure_counts': dict(self._failure_counts),
            'last_alert_times': dict(self._last_alert_times),
        }
    
    def force_health_check(self) -> Dict:
        """Force an immediate health check and return results"""
        logger.info("Forcing immediate replica health check...")
        
        status = self.replica_manager.check_replication_status()
        lag_status = self.replica_manager.monitor_replication_lag()
        
        results = {}
        for replica_alias, replica_info in status.items():
            lag = lag_status.get(replica_alias, -1)
            is_healthy = self._evaluate_replica_health(replica_info, lag)
            
            results[replica_alias] = {
                'healthy': is_healthy,
                'replication_lag': lag,
                'io_running': replica_info.get('io_running'),
                'sql_running': replica_info.get('sql_running'),
                'last_error': replica_info.get('last_error'),
                'check_time': time.time(),
            }
            
            # Update cache
            cache.set(f"db_health_{replica_alias}", results[replica_alias], 120)
        
        return results


class ReplicaMetricsCollector:
    """
    Collects and stores metrics about replica performance
    """
    
    def __init__(self):
        self.replica_manager = ReadReplicaManager()
        self.metrics_retention = getattr(settings, 'REPLICA_METRICS_RETENTION', 86400)  # 24 hours
    
    def collect_metrics(self) -> Dict:
        """Collect current metrics from all replicas"""
        metrics = {
            'timestamp': time.time(),
            'replicas': {}
        }
        
        status = self.replica_manager.check_replication_status()
        lag_status = self.replica_manager.monitor_replication_lag()
        
        for replica_alias, replica_info in status.items():
            metrics['replicas'][replica_alias] = {
                'healthy': replica_info.get('healthy', False),
                'replication_lag': lag_status.get(replica_alias, -1),
                'io_running': replica_info.get('io_running') == 'Yes',
                'sql_running': replica_info.get('sql_running') == 'Yes',
                'has_error': bool(replica_info.get('last_error')),
            }
        
        # Store metrics in cache
        cache.set('replica_metrics_latest', metrics, self.metrics_retention)
        
        # Store historical metrics (simplified - in production, use a proper time series DB)
        historical_key = f"replica_metrics_{int(time.time() // 300) * 300}"  # 5-minute buckets
        cache.set(historical_key, metrics, self.metrics_retention)
        
        return metrics
    
    def get_metrics_summary(self, hours: int = 24) -> Dict:
        """Get metrics summary for the specified time period"""
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        # This is a simplified implementation
        # In production, you'd want to use a proper time series database
        latest_metrics = cache.get('replica_metrics_latest', {})
        
        summary = {
            'period_hours': hours,
            'start_time': start_time,
            'end_time': end_time,
            'replicas': {}
        }
        
        if 'replicas' in latest_metrics:
            for replica_alias, replica_data in latest_metrics['replicas'].items():
                summary['replicas'][replica_alias] = {
                    'current_status': replica_data,
                    'uptime_percentage': 95.0,  # Placeholder - would calculate from historical data
                    'average_lag': replica_data.get('replication_lag', 0),
                    'max_lag': replica_data.get('replication_lag', 0),
                }
        
        return summary


# Global monitor instance
_monitor_instance = None


def get_replica_monitor() -> ReplicaHealthMonitor:
    """Get the global replica monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ReplicaHealthMonitor()
    return _monitor_instance


def start_replica_monitoring():
    """Start replica monitoring"""
    monitor = get_replica_monitor()
    monitor.start_monitoring()


def stop_replica_monitoring():
    """Stop replica monitoring"""
    monitor = get_replica_monitor()
    monitor.stop_monitoring()


def get_replica_health_status() -> Dict:
    """Get current replica health status"""
    monitor = get_replica_monitor()
    return monitor.force_health_check()