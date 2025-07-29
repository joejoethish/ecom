"""
Tests for authentication tasks.
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from datetime import timedelta
from apps.authentication.models import PasswordResetToken, PasswordResetAttempt
from apps.authentication.tasks import (
    cleanup_expired_password_reset_tokens,
    cleanup_old_password_reset_attempts,
    monitor_password_reset_token_performance,
    send_password_reset_security_alert
)

User = get_user_model()


class PasswordResetTasksTestCase(TestCase):
    """Test password reset cleanup and monitoring tasks."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )

    def test_cleanup_expired_password_reset_tokens(self):
        """Test cleanup of expired password reset tokens."""
        now = timezone.now()
        
        # Create test tokens
        # Expired token
        expired_token = PasswordResetToken.objects.create(
            user=self.user,
            token_hash='expired_hash',
            expires_at=now - timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        # Old token (>24h)
        old_token = PasswordResetToken.objects.create(
            user=self.user,
            token_hash='old_hash',
            expires_at=now + timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        old_token.created_at = now - timedelta(hours=25)
        old_token.save()
        
        # Used token (>1h old)
        used_token = PasswordResetToken.objects.create(
            user=self.user,
            token_hash='used_hash',
            expires_at=now + timedelta(hours=1),
            is_used=True,
            ip_address='192.168.1.1'
        )
        used_token.created_at = now - timedelta(hours=2)
        used_token.save()
        
        # Valid active token (should not be deleted)
        active_token = PasswordResetToken.objects.create(
            user=self.user,
            token_hash='active_hash',
            expires_at=now + timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        # Run cleanup task
        result = cleanup_expired_password_reset_tokens()
        
        # Verify results
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['total_deleted'], 3)
        
        # Verify tokens were deleted correctly
        self.assertFalse(PasswordResetToken.objects.filter(id=expired_token.id).exists())
        self.assertFalse(PasswordResetToken.objects.filter(id=old_token.id).exists())
        self.assertFalse(PasswordResetToken.objects.filter(id=used_token.id).exists())
        self.assertTrue(PasswordResetToken.objects.filter(id=active_token.id).exists())

    def test_cleanup_old_password_reset_attempts(self):
        """Test cleanup of old password reset attempts."""
        now = timezone.now()
        
        # Create test attempts
        # Old attempt (should be deleted)
        old_attempt = PasswordResetAttempt.objects.create(
            ip_address='192.168.1.1',
            email='test@example.com',
            success=True
        )
        old_attempt.created_at = now - timedelta(days=8)
        old_attempt.save()
        
        # Recent attempt (should be kept)
        recent_attempt = PasswordResetAttempt.objects.create(
            ip_address='192.168.1.2',
            email='test@example.com',
            success=False
        )
        
        # Run cleanup task
        result = cleanup_old_password_reset_attempts(days_old=7)
        
        # Verify results
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['deleted_count'], 1)
        
        # Verify attempts were handled correctly
        self.assertFalse(PasswordResetAttempt.objects.filter(id=old_attempt.id).exists())
        self.assertTrue(PasswordResetAttempt.objects.filter(id=recent_attempt.id).exists())

    def test_monitor_password_reset_token_performance(self):
        """Test password reset token performance monitoring."""
        now = timezone.now()
        
        # Create test data
        # Active token
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='active_hash',
            expires_at=now + timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        # Expired token
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='expired_hash',
            expires_at=now - timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        # Used token
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='used_hash',
            expires_at=now + timedelta(hours=1),
            is_used=True,
            ip_address='192.168.1.1'
        )
        
        # Reset attempts
        PasswordResetAttempt.objects.create(
            ip_address='192.168.1.1',
            email='test@example.com',
            success=True
        )
        PasswordResetAttempt.objects.create(
            ip_address='192.168.1.2',
            email='test@example.com',
            success=False
        )
        
        # Run monitoring task
        result = monitor_password_reset_token_performance()
        
        # Verify results
        self.assertEqual(result['status'], 'success')
        self.assertIn('token_statistics', result)
        self.assertIn('attempt_statistics', result)
        self.assertIn('health_indicators', result)
        
        # Check token statistics
        token_stats = result['token_statistics']
        self.assertEqual(token_stats['total_tokens'], 3)
        self.assertEqual(token_stats['active_tokens'], 1)
        self.assertEqual(token_stats['expired_tokens'], 1)
        self.assertEqual(token_stats['used_tokens'], 1)
        
        # Check attempt statistics
        attempt_stats = result['attempt_statistics']
        self.assertEqual(attempt_stats['total_attempts'], 2)
        self.assertEqual(attempt_stats['successful_attempts_7d'], 1)
        self.assertEqual(attempt_stats['success_rate_7d'], 50.0)

    @patch('apps.authentication.tasks.send_email_task')
    def test_send_password_reset_security_alert(self, mock_send_email):
        """Test sending password reset security alerts."""
        mock_send_email.delay = MagicMock()
        
        alert_details = {
            'ip_address': '192.168.1.1',
            'attempt_count': 10,
            'time_window': '1 hour'
        }
        
        # Run security alert task
        result = send_password_reset_security_alert(
            alert_type='RATE_LIMIT_EXCEEDED',
            details=alert_details
        )
        
        # Verify results
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['alert_type'], 'RATE_LIMIT_EXCEEDED')
        self.assertEqual(result['recipients_count'], 1)
        
        # Verify email was sent
        mock_send_email.delay.assert_called_once()
        call_args = mock_send_email.delay.call_args
        self.assertIn('Security Alert', call_args[1]['subject'])
        self.assertEqual(call_args[1]['recipient_list'], ['admin@example.com'])

    @patch('apps.authentication.tasks.send_email_task')
    def test_send_security_alert_no_admins(self, mock_send_email):
        """Test security alert when no admin users exist."""
        # Remove admin user
        self.admin_user.delete()
        
        # Run security alert task
        result = send_password_reset_security_alert(
            alert_type='TEST_ALERT',
            details={}
        )
        
        # Verify no email was sent
        self.assertEqual(result['status'], 'no_recipients')
        mock_send_email.delay.assert_not_called()

    def test_cleanup_tasks_with_no_data(self):
        """Test cleanup tasks when no data exists."""
        # Run cleanup tasks on empty database
        token_result = cleanup_expired_password_reset_tokens()
        attempt_result = cleanup_old_password_reset_attempts()
        
        # Verify results
        self.assertEqual(token_result['status'], 'success')
        self.assertEqual(token_result['total_deleted'], 0)
        
        self.assertEqual(attempt_result['status'], 'success')
        self.assertEqual(attempt_result['deleted_count'], 0)

    def test_monitoring_with_no_data(self):
        """Test monitoring task when no data exists."""
        # Run monitoring task on empty database
        result = monitor_password_reset_token_performance()
        
        # Verify results
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['token_statistics']['total_tokens'], 0)
        self.assertEqual(result['attempt_statistics']['total_attempts'], 0)
        self.assertEqual(result['attempt_statistics']['success_rate_7d'], 0)

    def test_cleanup_with_transaction_rollback(self):
        """Test that cleanup operations are atomic."""
        # Create test token
        token = PasswordResetToken.objects.create(
            user=self.user,
            token_hash='test_hash',
            expires_at=timezone.now() - timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        # Mock a database error during cleanup
        with patch('apps.authentication.models.PasswordResetToken.objects.filter') as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.delete.side_effect = Exception('Database error')
            mock_filter.return_value = mock_queryset
            
            # Run cleanup task (should handle the exception)
            with self.assertRaises(Exception):
                cleanup_expired_password_reset_tokens()
        
        # Verify token still exists (transaction rolled back)
        self.assertTrue(PasswordResetToken.objects.filter(id=token.id).exists())