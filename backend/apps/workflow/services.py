import json
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from .models import (
    Workflow, WorkflowExecution, WorkflowExecutionLog,
    WorkflowApproval, WorkflowNode, WorkflowConnection,
    WorkflowIntegration
)

class WorkflowEngine:
    """Core workflow execution engine"""
    
    def execute_workflow(self, workflow, triggered_by=None, trigger_data=None):
        """Execute a workflow"""
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            triggered_by=triggered_by,
            trigger_data=trigger_data or {},
            status='running',
            started_at=timezone.now()
        )
        
        # Log execution start
        self._log_execution(execution, 'info', 'Workflow execution started')
        
        # Find start node
        start_node = workflow.nodes.filter(node_type='start').first()
        if not start_node:
            self._fail_execution(execution, 'No start node found')
            return execution
        
        # Execute workflow asynchronously
        execute_workflow_task.delay(execution.id, start_node.id)
        
        return execution
    
    def retry_execution(self, failed_execution):
        """Retry a failed execution"""
        new_execution = WorkflowExecution.objects.create(
            workflow=failed_execution.workflow,
            triggered_by=failed_execution.triggered_by,
            trigger_data=failed_execution.trigger_data,
            status='running',
            started_at=timezone.now()
        )
        
        self._log_execution(new_execution, 'info', f'Retrying failed execution {failed_execution.id}')
        
        # Find start node and execute
        start_node = failed_execution.workflow.nodes.filter(node_type='start').first()
        execute_workflow_task.delay(new_execution.id, start_node.id)
        
        return new_execution
    
    def continue_execution_after_approval(self, approval):
        """Continue execution after approval"""
        execution = approval.execution
        if execution.status == 'paused':
            execution.status = 'running'
            execution.save()
            
            # Find next nodes after approval node
            next_connections = approval.node.outgoing_connections.all()
            for connection in next_connections:
                if self._evaluate_connection_condition(connection, execution.execution_data):
                    execute_node_task.delay(execution.id, connection.target_node.id)
                    break
    
    def handle_approval_rejection(self, approval):
        """Handle approval rejection"""
        execution = approval.execution
        execution.status = 'failed'
        execution.completed_at = timezone.now()
        execution.save()
        
        self._log_execution(execution, 'error', f'Execution failed due to approval rejection: {approval.comments}')
    
    def _log_execution(self, execution, level, message, data=None, node=None):
        """Log execution event"""
        WorkflowExecutionLog.objects.create(
            execution=execution,
            node=node,
            level=level,
            message=message,
            data=data or {}
        )
    
    def _fail_execution(self, execution, error_message):
        """Mark execution as failed"""
        execution.status = 'failed'
        execution.completed_at = timezone.now()
        execution.save()
        
        self._log_execution(execution, 'error', error_message)
    
    def _evaluate_connection_condition(self, connection, execution_data):
        """Evaluate connection condition"""
        if not connection.condition:
            return True
        
        # Simple condition evaluation (can be extended)
        condition = connection.condition
        if 'field' in condition and 'operator' in condition and 'value' in condition:
            field_value = execution_data.get(condition['field'])
            operator = condition['operator']
            expected_value = condition['value']
            
            if operator == 'equals':
                return field_value == expected_value
            elif operator == 'not_equals':
                return field_value != expected_value
            elif operator == 'greater_than':
                return field_value > expected_value
            elif operator == 'less_than':
                return field_value < expected_value
            elif operator == 'contains':
                return expected_value in str(field_value)
        
        return True

