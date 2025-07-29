"""
Authentication-related background tasks.
"""
import logging
from typing import Dict, Any
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_expired_password_reset_tokens(self):
    """
    Clean up expired password reset tokens to prevent database bloat.
    Removes tokens that are expired or older than 24 hours.
    
    Requirements: 2.6, 5.4
    """
    try:
        from apps.authentication.models import PasswordResetToken
        
        logger.info("Starting cleanup of expired password reset tokens")
        
        # Calculate cutoff times
        now = timezone.now()
        expired_cutoff = now  # Tokens past their expires_at time
        old_cutoff = now - timedelta(hours=24)  # Tokens older than 24 hours regardless of expiry
        
        with transaction.atomic():
            # Count tokens before cleanup for monitoring
            total_tokens_before = PasswordResetToken.objects.count()
            
            # Delete expired tokens (past their expires_at time)
            expired_deleted, _ = PasswordResetToken.objects.filter(
                expires_at__lt=expired_cutoff
            ).delete()
            
            # Delete old tokens (older than 24 hours, regardless of expiry status)
            old_deleted, _ = PasswordResetToken.objects.filter(
                created_at__lt=old_cutoff
            ).delete()
            
            # Delete used tokens older than 1 hour (keep recent ones for audit)
            used_cutoff = now - timedelta(hours=1)
            used_deleted, _ = PasswordResetToken.objects.filter(
                is_used=True,
                created_at__lt=used_cutoff
            ).delete()
            
            total_deleted = expired_deleted + old_deleted + used_deleted
            total_tokens_after = PasswordResetToken.objects.count()
        
        result = {
            "status": "success",
            "tokens_before": total_tokens_before,
            "tokens_after": total_tokens_after,
            "expired_deleted": expired_deleted,
            "old_deleted": old_deleted,
            "used_deleted": used_deleted,
            "total_deleted": total_deleted,
            "cleanup_time": now.isoformat()
        }
        
        logger.info(
            f"Password reset token cleanup completed. "
            f"Deleted {total_deleted} tokens: "
            f"{expired_deleted} expired, {old_deleted} old, {used_deleted} used"
        )
        
        return result
        
    except Exception as exc:
        logger.error(f"Password reset token cleanup failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_old_password_reset_attempts(self, days_old: int = 7):
    """
    Clean up old password reset attempts to prevent database bloat.
    Keeps recent attempts for rate limiting and security monitoring.
    
    Requirements: 2.6, 5.4
    """
    try:
        from apps.authentication.models import PasswordResetAttempt
        
        logger.info(f"Starting cleanup of password reset attempts older than {days_old} days")
        
        # Calculate cutoff time
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        with transaction.atomic():
            # Count attempts before cleanup
            total_attempts_before = PasswordResetAttempt.objects.count()
            
            # Delete old attempts but keep recent ones for rate limiting
            deleted_count, _ = PasswordResetAttempt.objects.filter(
                created_at__lt=cutoff_date
            ).delete()
            
            total_attempts_after = PasswordResetAttempt.objects.count()
        
        result = {
            "status": "success",
            "attempts_before": total_attempts_before,
            "attempts_after": total_attempts_after,
            "deleted_count": deleted_count,
            "cutoff_days": days_old,
            "cleanup_time": timezone.now().isoformat()
        }
        
        logger.info(
            f"Password reset attempts cleanup completed. "
            f"Deleted {deleted_count} attempts older than {days_old} days"
        )
        
        return result
        
    except Exception as exc:
        logger.error(f"Password reset attempts cleanup failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def monitor_password_reset_token_performance(self):
    """
    Monitor password reset token system performance and generate metrics.
    Tracks token usage patterns, cleanup efficiency, and system health.
    
    Requirements: 2.6, 5.4
    """
    try:
        from apps.authentication.models import PasswordResetToken, PasswordResetAttempt
        from django.db.models import Count, Avg
        from django.db.models.functions import TruncDate
        
        logger.info("Starting password reset token performance monitoring")
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Token statistics
        total_tokens = PasswordResetToken.objects.count()
        active_tokens = PasswordResetToken.objects.filter(
            is_used=False,
            expires_at__gt=now
        ).count()
        expired_tokens = PasswordResetToken.objects.filter(
            expires_at__lt=now
        ).count()
        used_tokens = PasswordResetToken.objects.filter(is_used=True).count()
        
        # Recent activity (last 24 hours)
        recent_tokens_created = PasswordResetToken.objects.filter(
            created_at__gte=last_24h
        ).count()
        recent_tokens_used = PasswordResetToken.objects.filter(
            is_used=True,
            updated_at__gte=last_24h
        ).count()
        
        # Reset attempt statistics
        total_attempts = PasswordResetAttempt.objects.count()
        recent_attempts = PasswordResetAttempt.objects.filter(
            created_at__gte=last_24h
        ).count()
        successful_attempts = PasswordResetAttempt.objects.filter(
            success=True,
            created_at__gte=last_7d
        ).count()
        
        # Calculate success rate
        total_recent_attempts = PasswordResetAttempt.objects.filter(
            created_at__gte=last_7d
        ).count()
        success_rate = (successful_attempts / total_recent_attempts * 100) if total_recent_attempts > 0 else 0
        
        # Daily usage pattern (last 7 days)
        daily_usage = list(PasswordResetToken.objects.filter(
            created_at__gte=last_7d
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date'))
        
        # Performance metrics
        metrics = {
            "status": "success",
            "monitoring_time": now.isoformat(),
            "token_statistics": {
                "total_tokens": total_tokens,
                "active_tokens": active_tokens,
                "expired_tokens": expired_tokens,
                "used_tokens": used_tokens,
                "recent_created_24h": recent_tokens_created,
                "recent_used_24h": recent_tokens_used
            },
            "attempt_statistics": {
                "total_attempts": total_attempts,
                "recent_attempts_24h": recent_attempts,
                "successful_attempts_7d": successful_attempts,
                "success_rate_7d": round(success_rate, 2)
            },
            "daily_usage_7d": daily_usage,
            "health_indicators": {
                "token_utilization_rate": round((used_tokens / total_tokens * 100) if total_tokens > 0 else 0, 2),
                "expired_token_ratio": round((expired_tokens / total_tokens * 100) if total_tokens > 0 else 0, 2),
                "cleanup_needed": expired_tokens > 100  # Flag if many expired tokens exist
            }
        }
        
        # Log important metrics
        logger.info(
            f"Password reset monitoring: {total_tokens} total tokens, "
            f"{active_tokens} active, {expired_tokens} expired, "
            f"success rate: {success_rate:.1f}%"
        )
        
        # Alert if cleanup is needed
        if expired_tokens > 100:
            logger.warning(f"High number of expired tokens detected: {expired_tokens}")
        
        return metrics
        
    except Exception as exc:
        logger.error(f"Password reset token monitoring failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_security_alert(self, alert_type: str, details: Dict[str, Any]):
    """
    Send security alerts for suspicious password reset activity.
    
    Requirements: 4.1, 4.4, 4.5
    """
    try:
        from apps.authentication.models import User
        from tasks.tasks import send_email_task
        
        logger.info(f"Sending password reset security alert: {alert_type}")
        
        # Get admin emails
        admin_emails = list(User.objects.filter(
            is_staff=True,
            email_notifications=True
        ).values_list('email', flat=True))
        
        if not admin_emails:
            logger.warning("No admin emails found for security alert")
            return {"status": "no_recipients"}
        
        # Prepare alert context
        context = {
            'alert_type': alert_type,
            'details': details,
            'timestamp': timezone.now(),
            'system_name': 'Password Reset System'
        }
        
        # Send alert email
        send_email_task.delay(
            subject=f"Security Alert: Password Reset - {alert_type}",
            message=f"Security alert detected in password reset system: {alert_type}",
            recipient_list=admin_emails,
            template_name='emails/security_alert.html',
            context=context
        )
        
        logger.info(f"Security alert sent to {len(admin_emails)} administrators")
        
        return {
            "status": "success",
            "alert_type": alert_type,
            "recipients_count": len(admin_emails)
        }
        
    except Exception as exc:
        logger.error(f"Security alert sending failed: {str(exc)}")
        raise self.retry(exc=exc)