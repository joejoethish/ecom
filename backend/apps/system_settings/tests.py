from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from .models import (
    SystemSetting, SettingCategory, SettingChangeHistory, SettingBackup,
    SettingTemplate, SettingDependency, SettingDataType
)
from .services import (
    SettingsValidationService, SettingsBackupService, SettingsChangeService,
    SettingsTemplateService
)


class SystemSettingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = SettingCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )

    def test_setting_creation(self):
        """Test basic setting creation"""
        setting = SystemSetting.objects.create(
            key='test_setting',
            display_name='Test Setting',
            description='A test setting',
            category=self.category,
            data_type=SettingDataType.STRING,
            value='test_value',
            default_value='default_value',
            created_by=self.user
        )
        
        self.assertEqual(setting.key, 'test_setting')
        self.assertEqual(setting.get_typed_value(), 'test_value')
        self.assertEqual(setting.version, 1)

    def test_integer_validation(self):
        """Test integer data type validation"""
        setting = SystemSetting(
            key='int_setting',
            display_name='Integer Setting',
            category=self.category,
            data_type=SettingDataType.INTEGER,
            value='123',
            default_value='0'
        )
        
        # Should not raise exception
        setting.clean()
        self.assertEqual(setting.get_typed_value(), 123)
        
        # Test invalid integer
        setting.value = 'not_an_integer'
        with self.assertRaises(ValidationError):
            setting.clean()

    def test_boolean_validation(self):
        """Test boolean data type validation"""
        setting = SystemSetting(
            key='bool_setting',
            display_name='Boolean Setting',
            category=self.category,
            data_type=SettingDataType.BOOLEAN,
            value='true',
            default_value='false'
        )
        
        setting.clean()
        self.assertTrue(setting.get_typed_value())
        
        setting.value = 'false'
        setting.clean()
        self.assertFalse(setting.get_typed_value())

    def test_json_validation(self):
        """Test JSON data type validation"""
        setting = SystemSetting(
            key='json_setting',
            display_name='JSON Setting',
            category=self.category,
            data_type=SettingDataType.JSON,
            value='{"key": "value"}',
            default_value='{}'
        )
        
        setting.clean()
        self.assertEqual(setting.get_typed_value(), {"key": "value"})
        
        # Test invalid JSON
        setting.value = 'invalid_json'
        with self.assertRaises(ValidationError):
            setting.clean()

    def test_constraint_validation(self):
        """Test constraint validation"""
        setting = SystemSetting(
            key='constrained_setting',
            display_name='Constrained Setting',
            category=self.category,
            data_type=SettingDataType.INTEGER,
            value='50',
            default_value='0',
            min_value=10,
            max_value=100
        )
        
        # Valid value
        setting.clean()
        
        # Test min constraint
        setting.value = '5'
        with self.assertRaises(ValidationError):
            setting.clean()
        
        # Test max constraint
        setting.value = '150'
        with self.assertRaises(ValidationError):
            setting.clean()

    def test_allowed_values_validation(self):
        """Test allowed values constraint"""
        setting = SystemSetting(
            key='enum_setting',
            display_name='Enum Setting',
            category=self.category,
            data_type=SettingDataType.STRING,
            value='option1',
            default_value='option1',
            allowed_values=['option1', 'option2', 'option3']
        )
        
        # Valid value
        setting.clean()
        
        # Invalid value
        setting.value = 'invalid_option'
        with self.assertRaises(ValidationError):
            setting.clean()


class SettingCategoryModelTest(TestCase):
    def test_hierarchical_categories(self):
        """Test hierarchical category structure"""
        parent = SettingCategory.objects.create(
            name='parent',
            display_name='Parent Category'
        )
        
        child = SettingCategory.objects.create(
            name='child',
            display_name='Child Category',
            parent=parent
        )
        
        self.assertEqual(child.get_full_path(), 'Parent Category > Child Category')
        self.assertEqual(parent.get_full_path(), 'Parent Category')


class SettingsValidationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = SettingCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )

    def test_validate_setting_value(self):
        """Test setting value validation service"""
        setting = SystemSetting.objects.create(
            key='test_setting',
            display_name='Test Setting',
            category=self.category,
            data_type=SettingDataType.INTEGER,
            value='10',
            default_value='0',
            min_value=5,
            max_value=15,
            created_by=self.user
        )
        
        # Valid value
        self.assertTrue(
            SettingsValidationService.validate_setting_value(setting, '12')
        )
        
        # Invalid value (below min)
        self.assertFalse(
            SettingsValidationService.validate_setting_value(setting, '3')
        )
        
        # Invalid value (above max)
        self.assertFalse(
            SettingsValidationService.validate_setting_value(setting, '20')
        )

    def test_validate_dependencies(self):
        """Test dependency validation"""
        setting1 = SystemSetting.objects.create(
            key='setting1',
            display_name='Setting 1',
            category=self.category,
            data_type=SettingDataType.BOOLEAN,
            value='true',
            default_value='false',
            created_by=self.user
        )
        
        setting2 = SystemSetting.objects.create(
            key='setting2',
            display_name='Setting 2',
            category=self.category,
            data_type=SettingDataType.STRING,
            value='',
            default_value='',
            created_by=self.user
        )
        
        # Create dependency
        SettingDependency.objects.create(
            setting=setting2,
            depends_on=setting1,
            dependency_type='required'
        )
        
        # Test validation with dependency not met
        setting1.value = ''
        setting1.save()
        
        errors = SettingsValidationService.validate_dependencies(setting2, 'some_value')
        self.assertTrue(len(errors) > 0)


class SettingsBackupServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = SettingCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )
        
        # Create test settings
        for i in range(3):
            SystemSetting.objects.create(
                key=f'test_setting_{i}',
                display_name=f'Test Setting {i}',
                category=self.category,
                data_type=SettingDataType.STRING,
                value=f'value_{i}',
                default_value='default',
                created_by=self.user
            )

    def test_create_backup(self):
        """Test backup creation"""
        backup = SettingsBackupService.create_backup(
            name='Test Backup',
            description='A test backup',
            user=self.user
        )
        
        self.assertEqual(backup.name, 'Test Backup')
        self.assertEqual(len(backup.backup_data['settings']), 3)
        self.assertEqual(backup.created_by, self.user)

    def test_restore_backup(self):
        """Test backup restoration"""
        # Create backup
        backup = SettingsBackupService.create_backup(
            name='Test Backup',
            description='A test backup',
            user=self.user
        )
        
        # Modify a setting
        setting = SystemSetting.objects.get(key='test_setting_0')
        original_value = setting.value
        setting.value = 'modified_value'
        setting.save()
        
        # Restore backup
        results = SettingsBackupService.restore_backup(
            backup, self.user, conflict_resolution='overwrite'
        )
        
        # Check restoration
        setting.refresh_from_db()
        self.assertEqual(setting.value, original_value)
        self.assertEqual(results['restored'], 3)


class SettingsChangeServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = SettingCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )
        self.setting = SystemSetting.objects.create(
            key='test_setting',
            display_name='Test Setting',
            category=self.category,
            data_type=SettingDataType.STRING,
            value='original_value',
            default_value='default',
            created_by=self.user
        )

    def test_update_setting(self):
        """Test setting update with change tracking"""
        old_value = self.setting.value
        new_value = 'new_value'
        
        change_record = SettingsChangeService.update_setting(
            self.setting,
            new_value,
            self.user,
            change_reason='Test update'
        )
        
        # Check setting was updated
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.value, new_value)
        self.assertEqual(self.setting.version, 2)
        
        # Check change record
        self.assertEqual(change_record.old_value, old_value)
        self.assertEqual(change_record.new_value, new_value)
        self.assertEqual(change_record.changed_by, self.user)

    def test_approval_workflow(self):
        """Test setting change approval workflow"""
        # Create sensitive setting requiring approval
        self.setting.is_sensitive = True
        self.setting.save()
        
        change_record = SettingsChangeService.update_setting(
            self.setting,
            'new_sensitive_value',
            self.user,
            change_reason='Sensitive change'
        )
        
        # Setting should not be updated yet
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.value, 'original_value')
        self.assertEqual(change_record.approval_status, 'pending')
        
        # Approve change
        approver = User.objects.create_user(
            username='approver',
            email='approver@example.com',
            password='approverpass123'
        )
        
        SettingsChangeService.approve_change(change_record, approver)
        
        # Setting should now be updated
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.value, 'new_sensitive_value')
        
        change_record.refresh_from_db()
        self.assertEqual(change_record.approval_status, 'approved')
        self.assertEqual(change_record.approved_by, approver)


class SettingsTemplateServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = SettingCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )
        
        # Create test settings
        for i in range(2):
            SystemSetting.objects.create(
                key=f'template_setting_{i}',
                display_name=f'Template Setting {i}',
                category=self.category,
                data_type=SettingDataType.STRING,
                value=f'template_value_{i}',
                default_value='default',
                created_by=self.user
            )

    def test_create_template_from_category(self):
        """Test template creation from category"""
        template = SettingsTemplateService.create_template_from_category(
            category=self.category,
            name='Test Template',
            description='A test template',
            user=self.user
        )
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.category, self.category)
        self.assertEqual(len(template.template_data['settings']), 2)

    def test_apply_template(self):
        """Test template application"""
        # Create template
        template = SettingsTemplateService.create_template_from_category(
            category=self.category,
            name='Test Template',
            description='A test template',
            user=self.user
        )
        
        # Modify settings
        setting = SystemSetting.objects.get(key='template_setting_0')
        setting.value = 'modified_value'
        setting.save()
        
        # Apply template
        results = SettingsTemplateService.apply_template(
            template, self.user, overwrite_existing=True
        )
        
        # Check application
        setting.refresh_from_db()
        self.assertEqual(setting.value, 'template_value_0')
        self.assertEqual(results['applied'], 2)


class SystemSettingAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)
        
        self.category = SettingCategory.objects.create(
            name='test_category',
            display_name='Test Category'
        )
        
        self.setting = SystemSetting.objects.create(
            key='api_test_setting',
            display_name='API Test Setting',
            category=self.category,
            data_type=SettingDataType.STRING,
            value='api_test_value',
            default_value='default',
            created_by=self.user
        )

    def test_list_settings(self):
        """Test listing settings via API"""
        url = '/api/system-settings/settings/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['key'], 'api_test_setting')

    def test_create_setting(self):
        """Test creating setting via API"""
        url = '/api/system-settings/settings/'
        data = {
            'key': 'new_api_setting',
            'display_name': 'New API Setting',
            'category': self.category.id,
            'data_type': SettingDataType.STRING,
            'value': 'new_value',
            'default_value': 'default'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check setting was created
        setting = SystemSetting.objects.get(key='new_api_setting')
        self.assertEqual(setting.display_name, 'New API Setting')

    def test_update_setting(self):
        """Test updating setting via API"""
        url = f'/api/system-settings/settings/{self.setting.id}/'
        data = {
            'value': 'updated_api_value'
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check setting was updated
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.value, 'updated_api_value')

    def test_search_settings(self):
        """Test settings search via API"""
        url = '/api/system-settings/settings/search/'
        data = {
            'query': 'api_test'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_bulk_update_settings(self):
        """Test bulk update via API"""
        # Create another setting
        setting2 = SystemSetting.objects.create(
            key='bulk_test_setting',
            display_name='Bulk Test Setting',
            category=self.category,
            data_type=SettingDataType.STRING,
            value='bulk_value',
            default_value='default',
            created_by=self.user
        )
        
        url = '/api/system-settings/settings/bulk_update/'
        data = {
            'settings': [
                {'key': 'api_test_setting', 'value': 'bulk_updated_1'},
                {'key': 'bulk_test_setting', 'value': 'bulk_updated_2'}
            ],
            'change_reason': 'Bulk update test'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated'], 2)
        
        # Check settings were updated
        self.setting.refresh_from_db()
        setting2.refresh_from_db()
        self.assertEqual(self.setting.value, 'bulk_updated_1')
        self.assertEqual(setting2.value, 'bulk_updated_2')

    @patch('apps.system_settings.views.HttpResponse')
    def test_export_settings(self, mock_response):
        """Test settings export via API"""
        url = '/api/system-settings/settings/export/'
        data = {
            'format': 'json',
            'environment': 'production'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_history(self):
        """Test getting change history via API"""
        # Create a change
        SettingsChangeService.update_setting(
            self.setting,
            'history_test_value',
            self.user,
            change_reason='History test'
        )
        
        url = f'/api/system-settings/settings/{self.setting.id}/change_history/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_rollback_setting(self):
        """Test setting rollback via API"""
        # Create a change
        change_record = SettingsChangeService.update_setting(
            self.setting,
            'rollback_test_value',
            self.user,
            change_reason='Rollback test'
        )
        
        url = f'/api/system-settings/settings/{self.setting.id}/rollback/'
        data = {'version': change_record.version}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check setting was rolled back
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.value, 'api_test_value')  # Original value