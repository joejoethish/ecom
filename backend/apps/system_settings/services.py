from django.db import transaction
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json
import requests
from typing import Dict, List, Any, Optional

User = get_user_model()
from .models import (
    SystemSetting, SettingCategory, SettingChangeHistory, SettingBackup,
    SettingTemplate, SettingDependency, SettingNotification, SettingAuditLog,
    SettingEnvironmentSync
)


class SettingsValidationService:
    """Service for comprehensive settings validation"""
    
    @staticmethod
    def validate_setting_value(setting: SystemSetting, value: str) -> bool:
        """Validate a setting value against all rules"""
        try:
            # Create temporary setting instance for validation
            temp_setting = SystemSetting(
                key=setting.key,
                data_type=setting.data_type,
                value=value,
                min_value=setting.min_value,
                max_value=setting.max_value,
                min_length=setting.min_length,
                max_length=setting.max_length,
                regex_pattern=setting.regex_pattern,
                allowed_values=setting.allowed_values,
                is_required=setting.is_required
            )
            temp_setting.clean()
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def validate_dependencies(setting: SystemSetting, value: str) -> List[str]:
        """Validate setting dependencies"""
        errors = []
        
        for dependency in setting.dependencies.all():
            if dependency.dependency_type == 'required':
                if not dependency.depends_on.value:
                    errors.append(f"Required dependency '{dependency.depends_on.display_name}' is not set")
            
            elif dependency.dependency_type == 'conditional':
                condition = dependency.condition or {}
                if SettingsValidationService._check_condition(dependency.depends_on, condition):
                    if not value:
                        errors.append(f"Setting is required when '{dependency.depends_on.display_name}' meets condition")
            
            elif dependency.dependency_type == 'exclusive':
                if dependency.depends_on.value and value:
                    errors.append(f"Cannot be set when '{dependency.depends_on.display_name}' is also set")
        
        return errors
    
    @staticmethod
    def _check_condition(setting: SystemSetting, condition: Dict) -> bool:
        """Check if a condition is met"""
        setting_value = setting.get_typed_value()
        
        if 'equals' in condition:
            return setting_value == condition['equals']
        elif 'not_equals' in condition:
            return setting_value != condition['not_equals']
        elif 'greater_than' in condition:
            return setting_value > condition['greater_than']
        elif 'less_than' in condition:
            return setting_value < condition['less_than']
        elif 'in' in condition:
            return setting_value in condition['in']
        
        return False


class SettingsBackupService:
    """Service for settings backup and restore"""
    
    @staticmethod
    def create_backup(name: str, description: str, user: User, 
                     category_ids: Optional[List[int]] = None,
                     environment: str = 'production') -> SettingBackup:
        """Create a comprehensive settings backup"""
        
        query = SystemSetting.objects.filter(environment=environment, is_active=True)
        if category_ids:
            query = query.filter(category_id__in=category_ids)
        
        settings_data = []
        for setting in query:
            settings_data.append({
                'key': setting.key,
                'value': setting.value,
                'category': setting.category.name,
                'data_type': setting.data_type,
                'is_encrypted': setting.is_encrypted,
                'version': setting.version,
                'metadata': {
                    'display_name': setting.display_name,
                    'description': setting.description,
                    'help_text': setting.help_text,
                    'access_level': setting.access_level,
                    'requires_restart': setting.requires_restart,
                }
            })
        
        # Convert categories to serializable format
        categories_data = []
        for category in SettingCategory.objects.all():
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'display_name': category.display_name,
                'description': category.description,
                'parent_id': category.parent_id,
                'order': category.order,
                'icon': category.icon,
                'is_active': category.is_active,
                'created_at': category.created_at.isoformat(),
                'updated_at': category.updated_at.isoformat(),
            })
        
        backup_data = {
            'settings': settings_data,
            'categories': categories_data,
            'backup_metadata': {
                'created_at': timezone.now().isoformat(),
                'environment': environment,
                'total_settings': len(settings_data),
            }
        }
        
        return SettingBackup.objects.create(
            name=name,
            description=description,
            backup_data=backup_data,
            created_by=user,
            environment=environment
        )
    
    @staticmethod
    def restore_backup(backup: SettingBackup, user: User, 
                      conflict_resolution: str = 'skip') -> Dict[str, Any]:
        """Restore settings from backup with conflict resolution"""
        
        results = {
            'restored': 0,
            'skipped': 0,
            'errors': [],
            'conflicts': []
        }
        
        backup_settings = backup.backup_data.get('settings', [])
        
        with transaction.atomic():
            for setting_data in backup_settings:
                try:
                    existing_setting = SystemSetting.objects.filter(
                        key=setting_data['key']
                    ).first()
                    
                    if existing_setting:
                        if conflict_resolution == 'skip':
                            results['skipped'] += 1
                            continue
                        elif conflict_resolution == 'overwrite':
                            SettingsChangeService.update_setting(
                                existing_setting, 
                                setting_data['value'], 
                                user,
                                change_reason=f"Restored from backup: {backup.name}"
                            )
                            results['restored'] += 1
                        elif conflict_resolution == 'version':
                            if setting_data['version'] > existing_setting.version:
                                SettingsChangeService.update_setting(
                                    existing_setting, 
                                    setting_data['value'], 
                                    user,
                                    change_reason=f"Restored from backup: {backup.name}"
                                )
                                results['restored'] += 1
                            else:
                                results['skipped'] += 1
                    else:
                        # Create new setting
                        category = SettingCategory.objects.filter(
                            name=setting_data['category']
                        ).first()
                        
                        if category:
                            SystemSetting.objects.create(
                                key=setting_data['key'],
                                value=setting_data['value'],
                                category=category,
                                data_type=setting_data['data_type'],
                                is_encrypted=setting_data['is_encrypted'],
                                created_by=user,
                                **setting_data.get('metadata', {})
                            )
                            results['restored'] += 1
                        else:
                            results['errors'].append(f"Category not found for {setting_data['key']}")
                
                except Exception as e:
                    results['errors'].append(f"Error restoring {setting_data['key']}: {str(e)}")
        
        return results


