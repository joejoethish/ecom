"""
Management command to analyze logs and generate reports.
"""
import os
import json
import datetime
from collections import Counter, defaultdict
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.logs.models import SystemLog, SecurityEvent, PerformanceMetric, BusinessMetric


class Command(BaseCommand):
    help = 'Analyze logs and generate reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze'
        )
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['security', 'performance', 'business', 'all'],
            default='all',
            help='Type of report to generate'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='console',
            choices=['console', 'file', 'both'],
            help='Where to output the report'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        report_type = options['report_type']
        output = options['output']
        
        # Calculate the start date
        start_date = timezone.now() - datetime.timedelta(days=days)
        
        self.stdout.write(f"Analyzing logs from {start_date.strftime('%Y-%m-%d')} to now...")
        
        # Generate the requested reports
        if report_type in ['security', 'all']:
            security_report = self.generate_security_report(start_date)
            self.output_report('Security Report', security_report, output)
        
        if report_type in ['performance', 'all']:
            performance_report = self.generate_performance_report(start_date)
            self.output_report('Performance Report', performance_report, output)
        
        if report_type in ['business', 'all']:
            business_report = self.generate_business_report(start_date)
            self.output_report('Business Metrics Report', business_report, output)
        
        self.stdout.write(self.style.SUCCESS('Log analysis complete!'))
    
    def generate_security_report(self, start_date):
        """
        Generate a security report from the logs.
        """
        # Get security events from the database
        security_events = SecurityEvent.objects.filter(timestamp__gte=start_date)
        
        # Count events by type
        event_types = Counter(security_events.values_list('event_type', flat=True))
        
        # Count events by IP address
        ip_addresses = Counter(security_events.values_list('ip_address', flat=True))
        
        # Count events by username
        usernames = Counter(
            username for username in security_events.values_list('username', flat=True)
            if username and username != 'anonymous'
        )
        
        # Find suspicious IPs (those with multiple security events)
        suspicious_ips = [ip for ip, count in ip_addresses.items() if count >= 5]
        
        # Find accounts with multiple security events
        suspicious_accounts = [username for username, count in usernames.items() if count >= 3]
        
        # Generate the report
        report = {
            'total_security_events': security_events.count(),
            'event_types': dict(event_types.most_common(10)),
            'top_ip_addresses': dict(ip_addresses.most_common(10)),
            'top_usernames': dict(usernames.most_common(10)),
            'suspicious_ips': suspicious_ips,
            'suspicious_accounts': suspicious_accounts,
            'login_failures': security_events.filter(event_type='login_failure').count(),
            'brute_force_attempts': security_events.filter(event_type='brute_force_attempt').count(),
            'access_violations': security_events.filter(event_type='access_violation').count(),
            'csrf_failures': security_events.filter(event_type='csrf_failure').count(),
            'rate_limit_exceeded': security_events.filter(event_type='rate_limit_exceeded').count(),
        }
        
        return report
    
    def generate_performance_report(self, start_date):
        """
        Generate a performance report from the logs.
        """
        # Get performance metrics from the database
        performance_metrics = PerformanceMetric.objects.filter(timestamp__gte=start_date)
        
        # Calculate average response time
        response_times = list(performance_metrics.values_list('response_time', flat=True))
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Find slow endpoints
        endpoint_times = defaultdict(list)
        for metric in performance_metrics:
            if metric.endpoint:
                endpoint_times[metric.endpoint].append(metric.response_time)
        
        slow_endpoints = {
            endpoint: {
                'avg_time': sum(times) / len(times),
                'max_time': max(times),
                'count': len(times)
            }
            for endpoint, times in endpoint_times.items()
            if sum(times) / len(times) > 500  # Endpoints with avg time > 500ms
        }
        
        # Generate the report
        report = {
            'total_requests': performance_metrics.count(),
            'average_response_time': avg_response_time,
            'slow_endpoints': slow_endpoints,
            'max_response_time': max(response_times) if response_times else 0,
            'p95_response_time': sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else 0,
            'requests_over_1s': sum(1 for t in response_times if t > 1000),
            'requests_over_2s': sum(1 for t in response_times if t > 2000),
            'requests_over_5s': sum(1 for t in response_times if t > 5000),
        }
        
        return report
    
    def generate_business_report(self, start_date):
        """
        Generate a business metrics report from the logs.
        """
        # Get business metrics from the database
        business_metrics = BusinessMetric.objects.filter(timestamp__gte=start_date)
        
        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for metric in business_metrics:
            metrics_by_name[metric.name].append(metric.value)
        
        # Calculate averages for each metric
        metric_averages = {
            name: sum(values) / len(values)
            for name, values in metrics_by_name.items()
        }
        
        # Get specific metrics if available
        active_users = metrics_by_name.get('active_users', [])
        conversion_rate = metrics_by_name.get('conversion_rate', [])
        average_order_value = metrics_by_name.get('average_order_value', [])
        cart_abandonment_rate = metrics_by_name.get('cart_abandonment_rate', [])
        
        # Generate the report
        report = {
            'total_metrics_recorded': business_metrics.count(),
            'metric_types': list(metrics_by_name.keys()),
            'metric_averages': metric_averages,
            'active_users': {
                'average': sum(active_users) / len(active_users) if active_users else 0,
                'max': max(active_users) if active_users else 0,
                'trend': 'up' if len(active_users) > 1 and active_users[-1] > active_users[0] else 'down'
            },
            'conversion_rate': {
                'average': sum(conversion_rate) / len(conversion_rate) if conversion_rate else 0,
                'max': max(conversion_rate) if conversion_rate else 0,
                'trend': 'up' if len(conversion_rate) > 1 and conversion_rate[-1] > conversion_rate[0] else 'down'
            },
            'average_order_value': {
                'average': sum(average_order_value) / len(average_order_value) if average_order_value else 0,
                'max': max(average_order_value) if average_order_value else 0,
                'trend': 'up' if len(average_order_value) > 1 and average_order_value[-1] > average_order_value[0] else 'down'
            },
            'cart_abandonment_rate': {
                'average': sum(cart_abandonment_rate) / len(cart_abandonment_rate) if cart_abandonment_rate else 0,
                'min': min(cart_abandonment_rate) if cart_abandonment_rate else 0,
                'trend': 'down' if len(cart_abandonment_rate) > 1 and cart_abandonment_rate[-1] < cart_abandonment_rate[0] else 'up'
            }
        }
        
        return report
    
    def output_report(self, title, report, output_type):
        """
        Output the report to the console and/or file.
        """
        # Format the report as JSON
        report_json = json.dumps(report, indent=2)
        
        # Output to console
        if output_type in ['console', 'both']:
            self.stdout.write(f"\n{title}\n{'=' * len(title)}\n")
            self.stdout.write(report_json)
        
        # Output to file
        if output_type in ['file', 'both']:
            reports_dir = os.path.join(settings.BASE_DIR, 'logs', 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{title.lower().replace(' ', '_')}_{timestamp}.json"
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(report_json)
            
            self.stdout.write(f"Report saved to {filepath}")