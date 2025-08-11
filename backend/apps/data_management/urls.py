from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_simple import (
    DataImportJobViewSet, DataExportJobViewSet, DataMappingViewSet,
    DataSyncJobViewSet, DataBackupViewSet, DataAuditLogViewSet,
    DataQualityRuleViewSet, DataLineageViewSet, DataManagementStatsView
)

router = DefaultRouter()
router.register(r'import-jobs', DataImportJobViewSet)
router.register(r'export-jobs', DataExportJobViewSet)
router.register(r'mappings', DataMappingViewSet)
router.register(r'sync-jobs', DataSyncJobViewSet)
router.register(r'backups', DataBackupViewSet)
router.register(r'audit-logs', DataAuditLogViewSet)
router.register(r'quality-rules', DataQualityRuleViewSet)
router.register(r'lineage', DataLineageViewSet)
router.register(r'stats', DataManagementStatsView, basename='data-management-stats')

urlpatterns = [
    path('', include(router.urls)),
]