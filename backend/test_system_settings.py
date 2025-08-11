#!/usr/bin/env python
"""
Test script for comprehensive system settings management functionality.
"""
import os
import sys
import django
from django.test import TestCase
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from apps.system_settings.models import (
    SystemSetting, SettingCategory, SettingChangeHistory, SettingBackup,
    SettingTemplate, SettingDependency, SettingDataType
)
from apps.system_settings.services import (
    SettingsValidationService, SettingsBackupService, SettingsChangeService,
    SettingsTemplateService, SettingsSearchService
)

User = get_user_model()

def test_basic_functionality():
    """Test basic system settings functionality"""
    print("🔧 Testing System Settings Management...")
    
    # Create test user
    import uuid
    from django.db import connection
    
    try:
        user = User.objects.get(username='settings_test_user')
        created = False
    except User.DoesNotExist:
        # Create user with raw SQL to handle uuid field
        user_uuid = uuid.uuid4().hex
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO auth_user (
                    password, last_login, is_superuser, username, first_name, last_name,
                    is_staff, is_active, date_joined, created_at, updated_at, email,
                    user_type, phone_number, date_of_birth, gender, avatar,
                    is_verified, is_phone_verified, is_email_verified,
                    newsletter_subscription, sms_notifications, email_notifications,
                    bio, website, customer_group_id, uuid
                ) VALUES (
                    'pbkdf2_sha256$600000$test$test', NULL, 0, %s, %s, %s,
                    0, 1, NOW(), NOW(), NOW(), %s,
                    'customer', NULL, NULL, '', NULL,
                    0, 0, 0,
                    1, 1, 1,
                    '', '', NULL, %s
                )
            """, ['settings_test_user', 'Test', 'User', 'test@example.com', user_uuid])
        
        user = User.objects.get(username='settings_test_user')
        created = True
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create test category
    category, created = SettingCategory.objects.get_or_create(
        name='test_category',
        defaults={
            'display_name': 'Test Category',
            'description': 'A category for testing system settings',
            'order': 1
        }
    )
    
    print(f"✅ Created category: {category.display_name}")
    
    # Create test settings
    settings_data = [
        {
            'key': 'app_name',
            'display_name': 'Application Name',
            'description': 'The name of the application',
            'data_type': SettingDataType.STRING,
            'value': 'E-Commerce Platform',
            'default_value': 'My App',
            'help_text': 'This appears in the browser title and headers'
        },
        {
            'key': 'max_items_per_page',
            'display_name': 'Max Items Per Page',
            'description': 'Maximum number of items to display per page',
            'data_type': SettingDataType.INTEGER,
            'value': '20',
            'default_value': '10',
            'min_value': 5,
            'max_value': 100,
            'help_text': 'Controls pagination size across the application'
        },
        {
            'key': 'enable_notifications',
            'display_name': 'Enable Notifications',
            'description': 'Whether to send email notifications',
            'data_type': SettingDataType.BOOLEAN,
            'value': 'true',
            'default_value': 'false',
            'help_text': 'Turn on/off email notifications for users'
        },
        {
            'key': 'api_config',
            'display_name': 'API Configuration',
            'description': 'JSON configuration for API settings',
            'data_type': SettingDataType.JSON,
            'value': '{"timeout": 30, "retries": 3}',
            'default_value': '{}',
            'help_text': 'Advanced API configuration in JSON format'
        }
    ]
    
    created_settings = []
    for setting_data in settings_data:
        setting, created = SystemSetting.objects.get_or_create(
            key=setting_data['key'],
            defaults={
                **setting_data,
                'category': category,
                'created_by': user
            }
        )
        created_settings.append(setting)
        print(f"✅ Created setting: {setting.display_name} = {setting.get_typed_value()}")
    
    return user, category, created_settings

def test_validation_service():
    """Test settings validation service"""
    print("\n🔍 Testing Settings Validation Service...")
    
    user, category, settings = test_basic_functionality()
    
    # Test integer validation
    int_setting = next(s for s in settings if s.data_type == SettingDataType.INTEGER)
    
    # Valid value
    is_valid = SettingsValidationService.validate_setting_value(int_setting, '15')
    print(f"✅ Valid integer (15): {is_valid}")
    
    # Invalid value (below min)
    is_valid = SettingsValidationService.validate_setting_value(int_setting, '3')
    print(f"❌ Invalid integer below min (3): {is_valid}")
    
    # Invalid value (above max)
    is_valid = SettingsValidationService.validate_setting_value(int_setting, '150')
    print(f"❌ Invalid integer above max (150): {is_valid}")
    
    # Test JSON validation
    json_setting = next(s for s in settings if s.data_type == SettingDataType.JSON)
    
    # Valid JSON
    is_valid = SettingsValidationService.validate_setting_value(json_setting, '{"valid": true}')
    print(f"✅ Valid JSON: {is_valid}")
    
    # Invalid JSON
    is_valid = SettingsValidationService.validate_setting_value(json_setting, 'invalid_json')
    print(f"❌ Invalid JSON: {is_valid}")

def test_change_service():
    """Test settings change service with tracking"""
    print("\n📝 Testing Settings Change Service...")
    
    user, category, settings = test_basic_functionality()
    
    # Update a setting
    string_setting = next(s for s in settings if s.data_type == SettingDataType.STRING)
    old_value = string_setting.value
    new_value = 'Updated E-Commerce Platform'
    
    change_record = SettingsChangeService.update_setting(
        string_setting,
        new_value,
        user,
        change_reason='Testing change tracking'
    )
    
    print(f"✅ Updated setting: {string_setting.key}")
    print(f"   Old value: {old_value}")
    print(f"   New value: {new_value}")
    print(f"   Change record ID: {change_record.id}")
    print(f"   Version: {change_record.version}")
    
    # Verify the setting was updated
    string_setting.refresh_from_db()
    print(f"✅ Setting value after update: {string_setting.value}")
    print(f"✅ Setting version after update: {string_setting.version}")

def test_backup_service():
    """Test settings backup and restore service"""
    print("\n💾 Testing Settings Backup Service...")
    
    user, category, settings = test_basic_functionality()
    
    # Create a backup
    backup = SettingsBackupService.create_backup(
        name='Test Backup',
        description='A test backup of system settings',
        user=user
    )
    
    print(f"✅ Created backup: {backup.name}")
    print(f"   Settings count: {len(backup.backup_data['settings'])}")
    print(f"   Created at: {backup.created_at}")
    
    # Modify a setting
    setting_to_modify = settings[0]
    original_value = setting_to_modify.value
    setting_to_modify.value = 'Modified Value'
    setting_to_modify.save()
    
    print(f"✅ Modified setting {setting_to_modify.key} to: {setting_to_modify.value}")
    
    # Restore backup
    results = SettingsBackupService.restore_backup(
        backup,
        user,
        conflict_resolution='overwrite'
    )
    
    print(f"✅ Restored backup:")
    print(f"   Restored: {results['restored']}")
    print(f"   Skipped: {results['skipped']}")
    print(f"   Errors: {len(results['errors'])}")
    
    # Verify restoration
    setting_to_modify.refresh_from_db()
    print(f"✅ Setting value after restore: {setting_to_modify.value}")

def test_template_service():
    """Test settings template service"""
    print("\n📋 Testing Settings Template Service...")
    
    user, category, settings = test_basic_functionality()
    
    # Create template from category
    try:
        template = SettingTemplate.objects.get(name='Test Template')
    except SettingTemplate.DoesNotExist:
        template = SettingsTemplateService.create_template_from_category(
            category=category,
            name='Test Template',
            description='A template created from test category',
            user=user
        )
    
    print(f"✅ Created template: {template.name}")
    print(f"   Settings count: {len(template.template_data['settings'])}")
    
    # Modify some settings
    for setting in settings[:2]:
        setting.value = f"Modified_{setting.value}"
        setting.save()
    
    print("✅ Modified some settings")
    
    # Apply template
    results = SettingsTemplateService.apply_template(
        template,
        user,
        overwrite_existing=True
    )
    
    print(f"✅ Applied template:")
    print(f"   Applied: {results['applied']}")
    print(f"   Skipped: {results['skipped']}")
    print(f"   Errors: {len(results['errors'])}")

def test_search_service():
    """Test settings search service"""
    print("\n🔍 Testing Settings Search Service...")
    
    user, category, settings = test_basic_functionality()
    
    # Search by query
    results = SettingsSearchService.search_settings(
        query='notification',
        environment='production'
    )
    
    print(f"✅ Search for 'notification': {len(results)} results")
    for result in results:
        print(f"   - {result.key}: {result.display_name}")
    
    # Search by data type
    results = SettingsSearchService.search_settings(
        query='',
        filters={'data_type': SettingDataType.BOOLEAN}
    )
    
    print(f"✅ Search for boolean settings: {len(results)} results")
    for result in results:
        print(f"   - {result.key}: {result.get_typed_value()}")

def test_hierarchical_categories():
    """Test hierarchical category structure"""
    print("\n🏗️ Testing Hierarchical Categories...")
    
    # Create parent category
    parent_category = SettingCategory.objects.create(
        name='system',
        display_name='System Settings',
        description='Core system configuration',
        order=1
    )
    
    # Create child categories
    child_categories = [
        {
            'name': 'database',
            'display_name': 'Database Settings',
            'description': 'Database configuration options'
        },
        {
            'name': 'email',
            'display_name': 'Email Settings',
            'description': 'Email service configuration'
        },
        {
            'name': 'security',
            'display_name': 'Security Settings',
            'description': 'Security and authentication settings'
        }
    ]
    
    for child_data in child_categories:
        child = SettingCategory.objects.create(
            parent=parent_category,
            order=2,
            **child_data
        )
        print(f"✅ Created child category: {child.get_full_path()}")

def test_setting_dependencies():
    """Test setting dependencies"""
    print("\n🔗 Testing Setting Dependencies...")
    
    user, category, settings = test_basic_functionality()
    
    # Create dependent settings
    master_setting = SystemSetting.objects.create(
        key='enable_advanced_features',
        display_name='Enable Advanced Features',
        description='Master switch for advanced features',
        category=category,
        data_type=SettingDataType.BOOLEAN,
        value='true',
        default_value='false',
        created_by=user
    )
    
    dependent_setting = SystemSetting.objects.create(
        key='advanced_cache_size',
        display_name='Advanced Cache Size',
        description='Cache size for advanced features',
        category=category,
        data_type=SettingDataType.INTEGER,
        value='100',
        default_value='50',
        min_value=10,
        max_value=1000,
        created_by=user
    )
    
    # Create dependency
    dependency = SettingDependency.objects.create(
        setting=dependent_setting,
        depends_on=master_setting,
        dependency_type='conditional',
        condition={'equals': True}
    )
    
    print(f"✅ Created dependency: {dependent_setting.key} depends on {master_setting.key}")
    
    # Test dependency validation
    master_setting.value = 'false'
    master_setting.save()
    
    errors = SettingsValidationService.validate_dependencies(dependent_setting, '200')
    print(f"✅ Dependency validation errors when master is false: {len(errors)}")
    
    master_setting.value = 'true'
    master_setting.save()
    
    errors = SettingsValidationService.validate_dependencies(dependent_setting, '200')
    print(f"✅ Dependency validation errors when master is true: {len(errors)}")

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive System Settings Tests...\n")
    
    try:
        test_basic_functionality()
        test_validation_service()
        test_change_service()
        test_backup_service()
        test_template_service()
        test_search_service()
        test_hierarchical_categories()
        test_setting_dependencies()
        
        print("\n🎉 All tests completed successfully!")
        
        # Print summary
        print("\n📊 System Settings Summary:")
        print(f"   Categories: {SettingCategory.objects.count()}")
        print(f"   Settings: {SystemSetting.objects.count()}")
        print(f"   Change History: {SettingChangeHistory.objects.count()}")
        print(f"   Backups: {SettingBackup.objects.count()}")
        print(f"   Templates: {SettingTemplate.objects.count()}")
        print(f"   Dependencies: {SettingDependency.objects.count()}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)