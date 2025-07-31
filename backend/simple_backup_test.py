#!/usr/bin/env python
"""
Simple backup system test without Django dependencies

This script tests the backup system functionality without loading Django,
avoiding the connection monitoring and read replica issues.
"""

import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Configure logging for Windows console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Simple backup configuration
class SimpleBackupConfig:
    def __init__(self):
        self.backup_dir = tempfile.mkdtemp(prefix='backup_test_')
        self.encryption_key = 'test-encryption-key-for-testing-only'
        self.retention_days = 7
        self.compression_enabled = True
        self.verify_backups = True

def test_mysqldump_connection():
    """Test if mysqldump can connect to the database"""
    logger.info("Testing mysqldump connection...")
    
    try:
        import subprocess
        
        # Test mysqldump connection
        cmd = [
            'mysqldump',
            '--host=localhost',
            '--port=3307',
            '--user=root',
            '--password=root',
            '--single-transaction',
            '--no-data',  # Only structure, no data for test
            'ecommerce_db'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("[PASS] mysqldump connection test successful")
            return True
        else:
            logger.error(f"[FAIL] mysqldump failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"[FAIL] mysqldump test failed: {e}")
        return False

def test_mysql_connection():
    """Test direct MySQL connection"""
    logger.info("Testing direct MySQL connection...")
    
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host='localhost',
            port=3307,
            user='root',
            password='root',
            database='ecommerce_db'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        logger.info(f"[PASS] MySQL connection successful - Version: {version}")
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] MySQL connection failed: {e}")
        return False

def test_backup_encryption():
    """Test backup encryption functionality"""
    logger.info("Testing backup encryption...")
    
    try:
        from cryptography.fernet import Fernet
        import hashlib
        import base64
        
        # Create encryption key
        key_string = 'test-encryption-key-for-testing-only'
        key_bytes = key_string.encode('utf-8')
        hashed_key = hashlib.sha256(key_bytes).digest()
        encryption_key = base64.urlsafe_b64encode(hashed_key)
        
        cipher = Fernet(encryption_key)
        
        # Test data
        test_data = b"This is test backup data for encryption testing"
        
        # Encrypt
        encrypted_data = cipher.encrypt(test_data)
        
        # Decrypt
        decrypted_data = cipher.decrypt(encrypted_data)
        
        if decrypted_data == test_data:
            logger.info("[PASS] Backup encryption test successful")
            return True
        else:
            logger.error("[FAIL] Decrypted data doesn't match original")
            return False
            
    except Exception as e:
        logger.error(f"[FAIL] Encryption test failed: {e}")
        return False

def test_backup_creation():
    """Test actual backup creation"""
    logger.info("Testing backup creation...")
    
    try:
        import subprocess
        import gzip
        
        # Create temporary directory
        test_dir = Path(tempfile.mkdtemp(prefix='backup_test_'))
        backup_file = test_dir / 'test_backup.sql'
        compressed_file = test_dir / 'test_backup.sql.gz'
        
        try:
            # Create backup using mysqldump
            cmd = [
                'mysqldump',
                '--host=localhost',
                '--port=3307',
                '--user=root',
                '--password=root',
                '--single-transaction',
                '--routines',
                '--triggers',
                '--hex-blob',
                '--default-character-set=utf8mb4',
                'ecommerce_db'
            ]
            
            with open(backup_file, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=60
                )
            
            if result.returncode != 0:
                raise Exception(f"mysqldump failed: {result.stderr}")
            
            # Check if backup file was created and has content
            if not backup_file.exists() or backup_file.stat().st_size == 0:
                raise Exception("Backup file is empty or doesn't exist")
            
            # Test compression
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            if not compressed_file.exists():
                raise Exception("Compressed backup file wasn't created")
            
            # Test decompression
            with gzip.open(compressed_file, 'rb') as f_in:
                decompressed_content = f_in.read()
            
            original_content = backup_file.read_bytes()
            
            if decompressed_content != original_content:
                raise Exception("Decompressed content doesn't match original")
            
            backup_size = backup_file.stat().st_size
            compressed_size = compressed_file.stat().st_size
            compression_ratio = (1 - compressed_size / backup_size) * 100
            
            logger.info(f"[PASS] Backup creation successful")
            logger.info(f"  Original size: {backup_size:,} bytes")
            logger.info(f"  Compressed size: {compressed_size:,} bytes")
            logger.info(f"  Compression ratio: {compression_ratio:.1f}%")
            
            return True
            
        finally:
            # Cleanup
            shutil.rmtree(test_dir, ignore_errors=True)
            
    except Exception as e:
        logger.error(f"[FAIL] Backup creation failed: {e}")
        return False

def test_backup_restore():
    """Test backup restore functionality"""
    logger.info("Testing backup restore...")
    
    try:
        import subprocess
        
        # Create a test database for restore testing
        test_db_name = f"test_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Create test database
            create_db_cmd = [
                'mysql',
                '--host=localhost',
                '--port=3307',
                '--user=root',
                '--password=root',
                '-e',
                f'CREATE DATABASE {test_db_name}'
            ]
            
            result = subprocess.run(
                create_db_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to create test database: {result.stderr}")
            
            # Create a simple backup
            test_dir = Path(tempfile.mkdtemp(prefix='restore_test_'))
            backup_file = test_dir / 'restore_test.sql'
            
            # Create backup of original database
            backup_cmd = [
                'mysqldump',
                '--host=localhost',
                '--port=3307',
                '--user=root',
                '--password=root',
                '--single-transaction',
                'ecommerce_db'
            ]
            
            with open(backup_file, 'w') as f:
                result = subprocess.run(
                    backup_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=60
                )
            
            if result.returncode != 0:
                raise Exception(f"Backup creation failed: {result.stderr}")
            
            # Restore to test database
            restore_cmd = [
                'mysql',
                '--host=localhost',
                '--port=3307',
                '--user=root',
                '--password=root',
                test_db_name
            ]
            
            with open(backup_file, 'r') as f:
                result = subprocess.run(
                    restore_cmd,
                    stdin=f,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            
            if result.returncode != 0:
                raise Exception(f"Restore failed: {result.stderr}")
            
            logger.info("[PASS] Backup restore test successful")
            return True
            
        finally:
            # Cleanup test database
            try:
                drop_db_cmd = [
                    'mysql',
                    '--host=localhost',
                    '--port=3307',
                    '--user=root',
                    '--password=root',
                    '-e',
                    f'DROP DATABASE IF EXISTS {test_db_name}'
                ]
                subprocess.run(drop_db_cmd, capture_output=True, timeout=30)
            except:
                pass
            
            # Cleanup files
            try:
                shutil.rmtree(test_dir, ignore_errors=True)
            except:
                pass
                
    except Exception as e:
        logger.error(f"[FAIL] Backup restore failed: {e}")
        return False

def main():
    """Run all backup system tests"""
    logger.info("Starting simple backup system tests...")
    logger.info("=" * 50)
    
    tests = [
        ("MySQL Connection", test_mysql_connection),
        ("mysqldump Connection", test_mysqldump_connection),
        ("Backup Encryption", test_backup_encryption),
        ("Backup Creation", test_backup_creation),
        ("Backup Restore", test_backup_restore),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        logger.info("-" * 30)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"[FAIL] {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        if success:
            logger.info(f"[PASS] {test_name}")
            passed += 1
        else:
            logger.info(f"[FAIL] {test_name}")
            failed += 1
    
    logger.info("-" * 50)
    logger.info(f"Total Tests: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("All tests passed! Backup system is working correctly.")
    else:
        logger.info(f"{failed} test(s) failed. Please check the errors above.")
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)