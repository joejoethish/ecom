"""
Permission system for the admin panel RBAC.
"""
import json
import time
from typing import Dict, List, Optional, Set, Any
from functools import wraps
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from .models import AdminUser, AdminPermission, AdminRole, ActivityLog


class IsAdminUser(BasePermission):
    """
    Permission class to check if user is an admin user.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is an admin user."""
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


class AdminPermissionManager:
    """
    Centralized permission management system with caching and inheritance.
    """
    
    CACHE_PREFIX = 'admin_perm'
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_cache_key(cls, user_id: str, permission: str = None) -> str:
        """Generate cache key for permissions."""
        if permission:
            return f"{cls.CACHE_PREFIX}:user:{user_id}:perm:{permission}"
        return f"{cls.CACHE_PREFIX}:user:{user_id}:all"
    
    @classmethod
    def get_user_permissions(cls, user: AdminUser, use_cache: bool = True) -> Set[str]:
        """
        Get all permissions for a user including role-based and direct permissions.
        """
        cache_key = cls.get_cache_key(str(user.id))
        
        if use_cache:
            cached_permissions = cache.get(cache_key)
            if cached_permissions is not None:
                return set(cached_permissions)
        
        permissions = set()
        
        # Get direct permissions
        direct_permissions = user.permissions.filter(is_active=True).values_list('codename', flat=True)
        permissions.update(direct_permissions)
        
        # Get role-based permissions
        try:
            role = AdminRole.objects.get(name=user.role, is_active=True)
            role_permissions = role.get_all_permissions()
            permissions.update(perm.codename for perm in role_permissions if perm.is_active)
        except AdminRole.DoesNotExist:
            pass
        
        # Cache the permissions
        if use_cache:
            cache.set(cache_key, list(permissions), cls.CACHE_TIMEOUT)
        
        return permissions
    
    @classmethod
    def has_permission(cls, user: AdminUser, permission_codename: str, 
                      resource_id: str = None, context: Dict = None) -> bool:
        """
        Check if user has a specific permission with optional resource-level checking.
        """
        if not user.is_admin_active:
            return False
        
        # Super admin has all permissions
        if user.role == 'super_admin':
            return True
        
        # Check if user has the specific permission
        user_permissions = cls.get_user_permissions(user, use_cache=True)
        
        # Basic permission check
        if permission_codename not in user_permissions:
            return False
        
        # Resource-level permission checking
        if resource_id and context:
            return cls._check_resource_permission(user, permission_codename, resource_id, context)
        
        return True
    
    @classmethod
    def _check_resource_permission(cls, user: AdminUser, permission: str, 
                                 resource_id: str, context: Dict) -> bool:
        """
        Check resource-level permissions with context.
        """
        # Implement resource-level permission logic
        resource_type = context.get('resource_type')
        
        # Example: Check if user can only access their own data
        if permission.endswith('_own') and context.get('owner_id') != str(user.id):
            return False
        
        # Example: Department-based access control
        if resource_type == 'department_data' and user.department != context.get('department'):
            return False
        
        return True
    
    @classmethod
    def clear_user_cache(cls, user_id: str):
        """Clear cached permissions for a user."""
        cache_key = cls.get_cache_key(str(user_id))
        cache.delete(cache_key)
    
    @classmethod
    def clear_all_cache(cls):
        """Clear all permission caches."""
        cache.delete_pattern(f"{cls.CACHE_PREFIX}:*")


class AdminPermissionRequired(BasePermission):
    """
    DRF permission class for admin panel endpoints.
    """
    
    def __init__(self, permission_codename: str, resource_type: str = None):
        self.permission_codename = permission_codename
        self.resource_type = resource_type
    
    def has_permission(self, request, view):
        """Check if user has the required permission."""
        if not hasattr(request.user, 'adminuser'):
            return False
        
        admin_user = request.user.adminuser
        context = {
            'resource_type': self.resource_type,
            'request_method': request.method,
            'view_name': view.__class__.__name__
        }
        
        return AdminPermissionManager.has_permission(
            admin_user, 
            self.permission_codename,
            context=context
        )


