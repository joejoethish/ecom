#!/usr/bin/env python
"""
Simple test script for data management functionality.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')
django.setup()

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        # Test model imports
        from apps.data_management.models import (
            DataImportJob, DataExportJob, DataMapping, DataSyncJob,
            DataBackup, DataAuditLog, DataQualityRule, DataLineage
        )
        print("✓ Models imported successfully")
        
        # Test serializer imports
        from apps.data_management.serializers import (
            DataImportJobSerializer, DataExportJobSerializer, DataMappingSerializer,
            DataSyncJobSerializer, DataBackupSerializer, DataAuditLogSerializer,
            DataQualityRuleSerializer, DataLineageSerializer
        )
        print("✓ Serializers imported successfully")
        
        # Test service imports
        from apps.data_management.services import (
            DataImportService, DataExportService, DataTransformationService,
            DataQualityService
        )
        print("✓ Services imported successfully")
        
        # Test view imports
        from apps.data_management.views_simple import (
            DataImportJobViewSet, DataExportJobViewSet, DataMappingViewSet,
            DataSyncJobViewSet, DataBackupViewSet, DataAuditLogViewSet,
            DataQualityRuleViewSet, DataLineageViewSet, DataManagementStatsView
        )
        print("✓ Views imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


def test_services():
    """Test service initialization"""
    print("\nTesting services...")
    
    try:
        from apps.data_management.services import (
            DataImportService, DataExportService, DataTransformationService,
            DataQualityService
        )
        
        # Test service initialization
        import_service = DataImportService()
        export_service = DataExportService()
        transformation_service = DataTransformationService()
        quality_service = DataQualityService()
        
        print("✓ All services initialized successfully")
        
        # Test transformation service
        test_data = [{'name': 'test', 'value': '123'}]
        transformation_rules = {
            'name': [{'type': 'uppercase', 'parameters': {}}]
        }
        transformed = transformation_service.transform_data(test_data, transformation_rules)
        expected = [{'name': 'TEST', 'value': '123'}]
        
        if transformed == expected:
            print("✓ Transformation service working correctly")
        else:
            print(f"✗ Transformation failed: {transformed} != {expected}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Service error: {e}")
        return False


def test_url_patterns():
    """Test URL patterns"""
    print("\nTesting URL patterns...")
    
    try:
        from apps.data_management.urls import urlpatterns
        print(f"✓ URL patterns loaded: {len(urlpatterns)} patterns")
        
        # Check if router patterns exist
        router_found = False
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                router_found = True
                break
        
        if router_found:
            print("✓ Router patterns found")
        else:
            print("✗ No router patterns found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ URL pattern error: {e}")
        return False


def test_frontend_components():
    """Test that frontend components exist"""
    print("\nTesting frontend components...")
    
    try:
        import os
        
        # Check main page
        main_page = 'frontend/src/app/admin/data-management/page.tsx'
        if os.path.exists(main_page):
            print("✓ Main page component exists")
        else:
            print("✗ Main page component missing")
            return False
        
        # Check hooks
        hooks_file = 'frontend/src/app/admin/data-management/hooks/useDataManagement.ts'
        if os.path.exists(hooks_file):
            print("✓ Hooks file exists")
        else:
            print("✗ Hooks file missing")
            return False
        
        # Check components directory
        components_dir = 'frontend/src/app/admin/data-management/components'
        if os.path.exists(components_dir):
            component_files = os.listdir(components_dir)
            print(f"✓ Components directory exists with {len(component_files)} files")
        else:
            print("✗ Components directory missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Frontend component error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DATA MANAGEMENT SYSTEM - SIMPLE TEST")
    print("=" * 60)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test services
    if not test_services():
        success = False
    
    # Test URL patterns
    if not test_url_patterns():
        success = False
    
    # Test frontend components
    if not test_frontend_components():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL TESTS PASSED!")
        print("Data management system components are working correctly.")
        print("\nNext steps:")
        print("1. Run migrations: python manage.py makemigrations data_management")
        print("2. Apply migrations: python manage.py migrate")
        print("3. Set up defaults: python manage.py setup_data_management_defaults")
        print("4. Access the admin panel at /admin/data-management/")
    else:
        print("✗ SOME TESTS FAILED!")
        print("Please check the errors above.")
    print("=" * 60)
    
    return success


if __name__ == '__main__':
    main()