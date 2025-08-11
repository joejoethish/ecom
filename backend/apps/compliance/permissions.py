from rest_framework import permissions
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

User = get_user_model()

class CompliancePermission(permissions.BasePermission):
    """
    Custom permission class for compliance management.
    Checks if user has appropriate compliance permissions.
    """
    
    # Permission mapping for different actions
    PERMISSION_MAP = {
        # Framework permissions
        'complianceframework': {
            'list': 'compliance.view_complianceframework',
            'retrieve': 'compliance.view_complianceframework',
            'create': 'compliance.add_complianceframework',
            'update': 'compliance.change_complianceframework',
            'partial_update': 'compliance.change_complianceframework',
            'destroy': 'compliance.delete_complianceframework',
            'activate': 'compliance.change_complianceframework',
            'deactivate': 'compliance.change_complianceframework',
            'export': 'compliance.view_complianceframework',
        },
        
        # Policy permissions
        'compliancepolicy': {
            'list': 'compliance.view_compliancepolicy',
            'retrieve': 'compliance.view_compliancepolicy',
            'create': 'compliance.add_compliancepolicy',
            'update': 'compliance.change_compliancepolicy',
            'partial_update': 'compliance.change_compliancepolicy',
            'destroy': 'compliance.delete_compliancepolicy',
            'approve': 'compliance.approve_compliancepolicy',
            'reject': 'compliance.approve_compliancepolicy',
            'publish': 'compliance.change_compliancepolicy',
            'archive': 'compliance.change_compliancepolicy',
            'export': 'compliance.view_compliancepolicy',
        },
        
        # Control permissions
        'compliancecontrol': {
            'list': 'compliance.view_compliancecontrol',
            'retrieve': 'compliance.view_compliancecontrol',
            'create': 'compliance.add_compliancecontrol',
            'update': 'compliance.change_compliancecontrol',
            'partial_update': 'compliance.change_compliancecontrol',
            'destroy': 'compliance.delete_compliancecontrol',
            'test': 'compliance.test_compliancecontrol',
            'assign': 'compliance.change_compliancecontrol',
            'export': 'compliance.view_compliancecontrol',
        },
        
        # Assessment permissions
        'complianceassessment': {
            'list': 'compliance.view_complianceassessment',
            'retrieve': 'compliance.view_complianceassessment',
            'create': 'compliance.add_complianceassessment',
            'update': 'compliance.change_complianceassessment',
            'partial_update': 'compliance.change_complianceassessment',
            'destroy': 'compliance.delete_complianceassessment',
            'conduct': 'compliance.conduct_complianceassessment',
            'complete': 'compliance.change_complianceassessment',
            'export': 'compliance.view_complianceassessment',
        },
        
        # Incident permissions
        'complianceincident': {
            'list': 'compliance.view_complianceincident',
            'retrieve': 'compliance.view_complianceincident',
            'create': 'compliance.add_complianceincident',
            'update': 'compliance.change_complianceincident',
            'partial_update': 'compliance.change_complianceincident',
            'destroy': 'compliance.delete_complianceincident',
            'assign': 'compliance.change_complianceincident',
            'resolve': 'compliance.resolve_complianceincident',
            'close': 'compliance.resolve_complianceincident',
            'escalate': 'compliance.escalate_complianceincident',
            'export': 'compliance.view_complianceincident',
        },
        
        # Training permissions
        'compliancetraining': {
            'list': 'compliance.view_compliancetraining',
            'retrieve': 'compliance.view_compliancetraining',
            'create': 'compliance.add_compliancetraining',
            'update': 'compliance.change_compliancetraining',
            'partial_update': 'compliance.change_compliancetraining',
            'destroy': 'compliance.delete_compliancetraining',
            'assign': 'compliance.assign_compliancetraining',
            'activate': 'compliance.change_compliancetraining',
            'export': 'compliance.view_compliancetraining',
        },
        
        # Training Record permissions
        'compliancetrainingrecord': {
            'list': 'compliance.view_compliancetrainingrecord',
            'retrieve': 'compliance.view_compliancetrainingrecord',
            'create': 'compliance.add_compliancetrainingrecord',
            'update': 'compliance.change_compliancetrainingrecord',
            'partial_update': 'compliance.change_compliancetrainingrecord',
            'destroy': 'compliance.delete_compliancetrainingrecord',
            'complete': 'compliance.change_compliancetrainingrecord',
            'issue_certificate': 'compliance.issue_certificate',
            'export': 'compliance.view_compliancetrainingrecord',
        },
        
        # Audit Trail permissions
        'complianceaudittrail': {
            'list': 'compliance.view_complianceaudittrail',
            'retrieve': 'compliance.view_complianceaudittrail',
            'export': 'compliance.view_complianceaudittrail',
        },
        
        # Risk Assessment permissions
        'complianceriskassessment': {
            'list': 'compliance.view_complianceriskassessment',
            'retrieve': 'compliance.view_complianceriskassessment',
            'create': 'compliance.add_complianceriskassessment',
            'update': 'compliance.change_complianceriskassessment',
            'partial_update': 'compliance.change_complianceriskassessment',
            'destroy': 'compliance.delete_complianceriskassessment',
            'assess': 'compliance.assess_compliancerisk',
            'mitigate': 'compliance.mitigate_compliancerisk',
            'accept': 'compliance.accept_compliancerisk',
            'export': 'compliance.view_complianceriskassessment',
        },
        
        # Vendor permissions
        'compliancevendor': {
            'list': 'compliance.view_compliancevendor',
            'retrieve': 'compliance.view_compliancevendor',
            'create': 'compliance.add_compliancevendor',
            'update': 'compliance.change_compliancevendor',
            'partial_update': 'compliance.change_compliancevendor',
            'destroy': 'compliance.delete_compliancevendor',
            'assess': 'compliance.assess_compliancevendor',
            'onboard': 'compliance.onboard_compliancevendor',
            'terminate': 'compliance.terminate_compliancevendor',
            'export': 'compliance.view_compliancevendor',
        },
        
        # Report permissions
        'compliancereport': {
            'list': 'compliance.view_compliancereport',
            'retrieve': 'compliance.view_compliancereport',
            'create': 'compliance.add_compliancereport',
            'update': 'compliance.change_compliancereport',
            'partial_update': 'compliance.change_compliancereport',
            'destroy': 'compliance.delete_compliancereport',
            'generate': 'compliance.generate_compliancereport',
            'schedule': 'compliance.schedule_compliancereport',
            'download': 'compliance.download_compliancereport',
            'export': 'compliance.view_compliancereport',
        },
    }
    
    def has_permission(self, request, view):
        """
        Check if user has permission to access the view.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin has all permissions
        if request.user.is_superuser:
            return True
        
        # Get the model name and action
        model_name = getattr(view, 'model_name', None)
        if not model_name:
            # Try to get from queryset
            if hasattr(view, 'queryset') and view.queryset is not None:
                model_name = view.queryset.model.__name__.lower()
            elif hasattr(view, 'get_queryset'):
                try:
                    queryset = view.get_queryset()
                    if queryset is not None:
                        model_name = queryset.model.__name__.lower()
                except:
                    pass
        
        if not model_name:
            return False
        
        action = view.action if hasattr(view, 'action') else 'list'
        
        # Get required permission
        required_permission = self.get_required_permission(model_name, action)
        if not required_permission:
            return False
        
        # Check if user has the required permission
        return request.user.has_perm(required_permission)
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access specific object.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin has all permissions
        if request.user.is_superuser:
            return True
        
        # Get the model name and action
        model_name = obj.__class__.__name__.lower()
        action = view.action if hasattr(view, 'action') else 'retrieve'
        
        # Get required permission
        required_permission = self.get_required_permission(model_name, action)
        if not required_permission:
            return False
        
        # Check if user has the required permission
        if not request.user.has_perm(required_permission):
            return False
        
        # Additional object-level checks
        return self.check_object_level_permission(request.user, obj, action)
    
    def get_required_permission(self, model_name, action):
        """
        Get the required permission for a model and action.
        """
        model_permissions = self.PERMISSION_MAP.get(model_name, {})
        return model_permissions.get(action)
    
    def check_object_level_permission(self, user, obj, action):
        """
        Check object-level permissions based on ownership and business rules.
        """
        # Check if user is the owner of the object
        if hasattr(obj, 'created_by') and obj.created_by == user:
            return True
        
        # Check if user is assigned to the object
        if hasattr(obj, 'assigned_to') and obj.assigned_to == user:
            return True
        
        # Check if user is the owner of the object
        if hasattr(obj, 'owner') and obj.owner == user:
            return True
        
        # Check if user is the assessor
        if hasattr(obj, 'assessor') and obj.assessor == user:
            return True
        
        # Check if user reported the incident
        if hasattr(obj, 'reported_by') and obj.reported_by == user:
            return True
        
        # Check if user is the risk owner
        if hasattr(obj, 'risk_owner') and obj.risk_owner == user:
            return True
        
        # For read-only actions, allow if user has view permission
        if action in ['retrieve', 'list', 'export']:
            return True
        
        # For other actions, check if user has appropriate role-based permissions
        return self.check_role_based_permission(user, obj, action)
    
    def check_role_based_permission(self, user, obj, action):
        """
        Check role-based permissions for specific actions.
        """
        # Get user's role
        user_role = getattr(user, 'role', None)
        
        # Define role hierarchy
        role_hierarchy = {
            'compliance_admin': 5,
            'compliance_manager': 4,
            'compliance_officer': 3,
            'compliance_analyst': 2,
            'compliance_viewer': 1,
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        
        # Define minimum role levels for actions
        action_requirements = {
            'create': 2,  # Analyst and above
            'update': 2,  # Analyst and above
            'delete': 4,  # Manager and above
            'approve': 4,  # Manager and above
            'resolve': 3,  # Officer and above
            'escalate': 3,  # Officer and above
            'assign': 3,  # Officer and above
            'conduct': 3,  # Officer and above
            'assess': 3,  # Officer and above
            'mitigate': 3,  # Officer and above
            'accept': 4,  # Manager and above
            'generate': 2,  # Analyst and above
            'schedule': 3,  # Officer and above
        }
        
        required_level = action_requirements.get(action, 1)
        return user_level >= required_level


class ComplianceFrameworkPermission(CompliancePermission):
    """
    Specific permission class for Compliance Framework operations.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Framework-specific object permissions.
        """
        if not super().has_object_permission(request, view, obj):
            return False
        
        # Additional framework-specific checks
        action = view.action if hasattr(view, 'action') else 'retrieve'
        
        # Only compliance admins can delete active frameworks
        if action == 'destroy' and obj.status == 'active':
            return request.user.role == 'compliance_admin'
        
        return True


class CompliancePolicyPermission(CompliancePermission):
    """
    Specific permission class for Compliance Policy operations.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Policy-specific object permissions.
        """
        if not super().has_object_permission(request, view, obj):
            return False
        
        action = view.action if hasattr(view, 'action') else 'retrieve'
        
        # Only policy owners or managers can approve policies
        if action in ['approve', 'reject']:
            return (obj.owner == request.user or 
                   request.user.role in ['compliance_manager', 'compliance_admin'])
        
        # Only owners or managers can publish policies
        if action == 'publish':
            return (obj.owner == request.user or 
                   request.user.role in ['compliance_manager', 'compliance_admin'])
        
        return True


class ComplianceIncidentPermission(CompliancePermission):
    """
    Specific permission class for Compliance Incident operations.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Incident-specific object permissions.
        """
        if not super().has_object_permission(request, view, obj):
            return False
        
        action = view.action if hasattr(view, 'action') else 'retrieve'
        
        # Critical incidents require manager approval for resolution
        if action in ['resolve', 'close'] and obj.severity == 'critical':
            return request.user.role in ['compliance_manager', 'compliance_admin']
        
        # Only assigned users or managers can update incidents
        if action in ['update', 'partial_update']:
            return (obj.assigned_to == request.user or 
                   obj.reported_by == request.user or
                   request.user.role in ['compliance_manager', 'compliance_admin'])
        
        return True


class ComplianceTrainingPermission(CompliancePermission):
    """
    Specific permission class for Compliance Training operations.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Training-specific object permissions.
        """
        if not super().has_object_permission(request, view, obj):
            return False
        
        action = view.action if hasattr(view, 'action') else 'retrieve'
        
        # Only training creators or managers can assign training
        if action == 'assign':
            return (obj.created_by == request.user or 
                   request.user.role in ['compliance_manager', 'compliance_admin'])
        
        return True


class ComplianceRiskPermission(CompliancePermission):
    """
    Specific permission class for Compliance Risk Assessment operations.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Risk-specific object permissions.
        """
        if not super().has_object_permission(request, view, obj):
            return False
        
        action = view.action if hasattr(view, 'action') else 'retrieve'
        
        # High and critical risks require manager approval for acceptance
        if action == 'accept' and obj.inherent_risk_score >= 15:
            return request.user.role in ['compliance_manager', 'compliance_admin']
        
        # Only risk owners or managers can mitigate risks
        if action == 'mitigate':
            return (obj.risk_owner == request.user or 
                   request.user.role in ['compliance_manager', 'compliance_admin'])
        
        return True


class ComplianceReportPermission(CompliancePermission):
    """
    Specific permission class for Compliance Report operations.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Report-specific object permissions.
        """
        if not super().has_object_permission(request, view, obj):
            return False
        
        action = view.action if hasattr(view, 'action') else 'retrieve'
        
        # Only report creators or managers can schedule reports
        if action == 'schedule':
            return (obj.generated_by == request.user or 
                   request.user.role in ['compliance_manager', 'compliance_admin'])
        
        return True


class ComplianceAuditTrailPermission(permissions.BasePermission):
    """
    Special permission class for Audit Trail - read-only for most users.
    """
    
    def has_permission(self, request, view):
        """
        Only authenticated users with audit trail view permission can access.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin has all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user has audit trail view permission
        return request.user.has_perm('compliance.view_complianceaudittrail')
    
    def has_object_permission(self, request, view, obj):
        """
        Audit trail is read-only for all users except super admin.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin can do anything
        if request.user.is_superuser:
            return True
        
        # All other users can only view
        action = view.action if hasattr(view, 'action') else 'retrieve'
        return action in ['retrieve', 'list', 'export']


# Utility functions for permission checking
def check_compliance_permission(user, permission_name):
    """
    Utility function to check if user has specific compliance permission.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    return user.has_perm(f'compliance.{permission_name}')


def get_user_compliance_permissions(user):
    """
    Get all compliance permissions for a user.
    """
    if not user or not user.is_authenticated:
        return []
    
    if user.is_superuser:
        return ['all']
    
    permissions = []
    for model_perms in CompliancePermission.PERMISSION_MAP.values():
        for perm in model_perms.values():
            if user.has_perm(perm) and perm not in permissions:
                permissions.append(perm)
    
    return permissions


def can_user_access_compliance_module(user):
    """
    Check if user can access compliance module at all.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    # Check if user has any compliance permission
    compliance_permissions = get_user_compliance_permissions(user)
    return len(compliance_permissions) > 0