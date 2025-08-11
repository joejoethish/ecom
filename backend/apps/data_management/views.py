from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse, Http404
from django.core.files.storage import default_storage
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    DataImportJob, DataExportJob, DataMapping, DataSyncJob,
    DataBackup, DataAuditLog, DataQualityRule, DataLineage
)
from .serializers import (
    DataImportJobSerializer, DataExportJobSerializer, DataMappingSerializer,
    DataSyncJobSerializer, DataBackupSerializer, DataAuditLogSerializer,
    DataQualityRuleSerializer, DataLineageSerializer, ImportJobCreateSerializer,
    ExportJobCreateSerializer, DataValidationResultSerializer,
    BulkOperationSerializer
)
from .services import DataImportService, DataExportService, DataQualityService

logger = logging.getLogger(__name__)


class DataImportJobViewSet(viewsets.ModelViewSet):
    """ViewSet for data import jobs"""
    
    queryset = DataImportJob.objects.all()
    serializer_class = DataImportJobSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Filter by target model
        target_model = self.request.query_params.get('target_model')
        if target_model:
            queryset = queryset.filter(target_model=target_model)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create a new import job"""
        serializer = ImportJobCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Handle file upload
                uploaded_file = request.FILES.get('file')
                if not uploaded_file:
                    return Response(
                        {'error': 'No file uploaded'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Save file
                file_path = f"imports/{uploaded_file.name}"
                saved_path = default_storage.save(file_path, uploaded_file)
                
                # Create import job
                service = DataImportService()
                job = service.create_import_job(
                    user=request.user,
                    file_path=saved_path,
                    **serializer.validated_data
                )
                
                response_serializer = DataImportJobSerializer(job)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Error creating import job: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an import job"""
        self.check_permissions(['data_management.change_dataimportjob'])
        
        job = self.get_object()
        if job.status in ['pending', 'processing']:
            job.status = 'cancelled'
            job.save()
            return Response({'message': 'Job cancelled successfully'})
        
        return Response(
            {'error': 'Job cannot be cancelled'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed import job"""
        self.check_permissions(['data_management.change_dataimportjob'])
        
        job = self.get_object()
        if job.status == 'failed':
            job.status = 'pending'
            job.progress_percentage = 0
            job.processed_records = 0
            job.successful_records = 0
            job.failed_records = 0
            job.error_log = []
            job.validation_errors = []
            job.save()
            
            # Restart processing
            from .services import process_import_job
            process_import_job.delay(str(job.id))
            
            return Response({'message': 'Job restarted successfully'})
        
        return Response(
            {'error': 'Job cannot be retried'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def validate(self, request, pk=None):
        """Validate import data without processing"""
        self.check_permissions(['data_management.view_dataimportjob'])
        
        job = self.get_object()
        service = DataImportService()
        
        try:
            validation_results = service.validate_import_data(job)
            serializer = DataValidationResultSerializer(validation_results)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error validating import data: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on import jobs"""
        self.check_permissions(['data_management.change_dataimportjob'])
        
        serializer = BulkOperationSerializer(data=request.data)
        if serializer.is_valid():
            operation = serializer.validated_data['operation']
            job_ids = serializer.validated_data['job_ids']
            
            jobs = DataImportJob.objects.filter(id__in=job_ids)
            
            if operation == 'delete':
                jobs.delete()
            elif operation == 'cancel':
                jobs.filter(status__in=['pending', 'processing']).update(status='cancelled')
            elif operation == 'retry':
                failed_jobs = jobs.filter(status='failed')
                for job in failed_jobs:
                    job.status = 'pending'
                    job.progress_percentage = 0
                    job.processed_records = 0
                    job.successful_records = 0
                    job.failed_records = 0
                    job.error_log = []
                    job.validation_errors = []
                    job.save()
                    
                    from .services import process_import_job
                    process_import_job.delay(str(job.id))
            
            return Response({'message': f'Bulk {operation} completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataExportJobViewSet(AdminPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for data export jobs"""
    
    queryset = DataExportJob.objects.all()
    serializer_class = DataExportJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_permissions = ['data_management.view_dataexportjob']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by export format
        format_filter = self.request.query_params.get('format')
        if format_filter:
            queryset = queryset.filter(export_format=format_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create a new export job"""
        self.check_permissions(['data_management.add_dataexportjob'])
        
        serializer = ExportJobCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = DataExportService()
                job = service.create_export_job(
                    user=request.user,
                    **serializer.validated_data
                )
                
                response_serializer = DataExportJobSerializer(job)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Error creating export job: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download export file"""
        self.check_permissions(['data_management.view_dataexportjob'])
        
        job = self.get_object()
        
        if job.status != 'completed' or not job.file_path:
            return Response(
                {'error': 'Export file not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not default_storage.exists(job.file_path):
            return Response(
                {'error': 'Export file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            file_content = default_storage.open(job.file_path, 'rb').read()
            
            response = HttpResponse(
                file_content,
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{job.file_path.split("/")[-1]}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error downloading export file: {str(e)}")
            return Response(
                {'error': 'Error downloading file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an export job"""
        self.check_permissions(['data_management.change_dataexportjob'])
        
        job = self.get_object()
        if job.status in ['pending', 'processing']:
            job.status = 'cancelled'
            job.save()
            return Response({'message': 'Job cancelled successfully'})
        
        return Response(
            {'error': 'Job cannot be cancelled'},
            status=status.HTTP_400_BAD_REQUEST
        )


class DataMappingViewSet(AdminPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for data mappings"""
    
    queryset = DataMapping.objects.all()
    serializer_class = DataMappingSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_permissions = ['data_management.view_datamapping']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by target model
        target_model = self.request.query_params.get('target_model')
        if target_model:
            queryset = queryset.filter(target_model=target_model)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        self.check_permissions(['data_management.add_datamapping'])
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        self.check_permissions(['data_management.change_datamapping'])
        serializer.save()
    
    def perform_destroy(self, instance):
        self.check_permissions(['data_management.delete_datamapping'])
        super().perform_destroy(instance)


class DataSyncJobViewSet(AdminPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for data sync jobs"""
    
    queryset = DataSyncJob.objects.all()
    serializer_class = DataSyncJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_permissions = ['data_management.view_datasyncjob']
    
    def perform_create(self, serializer):
        self.check_permissions(['data_management.add_datasyncjob'])
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        self.check_permissions(['data_management.change_datasyncjob'])
        serializer.save()
    
    def perform_destroy(self, instance):
        self.check_permissions(['data_management.delete_datasyncjob'])
        super().perform_destroy(instance)
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Run sync job immediately"""
        self.check_permissions(['data_management.change_datasyncjob'])
        
        job = self.get_object()
        if job.status == 'active':
            # Trigger sync job
            # Implementation would depend on specific sync requirements
            return Response({'message': 'Sync job started'})
        
        return Response(
            {'error': 'Job is not active'},
            status=status.HTTP_400_BAD_REQUEST
        )


class DataBackupViewSet(AdminPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for data backups"""
    
    queryset = DataBackup.objects.all()
    serializer_class = DataBackupSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_permissions = ['data_management.view_databackup']
    
    def perform_create(self, serializer):
        self.check_permissions(['data_management.add_databackup'])
        serializer.save(created_by=self.request.user)
    
    def perform_destroy(self, instance):
        self.check_permissions(['data_management.delete_databackup'])
        # Delete backup file if it exists
        if instance.backup_path and default_storage.exists(instance.backup_path):
            default_storage.delete(instance.backup_path)
        super().perform_destroy(instance)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore from backup"""
        self.check_permissions(['data_management.change_databackup'])
        
        backup = self.get_object()
        if backup.status == 'completed':
            # Implementation would depend on specific restore requirements
            return Response({'message': 'Restore started'})
        
        return Response(
            {'error': 'Backup is not available for restore'},
            status=status.HTTP_400_BAD_REQUEST
        )


class DataAuditLogViewSet(AdminPermissionMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for data audit logs"""
    
    queryset = DataAuditLog.objects.all()
    serializer_class = DataAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_permissions = ['data_management.view_dataauditlog']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')


class DataQualityRuleViewSet(AdminPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for data quality rules"""
    
    queryset = DataQualityRule.objects.all()
    serializer_class = DataQualityRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_permissions = ['data_management.view_dataqualityrule']
    
    def perform_create(self, serializer):
        self.check_permissions(['data_management.add_dataqualityrule'])
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        self.check_permissions(['data_management.change_dataqualityrule'])
        serializer.save()
    
    def perform_destroy(self, instance):
        self.check_permissions(['data_management.delete_dataqualityrule'])
        super().perform_destroy(instance)
    
    @action(detail=False, methods=['post'])
    def check_quality(self, request):
        """Check data quality for a model"""
        self.check_permissions(['data_management.view_dataqualityrule'])
        
        model_name = request.data.get('model_name')
        if not model_name:
            return Response(
                {'error': 'model_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = DataQualityService()
            # This would need actual data to check
            # For now, return a placeholder response
            quality_report = {
                'total_records': 0,
                'quality_score': 100,
                'issues': [],
                'rule_results': []
            }
            
            return Response(quality_report)
            
        except Exception as e:
            logger.error(f"Error checking data quality: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DataLineageViewSet(AdminPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for data lineage"""
    
    queryset = DataLineage.objects.all()
    serializer_class = DataLineageSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_permissions = ['data_management.view_datalineage']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by source
        source_name = self.request.query_params.get('source_name')
        if source_name:
            queryset = queryset.filter(source_name=source_name)
        
        # Filter by target
        target_name = self.request.query_params.get('target_name')
        if target_name:
            queryset = queryset.filter(target_name=target_name)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def lineage_graph(self, request):
        """Get lineage graph data"""
        self.check_permissions(['data_management.view_datalineage'])
        
        lineage_data = DataLineage.objects.filter(is_active=True)
        
        nodes = set()
        edges = []
        
        for lineage in lineage_data:
            nodes.add(lineage.source_name)
            nodes.add(lineage.target_name)
            edges.append({
                'source': lineage.source_name,
                'target': lineage.target_name,
                'transformation': lineage.transformation_type
            })
        
        graph_data = {
            'nodes': [{'id': node, 'label': node} for node in nodes],
            'edges': edges
        }
        
        return Response(graph_data)


class DataManagementStatsView(AdminPermissionMixin, viewsets.ViewSet):
    """ViewSet for data management statistics"""
    
    permission_classes = [permissions.IsAuthenticated]
    required_permissions = ['data_management.view_stats']
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics"""
        self.check_permissions(['data_management.view_stats'])
        
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