class SettingsChangeService:
    """Service for managing setting changes with approval workflow"""
    
    @staticmethod
    def update_setting(setting: SystemSetting, new_value: str, user: User,
                      change_reason: str = '', requires_approval: bool = None) -> SettingChangeHistory:
        """Update a setting with change tracking"""
        
        old_value = setting.value
        
        # Validate new value
        if not SettingsValidationService.validate_setting_value(setting, new_value):
            raise ValidationError("Invalid setting value")
        
        # Check dependencies
        dependency_errors = SettingsValidationService.validate_dependencies(setting, new_value)
        if dependency_errors:
            raise ValidationError(dependency_errors)
        
        # Determine if approval is required
        if requires_approval is None:
            requires_approval = setting.is_sensitive or setting.requires_restart
        
        with transaction.atomic():
            # Create change history record
            change_record = SettingChangeHistory.objects.create(
                setting=setting,
                old_value=old_value,
                new_value=new_value,
                version=setting.version + 1,
                change_reason=change_reason,
                changed_by=user,
                requires_approval=requires_approval,
                approval_status='pending' if requires_approval else 'approved'
            )
            
            # Update setting if no approval required
            if not requires_approval:
                setting.value = new_value
                setting.version += 1
                setting.updated_by = user
                setting.save()
                
                # Create audit log
                SettingAuditLog.objects.create(
                    setting=setting,
                    action='update',
                    user=user,
                    details={
                        'old_value': old_value,
                        'new_value': new_value,
                        'change_reason': change_reason
                    }
                )
                
                # Send notifications
                SettingsNotificationService.send_change_notifications(setting, old_value, new_value, user)
        
        return change_record
    
    @staticmethod
    def approve_change(change_record: SettingChangeHistory, approver: User) -> bool:
        """Approve a pending setting change"""
        
        if change_record.approval_status != 'pending':
            raise ValidationError("Change is not pending approval")
        
        with transaction.atomic():
            change_record.approved_by = approver
            change_record.approved_at = timezone.now()
            change_record.approval_status = 'approved'
            change_record.save()
            
            # Apply the change
            setting = change_record.setting
            old_value = setting.value
            setting.value = change_record.new_value
            setting.version = change_record.version
            setting.updated_by = change_record.changed_by
            setting.save()
            
            # Create audit log
            SettingAuditLog.objects.create(
                setting=setting,
                action='update',
                user=approver,
                details={
                    'approved_change': change_record.id,
                    'original_user': change_record.changed_by.username,
                    'old_value': old_value,
                    'new_value': change_record.new_value
                }
            )
            
            # Send notifications
            SettingsNotificationService.send_change_notifications(
                setting, old_value, change_record.new_value, change_record.changed_by
            )
        
        return True


