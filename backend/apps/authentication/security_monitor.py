"""
Security monitoring utilities for authentication system.
"""
import logging
import json
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.core.mail import send_mail
from datetime import timedelta
from typing import Dict, List, Optional
from .models import PasswordResetAttempt, EmailVerificationAttempt, User

logger = logging.getLogger(__name__)


class SecurityMonitor:
    """
    Security monitoring and analysis for authentication system.
    Requirements: 1.1, 1.2, 2.1, 2.2 - IP-based rate limiting and monitoring
    """
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour
        
    def get_suspicious_ips(self, hours: int = 24) -> List[Dict]:
        """Get list of suspicious IP addresses in the last N hours."""
        suspicious_ips = []
        
        # Get IPs from cache (real-time monitoring)
        cache_pattern = "security:suspicious_ips:*"
        # Note: Django cache doesn't support pattern matching, so we'll track known suspicious IPs
        
        # Get IPs from database (historical data)
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Analyze password reset attempts
        password_reset_ips = (
            PasswordResetAttempt.objects
            .filter(created_at__gte=cutoff_time, success=False)
            .values('ip_address')
            .annotate(
                failed_attempts=models.Count('id'),
                latest_attempt=models.Max('created_at')
            )
            .filter(failed_attempts__gte=5)  # 5 or more failed attempts
        )
        
        for ip_data in password_reset_ips:
            suspicious_ips.append({
                'ip_address': ip_data['ip_address'],
                'activity_type': 'PASSWORD_RESET_ABUSE',
                'failed_attempts': ip_data['failed_attempts'],
                'latest_attempt': ip_data['latest_attempt'],
                'severity': 'HIGH' if ip_data['failed_attempts'] >= 10 else 'MEDIUM'
            })
        
        # Analyze email verification attempts
        email_verification_ips = (
            EmailVerificationAttempt.objects
            .filter(created_at__gte=cutoff_time, success=False)
            .values('ip_address')
            .annotate(
                failed_attempts=models.Count('id'),
                latest_attempt=models.Max('created_at')
            )
            .filter(failed_attempts__gte=5)  # 5 or more failed attempts
        )
        
        for ip_data in email_verification_ips:
            suspicious_ips.append({
                'ip_address': ip_data['ip_address'],
                'activity_type': 'EMAIL_VERIFICATION_ABUSE',
                'failed_attempts': ip_data['failed_attempts'],
                'latest_attempt': ip_data['latest_attempt'],
                'severity': 'MEDIUM'
            })
        
        return suspicious_ips
    
    def get_locked_accounts(self) -> List[Dict]:
        """Get list of currently locked accounts."""
        locked_accounts = User.objects.filter(
            account_locked_until__gt=timezone.now()
        ).values(
            'email', 'failed_login_attempts', 'account_locked_until', 'last_login_ip'
        )
        
        return [
            {
                'email': account['email'],
                'failed_attempts': account['failed_login_attempts'],
                'locked_until': account['account_locked_until'],
                'last_ip': account['last_login_ip'],
                'remaining_time': (account['account_locked_until'] - timezone.now()).total_seconds()
            }
            for account in locked_accounts
        ]
    
    def get_rate_limit_violations(self, hours: int = 1) -> List[Dict]:
        """Get recent rate limit violations from cache."""
        violations = []
        
        # This would typically query a logging system or database
        # For now, we'll return cached data structure
        
        return violations
    
    def analyze_login_patterns(self, hours: int = 24) -> Dict:
        """Analyze login patterns for anomalies."""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Analyze failed login attempts by IP
        failed_by_ip = {}
        password_attempts = PasswordResetAttempt.objects.filter(
            created_at__gte=cutoff_time,
            success=False
        )
        
        for attempt in password_attempts:
            ip = attempt.ip_address
            if ip not in failed_by_ip:
                failed_by_ip[ip] = {
                    'count': 0,
                    'emails': set(),
                    'user_agents': set()
                }
            
            failed_by_ip[ip]['count'] += 1
            failed_by_ip[ip]['emails'].add(attempt.email)
            failed_by_ip[ip]['user_agents'].add(attempt.user_agent[:50])  # Truncate for analysis
        
        # Identify potential brute force attacks
        brute_force_ips = {
            ip: data for ip, data in failed_by_ip.items()
            if data['count'] >= 10 or len(data['emails']) >= 5
        }
        
        # Analyze account lockouts
        recent_lockouts = User.objects.filter(
            account_locked_until__gte=cutoff_time
        ).count()
        
        return {
            'total_failed_attempts': sum(data['count'] for data in failed_by_ip.values()),
            'unique_ips_with_failures': len(failed_by_ip),
            'potential_brute_force_ips': len(brute_force_ips),
            'recent_account_lockouts': recent_lockouts,
            'brute_force_details': {
                ip: {
                    'attempts': data['count'],
                    'unique_emails': len(data['emails']),
                    'unique_user_agents': len(data['user_agents'])
                }
                for ip, data in brute_force_ips.items()
            }
        }
    
    def get_security_summary(self) -> Dict:
        """Get comprehensive security summary."""
        now = timezone.now()
        
        # Current status
        locked_accounts = self.get_locked_accounts()
        suspicious_ips = self.get_suspicious_ips(hours=24)
        
        # Recent activity analysis
        login_analysis = self.analyze_login_patterns(hours=24)
        
        # Rate limiting status
        rate_limit_config = getattr(settings, 'AUTH_RATE_LIMITING', {})
        
        return {
            'timestamp': now.isoformat(),
            'current_status': {
                'locked_accounts_count': len(locked_accounts),
                'suspicious_ips_count': len(suspicious_ips),
                'rate_limiting_enabled': rate_limit_config.get('ENABLED', False),
                'account_lockout_enabled': getattr(settings, 'ACCOUNT_LOCKOUT', {}).get('ENABLED', False),
            },
            'recent_activity': login_analysis,
            'locked_accounts': locked_accounts[:10],  # Limit to 10 most recent
            'suspicious_ips': suspicious_ips[:10],  # Limit to 10 most suspicious
            'security_settings': {
                'max_failed_attempts': getattr(settings, 'ACCOUNT_LOCKOUT', {}).get('MAX_FAILED_ATTEMPTS', 5),
                'lockout_duration_minutes': getattr(settings, 'ACCOUNT_LOCKOUT', {}).get('LOCKOUT_DURATION_MINUTES', 30),
                'login_rate_limit': rate_limit_config.get('LOGIN_ATTEMPTS', 5),
                'login_rate_window': rate_limit_config.get('LOGIN_WINDOW', 900),
            }
        }
    
    def log_security_event(self, event_type: str, details: Dict, severity: str = 'INFO'):
        """Log security events for monitoring."""
        log_message = f"SECURITY EVENT - Type: {event_type}, Severity: {severity}, Details: {details}"
        
        if severity == 'CRITICAL':
            logger.critical(log_message)
        elif severity == 'HIGH':
            logger.error(log_message)
        elif severity == 'MEDIUM':
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Store in cache for real-time monitoring
        cache_key = f"security:events:{event_type}:{int(timezone.now().timestamp())}"
        cache.set(cache_key, {
            'type': event_type,
            'details': details,
            'severity': severity,
            'timestamp': timezone.now().isoformat()
        }, 86400)  # Keep for 24 hours
    
    def check_ip_reputation(self, ip_address: str) -> Dict:
        """Check IP address reputation based on historical data."""
        # Check recent failed attempts
        recent_failures = PasswordResetAttempt.objects.filter(
            ip_address=ip_address,
            created_at__gte=timezone.now() - timedelta(hours=24),
            success=False
        ).count()
        
        # Check email verification failures
        email_failures = EmailVerificationAttempt.objects.filter(
            ip_address=ip_address,
            created_at__gte=timezone.now() - timedelta(hours=24),
            success=False
        ).count()
        
        # Calculate reputation score (0-100, higher is better)
        total_failures = recent_failures + email_failures
        
        if total_failures == 0:
            reputation_score = 100
            risk_level = 'LOW'
        elif total_failures <= 3:
            reputation_score = 80
            risk_level = 'LOW'
        elif total_failures <= 10:
            reputation_score = 50
            risk_level = 'MEDIUM'
        elif total_failures <= 20:
            reputation_score = 20
            risk_level = 'HIGH'
        else:
            reputation_score = 0
            risk_level = 'CRITICAL'
        
        return {
            'ip_address': ip_address,
            'reputation_score': reputation_score,
            'risk_level': risk_level,
            'recent_failures': total_failures,
            'password_reset_failures': recent_failures,
            'email_verification_failures': email_failures,
            'last_checked': timezone.now().isoformat()
        }


