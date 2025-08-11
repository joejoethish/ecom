from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SystemSettingViewSet, SettingCategoryViewSet, SettingBackupViewSet,
    SettingTemplateViewSet, SettingChangeHistoryViewSet, SettingAuditLogViewSet
)

router = DefaultRouter()
router.register(r'settings', SystemSettingViewSet, basename='systemsetting')
router.register(r'categories', SettingCategoryViewSet, basename='settingcategory')
router.register(r'backups', SettingBackupViewSet, basename='settingbackup')
router.register(r'templates', SettingTemplateViewSet, basename='settingtemplate')
router.register(r'change-history', SettingChangeHistoryViewSet, basename='settingchangehistory')
router.register(r'audit-logs', SettingAuditLogViewSet, basename='settingauditlog')

urlpatterns = [
    path('api/system-settings/', include(router.urls)),
]