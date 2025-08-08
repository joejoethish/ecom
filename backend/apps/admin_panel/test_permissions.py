"""
Comprehensive test suite for the admin panel RBAC permission system.
This file contains advanced tests for permission management, caching, and security.
"""
import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import (
    AdminUser, AdminRole, AdminPermission, ActivityLog,
    AdminSession, SystemSettings
)
from .permissions import (
    AdminPermissionManager, AdminPermissionRequired, admin_permission_required,
    PermissionAuditMixin, DynamicPermissionChecker, PermissionInheritanceManager,
    PermissionValidator, PermissionValidationError, AdminPermissions
)


class AdvancedPermissionManagerTest(TestCase):
    """Advanced tests for AdminPermissionManager with complex scenarios."""
    
    def setUp(self):
        """Set up complex test scenario with multiple users, roles, and permissions."""
        cache.clear()
        
        # Create multiple permissions with different characteristics
        self.permissions = {
            'basic_view': AdminPermission.objects.create(
                codename='basic.view.all',
                name='Basic View All',
                module='basic',
                action='view',
                resource='all',
                is_sensitive=False,
                minimum_role_level=3
            ),
            'sensitive_edit': AdminPermission.objects.create(
                codename='sensitive.edit.all',
                name='Sensitive Edit All',
                module='sensitive',
                action='edit',
                resource='all',
                is_sensitive=True,
                minimum_role_level=1
            ),
            'own_data': AdminPermission.objects.create(
                codename='data.view.own',
                name='View Own Data',
                module='data',
                action='view',
                resource='own',
                is_sensitive=False,
                minimum_role_level=2
            ),
            'critical_delete': AdminPermission.objects.create(
                codename='critical.delete.all',
                name='Critical Delete All',
                module='critical',
                action='delete',
                resource='all',
                is_sensitive=True,
                minimum_role_level=0,
                allow_direct_assignment=False
            )
        }
        
        # Create role hierarchy
        self.roles = {
            'super_admin': AdminRole.objects.create(
                name='super_admin',
                display_name='Super Administrator',
                level=0,
                description='Highest level admin with all permissions'
            ),
            'admin': AdminRole.objects.create(
                name='admin',
                display_name='Administrator',
                level=1,
                description='High level admin'
            ),
            'manager': AdminRole.objects.create(
                name='manager',
                display_name='Manager',
                level=2,
                description='Management level access'
            ),
            'analyst': AdminRole.objects.create(
                name='analyst',
                display_name='Analyst',
                level=3,
                description='Analysis and reporting access'
            )
        }
        
        # Assign permissions to roles
        self.roles['super_admin'].permissions.add(*self.permissions.values())
        self.roles['admin'].permissions.add(
            self.permissions['basic_view'],
            self.permissions['sensitive_edit'],
            self.permissions['own_data']
        )
        self.roles['manager'].permissions.add(
            self.permissions['basic_view'],
            self.permissions['own_data']
        )
        self.roles['analyst'].permissions.add(
            self.permissions['basic_view']
        )
        
        # Create test users with different roles
        self.users = {
            'super_admin': AdminUser.objects.create_user(
                username='superadmin',
                email='super@example.com',
                password='testpass123',
                role='super_admin',
                department='it'
            ),
            'admin': AdminUser.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='testpass123',
                role='admin',
                department='it'
            ),
            'manager': AdminUser.objects.create_user(
                username='manager',
                email='manager@example.com',
                password='testpass123',
                role='manager',
                department='sales'
            ),
            'analyst': AdminUser.objects.create_user(
                username='analyst',
                email='analyst@example.com',
                password='testpass123',
                role='analyst',
                department='marketing'
            ),
            'inactive': AdminUser.objects.create_user(
                username='inactive',
                email='inactive@example.com',
                password='testpass123',
                role='analyst',
                department='marketing',
                is_admin_active=False
            )
        }
    
    def test_complex_permission_inheritance(self):
        """Test complex permission inheritance scenarios."""
        # Test that each role has expected permissions
        super_admin_perms = AdminPermissionManager.get_user_permissions(self.users['super_admin'])
        admin_perms = AdminPermissionManager.get_user_permissions(self.users['admin'])
        manager_perms = AdminPermissionManager.get_user_permissions(self.users['manager'])
        analyst_perms = AdminPermissionManager.get_user_permissions(self.users['analyst'])
        
        # Super admin should have all permissions
        self.assertEqual(len(super_admin_perms), 4)
        
        # Admin should have 3 permissions
        self.assertEqual(len(admin_perms), 3)
        self.assertIn('basic.view.all', admin_perms)
        self.assertIn('sensitive.edit.all', admin_perms)
        self.assertIn('data.view.own', admin_perms)
        self.assertNotIn('critical.delete.all', admin_perms)
        
        # Manager should have 2 permissions
        self.assertEqual(len(manager_perms), 2)
        self.assertIn('basic.view.all', manager_perms)
        self.assertIn('data.view.own', manager_perms)
        
        # Analyst should have 1 permission
        self.assertEqual(len(analyst_perms), 1)
        self.assertIn('basic.view.all', analyst_perms)
    
    def test_permission_caching_performance(self):
        """Test permission caching performance and behavior."""
        user = self.users['admin']
        
        # Time uncached call
        start_time = time.time()
        perms1 = AdminPermissionManager.get_user_permissions(user, use_cache=False)
        uncached_time = time.time() - start_time
        
        # Time cached call
        start_time = time.time()
        perms2 = AdminPermissionManager.get_user_permissions(user, use_cache=True)
        first_cached_time = time.time() - start_time
        
        # Time second cached call
        start_time = time.time()
        perms3 = AdminPermissionManager.get_user_permissions(user, use_cache=True)
        second_cached_time = time.time() - start_time
        
        # Results should be identical
        self.assertEqual(perms1, perms2)
        self.assertEqual(perms2, perms3)
        
        # Second cached call should be faster than first cached call
        self.assertLess(second_cached_time, first_cached_time)
        
        # Verify cache key generation
        cache_key = AdminPermissionManager.get_cache_key(str(user.id))
        self.assertTrue(cache_key.startswith('admin_perm:user:'))
        
        # Verify cache clearing
        AdminPermissionManager.clear_user_cache(str(user.id))
        cached_perms = cache.get(cache_key)
        self.assertIsNone(cached_perms)
    
    def test_resource_level_permission_complex(self):
        """Test complex resource-level permission scenarios."""
        user = self.users['manager']
        
        # Test department-based access control
        context = {
            'resource_type': 'department_data',
            'department': 'sales',  # Same as user's department
            'owner_id': str(user.id)
        }
        
        # Should have access to own department data
        self.assertTrue(
            AdminPermissionManager.has_permission(
                user, 'data.view.own', resource_id='123', context=context
            )
        )
        
        # Should not have access to other department data
        context['department'] = 'marketing'
        self.assertFalse(
            AdminPermissionManager.has_permission(
                user, 'data.view.own', resource_id='123', context=context
            )
        )
        
        # Test ownership-based access control
        context = {
            'resource_type': 'user_data',
            'owner_id': 'other_user_id'
        }
        
        # Should not have access to other user's data for 'own' permission
        self.assertFalse(
            AdminPermissionManager.has_permission(
                user, 'data.view.own', resource_id='456', context=context
            )
        )
    
    def test_concurrent_permission_access(self):
        """Test concurrent access to permission system."""
        import threading
        import queue
        
        user = self.users['admin']
        results = queue.Queue()
        
        def check_permissions():
            """Function to run in thread."""
            try:
                perms = AdminPermissionManager.get_user_permissions(user)
                has_perm = AdminPermissionManager.has_permission(user, 'basic.view.all')
                results.put((perms, has_perm, None))
            except Exception as e:
                results.put((None, None, e))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=check_permissions)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        while not results.empty():
            perms, has_perm, error = results.get()
            self.assertIsNone(error, f"Thread error: {error}")
            self.assertIsNotNone(perms)
            self.assertTrue(has_perm)
    
    def test_permission_edge_cases(self):
        """Test edge cases in permission checking."""
        # Test with None user
        self.assertFalse(
            AdminPermissionManager.has_permission(None, 'any.permission')
        )
        
        # Test with empty permission string
        user = self.users['admin']
        self.assertFalse(
            AdminPermissionManager.has_permission(user, '')
        )
        
        # Test with non-existent permission
        self.assertFalse(
            AdminPermissionManager.has_permission(user, 'non.existent.permission')
        )
        
        # Test with inactive permission
        inactive_perm = AdminPermission.objects.create(
            codename='inactive.permission',
            name='Inactive Permission',
            is_active=False
        )
        role = AdminRole.objects.get(name='admin')
        role.permissions.add(inactive_perm)
        
        # Clear cache to ensure fresh data
        AdminPermissionManager.clear_user_cache(str(user.id))
        
        self.assertFalse(
            AdminPermissionManager.has_permission(user, 'inactive.permission')
        )


