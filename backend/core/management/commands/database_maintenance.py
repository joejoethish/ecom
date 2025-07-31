"""
Django management command for database maintenance operations

Usage:
    python manage.py database_maintenance --help
    python manage.py database_maintenance --full-maintenance
    python manage.py database_maintenance --analyze-tables
    python manage.py database_maintenance --optimize-tables
    python manage.py database_maintenance --cleanup-data --dry-run
    python manage.py database_maintenance --collect-stats
    python manage.py database_maintenance --recommendations
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from core.database_maintenance import (
    DatabaseMaintenanceScheduler,
    IndexMaintenanceManager,
    DataCleanupManager,
    DatabaseStatisticsCollector,
    run_database_maintenance,
    get_maintenance_recommendations
)


class Command(BaseCommand):
    help = 'Run database maintenance operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            type=str,
            default='default',
            help='Database alias to perform maintenance on (default: default)'
        )
        
        parser.add_argument(
            '--full-maintenance',
            action='store_true',
            help='Run complete maintenance routine (analyze, optimize, cleanup, stats)'
        )
        
        parser.add_argument(
            '--analyze-tables',
            action='store_true',
            help='Analyze all tables and update statistics'
        )
        
        parser.add_argument(
            '--optimize-tables',
            action='store_true',
            help='Optimize fragmented tables'
        )
        
        parser.add_argument(
            '--rebuild-indexes',
            action='store_true',
            help='Rebuild all indexes'
        )
        
        parser.add_argument(
            '--cleanup-data',
            action='store_true',
            help='Clean up old data according to configured rules'
        )
        
        parser.add_argument(
            '--archive-orders',
            action='store_true',
            help='Archive old completed orders'
        )
        
        parser.add_argument(
            '--collect-stats',
            action='store_true',
            help='Collect database statistics'
        )
        
        parser.add_argument(
            '--recommendations',
            action='store_true',
            help='Generate maintenance recommendations'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        
        parser.add_argument(
            '--days-old',
            type=int,
            default=365,
            help='Number of days old for archiving operations (default: 365)'
        )
        
        parser.add_argument(
            '--output-format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        database_alias = options['database']
        dry_run = options['dry_run']
        output_format = options['output_format']
        verbose = options['verbose']
        
        # Validate database alias
        if database_alias not in settings.DATABASES:
            raise CommandError(f"Database alias '{database_alias}' not found in settings")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN MODE - No changes will be made to database '{database_alias}'")
            )
        
        try:
            if options['full_maintenance']:
                self._run_full_maintenance(database_alias, dry_run, output_format, verbose)
            
            elif options['analyze_tables']:
                self._analyze_tables(database_alias, output_format, verbose)
            
            elif options['optimize_tables']:
                self._optimize_tables(database_alias, output_format, verbose)
            
            elif options['rebuild_indexes']:
                self._rebuild_indexes(database_alias, output_format, verbose)
            
            elif options['cleanup_data']:
                self._cleanup_data(database_alias, dry_run, output_format, verbose)
            
            elif options['archive_orders']:
                self._archive_orders(database_alias, options['days_old'], dry_run, output_format, verbose)
            
            elif options['collect_stats']:
                self._collect_statistics(database_alias, output_format, verbose)
            
            elif options['recommendations']:
                self._generate_recommendations(database_alias, output_format, verbose)
            
            else:
                self.stdout.write(
                    self.style.ERROR("No operation specified. Use --help to see available options.")
                )
                return
        
        except Exception as e:
            raise CommandError(f"Maintenance operation failed: {str(e)}")

    def _run_full_maintenance(self, database_alias, dry_run, output_format, verbose):
        """Run complete maintenance routine"""
        self.stdout.write(f"Running full maintenance for database '{database_alias}'...")
        
        result = run_database_maintenance(database_alias, dry_run)
        
        if output_format == 'json':
            self.stdout.write(json.dumps(result, indent=2))
        else:
            self._display_maintenance_result(result, verbose)

    def _analyze_tables(self, database_alias, output_format, verbose):
        """Analyze all tables"""
        self.stdout.write(f"Analyzing tables in database '{database_alias}'...")
        
        index_manager = IndexMaintenanceManager(database_alias)
        results = index_manager.analyze_all_tables()
        
        if output_format == 'json':
            self.stdout.write(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            self.stdout.write(f"Analyzed {len(results)} tables")
            if verbose:
                for result in results:
                    self.stdout.write(f"  - {result.table_name}: {result.rows_processed:,} rows, "
                                    f"{result.duration_seconds:.2f}s")

    def _optimize_tables(self, database_alias, output_format, verbose):
        """Optimize fragmented tables"""
        self.stdout.write(f"Optimizing fragmented tables in database '{database_alias}'...")
        
        index_manager = IndexMaintenanceManager(database_alias)
        results = index_manager.optimize_fragmented_tables()
        
        if output_format == 'json':
            self.stdout.write(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            total_size_reduction = sum(r.before_size_mb - r.after_size_mb for r in results)
            self.stdout.write(f"Optimized {len(results)} tables, freed {total_size_reduction:.2f}MB")
            
            if verbose:
                for result in results:
                    size_reduction = result.before_size_mb - result.after_size_mb
                    frag_improvement = result.fragmentation_before - result.fragmentation_after
                    self.stdout.write(f"  - {result.table_name}: {size_reduction:+.2f}MB, "
                                    f"fragmentation: {frag_improvement:+.2f}%")

    def _rebuild_indexes(self, database_alias, output_format, verbose):
        """Rebuild all indexes"""
        self.stdout.write(f"Rebuilding indexes in database '{database_alias}'...")
        
        index_manager = IndexMaintenanceManager(database_alias)
        results = index_manager.rebuild_indexes()
        
        if output_format == 'json':
            self.stdout.write(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            total_size_change = sum(r.after_size_mb - r.before_size_mb for r in results)
            self.stdout.write(f"Rebuilt indexes for {len(results)} tables, "
                            f"size change: {total_size_change:+.2f}MB")
            
            if verbose:
                for result in results:
                    size_change = result.after_size_mb - result.before_size_mb
                    self.stdout.write(f"  - {result.table_name}: {size_change:+.2f}MB, "
                                    f"{result.duration_seconds:.2f}s")

    def _cleanup_data(self, database_alias, dry_run, output_format, verbose):
        """Clean up old data"""
        action = "Would clean up" if dry_run else "Cleaning up"
        self.stdout.write(f"{action} old data in database '{database_alias}'...")
        
        cleanup_manager = DataCleanupManager(database_alias)
        results = cleanup_manager.cleanup_old_data(dry_run)
        
        if output_format == 'json':
            self.stdout.write(json.dumps([r.to_dict() for r in results], indent=2))
        else:
            total_rows = sum(r.rows_affected for r in results)
            total_size_freed = sum(r.data_size_freed_mb for r in results)
            
            action_past = "Would have cleaned" if dry_run else "Cleaned"
            self.stdout.write(f"{action_past} {total_rows:,} rows from {len(results)} tables, "
                            f"freed {total_size_freed:.2f}MB")
            
            if verbose:
                for result in results:
                    self.stdout.write(f"  - {result.table_name}: {result.rows_affected:,} rows, "
                                    f"{result.data_size_freed_mb:.2f}MB")

    def _archive_orders(self, database_alias, days_old, dry_run, output_format, verbose):
        """Archive old orders"""
        action = "Would archive" if dry_run else "Archiving"
        self.stdout.write(f"{action} orders older than {days_old} days in database '{database_alias}'...")
        
        cleanup_manager = DataCleanupManager(database_alias)
        result = cleanup_manager.archive_old_orders(days_old, dry_run)
        
        if result:
            if output_format == 'json':
                self.stdout.write(json.dumps(result.to_dict(), indent=2))
            else:
                action_past = "Would have archived" if dry_run else "Archived"
                self.stdout.write(f"{action_past} {result.rows_affected:,} orders")
        else:
            self.stdout.write("No old orders found to archive")

    def _collect_statistics(self, database_alias, output_format, verbose):
        """Collect database statistics"""
        self.stdout.write(f"Collecting statistics for database '{database_alias}'...")
        
        stats_collector = DatabaseStatisticsCollector(database_alias)
        statistics = stats_collector.collect_database_statistics()
        
        if output_format == 'json':
            self.stdout.write(json.dumps(statistics.to_dict(), indent=2))
        else:
            self.stdout.write(f"Database Statistics for '{database_alias}':")
            self.stdout.write(f"  Total Size: {statistics.total_size_mb:.2f} MB")
            self.stdout.write(f"  Data Size: {statistics.data_size_mb:.2f} MB")
            self.stdout.write(f"  Index Size: {statistics.index_size_mb:.2f} MB")
            self.stdout.write(f"  Tables: {statistics.total_tables}")
            self.stdout.write(f"  Indexes: {statistics.total_indexes}")
            self.stdout.write(f"  Fragmentation: {statistics.fragmentation_percent:.2f}%")
            
            if verbose:
                self.stdout.write("\nTop 10 Largest Tables:")
                sorted_tables = sorted(
                    statistics.table_statistics.items(),
                    key=lambda x: x[1]['total_size_mb'],
                    reverse=True
                )[:10]
                
                for table_name, stats in sorted_tables:
                    self.stdout.write(f"  - {table_name}: {stats['total_size_mb']:.2f}MB "
                                    f"({stats['row_count']:,} rows, "
                                    f"{stats['fragmentation_percent']:.1f}% fragmented)")

    def _generate_recommendations(self, database_alias, output_format, verbose):
        """Generate maintenance recommendations"""
        self.stdout.write(f"Generating maintenance recommendations for database '{database_alias}'...")
        
        recommendations = get_maintenance_recommendations(database_alias)
        
        if 'error' in recommendations:
            raise CommandError(f"Failed to generate recommendations: {recommendations['error']}")
        
        if output_format == 'json':
            self.stdout.write(json.dumps(recommendations, indent=2))
        else:
            rec_list = recommendations.get('recommendations', [])
            
            if not rec_list:
                self.stdout.write("No maintenance recommendations at this time.")
                return
            
            self.stdout.write(f"Found {len(rec_list)} maintenance recommendations:")
            
            for i, rec in enumerate(rec_list, 1):
                priority = rec.get('priority', 'unknown').upper()
                rec_type = rec.get('type', 'unknown')
                message = rec.get('message', 'No message')
                action = rec.get('action', 'No action specified')
                
                priority_style = self.style.ERROR if priority == 'HIGH' else self.style.WARNING
                
                self.stdout.write(f"\n{i}. {priority_style(f'[{priority}]')} {rec_type}")
                self.stdout.write(f"   Message: {message}")
                self.stdout.write(f"   Recommended Action: {action}")
                
                if 'affected_tables' in rec:
                    tables = rec['affected_tables'][:5]  # Show first 5 tables
                    table_list = ', '.join(tables)
                    if len(rec['affected_tables']) > 5:
                        table_list += f" (and {len(rec['affected_tables']) - 5} more)"
                    self.stdout.write(f"   Affected Tables: {table_list}")

    def _display_maintenance_result(self, result, verbose):
        """Display maintenance result in text format"""
        status = result.get('status', 'unknown')
        duration = result.get('duration_seconds', 0)
        improvements = result.get('improvements', {})
        
        if status == 'completed':
            self.stdout.write(self.style.SUCCESS(f"Maintenance completed successfully in {duration:.2f}s"))
        else:
            self.stdout.write(self.style.ERROR(f"Maintenance failed: {result.get('error', 'Unknown error')}"))
            return
        
        # Display improvements
        size_reduction = improvements.get('size_reduction_mb', 0)
        frag_improvement = improvements.get('fragmentation_improvement_percent', 0)
        rows_cleaned = improvements.get('total_rows_cleaned', 0)
        
        self.stdout.write("\nImprovements:")
        self.stdout.write(f"  Size reduction: {size_reduction:.2f} MB")
        self.stdout.write(f"  Fragmentation improvement: {frag_improvement:.2f}%")
        self.stdout.write(f"  Rows cleaned: {rows_cleaned:,}")
        
        # Display task summaries
        if verbose:
            self.stdout.write("\nTasks completed:")
            for task in result.get('tasks', []):
                self.stdout.write(f"  - {task['task_type']}: {task['summary']}")