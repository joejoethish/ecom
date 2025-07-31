#!/usr/bin/env python
"""
Simple test for database maintenance tasks
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

def test_task_imports():
    """Test that all maintenance tasks can be imported"""
    print("Testing task imports...")
    
    try:
        from tasks.database_maintenance_tasks import (
            run_daily_maintenance_task,
            analyze_tables_task,
            optimize_fragmented_tables_task,
            cleanup_old_data_task,
            collect_database_statistics_task,
            generate_maintenance_recommendations_task,
            rebuild_indexes_task,
            archive_old_orders_task,
            weekly_maintenance_task
        )
        print("✓ All maintenance tasks imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_schedule_configuration():
    """Test that maintenance tasks are properly scheduled"""
    print("Testing schedule configuration...")
    
    try:
        from tasks.schedules import CELERY_BEAT_SCHEDULE, CELERY_TASK_ROUTES
        
        # Check for maintenance schedules
        maintenance_schedules = [
            'daily-database-maintenance',
            'analyze-database-tables',
            'optimize-fragmented-tables',
            'cleanup-old-data',
            'collect-database-statistics',
            'generate-maintenance-recommendations',
            'archive-old-orders',
            'rebuild-database-indexes',
            'weekly-database-maintenance'
        ]
        
        missing_schedules = []
        for schedule in maintenance_schedules:
            if schedule not in CELERY_BEAT_SCHEDULE:
                missing_schedules.append(schedule)
        
        if missing_schedules:
            print(f"✗ Missing schedules: {missing_schedules}")
            return False
        
        print(f"✓ All {len(maintenance_schedules)} maintenance schedules configured")
        
        # Check for task routes
        maintenance_task_routes = [
            'tasks.database_maintenance_tasks.run_daily_maintenance_task',
            'tasks.database_maintenance_tasks.analyze_tables_task',
            'tasks.database_maintenance_tasks.optimize_fragmented_tables_task',
            'tasks.database_maintenance_tasks.cleanup_old_data_task',
            'tasks.database_maintenance_tasks.collect_database_statistics_task',
            'tasks.database_maintenance_tasks.generate_maintenance_recommendations_task'
        ]
        
        missing_routes = []
        for route in maintenance_task_routes:
            if route not in CELERY_TASK_ROUTES:
                missing_routes.append(route)
        
        if missing_routes:
            print(f"✗ Missing task routes: {missing_routes}")
            return False
        
        print(f"✓ All {len(maintenance_task_routes)} maintenance task routes configured")
        return True
        
    except ImportError as e:
        print(f"✗ Schedule configuration test failed: {e}")
        return False

def test_maintenance_modules():
    """Test that maintenance modules can be imported"""
    print("Testing maintenance modules...")
    
    try:
        from core.database_maintenance import (
            DatabaseMaintenanceScheduler,
            IndexMaintenanceManager,
            DataCleanupManager,
            DatabaseStatisticsCollector
        )
        print("✓ All maintenance modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Module import failed: {e}")
        return False

def test_management_command():
    """Test that management command exists"""
    print("Testing management command...")
    
    try:
        from core.management.commands.database_maintenance import Command
        print("✓ Management command imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Management command import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Database Maintenance Tasks - Simple Test")
    print("=" * 50)
    
    tests = [
        ("Task Imports", test_task_imports),
        ("Schedule Configuration", test_schedule_configuration),
        ("Maintenance Modules", test_maintenance_modules),
        ("Management Command", test_management_command),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} - PASSED")
            else:
                failed += 1
                print(f"✗ {test_name} - FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())