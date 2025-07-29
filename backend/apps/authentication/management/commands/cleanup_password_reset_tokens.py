"""
Management command to manually clean up password reset tokens.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from apps.authentication.models import PasswordResetToken, PasswordResetAttempt


class Command(BaseCommand):
    help = 'Clean up expired password reset tokens and old reset attempts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--tokens-only',
            action='store_true',
            help='Only clean up tokens, not attempts',
        )
        parser.add_argument(
            '--attempts-only',
            action='store_true',
            help='Only clean up attempts, not tokens',
        )
        parser.add_argument(
            '--attempts-days',
            type=int,
            default=7,
            help='Number of days to keep reset attempts (default: 7)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation prompt',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        tokens_only = options['tokens_only']
        attempts_only = options['attempts_only']
        attempts_days = options['attempts_days']
        force = options['force']

        if tokens_only and attempts_only:
            raise CommandError("Cannot specify both --tokens-only and --attempts-only")

        self.stdout.write(
            self.style.SUCCESS('Password Reset Token Cleanup')
        )
        self.stdout.write('=' * 50)

        # Calculate cutoff times
        now = timezone.now()
        expired_cutoff = now
        old_cutoff = now - timedelta(hours=24)
        used_cutoff = now - timedelta(hours=1)
        attempts_cutoff = now - timedelta(days=attempts_days)

        total_deleted = 0
        
        # Clean up tokens
        if not attempts_only:
            self.stdout.write('\nAnalyzing password reset tokens...')
            
            # Count tokens to be deleted
            expired_count = PasswordResetToken.objects.filter(
                expires_at__lt=expired_cutoff
            ).count()
            
            old_count = PasswordResetToken.objects.filter(
                created_at__lt=old_cutoff
            ).count()
            
            used_count = PasswordResetToken.objects.filter(
                is_used=True,
                created_at__lt=used_cutoff
            ).count()
            
            total_tokens_to_delete = expired_count + old_count + used_count
            total_tokens = PasswordResetToken.objects.count()
            
            self.stdout.write(f'  Total tokens: {total_tokens}')
            self.stdout.write(f'  Expired tokens: {expired_count}')
            self.stdout.write(f'  Old tokens (>24h): {old_count}')
            self.stdout.write(f'  Used tokens (>1h): {used_count}')
            self.stdout.write(f'  Total to delete: {total_tokens_to_delete}')
            
            if total_tokens_to_delete > 0:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(f'DRY RUN: Would delete {total_tokens_to_delete} tokens')
                    )
                else:
                    if not force:
                        confirm = input(f'Delete {total_tokens_to_delete} tokens? [y/N]: ')
                        if confirm.lower() != 'y':
                            self.stdout.write('Token cleanup cancelled.')
                            return
                    
                    with transaction.atomic():
                        # Delete expired tokens
                        expired_deleted, _ = PasswordResetToken.objects.filter(
                            expires_at__lt=expired_cutoff
                        ).delete()
                        
                        # Delete old tokens
                        old_deleted, _ = PasswordResetToken.objects.filter(
                            created_at__lt=old_cutoff
                        ).delete()
                        
                        # Delete used tokens
                        used_deleted, _ = PasswordResetToken.objects.filter(
                            is_used=True,
                            created_at__lt=used_cutoff
                        ).delete()
                        
                        tokens_deleted = expired_deleted + old_deleted + used_deleted
                        total_deleted += tokens_deleted
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully deleted {tokens_deleted} tokens')
                    )
            else:
                self.stdout.write('No tokens to delete.')

        # Clean up attempts
        if not tokens_only:
            self.stdout.write('\nAnalyzing password reset attempts...')
            
            old_attempts_count = PasswordResetAttempt.objects.filter(
                created_at__lt=attempts_cutoff
            ).count()
            
            total_attempts = PasswordResetAttempt.objects.count()
            
            self.stdout.write(f'  Total attempts: {total_attempts}')
            self.stdout.write(f'  Old attempts (>{attempts_days}d): {old_attempts_count}')
            
            if old_attempts_count > 0:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(f'DRY RUN: Would delete {old_attempts_count} attempts')
                    )
                else:
                    if not force:
                        confirm = input(f'Delete {old_attempts_count} attempts? [y/N]: ')
                        if confirm.lower() != 'y':
                            self.stdout.write('Attempts cleanup cancelled.')
                            return
                    
                    with transaction.atomic():
                        attempts_deleted, _ = PasswordResetAttempt.objects.filter(
                            created_at__lt=attempts_cutoff
                        ).delete()
                        
                        total_deleted += attempts_deleted
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully deleted {attempts_deleted} attempts')
                    )
            else:
                self.stdout.write('No attempts to delete.')

        # Summary
        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN COMPLETED - No data was actually deleted')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Cleanup completed. Total items deleted: {total_deleted}')
            )