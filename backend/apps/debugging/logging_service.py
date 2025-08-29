"""
Comprehensive logging service for the E2E Workflow Debugging System.
Provides structured logging across all system layers with correlation ID support.
"""

import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.db import connection
from django.conf import settings
from django.contrib.auth.models import User
from .models import ErrorLog, WorkflowSession, TraceStep, PerformanceSnapshot
from .utils import get_correlation_id_from_request


class StructuredLogger:
    """Enhanced structured logger with correlation ID support"""
    
    def __init__(self, name: str, correlation_id: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.context = {}
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for this logger instance"""
        self.correlation_id = correlation_id
    
    def add_context(self, **kwargs):
        """Add context information to all log messages"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context information"""
        self.context.clear()
    
    def _format_message(self, message: str, extra_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Format log message with structured data"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'correlation_id': self.correlation_id,
            'message': message,
            'context': self.context.copy()
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        return log_data
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        log_data = self._format_message(message, kwargs)
        self.logger.debug(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        log_data = self._format_message(message, kwargs)
        self.logger.info(json.dumps(log_data))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        log_data = self._format_message(message, kwargs)
        self.logger.warning(json.dumps(log_data))
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        log_data = self._format_message(message, kwargs)
        self.logger.error(json.dumps(log_data))
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        log_data = self._format_message(message, kwargs)
        self.logger.critical(json.dumps(log_data))


class DatabaseQueryLogger:
    """Logger for database queries with execution time tracking"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.logger = StructuredLogger('database.queries', correlation_id)
        self.query_count = 0
        self.total_time = 0.0
        self.slow_queries = []
        self.slow_query_threshold = 100  # milliseconds
    
    def log_query(self, query: str, params: tuple, execution_time: float, 
                  connection_alias: str = 'default'):
        """Log a database query with execution time"""
        self.query_count += 1
        self.total_time += execution_time
        
        query_data = {
            'layer': 'database',
            'component': 'query_executor',
            'query': query,
            'params': params,
            'execution_time_ms': execution_time * 1000,
            'connection_alias': connection_alias,
            'query_number': self.query_count
        }
        
        # Check if query is slow
        execution_time_ms = execution_time * 1000
        if execution_time_ms > self.slow_query_threshold:
            query_data['is_slow_query'] = True
            self.slow_queries.append(query_data)
            self.logger.warning(
                f"Slow query detected: {execution_time_ms:.2f}ms",
                **query_data
            )
        else:
            self.logger.debug(
                f"Query executed: {execution_time_ms:.2f}ms",
                **query_data
            )
        
        # Record performance metric
        PerformanceSnapshot.objects.create(
            correlation_id=self.correlation_id,
            layer='database',
            component='query_executor',
            metric_name='query_execution_time',
            metric_value=execution_time_ms,
            metadata=query_data
        )
    
    def get_query_summary(self) -> Dict[str, Any]:
        """Get summary of queries executed"""
        return {
            'total_queries': self.query_count,
            'total_time_ms': self.total_time * 1000,
            'average_time_ms': (self.total_time * 1000) / self.query_count if self.query_count > 0 else 0,
            'slow_queries_count': len(self.slow_queries),
            'slow_queries': self.slow_queries
        }


class FrontendLogger:
    """Logger for frontend interactions and API calls"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.logger = StructuredLogger('frontend.interactions', correlation_id)
    
    def log_user_interaction(self, interaction_type: str, element: str, 
                           page_url: str, user_id: Optional[int] = None,
                           metadata: Optional[Dict] = None):
        """Log user interaction on frontend"""
        interaction_data = {
            'layer': 'frontend',
            'component': 'user_interaction',
            'interaction_type': interaction_type,
            'element': element,
            'page_url': page_url,
            'user_id': user_id,
            'timestamp': timezone.now().isoformat()
        }
        
        if metadata:
            interaction_data['metadata'] = metadata
        
        self.logger.info(
            f"User interaction: {interaction_type} on {element}",
            **interaction_data
        )
    
    def log_api_call(self, method: str, endpoint: str, status_code: int,
                    response_time_ms: float, payload_size: Optional[int] = None,
                    error_message: Optional[str] = None):
        """Log API call from frontend"""
        api_call_data = {
            'layer': 'frontend',
            'component': 'api_client',
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time_ms': response_time_ms,
            'payload_size_bytes': payload_size,
            'timestamp': timezone.now().isoformat()
        }
        
        if error_message:
            api_call_data['error_message'] = error_message
            self.logger.error(
                f"API call failed: {method} {endpoint} - {error_message}",
                **api_call_data
            )
        else:
            self.logger.info(
                f"API call: {method} {endpoint} - {status_code} ({response_time_ms}ms)",
                **api_call_data
            )
        
        # Record performance metric
        PerformanceSnapshot.objects.create(
            correlation_id=self.correlation_id,
            layer='frontend',
            component='api_client',
            metric_name='api_response_time',
            metric_value=response_time_ms,
            metadata=api_call_data
        )
    
    def log_page_load(self, page_url: str, load_time_ms: float, 
                     resources_loaded: int, user_id: Optional[int] = None):
        """Log page load performance"""
        page_load_data = {
            'layer': 'frontend',
            'component': 'page_loader',
            'page_url': page_url,
            'load_time_ms': load_time_ms,
            'resources_loaded': resources_loaded,
            'user_id': user_id,
            'timestamp': timezone.now().isoformat()
        }
        
        self.logger.info(
            f"Page loaded: {page_url} ({load_time_ms}ms, {resources_loaded} resources)",
            **page_load_data
        )
        
        # Record performance metric
        PerformanceSnapshot.objects.create(
            correlation_id=self.correlation_id,
            layer='frontend',
            component='page_loader',
            metric_name='page_load_time',
            metric_value=load_time_ms,
            metadata=page_load_data
        )


class LogAggregationService:
    """Service for aggregating and correlating logs across all layers"""
    
    def __init__(self):
        self.logger = StructuredLogger('log_aggregation')
    
    def get_correlated_logs(self, correlation_id: str, 
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get all logs correlated by correlation ID"""
        
        # Get workflow session
        try:
            workflow_session = WorkflowSession.objects.get(correlation_id=correlation_id)
        except WorkflowSession.DoesNotExist:
            workflow_session = None
        
        # Get trace steps
        trace_steps = []
        if workflow_session:
            steps = TraceStep.objects.filter(workflow_session=workflow_session)
            if start_time:
                steps = steps.filter(start_time__gte=start_time)
            if end_time:
                steps = steps.filter(start_time__lte=end_time)
            
            trace_steps = [
                {
                    'layer': step.layer,
                    'component': step.component,
                    'operation': step.operation,
                    'start_time': step.start_time.isoformat(),
                    'end_time': step.end_time.isoformat() if step.end_time else None,
                    'duration_ms': step.duration_ms,
                    'status': step.status,
                    'metadata': step.metadata
                }
                for step in steps.order_by('start_time')
            ]
        
        # Get performance snapshots
        perf_query = PerformanceSnapshot.objects.filter(correlation_id=correlation_id)
        if start_time:
            perf_query = perf_query.filter(timestamp__gte=start_time)
        if end_time:
            perf_query = perf_query.filter(timestamp__lte=end_time)
        
        performance_metrics = [
            {
                'layer': snapshot.layer,
                'component': snapshot.component,
                'metric_name': snapshot.metric_name,
                'metric_value': snapshot.metric_value,
                'timestamp': snapshot.timestamp.isoformat(),
                'metadata': snapshot.metadata
            }
            for snapshot in perf_query.order_by('timestamp')
        ]
        
        # Get error logs
        error_query = ErrorLog.objects.filter(correlation_id=correlation_id)
        if start_time:
            error_query = error_query.filter(timestamp__gte=start_time)
        if end_time:
            error_query = error_query.filter(timestamp__lte=end_time)
        
        error_logs = [
            {
                'layer': error.layer,
                'component': error.component,
                'severity': error.severity,
                'error_type': error.error_type,
                'error_message': error.error_message,
                'timestamp': error.timestamp.isoformat(),
                'stack_trace': error.stack_trace,
                'metadata': error.metadata
            }
            for error in error_query.order_by('timestamp')
        ]
        
        return {
            'correlation_id': correlation_id,
            'workflow_session': {
                'workflow_type': workflow_session.workflow_type if workflow_session else None,
                'start_time': workflow_session.start_time.isoformat() if workflow_session else None,
                'end_time': workflow_session.end_time.isoformat() if workflow_session and workflow_session.end_time else None,
                'status': workflow_session.status if workflow_session else None,
                'metadata': workflow_session.metadata if workflow_session else {}
            } if workflow_session else None,
            'trace_steps': trace_steps,
            'performance_metrics': performance_metrics,
            'error_logs': error_logs,
            'summary': {
                'total_trace_steps': len(trace_steps),
                'total_performance_metrics': len(performance_metrics),
                'total_errors': len(error_logs),
                'layers_involved': list(set([step['layer'] for step in trace_steps] + 
                                          [metric['layer'] for metric in performance_metrics] + 
                                          [error['layer'] for error in error_logs]))
            }
        }
    
    def analyze_workflow_performance(self, correlation_id: str) -> Dict[str, Any]:
        """Analyze performance of a complete workflow"""
        correlated_data = self.get_correlated_logs(correlation_id)
        
        if not correlated_data['workflow_session']:
            return {'error': 'No workflow session found for correlation ID'}
        
        # Analyze timing
        trace_steps = correlated_data['trace_steps']
        if not trace_steps:
            return {'error': 'No trace steps found'}
        
        # Calculate total workflow time
        start_times = [step['start_time'] for step in trace_steps if step['start_time']]
        end_times = [step['end_time'] for step in trace_steps if step['end_time']]
        
        if start_times and end_times:
            workflow_start = min(start_times)
            workflow_end = max(end_times)
            
            start_dt = datetime.fromisoformat(workflow_start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(workflow_end.replace('Z', '+00:00'))
            total_duration_ms = (end_dt - start_dt).total_seconds() * 1000
        else:
            total_duration_ms = None
        
        # Analyze by layer
        layer_performance = {}
        for step in trace_steps:
            layer = step['layer']
            if layer not in layer_performance:
                layer_performance[layer] = {
                    'total_time_ms': 0,
                    'step_count': 0,
                    'failed_steps': 0
                }
            
            if step['duration_ms']:
                layer_performance[layer]['total_time_ms'] += step['duration_ms']
            layer_performance[layer]['step_count'] += 1
            
            if step['status'] == 'failed':
                layer_performance[layer]['failed_steps'] += 1
        
        # Calculate averages
        for layer_data in layer_performance.values():
            if layer_data['step_count'] > 0:
                layer_data['average_time_ms'] = layer_data['total_time_ms'] / layer_data['step_count']
                layer_data['success_rate'] = (layer_data['step_count'] - layer_data['failed_steps']) / layer_data['step_count']
        
        return {
            'correlation_id': correlation_id,
            'total_duration_ms': total_duration_ms,
            'layer_performance': layer_performance,
            'error_count': len(correlated_data['error_logs']),
            'performance_issues': self._identify_performance_issues(correlated_data),
            'recommendations': self._generate_recommendations(correlated_data)
        }
    
    def _identify_performance_issues(self, correlated_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance issues from correlated data"""
        issues = []
        
        # Check for slow trace steps
        for step in correlated_data['trace_steps']:
            if step['duration_ms'] and step['duration_ms'] > 1000:  # Slower than 1 second
                issues.append({
                    'type': 'slow_operation',
                    'layer': step['layer'],
                    'component': step['component'],
                    'operation': step['operation'],
                    'duration_ms': step['duration_ms'],
                    'severity': 'high' if step['duration_ms'] > 5000 else 'medium'
                })
        
        # Check for high error rates
        error_count = len(correlated_data['error_logs'])
        total_operations = len(correlated_data['trace_steps'])
        
        if total_operations > 0:
            error_rate = error_count / total_operations
            if error_rate > 0.1:  # More than 10% error rate
                issues.append({
                    'type': 'high_error_rate',
                    'error_rate': error_rate,
                    'error_count': error_count,
                    'total_operations': total_operations,
                    'severity': 'critical' if error_rate > 0.5 else 'high'
                })
        
        return issues
    
    def _generate_recommendations(self, correlated_data: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on correlated data"""
        recommendations = []
        
        # Analyze performance metrics for recommendations
        db_metrics = [m for m in correlated_data['performance_metrics'] if m['layer'] == 'database']
        api_metrics = [m for m in correlated_data['performance_metrics'] if m['layer'] == 'api']
        
        # Database recommendations
        slow_queries = [m for m in db_metrics if m['metric_name'] == 'query_execution_time' and m['metric_value'] > 100]
        if slow_queries:
            recommendations.append(f"Optimize {len(slow_queries)} slow database queries (>100ms)")
        
        # API recommendations
        slow_apis = [m for m in api_metrics if m['metric_name'] == 'response_time' and m['metric_value'] > 500]
        if slow_apis:
            recommendations.append(f"Optimize {len(slow_apis)} slow API endpoints (>500ms)")
        
        # Error-based recommendations
        if correlated_data['error_logs']:
            error_types = set(error['error_type'] for error in correlated_data['error_logs'])
            recommendations.append(f"Address {len(error_types)} types of errors: {', '.join(error_types)}")
        
        return recommendations


# Global logger instances
structured_logger = StructuredLogger('debugging.system')
database_logger = DatabaseQueryLogger()
frontend_logger = FrontendLogger()
log_aggregation = LogAggregationService()