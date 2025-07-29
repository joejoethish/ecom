"""
Management command to manually invalidate password reset tokens.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from apps.authentication.models import PasswordResetToken, User


class Command(BaseCommand):
    help = 'Manually invalidate password reset tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Invalidate tokens for specific user email',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Invalidate tokens for specific user ID',
        )
        parser.add_argument(
            '--all-active',
            action='store_true',
            help='Invalidate all active tokens (use with caution)',
        )
        parser.add_argument(
            '--token-hash',
            type=str,
            help='Invalidate specific token by hash',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be invalidated without actually doing it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force invalidation without confirmation prompt',
        )

    def handle(self, *args, **options):
        user_email = options['user_email']
        user_id = options['user_id']
        all_active = options['all_active']
        token_hash = options['token_hash']
        dry_run = options['dry_run']
        force = options['force']

        # Validate arguments
        option_count = sum([bool(user_email), bool(user_id), bool(all_active), bool(token_hash)])
        if option_count != 1:
            raise CommandError(
                "Specify exactly one of: --user-email, --user-id, --all-active, or --token-hash"
            )

        self.stdout.write(
            self.style.SUCCESS('Password Reset Token Invalidation')
        )
        self.stdout.write('=' * 50)

        tokens_to_invalidate = None

        # Build query based on options
        if user_email:
            try:
                user = User.objects.get(email=user_email)
                tokens_to_invalidate = PasswordResetToken.objects.filter(
                    user=user,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                self.stdout.write(f'Target: All active tokens for user {user_email}')
            except User.DoesNotExist:
                raise CommandError(f"User with email '{user_email}' not found")

        elif user_id:
            try:
                user = User.objects.get(id=user_id)
                tokens_to_invalidate = PasswordResetToken.objects.filter(
                    user=user,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                self.stdout.write(f'Target: All active tokens for user ID {user_id} ({user.email})')
            except User.DoesNotExist:
                raise CommandError(f"User with ID '{user_id}' not found")

        elif token_hash:
            tokens_to_invalidate = PasswordResetToken.objects.filter(
                token_hash=token_hash,
                is_used=False
            )
            self.stdout.write(f'Target: Specific token with hash {token_hash[:16]}...')

        elif all_active:
            tokens_to_invalidate = PasswordResetToken.objects.filter(
                is_used=False,
                expires_at__gt=timezone.now()
            )
            self.stdout.write('Target: ALL active tokens in the system')
            self.stdout.write(
                self.style.WARNING('⚠ This will invalidate ALL active password reset tokens!')
            )

        # Check if tokens exist
        if not tokens_to_invalidate.exists():
            self.stdout.write(
                self.style.WARNING('No matching tokens found to invalidate.')
            )
            return

        token_count = tokens_to_invalidate.count()
        
        # Show token details
        self.stdout.write(f'\nTokens to invalidate: {token_count}')
        
        if token_count <= 10:  # Show details for small numbers
            for token in tokens_to_invalidate:
                created = token.created_at.strftime('%Y-%m-%d %H:%M:%S')
                expires = token.expires_at.strftime('%Y-%m-%d %H:%M:%S')
                self.stdout.write(
                    f'  • User: {token.user.email}, Created: {created}, Expires: {expires}'
                )
        else:
            # Show summary for large numbers
            users_affected = tokens_to_invalidate.values('user__email').distinct().count()
            self.stdout.write(f'  • Affects {users_affected} unique users')

        # Confirm action
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\nDRY RUN: Would invalidate {token_count} tokens')
            )
            return

        if not force:
            if all_active:
                confirm_text = 'INVALIDATE ALL'
                prompt = f'Type "{confirm_text}" to confirm invalidating ALL active tokens: '
            else:
                confirm_text = 'yes'
                prompt = f'Invalidate {token_count} tokens? Type "yes" to confirm: '
            
            confirmation = input(prompt)
            if confirmation != confirm_text:
                self.stdout.write('Invalidation cancelled.')
                return

        # Perform invalidation
        try:
            with transaction.atomic():
                updated_count = tokens_to_invalidate.update(
                    is_used=True,
                    updated_at=timezone.now()
                )
                
                # Log the invalidation
                self.stdout.write(
                    self.style.SUCCESS(f'\nSuccessfully invalidated {updated_count} tokens')
                )
                
                # Show affected users
                if updated_count > 0:
                    affected_users = tokens_to_invalidate.values_list('user__email', flat=True).distinct()
                    self.stdout.write('\nAffected users:')
                    for email in affected_users:
                        self.stdout.write(f'  • {email}')

        except Exception as e:
            raise CommandError(f'Failed to invalidate tokens: {str(e)}')

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS('Token invalidation completed successfully')
        )
        
        # Provide next steps
        self.stdout.write('\nNext steps:')
        self.stdout.write('• Affected users will need to request new password reset tokens')
        self.stdout.write('• Consider notifying users if this was done for security reasons')
        self.stdout.write('• Monitor logs for any related security events')