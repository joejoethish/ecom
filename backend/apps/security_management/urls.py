from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SecurityThreatViewSet, SecurityIncidentViewSet, SecurityVulnerabilityViewSet,
    SecurityAuditViewSet, SecurityPolicyViewSet, SecurityTrainingViewSet,
    SecurityTrainingRecordViewSet, SecurityRiskAssessmentViewSet,
    SecurityMonitoringRuleViewSet, SecurityAlertViewSet, SecurityConfigurationViewSet,
    SecurityDashboardViewSet
)

router = DefaultRouter()
router.register(r'threats', SecurityThreatViewSet)
router.register(r'incidents', SecurityIncidentViewSet)
router.register(r'vulnerabilities', SecurityVulnerabilityViewSet)
router.register(r'audits', SecurityAuditViewSet)
router.register(r'policies', SecurityPolicyViewSet)
router.register(r'training', SecurityTrainingViewSet)
router.register(r'training-records', SecurityTrainingRecordViewSet)
router.register(r'risk-assessments', SecurityRiskAssessmentViewSet)
router.register(r'monitoring-rules', SecurityMonitoringRuleViewSet)
router.register(r'alerts', SecurityAlertViewSet)
router.register(r'configurations', SecurityConfigurationViewSet)
router.register(r'dashboard', SecurityDashboardViewSet, basename='security-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]