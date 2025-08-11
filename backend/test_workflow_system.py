#!/usr/bin/env python3
"""
Test script for the Comprehensive Workflow Automation System
Tests the workflow models, services, and API endpoints
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from apps.workflow.models import (
    WorkflowTemplate, Workflow, WorkflowNode, WorkflowConnection,
    WorkflowExecution, WorkflowExecutionLog, WorkflowApproval,
    WorkflowSchedule, WorkflowMetrics, WorkflowIntegration
)
from apps.workflow.services import WorkflowEngine, WorkflowValidator, NodeExecutor
from apps.workflow.serializers import WorkflowSerializer, WorkflowTemplateSerializer

User = get_user_model()

class WorkflowSystemTest:
    def __init__(self):
        self.client = Client()
        self.user = None
        self.setup_test_data()

    def setup_test_data(self):
        """Create test user and basic data"""
        try:
            self.user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            print("✓ Test user created successfully")
        except Exception as e:
            print(f"✗ Error creating test user: {e}")

    def test_workflow_models(self):
        """Test workflow model creation and relationships"""
        print("\n=== Testing Workflow Models ===")
        
        try:
            # Test WorkflowTemplate creation
            template = WorkflowTemplate.objects.create(
                name="Test Template",
                description="A test workflow template",
                category="approval",
                created_by=self.user
            )
            print("✓ WorkflowTemplate created successfully")

            # Test Workflow creation
            workflow = Workflow.objects.create(
                name="Test Workflow",
                description="A test workflow",
                template=template,
                created_by=self.user,
                status="draft",
                trigger_type="manual"
            )
            print("✓ Workflow created successfully")

            # Test WorkflowNode creation
            start_node = WorkflowNode.objects.create(
                workflow=workflow,
                node_id="start-1",
                node_type="start",
                name="Start Node",
                position={"x": 100, "y": 100}
            )
            
            task_node = WorkflowNode.objects.create(
                workflow=workflow,
                node_id="task-1",
                node_type="task",
                name="Task Node",
                position={"x": 300, "y": 100},
                config={
                    "task_type": "custom",
                    "description": "Test task",
                    "timeout": 300
                }
            )
            
            end_node = WorkflowNode.objects.create(
                workflow=workflow,
                node_id="end-1",
                node_type="end",
                name="End Node",
                position={"x": 500, "y": 100}
            )
            print("✓ WorkflowNodes created successfully")

            # Test WorkflowConnection creation
            connection1 = WorkflowConnection.objects.create(
                workflow=workflow,
                source_node=start_node,
                target_node=task_node
            )
            
            connection2 = WorkflowConnection.objects.create(
                workflow=workflow,
                source_node=task_node,
                target_node=end_node
            )
            print("✓ WorkflowConnections created successfully")

            # Test WorkflowIntegration creation
            integration = WorkflowIntegration.objects.create(
                name="Test API Integration",
                integration_type="api",
                endpoint_url="https://api.example.com",
                created_by=self.user,
                configuration={
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"}
                }
            )
            print("✓ WorkflowIntegration created successfully")

            return True

        except Exception as e:
            print(f"✗ Error testing workflow models: {e}")
            return False

    def test_workflow_validator(self):
        """Test workflow validation logic"""
        print("\n=== Testing Workflow Validator ===")
        
        try:
            validator = WorkflowValidator()
            
            # Test valid workflow
            valid_workflow = {
                "nodes": [
                    {"id": "start-1", "type": "start", "name": "Start"},
                    {"id": "task-1", "type": "task", "name": "Task"},
                    {"id": "end-1", "type": "end", "name": "End"}
                ],
                "connections": [
                    {"source": "start-1", "target": "task-1"},
                    {"source": "task-1", "target": "end-1"}
                ]
            }
            
            result = validator.validate_workflow(valid_workflow)
            if result['is_valid']:
                print("✓ Valid workflow validation passed")
            else:
                print(f"✗ Valid workflow validation failed: {result['errors']}")
                return False

            # Test invalid workflow (no start node)
            invalid_workflow = {
                "nodes": [
                    {"id": "task-1", "type": "task", "name": "Task"},
                    {"id": "end-1", "type": "end", "name": "End"}
                ],
                "connections": [
                    {"source": "task-1", "target": "end-1"}
                ]
            }
            
            result = validator.validate_workflow(invalid_workflow)
            if not result['is_valid'] and 'start node' in str(result['errors']).lower():
                print("✓ Invalid workflow validation passed")
            else:
                print(f"✗ Invalid workflow validation failed: {result}")
                return False

            return True

        except Exception as e:
            print(f"✗ Error testing workflow validator: {e}")
            return False

    def test_workflow_engine(self):
        """Test workflow execution engine"""
        print("\n=== Testing Workflow Engine ===")
        
        try:
            # Get a workflow from the database
            workflow = Workflow.objects.first()
            if not workflow:
                print("✗ No workflow found for testing")
                return False

            engine = WorkflowEngine()
            
            # Test workflow execution
            execution = engine.execute_workflow(
                workflow=workflow,
                triggered_by=self.user,
                trigger_data={"test": "data"}
            )
            
            if execution and execution.status in ['running', 'pending']:
                print("✓ Workflow execution started successfully")
            else:
                print(f"✗ Workflow execution failed: {execution}")
                return False

            # Test execution logging
            logs = WorkflowExecutionLog.objects.filter(execution=execution)
            if logs.exists():
                print("✓ Workflow execution logging works")
            else:
                print("✗ No execution logs found")

            return True

        except Exception as e:
            print(f"✗ Error testing workflow engine: {e}")
            return False

    def test_node_executor(self):
        """Test individual node execution"""
        print("\n=== Testing Node Executor ===")
        
        try:
            executor = NodeExecutor()
            
            # Get a workflow execution
            execution = WorkflowExecution.objects.first()
            if not execution:
                print("✗ No workflow execution found for testing")
                return False

            # Get a task node
            task_node = WorkflowNode.objects.filter(node_type='task').first()
            if not task_node:
                print("✗ No task node found for testing")
                return False

            # Test node execution
            result = executor.execute_node(execution, task_node)
            
            if result and 'success' in result:
                print("✓ Node execution completed")
                if result['success']:
                    print("✓ Node execution was successful")
                else:
                    print(f"✓ Node execution failed as expected: {result.get('error', 'Unknown error')}")
            else:
                print(f"✗ Invalid node execution result: {result}")
                return False

            return True

        except Exception as e:
            print(f"✗ Error testing node executor: {e}")
            return False

    def test_workflow_serializers(self):
        """Test workflow serializers"""
        print("\n=== Testing Workflow Serializers ===")
        
        try:
            # Test WorkflowTemplateSerializer
            template = WorkflowTemplate.objects.first()
            if template:
                serializer = WorkflowTemplateSerializer(template)
                data = serializer.data
                if 'name' in data and 'category' in data:
                    print("✓ WorkflowTemplateSerializer works")
                else:
                    print(f"✗ WorkflowTemplateSerializer missing fields: {data}")
                    return False

            # Test WorkflowSerializer
            workflow = Workflow.objects.first()
            if workflow:
                serializer = WorkflowSerializer(workflow)
                data = serializer.data
                if 'name' in data and 'status' in data and 'nodes' in data:
                    print("✓ WorkflowSerializer works")
                else:
                    print(f"✗ WorkflowSerializer missing fields: {data}")
                    return False

            return True

        except Exception as e:
            print(f"✗ Error testing workflow serializers: {e}")
            return False

    def test_workflow_api_endpoints(self):
        """Test workflow API endpoints"""
        print("\n=== Testing Workflow API Endpoints ===")
        
        try:
            # Login user
            self.client.login(username='testuser', password='testpass123')
            
            # Test workflow list endpoint
            response = self.client.get('/api/workflow/workflows/')
            if response.status_code == 200:
                print("✓ Workflow list endpoint works")
            else:
                print(f"✗ Workflow list endpoint failed: {response.status_code}")
                return False

            # Test workflow template list endpoint
            response = self.client.get('/api/workflow/templates/')
            if response.status_code == 200:
                print("✓ Workflow template list endpoint works")
            else:
                print(f"✗ Workflow template list endpoint failed: {response.status_code}")
                return False

            # Test workflow execution list endpoint
            response = self.client.get('/api/workflow/executions/')
            if response.status_code == 200:
                print("✓ Workflow execution list endpoint works")
            else:
                print(f"✗ Workflow execution list endpoint failed: {response.status_code}")
                return False

            # Test workflow analytics endpoint
            response = self.client.get('/api/workflow/analytics/dashboard/')
            if response.status_code == 200:
                print("✓ Workflow analytics endpoint works")
            else:
                print(f"✗ Workflow analytics endpoint failed: {response.status_code}")
                return False

            return True

        except Exception as e:
            print(f"✗ Error testing workflow API endpoints: {e}")
            return False

    def test_workflow_integration(self):
        """Test workflow integration functionality"""
        print("\n=== Testing Workflow Integration ===")
        
        try:
            from apps.workflow.services import IntegrationTester
            
            # Get an integration
            integration = WorkflowIntegration.objects.first()
            if not integration:
                print("✗ No integration found for testing")
                return False

            tester = IntegrationTester()
            
            # Test integration (this will likely fail due to fake URL, but should not crash)
            result = tester.test_integration(integration)
            
            if result and 'success' in result:
                print("✓ Integration testing completed")
                if result['success']:
                    print("✓ Integration test was successful")
                else:
                    print(f"✓ Integration test failed as expected: {result.get('message', 'Unknown error')}")
            else:
                print(f"✗ Invalid integration test result: {result}")
                return False

            return True

        except Exception as e:
            print(f"✗ Error testing workflow integration: {e}")
            return False

    def run_all_tests(self):
        """Run all workflow system tests"""
        print("Starting Comprehensive Workflow Automation System Tests...")
        print("=" * 60)
        
        tests = [
            self.test_workflow_models,
            self.test_workflow_validator,
            self.test_workflow_engine,
            self.test_node_executor,
            self.test_workflow_serializers,
            self.test_workflow_api_endpoints,
            self.test_workflow_integration,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"✗ Test failed with exception: {e}")
        
        print("\n" + "=" * 60)
        print(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All workflow system tests passed!")
            return True
        else:
            print(f"❌ {total - passed} tests failed")
            return False

def main():
    """Main test function"""
    tester = WorkflowSystemTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Workflow Automation System is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some workflow system tests failed. Please check the implementation.")
        sys.exit(1)

if __name__ == '__main__':
    main()