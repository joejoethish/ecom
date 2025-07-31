"""
Backup Scheduler Service

This module provides automated scheduling for database backups including:
- Scheduled full and incremental backups
- Backup monitoring and alerting
- Automatic cleanup of old backups
- Health checks and status reporting

Requirements covered:
- 3.1: Automated daily full backups and hourly incremental backups
- 3.5: Automatic cleanup of old backups according to retention policies
- 3.6: Alert administrators of backup failures or issues
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from core.backup_manager import MySQLBackupManager, BackupConfig


logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    """Configuration for backup scheduling"""
    full_backup_hour: int = 2  # 2 AM
    full_backup_minute: int = 0
    incremental_interval_hours: int = 4
    cleanup_hour: int = 3  # 3 AM
    cleanup_minute: int = 0
    health_check_interval_minutes: int = 30
    max_consecutive_failures: int = 3
    alert_email_recipients: List[str] = None
    alert_on_failure: bool = True
    alert_on_success: bool = False


class BackupAlert:
    """Handle backup alerts and notifications"""
    
    def __init__(self, config: ScheduleConfig):
        self.config = config
        self.recipients = config.alert_email_recipients or []
    
    def send_alert(self, subject: str, message: str, level: str = 'info'):
        """Send alert notification"""
        try:
            if not self.recipients:
                logger.warning("No alert recipients configured")
                return
            
            # Log the alert
            log_method = getattr(logger, level.lower(), logger.info)
            log_method(f"BACKUP ALERT: {subject} - {message}")
            
            # Send email if configured
            if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                full_message = f"""
Backup System Alert

Level: {level.upper()}
Time: {datetime.now().isoformat()}
Subject: {subject}

Message:
{message}

