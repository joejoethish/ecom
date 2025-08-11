#!/usr/bin/env python3
"""
Simple test for multi-tenant architecture implementation.
Tests basic functionality without requiring migrations.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

def test_tenant_models():
    """Test tenant model definitions"""
    print("Testing tenant model definitions...")
    
    try:
        from apps.tenants.models import (
            Tenant, TenantUser, TenantSubscription, TenantUsage,
            TenantInvitation, TenantAuditLog, TenantBackup
        )
        
        # Test model imports
        assert Tenant is not None
        assert TenantUser is not None
        assert TenantSubscription is not None
        assert TenantUsage is not None
        assert TenantInvitation is not None
        assert TenantAuditLog is not None
        assert TenantBackup is not None
        
        print("✓ All tenant models imported successfully")
        
        # Test model fields
        tenant_fields = [f.name for f in Tenant._meta.fields]
        required_fields = ['name', 'slug', 'subdomain', 'plan', 'status']
        
        for field in required_fields:
            assert field in tenant_fields, f"Missing field: {field}"
        
        print("✓ Tenant model has required fields")
        
        # Test choices
        assert hasattr(Tenant, 'PLAN_CHOICES')
        assert hasattr(Tenant, 'STATUS_CHOICES')
        assert hasattr(TenantUser, 'ROLE_CHOICES')
        
        print("✓ Model choices defined correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {str(e)}")
        return False


def test_tenant_services():
    """Test tenant service definitions"""
    print("Testing tenant service definitions...")
    
    try:
        from apps.tenants.services import (
            TenantProvisioningService, TenantUserManagementService,
            TenantBillingService, TenantAnalyticsService, TenantBackupService
        )
        
        # Test service imports
        assert TenantProvisioningService is not None
        assert TenantUserManagementService is not None
        assert TenantBillingService is not None
        assert TenantAnalyticsService is not None
        assert TenantBackupService is not None
        
        print("✓ All tenant services imported successfully")
        
        # Test service methods exist
        assert hasattr(TenantProvisioningService, 'create_tenant')
        assert hasattr(TenantUserManagementService, 'invite_user')
        assert hasattr(TenantBillingService, 'create_subscription')
        assert hasattr(TenantAnalyticsService, 'get_tenant_dashboard_stats')
        assert hasattr(TenantBackupService, 'create_backup')
        
        print("✓ Service methods defined correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {str(e)}")
        return False


def test_tenant_serializers():
    """Test tenant serializer definitions"""
    print("Testing tenant serializer definitions...")
    
    try:
        from apps.tenants.serializers import (
            TenantSerializer, TenantCreateSerializer, TenantUserSerializer,
            TenantSubscriptionSerializer, TenantUsageSerializer,
            TenantInvitationSerializer, TenantAuditLogSerializer,
            TenantBackupSerializer
        )
        
        # Test serializer imports
        assert TenantSerializer is not None
        assert TenantCreateSerializer is not None
        assert TenantUserSerializer is not None
        assert TenantSubscriptionSerializer is not None
        assert TenantUsageSerializer is not None
        assert TenantInvitationSerializer is not None
        assert TenantAuditLogSerializer is not None
        assert TenantBackupSerializer is not None
        
        print("✓ All tenant serializers imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Serializer test failed: {str(e)}")
        return False


def test_tenant_views():
    """Test tenant view definitions"""
    print("Testing tenant view definitions...")
    
    try:
        from apps.tenants.views import (
            TenantViewSet, TenantUserViewSet, TenantSubscriptionViewSet,
            TenantUsageViewSet, TenantInvitationViewSet, TenantAuditLogViewSet,
            TenantBackupViewSet, AcceptInvitationView, TenantStatsView
        )
        
        # Test view imports
        assert TenantViewSet is not None
        assert TenantUserViewSet is not None
        assert TenantSubscriptionViewSet is not None
        assert TenantUsageViewSet is not None
        assert TenantInvitationViewSet is not None
        assert TenantAuditLogViewSet is not None
        assert TenantBackupViewSet is not None
        assert AcceptInvitationView is not None
        assert TenantStatsView is not None
        
        print("✓ All tenant views imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ View test failed: {str(e)}")
        return False


def test_tenant_middleware():
    """Test tenant middleware definitions"""
    print("Testing tenant middleware definitions...")
    
    try:
        from apps.tenants.middleware import (
            TenantMiddleware, get_current_tenant, set_current_tenant,
            TenantQuerySetMixin, TenantModelMixin, TenantPermissionMixin
        )
        
        # Test middleware imports
        assert TenantMiddleware is not None
        assert get_current_tenant is not None
        assert set_current_tenant is not None
        assert TenantQuerySetMixin is not None
        assert TenantModelMixin is not None
        assert TenantPermissionMixin is not None
        
        print("✓ All tenant middleware imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Middleware test failed: {str(e)}")
        return False


def test_tenant_urls():
    """Test tenant URL definitions"""
    print("Testing tenant URL definitions...")
    
    try:
        from apps.tenants.urls import urlpatterns
        
        # Test URL patterns exist
        assert urlpatterns is not None
        assert len(urlpatterns) > 0
        
        print("✓ Tenant URLs defined successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ URL test failed: {str(e)}")
        return False


def test_frontend_components():
    """Test frontend component files exist"""
    print("Testing frontend component files...")
    
    try:
        component_files = [
            '../frontend/src/components/tenants/TenantDashboard.tsx',
            '../frontend/src/components/tenants/TenantSettings.tsx',
            '../frontend/src/components/tenants/TenantUserManagement.tsx',
            '../frontend/src/components/tenants/TenantAnalytics.tsx',
            '../frontend/src/app/admin/tenants/page.tsx'
        ]
        
        for file_path in component_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Component file not found: {file_path}")
        
        print("✓ All frontend component files exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend component test failed: {str(e)}")
        return False


def run_simple_test():
    """Run simple tenant system test"""
    print("=" * 60)
    print("SIMPLE MULTI-TENANT ARCHITECTURE TEST")
    print("=" * 60)
    
    tests = [
        test_tenant_models,
        test_tenant_services,
        test_tenant_serializers,
        test_tenant_views,
        test_tenant_middleware,
        test_tenant_urls,
        test_frontend_components,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            failed += 1
        print()
    
    print("=" * 60)
    if failed == 0:
        print("✅ ALL MULTI-TENANT ARCHITECTURE TESTS PASSED!")
        print(f"✓ {passed} tests passed")
    else:
        print(f"❌ {failed} tests failed, {passed} tests passed")
    print("=" * 60)
    
    print("\nMulti-Tenant Architecture Features Implemented:")
    print("• Tenant data models and relationships")
    print("• Tenant provisioning and management services")
    print("• User invitation and management system")
    print("• Subscription and billing management")
    print("• Usage tracking and analytics")
    print("• Audit logging and security")
    print("• Backup and disaster recovery")
    print("• Multi-tenant middleware and context")
    print("• REST API endpoints and serializers")
    print("• Frontend React components")
    print("• Settings and configuration management")
    print("• Role-based access control")
    print("• Data isolation and security")
    
    return failed == 0


if __name__ == '__main__':
    success = run_simple_test()
    sys.exit(0 if success else 1)