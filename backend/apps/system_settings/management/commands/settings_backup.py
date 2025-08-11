from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()
from apps.system_settings.services import SettingsBackupService
from apps.system_settings.models import SettingCategory


class Command(BaseCommand):
    help = 'Create a backup of system settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Name for the backup'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Description for the backup'
        )
        parser.add_argument(
            '--environment',
            type=str,
            default='production',
            help='Environment to backup (default: production)'
        )
        parser.add_argument(
            '--categories',
            type=str,
            nargs='*',
            help='Category names to backup (backup all if not specified)'
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username to attribute the backup to (default: admin)'
        )

    def handle(self, *args, **options):
        try:
            # Get user
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            raise CommandError(f"User '{options['user']}' does not exist")

        # Get category IDs if specified
        category_ids = None
        if options['categories']:
            categories = SettingCategory.objects.filter(
                name__in=options['categories']
            )
            if not categories.exists():
                raise CommandError("No matching categories found")
            category_ids = list(categories.values_list('id', flat=True))

        try:
            backup = SettingsBackupService.create_backup(
                name=options['name'],
                description=options['description'],
                user=user,
                category_ids=category_ids,
                environment=options['environment']
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created backup '{backup.name}' "
                    f"with {len(backup.backup_data.get('settings', []))} settings"
                )
            )

        except Exception as e:
            raise CommandError(f"Failed to create backup: {str(e)}")