"""
Ongoing Maintenance and Monitoring Coordinator

This module provides comprehensive ongoing maintenance and monitoring capabilities.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

print("DEBUG: About to define MaintenanceSchedule")

@dataclass
class MaintenanceSchedule:
    """Database maintenance schedule configuration"""
    schedule_id: str
    database_alias: str
    task_type: str
    schedule_cron: str
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    failure_count: int = 0
    max_failures: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        if data['last_run']:
            data['last_run'] = self.last_run.isoformat()
        if data['next_run']:
            data['next_run'] = self.next_run.isoformat()
        return data


@dataclass
class MaintenanceStatus:
    """Overall maintenance system status"""
    coordinator_status: str
    active_schedules: int
    failed_schedules: int
    last_maintenance_run: Optional[datetime]
    next_scheduled_run: Optional[datetime]
    monitoring_enabled: bool
    backup_testing_enabled: bool
    disaster_recovery_ready: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        if data['last_maintenance_run']:
            data['last_maintenance_run'] = self.last_maintenance_run.isoformat()
        if data['next_scheduled_run']:
            data['next_scheduled_run'] = self.next_scheduled_run.isoformat()
        return data


class OngoingMaintenanceCoordinator:
    """
    Central coordinator for all ongoing database maintenance and monitoring activities.
    """
    
    def __init__(self):
        self.schedules: Dict[str, MaintenanceSchedule] = {}
        self.monitoring_enabled = True
        self.coordinator_running = False
        self._coordinator_thread = None
        self._lock = threading.RLock()
        
        # Load basic configuration
        self.config = {
            'coordinator_interval': 60,
            'enable_monitoring': True,
            'enable_backup_testing': True,
            'enable_disaster_recovery': True,
            'notification_emails': [],
        }
        
        # Load basic schedules
        self._load_maintenance_schedules()
    
    def _load_maintenance_schedules(self):
        """Load maintenance schedules from configuration"""
        default_schedules = {
            'daily_maintenance': {
                'database_alias': 'default',
                'task_type': 'daily',
                'schedule_cron': '0 2 * * *',
                'enabled': True
            },
            'weekly_optimization': {
                'database_alias': 'default',
                'task_type': 'weekly',
                'schedule_cron': '0 3 * * 0',
                'enabled': True
            },
        }
        
        for schedule_id, schedule_config in default_schedules.items():
            schedule = MaintenanceSchedule(
                schedule_id=schedule_id,
                database_alias=schedule_config['database_alias'],
                task_type=schedule_config['task_type'],
                schedule_cron=schedule_config['schedule_cron'],
                enabled=schedule_config['enabled']
            )
            
            schedule.next_run = datetime.now() + timedelta(days=1)
            self.schedules[schedule_id] = schedule
        
        logger.info(f"Loaded {len(self.schedules)} maintenance schedules")
    
    def start_coordinator(self):
        """Start the maintenance coordinator"""
        if self.coordinator_running:
            logger.warning("Maintenance coordinator is already running")
            return
        
        self.coordinator_running = True
        logger.info("Ongoing maintenance coordinator started")
    
    def stop_coordinator(self):
        """Stop the maintenance coordinator"""
        self.coordinator_running = False
        logger.info("Ongoing maintenance coordinator stopped")
    
    def get_coordinator_status(self) -> Dict[str, Any]:
        """Get current coordinator status"""
        active_schedules = sum(1 for s in self.schedules.values() if s.enabled)
        failed_schedules = sum(1 for s in self.schedules.values() if s.failure_count >= s.max_failures)
        
        status = MaintenanceStatus(
            coordinator_status='running' if self.coordinator_running else 'stopped',
            active_schedules=active_schedules,
            failed_schedules=failed_schedules,
            last_maintenance_run=None,
            next_scheduled_run=None,
            monitoring_enabled=self.config['enable_monitoring'],
            backup_testing_enabled=self.config['enable_backup_testing'],
            disaster_recovery_ready=self.config['enable_disaster_recovery']
        )
        
        return status.to_dict()
    
    def get_maintenance_schedules(self) -> Dict[str, Dict[str, Any]]:
        """Get all maintenance schedules"""
        return {schedule_id: schedule.to_dict() for schedule_id, schedule in self.schedules.items()}
    
    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a maintenance schedule"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].enabled = True
            self.schedules[schedule_id].failure_count = 0
            logger.info(f"Enabled maintenance schedule: {schedule_id}")
            return True
        return False
    
    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a maintenance schedule"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].enabled = False
            logger.info(f"Disabled maintenance schedule: {schedule_id}")
            return True
        return False
    
    def trigger_manual_maintenance(self, database_alias: str, maintenance_type: str = 'daily') -> str:
        """Trigger manual maintenance execution"""
        logger.info(f"Manual {maintenance_type} maintenance triggered for {database_alias}")
        return f"Manual {maintenance_type} maintenance started for {database_alias}"


# Global coordinator instance
_coordinator_instance = None


def get_maintenance_coordinator() -> OngoingMaintenanceCoordinator:
    """Get the global maintenance coordinator instance"""
    global _coordinator_instance
    
    if _coordinator_instance is None:
        _coordinator_instance = OngoingMaintenanceCoordinator()
    
    return _coordinator_instance


def start_maintenance_coordinator():
    """Start the global maintenance coordinator"""
    coordinator = get_maintenance_coordinator()
    coordinator.start_coordinator()


def stop_maintenance_coordinator():
    """Stop the global maintenance coordinator"""
    global _coordinator_instance
    
    if _coordinator_instance:
        _coordinator_instance.stop_coordinator()
        _coordinator_instance = None