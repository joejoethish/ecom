from rest_framework import serializers
from .models import (
    WorkflowTemplate, Workflow, WorkflowNode, WorkflowConnection,
    WorkflowExecution, WorkflowExecutionLog, WorkflowApproval,
    WorkflowSchedule, WorkflowMetrics, WorkflowIntegration
)

class WorkflowTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = WorkflowTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

class WorkflowNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNode
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class WorkflowConnectionSerializer(serializers.ModelSerializer):
    source_node_name = serializers.CharField(source='source_node.name', read_only=True)
    target_node_name = serializers.CharField(source='target_node.name', read_only=True)
    
    class Meta:
        model = WorkflowConnection
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class WorkflowSerializer(serializers.ModelSerializer):
    nodes = WorkflowNodeSerializer(many=True, read_only=True)
    connections = WorkflowConnectionSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    executions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Workflow
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')
    
    def get_executions_count(self, obj):
        return obj.executions.count()

class WorkflowExecutionLogSerializer(serializers.ModelSerializer):
    node_name = serializers.CharField(source='node.name', read_only=True)
    
    class Meta:
        model = WorkflowExecutionLog
        fields = '__all__'
        read_only_fields = ('id', 'timestamp')

class WorkflowExecutionSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    triggered_by_name = serializers.CharField(source='triggered_by.get_full_name', read_only=True)
    current_node_name = serializers.CharField(source='current_node.name', read_only=True)
    logs = WorkflowExecutionLogSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowExecution
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None

class WorkflowApprovalSerializer(serializers.ModelSerializer):
    execution_id = serializers.CharField(source='execution.id', read_only=True)
    workflow_name = serializers.CharField(source='execution.workflow.name', read_only=True)
    node_name = serializers.CharField(source='node.name', read_only=True)
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)
    
    class Meta:
        model = WorkflowApproval
        fields = '__all__'
        read_only_fields = ('id', 'requested_at', 'responded_at')

class WorkflowScheduleSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    
    class Meta:
        model = WorkflowSchedule
        fields = '__all__'
        read_only_fields = ('id', 'last_run', 'next_run', 'created_at')

class WorkflowMetricsSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowMetrics
        fields = '__all__'
        read_only_fields = ('id',)
    
    def get_success_rate(self, obj):
        if obj.executions_count > 0:
            return (obj.successful_executions / obj.executions_count) * 100
        return 0

class WorkflowIntegrationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = WorkflowIntegration
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'created_at')

# Specialized serializers for workflow designer
class WorkflowDesignerSerializer(serializers.ModelSerializer):
    """Serializer optimized for the visual workflow designer"""
    nodes = serializers.SerializerMethodField()
    connections = serializers.SerializerMethodField()
    
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'description', 'status', 'nodes', 'connections', 'workflow_definition']
    
    def get_nodes(self, obj):
        nodes = obj.nodes.all()
        return [{
            'id': node.node_id,
            'type': node.node_type,
            'name': node.name,
            'position': node.position,
            'config': node.config
        } for node in nodes]
    
    def get_connections(self, obj):
        connections = obj.connections.all()
        return [{
            'id': str(conn.id),
            'source': conn.source_node.node_id,
            'target': conn.target_node.node_id,
            'condition': conn.condition,
            'label': conn.label
        } for conn in connections]

class WorkflowExecutionSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for execution lists"""
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    triggered_by_name = serializers.CharField(source='triggered_by.get_full_name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowExecution
        fields = ['id', 'workflow_name', 'status', 'triggered_by_name', 'started_at', 'completed_at', 'duration']
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None