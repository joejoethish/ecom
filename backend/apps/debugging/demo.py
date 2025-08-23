#!/usr/bin/env python
"""
Demo script to showcase the E2E Workflow Debugging System functionality
"""
import os
import sys
import django
import uuid
from datetime import timedelta
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from apps.debugging.models import WorkflowSession, TraceStep, PerformanceSnapshot, ErrorLog
from apps.debugging.utils import WorkflowTracer, PerformanceMonitor, ErrorLogger
from django.contrib.auth import get_user_model

User = get_user_model()


def demo_workflow_tracing():
    """Demonstrate workflow tracing functionality"""
    print("\n=== Workflow Tracing Demo ===")
    
    # Create a test user if it doesn't exist
    user, created = User.objects.get_or_create(
        username='demo_user',
        defaults={
            'email': 'demo@example.com',
            'first_name': 'Demo',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('demo123')
        user.save()
        print(f"Created demo user: {user.username}")
    
    # Initialize workflow tracer
    tracer = WorkflowTracer()
    print(f"Correlation ID: {tracer.correlation_id}")
    
    # Start a login workflow
    workflow = tracer.start_workflow(
        workflow_type='login',
        user=user,
        metadata={
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0 (Demo Browser)',
            'session_id': 'demo_session_123'
        }
    )
    print(f"Started workflow: {workflow.workflow_type} - {workflow.correlation_id}")
    
    # Add trace steps
    steps = [
        ('frontend', 'LoginForm', 'form_submission'),
        ('api', 'AuthViewSet', 'authenticate_user'),
        ('database', 'UserModel', 'user_lookup'),
        ('api', 'JWTService', 'generate_token'),
        ('frontend', 'AuthService', 'store_token')
    ]
    
    trace_steps = []
    for layer, component, operation in steps:
        step = tracer.add_trace_step(
            workflow_session=workflow,
            layer=layer,
            component=component,
            operation=operation,
            metadata={'step_order': len(trace_steps) + 1}
        )
        trace_steps.append(step)
        print(f"Added trace step: {layer}.{component}.{operation}")
        
        # Simulate some processing time
        import time
        time.sleep(0.1)
        
        # Complete the step
        tracer.complete_trace_step(
            step,
            metadata={'success': True, 'processing_time_ms': 100}
        )
        print(f"Completed trace step: {step.id} ({step.duration_ms}ms)")
    
    # Complete the workflow
    workflow.status = 'completed'
    workflow.end_time = timezone.now()
    workflow.save()
    
    print(f"Workflow completed: {workflow.status}")
    print(f"Total trace steps: {workflow.trace_steps.count()}")


def demo_performance_monitoring():
    """Demonstrate performance monitoring functionality"""
    print("\n=== Performance Monitoring Demo ===")
    
    correlation_id = uuid.uuid4()
    
    # Record various performance metrics
    metrics = [
        ('api', 'ProductViewSet', 'response_time', 150.0),
        ('database', 'ProductQuery', 'response_time', 45.0),
        ('frontend', 'ProductList', 'response_time', 200.0),
        ('system', 'WebServer', 'memory_usage', 75.5),
        ('system', 'WebServer', 'cpu_usage', 45.2),
        ('cache', 'Redis', 'cache_hit_rate', 85.0),
    ]
    
    for layer, component, metric_name, value in metrics:
        snapshot = PerformanceMonitor.record_metric(
            layer=layer,
            component=component,
            metric_name=metric_name,
            metric_value=value,
            correlation_id=correlation_id,
            metadata={'demo': True, 'timestamp': timezone.now().isoformat()}
        )
        
        # Check thresholds
        threshold_check = PerformanceMonitor.check_thresholds(
            layer=layer,
            component=component,
            metric_name=metric_name,
            metric_value=value
        )
        
        status_color = {
            'normal': '✅',
            'warning': '⚠️',
            'critical': '🚨',
            'no_threshold': '❓'
        }.get(threshold_check['status'], '❓')
        
        print(f"{status_color} {layer}.{component} - {metric_name}: {value} ({threshold_check['status']})")


def demo_error_logging():
    """Demonstrate error logging functionality"""
    print("\n=== Error Logging Demo ===")
    
    correlation_id = uuid.uuid4()
    
    # Log various types of errors
    errors = [
        ('api', 'ProductViewSet', 'ValidationError', 'Invalid product data provided', 'warning'),
        ('database', 'MySQL', 'ConnectionError', 'Database connection timeout', 'error'),
        ('frontend', 'PaymentForm', 'NetworkError', 'Payment gateway unreachable', 'error'),
        ('system', 'WebServer', 'MemoryError', 'Out of memory condition detected', 'critical'),
    ]
    
    for layer, component, error_type, message, severity in errors:
        error_log = ErrorLogger.log_error(
            layer=layer,
            component=component,
            error_type=error_type,
            error_message=message,
            correlation_id=correlation_id,
            severity=severity,
            metadata={
                'demo': True,
                'error_code': f'ERR_{len(errors)}',
                'timestamp': timezone.now().isoformat()
            }
        )
        
        severity_icon = {
            'debug': '🐛',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }.get(severity, '❓')
        
        print(f"{severity_icon} {layer}.{component} - {error_type}: {message}")


def demo_system_stats():
    """Display system statistics"""
    print("\n=== System Statistics ===")
    
    # Workflow statistics
    total_workflows = WorkflowSession.objects.count()
    completed_workflows = WorkflowSession.objects.filter(status='completed').count()
    failed_workflows = WorkflowSession.objects.filter(status='failed').count()
    
    print(f"📊 Workflows: {total_workflows} total, {completed_workflows} completed, {failed_workflows} failed")
    
    # Performance statistics
    total_metrics = PerformanceSnapshot.objects.count()
    recent_metrics = PerformanceSnapshot.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    print(f"📈 Performance Metrics: {total_metrics} total, {recent_metrics} in last hour")
    
    # Error statistics
    total_errors = ErrorLog.objects.count()
    unresolved_errors = ErrorLog.objects.filter(resolved=False).count()
    critical_errors = ErrorLog.objects.filter(severity='critical').count()
    
    print(f"🚨 Errors: {total_errors} total, {unresolved_errors} unresolved, {critical_errors} critical")
    
    # Recent activity
    recent_workflows = WorkflowSession.objects.filter(
        start_time__gte=timezone.now() - timedelta(hours=1)
    ).order_by('-start_time')[:5]
    
    print(f"\n📋 Recent Workflows:")
    for workflow in recent_workflows:
        print(f"  - {workflow.workflow_type} ({workflow.status}) - {workflow.start_time}")


if __name__ == '__main__':
    print("🚀 E2E Workflow Debugging System Demo")
    print("=" * 50)
    
    try:
        demo_workflow_tracing()
        demo_performance_monitoring()
        demo_error_logging()
        demo_system_stats()
        
        print("\n✅ Demo completed successfully!")
        print("🔍 Check the Django admin panel to view the debugging data:")
        print("   - Workflow Sessions")
        print("   - Trace Steps")
        print("   - Performance Snapshots")
        print("   - Error Logs")
        print("   - Debug Configurations")
        print("   - Performance Thresholds")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()