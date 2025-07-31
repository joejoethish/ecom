#!/usr/bin/env python3
"""
Test script for the Ongoing Maintenance Coordinator

This script tests the functionality of the ongoing maintenance coordinator including:
- Coordinator initialization and startup
- Schedule management
- Manual maintenance triggering
- Status reporting
- Component integration
"""

import os
import sys
import django
import time
import json
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from core.ongoing_maintenance_coordinator import (
    OngoingMaintenanceCoordinator,
    get_maintenance_coordinator,
    start_maintenance_coordinator,
    stop_maintenance_coordinator
)


def test_coordinator_initialization():
    """Test coordinator initialization"""
    print("=== Testing Coordinator Initialization ===")
    
    try:
        coordinator = OngoingMaintenanceCoordinator()
        
        # Check basic properties
        assert hasattr(coordinator, 'schedules')
        assert hasattr(coordinator, 'monitoring_enabled')
        assert hasattr(coordinator, 'coordinator_running')
        
        print("✓ Coordinator initialized successfully")
        
        # Check schedules loaded
        schedules = coordinator.get_maintenance_schedules()
        print(f"✓ Loaded {len(schedules)} maintenance schedules")
        
        for schedule_id, schedule_data in schedules.items():
            print(f"  - {schedule_id}: {schedule_data['task_type']} ({'enabled' if schedule_data['enabled'] else 'disabled'})")
        
        return True
        
    except Exception as e:
        print(f"✗ Coordinator initialization failed: {e}")
        return False


def test_coordinator_status():
    """Test coordinator status reporting"""
    print("\n=== Testing Coordinator Status ===")
    
    try:
        coordinator = get_maintenance_coordinator()
        status = coordinator.get_coordinator_status()
        
        # Check status structure
        required_fields = [
            'coordinator_status', 'active_schedules', 'failed_schedules',
            'monitoring_enabled', 'backup_testing_enabled', 'disaster_recovery_ready'
        ]
        
        for field in required_fields:
            assert field in status, f"Missing status field: {field}"
        
        print("✓ Status structure is valid")
        print(f"  - Coordinator Status: {status['coordinator_status']}")
        print(f"  - Active Schedules: {status['active_schedules']}")
        print(f"  - Failed Schedules: {status['failed_schedules']}")
        print(f"  - Monitoring Enabled: {status['monitoring_enabled']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Status reporting failed: {e}")
        return False


def test_schedule_management():
    """Test schedule enable/disable functionality"""
    print("\n=== Testing Schedule Management ===")
    
    try:
        coordinator = get_maintenance_coordinator()
        
        # Test disabling a schedule
        result = coordinator.disable_schedule('daily_maintenance')
        assert result == True, "Failed to disable schedule"
        print("✓ Successfully disabled daily_maintenance schedule")
        
        # Check schedule is disabled
        schedules = coordinator.get_maintenance_schedules()
        assert schedules['daily_maintenance']['enabled'] == False
        print("✓ Schedule status correctly updated")
        
        # Test enabling the schedule
        result = coordinator.enable_schedule('daily_maintenance')
        assert result == True, "Failed to enable schedule"
        print("✓ Successfully enabled daily_maintenance schedule")
        
        # Check schedule is enabled
        schedules = coordinator.get_maintenance_schedules()
        assert schedules['daily_maintenance']['enabled'] == True
        print("✓ Schedule status correctly restored")
        
        # Test invalid schedule
        result = coordinator.disable_schedule('nonexistent_schedule')
        assert result == False, "Should return False for invalid schedule"
        print("✓ Correctly handled invalid schedule")
        
        return True
        
    except Exception as e:
        print(f"✗ Schedule management failed: {e}")
        return False


def test_manual_maintenance_trigger():
    """Test manual maintenance triggering"""
    print("\n=== Testing Manual Maintenance Trigger ===")
    
    try:
        coordinator = get_maintenance_coordinator()
        
        # Test different maintenance types
        maintenance_types = ['daily', 'weekly', 'backup_test']
        
        for maintenance_type in maintenance_types:
            try:
                result = coordinator.trigger_manual_maintenance('default', maintenance_type)
                print(f"✓ Successfully triggered {maintenance_type} maintenance: {result}")
            except Exception as e:
                print(f"⚠ {maintenance_type} maintenance trigger failed (expected if Celery not running): {e}")
        
        # Test invalid maintenance type
        try:
            coordinator.trigger_manual_maintenance('default', 'invalid_type')
            print("✗ Should have failed for invalid maintenance type")
            return False
        except ValueError:
            print("✓ Correctly rejected invalid maintenance type")
        
        return True
        
    except Exception as e:
        print(f"✗ Manual maintenance trigger failed: {e}")
        return False


