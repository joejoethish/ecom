from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
import yaml
import csv
import io
from typing import Dict, Any

from .models import (
    SystemSetting, SettingCategory, SettingChangeHistory, SettingBackup,
    SettingTemplate, SettingDependency, SettingNotification, SettingAuditLog,
    SettingEnvironmentSync
)
from .serializers import (
    SystemSettingSerializer, SystemSettingCreateUpdateSerializer,
    SettingCategorySerializer, SettingChangeHistorySerializer,
    SettingBackupSerializer, SettingBackupCreateSerializer, SettingBackupRestoreSerializer,
    SettingTemplateSerializer, SettingTemplateCreateSerializer, SettingTemplateApplySerializer,
    SettingDependencySerializer, SettingNotificationSerializer,
    SettingAuditLogSerializer, SettingEnvironmentSyncSerializer,
    SettingSearchSerializer, SettingBulkUpdateSerializer,
    SettingExportSerializer, SettingImportSerializer,
    SettingComplianceSerializer, SettingMonitoringSerializer
)
from .services import (
    SettingsValidationService, SettingsBackupService, SettingsChangeService,
    SettingsTemplateService, SettingsNotificationService,
    SettingsEnvironmentSyncService, SettingsSearchService,
    SettingsPerformanceService
)


class SystemSettingViewSet(viewsets.ModelViewSet):
    """Comprehensive viewset for system settings management"""
    queryset = SystemSetting.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SystemSettingCreateUpdateSerializer
        return SystemSettingSerializer
    
    def get_queryset(self):
        queryset = SystemSetting.objects.select_related('category', 'created_by', 'updated_by')
        
        # Filter by environment
        environment = self.request.query_params.get('environment', 'production')
        queryset = queryset.filter(environment=environment)
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by access level based on user permissions
        user = self.request.user
        if not user.is_superuser:
            if user.is_staff:
                queryset = queryset.exclude(access_level='superuser')
            else:
                queryset = queryset.filter(access_level='public')
        
        return queryset.filter(is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        old_instance = self.get_object()
        new_value = serializer.validated_data.get('value', old_instance.value)
        
        # Use change service for proper tracking
        if new_value != old_instance.value:
            SettingsChangeService.update_setting(
                old_instance,
                new_value,
                self.request.user,
                change_reason=f"Updated via API"
            )
        else:
            serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced search for settings"""
        serializer = SettingSearchSerializer(data=request.data)
        if serializer.is_valid():
            settings = SettingsSearchService.search_settings(
                query=serializer.validated_data.get('query', ''),
                category_id=serializer.validated_data.get('category_id'),
                environment=serializer.validated_data.get('environment', 'production'),
                filters={
                    k: v for k, v in serializer.validated_data.items()
                    if k not in ['query', 'category_id', 'environment'] and v is not None
                }
            )
            
            result_serializer = SystemSettingSerializer(settings, many=True)
            return Response(result_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update multiple settings"""
        serializer = SettingBulkUpdateSerializer(data=request.data)
        if serializer.is_valid():
            settings_data = serializer.validated_data['settings']
            change_reason = serializer.validated_data.get('change_reason', 'Bulk update via API')
            
            results = {
                'updated': 0,
                'errors': [],
                'skipped': 0
            }
            
            for setting_data in settings_data:
                try:
                    setting = SystemSetting.objects.get(key=setting_data['key'])
                    if setting_data['value'] != setting.value:
                        SettingsChangeService.update_setting(
                            setting,
                            setting_data['value'],
                            request.user,
                            change_reason=change_reason
                        )
                        results['updated'] += 1
                    else:
                        results['skipped'] += 1
                except SystemSetting.DoesNotExist:
                    results['errors'].append(f"Setting {setting_data['key']} not found")
                except Exception as e:
                    results['errors'].append(f"Error updating {setting_data['key']}: {str(e)}")
            
            return Response(results)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """Export settings to various formats"""
        serializer = SettingExportSerializer(data=request.data)
        if serializer.is_valid():
            category_ids = serializer.validated_data.get('category_ids')
            environment = serializer.validated_data.get('environment', 'production')
            format_type = serializer.validated_data.get('format', 'json')
            include_sensitive = serializer.validated_data.get('include_sensitive', False)
            
            queryset = SystemSetting.objects.filter(
                environment=environment,
                is_active=True
            )
            
            if category_ids:
                queryset = queryset.filter(category_id__in=category_ids)
            
            if not include_sensitive:
                queryset = queryset.filter(is_sensitive=False)
            
            settings_data = []
            for setting in queryset:
                settings_data.append({
                    'key': setting.key,
                    'display_name': setting.display_name,
                    'description': setting.description,
                    'category': setting.category.name,
                    'data_type': setting.data_type,
                    'value': setting.get_decrypted_value() if include_sensitive else setting.value,
                    'default_value': setting.default_value,
                    'help_text': setting.help_text,
                    'is_required': setting.is_required,
                    'requires_restart': setting.requires_restart,
                })
            
            if format_type == 'json':
                response = HttpResponse(
                    json.dumps(settings_data, indent=2),
                    content_type='application/json'
                )
                response['Content-Disposition'] = f'attachment; filename="settings_{environment}.json"'
            
            elif format_type == 'yaml':
                response = HttpResponse(
                    yaml.dump(settings_data, default_flow_style=False),
                    content_type='application/x-yaml'
                )
                response['Content-Disposition'] = f'attachment; filename="settings_{environment}.yaml"'
            
            elif format_type == 'csv':
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=settings_data[0].keys() if settings_data else [])
                writer.writeheader()
                writer.writerows(settings_data)
                
                response = HttpResponse(output.getvalue(), content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="settings_{environment}.csv"'
            
            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def import_settings(self, request):
        """Import settings from file"""
        serializer = SettingImportSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            format_type = serializer.validated_data['format']
            conflict_resolution = serializer.validated_data.get('conflict_resolution', 'skip')
            validate_only = serializer.validated_data.get('validate_only', False)
            
            try:
                file_content = file.read().decode('utf-8')
                
                if format_type == 'json':
                    settings_data = json.loads(file_content)
                elif format_type == 'yaml':
                    settings_data = yaml.safe_load(file_content)
                elif format_type == 'csv':
                    reader = csv.DictReader(io.StringIO(file_content))
                    settings_data = list(reader)
                
                results = {
                    'imported': 0,
                    'skipped': 0,
                    'errors': [],
                    'validation_errors': []
                }
                
                for setting_data in settings_data:
                    try:
                        existing_setting = SystemSetting.objects.filter(
                            key=setting_data['key']
                        ).first()
                        
                        if validate_only:
                            # Just validate, don't import
                            if existing_setting:
                                if not SettingsValidationService.validate_setting_value(
                                    existing_setting, setting_data['value']
                                ):
                                    results['validation_errors'].append(
                                        f"Invalid value for {setting_data['key']}"
                                    )
                            continue
                        
                        if existing_setting:
                            if conflict_resolution == 'skip':
                                results['skipped'] += 1
                                continue
                            elif conflict_resolution == 'overwrite':
                                SettingsChangeService.update_setting(
                                    existing_setting,
                                    setting_data['value'],
                                    request.user,
                                    change_reason="Imported from file"
                                )
                                results['imported'] += 1
                        else:
                            results['errors'].append(f"Setting {setting_data['key']} not found")
                    
                    except Exception as e:
                        results['errors'].append(f"Error processing {setting_data.get('key', 'unknown')}: {str(e)}")
                
                return Response(results)
            
            except Exception as e:
                return Response(
                    {'error': f"Failed to parse file: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def change_history(self, request, pk=None):
        """Get change history for a setting"""
        setting = self.get_object()
        history = SettingChangeHistory.objects.filter(setting=setting).order_by('-changed_at')
        
        page = self.paginate_queryset(history)
        if page is not None:
            serializer = SettingChangeHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SettingChangeHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def audit_log(self, request, pk=None):
        """Get audit log for a setting"""
        setting = self.get_object()
        audit_logs = SettingAuditLog.objects.filter(setting=setting).order_by('-timestamp')
        
        page = self.paginate_queryset(audit_logs)
        if page is not None:
            serializer = SettingAuditLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SettingAuditLogSerializer(audit_logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """Rollback setting to a previous version"""
        setting = self.get_object()
        version = request.data.get('version')
        
        if not version:
            return Response(
                {'error': 'Version number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            change_record = SettingChangeHistory.objects.get(
                setting=setting,
                version=version
            )
            
            SettingsChangeService.update_setting(
                setting,
                change_record.old_value,
                request.user,
                change_reason=f"Rollback to version {version}"
            )
            
            return Response({'message': f'Setting rolled back to version {version}'})
        
        except SettingChangeHistory.DoesNotExist:
            return Response(
                {'error': f'Version {version} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def performance_impact(self, request, pk=None):
        """Get performance impact analysis for a setting"""
        setting = self.get_object()
        impact = SettingsPerformanceService.analyze_performance_impact(setting)
        return Response(impact)
    
    @action(detail=True, methods=['post'])
    def sync_to_environment(self, request, pk=None):
        """Sync setting to another environment"""
        setting = self.get_object()
        target_environment = request.data.get('target_environment')
        
        if not target_environment:
            return Response(
                {'error': 'Target environment is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            sync_record = SettingsEnvironmentSyncService.sync_setting_to_environment(
                setting, target_environment, request.user
            )
            
            serializer = SettingEnvironmentSyncSerializer(sync_record)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SettingCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for setting categories"""
    queryset = SettingCategory.objects.all()
    serializer_class = SettingCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SettingCategory.objects.filter(is_active=True).order_by('order', 'name')
    
    @action(detail=True, methods=['get'])
    def settings(self, request, pk=None):
        """Get all settings in a category"""
        category = self.get_object()
        settings = SystemSetting.objects.filter(
            category=category,
            is_active=True
        ).order_by('display_name')
        
        serializer = SystemSettingSerializer(settings, many=True)
        return Response(serializer.data)


class SettingBackupViewSet(viewsets.ModelViewSet):
    """ViewSet for settings backups"""
    queryset = SettingBackup.objects.all()
    serializer_class = SettingBackupSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SettingBackup.objects.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        """Create a new settings backup"""
        serializer = SettingBackupCreateSerializer(data=request.data)
        if serializer.is_valid():
            backup = SettingsBackupService.create_backup(
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                user=request.user,
                category_ids=serializer.validated_data.get('category_ids'),
                environment=serializer.validated_data.get('environment', 'production')
            )
            
            result_serializer = SettingBackupSerializer(backup)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore settings from backup"""
        backup = self.get_object()
        serializer = SettingBackupRestoreSerializer(data=request.data)
        
        if serializer.is_valid():
            results = SettingsBackupService.restore_backup(
                backup,
                request.user,
                conflict_resolution=serializer.validated_data.get('conflict_resolution', 'skip')
            )
            
            return Response(results)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SettingTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for settings templates"""
    queryset = SettingTemplate.objects.all()
    serializer_class = SettingTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = SettingTemplate.objects.order_by('name')
        
        # Filter by public templates or user's own templates
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(is_public=True) | Q(created_by=self.request.user)
            )
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def create_from_category(self, request):
        """Create template from category settings"""
        serializer = SettingTemplateCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                category = SettingCategory.objects.get(
                    id=serializer.validated_data['category_id']
                )
                
                template = SettingsTemplateService.create_template_from_category(
                    category=category,
                    name=serializer.validated_data['name'],
                    description=serializer.validated_data.get('description', ''),
                    user=request.user
                )
                
                result_serializer = SettingTemplateSerializer(template)
                return Response(result_serializer.data, status=status.HTTP_201_CREATED)
            
            except SettingCategory.DoesNotExist:
                return Response(
                    {'error': 'Category not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply a settings template"""
        template = self.get_object()
        serializer = SettingTemplateApplySerializer(data=request.data)
        
        if serializer.is_valid():
            results = SettingsTemplateService.apply_template(
                template,
                request.user,
                overwrite_existing=serializer.validated_data.get('overwrite_existing', False)
            )
            
            return Response(results)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SettingChangeHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for setting change history"""
    queryset = SettingChangeHistory.objects.all()
    serializer_class = SettingChangeHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SettingChangeHistory.objects.select_related(
            'setting', 'changed_by', 'approved_by'
        ).order_by('-changed_at')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a pending change"""
        change_record = self.get_object()
        
        if change_record.approval_status != 'pending':
            return Response(
                {'error': 'Change is not pending approval'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            SettingsChangeService.approve_change(change_record, request.user)
            return Response({'message': 'Change approved successfully'})
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a pending change"""
        change_record = self.get_object()
        
        if change_record.approval_status != 'pending':
            return Response(
                {'error': 'Change is not pending approval'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        change_record.approval_status = 'rejected'
        change_record.approved_by = request.user
        change_record.approved_at = timezone.now()
        change_record.save()
        
        return Response({'message': 'Change rejected'})


class SettingAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for settings audit logs"""
    queryset = SettingAuditLog.objects.all()
    serializer_class = SettingAuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SettingAuditLog.objects.select_related(
            'setting', 'user'
        ).order_by('-timestamp')
    
    @action(detail=False, methods=['post'])
    def compliance_report(self, request):
        """Generate compliance report"""
        serializer = SettingComplianceSerializer(data=request.data)
        if serializer.is_valid():
            start_date = serializer.validated_data.get('start_date')
            end_date = serializer.validated_data.get('end_date')
            compliance_flags = serializer.validated_data.get('compliance_flags', [])
            environment = serializer.validated_data.get('environment', 'production')
            
            queryset = SettingAuditLog.objects.all()
            
            if start_date:
                queryset = queryset.filter(timestamp__gte=start_date)
            if end_date:
                queryset = queryset.filter(timestamp__lte=end_date)
            if compliance_flags:
                queryset = queryset.filter(compliance_flags__overlap=compliance_flags)
            
            # Filter by environment through setting relationship
            queryset = queryset.filter(setting__environment=environment)
            
            audit_logs = queryset.order_by('-timestamp')
            result_serializer = SettingAuditLogSerializer(audit_logs, many=True)
            
            return Response({
                'total_events': audit_logs.count(),
                'compliance_flags': compliance_flags,
                'period': {
                    'start': start_date,
                    'end': end_date
                },
                'events': result_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)