class SecurityNotificationService:
    """
    Service for sending security notifications and alerts.
    Requirements: 2.1, 2.2, 5.1, 5.2 - Implement security notification system
    """
    
    def __init__(self):
        self.admin_emails = getattr(settings, 'SECURITY_ADMIN_EMAILS', [])
        self.notification_enabled = getattr(settings, 'SECURITY_NOTIFICATIONS_ENABLED', True)
    
    def send_security_alert(self, alert_type: str, details: Dict, severity: str = 'MEDIUM'):
        """Send security alert to administrators."""
        if not self.notification_enabled or not self.admin_emails:
            return
        
        subject = f"Security Alert: {alert_type} ({severity})"
        
        message = f"""
Security Alert Detected

Alert Type: {alert_type}
Severity: {severity}
Timestamp: {timezone.now().isoformat()}

Details:
{json.dumps(details, indent=2)}

This is an automated security notification from the e-commerce platform.
Please review and take appropriate action if necessary.
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=self.admin_emails,
                fail_silently=False
            )
            logger.info(f"Security alert sent: {alert_type} ({severity})")
        except Exception as e:
            logger.error(f"Failed to send security alert: {str(e)}")
    
    def send_account_lockout_notification(self, user_email: str, ip_address: str, failed_attempts: int):
        """Send notification when an account is locked."""
        self.send_security_alert(
            alert_type='ACCOUNT_LOCKOUT',
            details={
                'user_email': user_email,
                'ip_address': ip_address,
                'failed_attempts': failed_attempts,
                'action': 'Account temporarily locked due to multiple failed login attempts'
            },
            severity='HIGH'
        )
    
    def send_brute_force_alert(self, ip_address: str, attempts: int, time_window: str):
        """Send notification for potential brute force attacks."""
        self.send_security_alert(
            alert_type='BRUTE_FORCE_ATTACK',
            details={
                'ip_address': ip_address,
                'attempts': attempts,
                'time_window': time_window,
                'action': 'Multiple failed authentication attempts detected from single IP'
            },
            severity='CRITICAL'
        )
    
    def send_suspicious_activity_alert(self, activity_type: str, ip_address: str, details: Dict):
        """Send notification for suspicious activities."""
        self.send_security_alert(
            alert_type='SUSPICIOUS_ACTIVITY',
            details={
                'activity_type': activity_type,
                'ip_address': ip_address,
                **details
            },
            severity='MEDIUM'
        )


class SecurityEventLogger:
    """
    Enhanced security event logging system.
    Requirements: 2.1, 2.2, 5.1, 5.2 - Create authentication event logging
    """
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.notification_service = SecurityNotificationService()
    
    def log_authentication_event(self, event_type: str, user_email: str = None, 
                                ip_address: str = None, user_agent: str = None, 
                                success: bool = True, details: Dict = None):
        """Log authentication events with structured data."""
        event_data = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'user_email': user_email,
            'ip_address': ip_address,
            'user_agent': user_agent[:100] if user_agent else None,  # Truncate for storage
            'success': success,
            'details': details or {}
        }
        
        # Log to structured logger
        log_message = f"AUTH_EVENT: {event_type} - User: {user_email}, IP: {ip_address}, Success: {success}"
        
        if success:
            self.logger.info(log_message, extra=event_data)
        else:
            self.logger.warning(log_message, extra=event_data)
        
        # Store in cache for real-time monitoring
        cache_key = f"security:auth_events:{int(timezone.now().timestamp())}"
        cache.set(cache_key, event_data, 86400)  # Keep for 24 hours
        
        # Check for patterns that require immediate attention
        self._analyze_event_patterns(event_data)
    
    def log_login_attempt(self, email: str, ip_address: str, user_agent: str, success: bool, failure_reason: str = None):
        """Log login attempts."""
        details = {}
        if not success and failure_reason:
            details['failure_reason'] = failure_reason
        
        self.log_authentication_event(
            event_type='LOGIN_ATTEMPT',
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details
        )
    
    def log_registration_attempt(self, email: str, ip_address: str, user_agent: str, success: bool, failure_reason: str = None):
        """Log registration attempts."""
        details = {}
        if not success and failure_reason:
            details['failure_reason'] = failure_reason
        
        self.log_authentication_event(
            event_type='REGISTRATION_ATTEMPT',
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details
        )
    
    def log_password_reset_request(self, email: str, ip_address: str, user_agent: str, success: bool):
        """Log password reset requests."""
        self.log_authentication_event(
            event_type='PASSWORD_RESET_REQUEST',
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
    
    def log_email_verification_attempt(self, email: str, ip_address: str, user_agent: str, success: bool):
        """Log email verification attempts."""
        self.log_authentication_event(
            event_type='EMAIL_VERIFICATION_ATTEMPT',
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
    
    def log_account_lockout(self, email: str, ip_address: str, failed_attempts: int):
        """Log account lockout events."""
        self.log_authentication_event(
            event_type='ACCOUNT_LOCKOUT',
            user_email=email,
            ip_address=ip_address,
            success=False,
            details={'failed_attempts': failed_attempts}
        )
        
        # Send immediate notification
        self.notification_service.send_account_lockout_notification(email, ip_address, failed_attempts)
    
    def log_suspicious_activity(self, activity_type: str, ip_address: str, details: Dict):
        """Log suspicious activities."""
        self.log_authentication_event(
            event_type='SUSPICIOUS_ACTIVITY',
            ip_address=ip_address,
            success=False,
            details={'activity_type': activity_type, **details}
        )
        
        # Send notification for critical activities
        if activity_type in ['BRUTE_FORCE_ATTEMPT', 'HIGH_REQUEST_RATE']:
            self.notification_service.send_suspicious_activity_alert(activity_type, ip_address, details)
    
    def _analyze_event_patterns(self, event_data: Dict):
        """Analyze event patterns for immediate threats."""
        if not event_data['success'] and event_data['ip_address']:
            # Check for brute force patterns
            self._check_brute_force_pattern(event_data['ip_address'], event_data['event_type'])
    
    def _check_brute_force_pattern(self, ip_address: str, event_type: str):
        """Check for brute force attack patterns."""
        # Count failed attempts in last hour
        hour_key = f"security:failed_attempts:{ip_address}:{int(timezone.now().timestamp()) // 3600}"
        failed_count = cache.get(hour_key, 0)
        cache.set(hour_key, failed_count + 1, 3600)
        
        # Alert if threshold exceeded
        if failed_count >= 10:  # 10 failed attempts in an hour
            self.notification_service.send_brute_force_alert(
                ip_address=ip_address,
                attempts=failed_count,
                time_window='1 hour'
            )


# Global security monitor instance
security_monitor = SecurityMonitor()
security_event_logger = SecurityEventLogger()
security_notification_service = SecurityNotificationService()