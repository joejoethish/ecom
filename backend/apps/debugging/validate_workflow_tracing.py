#!/usr/bin/env python
"""
Validation script for workflow tracing functionality
"""

import os
import sys
import django
import uuid
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from apps.debugging.services import WorkflowSessionManager, WorkflowTracingEngine
from apps.debugging.models import WorkflowSession, TraceStep


def test_workflow_session_manager():
    """Test workflow session manager"""
    print("Testing WorkflowSessionManager...")
    
    correlation_id = uuid.uuid4()
    session_manager = WorkflowSessionManager(correlation_id)
    
    # Start session
    session = session_manager.start_session('test_workflow')
    print(f"✓ Created session: {session.correlation_id}")
    
    # Complete session
    completed_session = session_manager.complete_session({'test': 'completed'})
    print(f"✓ Completed session: {completed_session.status}")
    
    return True


def test_workflow_tracing_engine():
    """Test complete workflow tracing engine"""
    print("\nTesting WorkflowTracingEngine...")
    
    engine = WorkflowTracingEngine()
    
    # Start workflow
    session = engine.start_workflow('validation_test')
    print(f"✓ Started workflow: {session.correlation_id}")
    
    # Add trace steps
    with engine.trace_step('frontend', 'TestComponent', 'render') as step:
        time.sleep(0.01)
        step.add_metadata({'component': 'TestComponent'})
    print("✓ Added frontend trace step")
    
    with engine.trace_step('api', 'TestView', 'process') as step:
        time.sleep(0.02)
        step.add_metadata({'view': 'TestView'})
    print("✓ Added API trace step")
    
    with engine.trace_step('database', 'TestModel', 'query') as step:
        time.sleep(0.005)
        step.add_metadata({'model': 'TestModel'})
    print("✓ Added database trace step")
    
    # Complete workflow
    analysis = engine.complete_workflow()
    print(f"✓ Completed workflow with {analysis['summary']['total_steps']} steps")
    
    # Verify analysis structure
    assert 'session' in analysis
    assert 'timing_analysis' in analysis
    assert 'error_analysis' in analysis
    assert 'summary' in analysis
    print("✓ Analysis structure is correct")
    
    # Verify timing analysis
    timing = analysis['timing_analysis']
    assert timing['step_count'] == 3
    assert 'frontend' in timing['layers']
    assert 'api' in timing['layers']
    assert 'database' in timing['layers']
    print("✓ Timing analysis is correct")
    
    return True


def test_error_tracking():
    """Test error tracking functionality"""
    print("\nTesting error tracking...")
    
    engine = WorkflowTracingEngine()
    session = engine.start_workflow('error_test')
    
    # Track an error
    engine.error_tracker.track_error(
        layer='api',
        component='TestView',
        error_type='ValidationError',
        error_message='Test error message'
    )
    print("✓ Tracked error")
    
    # Get error analysis
    error_analysis = engine.error_tracker.analyze_error_patterns()
    assert error_analysis['error_count'] == 1
    assert 'api' in error_analysis['layers_affected']
    print("✓ Error analysis is correct")
    
    # Fail workflow
    analysis = engine.fail_workflow('Test failure')
    assert analysis['session']['status'] == 'failed'
    print("✓ Failed workflow correctly")
    
    return True


def test_database_models():
    """Test database model creation and queries"""
    print("\nTesting database models...")
    
    # Count existing records
    workflow_count = WorkflowSession.objects.count()
    step_count = TraceStep.objects.count()
    
    print(f"✓ Found {workflow_count} workflow sessions")
    print(f"✓ Found {step_count} trace steps")
    
    # Test recent workflows
    recent_workflows = WorkflowSession.objects.filter(
        workflow_type__in=['test_workflow', 'validation_test', 'error_test']
    ).order_by('-start_time')[:5]
    
    print(f"✓ Found {recent_workflows.count()} recent test workflows")
    
    for workflow in recent_workflows:
        steps = workflow.trace_steps.count()
        print(f"  - {workflow.workflow_type}: {steps} steps, status: {workflow.status}")
    
    return True


def main():
    """Run all validation tests"""
    print("=== Workflow Tracing Validation ===\n")
    
    try:
        # Run tests
        test_workflow_session_manager()
        test_workflow_tracing_engine()
        test_error_tracking()
        test_database_models()
        
        print("\n=== All Tests Passed! ===")
        print("✓ Workflow session management works correctly")
        print("✓ Workflow tracing engine works correctly")
        print("✓ Error tracking works correctly")
        print("✓ Database models work correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)