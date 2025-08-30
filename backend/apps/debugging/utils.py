import uuid
import time
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import WorkflowSession, TraceStep, PerformanceSnapshot, ErrorLog


class WorkflowTracer:
    """Utility class for tracing workflows across the system"""
    
    def __init__(self, correlation_id=None):
        self.correlation_id = correlation_id or uuid.uuid4()
    
    def start_workflow_instance(self, workflow_type, user=None, session_key=None, metadata=None):
        """Start a new workflow session (instance method)"""
        workflow = WorkflowSession.objects.create(
            correlation_id=self.correlation_id,
            workflow_type=workflow_type,
            user=user,
            session_key=session_key,
            metadata=metadata or {}
        )
        return workflow
    
    def add_trace_step_instance(self, workflow_session, layer, component, operation, metadata=None):
        """Add a trace step to the workflow (instance method)"""
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
    
    @staticmethod
    def start_workflow(workflow_type, correlation_id=None, user=None, session_key=None, metadata=None):
        """Start a new workflow session (static method)"""
        if isinstance(correlation_id, str):
            correlation_id = uuid.UUID(correlation_id)
        elif correlation_id is None:
            correlation_id = uuid.uuid4()
        
        workflow = WorkflowSession.objects.create(
            correlation_id=correlation_id,
            workflow_type=workflow_type,
            user=user,
            session_key=session_key,
            metadata=metadata or {}
        )
        return workflow
    
    @staticmethod
    def add_trace_step(correlation_id, layer, component, operation, metadata=None):
        """Add a trace step to the workflow (static method)"""
        if isinstance(correlation_id, str):
            correlation_id = uuid.UUID(correlation_id)
        
        # Find the workflow session
        try:
            workflow_session = WorkflowSession.objects.get(correlation_id=correlation_id)
        except WorkflowSession.DoesNotExist:
            # Create a new workflow session if it doesn't exist
            workflow_session = WorkflowSession.objects.create(
                correlation_id=correlation_id,
                workflow_type='unknown',
                metadata={}
            )
        
        trace_step = TraceStep.objects.create(
            workflow_session=workflow_session,
            layer=layer,
            component=component,
            operation=operation,
            start_time=timezone.now(),
            metadata=metadata or {}
        )
        return trace_step
    
    @staticmethod
    def complete_workflow(correlation_id, status='completed', metadata=None):
        """Complete a workflow session (static method)"""
        if isinstance(correlation_id, str):
            correlation_id = uuid.UUID(correlation_id)
        
        try:
            workflow_session = WorkflowSession.objects.get(correlation_id=correlation_id)
            workflow_session.status = status
            workflow_session.end_time = timezone.now()
            
            if workflow_session.start_time:
                delta = workflow_session.end_time - workflow_session.start_time
                workflow_session.duration_ms = int(delta.total_seconds() * 1000)
            
            if metadata:
                workflow_session.metadata.update(metadata)
            
            workflow_session.save()
            return workflow_session
        except WorkflowSession.DoesNotExist:
            return None
    
    @staticmethod
    def fail_workflow(correlation_id, error_message, metadata=None):
        """Mark a workflow as failed (static method)"""
        if isinstance(correlation_id, str):
            correlation_id = uuid.UUID(correlation_id)
        
        try:
            workflow_session = WorkflowSession.objects.get(correlation_id=correlation_id)
            workflow_session.status = 'failed'
            workflow_session.end_time = timezone.now()
            
            if workflow_session.start_time:
                delta = workflow_session.end_time - workflow_session.start_time
                workflow_session.duration_ms = int(delta.total_seconds() * 1000)
            
            workflow_session.metadata.update({
                'error_message': error_message,
                **(metadata or {})
            })
            
            workflow_session.save()
            return workflow_session
        except WorkflowSession.DoesNotExist:
            return None


class PerformanceMonitor:
    """Utility class for monitoring performance metrics"""
    
    @staticmethod
    def record_metric(layer, component, metric_name, metric_value, 
                     correlation_id=None, metadata=None):
        """Record a performance metric"""
        # Get thresholds if they exist
        from .models import PerformanceThreshold
        
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
        
        return snapshot
    
    @staticmethod
    def check_thresholds():
        """Check all recent metrics against thresholds and return alerts"""
        from .models import PerformanceSnapshot, PerformanceThreshold
        from django.utils import timezone
        from datetime import timedelta
        
        alerts = []
        
        # Check metrics from the last hour
        cutoff_time = timezone.now() - timedelta(hours=1)
        recent_metrics = PerformanceSnapshot.objects.filter(
            timestamp__gte=cutoff_time
        ).select_related()
        
        for metric in recent_metrics:
            threshold = PerformanceThreshold.objects.filter(
                metric_name=metric.metric_name,
                layer=metric.layer,
                component=metric.component or '',
                enabled=True
            ).first()
            
            if threshold:
                alert_level = None
                if threshold.critical_threshold and metric.metric_value >= threshold.critical_threshold:
                    alert_level = 'critical'
                elif threshold.warning_threshold and metric.metric_value >= threshold.warning_threshold:
                    alert_level = 'warning'
                
                if alert_level:
                    alerts.append({
                        'level': alert_level,
                        'metric_name': metric.metric_name,
                        'layer': metric.layer,
                        'component': metric.component,
                        'value': metric.metric_value,
                        'threshold': threshold.critical_threshold if alert_level == 'critical' else threshold.warning_threshold,
                        'timestamp': metric.timestamp,
                        'correlation_id': metric.correlation_id
                    })
        
        return alerts
    
    @staticmethod
    def analyze_trends(layer, component, metric_name, hours=24):
        """Analyze performance trends for a specific metric"""
        from .models import PerformanceSnapshot
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        metrics = PerformanceSnapshot.objects.filter(
            layer=layer,
            component=component,
            metric_name=metric_name,
            timestamp__gte=cutoff_time
        ).order_by('timestamp')
        
        if not metrics.exists():
            return {'trend_direction': 'no_data', 'data_points': 0}
        
        values = [m.metric_value for m in metrics]
        
        # Simple trend analysis
        if len(values) < 2:
            trend_direction = 'insufficient_data'
        else:
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            
            if avg_second > avg_first * 1.1:  # 10% increase
                trend_direction = 'increasing'
            elif avg_second < avg_first * 0.9:  # 10% decrease
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        
        return {
            'trend_direction': trend_direction,
            'average_value': sum(values) / len(values),
            'min_value': min(values),
            'max_value': max(values),
            'data_points': len(values),
            'time_range_hours': hours
        }
    
    @staticmethod
    def track_memory_usage(operation_name, correlation_id=None):
        """Track current memory usage for an operation"""
        try:
            import psutil
            import os
            
            # Get current process memory usage
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            
            # Record the memory usage metric
            PerformanceMonitor.record_metric(
                layer='system',
                component='memory',
                metric_name='memory_usage',
                metric_value=memory_mb,
                correlation_id=correlation_id,
                metadata={'operation': operation_name, 'unit': 'MB'}
            )
            
            return memory_mb
        except ImportError:
            # psutil not available, return None
            return None


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