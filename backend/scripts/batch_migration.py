#!/usr/bin/env python3
"""
Batch migration utility for SQLite to MySQL migration.
Provides automated migration with progress tracking and error handling.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add Django project to path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')

import django
django.setup()

from core.migration import (
    DatabaseMigrationService,
    MigrationValidator,
    create_migration_service
)


class BatchMigrationManager:
    """
    Manages batch migration operations with advanced features.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize batch migration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.logger = self._setup_logging()
        self.migration_service: Optional[DatabaseMigrationService] = None
        self.start_time: Optional[datetime] = None
        
    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load migration configuration"""
        default_config = {
            'batch_size': 1000,
            'create_rollback': True,
            'max_retries': 3,
            'retry_delay': 5,
            'validation_sample_size': 100,
            'parallel_tables': 1,
            'skip_tables': [],
            'priority_tables': [],
            'log_level': 'INFO',
            'output_format': 'text',
            'save_progress': True,
            'progress_file': 'migration_progress.json'
        }
        
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('batch_migration')
        logger.setLevel(getattr(logging, self.config['log_level']))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = Path('migration_batch.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def save_progress(self, progress_data: Dict[str, Any]):
        """Save migration progress to file"""
        if not self.config['save_progress']:
            return
        
        progress_file = Path(self.config['progress_file'])
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2, default=str)
        
        self.logger.info(f"Progress saved to {progress_file}")
    
    def load_progress(self) -> Dict[str, Any]:
        """Load previous migration progress"""
        progress_file = Path(self.config['progress_file'])
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                return json.load(f)
        return {}
    
    def run_migration_with_retry(self, table_name: str) -> Dict[str, Any]:
        """
        Run migration for a single table with retry logic.
        
        Args:
            table_name: Name of the table to migrate
            
        Returns:
            Dict: Migration results
        """
        max_retries = self.config['max_retries']
        retry_delay = self.config['retry_delay']
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"Migrating table {table_name} (attempt {attempt + 1}/{max_retries + 1})")
                
                # Create rollback point
                if self.config['create_rollback']:
                    self.migration_service.create_rollback_point(table_name)
                
                # Get schema and create MySQL table
                columns = self.migration_service.get_table_schema(table_name)
                if not self.migration_service.create_mysql_table(table_name, columns):
                    raise Exception(f"Failed to create MySQL table {table_name}")
                
                # Migrate data
                progress = self.migration_service.migrate_table_data(
                    table_name, 
                    self.config['batch_size']
                )
                
                # Validate migration
                validation = self.migration_service.validate_migration(table_name)
                
                if progress.status == 'completed' and validation.is_valid:
                    self.logger.info(f"Successfully migrated table {table_name}")
                    return {
                        'status': 'success',
                        'table_name': table_name,
                        'progress': progress,
                        'validation': validation,
                        'attempts': attempt + 1
                    }
                else:
                    error_msg = f"Migration validation failed for {table_name}"
                    if progress.status != 'completed':
                        error_msg = f"Migration failed for {table_name}: {progress.error_message}"
                    
                    if attempt < max_retries:
                        self.logger.warning(f"{error_msg}, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception(error_msg)
                
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"Migration attempt {attempt + 1} failed for {table_name}: {e}")
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"All migration attempts failed for {table_name}: {e}")
                    return {
                        'status': 'failed',
                        'table_name': table_name,
                        'error': str(e),
                        'attempts': attempt + 1
                    }
        
        return {
            'status': 'failed',
            'table_name': table_name,
            'error': 'Maximum retries exceeded',
            'attempts': max_retries + 1
        }
    
    def get_migration_order(self, tables: List[str]) -> List[str]:
        """
        Determine optimal migration order based on configuration.
        
        Args:
            tables: List of table names
            
        Returns:
            List[str]: Ordered list of tables
        """
        # Filter out skipped tables
        filtered_tables = [t for t in tables if t not in self.config['skip_tables']]
        
        # Prioritize tables
        priority_tables = [t for t in self.config['priority_tables'] if t in filtered_tables]
        remaining_tables = [t for t in filtered_tables if t not in priority_tables]
        
        # Return priority tables first, then remaining tables
        return priority_tables + sorted(remaining_tables)
    
    def run_batch_migration(self) -> Dict[str, Any]:
        """
        Run complete batch migration with all configured options.
        
        Returns:
            Dict: Complete migration results
        """
        self.start_time = datetime.now()
        self.logger.info("Starting batch migration process")
        
        # Initialize migration service
        self.migration_service = create_migration_service()
        
        if not self.migration_service.connect_databases():
            raise RuntimeError("Failed to connect to databases")
        
        try:
            # Load previous progress
            previous_progress = self.load_progress()
            completed_tables = set(previous_progress.get('completed_tables', []))
            
            # Get tables to migrate
            all_tables = self.migration_service.get_sqlite_tables()
            tables_to_migrate = [t for t in all_tables if t not in completed_tables]
            
            if not tables_to_migrate:
                self.logger.info("All tables already migrated")
                return previous_progress
            
            # Determine migration order
            ordered_tables = self.get_migration_order(tables_to_migrate)
            
            self.logger.info(f"Migrating {len(ordered_tables)} tables: {', '.join(ordered_tables)}")
            
            # Initialize results
            results = {
                'start_time': self.start_time,
                'total_tables': len(ordered_tables),
                'completed_tables': list(completed_tables),
                'successful_migrations': 0,
                'failed_migrations': 0,
                'table_results': {},
                'config': self.config
            }
            
            # Migrate tables
            for i, table_name in enumerate(ordered_tables, 1):
                self.logger.info(f"Processing table {i}/{len(ordered_tables)}: {table_name}")
                
                table_result = self.run_migration_with_retry(table_name)
                results['table_results'][table_name] = table_result
                
                if table_result['status'] == 'success':
                    results['successful_migrations'] += 1
                    results['completed_tables'].append(table_name)
                    self.logger.info(f"✓ {table_name} migrated successfully")
                else:
                    results['failed_migrations'] += 1
                    self.logger.error(f"✗ {table_name} migration failed: {table_result.get('error')}")
                
                # Save progress after each table
                self.save_progress(results)
                
                # Progress update
                progress_pct = (i / len(ordered_tables)) * 100
                self.logger.info(f"Overall progress: {progress_pct:.1f}% ({i}/{len(ordered_tables)})")
            
            # Finalize results
            results['end_time'] = datetime.now()
            results['total_duration'] = (results['end_time'] - results['start_time']).total_seconds()
            results['success_rate'] = (results['successful_migrations'] / len(ordered_tables)) * 100
            
            # Save final results
            self.save_progress(results)
            
            # Generate summary
            self.logger.info("Batch migration completed")
            self.logger.info(f"Success rate: {results['success_rate']:.1f}%")
            self.logger.info(f"Total duration: {results['total_duration']:.2f} seconds")
            
            return results
            
        finally:
            self.migration_service.disconnect_databases()
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate detailed migration report.
        
        Args:
            results: Migration results
            
        Returns:
            str: Report content
        """
        report_lines = [
            "=" * 80,
            "DATABASE MIGRATION REPORT",
            "=" * 80,
            f"Start Time: {results['start_time']}",
            f"End Time: {results.get('end_time', 'In Progress')}",
            f"Duration: {results.get('total_duration', 0):.2f} seconds",
            "",
            "SUMMARY:",
            f"  Total Tables: {results['total_tables']}",
            f"  Successful: {results['successful_migrations']}",
            f"  Failed: {results['failed_migrations']}",
            f"  Success Rate: {results.get('success_rate', 0):.1f}%",
            "",
            "TABLE DETAILS:",
        ]
        
        for table_name, table_result in results.get('table_results', {}).items():
            status_symbol = "✓" if table_result['status'] == 'success' else "✗"
            report_lines.append(f"  {status_symbol} {table_name}: {table_result['status']}")
            
            if table_result['status'] == 'success':
                progress = table_result['progress']
                validation = table_result['validation']
                report_lines.extend([
                    f"    Records: {progress.migrated_records}/{progress.total_records}",
                    f"    Duration: {progress.duration_seconds:.2f}s",
                    f"    Validation: {'PASS' if validation.is_valid else 'FAIL'}"
                ])
            else:
                report_lines.append(f"    Error: {table_result.get('error', 'Unknown error')}")
                report_lines.append(f"    Attempts: {table_result.get('attempts', 1)}")
        
        if results['failed_migrations'] > 0:
            report_lines.extend([
                "",
                "FAILED TABLES:",
                "  The following tables failed migration and may need manual intervention:"
            ])
            
            for table_name, table_result in results.get('table_results', {}).items():
                if table_result['status'] == 'failed':
                    report_lines.append(f"  - {table_name}: {table_result.get('error')}")
        
        report_lines.extend([
            "",
            "CONFIGURATION:",
            f"  Batch Size: {results['config']['batch_size']}",
            f"  Max Retries: {results['config']['max_retries']}",
            f"  Rollback Points: {results['config']['create_rollback']}",
            f"  Skip Tables: {results['config']['skip_tables']}",
            "=" * 80
        ])
        
        return "\n".join(report_lines)


def main():
    """Main entry point for batch migration script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch SQLite to MySQL migration')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--report-only', action='store_true', help='Generate report from existing progress')
    parser.add_argument('--clean-start', action='store_true', help='Start fresh migration (ignore previous progress)')
    
    args = parser.parse_args()
    
    try:
        manager = BatchMigrationManager(args.config)
        
        if args.report_only:
            # Generate report from existing progress
            progress = manager.load_progress()
            if progress:
                report = manager.generate_report(progress)
                print(report)
                
                # Save report to file
                report_file = Path(f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                with open(report_file, 'w') as f:
                    f.write(report)
                print(f"\nReport saved to: {report_file}")
            else:
                print("No migration progress found")
            return
        
        if args.clean_start:
            # Remove existing progress file
            progress_file = Path(manager.config['progress_file'])
            if progress_file.exists():
                progress_file.unlink()
                print("Previous progress cleared")
        
        # Run migration
        results = manager.run_batch_migration()
        
        # Generate and display report
        report = manager.generate_report(results)
        print("\n" + report)
        
        # Save report to file
        report_file = Path(f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\nDetailed report saved to: {report_file}")
        
        # Exit with appropriate code
        if results['failed_migrations'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"Batch migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()