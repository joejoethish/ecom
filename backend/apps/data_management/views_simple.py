from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import (
    DataImportJob, DataExportJob, DataMapping, DataSyncJob,
    DataBackup, DataAuditLog, DataQualityRule, DataLineage
)
from .serializers import (
    DataImportJobSerializer, DataExportJobSerializer, DataMappingSerializer,
    DataSyncJobSerializer, DataBackupSerializer, DataAuditLogSerializer,
    DataQualityRuleSerializer, DataLineageSerializer
)


class DataImportJobViewSet(viewsets.ModelViewSet):
    """ViewSet for data import jobs"""
    
    queryset = DataImportJob.objects.all()
    serializer_class = DataImportJobSerializer
    permission_classes = [permissions.IsAuthenticated]


class DataExportJobViewSet(viewsets.ModelViewSet):
    """ViewSet for data export jobs"""
    
    queryset = DataExportJob.objects.all()
    serializer_class = DataExportJobSerializer
    permission_classes = [permissions.IsAuthenticated]


class DataMappingViewSet(viewsets.ModelViewSet):
    """ViewSet for data mappings"""
    
    queryset = DataMapping.objects.all()
    serializer_class = DataMappingSerializer
    permission_classes = [permissions.IsAuthenticated]


class DataSyncJobViewSet(viewsets.ModelViewSet):
    """ViewSet for data sync jobs"""
    
    queryset = DataSyncJob.objects.all()
    serializer_class = DataSyncJobSerializer
    permission_classes = [permissions.IsAuthenticated]


class DataBackupViewSet(viewsets.ModelViewSet):
    """ViewSet for data backups"""
    
    queryset = DataBackup.objects.all()
    serializer_class = DataBackupSerializer
    permission_classes = [permissions.IsAuthenticated]


class DataAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for data audit logs"""
    
    queryset = DataAuditLog.objects.all()
    serializer_class = DataAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]


class DataQualityRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for data quality rules"""
    
    queryset = DataQualityRule.objects.all()
    serializer_class = DataQualityRuleSerializer
    permission_classes = [permissions.IsAuthenticated]


class DataLineageViewSet(viewsets.ModelViewSet):
    """ViewSet for data lineage"""
    
    queryset = DataLineage.objects.all()
    serializer_class = DataLineageSerializer
    permission_classes = [permissions.IsAuthenticated]


class DataManagementStatsView(viewsets.ViewSet):
    """ViewSet for data management statistics"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics"""
        
        # Get date range for statistics
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        stats = {
            'import_jobs': {
                'total': DataImportJob.objects.count(),
                'recent': DataImportJob.objects.filter(created_at__gte=start_date).count(),
                'successful': DataImportJob.objects.filter(status='completed').count(),
                'failed': DataImportJob.objects.filter(status='failed').count(),
                'processing': DataImportJob.objects.filter(status='processing').count(),
            },
            'export_jobs': {
                'total': DataExportJob.objects.count(),
                'recent': DataExportJob.objects.filter(created_at__gte=start_date).count(),
                'successful': DataExportJob.objects.filter(status='completed').count(),
                'failed': DataExportJob.objects.filter(status='failed').count(),
                'processing': DataExportJob.objects.filter(status='processing').count(),
            },
            'data_mappings': {
                'total': DataMapping.objects.count(),
                'active': DataMapping.objects.filter(is_active=True).count(),
            },
            'sync_jobs': {
                'total': DataSyncJob.objects.count(),
                'active': DataSyncJob.objects.filter(status='active').count(),
                'paused': DataSyncJob.objects.filter(status='paused').count(),
            },
            'backups': {
                'total': DataBackup.objects.count(),
                'recent': DataBackup.objects.filter(created_at__gte=start_date).count(),
                'successful': DataBackup.objects.filter(status='completed').count(),
            },
            'quality_rules': {
                'total': DataQualityRule.objects.count(),
                'active': DataQualityRule.objects.filter(is_active=True).count(),
            }
        }
        
        return Response(stats)