"""
Tests for authentication management commands.
"""
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from io import StringIO
from datetime import timedelta
from apps.authentication.models import PasswordResetToken, PasswordResetAttempt

User = get_user_model()


class ManagementCommandsTestCase(TestCase):
    """Test authentication management commands."""

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

    def test_cleanup_password_reset_tokens_dry_run(self):
        """Test cleanup command with dry run option."""
        now = timezone.now()
        
        # Create expired token
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='expired_hash',
            expires_at=now - timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        # Create old attempt
        old_attempt = PasswordResetAttempt.objects.create(
            ip_address='192.168.1.1',
            email='test@example.com',
            success=True
        )
        old_attempt.created_at = now - timedelta(days=8)
        old_attempt.save()
        
        out = StringIO()
        call_command('cleanup_password_reset_tokens', '--dry-run', stdout=out)
        
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
        self.assertIn('Would delete', output)
        
        # Verify nothing was actually deleted
        self.assertEqual(PasswordResetToken.objects.count(), 1)
        self.assertEqual(PasswordResetAttempt.objects.count(), 1)

    def test_cleanup_password_reset_tokens_force(self):
        """Test cleanup command with force option."""
        now = timezone.now()
        
        # Create expired token
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='expired_hash',
            expires_at=now - timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        # Create old attempt
        old_attempt = PasswordResetAttempt.objects.create(
            ip_address='192.168.1.1',
            email='test@example.com',
            success=True
        )
        old_attempt.created_at = now - timedelta(days=8)
        old_attempt.save()
        
        out = StringIO()
        call_command('cleanup_password_reset_tokens', '--force', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Successfully deleted', output)
        
        # Verify data was deleted
        self.assertEqual(PasswordResetToken.objects.count(), 0)
        self.assertEqual(PasswordResetAttempt.objects.count(), 0)

    def test_cleanup_tokens_only(self):
        """Test cleanup command with tokens-only option."""
        now = timezone.now()
        
        # Create expired token
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='expired_hash',
            expires_at=now - timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        # Create old attempt
        old_attempt = PasswordResetAttempt.objects.create(
            ip_address='192.168.1.1',
            email='test@example.com',
            success=True
        )
        old_attempt.created_at = now - timedelta(days=8)
        old_attempt.save()
        
        out = StringIO()
        call_command('cleanup_password_reset_tokens', '--tokens-only', '--force', stdout=out)
        
        # Verify only tokens were deleted
        self.assertEqual(PasswordResetToken.objects.count(), 0)
        self.assertEqual(PasswordResetAttempt.objects.count(), 1)

    def test_cleanup_attempts_only(self):
        """Test cleanup command with attempts-only option."""
        now = timezone.now()
        
        # Create expired token
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='expired_hash',
            expires_at=now - timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        # Create old attempt
        old_attempt = PasswordResetAttempt.objects.create(
            ip_address='192.168.1.1',
            email='test@example.com',
            success=True
        )
        old_attempt.created_at = now - timedelta(days=8)
        old_attempt.save()
        
        out = StringIO()
        call_command('cleanup_password_reset_tokens', '--attempts-only', '--force', stdout=out)
        
        # Verify only attempts were deleted
        self.assertEqual(PasswordResetToken.objects.count(), 1)
        self.assertEqual(PasswordResetAttempt.objects.count(), 0)

    def test_password_reset_stats_command(self):
        """Test password reset stats command."""
        now = timezone.now()
        
        # Create test data
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='active_hash',
            expires_at=now + timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='expired_hash',
            expires_at=now - timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        PasswordResetAttempt.objects.create(
            ip_address='192.168.1.1',
            email='test@example.com',
            success=True
        )
        
        out = StringIO()
        call_command('password_reset_stats', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Password Reset System Statistics', output)
        self.assertIn('Token Statistics', output)
        self.assertIn('Attempt Statistics', output)
        self.assertIn('Usage Patterns', output)
        self.assertIn('System Health Indicators', output)

    def test_password_reset_stats_detailed(self):
        """Test password reset stats command with detailed option."""
        # Create test data
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='test_hash',
            expires_at=timezone.now() + timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        out = StringIO()
        call_command('password_reset_stats', '--detailed', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Hourly token creation', output)

    def test_invalidate_password_reset_tokens_by_email(self):
        """Test invalidating tokens by user email."""
        now = timezone.now()
        
        # Create active token
        token = PasswordResetToken.objects.create(
            user=self.user,
            token_hash='active_hash',
            expires_at=now + timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        out = StringIO()
        call_command(
            'invalidate_password_reset_tokens',
            '--user-email', 'test@example.com',
            '--force',
            stdout=out
        )
        
        output = out.getvalue()
        self.assertIn('Successfully invalidated', output)
        
        # Verify token was invalidated
        token.refresh_from_db()
        self.assertTrue(token.is_used)

    def test_invalidate_password_reset_tokens_by_user_id(self):
        """Test invalidating tokens by user ID."""
        now = timezone.now()
        
        # Create active token
        token = PasswordResetToken.objects.create(
            user=self.user,
            token_hash='active_hash',
            expires_at=now + timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        out = StringIO()
        call_command(
            'invalidate_password_reset_tokens',
            '--user-id', str(self.user.id),
            '--force',
            stdout=out
        )
        
        # Verify token was invalidated
        token.refresh_from_db()
        self.assertTrue(token.is_used)

    def test_invalidate_password_reset_tokens_by_hash(self):
        """Test invalidating specific token by hash."""
        now = timezone.now()
        
        # Create active token
        token = PasswordResetToken.objects.create(
            user=self.user,
            token_hash='specific_hash',
            expires_at=now + timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        out = StringIO()
        call_command(
            'invalidate_password_reset_tokens',
            '--token-hash', 'specific_hash',
            '--force',
            stdout=out
        )
        
        # Verify token was invalidated
        token.refresh_from_db()
        self.assertTrue(token.is_used)

    def test_invalidate_all_active_tokens_dry_run(self):
        """Test invalidating all active tokens with dry run."""
        now = timezone.now()
        
        # Create multiple active tokens
        for i in range(3):
            PasswordResetToken.objects.create(
                user=self.user,
                token_hash=f'hash_{i}',
                expires_at=now + timedelta(hours=1),
                ip_address='192.168.1.1'
            )
        
        out = StringIO()
        call_command(
            'invalidate_password_reset_tokens',
            '--all-active',
            '--dry-run',
            stdout=out
        )
        
        output = out.getvalue()
        self.assertIn('DRY RUN', output)
        self.assertIn('Would invalidate 3 tokens', output)
        
        # Verify no tokens were actually invalidated
        active_count = PasswordResetToken.objects.filter(is_used=False).count()
        self.assertEqual(active_count, 3)

    def test_invalidate_nonexistent_user_email(self):
        """Test invalidating tokens for nonexistent user email."""
        out = StringIO()
        err = StringIO()
        
        with self.assertRaises(SystemExit):
            call_command(
                'invalidate_password_reset_tokens',
                '--user-email', 'nonexistent@example.com',
                '--force',
                stdout=out,
                stderr=err
            )
        
        error_output = err.getvalue()
        self.assertIn('not found', error_output)

    def test_invalidate_no_matching_tokens(self):
        """Test invalidating when no matching tokens exist."""
        out = StringIO()
        call_command(
            'invalidate_password_reset_tokens',
            '--user-email', 'test@example.com',
            '--force',
            stdout=out
        )
        
        output = out.getvalue()
        self.assertIn('No matching tokens found', output)

    def test_stats_export_csv(self):
        """Test exporting stats to CSV file."""
        import tempfile
        import os
        
        # Create test data
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash='test_hash',
            expires_at=timezone.now() + timedelta(hours=1),
            ip_address='192.168.1.1'
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            csv_file = f.name
        
        try:
            out = StringIO()
            call_command(
                'password_reset_stats',
                '--export-csv', csv_file,
                stdout=out
            )
            
            output = out.getvalue()
            self.assertIn('Statistics exported', output)
            
            # Verify CSV file was created and has content
            self.assertTrue(os.path.exists(csv_file))
            with open(csv_file, 'r') as f:
                content = f.read()
                self.assertIn('Date,Tokens Created', content)
        
        finally:
            # Clean up
            if os.path.exists(csv_file):
                os.unlink(csv_file)

    def test_cleanup_command_conflicting_options(self):
        """Test cleanup command with conflicting options."""
        out = StringIO()
        err = StringIO()
        
        with self.assertRaises(SystemExit):
            call_command(
                'cleanup_password_reset_tokens',
                '--tokens-only',
                '--attempts-only',
                stdout=out,
                stderr=err
            )
        
        error_output = err.getvalue()
        self.assertIn('Cannot specify both', error_output)

    def test_invalidate_command_no_options(self):
        """Test invalidate command without required options."""
        out = StringIO()
        err = StringIO()
        
        with self.assertRaises(SystemExit):
            call_command(
                'invalidate_password_reset_tokens',
                stdout=out,
                stderr=err
            )
        
        error_output = err.getvalue()
        self.assertIn('Specify exactly one', error_output)