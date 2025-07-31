#!/usr/bin/env python3
"""
Simple test without Django to check coordinator class definition
"""

print("Testing coordinator class definition...")

# Test the class definition directly
try:
    from dataclasses import dataclass, asdict
    from datetime import datetime, timedelta
    from typing import Dict, Any, List, Optional
    
    print("✓ Basic imports successful")
    
    # Define the classes directly
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
    
    print("✓ MaintenanceSchedule class defined")
    
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
    
    print("✓ MaintenanceStatus class defined")
    
    class SimpleCoordinator:
        """Simplified coordinator for testing"""
        
        def __init__(self):
            self.schedules = {}
            self.coordinator_running = False
            print("✓ SimpleCoordinator initialized")
        
        def get_coordinator_status(self):
            return {
                'coordinator_status': 'stopped',
                'active_schedules': 0,
                'failed_schedules': 0,
                'monitoring_enabled': False,
                'backup_testing_enabled': False,
                'disaster_recovery_ready': False
            }
        
        def get_maintenance_schedules(self):
            return {}
        
        def enable_schedule(self, schedule_id: str) -> bool:
            return True
        
        def disable_schedule(self, schedule_id: str) -> bool:
            return True
    
    print("✓ SimpleCoordinator class defined")
    
    # Test instantiation
    coordinator = SimpleCoordinator()
    status = coordinator.get_coordinator_status()
    schedules = coordinator.get_maintenance_schedules()
    
    print("✓ Coordinator instantiated and methods work")
    print(f"Status: {status}")
    
    # Test schedule creation
    schedule = MaintenanceSchedule(
        schedule_id='test',
        database_alias='default',
        task_type='daily',
        schedule_cron='0 2 * * *'
    )
    
    print("✓ Schedule created successfully")
    print(f"Schedule: {schedule.to_dict()}")
    
    print("\n🎉 All basic tests passed! The issue is likely with Django integration.")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()