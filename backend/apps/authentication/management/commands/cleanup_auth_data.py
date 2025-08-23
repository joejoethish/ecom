"""
Management command to clean up expired authentication data.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.authentication.models import (
    PasswordReset, EmailVerification, PasswordResetAttempt, 
    EmailVerificationAttempt, UserSession
)


class Command(BaseCommand):
    help = 'Clean up expired authentication data including tokens, attempts, and sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to keep attempt records (default: 7)'
        )
        parser.add_argument(
            '--session-days',
            type=int,
            default=30,
            help='Number of days to keep inactive session records (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        session_days = options['session_days']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting authentication data cleanup (dry_run={dry_run})')
        )
        
        # Clean up expired password reset tokens
        expired_password_resets = PasswordReset.objects.filter(
            expires_at__lt=timezone.now()
        )
        password_reset_count = expired_password_resets.count()
        
        if not dry_run:
            expired_password_resets.delete()
        
        self.stdout.write(
            f'Password reset tokens: {password_reset_count} expired tokens {"would be" if dry_run else ""} deleted'
        )
        
        # Clean up used password reset tokens
        used_password_resets = PasswordReset.objects.filter(is_used=True)
        used_password_reset_count = used_password_resets.count()
        
        if not dry_run:
            used_password_resets.delete()
        
        self.stdout.write(
            f'Password reset tokens: {used_password_reset_count} used tokens {"would be" if dry_run else ""} deleted'
        )
        
        # Clean up expired email verification tokens
        expired_email_verifications = EmailVerification.objects.filter(
            expires_at__lt=timezone.now()
        )
        email_verification_count = expired_email_verifications.count()
        
        if not dry_run:
            expired_email_verifications.delete()
        
        self.stdout.write(
            f'Email verification tokens: {email_verification_count} expired tokens {"would be" if dry_run else ""} deleted'
        )
        
        # Clean up used email verification tokens
        used_email_verifications = EmailVerification.objects.filter(is_used=True)
        used_email_verification_count = used_email_verifications.count()
        
        if not dry_run:
            used_email_verifications.delete()
        
        self.stdout.write(
            f'Email verification tokens: {used_email_verification_count} used tokens {"would be" if dry_run else ""} deleted'
        )
        
        # Clean up old password reset attempts
        cutoff_date = timezone.now() - timedelta(days=days)
        old_password_attempts = PasswordResetAttempt.objects.filter(
            created_at__lt=cutoff_date
        )
        password_attempt_count = old_password_attempts.count()
        
        if not dry_run:
            old_password_attempts.delete()
        
        self.stdout.write(
            f'Password reset attempts: {password_attempt_count} old attempts {"would be" if dry_run else ""} deleted'
        )
        
        # Clean up old email verification attempts
        old_email_attempts = EmailVerificationAttempt.objects.filter(
            created_at__lt=cutoff_date
        )
        email_attempt_count = old_email_attempts.count()
        
        if not dry_run:
            old_email_attempts.delete()
        
        self.stdout.write(
            f'Email verification attempts: {email_attempt_count} old attempts {"would be" if dry_run else ""} deleted'
        )
        
        # Clean up old inactive sessions
        session_cutoff_date = timezone.now() - timedelta(days=session_days)
        old_sessions = UserSession.objects.filter(
            last_activity__lt=session_cutoff_date,
            is_active=False
        )
        session_count = old_sessions.count()
        
        if not dry_run:
            old_sessions.delete()
        
        self.stdout.write(
            f'User sessions: {session_count} old inactive sessions {"would be" if dry_run else ""} deleted'
        )
        
        # Summary
        total_cleaned = (
            password_reset_count + used_password_reset_count + 
            email_verification_count + used_email_verification_count +
            password_attempt_count + email_attempt_count + session_count
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleanup completed: {total_cleaned} total records {"would be" if dry_run else ""} cleaned up'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run. No data was actually deleted.')
            )