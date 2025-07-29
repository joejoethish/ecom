"""
Management command to display password reset system statistics and health metrics.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta
from apps.authentication.models import PasswordResetToken, PasswordResetAttempt


class Command(BaseCommand):
    help = 'Display password reset system statistics and health metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed hourly breakdown',
        )
        parser.add_argument(
            '--export-csv',
            type=str,
            help='Export statistics to CSV file',
        )

    def handle(self, *args, **options):
        days = options['days']
        detailed = options['detailed']
        export_csv = options['export_csv']

        self.stdout.write(
            self.style.SUCCESS('Password Reset System Statistics')
        )
        self.stdout.write('=' * 60)

        now = timezone.now()
        period_start = now - timedelta(days=days)

        # Token statistics
        self.show_token_statistics(now, period_start, days)
        
        # Attempt statistics
        self.show_attempt_statistics(now, period_start, days)
        
        # Usage patterns
        self.show_usage_patterns(period_start, detailed)
        
        # Health indicators
        self.show_health_indicators(now)
        
        # Export to CSV if requested
        if export_csv:
            self.export_to_csv(export_csv, period_start, days)

    def show_token_statistics(self, now, period_start, days):
        """Display token-related statistics."""
        self.stdout.write(f'\nToken Statistics (Last {days} days):')
        self.stdout.write('-' * 40)

        # Overall counts
        total_tokens = PasswordResetToken.objects.count()
        active_tokens = PasswordResetToken.objects.filter(
            is_used=False,
            expires_at__gt=now
        ).count()
        expired_tokens = PasswordResetToken.objects.filter(
            expires_at__lt=now,
            is_used=False
        ).count()
        used_tokens = PasswordResetToken.objects.filter(is_used=True).count()

        # Period-specific counts
        period_created = PasswordResetToken.objects.filter(
            created_at__gte=period_start
        ).count()
        period_used = PasswordResetToken.objects.filter(
            is_used=True,
            updated_at__gte=period_start
        ).count()

        self.stdout.write(f'  Total tokens in system: {total_tokens}')
        self.stdout.write(f'  Active tokens: {active_tokens}')
        self.stdout.write(f'  Expired tokens: {expired_tokens}')
        self.stdout.write(f'  Used tokens: {used_tokens}')
        self.stdout.write(f'  Created in period: {period_created}')
        self.stdout.write(f'  Used in period: {period_used}')

        # Calculate utilization rate
        if period_created > 0:
            utilization_rate = (period_used / period_created) * 100
            self.stdout.write(f'  Utilization rate: {utilization_rate:.1f}%')

    def show_attempt_statistics(self, now, period_start, days):
        """Display attempt-related statistics."""
        self.stdout.write(f'\nAttempt Statistics (Last {days} days):')
        self.stdout.write('-' * 40)

        # Overall counts
        total_attempts = PasswordResetAttempt.objects.count()
        period_attempts = PasswordResetAttempt.objects.filter(
            created_at__gte=period_start
        ).count()
        successful_attempts = PasswordResetAttempt.objects.filter(
            created_at__gte=period_start,
            success=True
        ).count()

        # Calculate success rate
        success_rate = (successful_attempts / period_attempts * 100) if period_attempts > 0 else 0

        # Top IPs by attempt count
        top_ips = PasswordResetAttempt.objects.filter(
            created_at__gte=period_start
        ).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        self.stdout.write(f'  Total attempts in system: {total_attempts}')
        self.stdout.write(f'  Attempts in period: {period_attempts}')
        self.stdout.write(f'  Successful attempts: {successful_attempts}')
        self.stdout.write(f'  Success rate: {success_rate:.1f}%')

        if top_ips:
            self.stdout.write('  Top IPs by attempts:')
            for ip_data in top_ips:
                self.stdout.write(f'    {ip_data["ip_address"]}: {ip_data["count"]} attempts')

    def show_usage_patterns(self, period_start, detailed):
        """Display usage patterns over time."""
        self.stdout.write('\nUsage Patterns:')
        self.stdout.write('-' * 40)

        if detailed:
            # Hourly breakdown
            hourly_data = PasswordResetToken.objects.filter(
                created_at__gte=period_start
            ).annotate(
                hour=TruncHour('created_at')
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('hour')

            self.stdout.write('  Hourly token creation:')
            for hour_data in hourly_data[-24:]:  # Last 24 hours
                hour = hour_data['hour'].strftime('%Y-%m-%d %H:00')
                count = hour_data['count']
                self.stdout.write(f'    {hour}: {count} tokens')
        else:
            # Daily breakdown
            daily_data = PasswordResetToken.objects.filter(
                created_at__gte=period_start
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            self.stdout.write('  Daily token creation:')
            for day_data in daily_data:
                date = day_data['date'].strftime('%Y-%m-%d')
                count = day_data['count']
                self.stdout.write(f'    {date}: {count} tokens')

    def show_health_indicators(self, now):
        """Display system health indicators."""
        self.stdout.write('\nSystem Health Indicators:')
        self.stdout.write('-' * 40)

        # Check for issues
        issues = []
        
        # High number of expired tokens
        expired_count = PasswordResetToken.objects.filter(
            expires_at__lt=now,
            is_used=False
        ).count()
        if expired_count > 100:
            issues.append(f'High number of expired tokens: {expired_count}')

        # Old unused tokens
        old_cutoff = now - timedelta(days=1)
        old_tokens = PasswordResetToken.objects.filter(
            created_at__lt=old_cutoff,
            is_used=False,
            expires_at__gt=now
        ).count()
        if old_tokens > 50:
            issues.append(f'Many old unused tokens: {old_tokens}')

        # Recent high failure rate
        recent_cutoff = now - timedelta(hours=24)
        recent_attempts = PasswordResetAttempt.objects.filter(
            created_at__gte=recent_cutoff
        ).count()
        recent_failures = PasswordResetAttempt.objects.filter(
            created_at__gte=recent_cutoff,
            success=False
        ).count()
        
        if recent_attempts > 0:
            failure_rate = (recent_failures / recent_attempts) * 100
            if failure_rate > 50:
                issues.append(f'High failure rate (24h): {failure_rate:.1f}%')

        # Display health status
        if issues:
            self.stdout.write(self.style.WARNING('  Issues detected:'))
            for issue in issues:
                self.stdout.write(f'    ⚠ {issue}')
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ System appears healthy'))

        # Recommendations
        self.stdout.write('\n  Recommendations:')
        if expired_count > 50:
            self.stdout.write('    • Run token cleanup to remove expired tokens')
        if old_tokens > 20:
            self.stdout.write('    • Consider reducing token expiry time')
        if recent_attempts > 0 and (recent_failures / recent_attempts) > 0.3:
            self.stdout.write('    • Investigate high failure rate causes')

    def export_to_csv(self, filename, period_start, days):
        """Export statistics to CSV file."""
        import csv
        
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['Date', 'Tokens Created', 'Tokens Used', 'Attempts', 'Successful Attempts'])
                
                # Get daily data
                daily_tokens = dict(PasswordResetToken.objects.filter(
                    created_at__gte=period_start
                ).annotate(
                    date=TruncDate('created_at')
                ).values('date').annotate(
                    count=Count('id')
                ).values_list('date', 'count'))
                
                daily_used = dict(PasswordResetToken.objects.filter(
                    is_used=True,
                    updated_at__gte=period_start
                ).annotate(
                    date=TruncDate('updated_at')
                ).values('date').annotate(
                    count=Count('id')
                ).values_list('date', 'count'))
                
                daily_attempts = dict(PasswordResetAttempt.objects.filter(
                    created_at__gte=period_start
                ).annotate(
                    date=TruncDate('created_at')
                ).values('date').annotate(
                    count=Count('id')
                ).values_list('date', 'count'))
                
                daily_successful = dict(PasswordResetAttempt.objects.filter(
                    created_at__gte=period_start,
                    success=True
                ).annotate(
                    date=TruncDate('created_at')
                ).values('date').annotate(
                    count=Count('id')
                ).values_list('date', 'count'))
                
                # Write data for each day
                current_date = period_start.date()
                end_date = timezone.now().date()
                
                while current_date <= end_date:
                    writer.writerow([
                        current_date.strftime('%Y-%m-%d'),
                        daily_tokens.get(current_date, 0),
                        daily_used.get(current_date, 0),
                        daily_attempts.get(current_date, 0),
                        daily_successful.get(current_date, 0)
                    ])
                    current_date += timedelta(days=1)
            
            self.stdout.write(
                self.style.SUCCESS(f'\nStatistics exported to {filename}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to export CSV: {str(e)}')
            )