from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.caching.models import CacheConfiguration, CacheOptimization
from apps.caching.optimization import cache_optimizer
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Analyze cache performance and generate optimization recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cache-name',
            type=str,
            help='Analyze specific cache by name'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)'
        )
        parser.add_argument(
            '--apply-optimizations',
            action='store_true',
            help='Automatically apply high-impact optimizations'
        )
        parser.add_argument(
            '--min-impact-score',
            type=float,
            default=70.0,
            help='Minimum impact score for auto-apply (default: 70.0)'
        )
        parser.add_argument(
            '--benchmark',
            action='store_true',
            help='Run performance benchmark'
        )
        parser.add_argument(
            '--benchmark-duration',
            type=int,
            default=60,
            help='Benchmark duration in seconds (default: 60)'
        )

    def handle(self, *args, **options):
        cache_name = options.get('cache_name')
        days = options.get('days', 7)
        apply_optimizations = options.get('apply_optimizations', False)
        min_impact_score = options.get('min_impact_score', 70.0)
        run_benchmark = options.get('benchmark', False)
        benchmark_duration = options.get('benchmark_duration', 60)
        
        try:
            # Get cache configurations to analyze
            if cache_name:
                configs = CacheConfiguration.objects.filter(
                    name=cache_name, is_active=True
                )
                if not configs.exists():
                    self.stdout.write(
                        self.style.ERROR(f'Cache configuration "{cache_name}" not found or inactive')
                    )
                    return
            else:
                configs = CacheConfiguration.objects.filter(is_active=True)
            
            if not configs.exists():
                self.stdout.write(
                    self.style.WARNING('No active cache configurations found')
                )
                return
            
            total_analyzed = 0
            total_optimizations = 0
            total_applied = 0
            
            for config in configs:
                total_analyzed += 1
                
                self.stdout.write(f'\nAnalyzing cache: {config.name}')
                self.stdout.write('='*50)
                
                try:
                    # Perform analysis
                    analysis = cache_optimizer.analyze_cache_performance(config.name, days)
                    
                    if 'error' in analysis:
                        self.stdout.write(
                            self.style.ERROR(f'Analysis failed: {analysis["error"]}')
                        )
                        continue
                    
                    # Display analysis results
                    self.stdout.write(f'Analysis Period: {analysis["analysis_period"]}')
                    self.stdout.write(f'Total Metrics: {analysis["total_metrics"]}')
                    self.stdout.write(f'Optimization Score: {analysis["optimization_score"]:.1f}/100')
                    
                    # Performance summary
                    summary = analysis.get('performance_summary', {})
                    self.stdout.write('\nPerformance Summary:')
                    self.stdout.write(f'  Hit Ratio: {summary.get("average_hit_ratio", 0):.2%}')
                    self.stdout.write(f'  Avg Response Time: {summary.get("average_response_time_ms", 0):.2f}ms')
                    self.stdout.write(f'  Memory Usage: {summary.get("average_memory_usage_percent", 0):.1f}%')
                    self.stdout.write(f'  Error Rate: {summary.get("error_rate", 0):.2%}')
                    
                    # Trends
                    trends = analysis.get('trends', {})
                    if trends and 'error' not in trends:
                        self.stdout.write('\nTrends:')
                        if 'hit_ratio_trend' in trends:
                            trend_color = self.style.SUCCESS if trends['hit_ratio_trend'] == 'improving' else self.style.WARNING
                            self.stdout.write(f'  Hit Ratio: {trend_color(trends["hit_ratio_trend"])}')
                        if 'response_time_trend' in trends:
                            trend_color = self.style.SUCCESS if trends['response_time_trend'] == 'improving' else self.style.WARNING
                            self.stdout.write(f'  Response Time: {trend_color(trends["response_time_trend"])}')
                    
                    # Bottlenecks
                    bottlenecks = analysis.get('bottlenecks', [])
                    if bottlenecks:
                        self.stdout.write('\nBottlenecks:')
                        for bottleneck in bottlenecks:
                            severity_color = self.style.ERROR if bottleneck['severity'] == 'high' else self.style.WARNING
                            self.stdout.write(f'  {severity_color(bottleneck["type"])}: {bottleneck["description"]}')
                    
                    # Generate optimizations
                    optimizations = cache_optimizer.optimize_cache_configuration(config.name)
                    
                    if 'error' in optimizations:
                        self.stdout.write(
                            self.style.ERROR(f'Optimization generation failed: {optimizations["error"]}')
                        )
                        continue
                    
                    opt_count = optimizations.get('optimizations_found', 0)
                    total_optimizations += opt_count
                    
                    if opt_count > 0:
                        self.stdout.write(f'\nOptimization Recommendations ({opt_count} found):')
                        
                        # Get the optimization records
                        opt_records = CacheOptimization.objects.filter(
                            cache_name=config.name,
                            is_applied=False
                        ).order_by('-impact_score')
                        
                        for opt in opt_records:
                            impact_color = self.style.SUCCESS if opt.impact_score >= 70 else self.style.WARNING
                            self.stdout.write(f'  {impact_color(opt.optimization_type)} (Impact: {opt.impact_score:.1f})')
                            self.stdout.write(f'    {opt.expected_improvement}')
                            
                            # Auto-apply high-impact optimizations
                            if apply_optimizations and opt.impact_score >= min_impact_score:
                                try:
                                    result = cache_optimizer.apply_optimization(opt.id)
                                    if result.get('success'):
                                        self.stdout.write(
                                            self.style.SUCCESS(f'    ✓ Applied automatically')
                                        )
                                        total_applied += 1
                                    else:
                                        self.stdout.write(
                                            self.style.ERROR(f'    ✗ Auto-apply failed: {result.get("error")}')
                                        )
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.ERROR(f'    ✗ Auto-apply failed: {e}')
                                    )
                    else:
                        self.stdout.write('\nNo optimization recommendations found.')
                    
                    # Run benchmark if requested
                    if run_benchmark:
                        self.stdout.write(f'\nRunning benchmark ({benchmark_duration}s)...')
                        
                        benchmark = cache_optimizer.benchmark_cache_performance(
                            config.name, benchmark_duration
                        )
                        
                        if 'error' not in benchmark:
                            stats = benchmark.get('statistics', {})
                            throughput = benchmark.get('throughput', {})
                            
                            self.stdout.write('Benchmark Results:')
                            self.stdout.write(f'  Operations/sec: {throughput.get("operations_per_second", 0):.2f}')
                            self.stdout.write(f'  Avg Response Time: {stats.get("avg_response_time", 0):.2f}ms')
                            self.stdout.write(f'  95th Percentile: {stats.get("p95_response_time", 0):.2f}ms')
                            self.stdout.write(f'  Error Rate: {throughput.get("error_rate", 0):.2%}')
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'Benchmark failed: {benchmark["error"]}')
                            )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Analysis failed for {config.name}: {e}')
                    )
                    logger.error(f'Cache analysis failed for {config.name}: {e}')
            
            # Summary
            self.stdout.write('\n' + '='*60)
            self.stdout.write('Optimization Summary:')
            self.stdout.write(f'  Caches analyzed: {total_analyzed}')
            self.stdout.write(f'  Total optimizations found: {total_optimizations}')
            
            if apply_optimizations:
                self.stdout.write(f'  Optimizations applied: {total_applied}')
                if total_applied > 0:
                    self.stdout.write(
                        self.style.SUCCESS('  Automatic optimizations have been applied!')
                    )
                    self.stdout.write('  Monitor cache performance to verify improvements.')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Optimization command failed: {e}')
            )
            logger.error(f'Cache optimization command failed: {e}')