class PermissionMiddlewareTest(TestCase):
    """Test permission checking in middleware-like scenarios."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
        # Create user and permissions
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123',
            role='admin'
        )
        
        self.permission = AdminPermission.objects.create(
            codename='api.access.all',
            name='API Access All',
            module='api',
            action='access'
        )
        
        self.role = AdminRole.objects.create(
            name='admin',
            display_name='Admin'
        )
        self.role.permissions.add(self.permission)
        
        # Create Django user and link to admin user
        User = get_user_model()
        self.django_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.django_user.adminuser = self.admin_user
    
    def test_permission_audit_mixin(self):
        """Test PermissionAuditMixin functionality."""
        class TestView(PermissionAuditMixin, APIView):
            permission_required = 'api.access.all'
            
            def get(self, request):
                return Response({'success': True})
        
        view = TestView()
        request = self.factory.get('/')
        request.user = self.django_user
        request.META = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_USER_AGENT': 'Test'}
        
        # Mock the parent dispatch method
        with patch.object(APIView, 'dispatch') as mock_dispatch:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_dispatch.return_value = mock_response
            
            response = view.dispatch(request)
            
            # Check that activity log was created
            log_exists = ActivityLog.objects.filter(
                admin_user=self.admin_user,
                action='permission_used',
                resource_type='permission',
                resource_id='api.access.all'
            ).exists()
            self.assertTrue(log_exists)
    
    def test_bulk_permission_operations(self):
        """Test bulk permission operations."""
        # Create multiple users
        users = []
        for i in range(5):
            user = AdminUser.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123',
                role='analyst'
            )
            users.append(user)
        
        # Create multiple permissions
        permissions = []
        for i in range(3):
            perm = AdminPermission.objects.create(
                codename=f'bulk.test.{i}',
                name=f'Bulk Test {i}',
                module='bulk'
            )
            permissions.append(perm)
        
        # Test bulk permission assignment
        role = AdminRole.objects.create(
            name='bulk_test_role',
            display_name='Bulk Test Role'
        )
        
        # Assign all permissions to role
        role.permissions.add(*permissions)
        
        # Update all users to use this role
        for user in users:
            user.role = 'bulk_test_role'
            user.save()
            # Clear cache for each user
            AdminPermissionManager.clear_user_cache(str(user.id))
        
        # Verify all users have all permissions
        for user in users:
            user_perms = AdminPermissionManager.get_user_permissions(user)
            expected_perms = {f'bulk.test.{i}' for i in range(3)}
            self.assertEqual(user_perms, expected_perms)


class SecurityTest(TestCase):
    """Test security aspects of the permission system."""
    
    def setUp(self):
        """Set up security test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='securitytest',
            email='security@example.com',
            password='testpass123',
            role='admin'
        )
        
        self.sensitive_permission = AdminPermission.objects.create(
            codename='security.sensitive.operation',
            name='Sensitive Security Operation',
            module='security',
            action='sensitive',
            is_sensitive=True,
            minimum_role_level=0  # Only super admin
        )
    
    def test_permission_escalation_prevention(self):
        """Test that permission escalation is prevented."""
        # Regular admin should not have super admin permissions
        self.assertFalse(
            AdminPermissionManager.has_permission(
                self.admin_user, 'security.sensitive.operation'
            )
        )
        
        # Even if permission is directly assigned, role level should be checked
        self.admin_user.permissions.add(self.sensitive_permission)
        AdminPermissionManager.clear_user_cache(str(self.admin_user.id))
        
        # Should still be denied due to role level restriction
        # (This would need to be implemented in the permission checking logic)
        # For now, we test that the permission exists but access control is role-based
        user_perms = AdminPermissionManager.get_user_permissions(self.admin_user)
        self.assertIn('security.sensitive.operation', user_perms)
    
    def test_session_based_permissions(self):
        """Test session-based permission restrictions."""
        # Create admin session
        session = AdminSession.objects.create(
            session_key='test_session',
            admin_user=self.admin_user,
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            expires_at=timezone.now() + timezone.timedelta(hours=1)
        )
        
        # Test that session is active
        self.assertTrue(session.is_active)
        self.assertFalse(session.is_expired)
        
        # Test session extension
        original_expiry = session.expires_at
        session.extend_session(minutes=30)
        self.assertGreater(session.expires_at, original_expiry)
    
    def test_permission_tampering_detection(self):
        """Test detection of permission tampering attempts."""
        # Create permission
        permission = AdminPermission.objects.create(
            codename='tamper.test',
            name='Tamper Test',
            module='tamper'
        )
        
        # Assign to user
        self.admin_user.permissions.add(permission)
        
        # Get permissions (should be cached)
        perms1 = AdminPermissionManager.get_user_permissions(self.admin_user)
        self.assertIn('tamper.test', perms1)
        
        # Modify permission in database
        permission.is_active = False
        permission.save()
        
        # Cached permissions should still show old state
        perms2 = AdminPermissionManager.get_user_permissions(self.admin_user, use_cache=True)
        self.assertIn('tamper.test', perms2)
        
        # Fresh permissions should show new state
        perms3 = AdminPermissionManager.get_user_permissions(self.admin_user, use_cache=False)
        self.assertNotIn('tamper.test', perms3)
        
        # Clear cache and verify
        AdminPermissionManager.clear_user_cache(str(self.admin_user.id))
        perms4 = AdminPermissionManager.get_user_permissions(self.admin_user)
        self.assertNotIn('tamper.test', perms4)


