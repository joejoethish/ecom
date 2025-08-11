"""
Utility functions for compliance management
"""
import csv
import json
import xlsxwriter
from io import BytesIO, StringIO
from django.http import HttpResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
import logging

logger = logging.getLogger(__name__)


class ComplianceExporter:
    """Utility class for exporting compliance data"""
    
    @staticmethod
    def export_to_csv(queryset, fields, filename=None):
        """Export queryset to CSV format"""
        if not filename:
            filename = f"compliance_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write header
        header = [field.replace('_', ' ').title() for field in fields]
        writer.writerow(header)
        
        # Write data
        for obj in queryset:
            row = []
            for field in fields:
                value = getattr(obj, field, '')
                if hasattr(value, 'all'):  # ManyToMany field
                    value = ', '.join(str(v) for v in value.all())
                elif callable(value):
                    value = value()
                row.append(str(value) if value is not None else '')
            writer.writerow(row)
        
        return response
    
    @staticmethod
    def export_to_excel(queryset, fields, filename=None, sheet_name='Data'):
        """Export queryset to Excel format"""
        if not filename:
            filename = f"compliance_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(sheet_name)
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D7E4BC',
            'border': 1
        })
        
        # Write header
        for col, field in enumerate(fields):
            header = field.replace('_', ' ').title()
            worksheet.write(0, col, header, header_format)
        
        # Write data
        for row, obj in enumerate(queryset, 1):
            for col, field in enumerate(fields):
                value = getattr(obj, field, '')
                if hasattr(value, 'all'):  # ManyToMany field
                    value = ', '.join(str(v) for v in value.all())
                elif callable(value):
                    value = value()
                worksheet.write(row, col, str(value) if value is not None else '')
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @staticmethod
    def export_to_pdf(data, title, filename=None):
        """Export data to PDF format"""
        if not filename:
            filename = f"compliance_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        doc = SimpleDocTemplate(response, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = styles['Title']
        story.append(Paragraph(title, title_style))
        story.append(Paragraph('<br/><br/>', styles['Normal']))
        
        # Data table
        if isinstance(data, list) and data:
            # Assume data is a list of dictionaries
            headers = list(data[0].keys())
            table_data = [headers]
            
            for item in data:
                row = [str(item.get(header, '')) for header in headers]
                table_data.append(row)
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        doc.build(story)
        return response


