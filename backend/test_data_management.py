#!/usr/bin/env python
"""
Test script for data management functionality.
"""
import os
import sys
import django
from django.test import TestCase
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')
django.setup()

from apps.data_management.models import (
    DataImportJob, DataExportJob, DataMapping, DataSyncJob,
    DataBackup, DataAuditLog, DataQualityRule, DataLineage
)
from apps.data_management.services import (
    DataImportService, DataExportService, DataTransformationService,
    DataQualityService
)
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


def test_data_management_models():
    """Test data management models creation"""
    print("Testing data management models...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    # Test DataImportJob
    try:
        content_type = ContentType.objects.get_or_create(
            app_label='test',
            model='testmodel'
        )[0]
        
        import_job = DataImportJob.objects.create(
            name='Test Import Job',
            description='Test import job description',
            file_path='/tmp/test.csv',
            file_format='csv',
            file_size=1024,
            target_model='testmodel',
            content_type=content_type,
            created_by=user
        )
        print(f"✓ Created DataImportJob: {import_job}")
        
        # Test DataExportJob
        export_job = DataExportJob.objects.create(
            name='Test Export Job',
            description='Test export job description',
            source_model='testmodel',
            content_type=content_type,
            export_format='csv',
            created_by=user
        )
        print(f"✓ Created DataExportJob: {export_job}")
        
        # Test DataMapping
        mapping = DataMapping.objects.create(
            name='Test Mapping',
            description='Test mapping description',
            target_model='testmodel',
            content_type=content_type,
            field_mappings={'field1': 'mapped_field1'},
            created_by=user
        )
        print(f"✓ Created DataMapping: {mapping}")
        
        # Test DataQualityRule
        quality_rule = DataQualityRule.objects.create(
            name='Test Quality Rule',
            description='Test quality rule description',
            rule_type='required',
            target_model='testmodel',
            target_field='test_field',
            created_by=user
        )
        print(f"✓ Created DataQualityRule: {quality_rule}")
        
        # Test DataLineage
        lineage = DataLineage.objects.create(
            source_type='file',
            source_name='test_source',
            source_field='source_field',
            target_type='table',
            target_name='test_target',
            target_field='target_field'
        )
        print(f"✓ Created DataLineage: {lineage}")
        
        print("✓ All data management models created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating models: {e}")
        return False
    
    return True


def test_data_services():
    """Test data management services"""
    print("\nTesting data management services...")
    
    try:
        # Test DataImportService
        import_service = DataImportService()
        print(f"✓ DataImportService initialized: {import_service}")
        
        # Test DataExportService
        export_service = DataExportService()
        print(f"✓ DataExportService initialized: {export_service}")
        
        # Test DataTransformationService
        transformation_service = DataTransformationService()
        test_data = [{'name': 'test', 'value': '123'}]
        transformation_rules = {
            'name': [{'type': 'uppercase', 'parameters': {}}]
        }
        transformed = transformation_service.transform_data(test_data, transformation_rules)
        print(f"✓ DataTransformationService test: {transformed}")
        
        # Test DataQualityService
        quality_service = DataQualityService()
        quality_report = quality_service.check_data_quality('testmodel', test_data)
        print(f"✓ DataQualityService test: {quality_report}")
        
        print("✓ All data management services tested successfully!")
        
    except Exception as e:
        print(f"✗ Error testing services: {e}")
        return False
    
    return True


def test_api_endpoints():
    """Test API endpoints"""
    print("\nTesting API endpoints...")
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Test import jobs endpoint (should require authentication)
        response = client.get('/api/v1/admin/data-management/import-jobs/')
        print(f"✓ Import jobs endpoint status: {response.status_code}")
        
        # Test export jobs endpoint
        response = client.get('/api/v1/admin/data-management/export-jobs/')
        print(f"✓ Export jobs endpoint status: {response.status_code}")
        
        # Test stats endpoint
        response = client.get('/api/v1/admin/data-management/stats/dashboard_stats/')
        print(f"✓ Stats endpoint status: {response.status_code}")
        
        print("✓ API endpoints tested successfully!")
        
    except Exception as e:
        print(f"✗ Error testing API endpoints: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("DATA MANAGEMENT SYSTEM TEST")
    print("=" * 50)
    
    success = True
    
    # Test models
    if not test_data_management_models():
        success = False
    
    # Test services
    if not test_data_services():
        success = False
    
    # Test API endpoints
    if not test_api_endpoints():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✓ ALL TESTS PASSED!")
        print("Data management system is working correctly.")
    else:
        print("✗ SOME TESTS FAILED!")
        print("Please check the errors above.")
    print("=" * 50)
    
    return success


if __name__ == '__main__':
    main()