from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TraceStep, WorkflowSession


@receiver(pre_save, sender=TraceStep)
def calculate_trace_step_duration(sender, instance, **kwargs):
    """Calculate duration when trace step is completed"""
    if instance.status == 'completed' and instance.end_time and instance.start_time:
        if not instance.duration_ms:
            delta = instance.end_time - instance.start_time
            instance.duration_ms = int(delta.total_seconds() * 1000)


@receiver(post_save, sender=TraceStep)
def update_workflow_session_status(sender, instance, created, **kwargs):
    """Update workflow session status based on trace steps"""
    if not created and instance.status in ['failed', 'completed']:
        workflow = instance.workflow_session
        
        # Check if all trace steps are completed or failed
        pending_steps = workflow.trace_steps.filter(status__in=['started'])
        
        if not pending_steps.exists():
            # All steps are done, determine workflow status
            failed_steps = workflow.trace_steps.filter(status='failed')
            
            if failed_steps.exists():
                workflow.status = 'failed'
            else:
                workflow.status = 'completed'
            
            workflow.end_time = timezone.now()
            workflow.save()


@receiver(pre_save, sender=WorkflowSession)
def set_workflow_correlation_id(sender, instance, **kwargs):
    """Ensure workflow session has a correlation ID"""
    if not instance.correlation_id:
        import uuid
        instance.correlation_id = uuid.uuid4()