#!/usr/bin/env python3
"""
Example script demonstrating zero-downtime migration usage.
Shows various ways to use the migration system with different configurations.
"""
import os
import sys
import time
from pathlib import Path

# Add Django project to path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')

import django
django.setup()

from core.zero_downtime_migration import (
    ZeroDowntimeMigrationService,
    MigrationMonitor,
    MigrationStage
)


def example_basic_migration():
    """Example 1: Basic migration with console monitoring"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Migration with Console Monitoring")
    print("=" * 60)
    
    # MySQL configuration
    mysql_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'migration_user',
        'password': 'migration_password',
        'database': 'ecommerce_mysql',
        'charset': 'utf8mb4'
    }
    
    # Create migration service
    migration = ZeroDowntimeMigrationService(
        sqlite_path='db.sqlite3',
        mysql_config=mysql_config
    )
    
    # Add console monitoring
    migration.add_progress_callback(MigrationMonitor.console_progress_callback)
    
    print("Migration service created with console monitoring")
    print("MySQL Config:", {k: v for k, v in mysql_config.items() if k != 'password'})
    print("Migration ID:", migration.migration_id)
    
    # Note: This would execute actual migration in production
    # success = migration.execute_migration()
    print("✓ Migration service configured successfully")


def example_advanced_monitoring():
    """Example 2: Advanced monitoring with callbacks and logging"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Advanced Monitoring with Callbacks")
    print("=" * 60)
    
    # Create migration service
    migration = ZeroDowntimeMigrationService()
    
    # Custom progress callback
    def custom_progress_callback(metrics):
        stage_name = metrics.stage.value.replace('_', ' ').title()
        print(f"[CUSTOM] {stage_name}: {metrics.progress_percentage:.1f}% "
              f"({metrics.records_migrated:,}/{metrics.total_records:,})")
    
    # Custom checkpoint callback
    def custom_checkpoint_callback(checkpoint):
        stage_name = checkpoint.stage.value.replace('_', ' ').title()
        status_emoji = "✅" if checkpoint.status == 'passed' else "❌"
        print(f"{status_emoji} Checkpoint: {stage_name} - {checkpoint.status.upper()}")
        
        if checkpoint.error_message:
            print(f"   Error: {checkpoint.error_message}")
    
    # Custom error callback
    def custom_error_callback(error, stage):
        print(f"🚨 ERROR in {stage.value}: {error}")
    
    # Register callbacks
    migration.add_progress_callback(custom_progress_callback)
    migration.add_checkpoint_callback(custom_checkpoint_callback)
    migration.add_error_callback(custom_error_callback)
    
    # Add file logging
    log_file = f"migration_{migration.migration_id}.log"
    migration.add_progress_callback(MigrationMonitor.file_progress_callback(log_file))
    
    print("Advanced monitoring configured:")
    print("- Custom progress callback")
    print("- Custom checkpoint callback") 
    print("- Custom error callback")
    print(f"- File logging to: {log_file}")
    print("✓ Advanced monitoring setup complete")


def example_rollback_configuration():
    """Example 3: Custom rollback trigger configuration"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Custom Rollback Configuration")
    print("=" * 60)
    
    # Create migration service
    migration = ZeroDowntimeMigrationService()
    
    # Configure custom rollback triggers
    migration.rollback_triggers.update({
        'max_errors': 3,                    # Rollback after 3 errors
        'max_validation_failures': 2,      # Rollback after 2 validation failures
        'max_sync_lag_seconds': 180,       # Rollback if sync lag > 3 minutes
        'max_migration_time_hours': 6       # Rollback if migration > 6 hours
    })
    
    print("Custom rollback triggers configured:")
    for trigger, value in migration.rollback_triggers.items():
        print(f"- {trigger}: {value}")
    
    # Demonstrate rollback trigger checking
    print("\nTesting rollback trigger conditions...")
    
    # Simulate high error count
    migration._update_metrics(error_count=4)
    if migration._check_rollback_triggers():
        print("✓ Rollback would be triggered due to high error count")
    
    print("✓ Rollback configuration example complete")


def example_migration_status_monitoring():
    """Example 4: Migration status monitoring and reporting"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Migration Status Monitoring")
    print("=" * 60)
    
    # Create migration service
    migration = ZeroDowntimeMigrationService()
    
    # Simulate some migration progress
    migration._update_metrics(
        stage=MigrationStage.INITIAL_DATA_SYNC,
        total_tables=5,
        total_records=10000,
        tables_processed=3,
        records_migrated=6000
    )
    
    # Create some checkpoints
    migration._create_checkpoint(
        MigrationStage.PREPARATION,
        'passed',
        {'tables_found': 5, 'total_records': 10000}
    )
    
    migration._create_checkpoint(
        MigrationStage.SCHEMA_SYNC,
        'passed',
        {'tables_created': 5}
    )
    
    # Get migration status
    status = migration.get_migration_status()
    
    print("Migration Status Report:")
    print(f"- Migration ID: {status['migration_id']}")
    print(f"- Current Stage: {status['current_stage']}")
    print(f"- Is Running: {status['is_running']}")
    print(f"- Rollback Triggered: {status['rollback_triggered']}")
    
    if status['metrics']:
        metrics = status['metrics']
        print(f"- Progress: {metrics['progress_percentage']:.1f}%")
        print(f"- Records Migrated: {metrics['records_migrated']:,}/{metrics['total_records']:,}")
        print(f"- Tables Processed: {metrics['tables_processed']}/{metrics['total_tables']}")
        print(f"- Migration Speed: {metrics['migration_speed']:.0f} records/second")
    
    print(f"- Checkpoints: {len(status['checkpoints'])}")
    for checkpoint in status['checkpoints']:
        stage_name = checkpoint['stage'].replace('_', ' ').title()
        print(f"  • {stage_name}: {checkpoint['status']}")
    
    print("✓ Status monitoring example complete")


