"""
Workflow Tracing Engine Services

This module provides comprehensive workflow tracing capabilities across
frontend, API, and database layers with correlation ID tracking, timing
analysis, and error correlation.
"""

import uuid
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction, connection
from django.contrib.auth.models import User
from django.core.cache import cache

from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, PerformanceThreshold
)
from .utils import WorkflowTracer, PerformanceMonitor, ErrorLogger

logger = logging.getLogger(__name__)


class WorkflowSessionManager:
    """Manages workflow sessions with correlation ID tracking"""
    
    def __init__(self, correlation_id: Optional[uuid.UUID] = None):
        self.correlation_id = correlation_id or uuid.uuid4()
        self._session = None
    
    def start_session(self, workflow_type: str, user: Optional[User] = None, 
                     session_key: Optional[str] = None, metadata: Optional[Dict] = None) -> WorkflowSession:
        """Start a new workflow session"""
        try:
            self._session = WorkflowSession.objects.create(
                correlation_id=self.correlation_id,
                workflow_type=workflow_type,
                user=user,
                session_key=session_key,
                status='in_progress',
                metadata=metadata or {}
            )
            
            logger.info(f"Started workflow session {self.correlation_id} for {workflow_type}")
            return self._session
            
        except Exception as e:
            ErrorLogger.log_exception(
                exception=e,
                layer='api',
                component='WorkflowSessionManager',
                correlation_id=self.correlation_id,
                metadata={'workflow_type': workflow_type}
            )
            raise
    
    def get_session(self) -> Optional[WorkflowSession]:
        """Get current workflow session"""
        if not self._session:
            try:
                self._session = WorkflowSession.objects.get(
                    correlation_id=self.correlation_id,
                    status='in_progress'
                )
            except WorkflowSession.DoesNotExist:
                return None
        return self._session
    
    def complete_session(self, metadata: Optional[Dict] = None) -> WorkflowSession:
        """Complete the workflow session"""
        session = self.get_session()
        if not session:
            raise ValueError(f"No active session found for correlation ID {self.correlation_id}")
        
        session.status = 'completed'
        session.end_time = timezone.now()
        
        if metadata:
            session.metadata.update(metadata)
        
        session.save()
        
        logger.info(f"Completed workflow session {self.correlation_id}")
        return session
    
    def fail_session(self, error_message: str, metadata: Optional[Dict] = None) -> WorkflowSession:
        """Mark the workflow session as failed"""
        session = self.get_session()
        if not session:
            raise ValueError(f"No active session found for correlation ID {self.correlation_id}")
        
        session.status = 'failed'
        session.end_time = timezone.now()
        session.metadata.update({
            'error_message': error_message,
            **(metadata or {})
        })
        
        session.save()
        
        logger.error(f"Failed workflow session {self.correlation_id}: {error_message}")
        return session


