"""
Backup Manager

This module provides comprehensive backup and recovery functionality
for database operations during migration.
"""

import os
import shutil
import sqlite3
import subprocess
from datetime import datetime
from django.conf import settings


class BackupManager:
    """Manager for database backup and recovery operations"""
    
    def __init__(self):
        self.backup_dir = getattr(settings, 'BACKUP_STORAGE_PATH', '/var/backups/mysql')
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_sqlite_backup(self):
        """Create backup of SQLite database"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"sqlite_backup_{timestamp}.sqlite3"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy SQLite database file
            sqlite_db_path = settings.DATABASES['default']['NAME']
            if os.path.exists(sqlite_db_path):
                shutil.copy2(sqlite_db_path, backup_path)
                print(f"SQLite backup created: {backup_path}")
                return backup_path
            else:
                raise FileNotFoundError(f"SQLite database not found: {sqlite_db_path}")
                
        except Exception as e:
            print(f"Error creating SQLite backup: {e}")
            raise
    
    def create_mysql_backup(self):
        """Create backup of MySQL database"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"mysql_backup_{timestamp}.sql"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Get MySQL connection details
            db_config = settings.DATABASES['default']
            
            # Create mysqldump command
            cmd = [
                'mysqldump',
                f"--host={db_config.get('HOST', 'localhost')}",
                f"--port={db_config.get('PORT', 3306)}",
                f"--user={db_config['USER']}",
                f"--password={db_config['PASSWORD']}",
                '--single-transaction',
                '--routines',
                '--triggers',
                db_config['NAME']
            ]
            
            # Execute mysqldump
            with open(backup_path, 'w') as backup_file:
                result = subprocess.run(cmd, stdout=backup_file, stderr=subprocess.PIPE, text=True)
                
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
            
            print(f"MySQL backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"Error creating MySQL backup: {e}")
            raise
    
    def verify_backup_integrity(self, backup_file):
        """Verify backup file integrity"""
        try:
            if not os.path.exists(backup_file):
                return False
            
            # Check file size
            file_size = os.path.getsize(backup_file)
            if file_size == 0:
                return False
            
            # For SQLite backups, try to open the database
            if backup_file.endswith('.sqlite3'):
                try:
                    conn = sqlite3.connect(backup_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()
                    return len(tables) > 0
                except sqlite3.Error:
                    return False
            
            # For SQL dumps, check if file contains SQL statements
            elif backup_file.endswith('.sql'):
                with open(backup_file, 'r') as f:
                    content = f.read(1000)  # Read first 1000 characters
                    return 'CREATE TABLE' in content or 'INSERT INTO' in content
            
            return True
            
        except Exception as e:
            print(f"Error verifying backup integrity: {e}")
            return False
    
    def restore_sqlite_backup(self, backup_file):
        """Restore SQLite database from backup"""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # Verify backup integrity
            if not self.verify_backup_integrity(backup_file):
                raise ValueError(f"Backup file is corrupted: {backup_file}")
            
            # Get current database path
            current_db_path = settings.DATABASES['default']['NAME']
            
            # Create backup of current database
            if os.path.exists(current_db_path):
                backup_current = f"{current_db_path}.pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(current_db_path, backup_current)
                print(f"Current database backed up to: {backup_current}")
            
            # Restore from backup
            shutil.copy2(backup_file, current_db_path)
            print(f"Database restored from: {backup_file}")
            
            return True
            
        except Exception as e:
            print(f"Error restoring SQLite backup: {e}")
            raise
    
    def restore_mysql_backup(self, backup_file):
        """Restore MySQL database from backup"""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # Verify backup integrity
            if not self.verify_backup_integrity(backup_file):
                raise ValueError(f"Backup file is corrupted: {backup_file}")
            
            # Get MySQL connection details
            db_config = settings.DATABASES['default']
            
            # Create mysql restore command
            cmd = [
                'mysql',
                f"--host={db_config.get('HOST', 'localhost')}",
                f"--port={db_config.get('PORT', 3306)}",
                f"--user={db_config['USER']}",
                f"--password={db_config['PASSWORD']}",
                db_config['NAME']
            ]
            
            # Execute mysql restore
            with open(backup_file, 'r') as backup_file_handle:
                result = subprocess.run(cmd, stdin=backup_file_handle, stderr=subprocess.PIPE, text=True)
                
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
            
            print(f"MySQL database restored from: {backup_file}")
            return True
            
        except Exception as e:
            print(f"Error restoring MySQL backup: {e}")
            raise
    
    def list_backups(self):
        """List available backups"""
        try:
            backups = []
            
            if os.path.exists(self.backup_dir):
                for filename in os.listdir(self.backup_dir):
                    if filename.endswith(('.sqlite3', '.sql')):
                        file_path = os.path.join(self.backup_dir, filename)
                        file_stat = os.stat(file_path)
                        
                        backups.append({
                            'filename': filename,
                            'path': file_path,
                            'size': file_stat.st_size,
                            'created': datetime.fromtimestamp(file_stat.st_ctime),
                            'modified': datetime.fromtimestamp(file_stat.st_mtime)
                        })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            return backups
            
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []
    
    def cleanup_old_backups(self, retention_days=30):
        """Clean up old backup files"""
        try:
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
            removed_count = 0
            
            if os.path.exists(self.backup_dir):
                for filename in os.listdir(self.backup_dir):
                    if filename.endswith(('.sqlite3', '.sql')):
                        file_path = os.path.join(self.backup_dir, filename)
                        file_stat = os.stat(file_path)
                        
                        if file_stat.st_ctime < cutoff_time:
                            os.remove(file_path)
                            removed_count += 1
                            print(f"Removed old backup: {filename}")
            
            print(f"Cleanup completed. Removed {removed_count} old backup files.")
            return removed_count
            
        except Exception as e:
            print(f"Error cleaning up old backups: {e}")
            return 0