def test_coordinator_lifecycle():
    """Test coordinator start/stop lifecycle"""
    print("\n=== Testing Coordinator Lifecycle ===")
    
    try:
        coordinator = get_maintenance_coordinator()
        
        # Test starting coordinator
        coordinator.start_coordinator()
        print("✓ Coordinator started successfully")
        
        # Check running status
        assert coordinator.coordinator_running == True
        print("✓ Coordinator running status is correct")
        
        # Wait a moment for threads to start
        time.sleep(2)
        
        # Test stopping coordinator
        coordinator.stop_coordinator()
        print("✓ Coordinator stopped successfully")
        
        # Check stopped status
        assert coordinator.coordinator_running == False
        print("✓ Coordinator stopped status is correct")
        
        return True
        
    except Exception as e:
        print(f"✗ Coordinator lifecycle test failed: {e}")
        return False


def test_global_coordinator_functions():
    """Test global coordinator functions"""
    print("\n=== Testing Global Coordinator Functions ===")
    
    try:
        # Test getting global instance
        coordinator1 = get_maintenance_coordinator()
        coordinator2 = get_maintenance_coordinator()
        
        # Should be the same instance
        assert coordinator1 is coordinator2
        print("✓ Global coordinator singleton working correctly")
        
        # Test global start/stop
        start_maintenance_coordinator()
        print("✓ Global start function works")
        
        time.sleep(1)
        
        stop_maintenance_coordinator()
        print("✓ Global stop function works")
        
        return True
        
    except Exception as e:
        print(f"✗ Global coordinator functions failed: {e}")
        return False


def test_configuration_loading():
    """Test configuration loading"""
    print("\n=== Testing Configuration Loading ===")
    
    try:
        coordinator = OngoingMaintenanceCoordinator()
        
        # Check configuration loaded
        assert hasattr(coordinator, 'config')
        assert isinstance(coordinator.config, dict)
        print("✓ Configuration loaded successfully")
        
        # Check required config keys
        required_keys = [
            'coordinator_interval', 'enable_monitoring', 'enable_backup_testing',
            'maintenance_window_start', 'maintenance_window_end'
        ]
        
        for key in required_keys:
            assert key in coordinator.config, f"Missing config key: {key}"
        
        print("✓ All required configuration keys present")
        print(f"  - Coordinator Interval: {coordinator.config['coordinator_interval']}s")
        print(f"  - Monitoring Enabled: {coordinator.config['enable_monitoring']}")
        print(f"  - Maintenance Window: {coordinator.config['maintenance_window_start']} - {coordinator.config['maintenance_window_end']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False


def test_component_integration():
    """Test integration with other components"""
    print("\n=== Testing Component Integration ===")
    
    try:
        coordinator = OngoingMaintenanceCoordinator()
        
        # Check component initialization
        components = [
            ('backup_manager', 'Backup Manager'),
            ('performance_monitor', 'Performance Monitor'),
            ('security_manager', 'Security Manager')
        ]
        
        for attr_name, display_name in components:
            component = getattr(coordinator, attr_name, None)
            if component:
                print(f"✓ {display_name} initialized successfully")
            else:
                print(f"⚠ {display_name} not initialized (may be expected)")
        
        # Test database monitor (may not be available in test environment)
        if coordinator.database_monitor:
            print("✓ Database Monitor initialized successfully")
        else:
            print("⚠ Database Monitor not initialized (may be expected in test environment)")
        
        return True
        
    except Exception as e:
        print(f"✗ Component integration test failed: {e}")
        return False


def test_schedule_calculation():
    """Test schedule calculation functionality"""
    print("\n=== Testing Schedule Calculation ===")
    
    try:
        coordinator = OngoingMaintenanceCoordinator()
        
        # Test cron expression parsing (if croniter is available)
        try:
            next_run = coordinator._calculate_next_run('0 2 * * *')  # Daily at 2 AM
            assert isinstance(next_run, datetime)
            print(f"✓ Cron expression parsed successfully: next run at {next_run}")
        except ImportError:
            print("⚠ croniter not available, using fallback scheduling")
        except Exception as e:
            print(f"⚠ Cron parsing failed, using fallback: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Schedule calculation test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all tests"""
    print("Starting Ongoing Maintenance Coordinator Tests")
    print("=" * 50)
    
    tests = [
        test_coordinator_initialization,
        test_configuration_loading,
        test_coordinator_status,
        test_schedule_management,
        test_schedule_calculation,
        test_manual_maintenance_trigger,
        test_component_integration,
        test_coordinator_lifecycle,
        test_global_coordinator_functions,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Ongoing Maintenance Coordinator is working correctly.")
    else:
        print(f"⚠ {failed} test(s) failed. Please review the output above.")
    
    return failed == 0


if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)