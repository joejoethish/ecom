from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import get_user_model
import csv
import json
from datetime import datetime, timedelta

from .models import (
    ComplianceFramework, CompliancePolicy, ComplianceControl,
    ComplianceAssessment, ComplianceIncident, ComplianceTraining,
    ComplianceTrainingRecord, ComplianceAuditTrail, ComplianceRiskAssessment,
    ComplianceVendor, ComplianceReport
)
from .serializers import (
    ComplianceFrameworkSerializer, CompliancePolicySerializer,
    ComplianceControlSerializer, ComplianceAssessmentSerializer,
    ComplianceIncidentSerializer, ComplianceTrainingSerializer,
    ComplianceTrainingRecordSerializer, ComplianceAuditTrailSerializer,
    ComplianceRiskAssessmentSerializer, ComplianceVendorSerializer,
    ComplianceReportSerializer, ComplianceDashboardSerializer,
    ComplianceMetricsSerializer, BulkComplianceActionSerializer,
    ComplianceExportSerializer, ComplianceImportSerializer
)
from .filters import (
    ComplianceFrameworkFilter, CompliancePolicyFilter,
    ComplianceControlFilter, ComplianceAssessmentFilter,
    ComplianceIncidentFilter, ComplianceTrainingFilter,
    ComplianceTrainingRecordFilter, ComplianceAuditTrailFilter,
    ComplianceRiskAssessmentFilter, ComplianceVendorFilter,
    ComplianceReportFilter
)
from .permissions import (
    CompliancePermission, ComplianceFrameworkPermission,
    CompliancePolicyPermission, ComplianceIncidentPermission,
    ComplianceTrainingPermission, ComplianceRiskPermission,
    ComplianceReportPermission, ComplianceAuditTrailPermission
)

User = get_user_model()


class ComplianceFrameworkViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Framework management"""
    queryset = ComplianceFramework.objects.all()
    serializer_class = ComplianceFrameworkSerializer
    permission_classes = [IsAuthenticated, ComplianceFrameworkPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceFrameworkFilter
    search_fields = ['name', 'description', 'version']
    ordering_fields = ['name', 'created_at', 'effective_date', 'status']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a compliance framework"""
        framework = self.get_object()
        framework.status = 'active'
        framework.save()
        return Response({'status': 'Framework activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a compliance framework"""
        framework = self.get_object()
        framework.status = 'inactive'
        framework.save()
        return Response({'status': 'Framework deactivated'})
    
    @action(detail=True, methods=['get'])
    def policies(self, request, pk=None):
        """Get all policies for a framework"""
        framework = self.get_object()
        policies = framework.policies.all()
        serializer = CompliancePolicySerializer(policies, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def controls(self, request, pk=None):
        """Get all controls for a framework"""
        framework = self.get_object()
        controls = framework.controls.all()
        serializer = ComplianceControlSerializer(controls, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get framework statistics"""
        stats = {
            'total_frameworks': ComplianceFramework.objects.count(),
            'active_frameworks': ComplianceFramework.objects.filter(status='active').count(),
            'frameworks_by_type': dict(
                ComplianceFramework.objects.values('framework_type')
                .annotate(count=Count('id'))
                .values_list('framework_type', 'count')
            ),
            'frameworks_by_status': dict(
                ComplianceFramework.objects.values('status')
                .annotate(count=Count('id'))
                .values_list('status', 'count')
            )
        }
        return Response(stats)


class CompliancePolicyViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Policy management"""
    queryset = CompliancePolicy.objects.select_related('framework', 'owner', 'approver')
    serializer_class = CompliancePolicySerializer
    permission_classes = [IsAuthenticated, CompliancePolicyPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CompliancePolicyFilter
    search_fields = ['title', 'description', 'content']
    ordering_fields = ['title', 'created_at', 'effective_date', 'status']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a policy"""
        policy = self.get_object()
        policy.status = 'approved'
        policy.approver = request.user
        policy.approved_at = timezone.now()
        policy.save()
        return Response({'status': 'Policy approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a policy"""
        policy = self.get_object()
        policy.status = 'draft'
        policy.approver = None
        policy.approved_at = None
        policy.save()
        return Response({'status': 'Policy rejected'})
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a policy"""
        policy = self.get_object()
        if policy.status == 'approved':
            policy.status = 'active'
            policy.save()
            return Response({'status': 'Policy published'})
        return Response(
            {'error': 'Policy must be approved before publishing'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a policy"""
        policy = self.get_object()
        policy.status = 'archived'
        policy.save()
        return Response({'status': 'Policy archived'})
    
    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """Get policies pending review"""
        policies = CompliancePolicy.objects.filter(
            review_date__lte=timezone.now().date(),
            status='active'
        )
        serializer = self.get_serializer(policies, many=True)
        return Response(serializer.data)


class ComplianceControlViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Control management"""
    queryset = ComplianceControl.objects.select_related('framework', 'policy', 'owner')
    serializer_class = ComplianceControlSerializer
    permission_classes = [IsAuthenticated, CompliancePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceControlFilter
    search_fields = ['title', 'description', 'control_id']
    ordering_fields = ['control_id', 'title', 'risk_level', 'created_at']
    ordering = ['control_id']
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test a control"""
        control = self.get_object()
        test_results = request.data.get('test_results', {})
        control.last_tested = timezone.now().date()
        
        # Calculate next test date based on frequency
        if control.frequency == 'daily':
            control.next_test_date = control.last_tested + timedelta(days=1)
        elif control.frequency == 'weekly':
            control.next_test_date = control.last_tested + timedelta(weeks=1)
        elif control.frequency == 'monthly':
            control.next_test_date = control.last_tested + timedelta(days=30)
        elif control.frequency == 'quarterly':
            control.next_test_date = control.last_tested + timedelta(days=90)
        elif control.frequency == 'annually':
            control.next_test_date = control.last_tested + timedelta(days=365)
        
        control.save()
        
        # Log the test results
        ComplianceAuditTrail.objects.create(
            user=request.user,
            action='test',
            model_name='ComplianceControl',
            object_id=str(control.id),
            object_repr=str(control),
            changes={'test_results': test_results},
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'status': 'Control tested successfully'})
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign a control to a user"""
        control = self.get_object()
        owner_id = request.data.get('owner_id')
        if owner_id:
            try:
                owner = User.objects.get(id=owner_id)
                control.owner = owner
                control.save()
                return Response({'status': 'Control assigned successfully'})
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {'error': 'Owner ID is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def overdue_testing(self, request):
        """Get controls with overdue testing"""
        controls = ComplianceControl.objects.filter(
            next_test_date__lt=timezone.now().date()
        )
        serializer = self.get_serializer(controls, many=True)
        return Response(serializer.data)


class ComplianceAssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Assessment management"""
    queryset = ComplianceAssessment.objects.select_related('framework', 'assessor')
    serializer_class = ComplianceAssessmentSerializer
    permission_classes = [IsAuthenticated, CompliancePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceAssessmentFilter
    search_fields = ['title', 'description', 'scope']
    ordering_fields = ['title', 'start_date', 'overall_score', 'created_at']
    ordering = ['-start_date']
    
    @action(detail=True, methods=['post'])
    def conduct(self, request, pk=None):
        """Start conducting an assessment"""
        assessment = self.get_object()
        assessment.status = 'in_progress'
        assessment.assessor = request.user
        assessment.save()
        return Response({'status': 'Assessment started'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete an assessment"""
        assessment = self.get_object()
        assessment.status = 'completed'
        assessment.findings = request.data.get('findings', [])
        assessment.recommendations = request.data.get('recommendations', [])
        assessment.overall_score = request.data.get('overall_score')
        assessment.risk_rating = request.data.get('risk_rating')
        assessment.save()
        return Response({'status': 'Assessment completed'})


class ComplianceIncidentViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Incident management"""
    queryset = ComplianceIncident.objects.select_related(
        'framework', 'reported_by', 'assigned_to'
    )
    serializer_class = ComplianceIncidentSerializer
    permission_classes = [IsAuthenticated, ComplianceIncidentPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceIncidentFilter
    search_fields = ['title', 'description', 'incident_id']
    ordering_fields = ['incident_id', 'occurred_at', 'severity', 'status']
    ordering = ['-occurred_at']
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign an incident to a user"""
        incident = self.get_object()
        assigned_to_id = request.data.get('assigned_to_id')
        if assigned_to_id:
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
                incident.assigned_to = assigned_to
                incident.save()
                return Response({'status': 'Incident assigned successfully'})
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {'error': 'Assigned to ID is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an incident"""
        incident = self.get_object()
        incident.status = 'resolved'
        incident.resolved_at = timezone.now()
        incident.root_cause = request.data.get('root_cause', '')
        incident.remediation_actions = request.data.get('remediation_actions', [])
        incident.lessons_learned = request.data.get('lessons_learned', '')
        incident.save()
        return Response({'status': 'Incident resolved'})
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close an incident"""
        incident = self.get_object()
        incident.status = 'closed'
        incident.save()
        return Response({'status': 'Incident closed'})
    
    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """Escalate an incident"""
        incident = self.get_object()
        escalation_reason = request.data.get('escalation_reason', '')
        
        # Log escalation
        ComplianceAuditTrail.objects.create(
            user=request.user,
            action='escalate',
            model_name='ComplianceIncident',
            object_id=str(incident.id),
            object_repr=str(incident),
            changes={'escalation_reason': escalation_reason},
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'status': 'Incident escalated'})
    
    @action(detail=False, methods=['get'])
    def critical_incidents(self, request):
        """Get critical incidents"""
        incidents = ComplianceIncident.objects.filter(severity='critical')
        serializer = self.get_serializer(incidents, many=True)
        return Response(serializer.data)


class ComplianceTrainingViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Training management"""
    queryset = ComplianceTraining.objects.select_related('framework', 'created_by')
    serializer_class = ComplianceTrainingSerializer
    permission_classes = [IsAuthenticated, ComplianceTrainingPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceTrainingFilter
    search_fields = ['title', 'description', 'content']
    ordering_fields = ['title', 'duration_hours', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign training to users"""
        training = self.get_object()
        user_ids = request.data.get('user_ids', [])
        due_date = request.data.get('due_date')
        
        if not user_ids or not due_date:
            return Response(
                {'error': 'User IDs and due date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assigned_count = 0
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                record, created = ComplianceTrainingRecord.objects.get_or_create(
                    training=training,
                    user=user,
                    defaults={
                        'assigned_date': timezone.now().date(),
                        'due_date': due_date,
                        'status': 'not_started'
                    }
                )
                if created:
                    assigned_count += 1
            except User.DoesNotExist:
                continue
        
        return Response({
            'status': f'Training assigned to {assigned_count} users'
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a training program"""
        training = self.get_object()
        training.status = 'active'
        training.save()
        return Response({'status': 'Training activated'})


class ComplianceTrainingRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Training Record management"""
    queryset = ComplianceTrainingRecord.objects.select_related('training', 'user')
    serializer_class = ComplianceTrainingRecordSerializer
    permission_classes = [IsAuthenticated, CompliancePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceTrainingRecordFilter
    ordering_fields = ['assigned_date', 'due_date', 'completed_date', 'score']
    ordering = ['-assigned_date']
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a training record"""
        record = self.get_object()
        record.status = 'completed'
        record.completed_date = timezone.now().date()
        record.score = request.data.get('score')
        record.time_spent_hours = request.data.get('time_spent_hours', 0)
        record.attempts += 1
        
        # Issue certificate if required and passed
        if (record.training.assessment_required and 
            record.score and 
            record.score >= record.training.passing_score):
            record.certificate_issued = True
        
        record.save()
        return Response({'status': 'Training completed'})
    
    @action(detail=True, methods=['post'])
    def issue_certificate(self, request, pk=None):
        """Issue certificate for completed training"""
        record = self.get_object()
        if record.status == 'completed':
            record.certificate_issued = True
            record.save()
            return Response({'status': 'Certificate issued'})
        return Response(
            {'error': 'Training must be completed first'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ComplianceAuditTrailViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Compliance Audit Trail (read-only)"""
    queryset = ComplianceAuditTrail.objects.select_related('user')
    serializer_class = ComplianceAuditTrailSerializer
    permission_classes = [IsAuthenticated, ComplianceAuditTrailPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceAuditTrailFilter
    search_fields = ['object_repr', 'changes']
    ordering_fields = ['timestamp', 'action', 'model_name']
    ordering = ['-timestamp']


class ComplianceRiskAssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Risk Assessment management"""
    queryset = ComplianceRiskAssessment.objects.select_related(
        'framework', 'risk_owner'
    ).prefetch_related('controls')
    serializer_class = ComplianceRiskAssessmentSerializer
    permission_classes = [IsAuthenticated, ComplianceRiskPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceRiskAssessmentFilter
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'inherent_risk_score', 'residual_risk_score', 'created_at']
    ordering = ['-inherent_risk_score']
    
    @action(detail=True, methods=['post'])
    def assess(self, request, pk=None):
        """Assess a risk"""
        risk = self.get_object()
        risk.status = 'assessed'
        risk.last_reviewed = timezone.now().date()
        risk.save()
        return Response({'status': 'Risk assessed'})
    
    @action(detail=True, methods=['post'])
    def mitigate(self, request, pk=None):
        """Mitigate a risk"""
        risk = self.get_object()
        risk.status = 'mitigated'
        risk.mitigation_strategies = request.data.get('mitigation_strategies', [])
        risk.residual_risk_score = request.data.get('residual_risk_score', risk.inherent_risk_score)
        risk.save()
        return Response({'status': 'Risk mitigated'})
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a risk"""
        risk = self.get_object()
        risk.status = 'accepted'
        risk.save()
        return Response({'status': 'Risk accepted'})
    
    @action(detail=False, methods=['get'])
    def high_risks(self, request):
        """Get high-risk assessments"""
        risks = ComplianceRiskAssessment.objects.filter(inherent_risk_score__gte=15)
        serializer = self.get_serializer(risks, many=True)
        return Response(serializer.data)


class ComplianceVendorViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Vendor management"""
    queryset = ComplianceVendor.objects.all()
    serializer_class = ComplianceVendorSerializer
    permission_classes = [IsAuthenticated, CompliancePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceVendorFilter
    search_fields = ['name', 'description', 'contact_person', 'contact_email']
    ordering_fields = ['name', 'risk_level', 'assessment_score', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def assess(self, request, pk=None):
        """Assess a vendor"""
        vendor = self.get_object()
        vendor.last_assessment_date = timezone.now().date()
        vendor.assessment_score = request.data.get('assessment_score')
        
        # Set next assessment date (typically annually)
        vendor.next_assessment_date = vendor.last_assessment_date + timedelta(days=365)
        vendor.save()
        
        return Response({'status': 'Vendor assessed'})
    
    @action(detail=True, methods=['post'])
    def onboard(self, request, pk=None):
        """Onboard a vendor"""
        vendor = self.get_object()
        vendor.status = 'active'
        vendor.save()
        return Response({'status': 'Vendor onboarded'})
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate a vendor"""
        vendor = self.get_object()
        vendor.status = 'terminated'
        vendor.save()
        return Response({'status': 'Vendor terminated'})


class ComplianceReportViewSet(viewsets.ModelViewSet):
    """ViewSet for Compliance Report management"""
    queryset = ComplianceReport.objects.select_related('framework', 'generated_by')
    serializer_class = ComplianceReportSerializer
    permission_classes = [IsAuthenticated, ComplianceReportPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ComplianceReportFilter
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'generated_at', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generate a report"""
        report = self.get_object()
        report.status = 'generating'
        report.generated_at = timezone.now()
        report.save()
        
        # Here you would implement the actual report generation logic
        # For now, we'll just mark it as completed
        report.status = 'completed'
        report.save()
        
        return Response({'status': 'Report generated'})
    
    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """Schedule a report"""
        report = self.get_object()
        report.scheduled = True
        report.schedule_frequency = request.data.get('schedule_frequency')
        report.recipients = request.data.get('recipients', [])
        
        # Calculate next run date
        if report.schedule_frequency == 'daily':
            report.next_run = timezone.now() + timedelta(days=1)
        elif report.schedule_frequency == 'weekly':
            report.next_run = timezone.now() + timedelta(weeks=1)
        elif report.schedule_frequency == 'monthly':
            report.next_run = timezone.now() + timedelta(days=30)
        
        report.save()
        return Response({'status': 'Report scheduled'})
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a report"""
        report = self.get_object()
        if report.status == 'completed' and report.file_path:
            # Here you would implement file download logic
            return Response({'download_url': f'/media/{report.file_path}'})
        return Response(
            {'error': 'Report not available for download'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ComplianceDashboardViewSet(viewsets.ViewSet):
    """ViewSet for Compliance Dashboard"""
    permission_classes = [IsAuthenticated, CompliancePermission]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get compliance dashboard overview"""
        data = {
            'total_frameworks': ComplianceFramework.objects.count(),
            'active_frameworks': ComplianceFramework.objects.filter(status='active').count(),
            'total_policies': CompliancePolicy.objects.count(),
            'approved_policies': CompliancePolicy.objects.filter(status='approved').count(),
            'total_controls': ComplianceControl.objects.count(),
            'implemented_controls': ComplianceControl.objects.filter(
                implementation_status='implemented'
            ).count(),
            'open_incidents': ComplianceIncident.objects.exclude(
                status__in=['resolved', 'closed']
            ).count(),
            'critical_incidents': ComplianceIncident.objects.filter(
                severity='critical'
            ).exclude(status__in=['resolved', 'closed']).count(),
            'pending_assessments': ComplianceAssessment.objects.filter(
                status='planned'
            ).count(),
            'overdue_trainings': ComplianceTrainingRecord.objects.filter(
                due_date__lt=timezone.now().date(),
                status__in=['not_started', 'in_progress']
            ).count(),
            'high_risks': ComplianceRiskAssessment.objects.filter(
                inherent_risk_score__gte=15
            ).count(),
            'vendor_assessments_due': ComplianceVendor.objects.filter(
                next_assessment_date__lte=timezone.now().date()
            ).count()
        }
        
        serializer = ComplianceDashboardSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get compliance metrics"""
        total_frameworks = ComplianceFramework.objects.count()
        active_frameworks = ComplianceFramework.objects.filter(status='active').count()
        
        total_policies = CompliancePolicy.objects.count()
        approved_policies = CompliancePolicy.objects.filter(status='approved').count()
        
        total_controls = ComplianceControl.objects.count()
        implemented_controls = ComplianceControl.objects.filter(
            implementation_status='implemented'
        ).count()
        
        total_incidents = ComplianceIncident.objects.count()
        resolved_incidents = ComplianceIncident.objects.filter(
            status__in=['resolved', 'closed']
        ).count()
        
        total_training_records = ComplianceTrainingRecord.objects.count()
        completed_training = ComplianceTrainingRecord.objects.filter(
            status='completed'
        ).count()
        
        total_risks = ComplianceRiskAssessment.objects.count()
        mitigated_risks = ComplianceRiskAssessment.objects.filter(
            status='mitigated'
        ).count()
        
        total_vendors = ComplianceVendor.objects.count()
        compliant_vendors = ComplianceVendor.objects.filter(
            assessment_score__gte=80
        ).count()
        
        data = {
            'framework_compliance_rate': (active_frameworks / total_frameworks * 100) if total_frameworks > 0 else 0,
            'policy_approval_rate': (approved_policies / total_policies * 100) if total_policies > 0 else 0,
            'control_implementation_rate': (implemented_controls / total_controls * 100) if total_controls > 0 else 0,
            'incident_resolution_rate': (resolved_incidents / total_incidents * 100) if total_incidents > 0 else 0,
            'training_completion_rate': (completed_training / total_training_records * 100) if total_training_records > 0 else 0,
            'risk_mitigation_rate': (mitigated_risks / total_risks * 100) if total_risks > 0 else 0,
            'vendor_compliance_rate': (compliant_vendors / total_vendors * 100) if total_vendors > 0 else 0
        }
        
        serializer = ComplianceMetricsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on compliance objects"""
        serializer = BulkComplianceActionSerializer(data=request.data)
        if serializer.is_valid():
            action = serializer.validated_data['action']
            object_ids = serializer.validated_data['object_ids']
            parameters = serializer.validated_data.get('parameters', {})
            
            # Implement bulk actions based on the action type
            # This is a simplified implementation
            result = {'processed': len(object_ids), 'action': action}
            return Response(result)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def export_data(self, request):
        """Export compliance data"""
        serializer = ComplianceExportSerializer(data=request.data)
        if serializer.is_valid():
            export_type = serializer.validated_data['export_type']
            model_name = serializer.validated_data['model_name']
            
            # Implement data export logic
            # This is a simplified implementation
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{model_name}_export.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Export completed'])
            
            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def import_data(self, request):
        """Import compliance data"""
        serializer = ComplianceImportSerializer(data=request.data)
        if serializer.is_valid():
            # Implement data import logic
            # This is a simplified implementation
            result = {'status': 'Import completed', 'records_processed': 0}
            return Response(result)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)