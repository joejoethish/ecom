from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from .models import Tenant
import threading

# Thread-local storage for tenant context
_thread_locals = threading.local()


class TenantMiddleware(MiddlewareMixin):
    """Middleware to identify and set current tenant"""
    
    def process_request(self, request):
        # Get tenant from subdomain or domain
        host = request.get_host().lower()
        
        # Try to get tenant from cache first
        cache_key = f"tenant:{host}"
        tenant = cache.get(cache_key)
        
        if not tenant:
            try:
                # Check if it's a custom domain
                if '.' in host and not host.startswith('www.'):
                    tenant = Tenant.objects.get(domain=host, is_active=True)
                else:
                    # Extract subdomain
                    subdomain = host.split('.')[0]
                    if subdomain and subdomain != 'www':
                        tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
                    else:
                        # Default tenant or main site
                        tenant = None
                
                # Cache tenant for 5 minutes
                if tenant:
                    cache.set(cache_key, tenant, 300)
                    
            except Tenant.DoesNotExist:
                raise Http404("Tenant not found")
        
        # Set tenant in request and thread-local storage
        request.tenant = tenant
        set_current_tenant(tenant)
        
        return None


def get_current_tenant():
    """Get current tenant from thread-local storage"""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant):
    """Set current tenant in thread-local storage"""
    _thread_locals.tenant = tenant


class TenantQuerySetMixin:
    """Mixin to automatically filter querysets by tenant"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant'):
            queryset = queryset.filter(tenant=tenant)
        return queryset


class TenantModelMixin:
    """Mixin to automatically set tenant on model save"""
    
    def save(self, *args, **kwargs):
        if not self.tenant_id:
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
        super().save(*args, **kwargs)


class TenantPermissionMixin:
    """Mixin to check tenant-specific permissions"""
    
    def has_permission(self, request, view):
        # Check if user belongs to current tenant
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'tenant') and request.tenant:
                if request.user.tenant != request.tenant:
                    return False
        return super().has_permission(request, view)


class TenantUsageLimitMixin:
    """Mixin to enforce tenant usage limits"""
    
    def check_usage_limits(self, tenant, resource_type):
        """Check if tenant has exceeded usage limits"""
        if not tenant:
            return True
            
        current_usage = self.get_current_usage(tenant, resource_type)
        limit = self.get_usage_limit(tenant, resource_type)
        
        return current_usage < limit
    
    def get_current_usage(self, tenant, resource_type):
        """Get current usage for a resource type"""
        usage_map = {
            'users': tenant.users.count(),
            'products': getattr(tenant, 'products', lambda: 0)().count() if hasattr(tenant, 'products') else 0,
            'orders': getattr(tenant, 'orders', lambda: 0)().count() if hasattr(tenant, 'orders') else 0,
        }
        return usage_map.get(resource_type, 0)
    
    def get_usage_limit(self, tenant, resource_type):
        """Get usage limit for a resource type"""
        limit_map = {
            'users': tenant.max_users,
            'products': tenant.max_products,
            'orders': tenant.max_orders,
        }
        return limit_map.get(resource_type, float('inf'))


class TenantSecurityMixin:
    """Mixin for tenant security features"""
    
    def is_tenant_active(self, tenant):
        """Check if tenant is active and subscription is valid"""
        if not tenant or not tenant.is_active:
            return False
            
        if tenant.status in ['suspended', 'expired', 'cancelled']:
            return False
            
        return True
    
    def log_tenant_activity(self, tenant, user, action, model_name, object_id=None, changes=None):
        """Log tenant activity for audit purposes"""
        from .models import TenantAuditLog
        
        TenantAuditLog.objects.create(
            tenant=tenant,
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id) if object_id else None,
            changes=changes or {},
            ip_address=getattr(user, 'last_login_ip', None)
        )