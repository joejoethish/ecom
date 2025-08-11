from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import csv
import json
from io import StringIO

from backend.apps.compliance.models import (
    ComplianceFramework, CompliancePolicy, ComplianceControl,
    ComplianceAssessment, ComplianceIncident, ComplianceTraining,
    ComplianceTrainingRecord, ComplianceRiskAssessment,
    ComplianceVendor, ComplianceReport
)


class Command(BaseCommand):
    help = 'Generate compliance reports and send notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['dashboard', 'incidents', 'training', 'risks', 'vendors', 'all'],
            default='all',
            help='Type of report to generate',
        )
        parser.add_argument(
            '--email',
            action='store_true',
            help='Send reports via email',
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path for the report',
        )
    
    def handle(self, *args, **options):
        report_type = options['report_type']
        
        if report_type == 'all':
            reports = ['dashboard', 'incidents', 'training', 'risks', 'vendors']
        else:
            reports = [report_type]
        
        for report in reports:
            self.stdout.write(f'Generating {report} report...')
            report_data = self.generate_report(report)
            
            if options['output_file']:
                self.save_report_to_file(report_data, options['output_file'], report)
            
            if options['email']:
                self.send_report_email(report_data, report)
        
        self.stdout.write(
            self.style.SUCCESS('Compliance reports generated successfully!')
        )
    
    def generate_report(self, report_type):
        """Generate specific type of compliance report"""
        if report_type == 'dashboard':
            return self.generate_dashboard_report()
        elif report_type == 'incidents':
            return self.generate_incidents_report()
        elif report_type == 'training':
            return self.generate_training_report()
        elif report_type == 'risks':
            return self.generate_risks_report()
        elif report_type == 'vendors':
            return self.generate_vendors_report()
    
    def generate_dashboard_report(self):
        """Generate compliance dashboard summary report"""
        now = timezone.now()
        
        return {
            'report_type': 'dashboard',
            'generated_at': now.isoformat(),
            'summary': {
                'frameworks': {
                    'total': ComplianceFramework.objects.count(),
                    'active': ComplianceFramework.objects.filter(status='active').count(),
                },
                'policies': {
                    'total': CompliancePolicy.objects.count(),
                    'approved': CompliancePolicy.objects.filter(status='approved').count(),
                    'pending_review': CompliancePolicy.objects.filter(
                        review_date__lte=now.date(), status='active'
                    ).count(),
                },
                'controls': {
                    'total': ComplianceControl.objects.count(),
                    'implemented': ComplianceControl.objects.filter(
                        implementation_status='implemented'
                    ).count(),
                    'overdue_testing': ComplianceControl.objects.filter(
                        next_test_date__lt=now.date()
                    ).count(),
                },
                'incidents': {
                    'total': ComplianceIncident.objects.count(),
                    'open': ComplianceIncident.objects.exclude(
                        status__in=['resolved', 'closed']
                    ).count(),
                    'critical': ComplianceIncident.objects.filter(
                        severity='critical'
                    ).exclude(status__in=['resolved', 'closed']).count(),
                },
                'training': {
                    'total_records': ComplianceTrainingRecord.objects.count(),
                    'completed': ComplianceTrainingRecord.objects.filter(
                        status='completed'
                    ).count(),
                    'overdue': ComplianceTrainingRecord.objects.filter(
                        due_date__lt=now.date(),
                        status__in=['not_started', 'in_progress']
                    ).count(),
                },
                'risks': {
                    'total': ComplianceRiskAssessment.objects.count(),
                    'high_risk': ComplianceRiskAssessment.objects.filter(
                        inherent_risk_score__gte=15
                    ).count(),
                    'overdue_review': ComplianceRiskAssessment.objects.filter(
                        review_date__lt=now.date()
                    ).count(),
                },
                'vendors': {
                    'total': ComplianceVendor.objects.count(),
                    'active': ComplianceVendor.objects.filter(status='active').count(),
                    'assessment_due': ComplianceVendor.objects.filter(
                        next_assessment_date__lte=now.date()
                    ).count(),
                }
            }
        }
    
    def generate_incidents_report(self):
        """Generate incidents report"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        incidents = ComplianceIncident.objects.filter(
            created_at__gte=thirty_days_ago
        ).select_related('framework', 'reported_by', 'assigned_to')
        
        return {
            'report_type': 'incidents',
            'period': 'Last 30 days',
            'generated_at': timezone.now().isoformat(),
            'total_incidents': incidents.count(),
            'incidents_by_severity': dict(
                incidents.values('severity').annotate(
                    count=models.Count('id')
                ).values_list('severity', 'count')
            ),
            'incidents_by_type': dict(
                incidents.values('incident_type').annotate(
                    count=models.Count('id')
                ).values_list('incident_type', 'count')
            ),
            'incidents_by_status': dict(
                incidents.values('status').annotate(
                    count=models.Count('id')
                ).values_list('status', 'count')
            ),
            'critical_incidents': list(
                incidents.filter(severity='critical').values(
                    'incident_id', 'title', 'status', 'occurred_at'
                )
            )
        }
    
    def generate_training_report(self):
        """Generate training completion report"""
        training_records = ComplianceTrainingRecord.objects.select_related(
            'training', 'user'
        )
        
        return {
            'report_type': 'training',
            'generated_at': timezone.now().isoformat(),
            'total_records': training_records.count(),
            'completion_rate': (
                training_records.filter(status='completed').count() /
                training_records.count() * 100
            ) if training_records.count() > 0 else 0,
            'records_by_status': dict(
                training_records.values('status').annotate(
                    count=models.Count('id')
                ).values_list('status', 'count')
            ),
            'overdue_training': list(
                training_records.filter(
                    due_date__lt=timezone.now().date(),
                    status__in=['not_started', 'in_progress']
                ).values(
                    'user__username', 'training__title', 'due_date', 'status'
                )
            ),
            'certificates_issued': training_records.filter(
                certificate_issued=True
            ).count()
        }
    
    def generate_risks_report(self):
        """Generate risk assessment report"""
        risks = ComplianceRiskAssessment.objects.select_related(
            'framework', 'risk_owner'
        )
        
        return {
            'report_type': 'risks',
            'generated_at': timezone.now().isoformat(),
            'total_risks': risks.count(),
            'high_risks': risks.filter(inherent_risk_score__gte=15).count(),
            'risks_by_category': dict(
                risks.values('risk_category').annotate(
                    count=models.Count('id')
                ).values_list('risk_category', 'count')
            ),
            'risks_by_status': dict(
                risks.values('status').annotate(
                    count=models.Count('id')
                ).values_list('status', 'count')
            ),
            'average_risk_score': risks.aggregate(
                avg_score=models.Avg('inherent_risk_score')
            )['avg_score'] or 0,
            'overdue_reviews': list(
                risks.filter(
                    review_date__lt=timezone.now().date()
                ).values(
                    'title', 'risk_category', 'inherent_risk_score', 'review_date'
                )
            )
        }
    
    def generate_vendors_report(self):
        """Generate vendor compliance report"""
        vendors = ComplianceVendor.objects.all()
        
        return {
            'report_type': 'vendors',
            'generated_at': timezone.now().isoformat(),
            'total_vendors': vendors.count(),
            'active_vendors': vendors.filter(status='active').count(),
            'vendors_by_risk_level': dict(
                vendors.values('risk_level').annotate(
                    count=models.Count('id')
                ).values_list('risk_level', 'count')
            ),
            'vendors_by_type': dict(
                vendors.values('vendor_type').annotate(
                    count=models.Count('id')
                ).values_list('vendor_type', 'count')
            ),
            'assessments_due': list(
                vendors.filter(
                    next_assessment_date__lte=timezone.now().date()
                ).values(
                    'name', 'vendor_type', 'risk_level', 'next_assessment_date'
                )
            ),
            'contracts_expiring': list(
                vendors.filter(
                    contract_end_date__lte=timezone.now().date() + timedelta(days=90)
                ).values(
                    'name', 'vendor_type', 'contract_end_date'
                )
            )
        }
    
    def save_report_to_file(self, report_data, base_filename, report_type):
        """Save report data to file"""
        filename = f"{base_filename}_{report_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.stdout.write(f'Report saved to: {filename}')
    
    def send_report_email(self, report_data, report_type):
        """Send report via email"""
        if not getattr(settings, 'EMAIL_HOST', None):
            self.stdout.write('Email not configured. Skipping email send.')
            return
        
        subject = f'Compliance {report_type.title()} Report - {timezone.now().strftime("%Y-%m-%d")}'
        
        # Create email body
        body = self.format_report_for_email(report_data, report_type)
        
        # Get recipients (this would be configurable in production)
        recipients = ['compliance@company.com']  # Configure as needed
        
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@company.com'),
                recipient_list=recipients,
                fail_silently=False
            )
            self.stdout.write(f'Report emailed successfully: {report_type}')
        except Exception as e:
            self.stdout.write(f'Failed to send email: {e}')
    
    def format_report_for_email(self, report_data, report_type):
        """Format report data for email body"""
        body = f"Compliance {report_type.title()} Report\n"
        body += f"Generated: {report_data['generated_at']}\n\n"
        
        if report_type == 'dashboard':
            summary = report_data['summary']
            body += "COMPLIANCE DASHBOARD SUMMARY\n"
            body += "=" * 30 + "\n\n"
            
            for category, data in summary.items():
                body += f"{category.upper()}:\n"
                for key, value in data.items():
                    body += f"  {key.replace('_', ' ').title()}: {value}\n"
                body += "\n"
        
        elif report_type == 'incidents':
            body += f"Total Incidents (Last 30 days): {report_data['total_incidents']}\n\n"
            
            if report_data['critical_incidents']:
                body += "CRITICAL INCIDENTS:\n"
                for incident in report_data['critical_incidents']:
                    body += f"  - {incident['incident_id']}: {incident['title']} ({incident['status']})\n"
        
        # Add more formatting for other report types as needed
        
        return body