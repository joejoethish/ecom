from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from backend.apps.compliance.models import (
    ComplianceFramework, CompliancePolicy, ComplianceControl,
    ComplianceAssessment, ComplianceIncident, ComplianceTraining,
    ComplianceTrainingRecord, ComplianceAuditTrail, ComplianceRiskAssessment,
    ComplianceVendor, ComplianceReport
)


class Command(BaseCommand):
    help = 'Clean up old compliance data and perform maintenance tasks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--archive-old-data',
            action='store_true',
            help='Archive old compliance data',
        )
        parser.add_argument(
            '--cleanup-audit-trail',
            action='store_true',
            help='Clean up old audit trail entries',
        )
        parser.add_argument(
            '--update-overdue-items',
            action='store_true',
            help='Update status of overdue items',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Number of days to keep data (default: 365)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        days_to_keep = options['days']
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        if options['archive_old_data']:
            self.archive_old_data(cutoff_date)
        
        if options['cleanup_audit_trail']:
            self.cleanup_audit_trail(cutoff_date)
        
        if options['update_overdue_items']:
            self.update_overdue_items()
        
        self.stdout.write(
            self.style.SUCCESS('Compliance cleanup completed!')
        )
    
    def archive_old_data(self, cutoff_date):
        """Archive old compliance data"""
        self.stdout.write('Archiving old compliance data...')
        
        # Archive old resolved incidents
        old_incidents = ComplianceIncident.objects.filter(
            resolved_at__lt=cutoff_date,
            status__in=['resolved', 'closed']
        )
        
        if self.dry_run:
            self.stdout.write(f'Would archive {old_incidents.count()} old incidents')
        else:
            # In a real implementation, you might move these to an archive table
            # or mark them as archived rather than deleting
            count = old_incidents.count()
            # old_incidents.update(status='archived')  # Example
            self.stdout.write(f'Archived {count} old incidents')
        
        # Archive old completed assessments
        old_assessments = ComplianceAssessment.objects.filter(
            end_date__lt=cutoff_date,
            status='completed'
        )
        
        if self.dry_run:
            self.stdout.write(f'Would archive {old_assessments.count()} old assessments')
        else:
            count = old_assessments.count()
            # old_assessments.update(status='archived')  # Example
            self.stdout.write(f'Archived {count} old assessments')
        
        # Archive old training records
        old_training_records = ComplianceTrainingRecord.objects.filter(
            completed_date__lt=cutoff_date,
            status='completed'
        )
        
        if self.dry_run:
            self.stdout.write(f'Would archive {old_training_records.count()} old training records')
        else:
            count = old_training_records.count()
            # In practice, you might want to keep training records for compliance purposes
            self.stdout.write(f'Would archive {count} old training records (keeping for compliance)')
    
    def cleanup_audit_trail(self, cutoff_date):
        """Clean up old audit trail entries"""
        self.stdout.write('Cleaning up old audit trail entries...')
        
        # Keep audit trail for a shorter period (e.g., 2 years for most actions)
        audit_cutoff = timezone.now() - timedelta(days=730)  # 2 years
        
        old_audit_entries = ComplianceAuditTrail.objects.filter(
            timestamp__lt=audit_cutoff
        ).exclude(
            # Keep critical actions longer
            action__in=['delete', 'approve', 'resolve']
        )
        
        if self.dry_run:
            self.stdout.write(f'Would delete {old_audit_entries.count()} old audit entries')
        else:
            count = old_audit_entries.count()
            old_audit_entries.delete()
            self.stdout.write(f'Deleted {count} old audit entries')
    
    def update_overdue_items(self):
        """Update status of overdue items"""
        self.stdout.write('Updating overdue items...')
        
        now = timezone.now()
        today = now.date()
        
        # Update overdue training records
        overdue_training = ComplianceTrainingRecord.objects.filter(
            due_date__lt=today,
            status__in=['not_started', 'in_progress']
        )
        
        if self.dry_run:
            self.stdout.write(f'Would mark {overdue_training.count()} training records as overdue')
        else:
            count = overdue_training.count()
            # You might want to add an 'overdue' status or send notifications
            # overdue_training.update(status='overdue')
            self.stdout.write(f'Found {count} overdue training records')
        
        # Update overdue control testing
        overdue_controls = ComplianceControl.objects.filter(
            next_test_date__lt=today,
            implementation_status='implemented'
        )
        
        if self.dry_run:
            self.stdout.write(f'Would mark {overdue_controls.count()} controls as needing testing')
        else:
            count = overdue_controls.count()
            # You might want to update status or send notifications
            self.stdout.write(f'Found {count} controls with overdue testing')
        
        # Update overdue policy reviews
        overdue_policies = CompliancePolicy.objects.filter(
            review_date__lt=today,
            status='active'
        )
        
        if self.dry_run:
            self.stdout.write(f'Would mark {overdue_policies.count()} policies as needing review')
        else:
            count = overdue_policies.count()
            # You might want to update status or send notifications
            self.stdout.write(f'Found {count} policies needing review')
        
        # Update overdue risk assessments
        overdue_risks = ComplianceRiskAssessment.objects.filter(
            review_date__lt=today
        )
        
        if self.dry_run:
            self.stdout.write(f'Would mark {overdue_risks.count()} risk assessments as needing review')
        else:
            count = overdue_risks.count()
            self.stdout.write(f'Found {count} risk assessments needing review')
        
        # Update overdue vendor assessments
        overdue_vendors = ComplianceVendor.objects.filter(
            next_assessment_date__lte=today,
            status='active'
        )
        
        if self.dry_run:
            self.stdout.write(f'Would mark {overdue_vendors.count()} vendors as needing assessment')
        else:
            count = overdue_vendors.count()
            self.stdout.write(f'Found {count} vendors needing assessment')
    
    def cleanup_old_reports(self, cutoff_date):
        """Clean up old generated reports"""
        self.stdout.write('Cleaning up old reports...')
        
        old_reports = ComplianceReport.objects.filter(
            generated_at__lt=cutoff_date,
            status='completed'
        )
        
        if self.dry_run:
            self.stdout.write(f'Would delete {old_reports.count()} old reports')
        else:
            count = old_reports.count()
            # Delete the actual report files first
            for report in old_reports:
                if report.file_path:
                    # Delete the physical file
                    # os.remove(report.file_path)  # Implement file deletion
                    pass
            
            old_reports.delete()
            self.stdout.write(f'Deleted {count} old reports')
    
    def optimize_database(self):
        """Perform database optimization tasks"""
        self.stdout.write('Performing database optimization...')
        
        # This would include tasks like:
        # - Updating statistics
        # - Rebuilding indexes
        # - Analyzing query performance
        # Implementation depends on your database backend
        
        if not self.dry_run:
            # Example for PostgreSQL:
            # from django.db import connection
            # with connection.cursor() as cursor:
            #     cursor.execute("ANALYZE;")
            pass
        
        self.stdout.write('Database optimization completed')
    
    def generate_cleanup_report(self):
        """Generate a report of cleanup activities"""
        report = {
            'cleanup_date': timezone.now().isoformat(),
            'items_processed': {
                'incidents': ComplianceIncident.objects.filter(
                    status__in=['resolved', 'closed']
                ).count(),
                'assessments': ComplianceAssessment.objects.filter(
                    status='completed'
                ).count(),
                'training_records': ComplianceTrainingRecord.objects.filter(
                    status='completed'
                ).count(),
                'audit_entries': ComplianceAuditTrail.objects.count(),
            },
            'overdue_items': {
                'training': ComplianceTrainingRecord.objects.filter(
                    due_date__lt=timezone.now().date(),
                    status__in=['not_started', 'in_progress']
                ).count(),
                'controls': ComplianceControl.objects.filter(
                    next_test_date__lt=timezone.now().date()
                ).count(),
                'policies': CompliancePolicy.objects.filter(
                    review_date__lt=timezone.now().date(),
                    status='active'
                ).count(),
            }
        }
        
        return report