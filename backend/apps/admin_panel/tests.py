"""
Tests for admin panel models and functionality.
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import (
    AdminUser, AdminRole, AdminPermission, SystemSettings,
    ActivityLog, AdminSession, AdminNotification, AdminLoginAttempt,
    AdminReport
)


class AdminUserModelTest(TestCase):
    """Test AdminUser model functionality."""
    
    def setUp(self):
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123',
            role='admin',
            department='it'
        )
    
    def test_admin_user_creation(self):
        """Test admin user creation."""
        self.assertEqual(self.admin_user.username, 'testadmin')
        self.assertEqual(self.admin_user.email, 'test@example.com')
        self.assertEqual(self.admin_user.role, 'admin')
        self.assertEqual(self.admin_user.department, 'it')
        self.assertTrue(self.admin_user.is_admin_active)
        self.assertFalse(self.admin_user.is_account_locked)
    
    def test_account_locking(self):
        """Test account locking functionality."""
        self.admin_user.lock_account(duration_minutes=30)
        self.assertTrue(self.admin_user.is_account_locked)
        
        self.admin_user.unlock_account()
        self.assertFalse(self.admin_user.is_account_locked)
        self.assertEqual(self.admin_user.failed_login_attempts, 0)


class AdminPermissionModelTest(TestCase):
    """Test AdminPermission model functionality."""
    
    def test_permission_creation(self):
        """Test permission creation."""
        permission = AdminPermission.objects.create(
            codename='products.view.all',
            name='View All Products',
            module='products',
            action='view',
            resource='all',
            is_sensitive=False
        )
        
        self.assertEqual(permission.codename, 'products.view.all')
        self.assertEqual(permission.module, 'products')
        self.assertEqual(permission.action, 'view')
        self.assertFalse(permission.is_sensitive)
        self.assertTrue(permission.is_active)


class AdminRoleModelTest(TestCase):
    """Test AdminRole model functionality."""
    
    def setUp(self):
        self.permission1 = AdminPermission.objects.create(
            codename='products.view.all',
            name='View Products',
            module='products',
            action='view'
        )
        self.permission2 = AdminPermission.objects.create(
            codename='orders.view.all',
            name='View Orders',
            module='orders',
            action='view'
        )
    
    def test_role_creation(self):
        """Test role creation."""
        role = AdminRole.objects.create(
            name='manager',
            display_name='Manager',
            description='Management role',
            level=1
        )
        role.permissions.add(self.permission1, self.permission2)
        
        self.assertEqual(role.name, 'manager')
        self.assertEqual(role.level, 1)
        self.assertEqual(role.permissions.count(), 2)
    
    def test_role_hierarchy(self):
        """Test role hierarchy."""
        parent_role = AdminRole.objects.create(
            name='admin',
            display_name='Admin',
            level=0
        )
        parent_role.permissions.add(self.permission1, self.permission2)
        
        child_role = AdminRole.objects.create(
            name='manager',
            display_name='Manager',
            level=1,
            parent_role=parent_role
        )
        child_role.permissions.add(self.permission1)
        
        # Test that child role inherits parent permissions
        all_permissions = child_role.get_all_permissions()
        self.assertEqual(len(all_permissions), 2)


class SystemSettingsModelTest(TestCase):
    """Test SystemSettings model functionality."""
    
    def test_setting_creation(self):
        """Test system setting creation."""
        setting = SystemSettings.objects.create(
            key='site_name',
            name='Site Name',
            value='Test Site',
            setting_type='string',
            category='general'
        )
        
        self.assertEqual(setting.key, 'site_name')
        self.assertEqual(setting.get_typed_value(), 'Test Site')
    
    def test_typed_values(self):
        """Test typed value conversion."""
        # Boolean setting
        bool_setting = SystemSettings.objects.create(
            key='test_bool',
            name='Test Boolean',
            value='true',
            setting_type='boolean',
            category='test'
        )
        self.assertTrue(bool_setting.get_typed_value())
        
        # Integer setting
        int_setting = SystemSettings.objects.create(
            key='test_int',
            name='Test Integer',
            value='42',
            setting_type='integer',
            category='test'
        )
        self.assertEqual(int_setting.get_typed_value(), 42)


class ActivityLogModelTest(TestCase):
    """Test ActivityLog model functionality."""
    
    def setUp(self):
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_activity_log_creation(self):
        """Test activity log creation."""
        log = ActivityLog.objects.create(
            admin_user=self.admin_user,
            action='create',
            description='Created test object',
            ip_address='127.0.0.1',
            module='test',
            severity='low'
        )
        
        self.assertEqual(log.admin_user, self.admin_user)
        self.assertEqual(log.action, 'create')
        self.assertEqual(log.severity, 'low')
        self.assertTrue(log.is_successful)


class AdminSessionModelTest(TestCase):
    """Test AdminSession model functionality."""
    
    def setUp(self):
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_session_creation(self):
        """Test admin session creation."""
        session = AdminSession.objects.create(
            session_key='test_session_key',
            admin_user=self.admin_user,
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            expires_at=timezone.now() + timezone.timedelta(hours=1)
        )
        
        self.assertEqual(session.admin_user, self.admin_user)
        self.assertEqual(session.ip_address, '127.0.0.1')
        self.assertTrue(session.is_active)
        self.assertFalse(session.is_expired)
    
    def test_session_extension(self):
        """Test session extension."""
        session = AdminSession.objects.create(
            session_key='test_session_key',
            admin_user=self.admin_user,
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            expires_at=timezone.now() + timezone.timedelta(minutes=30)
        )
        
        original_expiry = session.expires_at
        session.extend_session(minutes=60)
        
        self.assertGreater(session.expires_at, original_expiry)


class AdminNotificationModelTest(TestCase):
    """Test AdminNotification model functionality."""
    
    def setUp(self):
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_notification_creation(self):
        """Test notification creation."""
        notification = AdminNotification.objects.create(
            recipient=self.admin_user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='info',
            priority='normal'
        )
        
        self.assertEqual(notification.recipient, self.admin_user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)
    
    def test_mark_as_read(self):
        """Test marking notification as read."""
        notification = AdminNotification.objects.create(
            recipient=self.admin_user,
            title='Test Notification',
            message='This is a test notification'
        )
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

class AdminPermissionManagerTest(TestCase):
    """Test AdminPermissionManager functionality."""
    
    def setUp(self):
        """Set up test data."""
        from django.core.cache import cache
        from .permissions import AdminPermissionManager
        
        cache.clear()  # Clear cache before each test
        
        # Create test admin user
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123',
            role='manager',
            department='sales'
        )
        
        # Create test permissions
        self.permission1 = AdminPermission.objects.create(
            codename='products.view.all',
            name='View All Products',
            module='products',
            action='view',
            resource='all'
        )
        
        self.permission2 = AdminPermission.objects.create(
            codename='orders.edit.own',
            name='Edit Own Orders',
            module='orders',
            action='edit',
            resource='own'
        )
        
        self.permission3 = AdminPermission.objects.create(
            codename='users.delete.all',
            name='Delete All Users',
            module='users',
            action='delete',
            resource='all',
            is_sensitive=True
        )
        
        # Create test role
        self.role = AdminRole.objects.create(
            name='manager',
            display_name='Manager',
            description='Manager role',
            level=1
        )
        self.role.permissions.add(self.permission1, self.permission2)
        
        # Assign direct permission to user
        self.admin_user.permissions.add(self.permission3)
    
    def test_get_user_permissions(self):
        """Test getting user permissions with role and direct permissions."""
        from .permissions import AdminPermissionManager
        
        permissions = AdminPermissionManager.get_user_permissions(self.admin_user)
        
        # Should include both role permissions and direct permissions
        expected_permissions = {
            'products.view.all',
            'orders.edit.own', 
            'users.delete.all'
        }
        self.assertEqual(permissions, expected_permissions)
    
    def test_has_permission_basic(self):
        """Test basic permission checking."""
        from .permissions import AdminPermissionManager
        
        # Should have permission from role
        self.assertTrue(
            AdminPermissionManager.has_permission(self.admin_user, 'products.view.all')
        )
        
        # Should have direct permission
        self.assertTrue(
            AdminPermissionManager.has_permission(self.admin_user, 'users.delete.all')
        )
        
        # Should not have permission not assigned
        self.assertFalse(
            AdminPermissionManager.has_permission(self.admin_user, 'analytics.view.all')
        )
    
    def test_has_permission_inactive_user(self):
        """Test permission checking for inactive user."""
        from .permissions import AdminPermissionManager
        
        self.admin_user.is_admin_active = False
        self.admin_user.save()
        
        # Should not have any permissions when inactive
        self.assertFalse(
            AdminPermissionManager.has_permission(self.admin_user, 'products.view.all')
        )
    
    def test_has_permission_super_admin(self):
        """Test that super admin has all permissions."""
        from .permissions import AdminPermissionManager
        
        self.admin_user.role = 'super_admin'
        self.admin_user.save()
        
        # Should have any permission as super admin
        self.assertTrue(
            AdminPermissionManager.has_permission(self.admin_user, 'any.permission.here')
        )
    
    def test_resource_level_permissions(self):
        """Test resource-level permission checking."""
        from .permissions import AdminPermissionManager
        
        context = {
            'resource_type': 'order',
            'owner_id': str(self.admin_user.id)
        }
        
        # Should have permission for own resource
        self.assertTrue(
            AdminPermissionManager.has_permission(
                self.admin_user, 
                'orders.edit.own',
                resource_id='123',
                context=context
            )
        )
        
        # Should not have permission for other's resource
        context['owner_id'] = 'other_user_id'
        self.assertFalse(
            AdminPermissionManager.has_permission(
                self.admin_user,
                'orders.edit.own', 
                resource_id='123',
                context=context
            )
        )
    
    def test_permission_caching(self):
        """Test permission caching functionality."""
        from django.core.cache import cache
        from .permissions import AdminPermissionManager
        
        # First call should cache permissions
        permissions1 = AdminPermissionManager.get_user_permissions(self.admin_user, use_cache=True)
        
        # Check cache was set
        cache_key = AdminPermissionManager.get_cache_key(str(self.admin_user.id))
        cached_permissions = cache.get(cache_key)
        self.assertIsNotNone(cached_permissions)
        
        # Second call should use cache
        permissions2 = AdminPermissionManager.get_user_permissions(self.admin_user, use_cache=True)
        self.assertEqual(permissions1, permissions2)
        
        # Clear cache and verify it's cleared
        AdminPermissionManager.clear_user_cache(str(self.admin_user.id))
        cached_permissions = cache.get(cache_key)
        self.assertIsNone(cached_permissions)


class AdminPermissionRequiredTest(TestCase):
    """Test AdminPermissionRequired DRF permission class."""
    
    def setUp(self):
        """Set up test data."""
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        User = get_user_model()
        
        # Create Django user
        self.django_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create admin user
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='admin@example.com',
            password='testpass123',
            role='admin'
        )
        
        # Link Django user to admin user
        self.django_user.adminuser = self.admin_user
        
        # Create permission
        self.permission = AdminPermission.objects.create(
            codename='products.view.all',
            name='View Products',
            module='products',
            action='view'
        )
        
        # Create role and assign permission
        self.role = AdminRole.objects.create(
            name='admin',
            display_name='Admin'
        )
        self.role.permissions.add(self.permission)
        
        self.factory = APIRequestFactory()
    
    def test_permission_granted(self):
        """Test permission is granted when user has required permission."""
        from .permissions import AdminPermissionRequired
        
        permission_class = AdminPermissionRequired('products.view.all')
        
        request = self.factory.get('/')
        request.user = self.django_user
        
        view = type('TestView', (), {})()
        
        self.assertTrue(permission_class.has_permission(request, view))
    
    def test_permission_denied_no_admin_user(self):
        """Test permission is denied when user has no admin user."""
        from .permissions import AdminPermissionRequired
        
        permission_class = AdminPermissionRequired('products.view.all')
        
        request = self.factory.get('/')
        request.user = self.django_user
        # Remove admin user link
        delattr(request.user, 'adminuser')
        
        view = type('TestView', (), {})()
        
        self.assertFalse(permission_class.has_permission(request, view))
    
    def test_permission_denied_insufficient_permissions(self):
        """Test permission is denied when user lacks required permission."""
        from .permissions import AdminPermissionRequired
        
        permission_class = AdminPermissionRequired('analytics.view.all')
        
        request = self.factory.get('/')
        request.user = self.django_user
        
        view = type('TestView', (), {})()
        
        self.assertFalse(permission_class.has_permission(request, view))


class PermissionDecoratorTest(TestCase):
    """Test admin_permission_required decorator."""
    
    def setUp(self):
        """Set up test data."""
        from django.contrib.auth import get_user_model
        from django.test import RequestFactory
        
        User = get_user_model()
        
        # Create Django user
        self.django_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create admin user
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='admin@example.com',
            password='testpass123',
            role='admin'
        )
        
        # Link Django user to admin user
        self.django_user.adminuser = self.admin_user
        
        # Create permission
        self.permission = AdminPermission.objects.create(
            codename='products.view.all',
            name='View Products',
            module='products',
            action='view'
        )
        
        # Create role and assign permission
        self.role = AdminRole.objects.create(
            name='admin',
            display_name='Admin'
        )
        self.role.permissions.add(self.permission)
        
        self.factory = RequestFactory()
    
    def test_decorator_allows_access(self):
        """Test decorator allows access when user has permission."""
        from .permissions import admin_permission_required
        from django.http import JsonResponse
        
        @admin_permission_required('products.view.all')
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = self.factory.get('/')
        request.user = self.django_user
        request.META = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_USER_AGENT': 'Test'}
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_decorator_denies_access(self):
        """Test decorator denies access when user lacks permission."""
        from .permissions import admin_permission_required
        
        @admin_permission_required('analytics.view.all')
        def test_view(request):
            return JsonResponse({'success': True})
        
        request = self.factory.get('/')
        request.user = self.django_user
        request.META = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_USER_AGENT': 'Test'}
        
        response = test_view(request)
        self.assertEqual(response.status_code, 403)
        
        # Check that activity log was created
        log_exists = ActivityLog.objects.filter(
            admin_user=self.admin_user,
            action='permission_denied'
        ).exists()
        self.assertTrue(log_exists)


class DynamicPermissionCheckerTest(TestCase):
    """Test DynamicPermissionChecker functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_time_based_permission(self):
        """Test time-based permission checking."""
        from .permissions import DynamicPermissionChecker
        from django.utils import timezone
        
        current_time = timezone.now().time()
        
        # Create time window around current time
        start_time = (timezone.now() - timezone.timedelta(hours=1)).strftime('%H:%M')
        end_time = (timezone.now() + timezone.timedelta(hours=1)).strftime('%H:%M')
        
        # Should allow access within time window
        self.assertTrue(
            DynamicPermissionChecker.check_time_based_permission(
                self.admin_user, 'test.permission', start_time, end_time
            )
        )
        
        # Should deny access outside time window
        past_start = (timezone.now() - timezone.timedelta(hours=3)).strftime('%H:%M')
        past_end = (timezone.now() - timezone.timedelta(hours=2)).strftime('%H:%M')
        
        self.assertFalse(
            DynamicPermissionChecker.check_time_based_permission(
                self.admin_user, 'test.permission', past_start, past_end
            )
        )
    
    def test_ip_based_permission(self):
        """Test IP-based permission checking."""
        from .permissions import DynamicPermissionChecker
        
        allowed_ips = ['127.0.0.1', '192.168.1.0/24']
        
        # Should allow from allowed IP
        self.assertTrue(
            DynamicPermissionChecker.check_ip_based_permission(
                self.admin_user, 'test.permission', allowed_ips, '127.0.0.1'
            )
        )
        
        # Should allow from IP in allowed subnet
        self.assertTrue(
            DynamicPermissionChecker.check_ip_based_permission(
                self.admin_user, 'test.permission', allowed_ips, '192.168.1.100'
            )
        )
        
        # Should deny from disallowed IP
        self.assertFalse(
            DynamicPermissionChecker.check_ip_based_permission(
                self.admin_user, 'test.permission', allowed_ips, '10.0.0.1'
            )
        )
    
    def test_device_based_permission(self):
        """Test device-based permission checking."""
        from .permissions import DynamicPermissionChecker
        
        # Desktop user agent
        desktop_headers = {
            'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Should allow critical operations on desktop
        self.assertTrue(
            DynamicPermissionChecker.check_device_based_permission(
                self.admin_user, 'admin_normal_operation', desktop_headers
            )
        )
        
        # Mobile user agent
        mobile_headers = {
            'HTTP_USER_AGENT': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) Mobile'
        }
        
        # Should deny critical operations on mobile
        self.assertFalse(
            DynamicPermissionChecker.check_device_based_permission(
                self.admin_user, 'admin_critical_delete', mobile_headers
            )
        )
        
        # Should allow normal operations on mobile
        self.assertTrue(
            DynamicPermissionChecker.check_device_based_permission(
                self.admin_user, 'admin_normal_view', mobile_headers
            )
        )


