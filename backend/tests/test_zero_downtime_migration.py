"""
Comprehensive test suite for zero-downtime migration system.
Tests staged migration process, validation checkpoints, monitoring, and rollback triggers.
"""
import os
import sys
import unittest
import tempfile
import threading
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add Django project to path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')

import django
django.setup()

from core.zero_downtime_migration import (
    ZeroDowntimeMigrationService,
    MigrationStage,
    MigrationCheckpoint,
    MigrationMetrics,
    MigrationMonitor
)


class TestZeroDowntimeMigration(unittest.TestCase):
    """Test zero-downtime migration functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db',
            'charset': 'utf8mb4'
        }
        
        # Mock Django settings
        with patch('django.conf.settings') as mock_settings:
            mock_settings.BASE_DIR = Path(self.temp_dir)
            self.migration_service = ZeroDowntimeMigrationService(
                sqlite_path=self.temp_db.name,
                mysql_config=self.mysql_config
            )
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_migration_service_initialization(self):
        """Test migration service initialization"""
        self.assertIsNotNone(self.migration_service.migration_id)
        self.assertEqual(self.migration_service.current_stage, MigrationStage.PREPARATION)
        self.assertFalse(self.migration_service.is_running)
        self.assertFalse(self.migration_service.should_stop)
        self.assertFalse(self.migration_service.rollback_triggered)
        self.assertEqual(len(self.migration_service.checkpoints), 0)
        self.assertIsNone(self.migration_service.metrics)
    
    def test_callback_registration(self):
        """Test callback registration and notification"""
        progress_called = []
        checkpoint_called = []
        error_called = []
        
        def progress_callback(metrics):
            progress_called.append(metrics)
        
        def checkpoint_callback(checkpoint):
            checkpoint_called.append(checkpoint)
        
        def error_callback(error, stage):
            error_called.append((error, stage))
        
        # Register callbacks
        self.migration_service.add_progress_callback(progress_callback)
        self.migration_service.add_checkpoint_callback(checkpoint_callback)
        self.migration_service.add_error_callback(error_callback)
        
        # Test progress notification
        self.migration_service._update_metrics(
            stage=MigrationStage.PREPARATION,
            total_records=100,
            records_migrated=50
        )
        
        self.assertEqual(len(progress_called), 1)
        self.assertEqual(progress_called[0].records_migrated, 50)
        
        # Test checkpoint notification
        self.migration_service._create_checkpoint(
            MigrationStage.PREPARATION,
            'passed',
            {'test': 'data'}
        )
        
        self.assertEqual(len(checkpoint_called), 1)
        self.assertEqual(checkpoint_called[0].stage, MigrationStage.PREPARATION)
        
        # Test error notification
        test_error = Exception("Test error")
        self.migration_service._notify_error(test_error, MigrationStage.PREPARATION)
        
        self.assertEqual(len(error_called), 1)
        self.assertEqual(error_called[0][0], test_error)
        self.assertEqual(error_called[0][1], MigrationStage.PREPARATION)
    
    def test_checkpoint_creation(self):
        """Test checkpoint creation and storage"""
        validation_results = {'test': 'data', 'status': 'success'}
        
        checkpoint = self.migration_service._create_checkpoint(
            MigrationStage.SCHEMA_SYNC,
            'passed',
            validation_results
        )
        
        # Verify checkpoint properties
        self.assertEqual(checkpoint.stage, MigrationStage.SCHEMA_SYNC)
        self.assertEqual(checkpoint.status, 'passed')
        self.assertEqual(checkpoint.validation_results, validation_results)
        self.assertIsInstance(checkpoint.timestamp, datetime)
        
        # Verify checkpoint is stored
        self.assertEqual(len(self.migration_service.checkpoints), 1)
        self.assertEqual(self.migration_service.checkpoints[0], checkpoint)
    
    def test_metrics_update(self):
        """Test metrics update and calculation"""
        # Initial metrics update
        self.migration_service._update_metrics(
            stage=MigrationStage.INITIAL_DATA_SYNC,
            total_tables=5,
            total_records=1000,
            tables_processed=2,
            records_migrated=400
        )
        
        metrics = self.migration_service.metrics
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.stage, MigrationStage.INITIAL_DATA_SYNC)
        self.assertEqual(metrics.total_tables, 5)
        self.assertEqual(metrics.total_records, 1000)
        self.assertEqual(metrics.tables_processed, 2)
        self.assertEqual(metrics.records_migrated, 400)
        self.assertEqual(metrics.progress_percentage, 40.0)
        
        # Test migration speed calculation
        time.sleep(0.1)  # Small delay to ensure time difference
        self.migration_service._update_metrics(records_migrated=500)
        
        updated_metrics = self.migration_service.metrics
        self.assertEqual(updated_metrics.records_migrated, 500)
        self.assertGreater(updated_metrics.migration_speed, 0)
        self.assertIsNotNone(updated_metrics.estimated_completion)
    
    def test_rollback_trigger_checks(self):
        """Test rollback trigger conditions"""
        # Test error count trigger
        self.migration_service._update_metrics(error_count=5)
        self.assertTrue(self.migration_service._check_rollback_triggers())
        
        # Reset and test time limit trigger
        self.migration_service.metrics.error_count = 0
        self.migration_service.metrics.start_time = datetime.now() - timedelta(hours=25)
        self.assertTrue(self.migration_service._check_rollback_triggers())
        
        # Test validation failure trigger
        self.migration_service.metrics.start_time = datetime.now()
        for i in range(3):
            self.migration_service._create_checkpoint(
                MigrationStage.VALIDATION,
                'failed',
                {'error': f'test_error_{i}'}
            )
        self.assertTrue(self.migration_service._check_rollback_triggers())
    
    @patch('core.zero_downtime_migration.DatabaseMigrationService')
    def test_preparation_stage_success(self, mock_migration_service):
        """Test successful preparation stage"""
        # Mock database connections and table discovery
        mock_service = Mock()
        mock_service.connect_databases.return_value = True
        mock_service.get_sqlite_tables.return_value = ['users', 'products', 'orders']
        mock_service.sqlite_conn = Mock()
        
        # Mock cursor for record counting
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [(100,), (200,), (150,)]
        mock_service.sqlite_conn.cursor.return_value = mock_cursor
        
        self.migration_service.migration_service = mock_service
        
        # Execute preparation stage
        result = self.migration_service._stage_preparation()
        
        # Verify success
        self.assertTrue(result)
        self.assertEqual(len(self.migration_service.checkpoints), 2)  # in_progress + passed
        self.assertEqual(self.migration_service.checkpoints[-1].status, 'passed')
        self.assertIsNotNone(self.migration_service.metrics)
        self.assertEqual(self.migration_service.metrics.total_tables, 3)
        self.assertEqual(self.migration_service.metrics.total_records, 450)
    
    @patch('core.zero_downtime_migration.DatabaseMigrationService')
    def test_preparation_stage_failure(self, mock_migration_service):
        """Test preparation stage failure"""
        # Mock database connection failure
        mock_service = Mock()
        mock_service.connect_databases.return_value = False
        
        self.migration_service.migration_service = mock_service
        
        # Execute preparation stage
        result = self.migration_service._stage_preparation()
        
        # Verify failure
        self.assertFalse(result)
        self.assertEqual(len(self.migration_service.checkpoints), 2)  # in_progress + failed
        self.assertEqual(self.migration_service.checkpoints[-1].status, 'failed')
        self.assertIsNotNone(self.migration_service.checkpoints[-1].error_message)
    
    @patch('core.zero_downtime_migration.DatabaseMigrationService')
    def test_schema_sync_stage(self, mock_migration_service):
        """Test schema synchronization stage"""
        # Mock schema operations
        mock_service = Mock()
        mock_service.get_sqlite_tables.return_value = ['users', 'products']
        mock_service.get_table_schema.side_effect = [
            [{'name': 'id', 'type': 'INTEGER'}, {'name': 'name', 'type': 'TEXT'}],
            [{'name': 'id', 'type': 'INTEGER'}, {'name': 'title', 'type': 'TEXT'}]
        ]
        mock_service.create_mysql_table.return_value = True
        
        self.migration_service.migration_service = mock_service
        
        # Execute schema sync stage
        result = self.migration_service._stage_schema_sync()
        
        # Verify success
        self.assertTrue(result)
        self.assertEqual(len(self.migration_service.checkpoints), 2)
        self.assertEqual(self.migration_service.checkpoints[-1].status, 'passed')
        
        # Verify schema creation was called for each table
        self.assertEqual(mock_service.create_mysql_table.call_count, 2)
    
    @patch('core.zero_downtime_migration.DatabaseMigrationService')
    def test_data_sync_stage(self, mock_migration_service):
        """Test initial data synchronization stage"""
        # Mock data migration
        mock_service = Mock()
        mock_service.get_sqlite_tables.return_value = ['users', 'products']
        mock_service.create_rollback_point.return_value = True
        
        # Mock migration progress
        mock_progress_1 = Mock()
        mock_progress_1.status = 'completed'
        mock_progress_1.migrated_records = 100
        mock_progress_1.duration_seconds = 5.0
        
        mock_progress_2 = Mock()
        mock_progress_2.status = 'completed'
        mock_progress_2.migrated_records = 200
        mock_progress_2.duration_seconds = 8.0
        
        mock_service.migrate_table_data.side_effect = [mock_progress_1, mock_progress_2]
        
        self.migration_service.migration_service = mock_service
        
        # Execute data sync stage
        result = self.migration_service._stage_initial_data_sync()
        
        # Verify success
        self.assertTrue(result)
        self.assertEqual(len(self.migration_service.checkpoints), 2)
        self.assertEqual(self.migration_service.checkpoints[-1].status, 'passed')
        
        # Verify metrics were updated
        self.assertIsNotNone(self.migration_service.metrics)
        self.assertEqual(self.migration_service.metrics.records_migrated, 300)
        self.assertEqual(self.migration_service.metrics.tables_processed, 2)
    
    @patch('core.zero_downtime_migration.DatabaseMigrationService')
    def test_validation_stage(self, mock_migration_service):
        """Test data validation stage"""
        # Mock validation results
        mock_service = Mock()
        mock_service.get_sqlite_tables.return_value = ['users', 'products']
        
        mock_validation_1 = Mock()
        mock_validation_1.is_valid = True
        mock_validation_1.source_count = 100
        mock_validation_1.target_count = 100
        mock_validation_1.missing_records = []
        mock_validation_1.extra_records = []
        
        mock_validation_2 = Mock()
        mock_validation_2.is_valid = True
        mock_validation_2.source_count = 200
        mock_validation_2.target_count = 200
        mock_validation_2.missing_records = []
        mock_validation_2.extra_records = []
        
        mock_service.validate_migration.side_effect = [mock_validation_1, mock_validation_2]
        
        self.migration_service.migration_service = mock_service
        
        # Execute validation stage
        result = self.migration_service._stage_validation()
        
        # Verify success
        self.assertTrue(result)
        self.assertEqual(len(self.migration_service.checkpoints), 2)
        self.assertEqual(self.migration_service.checkpoints[-1].status, 'passed')
    
    @patch('core.zero_downtime_migration.DatabaseMigrationService')
    def test_validation_stage_failure(self, mock_migration_service):
        """Test validation stage with failures"""
        # Mock validation with failures
        mock_service = Mock()
        mock_service.get_sqlite_tables.return_value = ['users', 'products']
        
        mock_validation_1 = Mock()
        mock_validation_1.is_valid = False
        mock_validation_1.source_count = 100
        mock_validation_1.target_count = 95
        mock_validation_1.missing_records = [1, 2, 3, 4, 5]
        mock_validation_1.extra_records = []
        
        mock_validation_2 = Mock()
        mock_validation_2.is_valid = True
        mock_validation_2.source_count = 200
        mock_validation_2.target_count = 200
        mock_validation_2.missing_records = []
        mock_validation_2.extra_records = []
        
        mock_service.validate_migration.side_effect = [mock_validation_1, mock_validation_2]
        
        self.migration_service.migration_service = mock_service
        
        # Execute validation stage
        result = self.migration_service._stage_validation()
        
        # Verify failure
        self.assertFalse(result)
        self.assertEqual(len(self.migration_service.checkpoints), 2)
        self.assertEqual(self.migration_service.checkpoints[-1].status, 'failed')
    
    def test_cutover_stages(self):
        """Test cutover preparation and execution stages"""
        # Mock successful preparation
        with patch.object(self.migration_service.migration_service, 'get_sqlite_tables') as mock_tables, \
             patch.object(self.migration_service.migration_service, 'validate_migration') as mock_validate:
            
            mock_tables.return_value = ['users']
            mock_validation = Mock()
            mock_validation.is_valid = True
            mock_validate.return_value = mock_validation
            
            # Test cutover preparation
            result = self.migration_service._stage_cutover_preparation()
            self.assertTrue(result)
            
            # Test cutover execution
            result = self.migration_service._stage_cutover()
            self.assertTrue(result)
            
            # Test post-cutover validation
            result = self.migration_service._stage_post_cutover_validation()
            self.assertTrue(result)
    
    @patch('core.zero_downtime_migration.DatabaseMigrationService')
    def test_rollback_execution(self, mock_migration_service):
        """Test rollback execution"""
        # Mock rollback data and operations
        mock_service = Mock()
        mock_service.rollback_data = {'users': {}, 'products': {}}
        mock_service.rollback_table.return_value = True
        
        self.migration_service.migration_service = mock_service
        
        # Execute rollback
        result = self.migration_service._execute_rollback()
        
        # Verify rollback execution
        self.assertTrue(result)
        self.assertEqual(mock_service.rollback_table.call_count, 2)
        self.assertEqual(len(self.migration_service.checkpoints), 2)
        self.assertEqual(self.migration_service.checkpoints[-1].status, 'passed')
    
    def test_migration_status_reporting(self):
        """Test migration status reporting"""
        # Create some test data
        self.migration_service._update_metrics(
            stage=MigrationStage.INITIAL_DATA_SYNC,
            total_records=1000,
            records_migrated=500
        )
        
        self.migration_service._create_checkpoint(
            MigrationStage.PREPARATION,
            'passed',
            {'test': 'data'}
        )
        
        # Get status
        status = self.migration_service.get_migration_status()
        
        # Verify status structure
        self.assertIn('migration_id', status)
        self.assertIn('current_stage', status)
        self.assertIn('is_running', status)
        self.assertIn('metrics', status)
        self.assertIn('checkpoints', status)
        self.assertIn('last_checkpoint', status)
        
        # Verify content
        self.assertEqual(status['current_stage'], MigrationStage.PREPARATION.value)
        self.assertIsNotNone(status['metrics'])
        self.assertEqual(len(status['checkpoints']), 1)
        self.assertIsNotNone(status['last_checkpoint'])
    
    def test_migration_control(self):
        """Test migration control operations"""
        # Test stop request
        self.assertFalse(self.migration_service.should_stop)
        self.migration_service.stop_migration()
        self.assertTrue(self.migration_service.should_stop)
        
        # Test rollback trigger
        self.assertFalse(self.migration_service.rollback_triggered)
        self.migration_service.trigger_rollback("Test trigger")
        self.assertTrue(self.migration_service.rollback_triggered)
        self.assertTrue(self.migration_service.should_stop)
    
    def test_monitoring_callbacks(self):
        """Test monitoring callback utilities"""
        # Test console progress callback (should not raise exceptions)
        metrics = MigrationMetrics(
            stage=MigrationStage.INITIAL_DATA_SYNC,
            start_time=datetime.now(),
            current_time=datetime.now(),
            tables_processed=2,
            total_tables=5,
            records_migrated=500,
            total_records=1000,
            migration_speed=100.0,
            estimated_completion=datetime.now() + timedelta(seconds=50),
            error_count=0,
            warning_count=0
        )
        
        # This should not raise an exception
        try:
            MigrationMonitor.console_progress_callback(metrics)
        except Exception as e:
            self.fail(f"Console progress callback raised exception: {e}")
        
        # Test file progress callback
        temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_log.close()
        
        try:
            file_callback = MigrationMonitor.file_progress_callback(temp_log.name)
            file_callback(metrics)
            
            # Verify log file was written
            with open(temp_log.name, 'r') as f:
                content = f.read()
                self.assertIn('initial_data_sync', content)
                self.assertIn('500', content)  # records_migrated
        finally:
            os.unlink(temp_log.name)
    
    def test_migration_metrics_calculations(self):
        """Test migration metrics calculations"""
        start_time = datetime.now() - timedelta(seconds=60)
        current_time = datetime.now()
        
        metrics = MigrationMetrics(
            stage=MigrationStage.INITIAL_DATA_SYNC,
            start_time=start_time,
            current_time=current_time,
            tables_processed=3,
            total_tables=5,
            records_migrated=750,
            total_records=1000,
            migration_speed=12.5,
            estimated_completion=current_time + timedelta(seconds=20),
            error_count=1,
            warning_count=2
        )
        
        # Test progress percentage
        self.assertEqual(metrics.progress_percentage, 75.0)
        
        # Test elapsed time
        self.assertAlmostEqual(metrics.elapsed_time.total_seconds(), 60, delta=1)
        
        # Test serialization
        metrics_dict = metrics.to_dict()
        self.assertIn('stage', metrics_dict)
        self.assertIn('progress_percentage', metrics_dict)
        self.assertIn('elapsed_time_seconds', metrics_dict)
        self.assertEqual(metrics_dict['records_migrated'], 750)
        self.assertEqual(metrics_dict['error_count'], 1)
    
    def test_checkpoint_serialization(self):
        """Test checkpoint serialization"""
        checkpoint = MigrationCheckpoint(
            stage=MigrationStage.VALIDATION,
            timestamp=datetime.now(),
            status='passed',
            validation_results={'tables_validated': 5, 'errors': 0},
            error_message=None
        )
        
        # Test serialization
        checkpoint_dict = checkpoint.to_dict()
        
        # Verify structure
        self.assertIn('stage', checkpoint_dict)
        self.assertIn('timestamp', checkpoint_dict)
        self.assertIn('status', checkpoint_dict)
        self.assertIn('validation_results', checkpoint_dict)
        self.assertIn('error_message', checkpoint_dict)
        
        # Verify content
        self.assertEqual(checkpoint_dict['stage'], 'validation')
        self.assertEqual(checkpoint_dict['status'], 'passed')
        self.assertEqual(checkpoint_dict['validation_results']['tables_validated'], 5)
        self.assertIsNone(checkpoint_dict['error_message'])


class TestZeroDowntimeMigrationIntegration(unittest.TestCase):
    """Integration tests for zero-downtime migration"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Create test SQLite database
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE test_users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO test_users (name, email) VALUES
            ('John Doe', 'john@example.com'),
            ('Jane Smith', 'jane@example.com'),
            ('Bob Johnson', 'bob@example.com')
        ''')
        
        conn.commit()
        conn.close()
        
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db',
            'charset': 'utf8mb4'
        }
    
    def tearDown(self):
        """Clean up integration test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('django.conf.settings')
    @patch('mysql.connector.connect')
    def test_full_migration_workflow_mock(self, mock_mysql_connect, mock_settings):
        """Test full migration workflow with mocked dependencies"""
        # Mock Django settings
        mock_settings.BASE_DIR = Path(self.temp_dir)
        
        # Mock MySQL connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mysql_connect.return_value = mock_conn
        
        # Create migration service
        migration_service = ZeroDowntimeMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Track callback invocations
        progress_updates = []
        checkpoint_updates = []
        error_notifications = []
        
        migration_service.add_progress_callback(lambda m: progress_updates.append(m))
        migration_service.add_checkpoint_callback(lambda c: checkpoint_updates.append(c))
        migration_service.add_error_callback(lambda e, s: error_notifications.append((e, s)))
        
        # Mock the migration service methods to simulate successful execution
        with patch.object(migration_service, '_stage_preparation', return_value=True), \
             patch.object(migration_service, '_stage_schema_sync', return_value=True), \
             patch.object(migration_service, '_stage_initial_data_sync', return_value=True), \
             patch.object(migration_service, '_stage_validation', return_value=True), \
             patch.object(migration_service, '_stage_cutover_preparation', return_value=True), \
             patch.object(migration_service, '_stage_cutover', return_value=True), \
             patch.object(migration_service, '_stage_post_cutover_validation', return_value=True), \
             patch.object(migration_service, '_stage_cleanup', return_value=True):
            
            # Execute migration
            result = migration_service.execute_migration()
            
            # Verify successful completion
            self.assertTrue(result)
            self.assertEqual(migration_service.current_stage, MigrationStage.COMPLETED)
            self.assertFalse(migration_service.rollback_triggered)
            
            # Verify callbacks were invoked
            self.assertGreater(len(checkpoint_updates), 0)
            
            # Verify final status
            status = migration_service.get_migration_status()
            self.assertEqual(status['current_stage'], 'completed')
            self.assertFalse(status['rollback_triggered'])
    
    @patch('django.conf.settings')
    def test_migration_failure_and_rollback(self, mock_settings):
        """Test migration failure and automatic rollback"""
        # Mock Django settings
        mock_settings.BASE_DIR = Path(self.temp_dir)
        
        # Create migration service
        migration_service = ZeroDowntimeMigrationService(
            sqlite_path=self.temp_db.name,
            mysql_config=self.mysql_config
        )
        
        # Track error notifications
        error_notifications = []
        migration_service.add_error_callback(lambda e, s: error_notifications.append((e, s)))
        
        # Mock stages to simulate failure at validation stage
        with patch.object(migration_service, '_stage_preparation', return_value=True), \
             patch.object(migration_service, '_stage_schema_sync', return_value=True), \
             patch.object(migration_service, '_stage_initial_data_sync', return_value=True), \
             patch.object(migration_service, '_stage_validation', return_value=False), \
             patch.object(migration_service, '_execute_rollback', return_value=True):
            
            # Execute migration
            result = migration_service.execute_migration()
            
            # Verify failure and rollback
            self.assertFalse(result)
            self.assertEqual(migration_service.current_stage, MigrationStage.FAILED)
            self.assertTrue(migration_service.rollback_triggered)
    
    def test_migration_interruption(self):
        """Test migration interruption and graceful shutdown"""
        with patch('django.conf.settings') as mock_settings:
            mock_settings.BASE_DIR = Path(self.temp_dir)
            
            migration_service = ZeroDowntimeMigrationService(
                sqlite_path=self.temp_db.name,
                mysql_config=self.mysql_config
            )
            
            # Mock stages with delays to simulate long-running migration
            def slow_stage():
                time.sleep(0.1)
                return not migration_service.should_stop
            
            with patch.object(migration_service, '_stage_preparation', side_effect=slow_stage), \
                 patch.object(migration_service, '_stage_schema_sync', side_effect=slow_stage), \
                 patch.object(migration_service, '_execute_rollback', return_value=True):
                
                # Start migration in separate thread
                migration_thread = threading.Thread(target=migration_service.execute_migration)
                migration_thread.start()
                
                # Wait a bit then stop migration
                time.sleep(0.05)
                migration_service.stop_migration()
                
                # Wait for migration to complete
                migration_thread.join(timeout=1.0)
                
                # Verify migration was stopped
                self.assertTrue(migration_service.should_stop)


def run_zero_downtime_migration_tests():
    """Run zero-downtime migration tests"""
    print("ZERO-DOWNTIME MIGRATION TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestZeroDowntimeMigration))
    suite.addTests(loader.loadTestsFromTestCase(TestZeroDowntimeMigrationIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("ZERO-DOWNTIME MIGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    try:
        success = run_zero_downtime_migration_tests()
        if success:
            print("\n✅ All zero-downtime migration tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)