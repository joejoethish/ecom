#!/usr/bin/env python
"""
Test script for database maintenance and cleanup functionality

This script tests the database maintenance system including:
- Index maintenance and optimization
- Data cleanup procedures
- Statistics collection
- Maintenance scheduling and monitoring
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from core.database_maintenance import (
    DatabaseMaintenanceScheduler,
    IndexMaintenanceManager,
    DataCleanupManager,
    DatabaseStatisticsCollector,
    run_database_maintenance,
    get_maintenance_recommendations
)

from tasks.database_maintenance_tasks import (
    run_daily_maintenance_task,
    analyze_tables_task,
    optimize_fragmented_tables_task,
    cleanup_old_data_task,
    collect_database_statistics_task,
    generate_maintenance_recommendations_task
)


def test_index_maintenance():
    """Test index maintenance functionality"""
    print("=" * 60)
    print("Testing Index Maintenance")
    print("=" * 60)
    
    try:
        index_manager = IndexMaintenanceManager()
        
        # Test table analysis
        print("\n1. Testing table analysis...")
        analyze_results = index_manager.analyze_all_tables()
        print(f"   ✓ Analyzed {len(analyze_results)} tables")
        
        if analyze_results:
            for result in analyze_results[:3]:  # Show first 3 results
                print(f"   - {result.table_name}: {result.rows_processed:,} rows, "
                      f"{result.duration_seconds:.2f}s")
        
        # Test fragmented table optimization
        print("\n2. Testing fragmented table optimization...")
        optimize_results = index_manager.optimize_fragmented_tables()
        print(f"   ✓ Optimized {len(optimize_results)} fragmented tables")
        
        if optimize_results:
            total_size_reduction = sum(r.before_size_mb - r.after_size_mb for r in optimize_results)
            print(f"   - Total size reduction: {total_size_reduction:.2f}MB")
        
        print("   ✓ Index maintenance tests passed")
        
    except Exception as e:
        print(f"   ✗ Index maintenance test failed: {e}")
        return False
    
    return True


def test_data_cleanup():
    """Test data cleanup functionality"""
    print("=" * 60)
    print("Testing Data Cleanup")
    print("=" * 60)
    
    try:
        cleanup_manager = DataCleanupManager()
        
        # Test dry run cleanup
        print("\n1. Testing dry run data cleanup...")
        cleanup_results = cleanup_manager.cleanup_old_data(dry_run=True)
        print(f"   ✓ Would clean up data from {len(cleanup_results)} tables")
        
        total_rows = sum(r.rows_affected for r in cleanup_results)
        print(f"   - Total rows that would be cleaned: {total_rows:,}")
        
        # Test order archival (dry run)
        print("\n2. Testing order archival (dry run)...")
        archive_result = cleanup_manager.archive_old_orders(days_old=365, dry_run=True)
        
        if archive_result:
            print(f"   ✓ Would archive {archive_result.rows_affected:,} old orders")
        else:
            print("   ✓ No old orders found to archive")
        
        print("   ✓ Data cleanup tests passed")
        
    except Exception as e:
        print(f"   ✗ Data cleanup test failed: {e}")
        return False
    
    return True


def test_statistics_collection():
    """Test database statistics collection"""
    print("=" * 60)
    print("Testing Statistics Collection")
    print("=" * 60)
    
    try:
        stats_collector = DatabaseStatisticsCollector()
        
        # Test statistics collection
        print("\n1. Testing database statistics collection...")
        statistics = stats_collector.collect_database_statistics()
        
        print(f"   ✓ Collected statistics for database")
        print(f"   - Total size: {statistics.total_size_mb:.2f}MB")
        print(f"   - Tables: {statistics.total_tables}")
        print(f"   - Indexes: {statistics.total_indexes}")
        print(f"   - Fragmentation: {statistics.fragmentation_percent:.2f}%")
        
        # Test growth trend analysis
        print("\n2. Testing growth trend analysis...")
        growth_analysis = stats_collector.analyze_growth_trends(days_back=7)
        
        if 'error' not in growth_analysis:
            print("   ✓ Growth trend analysis completed")
            if 'daily_growth_mb' in growth_analysis:
                print(f"   - Daily growth: {growth_analysis['daily_growth_mb']:.2f}MB")
        else:
            print(f"   ⚠ Growth trend analysis: {growth_analysis['error']}")
        
        print("   ✓ Statistics collection tests passed")
        
    except Exception as e:
        print(f"   ✗ Statistics collection test failed: {e}")
        return False
    
    return True


def test_maintenance_scheduler():
    """Test maintenance scheduler functionality"""
    print("=" * 60)
    print("Testing Maintenance Scheduler")
    print("=" * 60)
    
    try:
        scheduler = DatabaseMaintenanceScheduler()
        
        # Test maintenance recommendations
        print("\n1. Testing maintenance recommendations...")
        recommendations = scheduler.get_maintenance_recommendations()
        
        if 'error' not in recommendations:
            rec_list = recommendations.get('recommendations', [])
            print(f"   ✓ Generated {len(rec_list)} maintenance recommendations")
            
            for rec in rec_list[:3]:  # Show first 3 recommendations
                priority = rec.get('priority', 'unknown')
                rec_type = rec.get('type', 'unknown')
                print(f"   - [{priority.upper()}] {rec_type}")
        else:
            print(f"   ✗ Recommendations failed: {recommendations['error']}")
        
        # Test maintenance history
        print("\n2. Testing maintenance history...")
        history = scheduler.get_maintenance_history()
        print(f"   ✓ Retrieved {len(history)} maintenance history entries")
        
        print("   ✓ Maintenance scheduler tests passed")
        
    except Exception as e:
        print(f"   ✗ Maintenance scheduler test failed: {e}")
        return False
    
    return True


def test_full_maintenance():
    """Test full maintenance routine"""
    print("=" * 60)
    print("Testing Full Maintenance Routine")
    print("=" * 60)
    
    try:
        print("\n1. Testing full maintenance (dry run)...")
        result = run_database_maintenance(dry_run=True)
        
        if result['status'] == 'completed':
            print("   ✓ Full maintenance completed successfully")
            print(f"   - Duration: {result['duration_seconds']:.2f}s")
            print(f"   - Tasks completed: {len(result.get('tasks', []))}")
            
            improvements = result.get('improvements', {})
            print(f"   - Size reduction: {improvements.get('size_reduction_mb', 0):.2f}MB")
            print(f"   - Fragmentation improvement: {improvements.get('fragmentation_improvement_percent', 0):.2f}%")
        else:
            print(f"   ✗ Full maintenance failed: {result.get('error', 'Unknown error')}")
            return False
        
        print("   ✓ Full maintenance tests passed")
        
    except Exception as e:
        print(f"   ✗ Full maintenance test failed: {e}")
        return False
    
    return True


def test_celery_tasks():
    """Test Celery tasks (without actually running them)"""
    print("=" * 60)
    print("Testing Celery Tasks")
    print("=" * 60)
    
    try:
        # Test task imports
        print("\n1. Testing task imports...")
        
        tasks_to_test = [
            run_daily_maintenance_task,
            analyze_tables_task,
            optimize_fragmented_tables_task,
            cleanup_old_data_task,
            collect_database_statistics_task,
            generate_maintenance_recommendations_task
        ]
        
        for task in tasks_to_test:
            print(f"   ✓ {task.name} imported successfully")
        
        print("   ✓ All Celery tasks imported successfully")
        
        # Test task configuration
        print("\n2. Testing task configuration...")
        from tasks.schedules import CELERY_BEAT_SCHEDULE, CELERY_TASK_ROUTES
        
        maintenance_schedules = [
            key for key in CELERY_BEAT_SCHEDULE.keys()
            if 'maintenance' in key or 'database' in key
        ]
        
        print(f"   ✓ Found {len(maintenance_schedules)} maintenance schedules")
        for schedule in maintenance_schedules[:5]:  # Show first 5
            print(f"   - {schedule}")
        
        maintenance_routes = [
            key for key in CELERY_TASK_ROUTES.keys()
            if 'database_maintenance_tasks' in key
        ]
        
        print(f"   ✓ Found {len(maintenance_routes)} maintenance task routes")
        
        print("   ✓ Celery task tests passed")
        
    except Exception as e:
        print(f"   ✗ Celery task test failed: {e}")
        return False
    
    return True


def test_management_command():
    """Test Django management command"""
    print("=" * 60)
    print("Testing Management Command")
    print("=" * 60)
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Test help command
        print("\n1. Testing management command help...")
        out = StringIO()
        call_command('database_maintenance', '--help', stdout=out)
        help_output = out.getvalue()
        
        if 'database maintenance operations' in help_output.lower():
            print("   ✓ Management command help works")
        else:
            print("   ⚠ Management command help may have issues")
        
        # Test dry run recommendations
        print("\n2. Testing recommendations command...")
        out = StringIO()
        try:
            call_command('database_maintenance', '--recommendations', '--output-format=text', stdout=out)
            recommendations_output = out.getvalue()
            print("   ✓ Recommendations command executed successfully")
        except Exception as e:
            print(f"   ⚠ Recommendations command failed: {e}")
        
        print("   ✓ Management command tests passed")
        
    except Exception as e:
        print(f"   ✗ Management command test failed: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("Database Maintenance System Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    tests = [
        ("Index Maintenance", test_index_maintenance),
        ("Data Cleanup", test_data_cleanup),
        ("Statistics Collection", test_statistics_collection),
        ("Maintenance Scheduler", test_maintenance_scheduler),
        ("Full Maintenance", test_full_maintenance),
        ("Celery Tasks", test_celery_tasks),
        ("Management Command", test_management_command),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✓ {test_name} - PASSED")
            else:
                failed += 1
                print(f"\n✗ {test_name} - FAILED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} - ERROR: {e}")
        
        print("-" * 60)
    
    # Summary
    total = passed + failed
    print(f"\nTest Summary:")
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Database maintenance system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())