class TraceStepRecorder:
    """Records individual trace steps within workflows"""
    
    def __init__(self, session_manager: WorkflowSessionManager):
        self.session_manager = session_manager
        self._active_steps: Dict[str, TraceStep] = {}
    
    def start_step(self, layer: str, component: str, operation: str, 
                   metadata: Optional[Dict] = None) -> TraceStep:
        """Start recording a trace step"""
        session = self.session_manager.get_session()
        if not session:
            raise ValueError("No active workflow session")
        
        step_key = f"{layer}.{component}.{operation}"
        
        try:
            trace_step = TraceStep.objects.create(
                workflow_session=session,
                layer=layer,
                component=component,
                operation=operation,
                start_time=timezone.now(),
                status='started',
                metadata=metadata or {}
            )
            
            self._active_steps[step_key] = trace_step
            
            logger.debug(f"Started trace step {step_key} for session {session.correlation_id}")
            return trace_step
            
        except Exception as e:
            ErrorLogger.log_exception(
                exception=e,
                layer='api',
                component='TraceStepRecorder',
                correlation_id=session.correlation_id,
                metadata={'step_key': step_key}
            )
            raise
    
    def complete_step(self, layer: str, component: str, operation: str, 
                     metadata: Optional[Dict] = None) -> TraceStep:
        """Complete a trace step"""
        step_key = f"{layer}.{component}.{operation}"
        trace_step = self._active_steps.get(step_key)
        
        if not trace_step:
            # Try to find the step in the database
            session = self.session_manager.get_session()
            if session:
                trace_step = TraceStep.objects.filter(
                    workflow_session=session,
                    layer=layer,
                    component=component,
                    operation=operation,
                    status='started'
                ).order_by('-start_time').first()
        
        if not trace_step:
            logger.warning(f"No active trace step found for {step_key}")
            return None
        
        trace_step.status = 'completed'
        trace_step.end_time = timezone.now()
        
        if trace_step.start_time:
            delta = trace_step.end_time - trace_step.start_time
            trace_step.duration_ms = int(delta.total_seconds() * 1000)
        
        if metadata:
            trace_step.metadata.update(metadata)
        
        trace_step.save()
        
        # Remove from active steps
        if step_key in self._active_steps:
            del self._active_steps[step_key]
        
        logger.debug(f"Completed trace step {step_key} in {trace_step.duration_ms}ms")
        return trace_step
    
    def fail_step(self, layer: str, component: str, operation: str, 
                  error_message: str, metadata: Optional[Dict] = None) -> TraceStep:
        """Mark a trace step as failed"""
        step_key = f"{layer}.{component}.{operation}"
        trace_step = self._active_steps.get(step_key)
        
        if not trace_step:
            # Try to find the step in the database
            session = self.session_manager.get_session()
            if session:
                trace_step = TraceStep.objects.filter(
                    workflow_session=session,
                    layer=layer,
                    component=component,
                    operation=operation,
                    status='started'
                ).order_by('-start_time').first()
        
        if not trace_step:
            logger.warning(f"No active trace step found for {step_key}")
            return None
        
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
        
        # Remove from active steps
        if step_key in self._active_steps:
            del self._active_steps[step_key]
        
        logger.error(f"Failed trace step {step_key}: {error_message}")
        return trace_step


class TimingAnalyzer:
    """Analyzes response times and performance across workflow steps"""
    
    def __init__(self, correlation_id: uuid.UUID):
        self.correlation_id = correlation_id
    
    def analyze_workflow_timing(self) -> Dict[str, Any]:
        """Analyze timing for complete workflow"""
        try:
            session = WorkflowSession.objects.get(correlation_id=self.correlation_id)
            steps = TraceStep.objects.filter(workflow_session=session).order_by('start_time')
            
            if not steps.exists():
                return {'error': 'No trace steps found'}
            
            analysis = {
                'workflow_type': session.workflow_type,
                'correlation_id': str(self.correlation_id),
                'total_duration_ms': 0,
                'step_count': steps.count(),
                'layers': {},
                'bottlenecks': [],
                'performance_issues': []
            }
            
            # Calculate total workflow duration
            if session.end_time and session.start_time:
                total_delta = session.end_time - session.start_time
                analysis['total_duration_ms'] = int(total_delta.total_seconds() * 1000)
            
            # Analyze each layer
            layer_stats = {}
            for step in steps:
                layer = step.layer
                if layer not in layer_stats:
                    layer_stats[layer] = {
                        'total_duration_ms': 0,
                        'step_count': 0,
                        'avg_duration_ms': 0,
                        'max_duration_ms': 0,
                        'min_duration_ms': float('inf'),
                        'steps': []
                    }
                
                duration = step.duration_ms or 0
                layer_stats[layer]['total_duration_ms'] += duration
                layer_stats[layer]['step_count'] += 1
                layer_stats[layer]['max_duration_ms'] = max(layer_stats[layer]['max_duration_ms'], duration)
                layer_stats[layer]['min_duration_ms'] = min(layer_stats[layer]['min_duration_ms'], duration)
                layer_stats[layer]['steps'].append({
                    'component': step.component,
                    'operation': step.operation,
                    'duration_ms': duration,
                    'status': step.status
                })
            
            # Calculate averages and identify bottlenecks
            for layer, stats in layer_stats.items():
                if stats['step_count'] > 0:
                    stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['step_count']
                    if stats['min_duration_ms'] == float('inf'):
                        stats['min_duration_ms'] = 0
                
                # Identify bottlenecks (steps taking >80% of layer time)
                if stats['max_duration_ms'] > 0:
                    threshold = stats['total_duration_ms'] * 0.8
                    for step_info in stats['steps']:
                        if step_info['duration_ms'] >= threshold:
                            analysis['bottlenecks'].append({
                                'layer': layer,
                                'component': step_info['component'],
                                'operation': step_info['operation'],
                                'duration_ms': step_info['duration_ms'],
                                'percentage': (step_info['duration_ms'] / stats['total_duration_ms']) * 100
                            })
            
            analysis['layers'] = layer_stats
            
            # Check for performance issues
            analysis['performance_issues'] = self._identify_performance_issues(steps)
            
            return analysis
            
        except WorkflowSession.DoesNotExist:
            return {'error': f'Workflow session not found for correlation ID {self.correlation_id}'}
        except Exception as e:
            logger.error(f"Error analyzing workflow timing: {e}")
            return {'error': str(e)}
    
    def _identify_performance_issues(self, steps) -> List[Dict[str, Any]]:
        """Identify performance issues in workflow steps"""
        issues = []
        
        # Check against performance thresholds
        thresholds = PerformanceThreshold.objects.filter(
            metric_name='response_time',
            enabled=True
        )
        
        threshold_map = {}
        for threshold in thresholds:
            key = f"{threshold.layer}.{threshold.component or '*'}"
            threshold_map[key] = threshold
        
        for step in steps:
            if not step.duration_ms:
                continue
            
            # Check specific component threshold
            threshold_key = f"{step.layer}.{step.component}"
            threshold = threshold_map.get(threshold_key)
            
            # Check layer-wide threshold if no specific threshold
            if not threshold:
                threshold_key = f"{step.layer}.*"
                threshold = threshold_map.get(threshold_key)
            
            if threshold:
                if step.duration_ms >= threshold.critical_threshold:
                    issues.append({
                        'type': 'critical_threshold_exceeded',
                        'layer': step.layer,
                        'component': step.component,
                        'operation': step.operation,
                        'duration_ms': step.duration_ms,
                        'threshold_ms': threshold.critical_threshold,
                        'severity': 'critical'
                    })
                elif step.duration_ms >= threshold.warning_threshold:
                    issues.append({
                        'type': 'warning_threshold_exceeded',
                        'layer': step.layer,
                        'component': step.component,
                        'operation': step.operation,
                        'duration_ms': step.duration_ms,
                        'threshold_ms': threshold.warning_threshold,
                        'severity': 'warning'
                    })
        
        return issues