class WorkflowValidator:
    """Validates workflow definitions"""
    
    def validate_workflow(self, workflow_data):
        """Validate complete workflow"""
        errors = []
        
        nodes = workflow_data.get('nodes', [])
        connections = workflow_data.get('connections', [])
        
        # Check for start and end nodes
        start_nodes = [n for n in nodes if n['type'] == 'start']
        end_nodes = [n for n in nodes if n['type'] == 'end']
        
        if len(start_nodes) != 1:
            errors.append('Workflow must have exactly one start node')
        
        if len(end_nodes) == 0:
            errors.append('Workflow must have at least one end node')
        
        # Check for orphaned nodes
        node_ids = {n['id'] for n in nodes}
        connected_nodes = set()
        
        for conn in connections:
            if conn['source'] not in node_ids:
                errors.append(f"Connection source '{conn['source']}' not found in nodes")
            if conn['target'] not in node_ids:
                errors.append(f"Connection target '{conn['target']}' not found in nodes")
            
            connected_nodes.add(conn['source'])
            connected_nodes.add(conn['target'])
        
        orphaned_nodes = node_ids - connected_nodes
        if orphaned_nodes and len(nodes) > 1:
            errors.append(f'Orphaned nodes found: {list(orphaned_nodes)}')
        
        # Check for cycles (basic check)
        if self._has_cycles(nodes, connections):
            errors.append('Workflow contains cycles')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def _has_cycles(self, nodes, connections):
        """Check for cycles in workflow (simplified)"""
        # Build adjacency list
        graph = {node['id']: [] for node in nodes}
        for conn in connections:
            if conn['source'] in graph and conn['target'] in graph:
                graph[conn['source']].append(conn['target'])
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False

