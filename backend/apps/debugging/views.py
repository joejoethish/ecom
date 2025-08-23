from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from datetime import timedelta

from .models import (
    WorkflowSession, TraceStep, PerformanceSnapshot, 
    ErrorLog, DebugConfiguration, PerformanceThreshold
)
from .serializers import (
    WorkflowSessionSerializer, WorkflowSessionCreateSerializer,
    TraceStepSerializer, PerformanceSnapshotSerializer,
    ErrorLogSerializer, ErrorLogCreateSerializer,
    DebugConfigurationSerializer, PerformanceThresholdSerializer,
    SystemHealthSerializer, WorkflowStatsSerializer
)


class WorkflowSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing workflow sessions"""
    queryset = WorkflowSession.objects.all().select_related('user').prefetch_related('trace_steps')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['workflow_type', 'status', 'user']
    ordering_fields = ['start_time', 'end_time', 'workflow_type']
    ordering = ['-start_time']
    search_fields = ['correlation_id', 'workflow_type']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WorkflowSessionCreateSerializer
        return WorkflowSessionSerializer
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a workflow session as completed"""
        workflow = self.get_object()
        workflow.status = 'completed'
        workflow.end_time = timezone.now()
        workflow.save()
        
        serializer = self.get_serializer(workflow)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Mark a workflow session as failed"""
        workflow = self.get_object()
        workflow.status = 'failed'
        workflow.end_time = timezone.now()
        if 'error_message' in request.data:
            workflow.metadata['error_message'] = request.data['error_message']
        workflow.save()
        
        serializer = self.get_serializer(workflow)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get workflow statistics"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        total_workflows = self.queryset.count()
        completed_workflows = self.queryset.filter(status='completed').count()
        failed_workflows = self.queryset.filter(status='failed').count()
        
        # Average duration for completed workflows
        avg_duration = self.queryset.filter(
            status='completed',
            end_time__isnull=False
        ).aggregate(
            avg_duration=Avg('end_time') - Avg('start_time')
        )['avg_duration']
        
        avg_duration_ms = int(avg_duration.total_seconds() * 1000) if avg_duration else 0
        
        # Workflow types distribution
        workflow_types = dict(
            self.queryset.values('workflow_type').annotate(
                count=Count('id')
            ).values_list('workflow_type', 'count')
        )
        
        # Recent activity (last 24 hours)
        recent_activity = list(
            self.queryset.filter(start_time__gte=last_24h).values(
                'correlation_id', 'workflow_type', 'status', 'start_time'
            )[:10]
        )
        
        stats_data = {
            'total_workflows': total_workflows,
            'completed_workflows': completed_workflows,
            'failed_workflows': failed_workflows,
            'average_duration_ms': avg_duration_ms,
            'workflow_types': workflow_types,
            'recent_activity': recent_activity
        }
        
        serializer = WorkflowStatsSerializer(stats_data)
        return Response(serializer.data)


class TraceStepViewSet(viewsets.ModelViewSet):
    """ViewSet for managing trace steps"""
    queryset = TraceStep.objects.all().select_related('workflow_session')
    serializer_class = TraceStepSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['workflow_session', 'layer', 'component', 'status']
    ordering_fields = ['start_time', 'duration_ms']
    ordering = ['start_time']
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a trace step as completed"""
        trace_step = self.get_object()
        trace_step.status = 'completed'
        trace_step.end_time = timezone.now()
        
        # Calculate duration
        if trace_step.start_time:
            delta = trace_step.end_time - trace_step.start_time
            trace_step.duration_ms = int(delta.total_seconds() * 1000)
        
        trace_step.save()
        
        serializer = self.get_serializer(trace_step)
        return Response(serializer.data)


