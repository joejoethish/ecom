"""
Simple test for workflow tracing functionality
"""

import uuid
import time
from django.test import TestCase
from django.contrib.auth.models import User

from .services import WorkflowSessionManager, WorkflowTracingEngine
from .models import WorkflowSession, TraceStep


class SimpleWorkflowTracingTest(TestCase):
    """Simple test for workflow tracing"""
    
    def test_workflow_session_creation(self):
        """Test basic workflow session creation"""
        correlation_id = uuid.uuid4()
        session_manager = WorkflowSessionManager(correlation_id)
        
        session = session_manager.start_session('test_workflow')
        
        self.assertEqual(session.correlation_id, correlation_id)
        self.assertEqual(session.workflow_type, 'test_workflow')
        self.assertEqual(session.status, 'in_progress')
        
        # Verify session exists in database
        db_session = WorkflowSession.objects.get(correlation_id=correlation_id)
        self.assertEqual(db_session.workflow_type, 'test_workflow')
    
    def test_complete_workflow_trace(self):
        """Test complete workflow tracing"""
        engine = WorkflowTracingEngine()
        
        # Start workflow
        session = engine.start_workflow('simple_test')
        
        # Add a trace step
        with engine.trace_step('api', 'TestView', 'process') as step:
            time.sleep(0.01)  # Simulate some work
            step.add_metadata({'test': 'data'})
        
        # Complete workflow
        analysis = engine.complete_workflow()
        
        # Verify analysis
        self.assertEqual(analysis['session']['status'], 'completed')
        self.assertEqual(analysis['summary']['total_steps'], 1)
        self.assertEqual(analysis['summary']['failed_steps'], 0)
        
        # Verify timing analysis
        timing = analysis['timing_analysis']
        self.assertEqual(timing['step_count'], 1)
        self.assertIn('api', timing['layers'])


if __name__ == '__main__':
    import django
    import os
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
    django.setup()
    
    import unittest
    unittest.main()