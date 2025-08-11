from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()
from apps.system_settings.services import SettingsBackupService
from apps.system_settings.models import SettingBackup


class Command(BaseCommand):
    help = 'Restore system settings from a backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-id',
            type=int,
            required=True,
            help='ID of the backup to restore'
        )
        parser.add_argument(
            '--conflict-resolution',
            type=str,
            choices=['skip', 'overwrite', 'version'],
            default='skip',
            help='How to handle conflicts (default: skip)'
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username to attribute the restore to (default: admin)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without making changes'
        )

    def handle(self, *args, **options):
        try:
            # Get user
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            raise CommandError(f"User '{options['user']}' does not exist")

        try:
            # Get backup
            backup = SettingBackup.objects.get(id=options['backup_id'])
        except SettingBackup.DoesNotExist:
            raise CommandError(f"Backup with ID {options['backup_id']} does not exist")

        if options['dry_run']:
            settings_data = backup.backup_data.get('settings', [])
            self.stdout.write(f"Backup: {backup.name}")
            self.stdout.write(f"Created: {backup.created_at}")
            self.stdout.write(f"Environment: {backup.environment}")
            self.stdout.write(f"Settings count: {len(settings_data)}")
            self.stdout.write("\nSettings that would be restored:")
            
            for setting_data in settings_data[:10]:  # Show first 10
                self.stdout.write(f"  - {setting_data['key']}: {setting_data['value'][:50]}...")
            
            if len(settings_data) > 10:
                self.stdout.write(f"  ... and {len(settings_data) - 10} more settings")
            
            return

        try:
            results = SettingsBackupService.restore_backup(
                backup,
                user,
                conflict_resolution=options['conflict_resolution']
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Restore completed:\n"
                    f"  - Restored: {results['restored']}\n"
                    f"  - Skipped: {results['skipped']}\n"
                    f"  - Errors: {len(results['errors'])}"
                )
            )

            if results['errors']:
                self.stdout.write(self.style.WARNING("Errors encountered:"))
                for error in results['errors']:
                    self.stdout.write(f"  - {error}")

        except Exception as e:
            raise CommandError(f"Failed to restore backup: {str(e)}")