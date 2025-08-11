#!/usr/bin/env python
"""
Comprehensive test script for Security Management System
Tests all security management functionality including threats, incidents, vulnerabilities, etc.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Add the backend directory to Python path
sys.path.append('/workspaces/Local_ecom/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.base')
django.setup()

from django.contrib.auth import get_user_model
from apps.security_management.models import (
    SecurityThreat, SecurityIncident, SecurityVulnerability, SecurityAudit,
    SecurityPolicy, SecurityTraining, SecurityTrainingRecord, SecurityRiskAssessment,
    SecurityMonitoringRule, SecurityAlert, SecurityConfiguration
)
from apps.security_management.services import (
    SecurityThreatService, SecurityIncidentService, SecurityVulnerabilityService,
    SecurityAuditService, SecurityPolicyService, SecurityTrainingService,
    SecurityRiskAssessmentService, SecurityAlertService, SecurityDashboardService,
    SecurityConfigurationService
)

User = get_user_model()


def test_security_management_system():
    """Test the complete security management system"""
    print("🔒 Testing Security Management System")
    print("=" * 50)
    
    # Create test users
    admin_user = create_test_users()
    
    # Test each component
    test_security_threats(admin_user)
    test_security_incidents(admin_user)
    test_security_vulnerabilities(admin_user)
    test_security_audits(admin_user)
    test_security_policies(admin_user)
    test_security_training(admin_user)
    test_security_risk_assessments(admin_user)
    test_security_monitoring_rules(admin_user)
    test_security_alerts(admin_user)
    test_security_configurations(admin_user)
    test_security_dashboard(admin_user)
    
    print("\n✅ All security management tests completed successfully!")


def create_test_users():
    """Create test users for security testing"""
    print("\n👤 Creating test users...")
    
    admin_user, created = User.objects.get_or_create(
        username='security_admin',
        defaults={
            'email': 'security@test.com',
            'first_name': 'Security',
            'last_name': 'Admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        admin_user.set_password('testpass123')
        admin_user.save()
        print(f"✅ Created admin user: {admin_user.username}")
    else:
        print(f"✅ Using existing admin user: {admin_user.username}")
    
    return admin_user


def test_security_threats(admin_user):
    """Test security threat management"""
    print("\n🚨 Testing Security Threats...")
    
    # Create test threat
    threat_data = {
        'threat_type': 'Malware Detection',
        'severity': 'high',
        'source_ip': '192.168.1.100',
        'target_resource': 'web-server-01',
        'description': 'Suspicious malware activity detected on web server',
        'detection_method': 'Antivirus Scan',
        'threat_indicators': {
            'file_hash': 'abc123def456',
            'process_name': 'suspicious.exe',
            'network_connections': ['malicious-domain.com']
        },
        'mitigation_actions': [
            'Quarantine infected files',
            'Block malicious IP addresses',
            'Update antivirus signatures'
        ]
    }
    
    threat = SecurityThreatService.create_threat(threat_data, admin_user)
    print(f"✅ Created threat: {threat.threat_type} (ID: {threat.id})")
    
    # Test threat statistics
    stats = SecurityThreatService.get_threat_statistics()
    print(f"✅ Threat statistics: {stats['total_threats']} total, {stats['active_threats']} active")
    
    # Test threat trends
    trends = SecurityThreatService.get_threat_trends(7)
    print(f"✅ Retrieved {len(trends)} days of threat trends")
    
    # Test status update
    updated_threat = SecurityThreatService.update_threat_status(
        str(threat.id), 'investigating', admin_user, 'Investigation started'
    )
    print(f"✅ Updated threat status to: {updated_threat.status}")


def test_security_incidents(admin_user):
    """Test security incident management"""
    print("\n🚨 Testing Security Incidents...")
    
    # Create test incident
    incident_data = {
        'title': 'Data Breach Attempt',
        'incident_type': 'data_breach',
        'severity': 'critical',
        'description': 'Unauthorized access attempt to customer database',
        'impact_assessment': 'Potential exposure of customer PII',
        'affected_systems': ['database-server-01', 'web-app-frontend'],
        'affected_users': ['customer_data'],
        'occurred_at': timezone.now() - timedelta(hours=2),
        'response_actions': [
            'Isolate affected systems',
            'Change database passwords',
            'Review access logs'
        ]
    }
    
    incident = SecurityIncidentService.create_incident(incident_data, admin_user)
    print(f"✅ Created incident: {incident.title} (Number: {incident.incident_number})")
    
    # Test timeline update
    timeline_entry = {
        'action': 'Initial Response',
        'description': 'Security team notified and response initiated',
        'status': 'investigating'
    }
    
    updated_incident = SecurityIncidentService.update_incident_timeline(
        str(incident.id), timeline_entry, admin_user
    )
    print(f"✅ Added timeline entry to incident: {incident.incident_number}")
    
    # Test incident statistics
    stats = SecurityIncidentService.get_incident_statistics()
    print(f"✅ Incident statistics: {stats['total_incidents']} total, {stats['open_incidents']} open")


def test_security_vulnerabilities(admin_user):
    """Test security vulnerability management"""
    print("\n🔍 Testing Security Vulnerabilities...")
    
    # Create test vulnerability
    vuln_data = {
        'title': 'SQL Injection in Login Form',
        'description': 'SQL injection vulnerability found in user login form',
        'severity': 'high',
        'cvss_score': 8.5,
        'cve_id': 'CVE-2024-12345',
        'affected_systems': ['web-app-01', 'database-01'],
        'affected_components': ['login_form.php', 'user_auth.js'],
        'exploit_available': True,
        'patch_available': True,
        'remediation_steps': 'Apply security patch v2.1.3 and implement input validation',
        'workaround': 'Disable login form temporarily',
        'due_date': timezone.now() + timedelta(days=7)
    }
    
    vulnerability = SecurityVulnerabilityService.create_vulnerability(vuln_data, admin_user)
    print(f"✅ Created vulnerability: {vulnerability.title} (ID: {vulnerability.vulnerability_id})")
    
    # Test vulnerability statistics
    stats = SecurityVulnerabilityService.get_vulnerability_statistics()
    print(f"✅ Vulnerability statistics: {stats['total_vulnerabilities']} total, {stats['critical_vulnerabilities']} critical")
    
    # Test vulnerability metrics
    metrics = SecurityVulnerabilityService.get_vulnerability_metrics()
    print(f"✅ Retrieved vulnerability metrics for {len(metrics)} severity levels")


def test_security_audits(admin_user):
    """Test security audit management"""
    print("\n📋 Testing Security Audits...")
    
    # Create test audit
    audit_data = {
        'audit_name': 'Annual Security Compliance Audit',
        'audit_type': 'compliance',
        'scope': 'Review all security controls and compliance with ISO 27001',
        'objectives': [
            'Verify access control implementation',
            'Review data protection measures',
            'Assess incident response procedures'
        ],
        'methodology': 'Document review, interviews, and technical testing',
        'compliance_frameworks': ['ISO 27001', 'SOC 2'],
        'scheduled_date': timezone.now() + timedelta(days=30)
    }
    
    audit = SecurityAuditService.create_audit(audit_data, admin_user)
    print(f"✅ Created audit: {audit.audit_name}")
    
    # Test audit statistics
    stats = SecurityAuditService.get_audit_statistics()
    print(f"✅ Audit statistics: {stats['total_audits']} total, {stats['pending_audits']} pending")


def test_security_policies(admin_user):
    """Test security policy management"""
    print("\n📜 Testing Security Policies...")
    
    # Create test policy
    policy_data = {
        'policy_name': 'Remote Work Security Policy',
        'policy_type': 'access_control',
        'description': 'Security requirements for remote work arrangements',
        'policy_content': '''
        Remote Work Security Requirements:
        1. Use company-approved VPN for all connections
        2. Enable full disk encryption on all devices
        3. Use multi-factor authentication for all systems
        4. Regular security training completion required
        ''',
        'compliance_requirements': ['ISO 27001', 'NIST Cybersecurity Framework'],
        'enforcement_rules': [
            'VPN connection monitoring',
            'Device encryption verification',
            'MFA compliance checking'
        ],
        'effective_date': timezone.now(),
        'review_date': timezone.now() + timedelta(days=365)
    }
    
    policy = SecurityPolicyService.create_policy(policy_data, admin_user)
    print(f"✅ Created policy: {policy.policy_name}")
    
    # Test policy statistics
    stats = SecurityPolicyService.get_policy_statistics()
    print(f"✅ Policy statistics: {stats['total_policies']} total, {stats['active_policies']} active")


def test_security_training(admin_user):
    """Test security training management"""
    print("\n🎓 Testing Security Training...")
    
    # Create test training
    training_data = {
        'training_name': 'Advanced Phishing Detection',
        'training_type': 'phishing_simulation',
        'description': 'Advanced training on detecting sophisticated phishing attempts',
        'content': '''
        Training modules:
        1. Spear phishing identification
        2. Business email compromise (BEC) detection
        3. Social engineering tactics
        4. Reporting procedures
        ''',
        'duration_minutes': 60,
        'required_for_roles': ['all_employees', 'executives'],
        'completion_criteria': {
            'min_score': 85,
            'max_attempts': 2,
            'time_limit': 90
        }
    }
    
    training = SecurityTraining.objects.create(
        **training_data,
        created_by=admin_user,
        status='published'
    )
    print(f"✅ Created training: {training.training_name}")
    
    # Test user enrollment
    record = SecurityTrainingService.enroll_user_in_training(
        str(training.id), admin_user.id
    )
    print(f"✅ Enrolled user in training: {record.status}")
    
    # Test training statistics
    stats = SecurityTrainingService.get_training_statistics()
    print(f"✅ Training statistics: {stats['total_trainings']} total, {stats['published_trainings']} published")
    
    # Test training metrics
    metrics = SecurityTrainingService.get_training_metrics()
    print(f"✅ Retrieved training metrics for {len(metrics)} training types")


def test_security_risk_assessments(admin_user):
    """Test security risk assessment management"""
    print("\n⚖️ Testing Security Risk Assessments...")
    
    # Test risk calculation
    risk_score, risk_level = SecurityRiskAssessmentService.calculate_risk_score(
        'high', 'medium'
    )
    print(f"✅ Risk calculation: Score {risk_score}, Level {risk_level}")
    
    # Create test risk assessment
    assessment_data = {
        'assessment_name': 'Cloud Infrastructure Risk Assessment',
        'asset_category': 'Cloud Infrastructure',
        'asset_description': 'AWS-based e-commerce infrastructure',
        'threat_sources': [
            'External attackers',
            'Insider threats',
            'Cloud service provider risks'
        ],
        'vulnerabilities': [
            'Misconfigured security groups',
            'Unencrypted data storage',
            'Weak access controls'
        ],
        'existing_controls': [
            'AWS CloudTrail logging',
            'Multi-factor authentication',
            'Regular security assessments'
        ],
        'likelihood': 'medium',
        'impact': 'high',
        'risk_level': risk_level,
        'risk_score': risk_score,
        'recommended_controls': [
            'Implement AWS Config rules',
            'Enable GuardDuty monitoring',
            'Regular penetration testing'
        ],
        'residual_risk': 'low',
        'review_date': timezone.now() + timedelta(days=180)
    }
    
    assessment = SecurityRiskAssessment.objects.create(
        **assessment_data,
        assessor=admin_user,
        status='approved'
    )
    print(f"✅ Created risk assessment: {assessment.assessment_name}")
    
    # Test risk statistics
    stats = SecurityRiskAssessmentService.get_risk_statistics()
    print(f"✅ Risk statistics: {stats['total_assessments']} total, {stats['high_risk_assessments']} high risk")


def test_security_monitoring_rules(admin_user):
    """Test security monitoring rules"""
    print("\n📊 Testing Security Monitoring Rules...")
    
    # Create test monitoring rule
    rule_data = {
        'rule_name': 'Suspicious File Access Pattern',
        'rule_type': 'anomaly_detection',
        'description': 'Detect unusual file access patterns that may indicate data exfiltration',
        'rule_logic': 'file_access_count > baseline * 5 AND access_time = off_hours',
        'conditions': {
            'metric': 'file_access_count',
            'threshold_multiplier': 5,
            'time_condition': 'off_hours',
            'file_types': ['*.pdf', '*.docx', '*.xlsx']
        },
        'actions': [
            'create_high_priority_alert',
            'log_detailed_activity',
            'notify_security_team',
            'require_manager_approval'
        ],
        'severity': 'high',
        'false_positive_rate': 0.05
    }
    
    rule = SecurityMonitoringRule.objects.create(
        **rule_data,
        created_by=admin_user,
        status='active'
    )
    print(f"✅ Created monitoring rule: {rule.rule_name}")


def test_security_alerts(admin_user):
    """Test security alert management"""
    print("\n🚨 Testing Security Alerts...")
    
    # Create test alert
    alert_data = {
        'alert_type': 'security_event',
        'severity': 'high',
        'title': 'Multiple Failed Login Attempts Detected',
        'description': 'User account has exceeded failed login attempt threshold',
        'source_system': 'Authentication Service',
        'event_data': {
            'username': 'test_user',
            'ip_address': '192.168.1.50',
            'attempt_count': 8,
            'time_window': '10 minutes'
        }
    }
    
    alert = SecurityAlert.objects.create(**alert_data)
    print(f"✅ Created alert: {alert.title}")
    
    # Test alert acknowledgment
    acknowledged_alert = SecurityAlertService.acknowledge_alert(
        str(alert.id), admin_user
    )
    print(f"✅ Acknowledged alert: {acknowledged_alert.status}")
    
    # Test alert statistics
    stats = SecurityAlertService.get_alert_statistics()
    print(f"✅ Alert statistics: {stats['total_alerts']} total, {stats['open_alerts']} open")


def test_security_configurations(admin_user):
    """Test security configuration management"""
    print("\n⚙️ Testing Security Configurations...")
    
    # Create test configuration
    config_data = {
        'config_name': 'Web Application Firewall Rules',
        'config_type': 'firewall',
        'description': 'WAF configuration for e-commerce application',
        'configuration_data': {
            'rules': [
                {'rule_id': 'SQL_INJECTION', 'action': 'block', 'enabled': True},
                {'rule_id': 'XSS_PROTECTION', 'action': 'block', 'enabled': True},
                {'rule_id': 'RATE_LIMITING', 'action': 'throttle', 'enabled': True}
            ],
            'whitelist_ips': ['192.168.1.0/24'],
            'blacklist_countries': ['CN', 'RU']
        },
        'baseline_config': {
            'default_action': 'allow',
            'logging_enabled': True,
            'monitoring_enabled': True
        },
        'compliance_requirements': ['PCI DSS', 'OWASP Top 10']
    }
    
    config = SecurityConfiguration.objects.create(
        **config_data,
        managed_by=admin_user,
        status='active'
    )
    print(f"✅ Created configuration: {config.config_name}")
    
    # Test configuration validation
    validated_config = SecurityConfigurationService.validate_configuration(
        str(config.id), admin_user
    )
    print(f"✅ Validated configuration: {validated_config.validation_status}")
    
    # Test configuration statistics
    stats = SecurityConfigurationService.get_configuration_statistics()
    print(f"✅ Configuration statistics: {stats['total_configurations']} total, {stats['active_configurations']} active")


def test_security_dashboard(admin_user):
    """Test security dashboard functionality"""
    print("\n📊 Testing Security Dashboard...")
    
    # Test dashboard statistics
    dashboard_stats = SecurityDashboardService.get_dashboard_stats()
    print(f"✅ Dashboard stats: Compliance score {dashboard_stats['compliance_score']}%")
    print(f"   - Total threats: {dashboard_stats['total_threats']}")
    print(f"   - Active incidents: {dashboard_stats['active_incidents']}")
    print(f"   - Critical vulnerabilities: {dashboard_stats['critical_vulnerabilities']}")
    print(f"   - Active alerts: {dashboard_stats['active_alerts']}")
    
    # Test security trends
    trends = SecurityDashboardService.get_security_trends(7)
    print(f"✅ Retrieved security trends:")
    print(f"   - Threat trends: {len(trends['threat_trends'])} days")
    print(f"   - Vulnerability metrics: {len(trends['vulnerability_metrics'])} severity levels")
    print(f"   - Training metrics: {len(trends['training_metrics'])} training types")


if __name__ == '__main__':
    try:
        test_security_management_system()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)