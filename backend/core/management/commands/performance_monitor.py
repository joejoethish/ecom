"""
Django management command for performance monitoring and optimization

This command provides CLI access to the performance monitoring system:
- Start/stop monitoring
- View current metrics and recommendations
- Generate reports
- Configure thresholds
"""

import json
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from core.performance_monitor import get_performance_monitor, initialize_performance_monitoring


class Command(BaseCommand):
    help = 'Performance monitoring and optimization management'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status', 'metrics', 'recommendations', 'capacity', 'regressions', 'report', 'reset-baseline', 'configure'],
            help='Action to perform'
        )
        
        parser.add_argument(
            '--database',
            type=str,
            default='default',
            help='Database alias to monitor (default: default)'
        )
        
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Monitoring interval in seconds (default: 60)'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Limit number of results (default: 20)'
        )
        
        parser.add_argument(
            '--metric',
            type=str,
            help='Specific metric for baseline reset'
        )
        
        parser.add_argument(
            '--regression-threshold',
            type=float,
            help='Regression detection threshold (0.0-1.0)'
        )
        
        parser.add_argument(
            '--capacity-warning',
            type=float,
            help='Capacity warning threshold (0.0-1.0)'
        )
        
        parser.add_argument(
            '--capacity-critical',
            type=float,
            help='Capacity critical threshold (0.0-1.0)'
        )
        
        parser.add_argument(
            '--output-format',
            choices=['table', 'json', 'csv'],
            default='table',
            help='Output format (default: table)'
        )
        
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Watch mode - continuously update display'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'start':
                self.start_monitoring(options)
            elif action == 'stop':
                self.stop_monitoring(options)
            elif action == 'status':
                self.show_status(options)
            elif action == 'metrics':
                self.show_metrics(options)
            elif action == 'recommendations':
                self.show_recommendations(options)
            elif action == 'capacity':
                self.show_capacity(options)
            elif action == 'regressions':
                self.show_regressions(options)
            elif action == 'report':
                self.generate_report(options)
            elif action == 'reset-baseline':
                self.reset_baseline(options)
            elif action == 'configure':
                self.configure_thresholds(options)
                
        except Exception as e:
            raise CommandError(f'Error executing {action}: {str(e)}')

    def start_monitoring(self, options):
        """Start performance monitoring"""
        interval = options['interval']
        
        self.stdout.write(f"Starting performance monitoring with {interval}s interval...")
        
        monitor = initialize_performance_monitoring(interval)
        
        self.stdout.write(
            self.style.SUCCESS(f'Performance monitoring started successfully')
        )
        
        if options['watch']:
            self.watch_metrics(monitor, options)

    def stop_monitoring(self, options):
        """Stop performance monitoring"""
        self.stdout.write("Stopping performance monitoring...")
        
        monitor = get_performance_monitor()
        monitor.stop_monitoring()
        
        self.stdout.write(
            self.style.SUCCESS('Performance monitoring stopped')
        )

    def show_status(self, options):
        """Show monitoring status"""
        monitor = get_performance_monitor()
        
        status_info = {
            'monitoring_enabled': monitor.monitoring_enabled,
            'monitoring_interval': monitor.monitoring_interval,
            'regression_threshold': monitor.regression_threshold,
            'capacity_warning_threshold': monitor.capacity_warning_threshold,
            'capacity_critical_threshold': monitor.capacity_critical_threshold,
            'databases_monitored': list(settings.DATABASES.keys()),
            'total_recommendations': len(monitor.optimization_recommendations),
            'total_capacity_recommendations': len(monitor.capacity_recommendations),
            'total_regressions': len(monitor.regressions),
            'baselines_count': len(monitor.baselines)
        }
        
        if options['output_format'] == 'json':
            self.stdout.write(json.dumps(status_info, indent=2))
        else:
            self.stdout.write("Performance Monitoring Status")
            self.stdout.write("=" * 40)
            for key, value in status_info.items():
                self.stdout.write(f"{key.replace('_', ' ').title()}: {value}")

    def show_metrics(self, options):
        """Show current performance metrics"""
        monitor = get_performance_monitor()
        db_alias = options['database']
        
        metrics = monitor.get_current_performance_metrics(db_alias)
        
        if options['output_format'] == 'json':
            self.stdout.write(json.dumps(metrics, indent=2))
        elif options['output_format'] == 'csv':
            self.output_metrics_csv(metrics)
        else:
            self.output_metrics_table(metrics, db_alias)
        
        if options['watch']:
            self.watch_metrics(monitor, options)

    def output_metrics_table(self, metrics, db_alias):
        """Output metrics in table format"""
        self.stdout.write(f"\nPerformance Metrics for {db_alias}")
        self.stdout.write("=" * 60)
        
        if not metrics:
            self.stdout.write("No metrics available")
            return
        
        # Header
        self.stdout.write(f"{'Metric':<20} {'Current':<10} {'Avg 10min':<12} {'Trend':<10}")
        self.stdout.write("-" * 60)
        
        # Data rows
        for metric_name, data in metrics.items():
            current = f"{data['current']:.2f}"
            avg = f"{data['average_10min']:.2f}"
            trend = f"{data['trend']:+.4f}"
            
            self.stdout.write(f"{metric_name:<20} {current:<10} {avg:<12} {trend:<10}")

    def output_metrics_csv(self, metrics):
        """Output metrics in CSV format"""
        self.stdout.write("metric,current,average_10min,trend")
        for metric_name, data in metrics.items():
            self.stdout.write(f"{metric_name},{data['current']:.2f},{data['average_10min']:.2f},{data['trend']:+.4f}")

    def show_recommendations(self, options):
        """Show optimization recommendations"""
        monitor = get_performance_monitor()
        limit = options['limit']
        
        recommendations = monitor.get_optimization_recommendations(limit)
        
        if options['output_format'] == 'json':
            self.stdout.write(json.dumps(recommendations, indent=2))
        else:
            self.output_recommendations_table(recommendations)

    def output_recommendations_table(self, recommendations):
        """Output recommendations in table format"""
        self.stdout.write(f"\nOptimization Recommendations ({len(recommendations)} total)")
        self.stdout.write("=" * 80)
        
        if not recommendations:
            self.stdout.write("No recommendations available")
            return
        
        for i, rec in enumerate(recommendations, 1):
            self.stdout.write(f"\n{i}. Priority: {rec['priority'].upper()}")
            self.stdout.write(f"   Query: {rec['query_text'][:60]}...")
            self.stdout.write(f"   Estimated Improvement: {rec['estimated_improvement']:.1f}%")
            self.stdout.write(f"   Implementation Effort: {rec['implementation_effort']}")
            self.stdout.write(f"   Timestamp: {rec['timestamp']}")
            
            self.stdout.write("   Recommendations:")
            for recommendation in rec['recommendations'][:3]:  # Show top 3
                self.stdout.write(f"   - {recommendation}")
            
            if len(rec['recommendations']) > 3:
                self.stdout.write(f"   ... and {len(rec['recommendations']) - 3} more")

    def show_capacity(self, options):
        """Show capacity recommendations"""
        monitor = get_performance_monitor()
        limit = options['limit']
        
        capacity_recs = monitor.get_capacity_recommendations(limit)
        
        if options['output_format'] == 'json':
            self.stdout.write(json.dumps(capacity_recs, indent=2))
        else:
            self.output_capacity_table(capacity_recs)

    def output_capacity_table(self, capacity_recs):
        """Output capacity recommendations in table format"""
        self.stdout.write(f"\nCapacity Planning Recommendations ({len(capacity_recs)} total)")
        self.stdout.write("=" * 80)
        
        if not capacity_recs:
            self.stdout.write("No capacity recommendations available")
            return
        
        for i, rec in enumerate(capacity_recs, 1):
            self.stdout.write(f"\n{i}. Resource: {rec['resource_type'].upper()}")
            self.stdout.write(f"   Current Usage: {rec['current_usage']:.1f}%")
            self.stdout.write(f"   Projected Usage: {rec['projected_usage']:.1f}%")
            self.stdout.write(f"   Time to Capacity: {rec['time_to_capacity']} days")
            self.stdout.write(f"   Urgency: {rec['urgency'].upper()}")
            self.stdout.write(f"   Recommended Action: {rec['recommended_action']}")
            
            if rec.get('cost_estimate'):
                self.stdout.write(f"   Estimated Cost: ${rec['cost_estimate']:.2f}/month")

    def show_regressions(self, options):
        """Show performance regressions"""
        monitor = get_performance_monitor()
        limit = options['limit']
        
        regressions = monitor.get_performance_regressions(limit)
        
        if options['output_format'] == 'json':
            self.stdout.write(json.dumps(regressions, indent=2))
        else:
            self.output_regressions_table(regressions)

    def output_regressions_table(self, regressions):
        """Output regressions in table format"""
        self.stdout.write(f"\nPerformance Regressions ({len(regressions)} total)")
        self.stdout.write("=" * 80)
        
        if not regressions:
            self.stdout.write("No performance regressions detected")
            return
        
        for i, reg in enumerate(regressions, 1):
            self.stdout.write(f"\n{i}. Database: {reg['database_alias']}")
            self.stdout.write(f"   Metric: {reg['metric_name']}")
            self.stdout.write(f"   Baseline: {reg['baseline_value']:.2f}")
            self.stdout.write(f"   Current: {reg['current_value']:.2f}")
            self.stdout.write(f"   Regression: {reg['regression_percentage']:.1f}%")
            self.stdout.write(f"   Severity: {reg['severity'].upper()}")
            self.stdout.write(f"   Detected: {reg['detection_timestamp']}")
            
            self.stdout.write("   Potential Causes:")
            for cause in reg['potential_causes'][:3]:
                self.stdout.write(f"   - {cause}")

    def generate_report(self, options):
        """Generate comprehensive performance report"""
        monitor = get_performance_monitor()
        db_alias = options['database']
        
        # Collect all data
        metrics = monitor.get_current_performance_metrics(db_alias)
        recommendations = monitor.get_optimization_recommendations(10)
        capacity_recs = monitor.get_capacity_recommendations(5)
        regressions = monitor.get_performance_regressions(10)
        baselines = monitor.get_performance_baselines()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'database': db_alias,
            'current_metrics': metrics,
            'optimization_recommendations': recommendations,
            'capacity_recommendations': capacity_recs,
            'performance_regressions': regressions,
            'baselines_count': len(baselines),
            'summary': {
                'total_recommendations': len(recommendations),
                'high_priority_recommendations': len([r for r in recommendations if r['priority'] in ['high', 'critical']]),
                'capacity_issues': len([c for c in capacity_recs if c['urgency'] in ['high', 'critical']]),
                'active_regressions': len(regressions),
                'critical_regressions': len([r for r in regressions if r['severity'] == 'critical'])
            }
        }
        
        if options['output_format'] == 'json':
            self.stdout.write(json.dumps(report, indent=2))
        else:
            self.output_report_text(report)

    def output_report_text(self, report):
        """Output report in text format"""
        self.stdout.write(f"\nPerformance Monitoring Report")
        self.stdout.write(f"Generated: {report['generated_at']}")
        self.stdout.write(f"Database: {report['database']}")
        self.stdout.write("=" * 60)
        
        # Summary
        summary = report['summary']
        self.stdout.write(f"\nSUMMARY:")
        self.stdout.write(f"  Total Recommendations: {summary['total_recommendations']}")
        self.stdout.write(f"  High Priority Recommendations: {summary['high_priority_recommendations']}")
        self.stdout.write(f"  Capacity Issues: {summary['capacity_issues']}")
        self.stdout.write(f"  Active Regressions: {summary['active_regressions']}")
        self.stdout.write(f"  Critical Regressions: {summary['critical_regressions']}")
        
        # Current metrics
        if report['current_metrics']:
            self.stdout.write(f"\nCURRENT METRICS:")
            self.output_metrics_table(report['current_metrics'], report['database'])
        
        # Top recommendations
        if report['optimization_recommendations']:
            self.stdout.write(f"\nTOP OPTIMIZATION RECOMMENDATIONS:")
            self.output_recommendations_table(report['optimization_recommendations'][:5])
        
        # Capacity issues
        if report['capacity_recommendations']:
            self.stdout.write(f"\nCAPACITY RECOMMENDATIONS:")
            self.output_capacity_table(report['capacity_recommendations'])
        
        # Recent regressions
        if report['performance_regressions']:
            self.stdout.write(f"\nRECENT REGRESSIONS:")
            self.output_regressions_table(report['performance_regressions'][:5])

    def reset_baseline(self, options):
        """Reset performance baseline"""
        monitor = get_performance_monitor()
        metric = options.get('metric')
        
        if not metric:
            raise CommandError("--metric parameter is required for reset-baseline action")
        
        monitor.reset_baseline(metric)
        self.stdout.write(
            self.style.SUCCESS(f'Baseline reset for metric: {metric}')
        )

    def configure_thresholds(self, options):
        """Configure monitoring thresholds"""
        monitor = get_performance_monitor()
        
        regression_threshold = options.get('regression_threshold')
        capacity_warning = options.get('capacity_warning')
        capacity_critical = options.get('capacity_critical')
        
        if not any([regression_threshold, capacity_warning, capacity_critical]):
            raise CommandError("At least one threshold parameter is required")
        
        monitor.update_thresholds(
            regression_threshold=regression_threshold,
            capacity_warning=capacity_warning,
            capacity_critical=capacity_critical
        )
        
        self.stdout.write(
            self.style.SUCCESS('Monitoring thresholds updated successfully')
        )

    def watch_metrics(self, monitor, options):
        """Watch mode - continuously update metrics display"""
        db_alias = options['database']
        
        try:
            self.stdout.write("\nWatching metrics (Press Ctrl+C to stop)...")
            self.stdout.write("Updating every 30 seconds\n")
            
            while True:
                # Clear screen (works on most terminals)
                self.stdout.write('\033[2J\033[H')
                
                # Show current time
                self.stdout.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Show metrics
                metrics = monitor.get_current_performance_metrics(db_alias)
                self.output_metrics_table(metrics, db_alias)
                
                # Show recent recommendations
                recommendations = monitor.get_optimization_recommendations(3)
                if recommendations:
                    self.stdout.write(f"\nRecent Recommendations:")
                    for i, rec in enumerate(recommendations, 1):
                        self.stdout.write(f"{i}. {rec['priority'].upper()}: {rec['query_text'][:50]}...")
                
                # Show capacity status
                capacity_recs = monitor.get_capacity_recommendations(3)
                if capacity_recs:
                    self.stdout.write(f"\nCapacity Status:")
                    for rec in capacity_recs:
                        if rec['urgency'] in ['high', 'critical']:
                            self.stdout.write(f"⚠️  {rec['resource_type']}: {rec['current_usage']:.1f}% ({rec['urgency']})")
                
                time.sleep(30)
                
        except KeyboardInterrupt:
            self.stdout.write("\nStopped watching metrics")