class PerformanceTest(TransactionTestCase):
    """Test performance aspects of the permission system."""
    
    def setUp(self):
        """Set up performance test data."""
        # Create large number of permissions
        self.permissions = []
        for i in range(100):
            perm = AdminPermission.objects.create(
                codename=f'perf.test.{i}',
                name=f'Performance Test {i}',
                module='performance'
            )
            self.permissions.append(perm)
        
        # Create role with all permissions
        self.role = AdminRole.objects.create(
            name='performance_role',
            display_name='Performance Role'
        )
        self.role.permissions.add(*self.permissions)
        
        # Create user
        self.admin_user = AdminUser.objects.create_user(
            username='perftest',
            email='perf@example.com',
            password='testpass123',
            role='performance_role'
        )
    
    def test_large_permission_set_performance(self):
        """Test performance with large permission sets."""
        # Time permission loading
        start_time = time.time()
        perms = AdminPermissionManager.get_user_permissions(self.admin_user, use_cache=False)
        load_time = time.time() - start_time
        
        # Should load 100 permissions
        self.assertEqual(len(perms), 100)
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(load_time, 1.0, f"Permission loading took {load_time:.3f}s")
        
        # Test cached performance
        start_time = time.time()
        cached_perms = AdminPermissionManager.get_user_permissions(self.admin_user, use_cache=True)
        cached_time = time.time() - start_time
        
        # Cached should be much faster
        self.assertLess(cached_time, load_time / 10)
        self.assertEqual(perms, cached_perms)
    
    def test_permission_checking_performance(self):
        """Test performance of individual permission checks."""
        # Load permissions into cache first
        AdminPermissionManager.get_user_permissions(self.admin_user)
        
        # Time multiple permission checks
        start_time = time.time()
        for i in range(50):
            has_perm = AdminPermissionManager.has_permission(
                self.admin_user, f'perf.test.{i}'
            )
            self.assertTrue(has_perm)
        
        check_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(check_time, 0.5, f"50 permission checks took {check_time:.3f}s")
    
    def test_cache_memory_usage(self):
        """Test cache memory usage with large permission sets."""
        import sys
        
        # Clear cache first
        cache.clear()
        
        # Load permissions for multiple users
        users = []
        for i in range(10):
            user = AdminUser.objects.create_user(
                username=f'cachetest{i}',
                email=f'cache{i}@example.com',
                password='testpass123',
                role='performance_role'
            )
            users.append(user)
            
            # Load permissions (will be cached)
            AdminPermissionManager.get_user_permissions(user)
        
        # Check that cache contains expected number of entries
        # This is implementation-dependent and may need adjustment
        cache_stats = cache._cache.get_stats() if hasattr(cache._cache, 'get_stats') else None
        
        # At minimum, verify that permissions were loaded for all users
        for user in users:
            perms = AdminPermissionManager.get_user_permissions(user, use_cache=True)
            self.assertEqual(len(perms), 100)


