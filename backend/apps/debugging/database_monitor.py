"""
Database Monitoring for Workflow Tracing

This module provides database-specific monitoring and tracing capabilities
to track database operations within workflows.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from django.db import connection
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .services import WorkflowTracingEngine
from .utils import PerformanceMonitor, ErrorLogger

logger = logging.getLogger(__name__)


class DatabaseQueryMonitor:
    """Monitor database queries within workflow traces"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id
        self.query_start_time = None
        self.active_queries = {}
    
    def start_query_monitoring(self, query_type: str, table_name: str, operation: str):
        """Start monitoring a database query"""
        query_key = f"{query_type}_{table_name}_{operation}_{time.time()}"
        self.active_queries[query_key] = {
            'start_time': time.time(),
            'query_type': query_type,
            'table_name': table_name,
            'operation': operation
        }
        return query_key
    
    def end_query_monitoring(self, query_key: str, query_sql: Optional[str] = None, 
                           result_count: Optional[int] = None, error: Optional[str] = None):
        """End monitoring a database query"""
        if query_key not in self.active_queries:
            return
        
        query_info = self.active_queries[query_key]
        duration_ms = (time.time() - query_info['start_time']) * 1000
        
        # Record performance metric
        PerformanceMonitor.record_metric(
            layer='database',
            component=query_info['table_name'],
            metric_name='query_time',
            metric_value=duration_ms,
            correlation_id=self.correlation_id,
            metadata={
                'query_type': query_info['query_type'],
                'operation': query_info['operation'],
                'sql': query_sql[:500] if query_sql else None,  # Truncate long queries
                'result_count': result_count,
                'error': error
            }
        )
        
        # Log slow queries
        if duration_ms > 100:  # Queries slower than 100ms
            severity = 'warning' if duration_ms < 1000 else 'error'
            ErrorLogger.log_error(
                layer='database',
                component=query_info['table_name'],
                error_type='SlowQuery',
                error_message=f"Query took {duration_ms:.2f}ms",
                correlation_id=self.correlation_id,
                severity=severity,
                metadata={
                    'query_type': query_info['query_type'],
                    'operation': query_info['operation'],
                    'duration_ms': duration_ms,
                    'sql': query_sql[:500] if query_sql else None
                }
            )
        
        # Clean up
        del self.active_queries[query_key]
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current database connection statistics"""
        try:
            with connection.cursor() as cursor:
                # Get connection count (MySQL specific)
                cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                threads_connected = cursor.fetchone()
                
                cursor.execute("SHOW STATUS LIKE 'Max_used_connections'")
                max_used_connections = cursor.fetchone()
                
                cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
                max_connections = cursor.fetchone()
                
                return {
                    'active_connections': int(threads_connected[1]) if threads_connected else 0,
                    'max_used_connections': int(max_used_connections[1]) if max_used_connections else 0,
                    'max_connections': int(max_connections[1]) if max_connections else 0,
                    'connection_utilization': (int(threads_connected[1]) / int(max_connections[1]) * 100) if threads_connected and max_connections else 0
                }
        except Exception as e:
            logger.error(f"Error getting connection stats: {e}")
            return {'error': str(e)}


class DatabaseOperationTracer:
    """Trace database operations within workflows"""
    
    def __init__(self, tracing_engine: WorkflowTracingEngine):
        self.tracing_engine = tracing_engine
        self.query_monitor = DatabaseQueryMonitor(str(tracing_engine.correlation_id))
    
    def trace_query(self, query_type: str, table_name: str, operation: str):
        """Context manager for tracing database queries"""
        return DatabaseQueryContext(self, query_type, table_name, operation)
    
    def trace_model_operation(self, model_name: str, operation: str, instance_id: Optional[int] = None):
        """Trace Django model operations"""
        metadata = {'model_name': model_name}
        if instance_id:
            metadata['instance_id'] = instance_id
        
        return self.tracing_engine.trace_step('database', model_name, operation, metadata)
    
    def trace_bulk_operation(self, model_name: str, operation: str, count: int):
        """Trace bulk database operations"""
        metadata = {'model_name': model_name, 'operation_count': count}
        return self.tracing_engine.trace_step('database', model_name, f'bulk_{operation}', metadata)


class DatabaseQueryContext:
    """Context manager for database query tracing"""
    
    def __init__(self, tracer: DatabaseOperationTracer, query_type: str, table_name: str, operation: str):
        self.tracer = tracer
        self.query_type = query_type
        self.table_name = table_name
        self.operation = operation
        self.query_key = None
        self.step_context = None
    
    def __enter__(self):
        # Start query monitoring
        self.query_key = self.tracer.query_monitor.start_query_monitoring(
            self.query_type, self.table_name, self.operation
        )
        
        # Start workflow step tracing
        self.step_context = self.tracer.tracing_engine.trace_step(
            'database', self.table_name, self.operation
        )
        self.step_context.__enter__()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # End query monitoring
        error_message = str(exc_val) if exc_val else None
        self.tracer.query_monitor.end_query_monitoring(
            self.query_key, error=error_message
        )
        
        # End workflow step tracing
        if self.step_context:
            self.step_context.__exit__(exc_type, exc_val, exc_tb)
        
        return False  # Don't suppress exceptions


class DatabaseSignalHandler:
    """Handle Django model signals for automatic tracing"""
    
    def __init__(self):
        self.enabled = True
        self.traced_models = set()
    
    def enable_tracing_for_model(self, model_class):
        """Enable automatic tracing for a model"""
        if model_class not in self.traced_models:
            self.traced_models.add(model_class)
            
            # Connect signals
            pre_save.connect(self._pre_save_handler, sender=model_class)
            post_save.connect(self._post_save_handler, sender=model_class)
            pre_delete.connect(self._pre_delete_handler, sender=model_class)
            post_delete.connect(self._post_delete_handler, sender=model_class)
    
    def disable_tracing_for_model(self, model_class):
        """Disable automatic tracing for a model"""
        if model_class in self.traced_models:
            self.traced_models.remove(model_class)
            
            # Disconnect signals
            pre_save.disconnect(self._pre_save_handler, sender=model_class)
            post_save.disconnect(self._post_save_handler, sender=model_class)
            pre_delete.disconnect(self._pre_delete_handler, sender=model_class)
            post_delete.disconnect(self._post_delete_handler, sender=model_class)
    
    def _get_correlation_id_from_context(self):
        """Get correlation ID from current request context"""
        # This would typically be stored in thread-local storage
        # or passed through the request context
        return getattr(cache, '_current_correlation_id', None)
    
    def _pre_save_handler(self, sender, instance, **kwargs):
        """Handle pre_save signal"""
        if not self.enabled:
            return
        
        correlation_id = self._get_correlation_id_from_context()
        if not correlation_id:
            return
        
        # Store start time for this operation
        operation_key = f"save_{sender.__name__}_{id(instance)}"
        cache.set(f"db_operation_start_{operation_key}", time.time(), 60)
    
    def _post_save_handler(self, sender, instance, created, **kwargs):
        """Handle post_save signal"""
        if not self.enabled:
            return
        
        correlation_id = self._get_correlation_id_from_context()
        if not correlation_id:
            return
        
        operation_key = f"save_{sender.__name__}_{id(instance)}"
        start_time = cache.get(f"db_operation_start_{operation_key}")
        
        if start_time:
            duration_ms = (time.time() - start_time) * 1000
            operation = 'create' if created else 'update'
            
            PerformanceMonitor.record_metric(
                layer='database',
                component=sender.__name__,
                metric_name='model_operation_time',
                metric_value=duration_ms,
                correlation_id=correlation_id,
                metadata={
                    'operation': operation,
                    'model_name': sender.__name__,
                    'instance_id': getattr(instance, 'pk', None)
                }
            )
            
            # Clean up
            cache.delete(f"db_operation_start_{operation_key}")
    
    def _pre_delete_handler(self, sender, instance, **kwargs):
        """Handle pre_delete signal"""
        if not self.enabled:
            return
        
        correlation_id = self._get_correlation_id_from_context()
        if not correlation_id:
            return
        
        # Store start time for this operation
        operation_key = f"delete_{sender.__name__}_{id(instance)}"
        cache.set(f"db_operation_start_{operation_key}", time.time(), 60)
    
    def _post_delete_handler(self, sender, instance, **kwargs):
        """Handle post_delete signal"""
        if not self.enabled:
            return
        
        correlation_id = self._get_correlation_id_from_context()
        if not correlation_id:
            return
        
        operation_key = f"delete_{sender.__name__}_{id(instance)}"
        start_time = cache.get(f"db_operation_start_{operation_key}")
        
        if start_time:
            duration_ms = (time.time() - start_time) * 1000
            
            PerformanceMonitor.record_metric(
                layer='database',
                component=sender.__name__,
                metric_name='model_operation_time',
                metric_value=duration_ms,
                correlation_id=correlation_id,
                metadata={
                    'operation': 'delete',
                    'model_name': sender.__name__,
                    'instance_id': getattr(instance, 'pk', None)
                }
            )
            
            # Clean up
            cache.delete(f"db_operation_start_{operation_key}")


# Global database signal handler instance
db_signal_handler = DatabaseSignalHandler()


def enable_model_tracing(model_class):
    """Enable automatic tracing for a Django model"""
    db_signal_handler.enable_tracing_for_model(model_class)


def disable_model_tracing(model_class):
    """Disable automatic tracing for a Django model"""
    db_signal_handler.disable_tracing_for_model(model_class)


class DatabaseHealthMonitor:
    """Monitor database health and performance"""
    
    def __init__(self):
        self.connection_pool_stats = {}
    
    def check_database_health(self) -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        health_status = {
            'status': 'healthy',
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Test basic connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health_status['checks']['connectivity'] = 'pass'
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['connectivity'] = 'fail'
            health_status['errors'].append(f"Database connectivity failed: {e}")
        
        try:
            # Check connection pool status
            monitor = DatabaseQueryMonitor()
            conn_stats = monitor.get_connection_stats()
            
            if 'error' not in conn_stats:
                health_status['checks']['connection_pool'] = conn_stats
                
                # Check for high connection utilization
                if conn_stats.get('connection_utilization', 0) > 80:
                    health_status['warnings'].append(
                        f"High connection pool utilization: {conn_stats['connection_utilization']:.1f}%"
                    )
                    if health_status['status'] == 'healthy':
                        health_status['status'] = 'warning'
            else:
                health_status['checks']['connection_pool'] = 'fail'
                health_status['errors'].append(f"Connection pool check failed: {conn_stats['error']}")
        
        except Exception as e:
            health_status['checks']['connection_pool'] = 'fail'
            health_status['errors'].append(f"Connection pool monitoring failed: {e}")
        
        try:
            # Check for slow queries in the last hour
            from .models import PerformanceSnapshot
            from django.utils import timezone
            from datetime import timedelta
            
            one_hour_ago = timezone.now() - timedelta(hours=1)
            slow_queries = PerformanceSnapshot.objects.filter(
                layer='database',
                metric_name='query_time',
                metric_value__gte=1000,  # Queries slower than 1 second
                timestamp__gte=one_hour_ago
            ).count()
            
            health_status['checks']['slow_queries'] = {
                'count': slow_queries,
                'threshold': 10
            }
            
            if slow_queries > 10:
                health_status['warnings'].append(f"High number of slow queries: {slow_queries} in the last hour")
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'warning'
        
        except Exception as e:
            health_status['checks']['slow_queries'] = 'fail'
            health_status['errors'].append(f"Slow query check failed: {e}")
        
        # Set overall status based on errors
        if health_status['errors']:
            health_status['status'] = 'unhealthy'
        elif health_status['warnings'] and health_status['status'] == 'healthy':
            health_status['status'] = 'warning'
        
        return health_status
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get database performance summary for the specified time period"""
        from .models import PerformanceSnapshot
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Avg, Max, Min, Count
        
        time_threshold = timezone.now() - timedelta(hours=hours)
        
        # Get database performance metrics
        db_metrics = PerformanceSnapshot.objects.filter(
            layer='database',
            timestamp__gte=time_threshold
        )
        
        summary = {
            'time_period_hours': hours,
            'total_operations': db_metrics.count(),
            'metrics': {}
        }
        
        # Aggregate by metric type
        for metric_name in ['query_time', 'model_operation_time']:
            metric_data = db_metrics.filter(metric_name=metric_name).aggregate(
                avg=Avg('metric_value'),
                max=Max('metric_value'),
                min=Min('metric_value'),
                count=Count('id')
            )
            
            if metric_data['count'] > 0:
                summary['metrics'][metric_name] = {
                    'average_ms': round(metric_data['avg'], 2) if metric_data['avg'] else 0,
                    'max_ms': metric_data['max'] or 0,
                    'min_ms': metric_data['min'] or 0,
                    'operation_count': metric_data['count']
                }
        
        return summary