class PerformanceSnapshotViewSet(viewsets.ModelViewSet):
    """ViewSet for managing performance snapshots"""
    queryset = PerformanceSnapshot.objects.all()
    serializer_class = PerformanceSnapshotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['layer', 'component', 'metric_name', 'correlation_id']
    ordering_fields = ['timestamp', 'metric_value']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Get performance alerts (metrics exceeding thresholds)"""
        alerts = []
        
        # Get metrics that exceed warning thresholds
        warning_metrics = self.queryset.filter(
            threshold_warning__isnull=False,
            metric_value__gte=F('threshold_warning')
        ).order_by('-timestamp')[:50]
        
        # Get metrics that exceed critical thresholds
        critical_metrics = self.queryset.filter(
            threshold_critical__isnull=False,
            metric_value__gte=F('threshold_critical')
        ).order_by('-timestamp')[:50]
        
        for metric in warning_metrics:
            alerts.append({
                'type': 'warning',
                'metric': self.get_serializer(metric).data
            })
        
        for metric in critical_metrics:
            alerts.append({
                'type': 'critical',
                'metric': self.get_serializer(metric).data
            })
        
        return Response({'alerts': alerts})


class ErrorLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing error logs"""
    queryset = ErrorLog.objects.all().select_related('user')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['layer', 'component', 'severity', 'error_type', 'resolved', 'correlation_id']
    ordering_fields = ['timestamp', 'severity']
    ordering = ['-timestamp']
    search_fields = ['error_message', 'error_type', 'component']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ErrorLogCreateSerializer
        return ErrorLogSerializer
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark an error as resolved"""
        error_log = self.get_object()
        error_log.resolved = True
        error_log.resolution_notes = request.data.get('resolution_notes', '')
        error_log.save()
        
        serializer = self.get_serializer(error_log)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get error summary statistics"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        total_errors = self.queryset.count()
        recent_errors = self.queryset.filter(timestamp__gte=last_24h).count()
        unresolved_errors = self.queryset.filter(resolved=False).count()
        
        # Error distribution by severity
        severity_distribution = dict(
            self.queryset.values('severity').annotate(
                count=Count('id')
            ).values_list('severity', 'count')
        )
        
        # Error distribution by layer
        layer_distribution = dict(
            self.queryset.values('layer').annotate(
                count=Count('id')
            ).values_list('layer', 'count')
        )
        
        # Top error types
        top_error_types = list(
            self.queryset.values('error_type').annotate(
                count=Count('id')
            ).order_by('-count')[:10].values_list('error_type', 'count')
        )
        
        summary_data = {
            'total_errors': total_errors,
            'recent_errors': recent_errors,
            'unresolved_errors': unresolved_errors,
            'severity_distribution': severity_distribution,
            'layer_distribution': layer_distribution,
            'top_error_types': dict(top_error_types)
        }
        
        return Response(summary_data)


class DebugConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing debug configuration"""
    queryset = DebugConfiguration.objects.all()
    serializer_class = DebugConfigurationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['config_type', 'enabled']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class PerformanceThresholdViewSet(viewsets.ModelViewSet):
    """ViewSet for managing performance thresholds"""
    queryset = PerformanceThreshold.objects.all()
    serializer_class = PerformanceThresholdSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['metric_name', 'layer', 'component', 'enabled']
    ordering_fields = ['layer', 'metric_name']
    ordering = ['layer', 'metric_name']


class SystemHealthViewSet(viewsets.ViewSet):
    """ViewSet for system health monitoring"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get overall system health status"""
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        
        # Active workflows
        active_workflows = WorkflowSession.objects.filter(
            status='in_progress'
        ).count()
        
        # Recent errors
        recent_errors = ErrorLog.objects.filter(
            timestamp__gte=last_hour,
            severity__in=['error', 'critical']
        ).count()
        
        # Performance alerts
        performance_alerts = PerformanceSnapshot.objects.filter(
            timestamp__gte=last_hour,
            metric_value__gte=F('threshold_warning')
        ).count()
        
        # Layer-specific health
        layers = {}
        for layer in ['frontend', 'api', 'database', 'cache']:
            layer_errors = ErrorLog.objects.filter(
                layer=layer,
                timestamp__gte=last_hour,
                severity__in=['error', 'critical']
            ).count()
            
            layer_performance_issues = PerformanceSnapshot.objects.filter(
                layer=layer,
                timestamp__gte=last_hour,
                metric_value__gte=F('threshold_warning')
            ).count()
            
            layers[layer] = {
                'status': 'healthy' if layer_errors == 0 and layer_performance_issues == 0 else 'degraded',
                'errors': layer_errors,
                'performance_issues': layer_performance_issues
            }
        
        # Overall status
        overall_status = 'healthy'
        if recent_errors > 0 or performance_alerts > 0:
            overall_status = 'degraded'
        if recent_errors > 10 or performance_alerts > 5:
            overall_status = 'critical'
        
        health_data = {
            'overall_status': overall_status,
            'active_workflows': active_workflows,
            'recent_errors': recent_errors,
            'performance_alerts': performance_alerts,
            'layers': layers,
            'timestamp': now
        }
        
        serializer = SystemHealthSerializer(health_data)
        return Response(serializer.data)