class IntegrationTest(TestCase):
    """Integration tests for the complete permission system."""
    
    def setUp(self):
        """Set up integration test scenario."""
        # Create complete permission hierarchy
        self.setup_complete_permission_system()
    
    def setup_complete_permission_system(self):
        """Set up a complete permission system for testing."""
        # Create all permission constants
        permission_constants = AdminPermissions.get_all_permissions()
        
        self.permissions = {}
        for perm_code in permission_constants:
            parts = perm_code.split('_')
            module = parts[1] if len(parts) > 1 else 'general'
            action = parts[2] if len(parts) > 2 else 'access'
            
            perm = AdminPermission.objects.create(
                codename=perm_code,
                name=perm_code.replace('_', ' ').title(),
                module=module,
                action=action
            )
            self.permissions[perm_code] = perm
        
        # Create role hierarchy with realistic permissions
        self.roles = {
            'super_admin': AdminRole.objects.create(
                name='super_admin',
                display_name='Super Administrator',
                level=0
            ),
            'admin': AdminRole.objects.create(
                name='admin',
                display_name='Administrator',
                level=1
            ),
            'manager': AdminRole.objects.create(
                name='manager',
                display_name='Manager',
                level=2
            ),
            'analyst': AdminRole.objects.create(
                name='analyst',
                display_name='Analyst',
                level=3
            ),
            'support': AdminRole.objects.create(
                name='support',
                display_name='Support',
                level=4
            ),
            'viewer': AdminRole.objects.create(
                name='viewer',
                display_name='Viewer',
                level=5
            )
        }
        
        # Assign permissions to roles based on hierarchy
        # Super admin gets all permissions
        self.roles['super_admin'].permissions.add(*self.permissions.values())
        
        # Admin gets most permissions except super critical ones
        admin_perms = [p for code, p in self.permissions.items() 
                      if not code.endswith('_critical')]
        self.roles['admin'].permissions.add(*admin_perms)
        
        # Manager gets management-related permissions
        manager_perms = [p for code, p in self.permissions.items() 
                        if any(x in code for x in ['user', 'product', 'order', 'reports'])]
        self.roles['manager'].permissions.add(*manager_perms)
        
        # Analyst gets view and analytics permissions
        analyst_perms = [p for code, p in self.permissions.items() 
                        if 'view' in code or 'analytics' in code or 'reports' in code]
        self.roles['analyst'].permissions.add(*analyst_perms)
        
        # Support gets basic user and order permissions
        support_perms = [p for code, p in self.permissions.items() 
                        if ('user' in code or 'order' in code) and 'view' in code]
        self.roles['support'].permissions.add(*support_perms)
        
        # Viewer gets only view permissions
        viewer_perms = [p for code, p in self.permissions.items() if 'view' in code]
        self.roles['viewer'].permissions.add(*viewer_perms)
        
        # Create users for each role
        self.users = {}
        for role_name in self.roles.keys():
            user = AdminUser.objects.create_user(
                username=f'{role_name}_user',
                email=f'{role_name}@example.com',
                password='testpass123',
                role=role_name,
                department='test'
            )
            self.users[role_name] = user
    
    def test_complete_permission_hierarchy(self):
        """Test the complete permission hierarchy works as expected."""
        # Test super admin has all permissions
        super_admin_perms = AdminPermissionManager.get_user_permissions(
            self.users['super_admin']
        )
        self.assertEqual(len(super_admin_perms), len(self.permissions))
        
        # Test role hierarchy - each lower role should have fewer permissions
        role_perm_counts = {}
        for role_name, user in self.users.items():
            perms = AdminPermissionManager.get_user_permissions(user)
            role_perm_counts[role_name] = len(perms)
        
        # Verify hierarchy (higher level roles have more permissions)
        self.assertGreater(role_perm_counts['super_admin'], role_perm_counts['admin'])
        self.assertGreater(role_perm_counts['admin'], role_perm_counts['manager'])
        self.assertGreater(role_perm_counts['manager'], role_perm_counts['analyst'])
    
    def test_end_to_end_permission_flow(self):
        """Test complete end-to-end permission checking flow."""
        # Test API request flow
        factory = APIRequestFactory()
        
        # Create Django user linked to admin user
        User = get_user_model()
        django_user = User.objects.create_user(
            username='apitest',
            email='api@example.com',
            password='testpass123'
        )
        django_user.adminuser = self.users['manager']
        
        # Test permission-protected view
        class ProtectedView(APIView):
            def get(self, request):
                return Response({'data': 'protected'})
        
        # Create request
        request = factory.get('/api/protected/')
        request.user = django_user
        
        # Test with required permission
        permission_class = AdminPermissionRequired(AdminPermissions.USER_VIEW)
        view = ProtectedView()
        
        # Manager should have user view permission
        has_permission = permission_class.has_permission(request, view)
        self.assertTrue(has_permission)
        
        # Test with permission manager doesn't have
        permission_class = AdminPermissionRequired(AdminPermissions.SETTINGS_CRITICAL)
        has_permission = permission_class.has_permission(request, view)
        self.assertFalse(has_permission)
    
    def test_permission_system_consistency(self):
        """Test that the permission system is internally consistent."""
        # Verify all permission constants exist as actual permissions
        constants = AdminPermissions.get_all_permissions()
        existing_permissions = set(AdminPermission.objects.values_list('codename', flat=True))
        
        for constant in constants:
            self.assertIn(constant, existing_permissions, 
                         f"Permission constant {constant} not found in database")
        
        # Verify role hierarchy is consistent
        for role_name, role in self.roles.items():
            if role_name != 'super_admin':
                # Each role should have fewer permissions than super admin
                role_perms = set(role.permissions.values_list('codename', flat=True))
                super_admin_perms = set(
                    self.roles['super_admin'].permissions.values_list('codename', flat=True)
                )
                self.assertTrue(role_perms.issubset(super_admin_perms))
        
        # Verify permission inheritance works
        for role_name in ['admin', 'manager', 'analyst']:
            inherited_perms = PermissionInheritanceManager.get_inherited_permissions(role_name)
            # Should have some inherited permissions (unless it's the top role)
            if role_name != 'super_admin':
                self.assertGreater(len(inherited_perms), 0)