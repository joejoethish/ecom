"""
Django management command for database performance benchmarking
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from core.performance_benchmarker import performance_benchmarker, LoadTestConfig


class Command(BaseCommand):
    help = 'Run database performance benchmarks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            type=str,
            default='default',
            help='Database alias to benchmark (default: default)'
        )
        
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['connection', 'crud', 'complex', 'load', 'comprehensive', 'compare'],
            default='comprehensive',
            help='Type of benchmark to run'
        )
        
        parser.add_argument(
            '--iterations',
            type=int,
            default=100,
            help='Number of iterations for connection/CRUD tests'
        )
        
        parser.add_argument(
            '--concurrent-users',
            type=int,
            default=10,
            help='Number of concurrent users for load testing'
        )
        
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Duration in seconds for load testing'
        )
        
        parser.add_argument(
            '--compare-databases',
            nargs='+',
            help='List of database aliases to compare'
        )
        
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path for results (JSON format)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        database_alias = options['database']
        test_type = options['test_type']
        
        if options['verbose']:
            self.stdout.write(f"Starting {test_type} benchmark for database: {database_alias}")
        
        try:
            if test_type == 'connection':
                suite = performance_benchmarker.benchmark_connection_performance(
                    database_alias, options['iterations']
                )
                results = performance_benchmarker.generate_performance_report(suite)
                
            elif test_type == 'crud':
                suite = performance_benchmarker.benchmark_crud_operations(
                    database_alias, options['iterations']
                )
                results = performance_benchmarker.generate_performance_report(suite)
                
            elif test_type == 'complex':
                suite = performance_benchmarker.benchmark_complex_queries(database_alias)
                results = performance_benchmarker.generate_performance_report(suite)
                
            elif test_type == 'load':
                config = LoadTestConfig(
                    concurrent_users=options['concurrent_users'],
                    test_duration=options['duration'],
                    queries_per_user=options['duration'] // 2
                )
                suite = performance_benchmarker.run_load_test(database_alias, config)
                results = performance_benchmarker.generate_performance_report(suite)
                
            elif test_type == 'comprehensive':
                results = performance_benchmarker.run_comprehensive_benchmark(database_alias)
                
            elif test_type == 'compare':
                if not options['compare_databases']:
                    raise CommandError("--compare-databases is required for comparison tests")
                
                results = performance_benchmarker.compare_databases(
                    options['compare_databases']
                )
            
            # Output results
            if options['output_file']:
                with open(options['output_file'], 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                self.stdout.write(
                    self.style.SUCCESS(f"Results saved to {options['output_file']}")
                )
            
            # Display summary
            self._display_results_summary(results, test_type, options['verbose'])
            
        except Exception as e:
            raise CommandError(f"Benchmark failed: {str(e)}")

    def _display_results_summary(self, results, test_type, verbose=False):
        """Display benchmark results summary"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("BENCHMARK RESULTS SUMMARY"))
        self.stdout.write("="*60)
        
        if test_type == 'compare':
            self._display_comparison_summary(results)
        elif test_type == 'comprehensive':
            self._display_comprehensive_summary(results, verbose)
        else:
            self._display_single_test_summary(results, verbose)

    def _display_single_test_summary(self, results, verbose=False):
        """Display summary for single test type"""
        if 'performance_metrics' in results:
            metrics = results['performance_metrics']
            
            self.stdout.write(f"Total Tests: {metrics['total_tests']}")
            self.stdout.write(f"Success Rate: {metrics['success_rate']:.1f}%")
            self.stdout.write(f"Average Execution Time: {metrics['average_execution_time']:.4f}s")
            self.stdout.write(f"Median Execution Time: {metrics['median_execution_time']:.4f}s")
            
            if verbose and 'percentiles' in results:
                percentiles = results['percentiles']
                self.stdout.write(f"95th Percentile: {percentiles['p95']:.4f}s")
                self.stdout.write(f"99th Percentile: {percentiles['p99']:.4f}s")
            
            if metrics['failed_tests'] > 0:
                self.stdout.write(
                    self.style.WARNING(f"Failed Tests: {metrics['failed_tests']}")
                )

    def _display_comprehensive_summary(self, results, verbose=False):
        """Display summary for comprehensive benchmark"""
        if 'benchmarks' in results:
            for test_name, test_results in results['benchmarks'].items():
                self.stdout.write(f"\n{test_name.upper()} BENCHMARK:")
                self.stdout.write("-" * 40)
                self._display_single_test_summary(test_results, verbose)

    def _display_comparison_summary(self, results):
        """Display summary for database comparison"""
        if 'summary' in results:
            for test_type, summary in results['summary'].items():
                self.stdout.write(f"\n{test_type.upper()} COMPARISON:")
                self.stdout.write("-" * 40)
                
                if 'best_performer' in summary:
                    self.stdout.write(
                        self.style.SUCCESS(f"Best Performer: {summary['best_performer']}")
                    )
                
                if 'performance_difference' in summary:
                    for db, diff in summary['performance_difference'].items():
                        self.stdout.write(f"{db}: {diff}")