class PermissionInheritanceManagerTest(TestCase):
    """Test PermissionInheritanceManager functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create permissions
        self.perm1 = AdminPermission.objects.create(
            codename='basic.view',
            name='Basic View'
        )
        self.perm2 = AdminPermission.objects.create(
            codename='advanced.edit',
            name='Advanced Edit'
        )
        self.perm3 = AdminPermission.objects.create(
            codename='super.delete',
            name='Super Delete'
        )
        
        # Create roles with hierarchy
        self.super_admin_role = AdminRole.objects.create(
            name='super_admin',
            display_name='Super Admin',
            level=0
        )
        self.super_admin_role.permissions.add(self.perm3)
        
        self.admin_role = AdminRole.objects.create(
            name='admin',
            display_name='Admin',
            level=1
        )
        self.admin_role.permissions.add(self.perm2)
        
        self.manager_role = AdminRole.objects.create(
            name='manager',
            display_name='Manager',
            level=2
        )
        self.manager_role.permissions.add(self.perm1)
    
    def test_get_inherited_permissions(self):
        """Test getting inherited permissions from parent roles."""
        from .permissions import PermissionInheritanceManager
        
        # Manager should inherit from admin and super_admin
        inherited = PermissionInheritanceManager.get_inherited_permissions('manager')
        
        expected_permissions = {'advanced.edit', 'super.delete'}
        self.assertEqual(inherited, expected_permissions)
    
    def test_validate_role_hierarchy(self):
        """Test role hierarchy validation."""
        from .permissions import PermissionInheritanceManager
        
        # Super admin can manage any role
        self.assertTrue(
            PermissionInheritanceManager.validate_role_hierarchy('super_admin', 'manager')
        )
        
        # Admin can manage manager (manager is in admin's hierarchy)
        self.assertTrue(
            PermissionInheritanceManager.validate_role_hierarchy('admin', 'manager')
        )
        
        # Manager cannot manage admin (admin is not in manager's hierarchy)
        self.assertFalse(
            PermissionInheritanceManager.validate_role_hierarchy('manager', 'admin')
        )
        
        # User can manage same role
        self.assertTrue(
            PermissionInheritanceManager.validate_role_hierarchy('manager', 'manager')
        )


class PermissionValidatorTest(TestCase):
    """Test PermissionValidator functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123',
            role='manager'
        )
        
        self.permission = AdminPermission.objects.create(
            codename='test.permission',
            name='Test Permission',
            minimum_role_level=1,
            allow_direct_assignment=True
        )
        
        self.restricted_permission = AdminPermission.objects.create(
            codename='restricted.permission',
            name='Restricted Permission',
            minimum_role_level=0,  # Only for super admin
            allow_direct_assignment=False
        )
        
        self.role = AdminRole.objects.create(
            name='manager',
            display_name='Manager',
            level=2
        )
    
    def test_validate_permission_assignment_success(self):
        """Test successful permission assignment validation."""
        from .permissions import PermissionValidator
        
        # Should succeed for allowed permission
        result = PermissionValidator.validate_permission_assignment(
            self.admin_user, self.permission
        )
        self.assertTrue(result)
    
    def test_validate_permission_assignment_failure(self):
        """Test failed permission assignment validation."""
        from .permissions import PermissionValidator, PermissionValidationError
        
        # Should fail for restricted permission
        with self.assertRaises(PermissionValidationError):
            PermissionValidator.validate_permission_assignment(
                self.admin_user, self.restricted_permission
            )
    
    def test_validate_role_permissions_success(self):
        """Test successful role permission validation."""
        from .permissions import PermissionValidator
        
        # Should succeed when role level meets permission requirements
        result = PermissionValidator.validate_role_permissions(
            self.role, [self.permission]
        )
        self.assertTrue(result)
    
    def test_validate_role_permissions_failure(self):
        """Test failed role permission validation."""
        from .permissions import PermissionValidator, PermissionValidationError
        
        # Should fail when role level doesn't meet permission requirements
        with self.assertRaises(PermissionValidationError):
            PermissionValidator.validate_role_permissions(
                self.role, [self.restricted_permission]
            )


class AdminPermissionsConstantsTest(TestCase):
    """Test AdminPermissions constants."""
    
    def test_get_all_permissions(self):
        """Test getting all permission constants."""
        from .permissions import AdminPermissions
        
        all_permissions = AdminPermissions.get_all_permissions()
        
        # Should include expected permissions
        expected_permissions = [
            'admin_user_view',
            'admin_product_view',
            'admin_order_view',
            'admin_analytics_view',
            'admin_settings_view'
        ]
        
        for perm in expected_permissions:
            self.assertIn(perm, all_permissions)
        
        # Should not include private attributes
        self.assertNotIn('get_all_permissions', all_permissions)