def example_web_monitoring_setup():
    """Example 5: Web monitoring setup"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Web Monitoring Setup")
    print("=" * 60)
    
    # Create migration service
    migration = ZeroDowntimeMigrationService()
    
    # Setup web monitoring via cache
    cache_key = f"migration_progress_{migration.migration_id}"
    cache_callback = MigrationMonitor.cache_progress_callback(cache_key)
    migration.add_progress_callback(cache_callback)
    
    print("Web monitoring configured:")
    print(f"- Cache key: {cache_key}")
    print("- Dashboard URL: http://localhost:8000/migration/dashboard/")
    print("- API endpoints:")
    print("  • GET /api/migration/monitor/ - List active migrations")
    print(f"  • GET /api/migration/monitor/{migration.migration_id}/ - Get specific migration")
    print("  • GET /api/migration/history/ - Get migration history")
    
    # Simulate progress update for cache
    migration._update_metrics(
        stage=MigrationStage.VALIDATION,
        total_records=5000,
        records_migrated=3500
    )
    
    print("✓ Web monitoring setup complete")


def example_error_handling():
    """Example 6: Error handling and recovery"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Error Handling and Recovery")
    print("=" * 60)
    
    # Create migration service
    migration = ZeroDowntimeMigrationService()
    
    # Error tracking callback
    errors_encountered = []
    
    def error_tracker(error, stage):
        errors_encountered.append({
            'error': str(error),
            'stage': stage.value,
            'timestamp': time.time()
        })
        print(f"🚨 Error tracked: {error} in stage {stage.value}")
    
    migration.add_error_callback(error_tracker)
    
    # Simulate some errors
    test_errors = [
        (Exception("Connection timeout"), MigrationStage.PREPARATION),
        (Exception("Validation failed"), MigrationStage.VALIDATION),
        (Exception("Rollback required"), MigrationStage.CUTOVER)
    ]
    
    print("Simulating error scenarios:")
    for error, stage in test_errors:
        migration._notify_error(error, stage)
    
    print(f"\nErrors tracked: {len(errors_encountered)}")
    for i, error_info in enumerate(errors_encountered, 1):
        print(f"{i}. {error_info['error']} (Stage: {error_info['stage']})")
    
    # Demonstrate manual rollback trigger
    print("\nTriggering manual rollback...")
    migration.trigger_rollback("Manual intervention required")
    
    print(f"Rollback triggered: {migration.rollback_triggered}")
    print("✓ Error handling example complete")


def main():
    """Run all examples"""
    print("ZERO-DOWNTIME MIGRATION SYSTEM EXAMPLES")
    print("=" * 60)
    print("This script demonstrates various usage patterns for the")
    print("zero-downtime migration system.")
    print()
    
    try:
        # Run examples
        example_basic_migration()
        example_advanced_monitoring()
        example_rollback_configuration()
        example_migration_status_monitoring()
        example_web_monitoring_setup()
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Configure your MySQL database settings")
        print("2. Run: python manage.py zero_downtime_migrate --help")
        print("3. Test with --dry-run first")
        print("4. Monitor via web dashboard during actual migration")
        print("5. Review migration logs and reports")
        
    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())