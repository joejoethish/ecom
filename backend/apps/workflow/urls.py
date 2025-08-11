from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowTemplateViewSet, WorkflowViewSet, WorkflowExecutionViewSet,
    WorkflowApprovalViewSet, WorkflowScheduleViewSet, WorkflowIntegrationViewSet,
    WorkflowAnalyticsViewSet
)

router = DefaultRouter()
router.register(r'templates', WorkflowTemplateViewSet)
router.register(r'workflows', WorkflowViewSet)
router.register(r'executions', WorkflowExecutionViewSet)
router.register(r'approvals', WorkflowApprovalViewSet)
router.register(r'schedules', WorkflowScheduleViewSet)
router.register(r'integrations', WorkflowIntegrationViewSet)
router.register(r'analytics', WorkflowAnalyticsViewSet, basename='workflow-analytics')

urlpatterns = [
    path('api/workflow/', include(router.urls)),
]