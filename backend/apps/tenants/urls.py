from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet, TenantUserViewSet, TenantSubscriptionViewSet,
    TenantUsageViewSet, TenantInvitationViewSet, TenantAuditLogViewSet,
    TenantBackupViewSet, AcceptInvitationView, TenantStatsView
)

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'users', TenantUserViewSet, basename='tenant-user')
router.register(r'subscriptions', TenantSubscriptionViewSet, basename='tenant-subscription')
router.register(r'usage', TenantUsageViewSet, basename='tenant-usage')
router.register(r'invitations', TenantInvitationViewSet, basename='tenant-invitation')
router.register(r'audit-logs', TenantAuditLogViewSet, basename='tenant-audit-log')
router.register(r'backups', TenantBackupViewSet, basename='tenant-backup')

urlpatterns = [
    path('api/tenants/', include(router.urls)),
    path('api/tenants/accept-invitation/<str:token>/', AcceptInvitationView.as_view(), name='accept-invitation'),
    path('api/tenants/stats/', TenantStatsView.as_view(), name='tenant-stats'),
]