class ComplianceNotifier:
    """Utility class for sending compliance notifications"""
    
    @staticmethod
    def send_notification(subject, message, recipients, template=None, context=None):
        """Send notification email"""
        if not recipients or not getattr(settings, 'EMAIL_HOST', None):
            logger.warning("Email not configured or no recipients provided")
            return False
        
        try:
            if template and context:
                html_message = render_to_string(template, context)
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@compliance.com'),
                    recipient_list=recipients,
                    html_message=html_message,
                    fail_silently=False
                )
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@compliance.com'),
                    recipient_list=recipients,
                    fail_silently=False
                )
            
            logger.info(f"Notification sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    @staticmethod
    def send_incident_alert(incident):
        """Send incident alert notification"""
        subject = f"Compliance Incident Alert: {incident.title}"
        message = f"""
        A new compliance incident has been reported:
        
        Incident ID: {incident.incident_id}
        Title: {incident.title}
        Severity: {incident.severity}
        Type: {incident.incident_type}
        Occurred: {incident.occurred_at}
        
        Please review and take appropriate action.
        """
        
        # Get recipients based on severity
        recipients = ComplianceNotifier.get_incident_recipients(incident.severity)
        
        return ComplianceNotifier.send_notification(subject, message, recipients)
    
    @staticmethod
    def send_training_reminder(training_record):
        """Send training reminder notification"""
        subject = f"Training Reminder: {training_record.training.title}"
        message = f"""
        This is a reminder that your compliance training is due:
        
        Training: {training_record.training.title}
        Due Date: {training_record.due_date}
        Status: {training_record.status}
        
        Please complete your training as soon as possible.
        """
        
        recipients = [training_record.user.email]
        
        return ComplianceNotifier.send_notification(subject, message, recipients)
    
    @staticmethod
    def get_incident_recipients(severity):
        """Get email recipients based on incident severity"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if severity == 'critical':
            # Critical incidents go to all compliance staff
            return list(
                User.objects.filter(
                    role__in=[
                        'compliance_admin', 'compliance_manager',
                        'compliance_officer', 'compliance_analyst'
                    ]
                ).values_list('email', flat=True)
            )
        elif severity == 'high':
            # High severity to managers and officers
            return list(
                User.objects.filter(
                    role__in=['compliance_admin', 'compliance_manager', 'compliance_officer']
                ).values_list('email', flat=True)
            )
        else:
            # Medium/Low to officers and analysts
            return list(
                User.objects.filter(
                    role__in=['compliance_officer', 'compliance_analyst']
                ).values_list('email', flat=True)
            )


class ComplianceCalculator:
    """Utility class for compliance calculations and metrics"""
    
    @staticmethod
    def calculate_risk_score(likelihood, impact):
        """Calculate risk score based on likelihood and impact"""
        likelihood_values = {
            'very_low': 1,
            'low': 2,
            'medium': 3,
            'high': 4,
            'very_high': 5
        }
        
        impact_values = {
            'negligible': 1,
            'minor': 2,
            'moderate': 3,
            'major': 4,
            'catastrophic': 5
        }
        
        likelihood_score = likelihood_values.get(likelihood, 3)
        impact_score = impact_values.get(impact, 3)
        
        return likelihood_score * impact_score
    
    @staticmethod
    def calculate_compliance_score(framework):
        """Calculate overall compliance score for a framework"""
        from .models import ComplianceControl
        
        controls = ComplianceControl.objects.filter(framework=framework)
        if not controls.exists():
            return 0
        
        implemented_controls = controls.filter(implementation_status='implemented').count()
        total_controls = controls.count()
        
        return (implemented_controls / total_controls) * 100 if total_controls > 0 else 0
    
    @staticmethod
    def calculate_training_completion_rate(framework=None):
        """Calculate training completion rate"""
        from .models import ComplianceTrainingRecord
        
        queryset = ComplianceTrainingRecord.objects.all()
        if framework:
            queryset = queryset.filter(training__framework=framework)
        
        total_records = queryset.count()
        completed_records = queryset.filter(status='completed').count()
        
        return (completed_records / total_records) * 100 if total_records > 0 else 0
    
    @staticmethod
    def calculate_incident_resolution_time(incident):
        """Calculate incident resolution time in hours"""
        if incident.resolved_at and incident.reported_at:
            delta = incident.resolved_at - incident.reported_at
            return delta.total_seconds() / 3600  # Convert to hours
        return None


class ComplianceValidator:
    """Utility class for compliance data validation"""
    
    @staticmethod
    def validate_policy_approval_workflow(policy):
        """Validate policy approval workflow"""
        errors = []
        
        if policy.status == 'active' and not policy.approved_at:
            errors.append("Policy cannot be active without approval")
        
        if policy.status == 'approved' and not policy.approver:
            errors.append("Approved policy must have an approver")
        
        if policy.review_date and policy.review_date <= policy.effective_date:
            errors.append("Review date must be after effective date")
        
        return errors
    
    @staticmethod
    def validate_risk_assessment(risk):
        """Validate risk assessment data"""
        errors = []
        
        if risk.residual_risk_score > risk.inherent_risk_score:
            errors.append("Residual risk score cannot be higher than inherent risk score")
        
        if risk.status == 'mitigated' and not risk.mitigation_strategies:
            errors.append("Mitigated risks must have mitigation strategies")
        
        return errors
    
    @staticmethod
    def validate_control_testing(control):
        """Validate control testing requirements"""
        errors = []
        
        if control.implementation_status == 'implemented' and not control.testing_procedures:
            errors.append("Implemented controls must have testing procedures")
        
        if control.last_tested and control.next_test_date:
            if control.next_test_date <= control.last_tested:
                errors.append("Next test date must be after last test date")
        
        return errors


class ComplianceReportGenerator:
    """Utility class for generating compliance reports"""
    
    @staticmethod
    def generate_dashboard_data():
        """Generate compliance dashboard data"""
        from .models import (
            ComplianceFramework, CompliancePolicy, ComplianceControl,
            ComplianceIncident, ComplianceTrainingRecord, ComplianceRiskAssessment
        )
        
        now = timezone.now()
        
        return {
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
            },
            'incidents': {
                'open': ComplianceIncident.objects.exclude(
                    status__in=['resolved', 'closed']
                ).count(),
                'critical': ComplianceIncident.objects.filter(
                    severity='critical'
                ).exclude(status__in=['resolved', 'closed']).count(),
            },
            'training': {
                'overdue': ComplianceTrainingRecord.objects.filter(
                    due_date__lt=now.date(),
                    status__in=['not_started', 'in_progress']
                ).count(),
            },
            'risks': {
                'high': ComplianceRiskAssessment.objects.filter(
                    inherent_risk_score__gte=15
                ).count(),
            }
        }
    
    @staticmethod
    def generate_compliance_metrics():
        """Generate compliance metrics"""
        metrics = {}
        
        # Calculate various compliance metrics
        frameworks = ComplianceFramework.objects.filter(status='active')
        
        for framework in frameworks:
            framework_metrics = {
                'compliance_score': ComplianceCalculator.calculate_compliance_score(framework),
                'training_completion': ComplianceCalculator.calculate_training_completion_rate(framework),
            }
            metrics[framework.name] = framework_metrics
        
        return metrics


def get_compliance_status_color(status):
    """Get color code for compliance status"""
    color_map = {
        'active': '#28a745',      # Green
        'inactive': '#6c757d',    # Gray
        'draft': '#ffc107',       # Yellow
        'approved': '#17a2b8',    # Blue
        'critical': '#dc3545',    # Red
        'high': '#fd7e14',        # Orange
        'medium': '#ffc107',      # Yellow
        'low': '#28a745',         # Green
        'completed': '#28a745',   # Green
        'in_progress': '#17a2b8', # Blue
        'not_started': '#6c757d', # Gray
        'overdue': '#dc3545',     # Red
    }
    return color_map.get(status.lower(), '#6c757d')


def format_compliance_date(date_obj):
    """Format date for compliance reports"""
    if not date_obj:
        return 'N/A'
    return date_obj.strftime('%Y-%m-%d')


def sanitize_filename(filename):
    """Sanitize filename for compliance exports"""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename