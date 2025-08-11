from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json
import threading

from .models import (
    ComplianceFramework, CompliancePolicy, ComplianceControl,
    ComplianceAssessment, ComplianceIncident, ComplianceTraining,
    ComplianceTrainingRecord, ComplianceAuditTrail, ComplianceRiskAssessment,
    ComplianceVendor, ComplianceReport
)

User = get_user_model()

# Thread-local storage for request context
_thread_locals = threading.local()


def get_current_request():
    """Get the current request from thread-local storage"""
    return getattr(_thread_locals, 'request', None)


def set_current_request(request):
    """Set the current request in thread-local storage"""
    _thread_locals.request = request


class ComplianceAuditMiddleware:
    """Middleware to capture request context for audit trails"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        set_current_request(None)
        return response


def create_audit_trail(sender, instance, action, **kwargs):
    """Create audit trail entry"""
    request = get_current_request()
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return
    
    # Get the changes if this is an update
    changes = {}
    if hasattr(instance, '_state') and instance._state.adding:
        action = 'create'
    elif action == 'delete':
        action = 'delete'
    else:
        action = 'update'
        # Get field changes (simplified - in production you'd want more sophisticated change tracking)
        if hasattr(instance, '_original_values'):
            for field, original_value in instance._original_values.items():
                current_value = getattr(instance, field, None)
                if original_value != current_value:
                    changes[field] = {
                        'old': str(original_value) if original_value is not None else None,
                        'new': str(current_value) if current_value is not None else None
                    }
    
    ComplianceAuditTrail.objects.create(
        user=request.user,
        action=action,
        model_name=sender.__name__,
        object_id=str(instance.pk),
        object_repr=str(instance),
        changes=changes,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        session_key=request.session.session_key if hasattr(request, 'session') else None
    )


# Store original values for change tracking
@receiver(pre_save)
def store_original_values(sender, instance, **kwargs):
    """Store original values before save for change tracking"""
    if sender._meta.app_label != 'compliance':
        return
    
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            instance._original_values = {}
            for field in instance._meta.fields:
                if not field.primary_key:
                    instance._original_values[field.name] = getattr(original, field.name)
        except sender.DoesNotExist:
            pass


# Audit trail signals
@receiver(post_save, sender=ComplianceFramework)
@receiver(post_save, sender=CompliancePolicy)
@receiver(post_save, sender=ComplianceControl)
@receiver(post_save, sender=ComplianceAssessment)
@receiver(post_save, sender=ComplianceIncident)
@receiver(post_save, sender=ComplianceTraining)
@receiver(post_save, sender=ComplianceTrainingRecord)
@receiver(post_save, sender=ComplianceRiskAssessment)
@receiver(post_save, sender=ComplianceVendor)
@receiver(post_save, sender=ComplianceReport)
def compliance_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for compliance models"""
    action = 'create' if created else 'update'
    create_audit_trail(sender, instance, action, **kwargs)
    
    # Send notifications based on the model and action
    send_compliance_notifications(sender, instance, action)


@receiver(post_delete, sender=ComplianceFramework)
@receiver(post_delete, sender=CompliancePolicy)
@receiver(post_delete, sender=ComplianceControl)
@receiver(post_delete, sender=ComplianceAssessment)
@receiver(post_delete, sender=ComplianceIncident)
@receiver(post_delete, sender=ComplianceTraining)
@receiver(post_delete, sender=ComplianceTrainingRecord)
@receiver(post_delete, sender=ComplianceRiskAssessment)
@receiver(post_delete, sender=ComplianceVendor)
@receiver(post_delete, sender=ComplianceReport)
def compliance_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for compliance models"""
    create_audit_trail(sender, instance, 'delete', **kwargs)


def send_compliance_notifications(sender, instance, action):
    """Send notifications based on compliance events"""
    notifications = []
    
    # Framework notifications
    if sender == ComplianceFramework:
        if action == 'create':
            notifications.append({
                'subject': f'New Compliance Framework Created: {instance.name}',
                'message': f'A new compliance framework "{instance.name}" has been created.',
                'recipients': get_compliance_managers()
            })
        elif action == 'update' and hasattr(instance, '_original_values'):
            if instance._original_values.get('status') != instance.status:
                notifications.append({
                    'subject': f'Framework Status Changed: {instance.name}',
                    'message': f'Framework "{instance.name}" status changed to {instance.status}.',
                    'recipients': get_compliance_managers()
                })
    
    # Policy notifications
    elif sender == CompliancePolicy:
        if action == 'create':
            notifications.append({
                'subject': f'New Policy Created: {instance.title}',
                'message': f'A new policy "{instance.title}" has been created and requires review.',
                'recipients': get_policy_reviewers()
            })
        elif action == 'update' and hasattr(instance, '_original_values'):
            if instance._original_values.get('status') != instance.status:
                if instance.status == 'approved':
                    notifications.append({
                        'subject': f'Policy Approved: {instance.title}',
                        'message': f'Policy "{instance.title}" has been approved.',
                        'recipients': [instance.owner.email] if instance.owner else []
                    })
                elif instance.status == 'active':
                    notifications.append({
                        'subject': f'Policy Published: {instance.title}',
                        'message': f'Policy "{instance.title}" is now active.',
                        'recipients': get_all_compliance_users()
                    })
    
    # Incident notifications
    elif sender == ComplianceIncident:
        if action == 'create':
            recipients = get_incident_responders()
            if instance.severity == 'critical':
                recipients.extend(get_compliance_managers())
            
            notifications.append({
                'subject': f'New Compliance Incident: {instance.title}',
                'message': f'A new {instance.severity} incident "{instance.title}" has been reported.',
                'recipients': recipients
            })
        elif action == 'update' and hasattr(instance, '_original_values'):
            if instance._original_values.get('status') != instance.status:
                if instance.status == 'resolved':
                    notifications.append({
                        'subject': f'Incident Resolved: {instance.title}',
                        'message': f'Incident "{instance.title}" has been resolved.',
                        'recipients': [instance.reported_by.email] if instance.reported_by else []
                    })
    
    # Training notifications
    elif sender == ComplianceTrainingRecord:
        if action == 'create':
            notifications.append({
                'subject': f'Training Assigned: {instance.training.title}',
                'message': f'You have been assigned training "{instance.training.title}". Due date: {instance.due_date}',
                'recipients': [instance.user.email]
            })
        elif action == 'update' and hasattr(instance, '_original_values'):
            if instance._original_values.get('status') != instance.status:
                if instance.status == 'completed':
                    notifications.append({
                        'subject': f'Training Completed: {instance.training.title}',
                        'message': f'Training "{instance.training.title}" has been completed.',
                        'recipients': get_training_managers()
                    })
    
    # Risk assessment notifications
    elif sender == ComplianceRiskAssessment:
        if action == 'create' and instance.inherent_risk_score >= 15:
            notifications.append({
                'subject': f'High Risk Identified: {instance.title}',
                'message': f'A high-risk assessment "{instance.title}" has been identified.',
                'recipients': get_risk_managers()
            })
    
    # Send all notifications
    for notification in notifications:
        send_notification_email(
            notification['subject'],
            notification['message'],
            notification['recipients']
        )


def send_notification_email(subject, message, recipients):
    """Send notification email"""
    if not recipients or not getattr(settings, 'EMAIL_HOST', None):
        return
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@compliance.com'),
            recipient_list=recipients,
            fail_silently=True
        )
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Failed to send notification email: {e}")


def get_compliance_managers():
    """Get email addresses of compliance managers"""
    return list(
        User.objects.filter(
            role__in=['compliance_manager', 'compliance_admin']
        ).values_list('email', flat=True)
    )


def get_policy_reviewers():
    """Get email addresses of policy reviewers"""
    return list(
        User.objects.filter(
            role__in=['compliance_manager', 'compliance_admin', 'compliance_officer']
        ).values_list('email', flat=True)
    )


def get_incident_responders():
    """Get email addresses of incident responders"""
    return list(
        User.objects.filter(
            role__in=['compliance_officer', 'compliance_analyst']
        ).values_list('email', flat=True)
    )


def get_training_managers():
    """Get email addresses of training managers"""
    return list(
        User.objects.filter(
            role__in=['compliance_manager', 'compliance_admin']
        ).values_list('email', flat=True)
    )


def get_risk_managers():
    """Get email addresses of risk managers"""
    return list(
        User.objects.filter(
            role__in=['compliance_manager', 'compliance_admin']
        ).values_list('email', flat=True)
    )


def get_all_compliance_users():
    """Get email addresses of all compliance users"""
    return list(
        User.objects.filter(
            role__in=[
                'compliance_admin', 'compliance_manager', 'compliance_officer',
                'compliance_analyst', 'compliance_viewer'
            ]
        ).values_list('email', flat=True)
    )


# Automated compliance checks
@receiver(post_save, sender=ComplianceControl)
def check_control_testing_schedule(sender, instance, **kwargs):
    """Check if control testing is overdue and create alerts"""
    if instance.next_test_date and instance.next_test_date < timezone.now().date():
        # Create an alert or notification for overdue testing
        send_notification_email(
            subject=f'Control Testing Overdue: {instance.title}',
            message=f'Control "{instance.title}" testing is overdue. Last tested: {instance.last_tested}',
            recipients=get_compliance_managers()
        )


@receiver(post_save, sender=ComplianceTrainingRecord)
def check_training_due_dates(sender, instance, **kwargs):
    """Check for overdue training and send reminders"""
    if (instance.due_date < timezone.now().date() and 
        instance.status in ['not_started', 'in_progress']):
        
        send_notification_email(
            subject=f'Training Overdue: {instance.training.title}',
            message=f'Your training "{instance.training.title}" is overdue. Please complete it as soon as possible.',
            recipients=[instance.user.email]
        )


@receiver(post_save, sender=CompliancePolicy)
def check_policy_review_dates(sender, instance, **kwargs):
    """Check for policies due for review"""
    if (instance.review_date <= timezone.now().date() and 
        instance.status == 'active'):
        
        send_notification_email(
            subject=f'Policy Review Due: {instance.title}',
            message=f'Policy "{instance.title}" is due for review.',
            recipients=[instance.owner.email] if instance.owner else get_policy_reviewers()
        )


@receiver(post_save, sender=ComplianceVendor)
def check_vendor_assessments(sender, instance, **kwargs):
    """Check for vendor assessments due"""
    if (instance.next_assessment_date <= timezone.now().date() and 
        instance.status == 'active'):
        
        send_notification_email(
            subject=f'Vendor Assessment Due: {instance.name}',
            message=f'Vendor "{instance.name}" assessment is due.',
            recipients=get_compliance_managers()
        )


# Compliance metrics calculation
@receiver(post_save, sender=ComplianceIncident)
def update_incident_metrics(sender, instance, **kwargs):
    """Update incident-related metrics"""
    # This could trigger recalculation of compliance dashboards
    # or update cached metrics
    pass


@receiver(post_save, sender=ComplianceTrainingRecord)
def update_training_metrics(sender, instance, **kwargs):
    """Update training completion metrics"""
    # This could trigger recalculation of training completion rates
    pass


# Data validation and business rules
@receiver(pre_save, sender=CompliancePolicy)
def validate_policy_approval(sender, instance, **kwargs):
    """Validate policy approval workflow"""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            # Ensure proper approval workflow
            if (original.status != 'approved' and instance.status == 'active'):
                raise ValueError("Policy must be approved before activation")
        except sender.DoesNotExist:
            pass


@receiver(pre_save, sender=ComplianceRiskAssessment)
def validate_risk_scores(sender, instance, **kwargs):
    """Validate risk assessment scores"""
    if instance.residual_risk_score > instance.inherent_risk_score:
        raise ValueError("Residual risk score cannot be higher than inherent risk score")


# Automated report generation
@receiver(post_save, sender=ComplianceReport)
def schedule_report_generation(sender, instance, **kwargs):
    """Schedule automated report generation"""
    if instance.scheduled and instance.next_run:
        # In a production environment, you would use Celery or similar
        # to schedule the actual report generation
        pass


# Integration with external systems
@receiver(post_save, sender=ComplianceIncident)
def integrate_with_external_systems(sender, instance, **kwargs):
    """Integrate with external compliance systems"""
    if instance.severity == 'critical' and instance.regulatory_notification_required:
        # Integrate with regulatory reporting systems
        # This is where you would call external APIs or services
        pass


# Cleanup and archival
@receiver(post_save, sender=ComplianceFramework)
def archive_old_frameworks(sender, instance, **kwargs):
    """Archive old framework versions"""
    if instance.status == 'archived':
        # Perform cleanup operations
        pass


# Performance optimization
@receiver(post_save)
def invalidate_compliance_cache(sender, instance, **kwargs):
    """Invalidate relevant caches when compliance data changes"""
    if sender._meta.app_label == 'compliance':
        # Invalidate dashboard caches, metrics caches, etc.
        # This would integrate with your caching system (Redis, Memcached, etc.)
        pass