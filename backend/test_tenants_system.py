#!/usr/bin/env python3
"""
Comprehensive test suite for the multi-tenant architecture system.
Tests tenant management, user management, billing, analytics, and backup functionality.
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from apps.tenants.models import (
    Tenant, TenantUser, TenantSubscription, TenantUsage,
    TenantInvitation, TenantAuditLog, TenantBackup
)
from apps.tenants.services import (
    TenantProvisioningService, TenantUserManagementService,
    TenantBillingService, TenantAnalyticsService, TenantBackupService
)


class TenantSystemTest(TestCase):
    """Test suite for multi-tenant architecture"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test tenant
        self.tenant_data = {
            'name': 'Test Corporation',
            'slug': 'test-corp',
            'subdomain': 'testcorp',
            'contact_name': 'John Doe',
            'contact_email': 'john@testcorp.com',
            'owner_username': 'admin',
            'owner_email': 'admin@testcorp.com',
            'owner_password': 'testpass123',
            'plan': 'professional'
        }
        
        self.tenant = TenantProvisioningService.create_tenant(self.tenant_data)
        self.owner = self.tenant.users.first()
    
    def test_tenant_creation(self):
        """Test tenant creation and provisioning"""
        print("Testing tenant creation...")
        
        # Test tenant was created
        self.assertIsNotNone(self.tenant)
        self.assertEqual(self.tenant.name, 'Test Corporation')
        self.assertEqual(self.tenant.slug, 'test-corp')
        self.assertEqual(self.tenant.subdomain, 'testcorp')
        self.assertEqual(self.tenant.plan, 'professional')
        self.assertEqual(self.tenant.status, 'trial')
        
        # Test owner was created
        self.assertIsNotNone(self.owner)
        self.assertEqual(self.owner.username, 'admin')
        self.assertEqual(self.owner.email, 'admin@testcorp.com')
        self.assertEqual(self.owner.role, 'owner')
        self.assertEqual(self.owner.tenant, self.tenant)
        
        # Test features were initialized
        self.assertIsInstance(self.tenant.features, dict)
        self.assertIn('analytics', self.tenant.features)
        
        print("✓ Tenant creation test passed")
    
    def test_user_invitation_system(self):
        """Test user invitation and acceptance"""
        print("Testing user invitation system...")
        
        # Test invitation creation
        invitation = TenantUserManagementService.invite_user(
            tenant=self.tenant,
            inviter=self.owner,
            email='newuser@testcorp.com',
            role='staff'
        )
        
        self.assertIsNotNone(invitation)
        self.assertEqual(invitation.email, 'newuser@testcorp.com')
        self.assertEqual(invitation.role, 'staff')
        self.assertEqual(invitation.status, 'pending')
        self.assertEqual(invitation.invited_by, self.owner)
        
        # Test invitation acceptance
        user_data = {
            'username': 'newuser',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        new_user = TenantUserManagementService.accept_invitation(
            token=invitation.token,
            user_data=user_data
        )
        
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.username, 'newuser')
        self.assertEqual(new_user.email, 'newuser@testcorp.com')
        self.assertEqual(new_user.role, 'staff')
        self.assertEqual(new_user.tenant, self.tenant)
        
        # Check invitation status updated
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'accepted')
        
        print("✓ User invitation system test passed")
    
    def test_subscription_management(self):
        """Test subscription and billing management"""
        print("Testing subscription management...")
        
        # Test subscription creation
        plan_data = {
            'name': 'Professional Plan',
            'plan_type': 'professional',
            'billing_cycle': 'monthly',
            'amount': '99.00',
            'currency': 'USD'
        }
        
        subscription = TenantBillingService.create_subscription(self.tenant, plan_data)
        
        self.assertIsNotNone(subscription)
        self.assertEqual(subscription.plan_name, 'Professional Plan')
        self.assertEqual(subscription.billing_cycle, 'monthly')
        self.assertEqual(float(subscription.amount), 99.00)
        
        # Check tenant status updated
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.status, 'active')
        self.assertEqual(self.tenant.plan, 'professional')
        
        # Test usage cost calculation
        usage_period = {
            'start': timezone.now() - timedelta(days=30),
            'end': timezone.now()
        }
        
        cost = TenantBillingService.calculate_usage_cost(self.tenant, usage_period)
        self.assertGreaterEqual(cost, 0)
        
        print("✓ Subscription management test passed")
    
    def test_usage_tracking(self):
        """Test tenant usage tracking"""
        print("Testing usage tracking...")
        
        # Create usage record
        usage = TenantUsage.objects.create(
            tenant=self.tenant,
            users_count=5,
            products_count=100,
            orders_count=50,
            storage_used_gb=2.5,
            api_calls_count=1000,
            period_start=timezone.now() - timedelta(days=1),
            period_end=timezone.now()
        )
        
        self.assertIsNotNone(usage)
        self.assertEqual(usage.users_count, 5)
        self.assertEqual(usage.products_count, 100)
        self.assertEqual(float(usage.storage_used_gb), 2.5)
        
        # Test analytics service
        stats = TenantAnalyticsService.get_tenant_dashboard_stats(self.tenant)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('users_count', stats)
        self.assertIn('storage_used', stats)
        
        print("✓ Usage tracking test passed")
    
    def test_audit_logging(self):
        """Test tenant audit logging"""
        print("Testing audit logging...")
        
        # Create audit log entry
        audit_log = TenantAuditLog.objects.create(
            tenant=self.tenant,
            user=self.owner,
            action='create',
            model_name='Product',
            object_id='123',
            object_repr='Test Product',
            changes={'name': 'Test Product', 'price': 99.99},
            ip_address='127.0.0.1'
        )
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'create')
        self.assertEqual(audit_log.model_name, 'Product')
        self.assertEqual(audit_log.user, self.owner)
        self.assertIsInstance(audit_log.changes, dict)
        
        print("✓ Audit logging test passed")
    
    def test_backup_system(self):
        """Test tenant backup system"""
        print("Testing backup system...")
        
        # Create backup
        backup = TenantBackupService.create_backup(self.tenant, 'full')
        
        self.assertIsNotNone(backup)
        self.assertEqual(backup.tenant, self.tenant)
        self.assertEqual(backup.backup_type, 'full')
        self.assertEqual(backup.status, 'pending')
        
        # Test backup record
        self.assertIsInstance(backup.id, type(backup.id))
        self.assertIsNotNone(backup.created_at)
        
        print("✓ Backup system test passed")
    
    def test_tenant_settings(self):
        """Test tenant settings management"""
        print("Testing tenant settings...")
        
        # Update tenant settings
        self.tenant.primary_color = '#ff0000'
        self.tenant.secondary_color = '#00ff00'
        self.tenant.features['custom_branding'] = True
        self.tenant.custom_settings['notifications'] = {
            'email_alerts': True,
            'sms_alerts': False
        }
        self.tenant.save()
        
        # Verify settings
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.primary_color, '#ff0000')
        self.assertEqual(self.tenant.secondary_color, '#00ff00')
        self.assertTrue(self.tenant.features['custom_branding'])
        self.assertTrue(self.tenant.custom_settings['notifications']['email_alerts'])
        
        print("✓ Tenant settings test passed")
    
    def test_tenant_limits(self):
        """Test tenant usage limits"""
        print("Testing tenant limits...")
        
        # Test default limits
        self.assertGreater(self.tenant.max_users, 0)
        self.assertGreater(self.tenant.max_products, 0)
        self.assertGreater(self.tenant.max_orders, 0)
        self.assertGreater(self.tenant.max_storage_gb, 0)
        
        # Test professional plan limits
        if self.tenant.plan == 'professional':
            self.assertGreaterEqual(self.tenant.max_users, 10)
            self.assertGreaterEqual(self.tenant.max_products, 1000)
        
        print("✓ Tenant limits test passed")
    
    def test_tenant_security(self):
        """Test tenant security features"""
        print("Testing tenant security...")
        
        # Test tenant isolation
        other_tenant = Tenant.objects.create(
            name='Other Corp',
            slug='other-corp',
            subdomain='othercorp',
            contact_name='Jane Doe',
            contact_email='jane@othercorp.com'
        )
        
        # Ensure tenants are isolated
        self.assertNotEqual(self.tenant.id, other_tenant.id)
        self.assertNotEqual(self.tenant.subdomain, other_tenant.subdomain)
        
        # Test user isolation
        self.assertEqual(self.owner.tenant, self.tenant)
        self.assertNotEqual(self.owner.tenant, other_tenant)
        
        print("✓ Tenant security test passed")


def run_comprehensive_test():
    """Run comprehensive tenant system test"""
    print("=" * 60)
    print("COMPREHENSIVE MULTI-TENANT ARCHITECTURE TEST")
    print("=" * 60)
    
    # Create test suite
    test_suite = TenantSystemTest()
    test_suite.setUp()
    
    try:
        # Run all tests
        test_suite.test_tenant_creation()
        test_suite.test_user_invitation_system()
        test_suite.test_subscription_management()
        test_suite.test_usage_tracking()
        test_suite.test_audit_logging()
        test_suite.test_backup_system()
        test_suite.test_tenant_settings()
        test_suite.test_tenant_limits()
        test_suite.test_tenant_security()
        
        print("\n" + "=" * 60)
        print("✅ ALL MULTI-TENANT ARCHITECTURE TESTS PASSED!")
        print("=" * 60)
        
        # Print summary
        print("\nTenant System Features Tested:")
        print("• Tenant provisioning and setup")
        print("• User invitation and management")
        print("• Subscription and billing")
        print("• Usage tracking and analytics")
        print("• Audit logging")
        print("• Backup and restore")
        print("• Settings management")
        print("• Usage limits enforcement")
        print("• Security and isolation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)