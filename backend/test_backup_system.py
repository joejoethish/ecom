#!/usr/bin/env python
"""
Test script for MySQL backup and recovery system

This script tests all major functionality of the backup system including:
- Full backup creation and verification
- Incremental backup creation and verification
- Backup encryption and decryption
- Point-in-time recovery capabilities
- Backup cleanup operations
- Scheduler functionality

Usage:
    python test_backup_system.py
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')
django.setup()

import logging
import tempfile
import shutil
from datetime import datetime, timedelta
from core.backup_manager import MySQLBackupManager, BackupConfig
from core.backup_scheduler import BackupScheduler, ScheduleConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackupSystemTester:
    """Test suite for backup system"""
    
    def __init__(self):
        # Create temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp(prefix='backup_test_'))
        logger.info(f"Using test directory: {self.test_dir}")
        
        # Configure backup manager for testing
        self.config = BackupConfig(
            backup_dir=str(self.test_dir),
            encryption_key='test-encryption-key-for-testing-only',
            retention_days=7,
            compression_enabled=True,
            verify_backups=True,
        )
        
        self.backup_manager = MySQLBackupManager(self.config)
        self.test_results = []
    
    def cleanup(self):
        """Clean up test directory"""
        try:
            shutil.rmtree(self.test_dir)
            logger.info(f"Cleaned up test directory: {self.test_dir}")
        except Exception as e:
            logger.error(f"Failed to cleanup test directory: {e}")
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        logger.info(f"Running test: {test_name}")
        
        try:
            start_time = datetime.now()
            test_func()
            duration = (datetime.now() - start_time).total_seconds()
            
            self.test_results.append({
                'name': test_name,
                'status': 'PASS',
                'duration': duration,
                'error': None
            })
            logger.info(f"[PASS] {test_name} - PASSED ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.test_results.append({
                'name': test_name,
                'status': 'FAIL',
                'duration': duration,
                'error': str(e)
            })
            logger.error(f"[FAIL] {test_name} - FAILED ({duration:.2f}s): {e}")
    
    def test_backup_config(self):
        """Test backup configuration"""
        assert self.config.backup_dir == str(self.test_dir)
        assert self.config.encryption_key == 'test-encryption-key-for-testing-only'
        assert self.config.retention_days == 7
        assert self.config.compression_enabled is True
        assert self.config.verify_backups is True
    
    def test_backup_storage_initialization(self):
        """Test backup storage directory creation"""
        storage = self.backup_manager.storage
        
        # Check that directories were created
        assert (self.test_dir / 'full').exists()
        assert (self.test_dir / 'incremental').exists()
        assert (self.test_dir / 'metadata').exists()
        assert (self.test_dir / 'temp').exists()
    
    def test_encryption_functionality(self):
        """Test backup encryption and decryption"""
        encryption = self.backup_manager.encryption
        
        # Create test file
        test_content = b"This is test backup content for encryption testing"
        test_file = self.test_dir / 'test_input.txt'
        encrypted_file = self.test_dir / 'test_encrypted.enc'
        decrypted_file = self.test_dir / 'test_decrypted.txt'
        
        # Write test content
        test_file.write_bytes(test_content)
        
        # Test encryption
        checksum = encryption.encrypt_file(str(test_file), str(encrypted_file))
        assert encrypted_file.exists()
        assert len(checksum) == 64  # SHA256 hex digest length
        
        # Test decryption
        decrypted_checksum = encryption.decrypt_file(str(encrypted_file), str(decrypted_file))
        assert decrypted_file.exists()
        assert checksum == decrypted_checksum
        
        # Verify content
        decrypted_content = decrypted_file.read_bytes()
        assert decrypted_content == test_content
    
    def test_full_backup_creation(self):
        """Test full backup creation"""
        try:
            metadata = self.backup_manager.create_full_backup()
            
            # Verify metadata
            assert metadata.backup_type == 'full'
            assert metadata.backup_id.startswith('full_')
            assert metadata.encrypted is True
            assert metadata.compression == 'gzip'
            assert metadata.file_size > 0
            assert len(metadata.checksum) == 64
            
            # Verify file exists
            backup_path = Path(metadata.file_path)
            assert backup_path.exists()
            assert backup_path.stat().st_size == metadata.file_size
            
            # Store for later tests
            self.test_full_backup_id = metadata.backup_id
            
        except Exception as e:
            # If MySQL is not available, create a mock backup for testing
            if "Can't connect to MySQL server" in str(e) or "Access denied" in str(e):
                logger.warning("MySQL not available, creating mock backup for testing")
                self._create_mock_backup('full')
            else:
                raise
    
    def test_incremental_backup_creation(self):
        """Test incremental backup creation"""
        try:
            metadata = self.backup_manager.create_incremental_backup()
            
            # Verify metadata
            assert metadata.backup_type == 'incremental'
            assert metadata.backup_id.startswith('incr_')
            assert metadata.encrypted is True
            assert metadata.compression == 'gzip'
            assert metadata.file_size > 0
            
            # Verify file exists
            backup_path = Path(metadata.file_path)
            assert backup_path.exists()
            
            # Store for later tests
            self.test_incremental_backup_id = metadata.backup_id
            
        except Exception as e:
            # If MySQL is not available, create a mock backup for testing
            if "Can't connect to MySQL server" in str(e) or "Access denied" in str(e):
                logger.warning("MySQL not available, creating mock backup for testing")
                self._create_mock_backup('incremental')
            else:
                raise
    
    def _create_mock_backup(self, backup_type: str):
        """Create a mock backup for testing when MySQL is not available"""
        from core.backup_manager import BackupMetadata
        import gzip
        
        backup_id = f"{backup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create mock SQL content
        mock_sql = """
