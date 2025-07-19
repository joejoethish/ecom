"""
Custom permission classes for the ecommerce platform.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Custom permission for seller-specific operations.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and hasattr(request.user, 'seller_profile')


class IsCustomerOrReadOnly(permissions.BasePermission):
    """
    Custom permission for customer-specific operations.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and hasattr(request.user, 'customer_profile')


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission for admin-only write operations.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners or admins to access/modify objects.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin users can access everything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user is the owner (works for different object types)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'customer') and hasattr(obj.customer, 'user'):
            return obj.customer.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False