def admin_permission_required(permission_codename: str, resource_type: str = None):
    """
    Decorator for view functions requiring admin permissions.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'adminuser'):
                return JsonResponse({'error': 'Admin access required'}, status=403)
            
            admin_user = request.user.adminuser
            context = {
                'resource_type': resource_type,
                'request_method': request.method,
                'view_args': args,
                'view_kwargs': kwargs
            }
            
            if not AdminPermissionManager.has_permission(admin_user, permission_codename, context=context):
                # Log the permission denial
                ActivityLog.objects.create(
                    admin_user=admin_user,
                    action='permission_denied',
                    description=f'Permission denied for {permission_codename}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    module='permission',
                    severity='medium'
                )
                return JsonResponse({'error': 'Insufficient permissions'}, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Permission constants for easy reference
class AdminPermissions:
    """Constants for admin permissions."""
    
    # User management
    USER_VIEW = 'admin_user_view'
    USER_CREATE = 'admin_user_create'
    USER_EDIT = 'admin_user_edit'
    USER_DELETE = 'admin_user_delete'
    USER_IMPERSONATE = 'admin_user_impersonate'
    
    # Product management
    PRODUCT_VIEW = 'admin_product_view'
    PRODUCT_CREATE = 'admin_product_create'
    PRODUCT_EDIT = 'admin_product_edit'
    PRODUCT_DELETE = 'admin_product_delete'
    PRODUCT_BULK_EDIT = 'admin_product_bulk_edit'
    
    # Order management
    ORDER_VIEW = 'admin_order_view'
    ORDER_EDIT = 'admin_order_edit'
    ORDER_CANCEL = 'admin_order_cancel'
    ORDER_REFUND = 'admin_order_refund'
    
    # Analytics and reporting
    ANALYTICS_VIEW = 'admin_analytics_view'
    REPORTS_VIEW = 'admin_reports_view'
    REPORTS_EXPORT = 'admin_reports_export'
    
    # System settings
    SETTINGS_VIEW = 'admin_settings_view'
    SETTINGS_EDIT = 'admin_settings_edit'
    SETTINGS_CRITICAL = 'admin_settings_critical'
    
    # Audit and logs
    AUDIT_VIEW = 'admin_audit_view'
    LOGS_VIEW = 'admin_logs_view'
    
    @classmethod
    def get_all_permissions(cls) -> List[str]:
        """Get all defined permission constants."""
        return [getattr(cls, attr) for attr in dir(cls) 
                if not attr.startswith('_') and isinstance(getattr(cls, attr), str)]

class PermissionAuditMixin:
    """
    Mixin to add permission auditing to views.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to add permission auditing."""
        response = super().dispatch(request, *args, **kwargs)
        
        # Log successful permission checks
        if hasattr(request.user, 'adminuser') and response.status_code < 400:
            permission_used = getattr(self, 'permission_required', None)
            if permission_used:
                ActivityLog.objects.create(
                    admin_user=request.user.adminuser,
                    action='permission_used',
                    description=f'Used permission {permission_used}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    module='permission',
                    severity='low'
                )
        
        return response


class DynamicPermissionChecker:
    """
    Dynamic permission checker for complex business rules.
    """
    
    @staticmethod
    def check_time_based_permission(user: AdminUser, permission: str, 
                                  start_time: str = None, end_time: str = None) -> bool:
        """Check if permission is valid within time constraints."""
        if not start_time or not end_time:
            return True
        
        from datetime import datetime, time
        current_time = timezone.now().time()
        start = datetime.strptime(start_time, '%H:%M').time()
        end = datetime.strptime(end_time, '%H:%M').time()
        
        if start <= end:
            return start <= current_time <= end
        else:  # Overnight period
            return current_time >= start or current_time <= end
    
    @staticmethod
    def check_ip_based_permission(user: AdminUser, permission: str, 
                                allowed_ips: List[str], request_ip: str) -> bool:
        """Check if permission is valid from the current IP."""
        if not allowed_ips:
            return True
        
        import ipaddress
        request_ip_obj = ipaddress.ip_address(request_ip)
        
        for allowed_ip in allowed_ips:
            try:
                if '/' in allowed_ip:  # CIDR notation
                    network = ipaddress.ip_network(allowed_ip, strict=False)
                    if request_ip_obj in network:
                        return True
                else:  # Single IP
                    if request_ip_obj == ipaddress.ip_address(allowed_ip):
                        return True
            except ValueError:
                continue
        
        return False


class PermissionInheritanceManager:
    """
    Manages permission inheritance in role hierarchies.
    """
    
    ROLE_HIERARCHY = {
        'super_admin': [],
        'admin': ['super_admin'],
        'manager': ['admin', 'super_admin'],
        'analyst': ['manager', 'admin', 'super_admin'],
        'support': ['analyst', 'manager', 'admin', 'super_admin'],
        'viewer': ['support', 'analyst', 'manager', 'admin', 'super_admin']
    }
    
    @classmethod
    def get_inherited_permissions(cls, role: str) -> Set[str]:
        """Get all permissions inherited from parent roles."""
        inherited_permissions = set()
        
        # Get parent roles
        parent_roles = cls.ROLE_HIERARCHY.get(role, [])
        
        for parent_role in parent_roles:
            try:
                parent_role_obj = AdminRole.objects.get(name=parent_role, is_active=True)
                parent_permissions = parent_role_obj.get_all_permissions()
                inherited_permissions.update(perm.codename for perm in parent_permissions if perm.is_active)
            except AdminRole.DoesNotExist:
                continue
        
        return inherited_permissions
    
    @classmethod
    def validate_role_hierarchy(cls, user_role: str, target_role: str) -> bool:
        """Check if user can manage target role based on hierarchy."""
        if user_role == 'super_admin':
            return True
        
        user_hierarchy = cls.ROLE_HIERARCHY.get(user_role, [])
        return target_role in user_hierarchy or target_role == user_role


class PermissionValidationError(Exception):
    """Custom exception for permission validation errors."""
    pass


class PermissionValidator:
    """
    Validates permission assignments and role configurations.
    """
    
    @staticmethod
    def validate_permission_assignment(user: AdminUser, permission: AdminPermission) -> bool:
        """Validate if permission can be assigned to user."""
        # Check if user's role allows this permission
        try:
            role = AdminRole.objects.get(name=user.role, is_active=True)
            role_permissions = role.get_all_permissions()
            
            # Check if permission is allowed for this role
            if permission not in role_permissions:
                # Check if it's explicitly allowed as direct permission
                if not permission.allow_direct_assignment:
                    raise PermissionValidationError(
                        f"Permission {permission.codename} cannot be directly assigned to role {user.role}"
                    )
            
            return True
        except AdminRole.DoesNotExist:
            raise PermissionValidationError(f"Role {user.role} does not exist")
    
    @staticmethod
    def validate_role_permissions(role: AdminRole, permissions: List[AdminPermission]) -> bool:
        """Validate if all permissions are compatible with role."""
        for permission in permissions:
            if permission.minimum_role_level > role.level:
                raise PermissionValidationError(
                    f"Permission {permission.codename} requires minimum role level {permission.minimum_role_level}, "
                    f"but role {role.name} has level {role.level}"
                )
        
        return True

# Utility functions for permission management
def bulk_assign_permissions(users: List[AdminUser], permissions: List[str], 
                          assign: bool = True) -> Dict[str, Any]:
    """
    Bulk assign or remove permissions from multiple users.
    
    Args:
        users: List of AdminUser objects
        permissions: List of permission codenames
        assign: True to assign, False to remove
    
    Returns:
        Dictionary with operation results
    """
    results = {
        'success_count': 0,
        'error_count': 0,
        'errors': []
    }
    
    # Get permission objects
    permission_objects = AdminPermission.objects.filter(
        codename__in=permissions, is_active=True
    )
    
    if len(permission_objects) != len(permissions):
        found_perms = set(permission_objects.values_list('codename', flat=True))
        missing_perms = set(permissions) - found_perms
        results['errors'].append(f"Permissions not found: {missing_perms}")
    
    for user in users:
        try:
            if assign:
                user.permissions.add(*permission_objects)
            else:
                user.permissions.remove(*permission_objects)
            
            # Clear user's permission cache
            AdminPermissionManager.clear_user_cache(str(user.id))
            results['success_count'] += 1
            
        except Exception as e:
            results['error_count'] += 1
            results['errors'].append(f"Error for user {user.username}: {str(e)}")
    
    return results


def create_permission_template(name: str, permissions: List[str], 
                             description: str = None) -> Dict[str, Any]:
    """
    Create a permission template for common role configurations.
    
    Args:
        name: Template name
        permissions: List of permission codenames
        description: Optional description
    
    Returns:
        Template configuration dictionary
    """
    # Validate permissions exist
    existing_perms = AdminPermission.objects.filter(
        codename__in=permissions, is_active=True
    ).values_list('codename', flat=True)
    
    missing_perms = set(permissions) - set(existing_perms)
    if missing_perms:
        raise PermissionValidationError(f"Permissions not found: {missing_perms}")
    
    template = {
        'name': name,
        'description': description or f"Permission template: {name}",
        'permissions': list(existing_perms),
        'created_at': timezone.now().isoformat(),
        'permission_count': len(existing_perms)
    }
    
    return template


def analyze_permission_usage(days: int = 30) -> Dict[str, Any]:
    """
    Analyze permission usage over the specified period.
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Dictionary with usage analytics
    """
    from django.db.models import Count, Q
    from datetime import timedelta
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Get permission usage from activity logs
    permission_usage = ActivityLog.objects.filter(
        created_at__gte=start_date,
        action='permission_used'
    ).values('description').annotate(
        usage_count=Count('id'),
        unique_users=Count('admin_user', distinct=True)
    ).order_by('-usage_count')
    
    # Get permission denials
    permission_denials = ActivityLog.objects.filter(
        created_at__gte=start_date,
        action='permission_denied'
    ).values('description').annotate(
        denial_count=Count('id'),
        unique_users=Count('admin_user', distinct=True)
    ).order_by('-denial_count')
    
    # Get all permissions for comparison
    all_permissions = AdminPermission.objects.filter(is_active=True)
    
    return {
        'analysis_period_days': days,
        'total_permissions': all_permissions.count(),
        'permission_usage': list(permission_usage[:10]),
        'permission_denials': list(permission_denials[:10])
    }


def generate_permission_matrix(roles: List[str] = None) -> Dict[str, Any]:
    """
    Generate a permission matrix showing which roles have which permissions.
    
    Args:
        roles: List of role names to include (all if None)
    
    Returns:
        Dictionary with permission matrix data
    """
    # Get roles
    role_query = AdminRole.objects.filter(is_active=True)
    if roles:
        role_query = role_query.filter(name__in=roles)
    
    roles_data = role_query.prefetch_related('permissions').order_by('level')
    
    # Get all permissions
    all_permissions = AdminPermission.objects.filter(is_active=True).order_by('module', 'codename')
    
    matrix = {
        'roles': [],
        'permissions': [],
        'matrix': {}
    }
    
    # Build role list
    for role in roles_data:
        role_perms = set(role.permissions.values_list('codename', flat=True))
        inherited_perms = PermissionInheritanceManager.get_inherited_permissions(role.name)
        all_role_perms = role_perms.union(inherited_perms)
        
        matrix['roles'].append({
            'name': role.name,
            'display_name': role.display_name,
            'level': role.level,
            'permission_count': len(all_role_perms)
        })
    
    # Build permission list
    for perm in all_permissions:
        matrix['permissions'].append({
            'codename': perm.codename,
            'name': perm.name,
            'module': perm.module,
            'is_sensitive': perm.is_sensitive
        })
    
    # Build matrix
    for role in roles_data:
        role_perms = set(role.permissions.values_list('codename', flat=True))
        inherited_perms = PermissionInheritanceManager.get_inherited_permissions(role.name)
        all_role_perms = role_perms.union(inherited_perms)
        
        matrix['matrix'][role.name] = {}
        for perm in all_permissions:
            has_permission = perm.codename in all_role_perms
            is_inherited = perm.codename in inherited_perms and perm.codename not in role_perms
            
            matrix['matrix'][role.name][perm.codename] = {
                'has_permission': has_permission,
                'is_inherited': is_inherited,
                'is_direct': has_permission and not is_inherited
            }
    
    return matrix


def validate_permission_security(user: AdminUser, requested_permissions: List[str]) -> Dict[str, Any]:
    """
    Validate permission requests for security compliance.
    
    Args:
        user: AdminUser requesting permissions
        requested_permissions: List of permission codenames
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'valid': True,
        'warnings': [],
        'errors': [],
        'recommendations': []
    }
    
    # Get permission objects
    permissions = AdminPermission.objects.filter(codename__in=requested_permissions)
    
    for perm in permissions:
        # Check role level requirements
        try:
            user_role = AdminRole.objects.get(name=user.role, is_active=True)
            if perm.minimum_role_level < user_role.level:
                results['errors'].append(
                    f"Permission {perm.codename} requires role level {perm.minimum_role_level}, "
                    f"user has level {user_role.level}"
                )
                results['valid'] = False
        except AdminRole.DoesNotExist:
            results['errors'].append(f"User role {user.role} not found")
            results['valid'] = False
        
        # Check sensitive permissions
        if perm.is_sensitive:
            results['warnings'].append(
                f"Permission {perm.codename} is marked as sensitive - requires additional approval"
            )
        
        # Check direct assignment restrictions
        if not perm.allow_direct_assignment:
            results['warnings'].append(
                f"Permission {perm.codename} should only be assigned through roles"
            )
    
    # Check for permission combinations that might be risky
    sensitive_perms = [p.codename for p in permissions if p.is_sensitive]
    if len(sensitive_perms) > 3:
        results['warnings'].append(
            f"Requesting {len(sensitive_perms)} sensitive permissions - consider role-based assignment"
        )
    
    return results