class ErrorTracker:
    """Tracks and correlates errors across the stack"""
    
    def __init__(self, correlation_id: uuid.UUID):
        self.correlation_id = correlation_id
    
    def track_error(self, layer: str, component: str, error_type: str, 
                   error_message: str, severity: str = 'error',
                   stack_trace: Optional[str] = None, metadata: Optional[Dict] = None) -> ErrorLog:
        """Track an error with correlation ID"""
        return ErrorLogger.log_error(
            layer=layer,
            component=component,
            error_type=error_type,
            error_message=error_message,
            correlation_id=self.correlation_id,
            severity=severity,
            stack_trace=stack_trace,
            metadata=metadata
        )
    
    def get_correlated_errors(self) -> List[ErrorLog]:
        """Get all errors correlated with this workflow"""
        return ErrorLog.objects.filter(
            correlation_id=self.correlation_id
        ).order_by('timestamp')
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns for this correlation ID"""
        errors = self.get_correlated_errors()
        
        if not errors:
            return {'error_count': 0, 'patterns': []}
        
        analysis = {
            'error_count': len(errors),
            'layers_affected': set(),
            'error_types': {},
            'severity_distribution': {},
            'timeline': [],
            'patterns': []
        }
        
        for error in errors:
            analysis['layers_affected'].add(error.layer)
            
            # Count error types
            if error.error_type not in analysis['error_types']:
                analysis['error_types'][error.error_type] = 0
            analysis['error_types'][error.error_type] += 1
            
            # Count severity levels
            if error.severity not in analysis['severity_distribution']:
                analysis['severity_distribution'][error.severity] = 0
            analysis['severity_distribution'][error.severity] += 1
            
            # Build timeline
            analysis['timeline'].append({
                'timestamp': error.timestamp.isoformat(),
                'layer': error.layer,
                'component': error.component,
                'error_type': error.error_type,
                'severity': error.severity,
                'message': error.error_message[:100]  # Truncate for overview
            })
        
        # Convert sets to lists for JSON serialization
        analysis['layers_affected'] = list(analysis['layers_affected'])
        
        # Identify patterns
        if len(errors) > 1:
            # Check for cascading errors (errors in sequence across layers)
            if len(analysis['layers_affected']) > 1:
                analysis['patterns'].append({
                    'type': 'cascading_errors',
                    'description': f"Errors cascaded across {len(analysis['layers_affected'])} layers",
                    'layers': analysis['layers_affected']
                })
            
            # Check for repeated error types
            for error_type, count in analysis['error_types'].items():
                if count > 1:
                    analysis['patterns'].append({
                        'type': 'repeated_error',
                        'description': f"Error type '{error_type}' occurred {count} times",
                        'error_type': error_type,
                        'count': count
                    })
        
        return analysis


class WorkflowTracingEngine:
    """Main workflow tracing engine that coordinates all tracing components"""
    
    def __init__(self, correlation_id: Optional[uuid.UUID] = None):
        self.correlation_id = correlation_id or uuid.uuid4()
        self.session_manager = WorkflowSessionManager(self.correlation_id)
        self.step_recorder = TraceStepRecorder(self.session_manager)
        self.timing_analyzer = TimingAnalyzer(self.correlation_id)
        self.error_tracker = ErrorTracker(self.correlation_id)
    
    def start_workflow(self, workflow_type: str, user: Optional[User] = None,
                      session_key: Optional[str] = None, metadata: Optional[Dict] = None) -> WorkflowSession:
        """Start a complete workflow trace"""
        return self.session_manager.start_session(workflow_type, user, session_key, metadata)
    
    def trace_step(self, layer: str, component: str, operation: str, metadata: Optional[Dict] = None):
        """Context manager for tracing a step"""
        return WorkflowStepContext(self.step_recorder, layer, component, operation, metadata)
    
    def complete_workflow(self, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Complete workflow and return comprehensive analysis"""
        session = self.session_manager.complete_session(metadata)
        
        # Generate comprehensive analysis
        timing_analysis = self.timing_analyzer.analyze_workflow_timing()
        error_analysis = self.error_tracker.analyze_error_patterns()
        
        return {
            'session': {
                'correlation_id': str(session.correlation_id),
                'workflow_type': session.workflow_type,
                'status': session.status,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'metadata': session.metadata
            },
            'timing_analysis': timing_analysis,
            'error_analysis': error_analysis,
            'summary': {
                'total_steps': TraceStep.objects.filter(workflow_session=session).count(),
                'failed_steps': TraceStep.objects.filter(workflow_session=session, status='failed').count(),
                'total_errors': len(error_analysis.get('timeline', [])),
                'performance_issues': len(timing_analysis.get('performance_issues', []))
            }
        }
    
    def fail_workflow(self, error_message: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Fail workflow and return analysis"""
        session = self.session_manager.fail_session(error_message, metadata)
        
        # Generate analysis for failed workflow
        timing_analysis = self.timing_analyzer.analyze_workflow_timing()
        error_analysis = self.error_tracker.analyze_error_patterns()
        
        return {
            'session': {
                'correlation_id': str(session.correlation_id),
                'workflow_type': session.workflow_type,
                'status': session.status,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'metadata': session.metadata
            },
            'timing_analysis': timing_analysis,
            'error_analysis': error_analysis,
            'failure_summary': {
                'error_message': error_message,
                'total_steps': TraceStep.objects.filter(workflow_session=session).count(),
                'completed_steps': TraceStep.objects.filter(workflow_session=session, status='completed').count(),
                'failed_steps': TraceStep.objects.filter(workflow_session=session, status='failed').count(),
                'total_errors': len(error_analysis.get('timeline', []))
            }
        }


class WorkflowStepContext:
    """Context manager for tracing individual workflow steps"""
    
    def __init__(self, step_recorder: TraceStepRecorder, layer: str, 
                 component: str, operation: str, metadata: Optional[Dict] = None):
        self.step_recorder = step_recorder
        self.layer = layer
        self.component = component
        self.operation = operation
        self.metadata = metadata or {}
        self.trace_step = None
    
    def __enter__(self):
        self.trace_step = self.step_recorder.start_step(
            self.layer, self.component, self.operation, self.metadata
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # No exception, complete the step
            self.step_recorder.complete_step(
                self.layer, self.component, self.operation, self.metadata
            )
        else:
            # Exception occurred, fail the step
            error_message = str(exc_val) if exc_val else "Unknown error"
            self.step_recorder.fail_step(
                self.layer, self.component, self.operation, 
                error_message, self.metadata
            )
        
        return False  # Don't suppress exceptions
    
    def add_metadata(self, metadata: Dict[str, Any]):
        """Add metadata to the current step"""
        self.metadata.update(metadata)
        if self.trace_step:
            self.trace_step.metadata.update(metadata)
            self.trace_step