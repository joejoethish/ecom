from django.db.models import Count, Q, Avg, F, Case, When, IntegerField, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
import logging
import json
import uuid
from .models import (
    SecurityThreat, SecurityIncident, SecurityAudit, SecurityPolicy,
    SecurityVulnerability, SecurityTraining, SecurityTrainingRecord,
    SecurityRiskAssessment, SecurityMonitoringRule, SecurityAlert,
    SecurityConfiguration
)

User = get_user_model()
logger = logging.getLogger(__name__)
class SecurityThreatService:
    """Service for managing security threats"""
    
    @staticmethod
    def get_threat_statistics() -> Dict[str, Any]:
        """Get comprehensive threat statistics"""
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        
        stats = {
            'total_threats': SecurityThreat.objects.count(),
            'active_threats': SecurityThreat.objects.filter(
                status__in=['detected', 'investigating']
            ).count(),
            'critical_threats': SecurityThreat.objects.filter(
                severity='critical'
            ).count(),
            'threats_last_30_days': SecurityThreat.objects.filter(
                detected_at__gte=last_30_days
            ).count(),
            'severity_breakdown': SecurityThreat.objects.values('severity').annotate(
                count=Count('id')
            ),
            'status_breakdown': SecurityThreat.objects.values('status').annotate(
                count=Count('id')
            ),
            'avg_resolution_time': SecurityThreat.objects.filter(
                resolved_at__isnull=False
            ).aggregate(
                avg_time=Avg(F('resolved_at') - F('detected_at'))
            )['avg_time']
        }
        
        return stats
    
    @staticmethod
    def get_threat_trends(days: int = 30) -> List[Dict[str, Any]]:
        """Get threat trends over specified period"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        trends = []
        current_date = start_date
        
        while current_date <= end_date:
            day_threats = SecurityThreat.objects.filter(
                detected_at__date=current_date
            )
            
            severity_breakdown = day_threats.values('severity').annotate(
                count=Count('id')
            )
            
            trends.append({
                'date': current_date,
                'threat_count': day_threats.count(),
                'severity_breakdown': {item['severity']: item['count'] for item in severity_breakdown}
            })
            
            current_date += timedelta(days=1)
        
        return trends
    
    @staticmethod
    def create_threat(threat_data: Dict[str, Any], user: User) -> SecurityThreat:
        """Create a new security threat"""
        try:
            with transaction.atomic():
                threat = SecurityThreat.objects.create(**threat_data)
                
                # Create corresponding alert if severity is high or critical
                if threat.severity in ['high', 'critical']:
                    SecurityAlert.objects.create(
                        alert_type='security_event',
                        severity=threat.severity,
                        title=f"Security Threat Detected: {threat.threat_type}",
                        description=threat.description,
                        source_system='Security Management',
                        event_data={
                            'threat_id': str(threat.id),
                            'threat_type': threat.threat_type,
                            'source_ip': threat.source_ip,
                            'detection_method': threat.detection_method
                        }
                    )
                
                logger.info(f"Security threat created: {threat.id} by user {user.username}")
                return threat
                
        except Exception as e:
            logger.error(f"Error creating security threat: {str(e)}")
            raise ValidationError(f"Failed to create security threat: {str(e)}")
    
    @staticmethod
    def update_threat_status(threat_id: str, status: str, user: User, notes: str = "") -> SecurityThreat:
        """Update threat status with audit trail"""
        try:
            threat = SecurityThreat.objects.get(id=threat_id)
            old_status = threat.status
            threat.status = status
            
            if status in ['resolved', 'false_positive']:
                threat.resolved_at = timezone.now()
            
            threat.save()
            
            # Log status change
            logger.info(f"Threat {threat_id} status changed from {old_status} to {status} by {user.username}")
            
            return threat
            
        except SecurityThreat.DoesNotExist:
            raise ValidationError("Security threat not found")
        except Exception as e:
            logger.error(f"Error updating threat status: {str(e)}")
            raise ValidationError(f"Failed to update threat status: {str(e)}")


class SecurityIncidentService:
    """Service for managing security incidents"""
    
    @staticmethod
    def get_incident_statistics() -> Dict[str, Any]:
        """Get comprehensive incident statistics"""
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        
        stats = {
            'total_incidents': SecurityIncident.objects.count(),
            'open_incidents': SecurityIncident.objects.filter(
                status__in=['open', 'investigating', 'contained']
            ).count(),
            'critical_incidents': SecurityIncident.objects.filter(
                severity='critical'
            ).count(),
            'incidents_last_30_days': SecurityIncident.objects.filter(
                detected_at__gte=last_30_days
            ).count(),
            'incident_type_breakdown': SecurityIncident.objects.values('incident_type').annotate(
                count=Count('id')
            ),
            'avg_resolution_time': SecurityIncident.objects.filter(
                resolved_at__isnull=False
            ).aggregate(
                avg_time=Avg(F('resolved_at') - F('detected_at'))
            )['avg_time'],
            'mttr': SecurityIncident.objects.filter(
                resolved_at__isnull=False,
                detected_at__gte=last_30_days
            ).aggregate(
                mttr=Avg(F('resolved_at') - F('detected_at'))
            )['mttr']
        }
        
        return stats
    
    @staticmethod
    def create_incident(incident_data: Dict[str, Any], user: User) -> SecurityIncident:
        """Create a new security incident"""
        try:
            with transaction.atomic():
                # Generate unique incident number
                incident_data['incident_number'] = f"INC-{str(uuid.uuid4())[:8].upper()}"
                incident_data['reported_by'] = user
                
                incident = SecurityIncident.objects.create(**incident_data)
                
                # Create high-priority alert for critical incidents
                if incident.severity == 'critical':
                    SecurityAlert.objects.create(
                        alert_type='security_event',
                        severity='critical',
                        title=f"Critical Security Incident: {incident.title}",
                        description=incident.description,
                        source_system='Incident Management',
                        event_data={
                            'incident_id': str(incident.id),
                            'incident_number': incident.incident_number,
                            'incident_type': incident.incident_type
                        }
                    )
                
                logger.info(f"Security incident created: {incident.incident_number} by user {user.username}")
                return incident
                
        except Exception as e:
            logger.error(f"Error creating security incident: {str(e)}")
            raise ValidationError(f"Failed to create security incident: {str(e)}")
    
    @staticmethod
    def update_incident_timeline(incident_id: str, timeline_entry: Dict[str, Any], user: User) -> SecurityIncident:
        """Add entry to incident timeline"""
        try:
            incident = SecurityIncident.objects.get(id=incident_id)
            
            timeline_entry.update({
                'timestamp': timezone.now().isoformat(),
                'user': user.username,
                'user_id': user.id
            })
            
            if not incident.timeline:
                incident.timeline = []
            
            incident.timeline.append(timeline_entry)
            incident.save()
            
            logger.info(f"Timeline updated for incident {incident.incident_number} by {user.username}")
            return incident
            
        except SecurityIncident.DoesNotExist:
            raise ValidationError("Security incident not found")
        except Exception as e:
            logger.error(f"Error updating incident timeline: {str(e)}")
            raise ValidationError(f"Failed to update incident timeline: {str(e)}")


class SecurityVulnerabilityService:
    """Service for managing security vulnerabilities"""
    
    @staticmethod
    def get_vulnerability_statistics() -> Dict[str, Any]:
        """Get comprehensive vulnerability statistics"""
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        
        stats = {
            'total_vulnerabilities': SecurityVulnerability.objects.count(),
            'open_vulnerabilities': SecurityVulnerability.objects.filter(
                status__in=['open', 'acknowledged', 'in_progress']
            ).count(),
            'critical_vulnerabilities': SecurityVulnerability.objects.filter(
                severity='critical'
            ).count(),
            'high_vulnerabilities': SecurityVulnerability.objects.filter(
                severity='high'
            ).count(),
            'vulnerabilities_last_30_days': SecurityVulnerability.objects.filter(
                discovered_date__gte=last_30_days
            ).count(),
            'severity_breakdown': SecurityVulnerability.objects.values('severity').annotate(
                count=Count('id')
            ),
            'avg_cvss_score': SecurityVulnerability.objects.filter(
                cvss_score__isnull=False
            ).aggregate(avg_score=Avg('cvss_score'))['avg_score'],
            'overdue_vulnerabilities': SecurityVulnerability.objects.filter(
                due_date__lt=now,
                status__in=['open', 'acknowledged', 'in_progress']
            ).count()
        }
        
        return stats
    
    @staticmethod
    def create_vulnerability(vuln_data: Dict[str, Any], user: User) -> SecurityVulnerability:
        """Create a new security vulnerability"""
        try:
            with transaction.atomic():
                # Generate unique vulnerability ID
                vuln_data['vulnerability_id'] = f"VULN-{str(uuid.uuid4())[:8].upper()}"
                
                vulnerability = SecurityVulnerability.objects.create(**vuln_data)
                
                # Create alert for high/critical vulnerabilities
                if vulnerability.severity in ['high', 'critical']:
                    SecurityAlert.objects.create(
                        alert_type='security_event',
                        severity=vulnerability.severity,
                        title=f"Security Vulnerability: {vulnerability.title}",
                        description=vulnerability.description,
                        source_system='Vulnerability Management',
                        event_data={
                            'vulnerability_id': str(vulnerability.id),
                            'vuln_id': vulnerability.vulnerability_id,
                            'cvss_score': vulnerability.cvss_score,
                            'cve_id': vulnerability.cve_id
                        }
                    )
                
                logger.info(f"Security vulnerability created: {vulnerability.vulnerability_id} by user {user.username}")
                return vulnerability
                
        except Exception as e:
            logger.error(f"Error creating security vulnerability: {str(e)}")
            raise ValidationError(f"Failed to create security vulnerability: {str(e)}")
    
    @staticmethod
    def get_vulnerability_metrics() -> List[Dict[str, Any]]:
        """Get vulnerability metrics by severity"""
        metrics = []
        
        for severity, _ in SecurityVulnerability.SEVERITY_CHOICES:
            vulns = SecurityVulnerability.objects.filter(severity=severity)
            
            avg_age = vulns.filter(
                resolved_date__isnull=True
            ).aggregate(
                avg_age=Avg(
                    Case(
                        When(resolved_date__isnull=True, 
                             then=timezone.now() - F('discovered_date')),
                        default=F('resolved_date') - F('discovered_date'),
                        output_field=IntegerField()
                    )
                )
            )['avg_age']
            
            metrics.append({
                'severity': severity,
                'count': vulns.count(),
                'avg_age_days': avg_age.days if avg_age else 0
            })
        
        return metrics


class SecurityAuditService:
    """Service for managing security audits"""
    
    @staticmethod
    def get_audit_statistics() -> Dict[str, Any]:
        """Get comprehensive audit statistics"""
        now = timezone.now()
        
        stats = {
            'total_audits': SecurityAudit.objects.count(),
            'pending_audits': SecurityAudit.objects.filter(
                status='planned',
                scheduled_date__gte=now
            ).count(),
            'in_progress_audits': SecurityAudit.objects.filter(
                status='in_progress'
            ).count(),
            'completed_audits': SecurityAudit.objects.filter(
                status='completed'
            ).count(),
            'audit_type_breakdown': SecurityAudit.objects.values('audit_type').annotate(
                count=Count('id')
            ),
            'overdue_audits': SecurityAudit.objects.filter(
                scheduled_date__lt=now,
                status='planned'
            ).count()
        }
        
        return stats
    
    @staticmethod
    def create_audit(audit_data: Dict[str, Any], user: User) -> SecurityAudit:
        """Create a new security audit"""
        try:
            audit_data['auditor'] = user
            audit = SecurityAudit.objects.create(**audit_data)
            
            logger.info(f"Security audit created: {audit.audit_name} by user {user.username}")
            return audit
            
        except Exception as e:
            logger.error(f"Error creating security audit: {str(e)}")
            raise ValidationError(f"Failed to create security audit: {str(e)}")


class SecurityPolicyService:
    """Service for managing security policies"""
    
    @staticmethod
    def get_policy_statistics() -> Dict[str, Any]:
        """Get comprehensive policy statistics"""
        now = timezone.now()
        
        stats = {
            'total_policies': SecurityPolicy.objects.count(),
            'active_policies': SecurityPolicy.objects.filter(
                status='active'
            ).count(),
            'draft_policies': SecurityPolicy.objects.filter(
                status='draft'
            ).count(),
            'policies_under_review': SecurityPolicy.objects.filter(
                status='review'
            ).count(),
            'policies_due_for_review': SecurityPolicy.objects.filter(
                review_date__lte=now,
                status='active'
            ).count(),
            'policy_type_breakdown': SecurityPolicy.objects.values('policy_type').annotate(
                count=Count('id')
            )
        }
        
        return stats
    
    @staticmethod
    def create_policy(policy_data: Dict[str, Any], user: User) -> SecurityPolicy:
        """Create a new security policy"""
        try:
            policy_data['owner'] = user
            policy = SecurityPolicy.objects.create(**policy_data)
            
            logger.info(f"Security policy created: {policy.policy_name} by user {user.username}")
            return policy
            
        except Exception as e:
            logger.error(f"Error creating security policy: {str(e)}")
            raise ValidationError(f"Failed to create security policy: {str(e)}")


class SecurityTrainingService:
    """Service for managing security training"""
    
    @staticmethod
    def get_training_statistics() -> Dict[str, Any]:
        """Get comprehensive training statistics"""
        stats = {
            'total_trainings': SecurityTraining.objects.count(),
            'published_trainings': SecurityTraining.objects.filter(
                status='published'
            ).count(),
            'total_training_records': SecurityTrainingRecord.objects.count(),
            'completed_trainings': SecurityTrainingRecord.objects.filter(
                status='completed'
            ).count(),
            'in_progress_trainings': SecurityTrainingRecord.objects.filter(
                status='in_progress'
            ).count(),
            'overdue_trainings': SecurityTrainingRecord.objects.filter(
                expires_at__lt=timezone.now(),
                status='completed'
            ).count(),
            'training_completion_rate': SecurityTrainingRecord.objects.filter(
                status='completed'
            ).count() / max(SecurityTrainingRecord.objects.count(), 1) * 100
        }
        
        return stats
    
    @staticmethod
    def get_training_metrics() -> List[Dict[str, Any]]:
        """Get training metrics by type"""
        metrics = []
        
        for training_type, _ in SecurityTraining.TRAINING_TYPES:
            trainings = SecurityTraining.objects.filter(training_type=training_type)
            records = SecurityTrainingRecord.objects.filter(training__training_type=training_type)
            completed_records = records.filter(status='completed')
            
            metrics.append({
                'training_type': training_type,
                'total_users': records.values('user').distinct().count(),
                'completed_users': completed_records.values('user').distinct().count(),
                'completion_rate': (completed_records.count() / max(records.count(), 1)) * 100,
                'avg_score': completed_records.aggregate(avg_score=Avg('score'))['avg_score'] or 0
            })
        
        return metrics
    
    @staticmethod
    def enroll_user_in_training(training_id: str, user_id: int) -> SecurityTrainingRecord:
        """Enroll a user in a training program"""
        try:
            training = SecurityTraining.objects.get(id=training_id)
            user = User.objects.get(id=user_id)
            
            record, created = SecurityTrainingRecord.objects.get_or_create(
                user=user,
                training=training,
                defaults={
                    'status': 'not_started',
                    'attempts': 0
                }
            )
            
            if created:
                logger.info(f"User {user.username} enrolled in training {training.training_name}")
            
            return record
            
        except (SecurityTraining.DoesNotExist, User.DoesNotExist) as e:
            raise ValidationError(f"Training or user not found: {str(e)}")
        except Exception as e:
            logger.error(f"Error enrolling user in training: {str(e)}")
            raise ValidationError(f"Failed to enroll user in training: {str(e)}")


class SecurityRiskAssessmentService:
    """Service for managing security risk assessments"""
    
    @staticmethod
    def get_risk_statistics() -> Dict[str, Any]:
        """Get comprehensive risk assessment statistics"""
        stats = {
            'total_assessments': SecurityRiskAssessment.objects.count(),
            'high_risk_assessments': SecurityRiskAssessment.objects.filter(
                risk_level__in=['high', 'very_high']
            ).count(),
            'pending_assessments': SecurityRiskAssessment.objects.filter(
                status='draft'
            ).count(),
            'approved_assessments': SecurityRiskAssessment.objects.filter(
                status='approved'
            ).count(),
            'avg_risk_score': SecurityRiskAssessment.objects.aggregate(
                avg_score=Avg('risk_score')
            )['avg_score'],
            'risk_level_breakdown': SecurityRiskAssessment.objects.values('risk_level').annotate(
                count=Count('id')
            )
        }
        
        return stats
    
    @staticmethod
    def calculate_risk_score(likelihood: str, impact: str) -> Tuple[float, str]:
        """Calculate risk score and level based on likelihood and impact"""
        risk_values = {
            'very_low': 1,
            'low': 2,
            'medium': 3,
            'high': 4,
            'very_high': 5
        }
        
        likelihood_value = risk_values.get(likelihood, 3)
        impact_value = risk_values.get(impact, 3)
        
        risk_score = likelihood_value * impact_value
        
        if risk_score <= 4:
            risk_level = 'very_low'
        elif risk_score <= 8:
            risk_level = 'low'
        elif risk_score <= 12:
            risk_level = 'medium'
        elif risk_score <= 16:
            risk_level = 'high'
        else:
            risk_level = 'very_high'
        
        return float(risk_score), risk_level


class SecurityAlertService:
    """Service for managing security alerts"""
    
    @staticmethod
    def get_alert_statistics() -> Dict[str, Any]:
        """Get comprehensive alert statistics"""
        now = timezone.now()
        last_24_hours = now - timedelta(hours=24)
        
        stats = {
            'total_alerts': SecurityAlert.objects.count(),
            'open_alerts': SecurityAlert.objects.filter(
                status='open'
            ).count(),
            'critical_alerts': SecurityAlert.objects.filter(
                severity='critical',
                status='open'
            ).count(),
            'alerts_last_24h': SecurityAlert.objects.filter(
                created_at__gte=last_24_hours
            ).count(),
            'alert_type_breakdown': SecurityAlert.objects.values('alert_type').annotate(
                count=Count('id')
            ),
            'severity_breakdown': SecurityAlert.objects.values('severity').annotate(
                count=Count('id')
            ),
            'avg_response_time': SecurityAlert.objects.filter(
                acknowledged_at__isnull=False
            ).aggregate(
                avg_time=Avg(F('acknowledged_at') - F('created_at'))
            )['avg_time']
        }
        
        return stats
    
    @staticmethod
    def acknowledge_alert(alert_id: str, user: User) -> SecurityAlert:
        """Acknowledge a security alert"""
        try:
            alert = SecurityAlert.objects.get(id=alert_id)
            alert.status = 'acknowledged'
            alert.acknowledged_by = user
            alert.acknowledged_at = timezone.now()
            alert.save()
            
            logger.info(f"Alert {alert_id} acknowledged by user {user.username}")
            return alert
            
        except SecurityAlert.DoesNotExist:
            raise ValidationError("Security alert not found")
        except Exception as e:
            logger.error(f"Error acknowledging alert: {str(e)}")
            raise ValidationError(f"Failed to acknowledge alert: {str(e)}")


class SecurityDashboardService:
    """Service for security dashboard data aggregation"""
    
    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """Get comprehensive security dashboard statistics"""
        threat_stats = SecurityThreatService.get_threat_statistics()
        incident_stats = SecurityIncidentService.get_incident_statistics()
        vuln_stats = SecurityVulnerabilityService.get_vulnerability_statistics()
        audit_stats = SecurityAuditService.get_audit_statistics()
        training_stats = SecurityTrainingService.get_training_statistics()
        risk_stats = SecurityRiskAssessmentService.get_risk_statistics()
        alert_stats = SecurityAlertService.get_alert_statistics()
        
        # Calculate overall compliance score
        compliance_factors = [
            (audit_stats['completed_audits'] / max(audit_stats['total_audits'], 1)) * 100,
            (training_stats['training_completion_rate']),
            ((vuln_stats['total_vulnerabilities'] - vuln_stats['critical_vulnerabilities']) / 
             max(vuln_stats['total_vulnerabilities'], 1)) * 100,
            ((incident_stats['total_incidents'] - incident_stats['open_incidents']) / 
             max(incident_stats['total_incidents'], 1)) * 100
        ]
        
        compliance_score = sum(compliance_factors) / len(compliance_factors)
        
        return {
            'total_threats': threat_stats['total_threats'],
            'active_incidents': incident_stats['open_incidents'],
            'critical_vulnerabilities': vuln_stats['critical_vulnerabilities'],
            'pending_audits': audit_stats['pending_audits'],
            'overdue_trainings': training_stats['overdue_trainings'],
            'high_risk_assessments': risk_stats['high_risk_assessments'],
            'active_alerts': alert_stats['open_alerts'],
            'compliance_score': round(compliance_score, 2)
        }
    
    @staticmethod
    def get_security_trends(days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """Get security trends for dashboard charts"""
        return {
            'threat_trends': SecurityThreatService.get_threat_trends(days),
            'vulnerability_metrics': SecurityVulnerabilityService.get_vulnerability_metrics(),
            'training_metrics': SecurityTrainingService.get_training_metrics()
        }


class SecurityConfigurationService:
    """Service for managing security configurations"""
    
    @staticmethod
    def get_configuration_statistics() -> Dict[str, Any]:
        """Get comprehensive configuration statistics"""
        stats = {
            'total_configurations': SecurityConfiguration.objects.count(),
            'active_configurations': SecurityConfiguration.objects.filter(
                status='active'
            ).count(),
            'failed_configurations': SecurityConfiguration.objects.filter(
                status='failed'
            ).count(),
            'pending_validations': SecurityConfiguration.objects.filter(
                validation_status='pending'
            ).count(),
            'config_type_breakdown': SecurityConfiguration.objects.values('config_type').annotate(
                count=Count('id')
            )
        }
        
        return stats
    
    @staticmethod
    def validate_configuration(config_id: str, user: User) -> SecurityConfiguration:
        """Validate a security configuration"""
        try:
            config = SecurityConfiguration.objects.get(id=config_id)
            
            # Perform validation logic here
            # This is a placeholder - actual validation would depend on config type
            validation_errors = []
            
            config.last_validated = timezone.now()
            config.validation_status = 'valid' if not validation_errors else 'invalid'
            config.validation_errors = validation_errors
            config.save()
            
            logger.info(f"Configuration {config.config_name} validated by user {user.username}")
            return config
            
        except SecurityConfiguration.DoesNotExist:
            raise ValidationError("Security configuration not found")
        except Exception as e:
            logger.error(f"Error validating configuration: {str(e)}")
            raise ValidationError(f"Failed to validate configuration: {str(e)}")