This is an automated message from the backup system.
"""
                
                send_mail(
                    subject=f"[Backup Alert] {subject}",
                    message=full_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'backup@system.local'),
                    recipient_list=self.recipients,
                    fail_silently=True
                )
            
        except Exception as e:
            logger.error(f"Failed to send backup alert: {e}")
    
    def alert_backup_success(self, backup_type: str, backup_id: str, size_mb: float):
        """Alert on successful backup"""
        if self.config.alert_on_success:
            self.send_alert(
                subject=f"{backup_type.title()} Backup Successful",
                message=f"Backup {backup_id} completed successfully. Size: {size_mb:.2f} MB",
                level='info'
            )
    
    def alert_backup_failure(self, backup_type: str, error: str):
        """Alert on backup failure"""
        if self.config.alert_on_failure:
            self.send_alert(
                subject=f"{backup_type.title()} Backup Failed",
                message=f"Backup operation failed with error: {error}",
                level='error'
            )
    
    def alert_verification_failure(self, backup_id: str):
        """Alert on backup verification failure"""
        self.send_alert(
            subject="Backup Verification Failed",
            message=f"Backup {backup_id} failed integrity verification",
            level='error'
        )
    
    def alert_cleanup_completed(self, removed_count: int, freed_space_mb: float):
        """Alert on cleanup completion"""
        if removed_count > 0:
            self.send_alert(
                subject="Backup Cleanup Completed",
                message=f"Removed {removed_count} old backups, freed {freed_space_mb:.2f} MB",
                level='info'
            )
    
    def alert_system_health(self, status: Dict):
        """Alert on system health issues"""
        issues = []
        
        if not status.get('recent_full_backup', False):
            issues.append("No recent full backup (>24 hours)")
        
        if not status.get('recent_incremental_backup', False):
            issues.append("No recent incremental backup (>4 hours)")
        
        if status.get('total_size_gb', 0) > 100:  # Alert if backups exceed 100GB
            issues.append(f"Backup storage usage high: {status['total_size_gb']:.2f} GB")
        
        if issues:
            self.send_alert(
                subject="Backup System Health Issues",
                message="The following issues were detected:\n" + "\n".join(f"- {issue}" for issue in issues),
                level='warning'
            )


class BackupScheduler:
    """Main backup scheduler service"""
    
    def __init__(self, backup_manager: MySQLBackupManager, schedule_config: ScheduleConfig):
        self.backup_manager = backup_manager
        self.schedule_config = schedule_config
        self.alert_manager = BackupAlert(schedule_config)
        self.running = False
        self.scheduler_thread = None
        self.failure_counts = {
            'full_backup': 0,
            'incremental_backup': 0,
            'cleanup': 0
        }
        self.last_operations = {
            'full_backup': None,
            'incremental_backup': None,
            'cleanup': None,
            'health_check': None
        }
    
    def start(self):
        """Start the backup scheduler"""
        if self.running:
            logger.warning("Backup scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Backup scheduler started")
    
    def stop(self):
        """Stop the backup scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=30)
        logger.info("Backup scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Backup scheduler loop started")
        
        while self.running:
            try:
                now = datetime.now()
                
                # Check for full backup schedule
                if self._should_run_full_backup(now):
                    self._run_full_backup()
                
                # Check for incremental backup schedule
                if self._should_run_incremental_backup(now):
                    self._run_incremental_backup()
                
                # Check for cleanup schedule
                if self._should_run_cleanup(now):
                    self._run_cleanup()
                
                # Check for health check schedule
                if self._should_run_health_check(now):
                    self._run_health_check()
                
                # Sleep for 1 minute before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in backup scheduler loop: {e}")
                time.sleep(60)  # Continue after error
    
    def _should_run_full_backup(self, now: datetime) -> bool:
        """Check if full backup should run"""
        if (now.hour == self.schedule_config.full_backup_hour and 
            now.minute == self.schedule_config.full_backup_minute):
            
            last_run = self.last_operations.get('full_backup')
            if not last_run or (now - last_run).days >= 1:
                return True
        
        return False
    
    def _should_run_incremental_backup(self, now: datetime) -> bool:
        """Check if incremental backup should run"""
        last_run = self.last_operations.get('incremental_backup')
        if not last_run:
            return True  # Run immediately if never run
        
        hours_since_last = (now - last_run).total_seconds() / 3600
        return hours_since_last >= self.schedule_config.incremental_interval_hours
    
    def _should_run_cleanup(self, now: datetime) -> bool:
        """Check if cleanup should run"""
        if (now.hour == self.schedule_config.cleanup_hour and 
            now.minute == self.schedule_config.cleanup_minute):
            
            last_run = self.last_operations.get('cleanup')
            if not last_run or (now - last_run).days >= 1:
                return True
        
        return False
    
    def _should_run_health_check(self, now: datetime) -> bool:
        """Check if health check should run"""
        last_run = self.last_operations.get('health_check')
        if not last_run:
            return True
        
        minutes_since_last = (now - last_run).total_seconds() / 60
        return minutes_since_last >= self.schedule_config.health_check_interval_minutes
    
    def _run_full_backup(self):
        """Execute full backup"""
        logger.info("Starting scheduled full backup")
        
        try:
            metadata = self.backup_manager.create_full_backup()
            size_mb = metadata.file_size / (1024 * 1024)
            
            # Verify backup integrity
            if self.backup_manager.config.verify_backups:
                if not self.backup_manager.verify_backup_integrity(metadata.backup_id):
                    raise Exception("Backup verification failed")
            
            self.failure_counts['full_backup'] = 0
            self.last_operations['full_backup'] = datetime.now()
            
            self.alert_manager.alert_backup_success('full', metadata.backup_id, size_mb)
            logger.info(f"Scheduled full backup completed: {metadata.backup_id}")
            
        except Exception as e:
            self.failure_counts['full_backup'] += 1
            error_msg = str(e)
            
            logger.error(f"Scheduled full backup failed: {error_msg}")
            self.alert_manager.alert_backup_failure('full', error_msg)
            
            # Alert if too many consecutive failures
            if self.failure_counts['full_backup'] >= self.schedule_config.max_consecutive_failures:
                self.alert_manager.send_alert(
                    subject="Critical: Multiple Full Backup Failures",
                    message=f"Full backup has failed {self.failure_counts['full_backup']} consecutive times. "
                           f"Latest error: {error_msg}",
                    level='critical'
                )
    
    def _run_incremental_backup(self):
        """Execute incremental backup"""
        logger.info("Starting scheduled incremental backup")
        
        try:
            metadata = self.backup_manager.create_incremental_backup()
            size_mb = metadata.file_size / (1024 * 1024)
            
            # Verify backup integrity
            if self.backup_manager.config.verify_backups:
                if not self.backup_manager.verify_backup_integrity(metadata.backup_id):
                    raise Exception("Backup verification failed")
            
            self.failure_counts['incremental_backup'] = 0
            self.last_operations['incremental_backup'] = datetime.now()
            
            self.alert_manager.alert_backup_success('incremental', metadata.backup_id, size_mb)
            logger.info(f"Scheduled incremental backup completed: {metadata.backup_id}")
            
        except Exception as e:
            self.failure_counts['incremental_backup'] += 1
            error_msg = str(e)
            
            logger.error(f"Scheduled incremental backup failed: {error_msg}")
            self.alert_manager.alert_backup_failure('incremental', error_msg)
            
            # Alert if too many consecutive failures
            if self.failure_counts['incremental_backup'] >= self.schedule_config.max_consecutive_failures:
                self.alert_manager.send_alert(
                    subject="Critical: Multiple Incremental Backup Failures",
                    message=f"Incremental backup has failed {self.failure_counts['incremental_backup']} consecutive times. "
                           f"Latest error: {error_msg}",
                    level='critical'
                )
    
    def _run_cleanup(self):
        """Execute backup cleanup"""
        logger.info("Starting scheduled backup cleanup")
        
        try:
            # Get current status for space calculation
            status_before = self.backup_manager.get_backup_status()
            size_before = status_before.get('total_size_bytes', 0)
            
            removed_backups = self.backup_manager.cleanup_old_backups()
            
            # Calculate freed space
            status_after = self.backup_manager.get_backup_status()
            size_after = status_after.get('total_size_bytes', 0)
            freed_space_mb = (size_before - size_after) / (1024 * 1024)
            
            self.failure_counts['cleanup'] = 0
            self.last_operations['cleanup'] = datetime.now()
            
            self.alert_manager.alert_cleanup_completed(len(removed_backups), freed_space_mb)
            logger.info(f"Scheduled cleanup completed: removed {len(removed_backups)} backups")
            
        except Exception as e:
            self.failure_counts['cleanup'] += 1
            error_msg = str(e)
            
            logger.error(f"Scheduled cleanup failed: {error_msg}")
            self.alert_manager.send_alert(
                subject="Backup Cleanup Failed",
                message=f"Backup cleanup failed with error: {error_msg}",
                level='error'
            )
    
    def _run_health_check(self):
        """Execute system health check"""
        try:
            status = self.backup_manager.get_backup_status()
            self.last_operations['health_check'] = datetime.now()
            
            # Check for health issues and alert if necessary
            self.alert_manager.alert_system_health(status)
            
            logger.debug("Health check completed")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def get_scheduler_status(self) -> Dict:
        """Get scheduler status information"""
        return {
            'running': self.running,
            'last_operations': {
                k: v.isoformat() if v else None 
                for k, v in self.last_operations.items()
            },
            'failure_counts': self.failure_counts.copy(),
            'schedule_config': {
                'full_backup_time': f"{self.schedule_config.full_backup_hour:02d}:{self.schedule_config.full_backup_minute:02d}",
                'incremental_interval_hours': self.schedule_config.incremental_interval_hours,
                'cleanup_time': f"{self.schedule_config.cleanup_hour:02d}:{self.schedule_config.cleanup_minute:02d}",
                'health_check_interval_minutes': self.schedule_config.health_check_interval_minutes,
            }
        }
    
    def force_full_backup(self) -> bool:
        """Force immediate full backup"""
        try:
            self._run_full_backup()
            return True
        except Exception as e:
            logger.error(f"Forced full backup failed: {e}")
            return False
    
    def force_incremental_backup(self) -> bool:
        """Force immediate incremental backup"""
        try:
            self._run_incremental_backup()
            return True
        except Exception as e:
            logger.error(f"Forced incremental backup failed: {e}")
            return False
    
    def force_cleanup(self) -> bool:
        """Force immediate cleanup"""
        try:
            self._run_cleanup()
            return True
        except Exception as e:
            logger.error(f"Forced cleanup failed: {e}")
            return False


