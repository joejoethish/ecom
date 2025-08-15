"""
Management command to mark migration as applied.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Mark enhanced authentication migration as applied'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES ('authentication', '0002_enhanced_authentication_models', NOW())
                """)
                self.stdout.write(self.style.SUCCESS('Marked migration 0002_enhanced_authentication_models as applied'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Migration may already be marked as applied: {e}'))