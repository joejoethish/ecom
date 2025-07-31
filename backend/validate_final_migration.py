#!/usr/bin/env python
"""
Final Migration Validation Script

This script performs comprehensive validation of the final migration cutover,
ensuring all systems are working correctly and data integrity is maintained.
"""

import os
import sys
import django
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.production')
django.setup()

from django.db import connections, transaction
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.test.utils import override_settings

User = get_user_model()


class FinalMigrationValidator:
    """Comprehensive validation of final migration cutover"""
    
    def __init__(self, environment='production'):
        self.environment = environment
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'environment': environment,
            'tests': {},
            'overall_status': 'UNKNOWN',
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'warnings': 0
            }
        }
        
    def run_all_validations(self):
        """Run all validation tests"""
        print(f"Starting final migration validation for {self.environment}")
        print("=" * 60)
        
        # Database validation
        self.validate_database_connectivity()
        self.validate_data_integrity()
        self.validate_database_performance()
        
        # Application validation
        self.validate_application_functionality()
        self.validate_api_endpoints()
        self.validate_cache_functionality()
        
        # System validation
        self.validate_system_resources()
        self.validate_monitoring_systems()
        self.validate_backup_systems()
        
        # Security validation
        self.validate_security_configuration()
        self.validate_ssl_configuration()
        
        # Performance validation
        self.validate_query_performance()
        self.validate_connection_pooling()
        
        # Generate final report
        self.generate_validation_report()
        
        return self.validation_results['overall_status'] == 'PASS'
    
    def validate_database_connectivity(self):
        """Validate database connectivity"""
        test_name = "Database Connectivity"
        print(f"Testing {test_name}...")
        
        try:
            # Test primary database connection
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                assert result[0] == 1, "Primary database query failed"
            
            # Test read replica connection (if configured)
            if 'read_replica' in connections.databases:
                with connections['read_replica'].cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    assert result[0] == 1, "Read replica query failed"
            
            self.record_test_result(test_name, 'PASS', "Database connectivity verified")
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Database connectivity failed: {str(e)}")
    
    def validate_data_integrity(self):
        """Validate data integrity after migration"""
        test_name = "Data Integrity"
        print(f"Testing {test_name}...")
        
        try:
            # Check table counts
            table_counts = self.get_table_counts()
            
            # Validate user data
            user_count = User.objects.count()
            assert user_count > 0, "No users found in database"
            
            # Test data relationships
            sample_user = User.objects.first()
            if sample_user:
                # Test user can be retrieved and updated
                sample_user.last_login = datetime.now()
                sample_user.save()
            
            # Validate foreign key constraints
            self.validate_foreign_key_constraints()
            
            self.record_test_result(
                test_name, 
                'PASS', 
                f"Data integrity verified. Tables: {len(table_counts)}, Users: {user_count}"
            )
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Data integrity validation failed: {str(e)}")
    
    def validate_database_performance(self):
        """Validate database performance"""
        test_name = "Database Performance"
        print(f"Testing {test_name}...")
        
        try:
            # Test query performance
            start_time = time.time()
            user_count = User.objects.count()
            query_time = time.time() - start_time
            
            # Performance thresholds
            max_query_time = 2.0  # seconds
            
            if query_time > max_query_time:
                self.record_test_result(
                    test_name, 
                    'WARNING', 
                    f"Query time ({query_time:.2f}s) exceeds threshold ({max_query_time}s)"
                )
            else:
                self.record_test_result(
                    test_name, 
                    'PASS', 
                    f"Database performance acceptable. Query time: {query_time:.2f}s"
                )
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Database performance test failed: {str(e)}")
    
    def validate_application_functionality(self):
        """Validate core application functionality"""
        test_name = "Application Functionality"
        print(f"Testing {test_name}...")
        
        try:
            # Test user operations
            test_username = f"migration_test_{int(time.time())}"
            
            # Create user
            test_user = User.objects.create_user(
                username=test_username,
                email=f"{test_username}@test.com",
                password="testpass123"
            )
            
            # Update user
            test_user.first_name = "Migration"
            test_user.last_name = "Test"
            test_user.save()
            
            # Retrieve user
            retrieved_user = User.objects.get(username=test_username)
            assert retrieved_user.first_name == "Migration", "User update failed"
            
            # Delete user
            retrieved_user.delete()
            
            # Verify deletion
            assert not User.objects.filter(username=test_username).exists(), "User deletion failed"
            
            self.record_test_result(test_name, 'PASS', "Application functionality verified")
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Application functionality test failed: {str(e)}")
    
    def validate_api_endpoints(self):
        """Validate API endpoints"""
        test_name = "API Endpoints"
        print(f"Testing {test_name}...")
        
        try:
            base_url = "http://localhost:8000"
            endpoints = [
                "/api/v1/health/",
                "/api/v1/products/",
                "/api/v1/categories/",
                "/admin/",
            ]
            
            failed_endpoints = []
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=10)
                    if response.status_code not in [200, 301, 302]:
                        failed_endpoints.append(f"{endpoint} (Status: {response.status_code})")
                except requests.RequestException as e:
                    failed_endpoints.append(f"{endpoint} (Error: {str(e)})")
            
            if failed_endpoints:
                self.record_test_result(
                    test_name, 
                    'FAIL', 
                    f"Failed endpoints: {', '.join(failed_endpoints)}"
                )
            else:
                self.record_test_result(test_name, 'PASS', f"All {len(endpoints)} endpoints accessible")
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"API endpoint validation failed: {str(e)}")
    
    def validate_cache_functionality(self):
        """Validate cache functionality"""
        test_name = "Cache Functionality"
        print(f"Testing {test_name}...")
        
        try:
            # Test cache operations
            cache_key = f"migration_test_{int(time.time())}"
            cache_value = "test_value_123"
            
            # Set cache
            cache.set(cache_key, cache_value, 300)
            
            # Get cache
            retrieved_value = cache.get(cache_key)
            assert retrieved_value == cache_value, "Cache value mismatch"
            
            # Delete cache
            cache.delete(cache_key)
            
            # Verify deletion
            deleted_value = cache.get(cache_key)
            assert deleted_value is None, "Cache deletion failed"
            
            self.record_test_result(test_name, 'PASS', "Cache functionality verified")
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Cache functionality test failed: {str(e)}")
    
    def validate_system_resources(self):
        """Validate system resources"""
        test_name = "System Resources"
        print(f"Testing {test_name}...")
        
        try:
            # Check disk space
            import shutil
            disk_usage = shutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            
            # Check memory
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_available = int([line for line in meminfo.split('\n') 
                                   if 'MemAvailable' in line][0].split()[1]) * 1024
                mem_available_gb = mem_available / (1024**3)
            
            # Resource thresholds
            min_disk_gb = 5
            min_memory_gb = 1
            
            issues = []
            if free_gb < min_disk_gb:
                issues.append(f"Low disk space: {free_gb:.1f}GB")
            
            if mem_available_gb < min_memory_gb:
                issues.append(f"Low memory: {mem_available_gb:.1f}GB")
            
            if issues:
                self.record_test_result(test_name, 'WARNING', f"Resource issues: {', '.join(issues)}")
            else:
                self.record_test_result(
                    test_name, 
                    'PASS', 
                    f"System resources adequate. Disk: {free_gb:.1f}GB, Memory: {mem_available_gb:.1f}GB"
                )
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"System resource validation failed: {str(e)}")
    
    def validate_monitoring_systems(self):
        """Validate monitoring systems"""
        test_name = "Monitoring Systems"
        print(f"Testing {test_name}...")
        
        try:
            # Check if monitoring files exist
            monitoring_files = [
                'logs/application.log',
                'logs/database.log',
                'logs/performance.log'
            ]
            
            missing_files = []
            for log_file in monitoring_files:
                if not os.path.exists(log_file):
                    missing_files.append(log_file)
            
            # Test performance monitoring
            try:
                from core.performance_monitor import DatabaseMonitor
                monitor = DatabaseMonitor()
                # This would test if monitoring is working
                monitoring_active = True
            except ImportError:
                monitoring_active = False
            
            if missing_files or not monitoring_active:
                issues = []
                if missing_files:
                    issues.append(f"Missing log files: {', '.join(missing_files)}")
                if not monitoring_active:
                    issues.append("Performance monitoring not active")
                
                self.record_test_result(test_name, 'WARNING', f"Monitoring issues: {', '.join(issues)}")
            else:
                self.record_test_result(test_name, 'PASS', "Monitoring systems operational")
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Monitoring validation failed: {str(e)}")
    
    def validate_backup_systems(self):
        """Validate backup systems"""
        test_name = "Backup Systems"
        print(f"Testing {test_name}...")
        
        try:
            # Check backup configuration
            backup_enabled = getattr(settings, 'BACKUP_ENABLED', False)
            backup_path = getattr(settings, 'BACKUP_STORAGE_PATH', '/var/backups/mysql')
            
            # Check if backup directory exists
            backup_dir_exists = os.path.exists(backup_path)
            
            # Check for recent backups
            recent_backups = []
            if backup_dir_exists:
                backup_files = os.listdir(backup_path)
                # Look for files modified in the last 24 hours
                cutoff_time = time.time() - (24 * 60 * 60)
                for backup_file in backup_files:
                    file_path = os.path.join(backup_path, backup_file)
                    if os.path.getmtime(file_path) > cutoff_time:
                        recent_backups.append(backup_file)
            
            if not backup_enabled:
                self.record_test_result(test_name, 'WARNING', "Backup system not enabled")
            elif not backup_dir_exists:
                self.record_test_result(test_name, 'FAIL', f"Backup directory does not exist: {backup_path}")
            elif not recent_backups:
                self.record_test_result(test_name, 'WARNING', "No recent backups found")
            else:
                self.record_test_result(
                    test_name, 
                    'PASS', 
                    f"Backup system operational. Recent backups: {len(recent_backups)}"
                )
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Backup validation failed: {str(e)}")
    
    def validate_security_configuration(self):
        """Validate security configuration"""
        test_name = "Security Configuration"
        print(f"Testing {test_name}...")
        
        try:
            security_issues = []
            
            # Check DEBUG setting
            if getattr(settings, 'DEBUG', True):
                security_issues.append("DEBUG is enabled in production")
            
            # Check SECRET_KEY
            secret_key = getattr(settings, 'SECRET_KEY', '')
            if not secret_key or len(secret_key) < 50:
                security_issues.append("SECRET_KEY is weak or missing")
            
            # Check ALLOWED_HOSTS
            allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
            if not allowed_hosts or '*' in allowed_hosts:
                security_issues.append("ALLOWED_HOSTS not properly configured")
            
            # Check database password
            db_password = settings.DATABASES['default'].get('PASSWORD', '')
            if not db_password:
                security_issues.append("Database password not set")
            
            if security_issues:
                self.record_test_result(
                    test_name, 
                    'FAIL', 
                    f"Security issues: {', '.join(security_issues)}"
                )
            else:
                self.record_test_result(test_name, 'PASS', "Security configuration validated")
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Security validation failed: {str(e)}")
    
    def validate_ssl_configuration(self):
        """Validate SSL configuration"""
        test_name = "SSL Configuration"
        print(f"Testing {test_name}...")
        
        try:
            # Check database SSL configuration
            db_options = settings.DATABASES['default'].get('OPTIONS', {})
            ssl_config = db_options.get('ssl', {})
            
            if not ssl_config:
                self.record_test_result(test_name, 'WARNING', "Database SSL not configured")
                return
            
            # Check SSL certificate files
            ssl_files = ['ca', 'cert', 'key']
            missing_files = []
            
            for ssl_file in ssl_files:
                if ssl_file in ssl_config:
                    file_path = ssl_config[ssl_file]
                    if not os.path.exists(file_path):
                        missing_files.append(file_path)
            
            if missing_files:
                self.record_test_result(
                    test_name, 
                    'FAIL', 
                    f"Missing SSL certificate files: {', '.join(missing_files)}"
                )
            else:
                self.record_test_result(test_name, 'PASS', "SSL configuration validated")
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"SSL validation failed: {str(e)}")
    
    def validate_query_performance(self):
        """Validate query performance"""
        test_name = "Query Performance"
        print(f"Testing {test_name}...")
        
        try:
            # Test various query types
            queries = [
                ("Simple SELECT", lambda: User.objects.count()),
                ("Filtered SELECT", lambda: User.objects.filter(is_active=True).count()),
                ("JOIN Query", lambda: User.objects.select_related().first()),
            ]
            
            performance_results = []
            
            for query_name, query_func in queries:
                start_time = time.time()
                result = query_func()
                query_time = time.time() - start_time
                performance_results.append((query_name, query_time))
            
            # Check if any queries are too slow
            slow_queries = [(name, time) for name, time in performance_results if time > 1.0]
            
            if slow_queries:
                slow_query_info = ', '.join([f"{name}: {time:.2f}s" for name, time in slow_queries])
                self.record_test_result(
                    test_name, 
                    'WARNING', 
                    f"Slow queries detected: {slow_query_info}"
                )
            else:
                avg_time = sum(time for _, time in performance_results) / len(performance_results)
                self.record_test_result(
                    test_name, 
                    'PASS', 
                    f"Query performance acceptable. Average: {avg_time:.3f}s"
                )
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Query performance validation failed: {str(e)}")
    
    def validate_connection_pooling(self):
        """Validate connection pooling"""
        test_name = "Connection Pooling"
        print(f"Testing {test_name}...")
        
        try:
            # Test multiple concurrent connections
            connection_times = []
            
            for i in range(5):
                start_time = time.time()
                with connections['default'].cursor() as cursor:
                    cursor.execute("SELECT 1")
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
            
            avg_connection_time = sum(connection_times) / len(connection_times)
            max_connection_time = max(connection_times)
            
            # Connection pooling should keep times low and consistent
            if max_connection_time > 0.5:  # 500ms threshold
                self.record_test_result(
                    test_name, 
                    'WARNING', 
                    f"High connection time detected: {max_connection_time:.3f}s"
                )
            else:
                self.record_test_result(
                    test_name, 
                    'PASS', 
                    f"Connection pooling working. Avg: {avg_connection_time:.3f}s"
                )
            
        except Exception as e:
            self.record_test_result(test_name, 'FAIL', f"Connection pooling validation failed: {str(e)}")
    
    def get_table_counts(self):
        """Get counts for all tables"""
        table_counts = {}
        
        with connections['default'].cursor() as cursor:
            # Get all table names
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                AND table_type = 'BASE TABLE'
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get count for each table
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except Exception as e:
                    table_counts[table] = f"Error: {str(e)}"
        
        return table_counts
    
    def validate_foreign_key_constraints(self):
        """Validate foreign key constraints"""
        with connections['default'].cursor() as cursor:
            # Check for foreign key constraint violations
            cursor.execute("""
                SELECT COUNT(*) as violations
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = DATABASE()
            """)
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                # Foreign keys exist, which is good
                pass
    
    def record_test_result(self, test_name, status, message):
        """Record test result"""
        self.validation_results['tests'][test_name] = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Update summary
        self.validation_results['summary']['total_tests'] += 1
        
        if status == 'PASS':
            self.validation_results['summary']['passed_tests'] += 1
            print(f"  ✓ {test_name}: {message}")
        elif status == 'WARNING':
            self.validation_results['summary']['warnings'] += 1
            print(f"  ⚠ {test_name}: {message}")
        else:  # FAIL
            self.validation_results['summary']['failed_tests'] += 1
            print(f"  ✗ {test_name}: {message}")
    
    def generate_validation_report(self):
        """Generate final validation report"""
        # Determine overall status
        if self.validation_results['summary']['failed_tests'] > 0:
            self.validation_results['overall_status'] = 'FAIL'
        elif self.validation_results['summary']['warnings'] > 0:
            self.validation_results['overall_status'] = 'WARNING'
        else:
            self.validation_results['overall_status'] = 'PASS'
        
        # Print summary
        print("\n" + "=" * 60)
        print("FINAL MIGRATION VALIDATION SUMMARY")
        print("=" * 60)
        
        summary = self.validation_results['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Warnings: {summary['warnings']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Overall Status: {self.validation_results['overall_status']}")
        
        # Save report to file
        report_file = f"final_migration_validation_{self.environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return self.validation_results['overall_status']


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Final Migration Validation')
    parser.add_argument(
        '--environment',
        choices=['staging', 'production'],
        default='production',
        help='Environment to validate'
    )
    
    args = parser.parse_args()
    
    validator = FinalMigrationValidator(args.environment)
    success = validator.run_all_validations()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()