# Global scheduler instance
_scheduler_instance = None


def get_backup_scheduler() -> Optional[BackupScheduler]:
    """Get the global backup scheduler instance"""
    return _scheduler_instance


def initialize_backup_scheduler():
    """Initialize the global backup scheduler"""
    global _scheduler_instance
    
    if _scheduler_instance is not None:
        logger.warning("Backup scheduler already initialized")
        return _scheduler_instance
    
    try:
        import os
        # Get configuration from Django settings
        backup_dir = getattr(settings, 'BACKUP_DIR', 
                           os.path.join(settings.BASE_DIR, 'backups'))
        encryption_key = getattr(settings, 'BACKUP_ENCRYPTION_KEY', 
                                'default-key-change-in-production')
        
        backup_config = BackupConfig(
            backup_dir=backup_dir,
            encryption_key=encryption_key,
            retention_days=getattr(settings, 'BACKUP_RETENTION_DAYS', 30),
            compression_enabled=getattr(settings, 'BACKUP_COMPRESSION_ENABLED', True),
            verify_backups=getattr(settings, 'BACKUP_VERIFY_ENABLED', True),
        )
        
        schedule_config = ScheduleConfig(
            full_backup_hour=getattr(settings, 'BACKUP_FULL_HOUR', 2),
            full_backup_minute=getattr(settings, 'BACKUP_FULL_MINUTE', 0),
            incremental_interval_hours=getattr(settings, 'BACKUP_INCREMENTAL_INTERVAL', 4),
            cleanup_hour=getattr(settings, 'BACKUP_CLEANUP_HOUR', 3),
            cleanup_minute=getattr(settings, 'BACKUP_CLEANUP_MINUTE', 0),
            health_check_interval_minutes=getattr(settings, 'BACKUP_HEALTH_CHECK_INTERVAL', 30),
            max_consecutive_failures=getattr(settings, 'BACKUP_MAX_FAILURES', 3),
            alert_email_recipients=getattr(settings, 'BACKUP_ALERT_RECIPIENTS', []),
            alert_on_failure=getattr(settings, 'BACKUP_ALERT_ON_FAILURE', True),
            alert_on_success=getattr(settings, 'BACKUP_ALERT_ON_SUCCESS', False),
        )
        
        backup_manager = MySQLBackupManager(backup_config)
        _scheduler_instance = BackupScheduler(backup_manager, schedule_config)
        
        logger.info("Backup scheduler initialized successfully")
        return _scheduler_instance
        
    except Exception as e:
        logger.error(f"Failed to initialize backup scheduler: {e}")
        return None


def start_backup_scheduler():
    """Start the backup scheduler service"""
    scheduler = get_backup_scheduler()
    if scheduler is None:
        scheduler = initialize_backup_scheduler()
    
    if scheduler:
        scheduler.start()
    else:
        logger.error("Cannot start backup scheduler - initialization failed")


def stop_backup_scheduler():
    """Stop the backup scheduler service"""
    scheduler = get_backup_scheduler()
    if scheduler:
        scheduler.stop()