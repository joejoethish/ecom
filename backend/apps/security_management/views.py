from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from .models import (
    SecurityThreat, SecurityIncident, SecurityAudit, SecurityPolicy,
    SecurityVulnerability, SecurityTraining, SecurityTrainingRecord,
    SecurityRiskAssessment, SecurityMonitoringRule, SecurityAlert,
    SecurityConfiguration
)
from .serializers import (
    SecurityThreatSerializer, SecurityIncidentSerializer, SecurityAuditSerializer,
    SecurityPolicySerializer, SecurityVulnerabilitySerializer, SecurityTrainingSerializer,
    SecurityTrainingRecordSerializer, SecurityRiskAssessmentSerializer,
    SecurityMonitoringRuleSerializer, SecurityAlertSerializer, SecurityConfigurationSerializer,
    SecurityDashboardStatsSerializer, ThreatTrendSerializer, VulnerabilityMetricsSerializer,
    SecurityTrainingMetricsSerializer
)
from .services import (
    SecurityThreatService, SecurityIncidentService, SecurityVulnerabilityService,
    SecurityAuditService, SecurityPolicyService, SecurityTrainingService,
    SecurityRiskAssessmentService, SecurityAlertService, SecurityDashboardService,
    SecurityConfigurationService
)

User = get_user_model()


class SecurityThreatViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security threats"""
    queryset = SecurityThreat.objects.all()
    serializer_class = SecurityThreatSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityThreat.objects.all()
        severity = self.request.query_params.get('severity')
        status_filter = self.request.query_params.get('status')
        
        if severity:
            queryset = queryset.filter(severity=severity)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-detected_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get threat statistics"""
        stats = SecurityThreatService.get_threat_statistics()
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get threat trends"""
        days = int(request.query_params.get('days', 30))
        trends = SecurityThreatService.get_threat_trends(days)
        serializer = ThreatTrendSerializer(trends, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update threat status"""
        threat = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        try:
            updated_threat = SecurityThreatService.update_threat_status(
                str(threat.id), new_status, request.user, notes
            )
            serializer = self.get_serializer(updated_threat)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class SecurityIncidentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security incidents"""
    queryset = SecurityIncident.objects.all()
    serializer_class = SecurityIncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityIncident.objects.all()
        incident_type = self.request.query_params.get('type')
        severity = self.request.query_params.get('severity')
        status_filter = self.request.query_params.get('status')
        
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-occurred_at')
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get incident statistics"""
        stats = SecurityIncidentService.get_incident_statistics()
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def add_timeline_entry(self, request, pk=None):
        """Add entry to incident timeline"""
        incident = self.get_object()
        timeline_entry = request.data
        
        try:
            updated_incident = SecurityIncidentService.update_incident_timeline(
                str(incident.id), timeline_entry, request.user
            )
            serializer = self.get_serializer(updated_incident)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class SecurityVulnerabilityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security vulnerabilities"""
    queryset = SecurityVulnerability.objects.all()
    serializer_class = SecurityVulnerabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityVulnerability.objects.all()
        severity = self.request.query_params.get('severity')
        status_filter = self.request.query_params.get('status')
        
        if severity:
            queryset = queryset.filter(severity=severity)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-cvss_score', '-discovered_date')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get vulnerability statistics"""
        stats = SecurityVulnerabilityService.get_vulnerability_statistics()
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get vulnerability metrics"""
        metrics = SecurityVulnerabilityService.get_vulnerability_metrics()
        serializer = VulnerabilityMetricsSerializer(metrics, many=True)
        return Response(serializer.data)


class SecurityAuditViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security audits"""
    queryset = SecurityAudit.objects.all()
    serializer_class = SecurityAuditSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityAudit.objects.all()
        audit_type = self.request.query_params.get('type')
        status_filter = self.request.query_params.get('status')
        
        if audit_type:
            queryset = queryset.filter(audit_type=audit_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-scheduled_date')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get audit statistics"""
        stats = SecurityAuditService.get_audit_statistics()
        return Response(stats)


class SecurityPolicyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security policies"""
    queryset = SecurityPolicy.objects.all()
    serializer_class = SecurityPolicySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityPolicy.objects.all()
        policy_type = self.request.query_params.get('type')
        status_filter = self.request.query_params.get('status')
        
        if policy_type:
            queryset = queryset.filter(policy_type=policy_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-effective_date')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get policy statistics"""
        stats = SecurityPolicyService.get_policy_statistics()
        return Response(stats)


class SecurityTrainingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security training"""
    queryset = SecurityTraining.objects.all()
    serializer_class = SecurityTrainingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityTraining.objects.all()
        training_type = self.request.query_params.get('type')
        status_filter = self.request.query_params.get('status')
        
        if training_type:
            queryset = queryset.filter(training_type=training_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('training_name')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get training statistics"""
        stats = SecurityTrainingService.get_training_statistics()
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get training metrics"""
        metrics = SecurityTrainingService.get_training_metrics()
        serializer = SecurityTrainingMetricsSerializer(metrics, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def enroll_user(self, request, pk=None):
        """Enroll user in training"""
        training = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            record = SecurityTrainingService.enroll_user_in_training(
                str(training.id), user_id
            )
            serializer = SecurityTrainingRecordSerializer(record)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class SecurityTrainingRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security training records"""
    queryset = SecurityTrainingRecord.objects.all()
    serializer_class = SecurityTrainingRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityTrainingRecord.objects.all()
        user_id = self.request.query_params.get('user_id')
        training_id = self.request.query_params.get('training_id')
        status_filter = self.request.query_params.get('status')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if training_id:
            queryset = queryset.filter(training_id=training_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-completed_at')


class SecurityRiskAssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security risk assessments"""
    queryset = SecurityRiskAssessment.objects.all()
    serializer_class = SecurityRiskAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityRiskAssessment.objects.all()
        risk_level = self.request.query_params.get('risk_level')
        status_filter = self.request.query_params.get('status')
        
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-risk_score', '-assessment_date')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get risk assessment statistics"""
        stats = SecurityRiskAssessmentService.get_risk_statistics()
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def calculate_risk(self, request):
        """Calculate risk score"""
        likelihood = request.data.get('likelihood')
        impact = request.data.get('impact')
        
        risk_score, risk_level = SecurityRiskAssessmentService.calculate_risk_score(
            likelihood, impact
        )
        
        return Response({
            'risk_score': risk_score,
            'risk_level': risk_level
        })


class SecurityMonitoringRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security monitoring rules"""
    queryset = SecurityMonitoringRule.objects.all()
    serializer_class = SecurityMonitoringRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityMonitoringRule.objects.all()
        rule_type = self.request.query_params.get('type')
        status_filter = self.request.query_params.get('status')
        
        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('rule_name')


class SecurityAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security alerts"""
    queryset = SecurityAlert.objects.all()
    serializer_class = SecurityAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityAlert.objects.all()
        alert_type = self.request.query_params.get('type')
        severity = self.request.query_params.get('severity')
        status_filter = self.request.query_params.get('status')
        
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get alert statistics"""
        stats = SecurityAlertService.get_alert_statistics()
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge alert"""
        alert = self.get_object()
        
        try:
            updated_alert = SecurityAlertService.acknowledge_alert(
                str(alert.id), request.user
            )
            serializer = self.get_serializer(updated_alert)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class SecurityConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing security configurations"""
    queryset = SecurityConfiguration.objects.all()
    serializer_class = SecurityConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = SecurityConfiguration.objects.all()
        config_type = self.request.query_params.get('type')
        status_filter = self.request.query_params.get('status')
        
        if config_type:
            queryset = queryset.filter(config_type=config_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('config_name')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get configuration statistics"""
        stats = SecurityConfigurationService.get_configuration_statistics()
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate configuration"""
        config = self.get_object()
        
        try:
            updated_config = SecurityConfigurationService.validate_configuration(
                str(config.id), request.user
            )
            serializer = self.get_serializer(updated_config)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class SecurityDashboardViewSet(viewsets.ViewSet):
    """ViewSet for security dashboard data"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dashboard statistics"""
        stats = SecurityDashboardService.get_dashboard_stats()
        serializer = SecurityDashboardStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get security trends"""
        days = int(request.query_params.get('days', 30))
        trends = SecurityDashboardService.get_security_trends(days)
        return Response(trends)