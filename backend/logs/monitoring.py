"""
System monitoring utilities for the ecommerce platform.
"""
import logging
import time
import os
import psutil
import threading
from django.utils import timezone
from django.conf import settings
from django.db import connection

# Create a dedicated monitoring logger
monitoring_logger = logging.getLogger('monitoring')

class SystemMonitor:
    """
    Monitor system resources and log metrics.
    """
    def __init__(self):
        self.interval = getattr(settings, 'SYSTEM_MONITORING_INTERVAL', 60)  # seconds
        self.enabled = getattr(settings, 'SYSTEM_MONITORING_ENABLED', True)
        self.thread = None
        self.stop_event = threading.Event()
    
    def start(self):
        """
        Start the monitoring thread.
        """
        if not self.enabled:
            return
        
        if self.thread is not None and self.thread.is_alive():
            return
        
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """
        Stop the monitoring thread.
        """
        if self.thread is not None and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=5)
    
    def _monitoring_loop(self):
        """
        Main monitoring loop that collects and logs metrics at regular intervals.
        """
        while not self.stop_event.is_set():
            try:
                self._collect_and_log_metrics()
            except Exception as e:
                monitoring_logger.error(f"Error in monitoring loop: {str(e)}")
            
            # Sleep for the specified interval or until stopped
            self.stop_event.wait(self.interval)
    
    def _collect_and_log_metrics(self):
        """
        Collect and log system metrics.
        """
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process(os.getpid())
        process_cpu = process.cpu_percent(interval=1)
        process_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Database metrics
        db_connections = len(connection.connection.queries) if hasattr(connection, 'connection') else 0
        
        # Log system metrics
        self._log_system_metrics(cpu_percent, memory, disk)
        
        # Log process metrics
        self._log_process_metrics(process_cpu, process_memory)
        
        # Log database metrics
        self._log_database_metrics(db_connections)
    
    def _log_system_metrics(self, cpu_percent, memory, disk):
        """
        Log system-level metrics.
        """
        extra = {
            'metric_name': 'system_metrics',
            'metric_value': cpu_percent,
            'dimensions': {
                'type': 'system'
            },
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available / (1024 * 1024),
            'memory_total_mb': memory.total / (1024 * 1024),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024 * 1024 * 1024),
            'disk_total_gb': disk.total / (1024 * 1024 * 1024),
            'timestamp': timezone.now().isoformat(),
        }
        
        monitoring_logger.info(
            f"System metrics: CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%",
            extra=extra
        )
    
    def _log_process_metrics(self, process_cpu, process_memory):
        """
        Log process-level metrics.
        """
        extra = {
            'metric_name': 'process_metrics',
            'metric_value': process_cpu,
            'dimensions': {
                'type': 'process'
            },
            'process_cpu_percent': process_cpu,
            'process_memory_mb': process_memory,
            'timestamp': timezone.now().isoformat(),
        }
        
        monitoring_logger.info(
            f"Process metrics: CPU: {process_cpu}%, Memory: {process_memory:.2f} MB",
            extra=extra
        )
    
    def _log_database_metrics(self, db_connections):
        """
        Log database metrics.
        """
        extra = {
            'metric_name': 'database_metrics',
            'metric_value': db_connections,
            'dimensions': {
                'type': 'database'
            },
            'db_connections': db_connections,
            'timestamp': timezone.now().isoformat(),
        }
        
        monitoring_logger.info(
            f"Database metrics: Connections: {db_connections}",
            extra=extra
        )


class BusinessMetricsMonitor:
    """
    Monitor and log business metrics.
    """
    def __init__(self):
        self.metrics_logger = logging.getLogger('metrics')
    
    def log_active_users(self, count, period='daily'):
        """
        Log active users metric.
        
        Args:
            count: Number of active users
            period: Time period (hourly, daily, weekly, monthly)
        """
        extra = {
            'metric_name': 'active_users',
            'metric_value': count,
            'dimensions': {
                'period': period
            },
            'timestamp': timezone.now().isoformat(),
        }
        
        self.metrics_logger.info(
            f"Active users ({period}): {count}",
            extra=extra
        )
    
    def log_conversion_rate(self, rate, source=None, period='daily'):
        """
        Log conversion rate metric.
        
        Args:
            rate: Conversion rate percentage
            source: Traffic source
            period: Time period (hourly, daily, weekly, monthly)
        """
        extra = {
            'metric_name': 'conversion_rate',
            'metric_value': rate,
            'dimensions': {
                'period': period,
                'source': source
            },
            'timestamp': timezone.now().isoformat(),
        }
        
        self.metrics_logger.info(
            f"Conversion rate ({period}): {rate}%" + (f" from {source}" if source else ""),
            extra=extra
        )
    
    def log_average_order_value(self, value, period='daily'):
        """
        Log average order value metric.
        
        Args:
            value: Average order value
            period: Time period (hourly, daily, weekly, monthly)
        """
        extra = {
            'metric_name': 'average_order_value',
            'metric_value': float(value),
            'dimensions': {
                'period': period
            },
            'timestamp': timezone.now().isoformat(),
        }
        
        self.metrics_logger.info(
            f"Average order value ({period}): {value}",
            extra=extra
        )
    
    def log_cart_abandonment_rate(self, rate, period='daily'):
        """
        Log cart abandonment rate metric.
        
        Args:
            rate: Cart abandonment rate percentage
            period: Time period (hourly, daily, weekly, monthly)
        """
        extra = {
            'metric_name': 'cart_abandonment_rate',
            'metric_value': rate,
            'dimensions': {
                'period': period
            },
            'timestamp': timezone.now().isoformat(),
        }
        
        self.metrics_logger.info(
            f"Cart abandonment rate ({period}): {rate}%",
            extra=extra
        )
    
    def log_inventory_levels(self, product_id, quantity, threshold=None):
        """
        Log inventory level metric.
        
        Args:
            product_id: ID of the product
            quantity: Current quantity
            threshold: Low stock threshold
        """
        is_low_stock = threshold is not None and quantity <= threshold
        
        extra = {
            'metric_name': 'inventory_level',
            'metric_value': quantity,
            'dimensions': {
                'product_id': product_id,
                'is_low_stock': is_low_stock
            },
            'threshold': threshold,
            'timestamp': timezone.now().isoformat(),
        }
        
        log_level = logging.WARNING if is_low_stock else logging.INFO
        
        self.metrics_logger.log(
            log_level,
            f"Inventory level for product #{product_id}: {quantity}" + 
            (f" (below threshold of {threshold})" if is_low_stock else ""),
            extra=extra
        )


# Singleton instances
system_monitor = SystemMonitor()
business_metrics = BusinessMetricsMonitor()