class PermissionExportManager:
    """Manager for exporting and importing permission configurations."""
    
    @staticmethod
    def export_role_configuration(role_name: str) -> Dict[str, Any]:
        """Export complete role configuration including permissions."""
        try:
            role = AdminRole.objects.get(name=role_name, is_active=True)
        except AdminRole.DoesNotExist:
            raise PermissionValidationError(f"Role {role_name} not found")
        
        permissions = role.permissions.filter(is_active=True).values(
            'codename', 'name', 'module', 'action', 'resource', 'is_sensitive'
        )
        
        return {
            'role': {
                'name': role.name,
                'display_name': role.display_name,
                'description': role.description,
                'level': role.level,
                'is_active': role.is_active
            },
            'permissions': list(permissions),
            'permission_count': len(permissions),
            'exported_at': timezone.now().isoformat(),
            'export_version': '1.0'
        }
    
    @staticmethod
    def import_role_configuration(config: Dict[str, Any], overwrite: bool = False) -> Dict[str, Any]:
        """Import role configuration from exported data."""
        results = {
            'success': False,
            'created': False,
            'updated': False,
            'errors': []
        }
        
        try:
            role_data = config['role']
            permissions_data = config['permissions']
            
            # Check if role exists
            role, created = AdminRole.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'display_name': role_data['display_name'],
                    'description': role_data.get('description', ''),
                    'level': role_data['level']
                }
            )
            
            if created:
                results['created'] = True
            elif overwrite:
                role.display_name = role_data['display_name']
                role.description = role_data.get('description', '')
                role.level = role_data['level']
                role.save()
                results['updated'] = True
            
            # Import permissions
            permission_codenames = [p['codename'] for p in permissions_data]
            permissions = AdminPermission.objects.filter(
                codename__in=permission_codenames, is_active=True
            )
            
            if len(permissions) != len(permission_codenames):
                found_perms = set(permissions.values_list('codename', flat=True))
                missing_perms = set(permission_codenames) - found_perms
                results['errors'].append(f"Missing permissions: {missing_perms}")
            
            # Assign permissions to role
            if overwrite:
                role.permissions.clear()
            role.permissions.add(*permissions)
            
            results['success'] = True
            
        except Exception as e:
            results['errors'].append(f"Import error: {str(e)}")
        
        return results


class AdminPanelPermission(BasePermission):
    """
    Permission class for admin panel access.
    """
    
    def has_permission(self, request, view):
        """Check if user has admin panel access."""
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff and
            hasattr(request.user, 'adminuser')
        )
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        if not self.has_permission(request, view):
            return False
        
        # Allow access if user is super admin
        if hasattr(request.user, 'adminuser') and request.user.adminuser.role == 'super_admin':
            return True
        
        # Check if user owns the object
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        return False