class SettingsTemplateService:
    """Service for settings templates"""
    
    @staticmethod
    def create_template_from_category(category: SettingCategory, name: str, 
                                    description: str, user: User) -> SettingTemplate:
        """Create a template from all settings in a category"""
        
        settings = SystemSetting.objects.filter(category=category, is_active=True)
        template_data = []
        
        for setting in settings:
            template_data.append({
                'key': setting.key,
                'value': setting.value,
                'data_type': setting.data_type,
                'metadata': {
                    'display_name': setting.display_name,
                    'description': setting.description,
                    'help_text': setting.help_text,
                }
            })
        
        return SettingTemplate.objects.create(
            name=name,
            description=description,
            template_data={'settings': template_data},
            category=category,
            created_by=user
        )
    
    @staticmethod
    def apply_template(template: SettingTemplate, user: User, 
                      overwrite_existing: bool = False) -> Dict[str, Any]:
        """Apply a settings template"""
        
        results = {
            'applied': 0,
            'skipped': 0,
            'errors': []
        }
        
        template_settings = template.template_data.get('settings', [])
        
        with transaction.atomic():
            for setting_data in template_settings:
                try:
                    existing_setting = SystemSetting.objects.filter(
                        key=setting_data['key']
                    ).first()
                    
                    if existing_setting:
                        if overwrite_existing:
                            SettingsChangeService.update_setting(
                                existing_setting,
                                setting_data['value'],
                                user,
                                change_reason=f"Applied template: {template.name}"
                            )
                            results['applied'] += 1
                        else:
                            results['skipped'] += 1
                    else:
                        results['errors'].append(f"Setting {setting_data['key']} not found")
                
                except Exception as e:
                    results['errors'].append(f"Error applying {setting_data['key']}: {str(e)}")
            
            # Update usage count
            template.usage_count += 1
            template.save()
        
        return results


