"""
Django management command to set up MySQL database
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model
from core.database import DatabaseHealthChecker
import sys

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up MySQL database with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-sample-data',
            action='store_true',
            help='Skip populating sample data',
        )
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip creating superuser',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Setting up MySQL database for ecommerce platform...')
        )
        self.stdout.write('=' * 60)

        # Step 1: Check database connection
        if not self.check_database_connection():
            return

        # Step 2: Run migrations
        if not self.run_migrations():
            return

        # Step 3: Create superuser
        if not options['skip_superuser']:
            if not self.create_superuser():
                return

        # Step 4: Populate sample data
        if not options['skip_sample_data']:
            if not self.populate_sample_data():
                return

        # Step 5: Display summary
        self.display_summary()

    def check_database_connection(self):
        """Check if database connection is working"""
        self.stdout.write('📡 Checking database connection...')
        
        try:
            health_info = DatabaseHealthChecker.check_connection()
            
            if health_info['status'] == 'healthy':
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Database connection successful")
                )
                self.stdout.write(f"  - Database: {health_info.get('database')}")
                self.stdout.write(f"  - Host: {health_info.get('host')}:{health_info.get('port')}")
                self.stdout.write(f"  - Engine: {health_info.get('engine')}")
                
                if health_info.get('mysql_version'):
                    self.stdout.write(f"  - MySQL Version: {health_info.get('mysql_version')}")
                
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Database connection failed: {health_info.get('error')}")
                )
                return False
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Database connection check failed: {e}")
            )
            return False

    def run_migrations(self):
        """Run Django migrations"""
        self.stdout.write('🔄 Running Django migrations...')
        
        try:
            # Make migrations first
            call_command('makemigrations', verbosity=0)
            self.stdout.write('  - Created migration files')
            
            # Apply migrations
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Migrations completed successfully'))
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Migration failed: {e}")
            )
            return False

    def create_superuser(self):
        """Create superuser if it doesn't exist"""
        self.stdout.write('👤 Creating superuser...')
        
        try:
            if User.objects.filter(email='admin@example.com').exists():
                self.stdout.write('  - Superuser already exists')
                return True
            
            # Create superuser
            admin_user = User.objects.create_superuser(
                email='admin@example.com',
                username='admin',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            
            self.stdout.write(
                self.style.SUCCESS('✓ Superuser created successfully')
            )
            self.stdout.write('  - Email: admin@example.com')
            self.stdout.write('  - Password: admin123')
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to create superuser: {e}")
            )
            return False

    def populate_sample_data(self):
        """Populate database with sample data"""
        self.stdout.write('📊 Populating sample data...')
        
        try:
            call_command('populate_sample_data', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('✓ Sample data populated successfully')
            )
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to populate sample data: {e}")
            )
            return False

    def display_summary(self):
        """Display setup summary"""
        self.stdout.write('=' * 60)
        self.stdout.write(
            self.style.SUCCESS('🎉 MySQL database setup completed successfully!')
        )
        
        # Get database stats
        try:
            stats = DatabaseHealthChecker.get_database_stats()
            
            self.stdout.write('\n📈 Database Statistics:')
            if 'database_size_mb' in stats:
                self.stdout.write(f'  - Database Size: {stats["database_size_mb"]} MB')
            if 'table_count' in stats:
                self.stdout.write(f'  - Tables: {stats["table_count"]}')
            if 'active_connections' in stats:
                self.stdout.write(f'  - Active Connections: {stats["active_connections"]}')
                
        except Exception as e:
            self.stdout.write(f'  - Could not retrieve stats: {e}')

        self.stdout.write('\n🔗 Connection Details:')
        self.stdout.write(f'  - Host: {connection.settings_dict.get("HOST")}:{connection.settings_dict.get("PORT")}')
        self.stdout.write(f'  - Database: {connection.settings_dict.get("NAME")}')
        self.stdout.write(f'  - Admin User: admin@example.com / admin123')
        
        self.stdout.write('\n🚀 Next Steps:')
        self.stdout.write('  - Start the Django development server: python manage.py runserver')
        self.stdout.write('  - Access admin panel: http://localhost:8000/admin/')
        self.stdout.write('  - Test API endpoints: http://localhost:8000/api/v1/')