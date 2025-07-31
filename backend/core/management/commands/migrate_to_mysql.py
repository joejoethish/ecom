"""
Django management command for SQLite to MySQL migration.
Provides command-line interface for database migration utilities.
"""
import json
import sys
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.migration import (
    DatabaseMigrationService, 
    MigrationValidator,
    create_migration_service,
    run_full_migration,
    validate_migration_results
)


class Command(BaseCommand):
    help = 'Migrate data from SQLite to MySQL database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['migrate', 'validate', 'rollback', 'cleanup', 'status'],
            default='migrate',
            help='Action to perform (default: migrate)'
        )
        
        parser.add_argument(
            '--table',
            type=str,
            help='Specific table to migrate/validate (optional)'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for data migration (default: 1000)'
        )
        
        parser.add_argument(
            '--no-rollback',
            action='store_true',
            help='Skip creating rollback points'
        )
        
        parser.add_argument(
            '--sqlite-path',
            type=str,
            help='Path to SQLite database file (optional)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform validation without actual migration'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if validation fails'
        )
        
        parser.add_argument(
            '--output-format',
            type=str,
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        action = options['action']
        
        try:
            if action == 'migrate':
                self.handle_migrate(options)
            elif action == 'validate':
                self.handle_validate(options)
            elif action == 'rollback':
                self.handle_rollback(options)
            elif action == 'cleanup':
                self.handle_cleanup(options)
            elif action == 'status':
                self.handle_status(options)
        except Exception as e:
            raise CommandError(f"Command failed: {str(e)}")
    
    def handle_migrate(self, options):
        """Handle migration action"""
        self.stdout.write(self.style.SUCCESS("Starting SQLite to MySQL migration..."))
        
        # Create migration service
        migration_service = create_migration_service(
            sqlite_path=options.get('sqlite_path')
        )
        
        if not migration_service.connect_databases():
            raise CommandError("Failed to connect to databases")
        
        try:
            # Pre-migration validation if not forced
            if not options['force'] and not options['dry_run']:
                self.stdout.write("Performing pre-migration validation...")
                validator = MigrationValidator(migration_service)
                
                tables = [options['table']] if options['table'] else migration_service.get_sqlite_tables()
                validation_failed = False
                
                for table_name in tables:
                    schema_result = validator.validate_schema_compatibility(table_name)
                    if not schema_result['is_compatible']:
                        self.stdout.write(
                            self.style.ERROR(f"Schema validation failed for {table_name}:")
                        )
                        for issue in schema_result['issues']:
                            self.stdout.write(f"  - {issue}")
                        validation_failed = True
                
                if validation_failed:
                    raise CommandError("Pre-migration validation failed. Use --force to proceed anyway.")
            
            # Perform migration
            if options['dry_run']:
                self.stdout.write(self.style.WARNING("DRY RUN: No actual migration performed"))
                return
            
            if options['table']:
                # Migrate single table
                self.stdout.write(f"Migrating table: {options['table']}")
                
                # Create rollback point
                if not options['no_rollback']:
                    migration_service.create_rollback_point(options['table'])
                
                # Get schema and create table
                columns = migration_service.get_table_schema(options['table'])
                if not migration_service.create_mysql_table(options['table'], columns):
                    raise CommandError(f"Failed to create MySQL table {options['table']}")
                
                # Migrate data
                progress = migration_service.migrate_table_data(options['table'], options['batch_size'])
                
                # Validate migration
                validation = migration_service.validate_migration(options['table'])
                
                # Output results
                self.output_single_table_results(options['table'], progress, validation, options['output_format'])
                
            else:
                # Migrate all tables
                self.stdout.write("Migrating all tables...")
                results = migration_service.migrate_all_tables(
                    batch_size=options['batch_size'],
                    create_rollback=not options['no_rollback']
                )
                
                # Output results
                self.output_migration_results(results, options['output_format'])
        
        finally:
            migration_service.disconnect_databases()
    
    def handle_validate(self, options):
        """Handle validation action"""
        self.stdout.write("Validating migration results...")
        
        table_names = [options['table']] if options['table'] else None
        results = validate_migration_results(table_names)
        
        self.output_validation_results(results, options['output_format'])
    
    def handle_rollback(self, options):
        """Handle rollback action"""
        if not options['table']:
            raise CommandError("Table name is required for rollback action")
        
        self.stdout.write(f"Rolling back table: {options['table']}")
        
        migration_service = create_migration_service()
        if not migration_service.connect_databases():
            raise CommandError("Failed to connect to databases")
        
        try:
            success = migration_service.rollback_table(options['table'])
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully rolled back table {options['table']}")
                )
            else:
                raise CommandError(f"Failed to rollback table {options['table']}")
        finally:
            migration_service.disconnect_databases()
    
    def handle_cleanup(self, options):
        """Handle cleanup action"""
        self.stdout.write("Cleaning up rollback points...")
        
        migration_service = create_migration_service()
        if not migration_service.connect_databases():
            raise CommandError("Failed to connect to databases")
        
        try:
            success = migration_service.cleanup_rollback_points(options.get('table'))
            if success:
                self.stdout.write(self.style.SUCCESS("Rollback points cleaned up successfully"))
            else:
                raise CommandError("Failed to cleanup rollback points")
        finally:
            migration_service.disconnect_databases()
    
    def handle_status(self, options):
        """Handle status action"""
        self.stdout.write("Checking migration status...")
        
        migration_service = create_migration_service()
        if not migration_service.connect_databases():
            raise CommandError("Failed to connect to databases")
        
        try:
            # Get database information
            sqlite_tables = migration_service.get_sqlite_tables()
            
            # Check MySQL tables
            mysql_cursor = migration_service.mysql_conn.cursor()
            mysql_cursor.execute("SHOW TABLES")
            mysql_tables = [row[0] for row in mysql_cursor.fetchall()]
            
            status_info = {
                'sqlite_tables': len(sqlite_tables),
                'mysql_tables': len(mysql_tables),
                'common_tables': len(set(sqlite_tables) & set(mysql_tables)),
                'missing_in_mysql': list(set(sqlite_tables) - set(mysql_tables)),
                'extra_in_mysql': list(set(mysql_tables) - set(sqlite_tables))
            }
            
            self.output_status_info(status_info, options['output_format'])
            
        finally:
            migration_service.disconnect_databases()
    
    def output_single_table_results(self, table_name, progress, validation, output_format):
        """Output results for single table migration"""
        if output_format == 'json':
            result = {
                'table': table_name,
                'migration': {
                    'status': progress.status,
                    'records_migrated': progress.migrated_records,
                    'total_records': progress.total_records,
                    'duration_seconds': progress.duration_seconds,
                    'progress_percentage': progress.progress_percentage
                },
                'validation': {
                    'is_valid': validation.is_valid,
                    'source_count': validation.source_count,
                    'target_count': validation.target_count,
                    'missing_records': len(validation.missing_records),
                    'extra_records': len(validation.extra_records)
                }
            }
            self.stdout.write(json.dumps(result, indent=2, default=str))
        else:
            self.stdout.write(f"\nMigration Results for {table_name}:")
            self.stdout.write(f"  Status: {progress.status}")
            self.stdout.write(f"  Records: {progress.migrated_records}/{progress.total_records}")
            self.stdout.write(f"  Progress: {progress.progress_percentage:.1f}%")
            if progress.duration_seconds:
                self.stdout.write(f"  Duration: {progress.duration_seconds:.2f} seconds")
            
            self.stdout.write(f"\nValidation Results:")
            self.stdout.write(f"  Valid: {validation.is_valid}")
            self.stdout.write(f"  Source count: {validation.source_count}")
            self.stdout.write(f"  Target count: {validation.target_count}")
            if validation.missing_records:
                self.stdout.write(f"  Missing records: {len(validation.missing_records)}")
            if validation.extra_records:
                self.stdout.write(f"  Extra records: {len(validation.extra_records)}")
    
    def output_migration_results(self, results, output_format):
        """Output results for full migration"""
        if output_format == 'json':
            self.stdout.write(json.dumps(results, indent=2, default=str))
        else:
            self.stdout.write(f"\nMigration Summary:")
            self.stdout.write(f"  Total tables: {results['total_tables']}")
            self.stdout.write(f"  Successful migrations: {results['successful_migrations']}")
            self.stdout.write(f"  Failed migrations: {results['failed_migrations']}")
            self.stdout.write(f"  Successful validations: {results['successful_validations']}")
            self.stdout.write(f"  Failed validations: {results['failed_validations']}")
            self.stdout.write(f"  Total duration: {results['total_duration']:.2f} seconds")
            
            if results['failed_migrations'] > 0:
                self.stdout.write(self.style.ERROR("\nFailed Tables:"))
                for table_name, table_info in results['tables'].items():
                    if table_info.get('migration_status') == 'failed':
                        self.stdout.write(f"  - {table_name}: {table_info.get('error', 'Unknown error')}")
            
            if results['log_file']:
                self.stdout.write(f"\nDetailed log saved to: {results['log_file']}")
    
    def output_validation_results(self, results, output_format):
        """Output validation results"""
        if output_format == 'json':
            # Convert ValidationResult objects to dictionaries
            json_results = {}
            for table_name, result in results.items():
                json_results[table_name] = {
                    'table_name': result.table_name,
                    'source_count': result.source_count,
                    'target_count': result.target_count,
                    'is_valid': result.is_valid,
                    'missing_records': len(result.missing_records),
                    'extra_records': len(result.extra_records),
                    'validation_time': result.validation_time.isoformat()
                }
            self.stdout.write(json.dumps(json_results, indent=2))
        else:
            self.stdout.write("\nValidation Results:")
            for table_name, result in results.items():
                status = "PASS" if result.is_valid else "FAIL"
                style = self.style.SUCCESS if result.is_valid else self.style.ERROR
                self.stdout.write(style(f"  {table_name}: {status}"))
                self.stdout.write(f"    Source: {result.source_count}, Target: {result.target_count}")
                if not result.is_valid:
                    if result.missing_records:
                        self.stdout.write(f"    Missing: {len(result.missing_records)} records")
                    if result.extra_records:
                        self.stdout.write(f"    Extra: {len(result.extra_records)} records")
    
    def output_status_info(self, status_info, output_format):
        """Output migration status information"""
        if output_format == 'json':
            self.stdout.write(json.dumps(status_info, indent=2))
        else:
            self.stdout.write("\nMigration Status:")
            self.stdout.write(f"  SQLite tables: {status_info['sqlite_tables']}")
            self.stdout.write(f"  MySQL tables: {status_info['mysql_tables']}")
            self.stdout.write(f"  Common tables: {status_info['common_tables']}")
            
            if status_info['missing_in_mysql']:
                self.stdout.write(f"  Missing in MySQL: {', '.join(status_info['missing_in_mysql'])}")
            
            if status_info['extra_in_mysql']:
                self.stdout.write(f"  Extra in MySQL: {', '.join(status_info['extra_in_mysql'])}")