class SettingsNotificationService:
    """Service for settings notifications"""
    
    @staticmethod
    def send_change_notifications(setting: SystemSetting, old_value: str, 
                                new_value: str, user: User):
        """Send notifications for setting changes"""
        
        notifications = SettingNotification.objects.filter(
            setting=setting, is_active=True
        )
        
        for notification in notifications:
            try:
                if notification.notification_type == 'email':
                    SettingsNotificationService._send_email_notification(
                        notification, setting, old_value, new_value, user
                    )
                elif notification.notification_type == 'webhook':
                    SettingsNotificationService._send_webhook_notification(
                        notification, setting, old_value, new_value, user
                    )
                elif notification.notification_type == 'slack':
                    SettingsNotificationService._send_slack_notification(
                        notification, setting, old_value, new_value, user
                    )
            except Exception as e:
                # Log notification failure but don't block the setting change
                SettingAuditLog.objects.create(
                    setting=setting,
                    action='notification_failed',
                    user=user,
                    details={
                        'notification_type': notification.notification_type,
                        'error': str(e)
                    }
                )
    
    @staticmethod
    def _send_email_notification(notification: SettingNotification, setting: SystemSetting,
                               old_value: str, new_value: str, user: User):
        """Send email notification"""
        subject = f"Setting Changed: {setting.display_name}"
        message = f"""
        Setting: {setting.display_name} ({setting.key})
        Changed by: {user.get_full_name() or user.username}
        Old value: {old_value}
        New value: {new_value}
        Time: {timezone.now()}
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=notification.recipients,
            fail_silently=False
        )
    
    @staticmethod
    def _send_webhook_notification(notification: SettingNotification, setting: SystemSetting,
                                 old_value: str, new_value: str, user: User):
        """Send webhook notification"""
        payload = {
            'event': 'setting_changed',
            'setting': {
                'key': setting.key,
                'display_name': setting.display_name,
                'old_value': old_value,
                'new_value': new_value,
            },
            'user': {
                'username': user.username,
                'full_name': user.get_full_name(),
            },
            'timestamp': timezone.now().isoformat()
        }
        
        for webhook_url in notification.recipients:
            requests.post(webhook_url, json=payload, timeout=10)
    
    @staticmethod
    def _send_slack_notification(notification: SettingNotification, setting: SystemSetting,
                               old_value: str, new_value: str, user: User):
        """Send Slack notification"""
        payload = {
            'text': f"Setting Changed: {setting.display_name}",
            'attachments': [{
                'color': 'warning',
                'fields': [
                    {'title': 'Setting', 'value': f"{setting.display_name} ({setting.key})", 'short': True},
                    {'title': 'Changed by', 'value': user.get_full_name() or user.username, 'short': True},
                    {'title': 'Old value', 'value': old_value, 'short': True},
                    {'title': 'New value', 'value': new_value, 'short': True},
                ]
            }]
        }
        
        for webhook_url in notification.recipients:
            requests.post(webhook_url, json=payload, timeout=10)


class SettingsEnvironmentSyncService:
    """Service for synchronizing settings across environments"""
    
    @staticmethod
    def sync_setting_to_environment(setting: SystemSetting, target_environment: str,
                                  user: User) -> SettingEnvironmentSync:
        """Sync a setting to another environment"""
        
        sync_record = SettingEnvironmentSync.objects.get_or_create(
            setting=setting,
            source_environment=setting.environment,
            target_environment=target_environment,
            defaults={'sync_status': 'pending'}
        )[0]
        
        try:
            # Find or create setting in target environment
            target_setting = SystemSetting.objects.filter(
                key=setting.key,
                environment=target_environment
            ).first()
            
            if target_setting:
                # Update existing setting
                SettingsChangeService.update_setting(
                    target_setting,
                    setting.value,
                    user,
                    change_reason=f"Synced from {setting.environment}"
                )
            else:
                # Create new setting in target environment
                SystemSetting.objects.create(
                    key=setting.key,
                    display_name=setting.display_name,
                    description=setting.description,
                    category=setting.category,
                    data_type=setting.data_type,
                    value=setting.value,
                    default_value=setting.default_value,
                    environment=target_environment,
                    created_by=user,
                    # Copy other attributes...
                )
            
            sync_record.sync_status = 'synced'
            sync_record.last_sync_at = timezone.now()
            sync_record.save()
            
        except Exception as e:
            sync_record.sync_status = 'failed'
            sync_record.sync_details = {'error': str(e)}
            sync_record.save()
            raise
        
        return sync_record


class SettingsSearchService:
    """Service for searching and filtering settings"""
    
    @staticmethod
    def search_settings(query: str, category_id: Optional[int] = None,
                       environment: str = 'production',
                       filters: Optional[Dict] = None) -> List[SystemSetting]:
        """Search settings with comprehensive filtering"""
        
        queryset = SystemSetting.objects.filter(
            environment=environment,
            is_active=True
        )
        
        if query:
            queryset = queryset.filter(
                models.Q(key__icontains=query) |
                models.Q(display_name__icontains=query) |
                models.Q(description__icontains=query) |
                models.Q(help_text__icontains=query)
            )
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        if filters:
            if 'data_type' in filters:
                queryset = queryset.filter(data_type=filters['data_type'])
            if 'access_level' in filters:
                queryset = queryset.filter(access_level=filters['access_level'])
            if 'requires_restart' in filters:
                queryset = queryset.filter(requires_restart=filters['requires_restart'])
            if 'is_sensitive' in filters:
                queryset = queryset.filter(is_sensitive=filters['is_sensitive'])
        
        return queryset.select_related('category').order_by('category__order', 'display_name')


class SettingsPerformanceService:
    """Service for analyzing settings performance impact"""
    
    @staticmethod
    def analyze_performance_impact(setting: SystemSetting) -> Dict[str, Any]:
        """Analyze potential performance impact of a setting change"""
        
        impact_analysis = {
            'restart_required': setting.requires_restart,
            'cache_invalidation': [],
            'dependent_services': [],
            'estimated_impact': 'low'
        }
        
        # Check for cache-related settings
        if 'cache' in setting.key.lower():
            impact_analysis['cache_invalidation'].append('application_cache')
            impact_analysis['estimated_impact'] = 'medium'
        
        # Check for database-related settings
        if 'database' in setting.key.lower() or 'db' in setting.key.lower():
            impact_analysis['dependent_services'].append('database')
            impact_analysis['estimated_impact'] = 'high'
        
        # Check dependencies
        dependent_settings = SystemSetting.objects.filter(
            dependencies__depends_on=setting
        )
        
        if dependent_settings.exists():
            impact_analysis['dependent_settings'] = [
                s.key for s in dependent_settings
            ]
            if len(impact_analysis['dependent_settings']) > 5:
                impact_analysis['estimated_impact'] = 'high'
        
        return impact_analysis