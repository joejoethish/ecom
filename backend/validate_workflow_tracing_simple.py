#!/usr/bin/env python
"""
Simple validation for workflow tracing using Django shell
"""

import os
import sys
import subprocess

def run_django_command(command):
    """Run a Django management command"""
    try:
        result = subprocess.run([
            'python', 'manage.py', 'shell', '-c', command
        ], capture_output=True, text=True, cwd='backend')
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)

def main():
    """Run validation tests"""
    print("=== Workflow Tracing Validation ===\n")
    
    tests = [
        {
            'name': 'Import Services',
            'command': '''
from apps.debugging.services import WorkflowTracingEngine, WorkflowSessionManager
print("✓ Services imported successfully")
'''
        },
        {
            'name': 'Import Models',
            'command': '''
from apps.debugging.models import WorkflowSession, TraceStep, PerformanceSnapshot, ErrorLog
print("✓ Models imported successfully")
'''
        },
        {
            'name': 'Create Workflow Session',
            'command': '''
import uuid
from apps.debugging.services import WorkflowSessionManager
correlation_id = uuid.uuid4()
manager = WorkflowSessionManager(correlation_id)
session = manager.start_session("test_workflow")
print(f"✓ Created session: {session.workflow_type}")
'''
        },
        {
            'name': 'Complete Workflow Trace',
            'command': '''
import time
from apps.debugging.services import WorkflowTracingEngine
engine = WorkflowTracingEngine()
session = engine.start_workflow("validation_test")
with engine.trace_step("api", "TestView", "process") as step:
    time.sleep(0.01)
    step.add_metadata({"test": "data"})
analysis = engine.complete_workflow()
print(f"✓ Completed workflow with {analysis['summary']['total_steps']} steps")
'''
        },
        {
            'name': 'Database Query',
            'command': '''
from apps.debugging.models import WorkflowSession
count = WorkflowSession.objects.count()
print(f"✓ Found {count} workflow sessions in database")
'''
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"Running: {test['name']}")
        success, output = run_django_command(test['command'])
        
        if success:
            print(f"  {output}")
            passed += 1
        else:
            print(f"  ❌ Failed: {output}")
            failed += 1
        print()
    
    print("=== Results ===")
    print(f"✓ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All workflow tracing components are working correctly!")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Check the implementation.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)