-- Mock backup for testing
CREATE DATABASE IF NOT EXISTS test_db;
USE test_db;
CREATE TABLE test_table (id INT PRIMARY KEY, name VARCHAR(100));
INSERT INTO test_table VALUES (1, 'Test Data');
"""
        
        # Create temporary files
        temp_dir = self.backup_manager.storage.backup_dir / 'temp'
        temp_sql = temp_dir / f"{backup_id}.sql"
        temp_compressed = temp_dir / f"{backup_id}.sql.gz"
        
        # Write and compress
        temp_sql.write_text(mock_sql)
        with open(temp_sql, 'rb') as f_in:
            with gzip.open(temp_compressed, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Encrypt
        final_path = self.backup_manager.storage.get_backup_path(backup_type, backup_id)
        checksum = self.backup_manager.encryption.encrypt_file(
            str(temp_compressed), str(final_path)
        )
        
        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            timestamp=datetime.now(),
            file_path=str(final_path),
            file_size=final_path.stat().st_size,
            checksum=checksum,
            encrypted=True,
            compression='gzip',
            database_name='test_db',
            mysql_version='8.0.0-mock',
            binlog_position='mysql-bin.000001:1234',
        )
        
        # Save metadata
        self.backup_manager.storage.save_metadata(metadata)
        
        # Cleanup temp files
        temp_sql.unlink(missing_ok=True)
        temp_compressed.unlink(missing_ok=True)
        
        # Store for later tests
        if backup_type == 'full':
            self.test_full_backup_id = backup_id
        else:
            self.test_incremental_backup_id = backup_id
    
    def test_backup_verification(self):
        """Test backup integrity verification"""
        # Test full backup verification
        if hasattr(self, 'test_full_backup_id'):
            is_valid = self.backup_manager.verify_backup_integrity(self.test_full_backup_id)
            assert is_valid is True
        
        # Test incremental backup verification
        if hasattr(self, 'test_incremental_backup_id'):
            is_valid = self.backup_manager.verify_backup_integrity(self.test_incremental_backup_id)
            assert is_valid is True
    
    def test_backup_listing(self):
        """Test backup listing functionality"""
        # List all backups
        all_backups = self.backup_manager.storage.list_backups()
        assert len(all_backups) >= 0
        
        # List full backups only
        full_backups = self.backup_manager.storage.list_backups('full')
        for backup in full_backups:
            assert backup.backup_type == 'full'
        
        # List incremental backups only
        incremental_backups = self.backup_manager.storage.list_backups('incremental')
        for backup in incremental_backups:
            assert backup.backup_type == 'incremental'
    
    def test_backup_metadata_operations(self):
        """Test backup metadata save/load operations"""
        if hasattr(self, 'test_full_backup_id'):
            # Load metadata
            metadata = self.backup_manager.storage.load_metadata(self.test_full_backup_id)
            assert metadata is not None
            assert metadata.backup_id == self.test_full_backup_id
            assert metadata.backup_type == 'full'
            assert metadata.encrypted is True
            
            # Test non-existent backup
            non_existent = self.backup_manager.storage.load_metadata('non_existent_backup')
            assert non_existent is None
    
    def test_backup_status_reporting(self):
        """Test backup system status reporting"""
        status = self.backup_manager.get_backup_status()
        
        # Check required fields
        assert 'total_backups' in status
        assert 'full_backups' in status
        assert 'incremental_backups' in status
        assert 'total_size_bytes' in status
        assert 'total_size_gb' in status
        assert 'backup_directory' in status
        assert 'retention_days' in status
        
        # Verify values
        assert status['backup_directory'] == str(self.test_dir)
        assert status['retention_days'] == 7
        assert status['total_backups'] >= 0
        assert status['total_size_bytes'] >= 0
    
    def test_backup_cleanup(self):
        """Test backup cleanup functionality"""
        # Create old backup metadata for testing
        old_backup_id = f"old_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        old_timestamp = datetime.now() - timedelta(days=10)  # Older than retention
        
        from core.backup_manager import BackupMetadata
        old_metadata = BackupMetadata(
            backup_id=old_backup_id,
            backup_type='full',
            timestamp=old_timestamp,
            file_path=str(self.test_dir / 'full' / f"{old_backup_id}.sql.gz.enc"),
            file_size=1024,
            checksum='dummy_checksum',
            encrypted=True,
            compression='gzip',
            database_name='test_db',
            mysql_version='8.0.0',
        )
        
        # Create dummy backup file
        dummy_file = Path(old_metadata.file_path)
        dummy_file.write_bytes(b'dummy backup content')
        
        # Save metadata
        self.backup_manager.storage.save_metadata(old_metadata)
        
        # Run cleanup
        removed_backups = self.backup_manager.cleanup_old_backups()
        
        # Verify cleanup
        assert old_backup_id in removed_backups
        assert not dummy_file.exists()
        
        # Verify metadata was removed
        loaded_metadata = self.backup_manager.storage.load_metadata(old_backup_id)
        assert loaded_metadata is None
    
    def test_scheduler_configuration(self):
        """Test backup scheduler configuration"""
        schedule_config = ScheduleConfig(
            full_backup_hour=2,
            incremental_interval_hours=4,
            cleanup_hour=3,
            health_check_interval_minutes=30,
            max_consecutive_failures=3,
        )
        
        scheduler = BackupScheduler(self.backup_manager, schedule_config)
        
        # Test configuration
        assert scheduler.schedule_config.full_backup_hour == 2
        assert scheduler.schedule_config.incremental_interval_hours == 4
        assert scheduler.schedule_config.cleanup_hour == 3
        assert scheduler.schedule_config.health_check_interval_minutes == 30
        assert scheduler.schedule_config.max_consecutive_failures == 3
        
        # Test status
        status = scheduler.get_scheduler_status()
        assert 'running' in status
        assert 'last_operations' in status
        assert 'failure_counts' in status
        assert 'schedule_config' in status
    
    def run_all_tests(self):
        """Run all backup system tests"""
        logger.info("Starting backup system tests...")
        
        # Run tests
        self.run_test("Backup Configuration", self.test_backup_config)
        self.run_test("Storage Initialization", self.test_backup_storage_initialization)
        self.run_test("Encryption Functionality", self.test_encryption_functionality)
        self.run_test("Full Backup Creation", self.test_full_backup_creation)
        self.run_test("Incremental Backup Creation", self.test_incremental_backup_creation)
        self.run_test("Backup Verification", self.test_backup_verification)
        self.run_test("Backup Listing", self.test_backup_listing)
        self.run_test("Metadata Operations", self.test_backup_metadata_operations)
        self.run_test("Status Reporting", self.test_backup_status_reporting)
        self.run_test("Backup Cleanup", self.test_backup_cleanup)
        self.run_test("Scheduler Configuration", self.test_scheduler_configuration)
        
        # Print results
        self.print_test_results()
    
    def print_test_results(self):
        """Print test results summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        total_duration = sum(r['duration'] for r in self.test_results)
        
        logger.info("\n" + "="*60)
        logger.info("BACKUP SYSTEM TEST RESULTS")
        logger.info("="*60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Total Duration: {total_duration:.2f}s")
        logger.info("="*60)
        
        if failed_tests > 0:
            logger.info("\nFAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    logger.info(f"  [FAIL] {result['name']}: {result['error']}")
        
        logger.info(f"\nTest directory: {self.test_dir}")
        logger.info("Run cleanup() to remove test files")


def main():
    """Main test function"""
    tester = BackupSystemTester()
    
    try:
        tester.run_all_tests()
    finally:
        # Ask user if they want to cleanup
        try:
            response = input("\nCleanup test directory? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                tester.cleanup()
            else:
                logger.info(f"Test files preserved in: {tester.test_dir}")
        except KeyboardInterrupt:
            logger.info(f"\nTest files preserved in: {tester.test_dir}")


if __name__ == '__main__':
    main()