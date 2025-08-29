import uuid
import time
from django.utils import timezone
from django.contrib.auth.models import User
from .models import WorkflowSession, TraceStep, PerformanceSnapshot, ErrorLog


class WorkflowTracer:
    """Utility class for tracing workflows across the system"""
    
    def __init__(self, correlation_id=None):
        self.correlation_id = correlation_id or uuid.uuid4()
    
    def start_workflow(self, workflow_type, user=None, session_key=None, metadata=None):
        """Start a new workflow session"""
        workflow = WorkflowSession.objects.create(
            correlation_id=self.correlation_id,
            workflow_type=workflow_type,
            user=user,
            session_key=session_key,
            metadata=metadata or {}
        )
        return workflow
    
    def add_trace_step(self, workflow_session, layer, component, operation, metadata=None):
        """Add a trace step to the workflow"""
        trace_step = TraceStep.objects.create(
            workflow_session=workflow_session,
            layer=layer,
            component=component,
            operation=operation,
            start_time=timezone.now(),
            metadata=metadata or {}
        )
        return trace_step
    
    def complete_trace_step(self, trace_step, metadata=None):
        """Mark a trace step as completed"""
        trace_step.status = 'completed'
        trace_step.end_time = timezone.now()
        
        if trace_step.start_time:
            delta = trace_step.end_time - trace_step.start_time
            trace_step.duration_ms = int(delta.total_seconds() * 1000)
        
        if metadata:
            trace_step.metadata.update(metadata)
        
        trace_step.save()
        return trace_step
    
    def fail_trace_step(self, trace_step, error_message, metadata=None):
        """Mark a trace step as failed"""
        trace_step.status = 'failed'
        trace_step.end_time = timezone.now()
        
        if trace_step.start_time:
            delta = trace_step.end_time - trace_step.start_time
            trace_step.duration_ms = int(delta.total_seconds() * 1000)
        
        trace_step.metadata.update({
            'error_message': error_message,
            **(metadata or {})
        })
        
        trace_step.save()
        return trace_step


class PerformanceMonitor:
    """Utility class for monitoring performance metrics"""
    
    def __init__(self, correlation_id=None):
        self.correlation_id = correlation_id or uuid.uuid4()
        self._metrics = []
    
    def measure_execution_time(self, operation_name):
        """Context manager for measuring execution time"""
        return ExecutionTimeContext(self, operation_name)
    
    def record_metric(self, layer, component, metric_name, metric_value, 
                     correlation_id=None, metadata=None):
        """Record a performance metric"""
        # Get thresholds if they exist
        from .models import PerformanceThreshold
        
        correlation_id = correlation_id or self.correlation_id
        
        threshold = PerformanceThreshold.objects.filter(
            metric_name=metric_name,
            layer=layer,
            component=component or '',
            enabled=True
        ).first()
        
        warning_threshold = threshold.warning_threshold if threshold else None
        critical_threshold = threshold.critical_threshold if threshold else None
        
        snapshot = PerformanceSnapshot.objects.create(
            correlation_id=correlation_id,
            layer=layer,
            component=component,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_warning=warning_threshold,
            threshold_critical=critical_threshold,
            metadata=metadata or {}
        )
        
        # Store in local metrics for reporting
        self._metrics.append({
            'layer': layer,
            'component': component,
            'metric_name': metric_name,
            'metric_value': metric_value,
            'timestamp': snapshot.timestamp,
            'correlation_id': correlation_id
        })
        
        return snapshot
    
    def get_performance_metrics(self):
        """Get collected performance metrics"""
        return self._metrics.copy()
    
    def track_memory_usage(self, operation_name):
        """Track current memory usage for an operation"""
        import psutil
        import os
        
        # Get current process memory usage
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
        
        # Record the memory usage metric
        self.record_metric(
            layer='system',
            component='memory',
            metric_name=f'{operation_name}_memory_usage',
            metric_value=memory_mb,
            metadata={'operation': operation_name, 'unit': 'MB'}
        )
        
        return memory_mb
    
    def check_thresholds(self, layer, component, metric_name, metric_value):
        """Check if metric value exceeds thresholds"""
        from .models import PerformanceThreshold
        
        threshold = PerformanceThreshold.objects.filter(
            metric_name=metric_name,
            layer=layer,
            component=component or '',
            enabled=True
        ).first()
        
        if not threshold:
            return {'status': 'no_threshold'}
        
        if threshold.critical_threshold and metric_value >= threshold.critical_threshold:
            return {'status': 'critical', 'threshold': threshold.critical_threshold}
        elif threshold.warning_threshold and metric_value >= threshold.warning_threshold:
            return {'status': 'warning', 'threshold': threshold.warning_threshold}
        else:
            return {'status': 'normal'}


class ExecutionTimeContext:
    """Context manager for measuring execution time"""
    
    def __init__(self, monitor, operation_name):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        # Record the execution time metric
        self.monitor.record_metric(
            layer='performance',
            component='demo',
            metric_name=f'{self.operation_name}_execution_time',
            metric_value=duration_ms,
            metadata={'operation': self.operation_name}
        )


class ErrorLogger:
    """Utility class for logging errors across the system"""
    
    @staticmethod
    def log_error(layer, component, error_type, error_message, 
                  correlation_id=None, severity='error', stack_trace=None,
                  user=None, request_path=None, request_method=None,
                  user_agent=None, ip_address=None, metadata=None):
        """Log an error to the debugging system"""
        error_log = ErrorLog.objects.create(
            correlation_id=correlation_id,
            layer=layer,
            component=component,
            severity=severity,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            user=user,
            request_path=request_path,
            request_method=request_method,
            user_agent=user_agent,
            ip_address=ip_address,
            metadata=metadata or {}
        )
        
        return error_log
    
    @staticmethod
    def log_exception(exception, layer, component, correlation_id=None, 
                     user=None, request=None, metadata=None):
        """Log an exception with stack trace"""
        import traceback
        
        error_type = exception.__class__.__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()
        
        # Extract request information if available
        request_path = getattr(request, 'path', None)
        request_method = getattr(request, 'method', None)
        user_agent = getattr(request, 'META', {}).get('HTTP_USER_AGENT')
        ip_address = getattr(request, 'META', {}).get('REMOTE_ADDR')
        
        return ErrorLogger.log_error(
            layer=layer,
            component=component,
            error_type=error_type,
            error_message=error_message,
            correlation_id=correlation_id,
            severity='error',
            stack_trace=stack_trace,
            user=user,
            request_path=request_path,
            request_method=request_method,
            user_agent=user_agent,
            ip_address=ip_address,
            metadata=metadata
        )


def get_correlation_id_from_request(request):
    """Extract correlation ID from request headers or generate new one"""
    correlation_id = request.META.get('HTTP_X_CORRELATION_ID')
    if correlation_id:
        try:
            return uuid.UUID(correlation_id)
        except ValueError:
            pass
    
    return uuid.uuid4()


def add_correlation_id_to_response(response, correlation_id):
    """Add correlation ID to response headers"""
    response['X-Correlation-ID'] = str(correlation_id)
    return response