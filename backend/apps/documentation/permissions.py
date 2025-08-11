from rest_framework import permissions
from django.db.models import Q


class DocumentationPermission(permissions.BasePermission):
    """
    Custom permission for documentation.
    - Public documents: readable by all authenticated users
    - Internal documents: readable by all authenticated users, editable by author
    - Restricted documents: readable/editable by author and contributors
    - Private documents: readable/editable by author only
    """

    def has_permission(self, request, view):
        """Check if user has permission to access the view"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the specific object"""
        user = request.user
        
        # Staff users have full access
        if user.is_staff:
            return True
        
        # Read permissions
        if request.method in permissions.SAFE_METHODS:
            if obj.visibility == 'public':
                return True
            elif obj.visibility == 'internal':
                return True
            elif obj.visibility == 'restricted':
                return (
                    obj.author == user or
                    obj.contributors.filter(id=user.id).exists()
                )
            elif obj.visibility == 'private':
                return obj.author == user
        
        # Write permissions
        else:
            if obj.visibility in ['public', 'internal']:
                return obj.author == user
            elif obj.visibility == 'restricted':
                return (
                    obj.author == user or
                    obj.contributors.filter(id=user.id).exists()
                )
            elif obj.visibility == 'private':
                return obj.author == user
        
        return False


class DocumentationCategoryPermission(permissions.BasePermission):
    """Permission for documentation categories"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions for staff only
        return request.user.is_staff


class DocumentationTemplatePermission(permissions.BasePermission):
    """Permission for documentation templates"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions for template creator or staff
        return obj.created_by == request.user or request.user.is_staff


class DocumentationReviewPermission(permissions.BasePermission):
    """Permission for documentation reviews"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for document author, reviewer, and staff
        if request.method in permissions.SAFE_METHODS:
            return (
                obj.documentation.author == request.user or
                obj.reviewer == request.user or
                request.user.is_staff
            )
        
        # Write permissions for reviewer only
        return obj.reviewer == request.user


class DocumentationAnalyticsPermission(permissions.BasePermission):
    """Permission for documentation analytics"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Only document authors and staff can view analytics
        return (
            obj.documentation.author == request.user or
            request.user.is_staff
        )