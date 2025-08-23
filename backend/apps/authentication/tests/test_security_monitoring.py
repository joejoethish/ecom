"""
Tests for authentication security monitoring system.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.authentication.security_monitor import (
    SecurityMonitor, SecurityEventLogger, SecurityNotificationService
)
from apps.authentication.models import PasswordResetAttempt, EmailVerificationAttempt

User = get_user_model()


class SecurityMonitorTest(TestCase):
    """Test security monitoring functionality."""
    
    def setUp(self):
        self.monitor = SecurityMonitor()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cache.clear()
    
    def test_get_suspicious_ips_password_reset_abuse(self):
        """Test detection of suspicious IPs from password reset abuse."""
        # Create multiple failed password reset attempts from same IP
        for i in range(6):
            PasswordResetAttempt.objects.create(
                ip_address='192.168.1.100',
                email=f'test{i}@example.com',
                success=False,
                user_agent='Test Agent'
            )
        
        suspicious_ips = self.monitor.get_suspicious_ips(hours=24)
        
        self.assertEqual(len(suspicious_ips), 1)
        self.assertEqual(suspicious_ips[0]['ip_address'], '192.168.1.100')
        self.assertEqual(suspicious_ips[0]['activity_type'], 'PASSWORD_RESET_ABUSE')
        self.assertEqual(suspicious_ips[0]['failed_attempts'], 6)
        self.assertEqual(suspicious_ips[0]['severity'], 'MEDIUM')
    
    def test_get_suspicious_ips_email_verification_abuse(self):
        """Test detection of suspicious IPs from email verification abuse."""
        # Create multiple failed email verification attempts from same IP
        for i in range(7):
            EmailVerificationAttempt.objects.create(
                ip_address='192.168.1.101',
                email=f'test{i}@example.com',
                success=False,
                user_agent='Test Agent'
            )
        
        suspicious_ips = self.monitor.get_suspicious_ips(hours=24)
        
        self.assertEqual(len(suspicious_ips), 1)
        self.assertEqual(suspicious_ips[0]['ip_address'], '192.168.1.101')
        self.assertEqual(suspicious_ips[0]['activity_type'], 'EMAIL_VERIFICATION_ABUSE')
        self.assertEqual(suspicious_ips[0]['failed_attempts'], 7)
    
    def test_get_locked_accounts(self):
        """Test retrieval of locked accounts."""
        # Lock the test user account
        self.user.lock_account()
        
        locked_accounts = self.monitor.get_locked_accounts()
        
        self.assertEqual(len(locked_accounts), 1)
        self.assertEqual(locked_accounts[0]['email'], 'test@example.com')
        self.assertEqual(locked_accounts[0]['failed_attempts'], 5)  # Default lockout threshold
        self.assertIsNotNone(locked_accounts[0]['locked_until'])
        self.assertGreater(locked_accounts[0]['remaining_time'], 0)
    
    def test_analyze_login_patterns(self):
        """Test login pattern analysis."""
        # Create various password reset attempts
        PasswordResetAttempt.objects.create(
            ip_address='192.168.1.100',
            email='test1@example.com',
            success=False,
            user_agent='Agent1'
        )
        PasswordResetAttempt.objects.create(
            ip_address='192.168.1.100',
            email='test2@example.com',
            success=False,
            user_agent='Agent2'
        )
        PasswordResetAttempt.objects.create(
            ip_address='192.168.1.101',
            email='test3@example.com',
            success=False,
            user_agent='Agent1'
        )
        
        analysis = self.monitor.analyze_login_patterns(hours=24)
        
        self.assertEqual(analysis['total_failed_attempts'], 3)
        self.assertEqual(analysis['unique_ips_with_failures'], 2)
        self.assertEqual(analysis['potential_brute_force_ips'], 0)  # Not enough attempts yet
    
    def test_check_ip_reputation(self):
        """Test IP reputation checking."""
        # Create some failed attempts for an IP
        for i in range(3):
            PasswordResetAttempt.objects.create(
                ip_address='192.168.1.100',
                email=f'test{i}@example.com',
                success=False,
                user_agent='Test Agent'
            )
        
        reputation = self.monitor.check_ip_reputation('192.168.1.100')
        
        self.assertEqual(reputation['ip_address'], '192.168.1.100')
        self.assertEqual(reputation['recent_failures'], 3)
        self.assertEqual(reputation['password_reset_failures'], 3)
        self.assertEqual(reputation['email_verification_failures'], 0)
        self.assertEqual(reputation['reputation_score'], 80)  # LOW risk for 3 failures
        self.assertEqual(reputation['risk_level'], 'LOW')
    
    def test_get_security_summary(self):
        """Test comprehensive security summary."""
        # Create some test data
        self.user.lock_account()
        
        PasswordResetAttempt.objects.create(
            ip_address='192.168.1.100',
            email='test@example.com',
            success=False,
            user_agent='Test Agent'
        )
        
        summary = self.monitor.get_security_summary()
        
        self.assertIn('timestamp', summary)
        self.assertIn('current_status', summary)
        self.assertIn('recent_activity', summary)
        self.assertIn('locked_accounts', summary)
        self.assertIn('suspicious_ips', summary)
        self.assertIn('security_settings', summary)
        
        self.assertEqual(summary['current_status']['locked_accounts_count'], 1)


class SecurityEventLoggerTest(TestCase):
    """Test security event logging functionality."""
    
    def setUp(self):
        self.logger = SecurityEventLogger()
        cache.clear()
    
    @patch('apps.authentication.security_monitor.logger')
    def test_log_authentication_event(self, mock_logger):
        """Test basic authentication event logging."""
        self.logger.log_authentication_event(
            event_type='LOGIN_ATTEMPT',
            user_email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Test Agent',
            success=True
        )
        
        # Check that event was logged
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        self.assertIn('LOGIN_ATTEMPT', call_args[0][0])
        self.assertIn('test@example.com', call_args[0][0])
    
    @patch('apps.authentication.security_monitor.logger')
    def test_log_failed_authentication_event(self, mock_logger):
        """Test logging of failed authentication events."""
        self.logger.log_authentication_event(
            event_type='LOGIN_ATTEMPT',
            user_email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Test Agent',
            success=False,
            details={'failure_reason': 'Invalid password'}
        )
        
        # Check that event was logged as warning
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        self.assertIn('LOGIN_ATTEMPT', call_args[0][0])
        self.assertIn('Success: False', call_args[0][0])
    
    def test_log_login_attempt(self):
        """Test login attempt logging."""
        with patch.object(self.logger, 'log_authentication_event') as mock_log:
            self.logger.log_login_attempt(
                email='test@example.com',
                ip_address='192.168.1.1',
                user_agent='Test Agent',
                success=True
            )
            
            mock_log.assert_called_once_with(
                event_type='LOGIN_ATTEMPT',
                user_email='test@example.com',
                ip_address='192.168.1.1',
                user_agent='Test Agent',
                success=True,
                details={}
            )
    
    def test_log_registration_attempt(self):
        """Test registration attempt logging."""
        with patch.object(self.logger, 'log_authentication_event') as mock_log:
            self.logger.log_registration_attempt(
                email='test@example.com',
                ip_address='192.168.1.1',
                user_agent='Test Agent',
                success=False,
                failure_reason='Email already exists'
            )
            
            mock_log.assert_called_once_with(
                event_type='REGISTRATION_ATTEMPT',
                user_email='test@example.com',
                ip_address='192.168.1.1',
                user_agent='Test Agent',
                success=False,
                details={'failure_reason': 'Email already exists'}
            )
    
    @patch('apps.authentication.security_monitor.SecurityNotificationService.send_account_lockout_notification')
    def test_log_account_lockout(self, mock_notification):
        """Test account lockout logging with notification."""
        self.logger.log_account_lockout(
            email='test@example.com',
            ip_address='192.168.1.1',
            failed_attempts=5
        )
        
        # Check that notification was sent
        mock_notification.assert_called_once_with(
            'test@example.com', '192.168.1.1', 5
        )
    
    @patch('apps.authentication.security_monitor.SecurityNotificationService.send_suspicious_activity_alert')
    def test_log_suspicious_activity_with_notification(self, mock_notification):
        """Test suspicious activity logging with notification."""
        self.logger.log_suspicious_activity(
            activity_type='BRUTE_FORCE_ATTEMPT',
            ip_address='192.168.1.1',
            details={'attempts': 15}
        )
        
        # Check that notification was sent for critical activity
        mock_notification.assert_called_once_with(
            'BRUTE_FORCE_ATTEMPT', '192.168.1.1', {'attempts': 15}
        )


@override_settings(
    SECURITY_ADMIN_EMAILS=['admin@example.com'],
    SECURITY_NOTIFICATIONS_ENABLED=True,
    DEFAULT_FROM_EMAIL='noreply@example.com'
)
class SecurityNotificationServiceTest(TestCase):
    """Test security notification service."""
    
    def setUp(self):
        self.service = SecurityNotificationService()
    
    @patch('apps.authentication.security_monitor.send_mail')
    def test_send_security_alert(self, mock_send_mail):
        """Test sending security alerts."""
        self.service.send_security_alert(
            alert_type='TEST_ALERT',
            details={'test': 'data'},
            severity='HIGH'
        )
        
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        
        self.assertIn('Security Alert: TEST_ALERT (HIGH)', call_args[1]['subject'])
        self.assertEqual(call_args[1]['recipient_list'], ['admin@example.com'])
        self.assertIn('TEST_ALERT', call_args[1]['message'])
        self.assertIn('HIGH', call_args[1]['message'])
    
    @patch('apps.authentication.security_monitor.send_mail')
    def test_send_account_lockout_notification(self, mock_send_mail):
        """Test account lockout notification."""
        self.service.send_account_lockout_notification(
            user_email='test@example.com',
            ip_address='192.168.1.1',
            failed_attempts=5
        )
        
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        
        self.assertIn('ACCOUNT_LOCKOUT', call_args[1]['subject'])
        self.assertIn('HIGH', call_args[1]['subject'])
    
    @patch('apps.authentication.security_monitor.send_mail')
    def test_send_brute_force_alert(self, mock_send_mail):
        """Test brute force attack alert."""
        self.service.send_brute_force_alert(
            ip_address='192.168.1.1',
            attempts=15,
            time_window='1 hour'
        )
        
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        
        self.assertIn('BRUTE_FORCE_ATTACK', call_args[1]['subject'])
        self.assertIn('CRITICAL', call_args[1]['subject'])
    
    @override_settings(SECURITY_NOTIFICATIONS_ENABLED=False)
    @patch('apps.authentication.security_monitor.send_mail')
    def test_notifications_disabled(self, mock_send_mail):
        """Test that notifications are not sent when disabled."""
        service = SecurityNotificationService()
        service.send_security_alert(
            alert_type='TEST_ALERT',
            details={'test': 'data'}
        )
        
        mock_send_mail.assert_not_called()
    
    @patch('apps.authentication.security_monitor.send_mail')
    @patch('apps.authentication.security_monitor.logger')
    def test_email_sending_failure(self, mock_logger, mock_send_mail):
        """Test handling of email sending failures."""
        mock_send_mail.side_effect = Exception('SMTP Error')
        
        self.service.send_security_alert(
            alert_type='TEST_ALERT',
            details={'test': 'data'}
        )
        
        # Check that error was logged
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn('Failed to send security alert', call_args)


class SecurityIntegrationTest(TestCase):
    """Test integration of all security monitoring components."""
    
    def setUp(self):
        self.monitor = SecurityMonitor()
        self.logger = SecurityEventLogger()
        self.notification_service = SecurityNotificationService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cache.clear()
    
    @patch('apps.authentication.security_monitor.send_mail')
    def test_complete_security_workflow(self, mock_send_mail):
        """Test complete security monitoring workflow."""
        # Simulate multiple failed login attempts
        for i in range(6):
            self.logger.log_login_attempt(
                email='test@example.com',
                ip_address='192.168.1.100',
                user_agent='Test Agent',
                success=False,
                failure_reason='Invalid password'
            )
        
        # Check that events were logged and cached
        # (This would normally trigger middleware to lock account)
        
        # Simulate account lockout
        self.user.lock_account()
        
        # Log the lockout event
        self.logger.log_account_lockout(
            email='test@example.com',
            ip_address='192.168.1.100',
            failed_attempts=5
        )
        
        # Verify security summary includes the incident
        summary = self.monitor.get_security_summary()
        self.assertEqual(summary['current_status']['locked_accounts_count'], 1)
        
        # Verify notification was sent
        mock_send_mail.assert_called()
    
    def test_ip_reputation_tracking(self):
        """Test IP reputation tracking across multiple services."""
        ip_address = '192.168.1.100'
        
        # Create failed attempts across different services
        PasswordResetAttempt.objects.create(
            ip_address=ip_address,
            email='test1@example.com',
            success=False,
            user_agent='Test Agent'
        )
        
        EmailVerificationAttempt.objects.create(
            ip_address=ip_address,
            email='test2@example.com',
            success=False,
            user_agent='Test Agent'
        )
        
        # Check reputation
        reputation = self.monitor.check_ip_reputation(ip_address)
        
        self.assertEqual(reputation['recent_failures'], 2)
        self.assertEqual(reputation['password_reset_failures'], 1)
        self.assertEqual(reputation['email_verification_failures'], 1)
        self.assertEqual(reputation['risk_level'], 'LOW')
        
        # Add more failures to increase risk
        for i in range(8):
            PasswordResetAttempt.objects.create(
                ip_address=ip_address,
                email=f'test{i+3}@example.com',
                success=False,
                user_agent='Test Agent'
            )
        
        # Check updated reputation
        reputation = self.monitor.check_ip_reputation(ip_address)
        self.assertEqual(reputation['recent_failures'], 10)
        self.assertEqual(reputation['risk_level'], 'MEDIUM')