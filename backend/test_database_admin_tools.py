#!/usr/bin/env python
"""
Test script for database administration tools.

This script validates the functionality of:
- Database monitoring
- Backup management
- User management
- Health checks
- Performance reporting
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

import logging
from datetime import datetime
from django.conf import settings
from django.db import connection, connections
from django.test import RequestFactory
from django.contrib.auth.models import User

# Import our admin tools
from core.admin.database_admin import DatabaseAdministrationSite, DatabaseMetricsAdmin, BackupAdmin
from core.database_monitor import DatabaseMonitor
from core.backup_manager import MySQLBackupManager, BackupConfig
from core.database_security import DatabaseSecurityManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseAdminToolsTest:
    """Test suite for database administration tools."""
    
    def __init__(self):
        self.factory = RequestFactory()
        self.admin_site = DatabaseAdministrationSite()
        self.results = {
            'monitoring': False,
            'backup': False,
            'security': False,
            'admin_interface': False,
            'health_check': False
        }
    
    def run_all_tests(self):
        """Run all tests and display results."""
        print("="*60)
        print("DATABASE ADMINISTRATION TOOLS TEST SUITE")
        print("="*60)
        print(f"Started at: {datetime.now()}")
        print()
        
        try:
            self.test_database_connections()
            self.test_monitoring_system()
            self.test_backup_system()
            self.test_security_system()
            self.test_admin_interface()
            self.test_health_checks()
            
            self.display_results()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            print(f"❌ Test suite failed: {e}")
    
    def test_database_connections(self):
        """Test database connections."""
        print("Testing database connections...")
        
        for db_alias in settings.DATABASES.keys():
            try:
                conn = connections[db_alias]
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    
                if result and result[0] == 1:
                    print(f"  ✅ {db_alias}: Connection successful")
                else:
                    print(f"  ❌ {db_alias}: Connection test failed")
                    
            except Exception as e:
                print(f"  ❌ {db_alias}: Connection failed - {e}")
        print()
    
    def test_monitoring_system(self):
        """Test database monitoring system."""
        print("Testing database monitoring system...")
        
        try:
            monitor = DatabaseMonitor()
            
            # Test metrics collection
            for db_alias in settings.DATABASES.keys():
                try:
                    metrics = monitor._collect_database_metrics(db_alias)
                    if metrics:
                        print(f"  ✅ Metrics collection working for {db_alias}")
                        print(f"     Status: {metrics.status}")
                        print(f"     Health Score: {metrics.health_score}")
                        self.results['monitoring'] = True
                    else:
                        print(f"  ❌ No metrics collected for {db_alias}")
                        
                except Exception as e:
                    print(f"  ❌ Metrics collection failed for {db_alias}: {e}")
            
            print(f"  ✅ Database monitor initialized successfully")
            
        except Exception as e:
            print(f"  ❌ Monitoring system test failed: {e}")
        print()
    
    def test_backup_system(self):
        """Test backup management system."""
        print("Testing backup management system...")
        
        try:
            backup_config = BackupConfig(
                backup_dir=getattr(settings, 'BACKUP_DIR', '/tmp/test_backups'),
                encryption_key='test-encryption-key-12345',
                retention_days=7
            )
            
            backup_manager = MySQLBackupManager(backup_config)
            
            # Test backup status
            status = backup_manager.get_backup_status()
            if 'error' not in status:
                print(f"  ✅ Backup system initialized")
                print(f"     Backup directory: {backup_config.backup_dir}")
                print(f"     Total backups: {status.get('total_backups', 0)}")
                self.results['backup'] = True
            else:
                print(f"  ❌ Backup system error: {status['error']}")
            
            # Test backup listing
            backups = backup_manager.storage.list_backups()
            print(f"  ✅ Found {len(backups)} existing backups")
            
        except Exception as e:
            print(f"  ❌ Backup system test failed: {e}")
        print()
    
    def test_security_system(self):
        """Test database security system."""
        print("Testing database security system...")
        
        try:
            security_manager = DatabaseSecurityManager()
            
            # Test audit table creation
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'db_audit_log'
                """)
                audit_table_exists = cursor.fetchone()[0] > 0
                
                if audit_table_exists:
                    print(f"  ✅ Audit log table exists")
                else:
                    print(f"  ❌ Audit log table not found")
                
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'db_security_events'
                """)
                security_table_exists = cursor.fetchone()[0] > 0
                
                if security_table_exists:
                    print(f"  ✅ Security events table exists")
                    self.results['security'] = True
                else:
                    print(f"  ❌ Security events table not found")
            
            # Test field encryption
            encrypted_value = security_manager.field_encryption.encrypt_field("test_data")
            decrypted_value = security_manager.field_encryption.decrypt_field(encrypted_value)
            
            if decrypted_value == "test_data":
                print(f"  ✅ Field encryption/decryption working")
            else:
                print(f"  ❌ Field encryption/decryption failed")
            
        except Exception as e:
            print(f"  ❌ Security system test failed: {e}")
        print()
    
    def test_admin_interface(self):
        """Test admin interface functionality."""
        print("Testing admin interface...")
        
        try:
            # Test admin site initialization
            admin_site = DatabaseAdministrationSite()
            print(f"  ✅ Admin site initialized: {admin_site.site_header}")
            
            # Test URL patterns
            urls = admin_site.get_urls()
            print(f"  ✅ Found {len(urls)} admin URLs")
            
            # Test admin views (simulate requests)
            request = self.factory.get('/db-admin/dashboard/')
            request.user = self.get_or_create_test_user()
            
            try:
                context = admin_site._get_dashboard_context()
                if context:
                    print(f"  ✅ Dashboard context generated")
                    self.results['admin_interface'] = True
                else:
                    print(f"  ❌ Dashboard context empty")
            except Exception as e:
                print(f"  ❌ Dashboard context generation failed: {e}")
            
        except Exception as e:
            print(f"  ❌ Admin interface test failed: {e}")
        print()
    
    def test_health_checks(self):
        """Test health check functionality."""
        print("Testing health check system...")
        
        try:
            admin_site = DatabaseAdministrationSite()
            
            # Test health check for each database
            for db_alias in settings.DATABASES.keys():
                try:
                    health_result = admin_site._perform_health_check(db_alias)
                    
                    print(f"  ✅ Health check completed for {db_alias}")
                    print(f"     Status: {health_result['status']}")
                    print(f"     Checks: {len(health_result['checks'])}")
                    print(f"     Recommendations: {len(health_result['recommendations'])}")
                    
                    if health_result['status'] in ['healthy', 'warning']:
                        self.results['health_check'] = True
                    
                except Exception as e:
                    print(f"  ❌ Health check failed for {db_alias}: {e}")
            
        except Exception as e:
            print(f"  ❌ Health check test failed: {e}")
        print()
    
    def get_or_create_test_user(self):
        """Get or create a test user for admin interface testing."""
        try:
            user = User.objects.get(username='test_admin')
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username='test_admin',
                email='test@example.com',
                password='test123'
            )
        return user
    
    def display_results(self):
        """Display test results summary."""
        print("="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
        
        print("-"*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Database administration tools are working correctly.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the configuration.")
        
        print("\nAccess the database administration interface at:")
        print("http://localhost:8000/db-admin/")
        print("="*60)


def main():
    """Main test execution function."""
    test_suite = DatabaseAdminToolsTest()
    test_suite.run_all_tests()


if __name__ == '__main__':
    main()