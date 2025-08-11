from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import (
    WorkflowTemplate, Workflow, WorkflowNode, WorkflowConnection,
    WorkflowExecution, WorkflowExecutionLog, WorkflowApproval,
    WorkflowSchedule, WorkflowMetrics, WorkflowIntegration
)
from .serializers import (
    WorkflowTemplateSerializer, WorkflowSerializer, WorkflowNodeSerializer,
    WorkflowConnectionSerializer, WorkflowExecutionSerializer,
    WorkflowExecutionLogSerializer, WorkflowApprovalSerializer,
    WorkflowScheduleSerializer, WorkflowMetricsSerializer,
    WorkflowIntegrationSerializer, WorkflowDesignerSerializer,
    WorkflowExecutionSummarySerializer
)
from .services import WorkflowEngine, WorkflowValidator

class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    queryset = WorkflowTemplate.objects.all()
    serializer_class = WorkflowTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available template categories"""
        categories = [{'value': choice[0], 'label': choice[1]} 
                     for choice in WorkflowTemplate.CATEGORY_CHOICES]
        return Response(categories)
    
    @action(detail=True, methods=['post'])
    def create_workflow(self, request, pk=None):
        """Create a new workflow from template"""
        template = self.get_object()
        workflow_data = request.data.copy()
        workflow_data['template'] = template.id
        workflow_data['created_by'] = request.user.id
        
        serializer = WorkflowSerializer(data=workflow_data)
        if serializer.is_valid():
            workflow = serializer.save()
            return Response(WorkflowSerializer(workflow).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def designer(self, request, pk=None):
        """Get workflow data for visual designer"""
        workflow = self.get_object()
        serializer = WorkflowDesignerSerializer(workflow)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def save_design(self, request, pk=None):
        """Save workflow design from visual designer"""
        workflow = self.get_object()
        design_data = request.data
        
        # Validate workflow design
        validator = WorkflowValidator()
        validation_result = validator.validate_workflow(design_data)
        
        if not validation_result['is_valid']:
            return Response({
                'error': 'Invalid workflow design',
                'details': validation_result['errors']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update workflow definition
        workflow.workflow_definition = design_data.get('workflow_definition', {})
        workflow.save()
        
        # Update nodes and connections
        self._update_workflow_nodes(workflow, design_data.get('nodes', []))
        self._update_workflow_connections(workflow, design_data.get('connections', []))
        
        return Response({'message': 'Workflow design saved successfully'})
    
    def _update_workflow_nodes(self, workflow, nodes_data):
        """Update workflow nodes"""
        # Delete existing nodes
        workflow.nodes.all().delete()
        
        # Create new nodes
        for node_data in nodes_data:
            WorkflowNode.objects.create(
                workflow=workflow,
                node_id=node_data['id'],
                node_type=node_data['type'],
                name=node_data['name'],
                position=node_data.get('position', {}),
                config=node_data.get('config', {})
            )
    
    def _update_workflow_connections(self, workflow, connections_data):
        """Update workflow connections"""
        # Delete existing connections
        workflow.connections.all().delete()
        
        # Create new connections
        for conn_data in connections_data:
            source_node = workflow.nodes.get(node_id=conn_data['source'])
            target_node = workflow.nodes.get(node_id=conn_data['target'])
            
            WorkflowConnection.objects.create(
                workflow=workflow,
                source_node=source_node,
                target_node=target_node,
                condition=conn_data.get('condition', {}),
                label=conn_data.get('label', '')
            )
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute workflow manually"""
        workflow = self.get_object()
        trigger_data = request.data.get('trigger_data', {})
        
        engine = WorkflowEngine()
        execution = engine.execute_workflow(workflow, request.user, trigger_data)
        
        serializer = WorkflowExecutionSerializer(execution)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate workflow"""
        workflow = self.get_object()
        workflow.status = 'active'
        workflow.save()
        return Response({'message': 'Workflow activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate workflow"""
        workflow = self.get_object()
        workflow.status = 'paused'
        workflow.save()
        return Response({'message': 'Workflow deactivated'})
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get workflow performance metrics"""
        workflow = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now().date() - timedelta(days=days)
        metrics = WorkflowMetrics.objects.filter(
            workflow=workflow,
            date__gte=start_date
        ).order_by('date')
        
        serializer = WorkflowMetricsSerializer(metrics, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """Get workflow executions"""
        workflow = self.get_object()
        executions = workflow.executions.all()[:50]  # Latest 50 executions
        
        serializer = WorkflowExecutionSummarySerializer(executions, many=True)
        return Response(serializer.data)

class WorkflowExecutionViewSet(viewsets.ModelViewSet):
    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        workflow_id = self.request.query_params.get('workflow')
        status_filter = self.request.query_params.get('status')
        
        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel workflow execution"""
        execution = self.get_object()
        if execution.status in ['pending', 'running', 'paused']:
            execution.status = 'cancelled'
            execution.save()
            
            # Log cancellation
            WorkflowExecutionLog.objects.create(
                execution=execution,
                level='info',
                message=f'Execution cancelled by {request.user.get_full_name()}',
                data={'cancelled_by': request.user.id}
            )
            
            return Response({'message': 'Execution cancelled'})
        
        return Response({
            'error': 'Cannot cancel execution in current status'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry failed workflow execution"""
        execution = self.get_object()
        if execution.status == 'failed':
            engine = WorkflowEngine()
            new_execution = engine.retry_execution(execution)
            
            serializer = WorkflowExecutionSerializer(new_execution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Can only retry failed executions'
        }, status=status.HTTP_400_BAD_REQUEST)

class WorkflowApprovalViewSet(viewsets.ModelViewSet):
    queryset = WorkflowApproval.objects.all()
    serializer_class = WorkflowApprovalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            # Show only approvals for current user
            queryset = queryset.filter(approver=self.request.user)
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve workflow request"""
        approval = self.get_object()
        if approval.status == 'pending' and approval.approver == request.user:
            approval.status = 'approved'
            approval.comments = request.data.get('comments', '')
            approval.response_data = request.data.get('response_data', {})
            approval.responded_at = timezone.now()
            approval.save()
            
            # Continue workflow execution
            engine = WorkflowEngine()
            engine.continue_execution_after_approval(approval)
            
            return Response({'message': 'Request approved'})
        
        return Response({
            'error': 'Cannot approve this request'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject workflow request"""
        approval = self.get_object()
        if approval.status == 'pending' and approval.approver == request.user:
            approval.status = 'rejected'
            approval.comments = request.data.get('comments', '')
            approval.response_data = request.data.get('response_data', {})
            approval.responded_at = timezone.now()
            approval.save()
            
            # Handle rejection in workflow
            engine = WorkflowEngine()
            engine.handle_approval_rejection(approval)
            
            return Response({'message': 'Request rejected'})
        
        return Response({
            'error': 'Cannot reject this request'
        }, status=status.HTTP_400_BAD_REQUEST)

class WorkflowScheduleViewSet(viewsets.ModelViewSet):
    queryset = WorkflowSchedule.objects.all()
    serializer_class = WorkflowScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate schedule"""
        schedule = self.get_object()
        schedule.is_active = True
        schedule.save()
        return Response({'message': 'Schedule activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate schedule"""
        schedule = self.get_object()
        schedule.is_active = False
        schedule.save()
        return Response({'message': 'Schedule deactivated'})

class WorkflowIntegrationViewSet(viewsets.ModelViewSet):
    queryset = WorkflowIntegration.objects.all()
    serializer_class = WorkflowIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test integration connection"""
        integration = self.get_object()
        
        # Test connection based on integration type
        from .services import IntegrationTester
        tester = IntegrationTester()
        result = tester.test_integration(integration)
        
        return Response(result)

class WorkflowAnalyticsViewSet(viewsets.ViewSet):
    """Analytics and reporting for workflows"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get workflow dashboard data"""
        # Get summary statistics
        total_workflows = Workflow.objects.count()
        active_workflows = Workflow.objects.filter(status='active').count()
        total_executions = WorkflowExecution.objects.count()
        pending_approvals = WorkflowApproval.objects.filter(
            status='pending',
            approver=request.user
        ).count()
        
        # Get recent executions
        recent_executions = WorkflowExecution.objects.select_related(
            'workflow', 'triggered_by'
        ).order_by('-created_at')[:10]
        
        # Get performance metrics
        success_rate = self._calculate_success_rate()
        avg_duration = self._calculate_average_duration()
        
        return Response({
            'summary': {
                'total_workflows': total_workflows,
                'active_workflows': active_workflows,
                'total_executions': total_executions,
                'pending_approvals': pending_approvals,
                'success_rate': success_rate,
                'avg_duration': avg_duration
            },
            'recent_executions': WorkflowExecutionSummarySerializer(
                recent_executions, many=True
            ).data
        })
    
    def _calculate_success_rate(self):
        """Calculate overall success rate"""
        total = WorkflowExecution.objects.count()
        if total == 0:
            return 0
        
        successful = WorkflowExecution.objects.filter(status='completed').count()
        return (successful / total) * 100
    
    def _calculate_average_duration(self):
        """Calculate average execution duration"""
        completed_executions = WorkflowExecution.objects.filter(
            status='completed',
            started_at__isnull=False,
            completed_at__isnull=False
        )
        
        if not completed_executions.exists():
            return 0
        
        total_duration = sum([
            (exec.completed_at - exec.started_at).total_seconds()
            for exec in completed_executions
        ])
        
        return total_duration / completed_executions.count()
    
    @action(detail=False, methods=['get'])
    def performance_trends(self, request):
        """Get workflow performance trends"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        metrics = WorkflowMetrics.objects.filter(
            date__gte=start_date
        ).values('date').annotate(
            total_executions=Count('executions_count'),
            success_rate=Avg('successful_executions') * 100 / Avg('executions_count')
        ).order_by('date')
        
        return Response(list(metrics))
    
    @action(detail=False, methods=['get'])
    def top_workflows(self, request):
        """Get top performing workflows"""
        workflows = Workflow.objects.annotate(
            executions_count=Count('executions'),
            success_rate=Count('executions', filter=Q(executions__status='completed')) * 100.0 / Count('executions')
        ).order_by('-executions_count')[:10]
        
        data = []
        for workflow in workflows:
            data.append({
                'id': workflow.id,
                'name': workflow.name,
                'executions_count': workflow.executions_count,
                'success_rate': workflow.success_rate or 0
            })
        
        return Response(data)