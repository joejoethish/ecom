from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ComplianceFrameworkViewSet, CompliancePolicyViewSet,
    ComplianceControlViewSet, ComplianceAssessmentViewSet,
    ComplianceIncidentViewSet, ComplianceTrainingViewSet,
    ComplianceTrainingRecordViewSet, ComplianceAuditTrailViewSet,
    ComplianceRiskAssessmentViewSet, ComplianceVendorViewSet,
    ComplianceReportViewSet, ComplianceDashboardViewSet
)

app_name = 'compliance'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'frameworks', ComplianceFrameworkViewSet, basename='framework')
router.register(r'policies', CompliancePolicyViewSet, basename='policy')
router.register(r'controls', ComplianceControlViewSet, basename='control')
router.register(r'assessments', ComplianceAssessmentViewSet, basename='assessment')
router.register(r'incidents', ComplianceIncidentViewSet, basename='incident')
router.register(r'training', ComplianceTrainingViewSet, basename='training')
router.register(r'training-records', ComplianceTrainingRecordViewSet, basename='training-record')
router.register(r'audit-trail', ComplianceAuditTrailViewSet, basename='audit-trail')
router.register(r'risk-assessments', ComplianceRiskAssessmentViewSet, basename='risk-assessment')
router.register(r'vendors', ComplianceVendorViewSet, basename='vendor')
router.register(r'reports', ComplianceReportViewSet, basename='report')
router.register(r'dashboard', ComplianceDashboardViewSet, basename='dashboard')

urlpatterns = [
    path('api/', include(router.urls)),
]