class NodeExecutor:
    """Executes individual workflow nodes"""
    
    def execute_node(self, execution, node):
        """Execute a specific node"""
        try:
            if node.node_type == 'task':
                return self._execute_task_node(execution, node)
            elif node.node_type == 'decision':
                return self._execute_decision_node(execution, node)
            elif node.node_type == 'approval':
                return self._execute_approval_node(execution, node)
            elif node.node_type == 'notification':
                return self._execute_notification_node(execution, node)
            elif node.node_type == 'integration':
                return self._execute_integration_node(execution, node)
            elif node.node_type == 'delay':
                return self._execute_delay_node(execution, node)
            elif node.node_type == 'condition':
                return self._execute_condition_node(execution, node)
            elif node.node_type == 'end':
                return self._execute_end_node(execution, node)
            else:
                return {'success': True, 'data': {}}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_task_node(self, execution, node):
        """Execute task node"""
        config = node.config
        task_type = config.get('task_type', 'custom')
        
        if task_type == 'data_transformation':
            return self._execute_data_transformation(execution, config)
        elif task_type == 'api_call':
            return self._execute_api_call(execution, config)
        elif task_type == 'database_operation':
            return self._execute_database_operation(execution, config)
        else:
            # Custom task execution
            return {'success': True, 'data': {'message': 'Task completed'}}
    
    def _execute_decision_node(self, execution, node):
        """Execute decision node"""
        config = node.config
        condition = config.get('condition', {})
        
        # Evaluate condition against execution data
        result = self._evaluate_condition(condition, execution.execution_data)
        
        return {
            'success': True,
            'data': {'decision_result': result}
        }
    
    def _execute_approval_node(self, execution, node):
        """Execute approval node"""
        config = node.config
        approver_id = config.get('approver_id')
        
        if not approver_id:
            return {'success': False, 'error': 'No approver specified'}
        
        # Create approval request
        approval = WorkflowApproval.objects.create(
            execution=execution,
            node=node,
            approver_id=approver_id,
            request_data=config.get('request_data', {}),
            status='pending'
        )
        
        # Send notification to approver
        self._send_approval_notification(approval)
        
        # Pause execution
        execution.status = 'paused'
        execution.save()
        
        return {
            'success': True,
            'data': {'approval_id': str(approval.id)},
            'pause_execution': True
        }
    
    def _execute_notification_node(self, execution, node):
        """Execute notification node"""
        config = node.config
        notification_type = config.get('type', 'email')
        
        if notification_type == 'email':
            return self._send_email_notification(execution, config)
        elif notification_type == 'sms':
            return self._send_sms_notification(execution, config)
        else:
            return {'success': False, 'error': f'Unknown notification type: {notification_type}'}
    
    def _execute_integration_node(self, execution, node):
        """Execute integration node"""
        config = node.config
        integration_id = config.get('integration_id')
        
        if not integration_id:
            return {'success': False, 'error': 'No integration specified'}
        
        try:
            integration = WorkflowIntegration.objects.get(id=integration_id)
            return self._call_integration(integration, config, execution.execution_data)
        except WorkflowIntegration.DoesNotExist:
            return {'success': False, 'error': 'Integration not found'}
    
    def _execute_delay_node(self, execution, node):
        """Execute delay node"""
        config = node.config
        delay_seconds = config.get('delay_seconds', 60)
        
        # Schedule continuation after delay
        execute_node_after_delay.apply_async(
            args=[execution.id, node.id],
            countdown=delay_seconds
        )
        
        return {
            'success': True,
            'data': {'delayed_seconds': delay_seconds},
            'pause_execution': True
        }
    
    def _execute_condition_node(self, execution, node):
        """Execute condition node"""
        config = node.config
        conditions = config.get('conditions', [])
        
        results = []
        for condition in conditions:
            result = self._evaluate_condition(condition, execution.execution_data)
            results.append(result)
        
        return {
            'success': True,
            'data': {'condition_results': results}
        }
    
    def _execute_end_node(self, execution, node):
        """Execute end node"""
        execution.status = 'completed'
        execution.completed_at = timezone.now()
        execution.save()
        
        return {
            'success': True,
            'data': {'message': 'Workflow completed'},
            'end_execution': True
        }
    
    def _evaluate_condition(self, condition, data):
        """Evaluate a condition"""
        # Simple condition evaluation
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        if not all([field, operator, value]):
            return False
        
        field_value = data.get(field)
        
        if operator == 'equals':
            return field_value == value
        elif operator == 'not_equals':
            return field_value != value
        elif operator == 'greater_than':
            return field_value > value
        elif operator == 'less_than':
            return field_value < value
        elif operator == 'contains':
            return value in str(field_value)
        
        return False
    
    def _send_approval_notification(self, approval):
        """Send approval notification"""
        subject = f'Workflow Approval Required: {approval.execution.workflow.name}'
        message = f'''
        A workflow requires your approval.
        
        Workflow: {approval.execution.workflow.name}
        Execution ID: {approval.execution.id}
        Node: {approval.node.name}
        
        Please review and approve/reject this request.
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [approval.approver.email],
            fail_silently=True
        )
    
    def _send_email_notification(self, execution, config):
        """Send email notification"""
        try:
            subject = config.get('subject', 'Workflow Notification')
            message = config.get('message', 'Workflow notification')
            recipients = config.get('recipients', [])
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=False
            )
            
            return {'success': True, 'data': {'sent_to': recipients}}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_sms_notification(self, execution, config):
        """Send SMS notification"""
        # Placeholder for SMS integration
        return {'success': True, 'data': {'message': 'SMS sent (placeholder)'}}
    
    def _call_integration(self, integration, config, execution_data):
        """Call external integration"""
        try:
            if integration.integration_type == 'api':
                return self._call_rest_api(integration, config, execution_data)
            elif integration.integration_type == 'webhook':
                return self._call_webhook(integration, config, execution_data)
            else:
                return {'success': False, 'error': f'Unsupported integration type: {integration.integration_type}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _call_rest_api(self, integration, config, execution_data):
        """Call REST API"""
        method = config.get('method', 'GET')
        endpoint = config.get('endpoint', '')
        headers = config.get('headers', {})
        payload = config.get('payload', {})
        
        url = integration.endpoint_url + endpoint
        
        # Replace variables in payload
        payload = self._replace_variables(payload, execution_data)
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        return {
            'success': response.status_code < 400,
            'data': {
                'status_code': response.status_code,
                'response': response.json() if response.content else {}
            }
        }
    
    def _call_webhook(self, integration, config, execution_data):
        """Call webhook"""
        payload = config.get('payload', {})
        payload = self._replace_variables(payload, execution_data)
        
        response = requests.post(
            integration.endpoint_url,
            json=payload,
            timeout=30
        )
        
        return {
            'success': response.status_code < 400,
            'data': {
                'status_code': response.status_code,
                'response': response.text
            }
        }
    
    def _replace_variables(self, data, variables):
        """Replace variables in data"""
        if isinstance(data, dict):
            return {k: self._replace_variables(v, variables) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables(item, variables) for item in data]
        elif isinstance(data, str) and data.startswith('{{') and data.endswith('}}'):
            var_name = data[2:-2].strip()
            return variables.get(var_name, data)
        else:
            return data

class IntegrationTester:
    """Tests workflow integrations"""
    
    def test_integration(self, integration):
        """Test integration connection"""
        try:
            if integration.integration_type == 'api':
                return self._test_api_integration(integration)
            elif integration.integration_type == 'webhook':
                return self._test_webhook_integration(integration)
            elif integration.integration_type == 'email':
                return self._test_email_integration(integration)
            else:
                return {
                    'success': False,
                    'message': f'Testing not supported for {integration.integration_type}'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Test failed: {str(e)}'
            }
    
    def _test_api_integration(self, integration):
        """Test API integration"""
        try:
            response = requests.get(
                integration.endpoint_url,
                timeout=10
            )
            return {
                'success': response.status_code < 400,
                'message': f'API responded with status {response.status_code}',
                'details': {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }
    
    def _test_webhook_integration(self, integration):
        """Test webhook integration"""
        test_payload = {'test': True, 'timestamp': timezone.now().isoformat()}
        
        try:
            response = requests.post(
                integration.endpoint_url,
                json=test_payload,
                timeout=10
            )
            return {
                'success': response.status_code < 400,
                'message': f'Webhook responded with status {response.status_code}',
                'details': {
                    'status_code': response.status_code,
                    'response': response.text[:200]  # First 200 chars
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Webhook test failed: {str(e)}'
            }
    
    def _test_email_integration(self, integration):
        """Test email integration"""
        # Placeholder for email testing
        return {
            'success': True,
            'message': 'Email integration test passed (placeholder)'
        }

# Celery tasks
@shared_task
def execute_workflow_task(execution_id, start_node_id):
    """Execute workflow asynchronously"""
    try:
        execution = WorkflowExecution.objects.get(id=execution_id)
        start_node = WorkflowNode.objects.get(id=start_node_id)
        
        executor = NodeExecutor()
        result = executor.execute_node(execution, start_node)
        
        if result['success']:
            # Update execution data
            execution.execution_data.update(result.get('data', {}))
            execution.save()
            
            # Continue to next nodes if not paused or ended
            if not result.get('pause_execution') and not result.get('end_execution'):
                next_connections = start_node.outgoing_connections.all()
                for connection in next_connections:
                    engine = WorkflowEngine()
                    if engine._evaluate_connection_condition(connection, execution.execution_data):
                        execute_node_task.delay(execution_id, connection.target_node.id)
                        break
        else:
            # Handle execution failure
            engine = WorkflowEngine()
            engine._fail_execution(execution, result.get('error', 'Node execution failed'))
    
    except Exception as e:
        execution = WorkflowExecution.objects.get(id=execution_id)
        engine = WorkflowEngine()
        engine._fail_execution(execution, f'Task execution error: {str(e)}')

@shared_task
def execute_node_task(execution_id, node_id):
    """Execute individual node asynchronously"""
    try:
        execution = WorkflowExecution.objects.get(id=execution_id)
        node = WorkflowNode.objects.get(id=node_id)
        
        executor = NodeExecutor()
        result = executor.execute_node(execution, node)
        
        if result['success']:
            # Update execution data
            execution.execution_data.update(result.get('data', {}))
            execution.current_node = node
            execution.save()
            
            # Continue to next nodes if not paused or ended
            if not result.get('pause_execution') and not result.get('end_execution'):
                next_connections = node.outgoing_connections.all()
                for connection in next_connections:
                    engine = WorkflowEngine()
                    if engine._evaluate_connection_condition(connection, execution.execution_data):
                        execute_node_task.delay(execution_id, connection.target_node.id)
                        break
        else:
            # Handle node execution failure
            engine = WorkflowEngine()
            engine._fail_execution(execution, result.get('error', 'Node execution failed'))
    
    except Exception as e:
        execution = WorkflowExecution.objects.get(id=execution_id)
        engine = WorkflowEngine()
        engine._fail_execution(execution, f'Node execution error: {str(e)}')

@shared_task
def execute_node_after_delay(execution_id, node_id):
    """Execute node after delay"""
    execute_node_task.delay(execution_id, node_id)