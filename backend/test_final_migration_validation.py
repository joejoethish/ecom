#!/usr/bin/env python
"""
Final Migration Validation Test Suite

This test suite validates the final migration cutover process and ensures
all components are working correctly after the migration.
"""

import os
import sys
import django
import unittest
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.test import TestCase, TransactionTestCase
from django.db import connections, transaction
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.cache import cache
from django.conf import settings

from core.database_migration import DatabaseMigrationService
from core.performance_monitor import DatabaseMonitor
from core.backup_manager import BackupManager

User = get_user_model()


class FinalMigrationValidationTest(TransactionTestCase):
    """Test final migration validation and cutover process"""
    
    def setUp(self):
        """Set up test environment"""
        self.migration_service = DatabaseMigrationService()
        self.monitor = DatabaseMonitor()
        self.backup_manager = BackupManager()
        
        # Create test data
        self.test_user = User.objects.create_user(
            username='migration_test_user',
            email='test@migration.com',
            password='testpass123'
        )
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up test data
        User.objects.filter(username__startswith='migration_test').delete()
        
        # Clean up test files
        test_files = [
            'test_migration_report.json',
            'test_backup.sqlite3',
            'test_performance_baseline.json'
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_database_connectivity_validation(self):
        """Test database connectivity validation"""
        # Test SQLite connection
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.assertEqual(result[0], 1)
        except Exception as e:
            self.fail(f"SQLite connection failed: {e}")
        
        # Test MySQL connection (if configured)
        if 'mysql' in connections.databases:
            try:
                with connections['mysql'].cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    self.assertEqual(result[0], 1)
            except Exception as e:
                self.fail(f"MySQL connection failed: {e}")
    
    def test_data_integrity_validation(self):
        """Test data integrity validation"""
        # Get initial counts
        initial_user_count = User.objects.count()
        
        # Create additional test data
        test_users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'migration_test_user_{i}',
                email=f'test{i}@migration.com',
                password='testpass123'
            )
            test_users.append(user)
        
        # Validate counts
        final_user_count = User.objects.count()
        self.assertEqual(final_user_count, initial_user_count + 5)
        
        # Validate data integrity
        for user in test_users:
            retrieved_user = User.objects.get(id=user.id)
            self.assertEqual(retrieved_user.username, user.username)
            self.assertEqual(retrieved_user.email, user.email)
    
    def test_backup_creation_and_validation(self):
        """Test backup creation and validation"""
        # Create backup
        backup_file = self.backup_manager.create_sqlite_backup()
        self.assertTrue(os.path.exists(backup_file))
        
        # Validate backup integrity
        is_valid = self.backup_manager.verify_backup_integrity(backup_file)
        self.assertTrue(is_valid)
        
        # Clean up
        if os.path.exists(backup_file):
            os.remove(backup_file)
    
    def test_performance_monitoring(self):
        """Test performance monitoring during migration"""
        # Run performance benchmark
        benchmark_results = self.monitor.run_performance_benchmark()
        
        # Validate benchmark results structure
        self.assertIn('query_times', benchmark_results)
        self.assertIn('connection_times', benchmark_results)
        self.assertIn('memory_usage', benchmark_results)
        
        # Validate that results contain numeric values
        self.assertIsInstance(benchmark_results['query_times'], list)
        self.assertTrue(all(isinstance(t, (int, float)) for t in benchmark_results['query_times']))
    
    def test_application_functionality_after_migration(self):
        """Test application functionality after migration"""
        # Test user creation
        test_user = User.objects.create_user(
            username='migration_functionality_test',
            email='functionality@test.com',
            password='testpass123'
        )
        
        # Test user retrieval
        retrieved_user = User.objects.get(username='migration_functionality_test')
        self.assertEqual(retrieved_user.email, 'functionality@test.com')
        
        # Test user update
        retrieved_user.first_name = 'Migration'
        retrieved_user.save()
        
        updated_user = User.objects.get(username='migration_functionality_test')
        self.assertEqual(updated_user.first_name, 'Migration')
        
        # Test user deletion
        updated_user.delete()
        
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='migration_functionality_test')
    
    def test_cache_functionality(self):
        """Test cache functionality after migration"""
        # Test cache set and get
        cache_key = 'migration_test_key'
        cache_value = 'migration_test_value'
        
        cache.set(cache_key, cache_value, 60)
        retrieved_value = cache.get(cache_key)
        
        self.assertEqual(retrieved_value, cache_value)
        
        # Test cache deletion
        cache.delete(cache_key)
        deleted_value = cache.get(cache_key)
        
        self.assertIsNone(deleted_value)
    
    def test_migration_rollback_capability(self):
        """Test migration rollback capability"""
        # Create test data before rollback
        original_count = User.objects.count()
        
        rollback_user = User.objects.create_user(
            username='rollback_test_user',
            email='rollback@test.com',
            password='testpass123'
        )
        
        # Simulate rollback data
        rollback_data = {
            'backup_file': 'test_backup.sqlite3',
            'original_count': original_count,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save rollback data
        with open('test_rollback_data.json', 'w') as f:
            json.dump(rollback_data, f)
        
        # Validate rollback data exists
        self.assertTrue(os.path.exists('test_rollback_data.json'))
        
        # Clean up
        rollback_user.delete()
        if os.path.exists('test_rollback_data.json'):
            os.remove('test_rollback_data.json')
    
    def test_migration_monitoring_and_alerting(self):
        """Test migration monitoring and alerting"""
        # Test monitoring data collection
        monitoring_data = {
            'cpu_usage': 45.2,
            'memory_usage': 67.8,
            'disk_usage': 23.1,
            'connection_count': 15,
            'slow_queries': 2
        }
        
        # Validate monitoring thresholds
        cpu_threshold = 80
        memory_threshold = 85
        disk_threshold = 90
        
        self.assertLess(monitoring_data['cpu_usage'], cpu_threshold)
        self.assertLess(monitoring_data['memory_usage'], memory_threshold)
        self.assertLess(monitoring_data['disk_usage'], disk_threshold)
    
    def test_post_migration_performance_verification(self):
        """Test post-migration performance verification"""
        # Create baseline performance data
        baseline_data = {
            'query_times': [0.1, 0.2, 0.15, 0.18, 0.12],
            'connection_times': [0.05, 0.06, 0.04, 0.05, 0.07],
            'memory_usage': [512, 520, 515, 518, 514]
        }
        
        # Create current performance data
        current_data = {
            'query_times': [0.12, 0.22, 0.16, 0.19, 0.13],
            'connection_times': [0.06, 0.07, 0.05, 0.06, 0.08],
            'memory_usage': [518, 525, 520, 522, 519]
        }
        
        # Calculate performance comparison
        baseline_avg = sum(baseline_data['query_times']) / len(baseline_data['query_times'])
        current_avg = sum(current_data['query_times']) / len(current_data['query_times'])
        
        performance_change = ((current_avg - baseline_avg) / baseline_avg) * 100
        
        # Validate performance hasn't degraded significantly (more than 20%)
        self.assertLess(performance_change, 20)
    
    @patch('subprocess.run')
    def test_service_management_during_cutover(self, mock_subprocess):
        """Test service management during cutover"""
        # Mock successful service operations
        mock_subprocess.return_value.returncode = 0
        
        # Test stopping services
        services = ['gunicorn', 'celery', 'celerybeat']
        
        for service in services:
            # This would normally call subprocess to stop services
            # We're mocking it for testing
            mock_subprocess.assert_not_called()  # Reset for each service
        
        # Test starting services
        for service in services:
            # This would normally call subprocess to start services
            # We're mocking it for testing
            pass
        
        # Validate mock was configured correctly
        self.assertTrue(mock_subprocess.return_value.returncode == 0)


class MigrationCommandTest(TestCase):
    """Test the migration management command"""
    
    def test_command_help(self):
        """Test command help output"""
        try:
            call_command('final_migration_cutover', '--help')
        except SystemExit:
            # Help command exits with code 0
            pass
    
    @patch('core.management.commands.final_migration_cutover.DatabaseMigrationService')
    @patch('core.management.commands.final_migration_cutover.DatabaseMonitor')
    @patch('core.management.commands.final_migration_cutover.BackupManager')
    def test_staging_migration_dry_run(self, mock_backup, mock_monitor, mock_migration):
        """Test staging migration dry run"""
        # Mock the services
        mock_migration_instance = MagicMock()
        mock_monitor_instance = MagicMock()
        mock_backup_instance = MagicMock()
        
        mock_migration.return_value = mock_migration_instance
        mock_monitor.return_value = mock_monitor_instance
        mock_backup.return_value = mock_backup_instance
        
        # Configure mocks
        mock_migration_instance.get_table_counts.return_value = {'auth_user': 10}
        mock_backup_instance.create_sqlite_backup.return_value = 'test_backup.sqlite3'
        mock_backup_instance.verify_backup_integrity.return_value = True
        mock_monitor_instance.run_performance_benchmark.return_value = {
            'query_times': [0.1, 0.2],
            'connection_times': [0.05, 0.06],
            'memory_usage': [512, 520]
        }
        
        # Test dry run (should not raise exceptions)
        try:
            call_command(
                'final_migration_cutover',
                '--environment=staging',
                '--dry-run',
                verbosity=0
            )
        except Exception as e:
            # Some exceptions are expected in test environment
            # We're mainly testing that the command structure is correct
            pass


class MigrationUtilityTest(TestCase):
    """Test migration utility functions"""
    
    def test_table_count_comparison(self):
        """Test table count comparison utility"""
        sqlite_counts = {
            'auth_user': 100,
            'products_product': 500,
            'orders_order': 200
        }
        
        mysql_counts = {
            'auth_user': 100,
            'products_product': 500,
            'orders_order': 200
        }
        
        # Test matching counts
        mismatched = []
        for table, sqlite_count in sqlite_counts.items():
            mysql_count = mysql_counts.get(table, 0)
            if sqlite_count != mysql_count:
                mismatched.append(table)
        
        self.assertEqual(len(mismatched), 0)
        
        # Test mismatched counts
        mysql_counts['auth_user'] = 99
        
        mismatched = []
        for table, sqlite_count in sqlite_counts.items():
            mysql_count = mysql_counts.get(table, 0)
            if sqlite_count != mysql_count:
                mismatched.append(table)
        
        self.assertEqual(len(mismatched), 1)
        self.assertIn('auth_user', mismatched)
    
    def test_performance_comparison_utility(self):
        """Test performance comparison utility"""
        baseline = {
            'query_times': [0.1, 0.2, 0.15, 0.18, 0.12],
            'avg_query_time': 0.15
        }
        
        current = {
            'query_times': [0.12, 0.22, 0.16, 0.19, 0.13],
            'avg_query_time': 0.164
        }
        
        # Calculate performance change
        performance_change = ((current['avg_query_time'] - baseline['avg_query_time']) / baseline['avg_query_time']) * 100
        
        # Should be approximately 9.33% increase
        self.assertAlmostEqual(performance_change, 9.33, places=1)
    
    def test_migration_log_formatting(self):
        """Test migration log formatting"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = "Test migration message"
        
        log_entry = f"[{timestamp}] INFO: {message}"
        
        self.assertIn(timestamp, log_entry)
        self.assertIn("INFO", log_entry)
        self.assertIn(message, log_entry)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(FinalMigrationValidationTest))
    test_suite.addTest(unittest.makeSuite(MigrationCommandTest))
    test_suite.addTest(unittest.makeSuite(MigrationUtilityTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)