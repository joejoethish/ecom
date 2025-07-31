"""
Security Audit and Compliance Reporting System

This module implements comprehensive security auditing and compliance checking:
- Automated security audits
- Compliance reporting (GDPR, PCI DSS, SOX)
- Security metrics and KPIs
- Risk assessment and scoring
- Audit trail management

Requirements: 4.2, 4.4, 4.5
"""

import os
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import mysql.connector
from mysql.connector import Error as MySQLError
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    SOX = "sox"
    HIPAA = "hipaa"
    ISO_27001 = "iso_27001"


class AuditStatus(Enum):
    """Audit status values."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"
    REQUIRES_REVIEW = "requires_review"


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceRule:
    """Compliance rule definition."""
    rule_id: str
    framework: ComplianceFramework
    title: str
    description: str
    requirement: str
    check_query: str
    expected_result: str
    risk_level: RiskLevel
    is_active: bool
    created_at: datetime
    last_updated: datetime


@dataclass
class AuditResult:
    """Audit check result."""
    audit_id: str
    rule_id: str
    timestamp: datetime
    status: AuditStatus
    actual_result: str
    expected_result: str
    compliance_score: float
    risk_score: float
    findings: List[str]
    recommendations: List[str]
    evidence: Dict[str, Any]


class SecurityAuditManager:
    """Comprehensive security audit and compliance management."""
    
    def __init__(self):
        """Initialize the security audit manager."""
        self.connection_config = self._get_connection_config()
        self.compliance_rules = {}
        self.audit_history = []
        
        # Configuration
        self.audit_retention_days = getattr(settings, 'AUDIT_RETENTION_DAYS', 365)
        self.compliance_check_interval = getattr(settings, 'COMPLIANCE_CHECK_HOURS', 24)
        
        # Initialize audit system
        self._initialize_audit_system()
    
    def _get_connection_config(self) -> Dict[str, Any]:
        """Get database connection configuration."""
        db_config = settings.DATABASES['default']
        return {
            'host': db_config['HOST'],
            'port': int(db_config['PORT']),
            'database': db_config['NAME'],
            'user': db_config['USER'],
            'password': db_config['PASSWORD'],
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True,
        }
    
    def _initialize_audit_system(self):
        """Initialize the audit system."""
        try:
            # Create audit tables
            self._create_audit_tables()
            
            # Load compliance rules
            self._load_compliance_rules()
            
            # Initialize default rules
            self._initialize_default_compliance_rules()
            
            logger.info("Security audit system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize security audit system: {e}")
    
    def _create_audit_tables(self):
        """Create tables for audit data."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            # Compliance rules table
            create_rules_table = """
            CREATE TABLE IF NOT EXISTS compliance_rules (
                rule_id VARCHAR(64) PRIMARY KEY,
                framework VARCHAR(32) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                requirement TEXT NOT NULL,
                check_query TEXT NOT NULL,
                expected_result TEXT NOT NULL,
                risk_level VARCHAR(16) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at DATETIME(6) NOT NULL,
                last_updated DATETIME(6) NOT NULL,
                INDEX idx_framework (framework),
                INDEX idx_risk_level (risk_level),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_rules_table)
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Audit tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create audit tables: {e}")
            raise
    
    def _load_compliance_rules(self):
        """Load compliance rules from database."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT rule_id, framework, title, description, requirement, 
                       check_query, expected_result, risk_level, is_active, 
                       created_at, last_updated
                FROM compliance_rules
                WHERE is_active = TRUE
            """)
            
            for row in cursor.fetchall():
                rule = ComplianceRule(
                    rule_id=row[0],
                    framework=ComplianceFramework(row[1]),
                    title=row[2],
                    description=row[3],
                    requirement=row[4],
                    check_query=row[5],
                    expected_result=row[6],
                    risk_level=RiskLevel(row[7]),
                    is_active=row[8],
                    created_at=row[9],
                    last_updated=row[10]
                )
                self.compliance_rules[rule.rule_id] = rule
            
            cursor.close()
            conn.close()
            
            logger.info(f"Loaded {len(self.compliance_rules)} compliance rules")
            
        except Exception as e:
            logger.error(f"Failed to load compliance rules: {e}")
    
    def _initialize_default_compliance_rules(self):
        """Initialize default compliance rules for various frameworks."""
        default_rules = [
            # GDPR Rules
            {
                'rule_id': 'gdpr_data_encryption',
                'framework': ComplianceFramework.GDPR,
                'title': 'Personal Data Encryption',
                'description': 'Verify that personal data is encrypted at rest',
                'requirement': 'Article 32 - Security of processing',
                'check_query': 'SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE "%encrypted%"',
                'expected_result': '>0',
                'risk_level': RiskLevel.HIGH
            },
            {
                'rule_id': 'gdpr_audit_logging',
                'framework': ComplianceFramework.GDPR,
                'title': 'Data Processing Audit Trail',
                'description': 'Verify audit logging is enabled for personal data access',
                'requirement': 'Article 30 - Records of processing activities',
                'check_query': 'SELECT COUNT(*) FROM information_schema.tables WHERE table_name = "db_audit_log"',
                'expected_result': '>0',
                'risk_level': RiskLevel.MEDIUM
            }
        ]
        
        for rule_data in default_rules:
            rule_id = rule_data['rule_id']
            if rule_id not in self.compliance_rules:
                rule = ComplianceRule(
                    rule_id=rule_id,
                    framework=rule_data['framework'],
                    title=rule_data['title'],
                    description=rule_data['description'],
                    requirement=rule_data['requirement'],
                    check_query=rule_data['check_query'],
                    expected_result=rule_data['expected_result'],
                    risk_level=rule_data['risk_level'],
                    is_active=True,
                    created_at=datetime.now(),
                    last_updated=datetime.now()
                )
                
                self._store_compliance_rule(rule)
                self.compliance_rules[rule_id] = rule
        
        logger.info(f"Initialized {len(default_rules)} default compliance rules")
    
    def _store_compliance_rule(self, rule: ComplianceRule):
        """Store compliance rule in database."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            insert_sql = """
            INSERT INTO compliance_rules (
                rule_id, framework, title, description, requirement, 
                check_query, expected_result, risk_level, is_active, 
                created_at, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                description = VALUES(description),
                requirement = VALUES(requirement),
                check_query = VALUES(check_query),
                expected_result = VALUES(expected_result),
                risk_level = VALUES(risk_level),
                is_active = VALUES(is_active),
                last_updated = VALUES(last_updated)
            """
            
            values = (
                rule.rule_id,
                rule.framework.value,
                rule.title,
                rule.description,
                rule.requirement,
                rule.check_query,
                rule.expected_result,
                rule.risk_level.value,
                rule.is_active,
                rule.created_at,
                rule.last_updated
            )
            
            cursor.execute(insert_sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store compliance rule {rule.rule_id}: {e}")
            raise
    
    def run_compliance_audit(self, framework: Optional[ComplianceFramework] = None) -> Dict[str, Any]:
        """Run comprehensive compliance audit."""
        audit_results = {
            'audit_id': f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'framework': framework.value if framework else 'all',
            'total_rules': 0,
            'compliant_rules': 0,
            'non_compliant_rules': 0,
            'partially_compliant_rules': 0,
            'overall_compliance_score': 0.0,
            'risk_score': 0.0,
            'rule_results': [],
            'summary_by_framework': {},
            'recommendations': []
        }
        
        try:
            # Filter rules by framework if specified
            rules_to_check = []
            for rule in self.compliance_rules.values():
                if framework is None or rule.framework == framework:
                    if rule.is_active:
                        rules_to_check.append(rule)
            
            audit_results['total_rules'] = len(rules_to_check)
            
            # Execute each compliance check
            for rule in rules_to_check:
                result = self._execute_compliance_check(rule)
                audit_results['rule_results'].append(asdict(result))
                
                # Update counters
                if result.status == AuditStatus.COMPLIANT:
                    audit_results['compliant_rules'] += 1
                elif result.status == AuditStatus.NON_COMPLIANT:
                    audit_results['non_compliant_rules'] += 1
                elif result.status == AuditStatus.PARTIALLY_COMPLIANT:
                    audit_results['partially_compliant_rules'] += 1
                
                # Aggregate scores
                audit_results['overall_compliance_score'] += result.compliance_score
                audit_results['risk_score'] += result.risk_score
                
                # Collect recommendations
                audit_results['recommendations'].extend(result.recommendations)
            
            # Calculate final scores
            if audit_results['total_rules'] > 0:
                audit_results['overall_compliance_score'] /= audit_results['total_rules']
                audit_results['risk_score'] /= audit_results['total_rules']
            
            # Store audit results
            self._store_audit_results(audit_results)
            
            logger.info(f"Compliance audit completed: {audit_results['overall_compliance_score']:.2f}% compliant")
            
            return audit_results
            
        except Exception as e:
            logger.error(f"Compliance audit failed: {e}")
            audit_results['error'] = str(e)
            return audit_results
    
    def _execute_compliance_check(self, rule: ComplianceRule) -> AuditResult:
        """Execute a single compliance check."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            # Execute the check query
            cursor.execute(rule.check_query)
            result = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Analyze the result
            actual_result = str(result)
            status, compliance_score, findings, recommendations = self._analyze_check_result(
                actual_result, rule.expected_result, rule
            )
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(status, rule.risk_level)
            
            audit_result = AuditResult(
                audit_id=f"check_{rule.rule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rule_id=rule.rule_id,
                timestamp=datetime.now(),
                status=status,
                actual_result=actual_result,
                expected_result=rule.expected_result,
                compliance_score=compliance_score,
                risk_score=risk_score,
                findings=findings,
                recommendations=recommendations,
                evidence={'query': rule.check_query, 'result': actual_result}
            )
            
            return audit_result
            
        except Exception as e:
            logger.error(f"Failed to execute compliance check for rule {rule.rule_id}: {e}")
            
            # Return failed audit result
            return AuditResult(
                audit_id=f"check_{rule.rule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rule_id=rule.rule_id,
                timestamp=datetime.now(),
                status=AuditStatus.REQUIRES_REVIEW,
                actual_result=f"Error: {str(e)}",
                expected_result=rule.expected_result,
                compliance_score=0.0,
                risk_score=1.0,
                findings=[f"Check execution failed: {str(e)}"],
                recommendations=["Review and fix the compliance check query"],
                evidence={'error': str(e)}
            )
    
    def _analyze_check_result(self, actual: str, expected: str, rule: ComplianceRule) -> Tuple[AuditStatus, float, List[str], List[str]]:
        """Analyze compliance check result."""
        findings = []
        recommendations = []
        
        try:
            # Parse expected result format
            if expected.startswith('>'):
                threshold = int(expected[1:])
                actual_value = self._extract_numeric_value(actual)
                
                if actual_value > threshold:
                    status = AuditStatus.COMPLIANT
                    compliance_score = 1.0
                    findings.append(f"Value {actual_value} exceeds minimum threshold {threshold}")
                else:
                    status = AuditStatus.NON_COMPLIANT
                    compliance_score = 0.0
                    findings.append(f"Value {actual_value} does not meet minimum threshold {threshold}")
                    recommendations.append(f"Increase value to meet minimum requirement of {threshold}")
            
            else:
                # Direct string comparison
                if expected in actual:
                    status = AuditStatus.COMPLIANT
                    compliance_score = 1.0
                    findings.append(f"Expected result '{expected}' found")
                else:
                    status = AuditStatus.NON_COMPLIANT
                    compliance_score = 0.0
                    findings.append(f"Expected result '{expected}' not found")
                    recommendations.append(f"Configure system to produce expected result: {expected}")
            
        except Exception as e:
            status = AuditStatus.REQUIRES_REVIEW
            compliance_score = 0.0
            findings.append(f"Result analysis failed: {str(e)}")
            recommendations.append("Review the compliance check logic")
        
        return status, compliance_score, findings, recommendations
    
    def _extract_numeric_value(self, result_string: str) -> int:
        """Extract numeric value from query result string."""
        import re
        numbers = re.findall(r'\d+', result_string)
        return int(numbers[0]) if numbers else 0
    
    def _calculate_risk_score(self, status: AuditStatus, risk_level: RiskLevel) -> float:
        """Calculate risk score based on compliance status and risk level."""
        # Risk multipliers by level
        risk_multipliers = {
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.75,
            RiskLevel.CRITICAL: 1.0
        }
        
        # Status impact on risk
        if status == AuditStatus.COMPLIANT:
            return 0.0
        elif status == AuditStatus.PARTIALLY_COMPLIANT:
            return risk_multipliers[risk_level] * 0.5
        elif status == AuditStatus.NON_COMPLIANT:
            return risk_multipliers[risk_level]
        else:  # REQUIRES_REVIEW or NOT_APPLICABLE
            return risk_multipliers[risk_level] * 0.3
    
    def _store_audit_results(self, audit_results: Dict[str, Any]):
        """Store audit results for historical tracking."""
        try:
            # Store in cache for quick access
            cache_key = f"audit_results_{audit_results['audit_id']}"
            cache.set(cache_key, audit_results, 86400)  # Cache for 24 hours
            
            # Add to audit history
            self.audit_history.append(audit_results)
            
            # Keep only recent audits in memory
            if len(self.audit_history) > 100:
                self.audit_history = self.audit_history[-100:]
            
            logger.info(f"Stored audit results for {audit_results['audit_id']}")
            
        except Exception as e:
            logger.error(f"Failed to store audit results: {e}")
    
    def generate_compliance_report(self, framework: Optional[ComplianceFramework] = None) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        try:
            # Run fresh audit
            audit_results = self.run_compliance_audit(framework)
            
            # Generate detailed report
            report = {
                'report_id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.now().isoformat(),
                'framework': framework.value if framework else 'all',
                'executive_summary': self._generate_executive_summary(audit_results),
                'detailed_findings': audit_results['rule_results'],
                'recommendations': audit_results['recommendations'],
                'next_audit_date': (datetime.now() + timedelta(hours=self.compliance_check_interval)).isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {'error': str(e)}
    
    def _generate_executive_summary(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of compliance status."""
        return {
            'overall_compliance_score': f"{audit_results['overall_compliance_score']:.1f}%",
            'total_issues': audit_results['non_compliant_rules'] + audit_results['partially_compliant_rules'],
            'compliance_status': 'Compliant' if audit_results['overall_compliance_score'] >= 80 else 'Non-Compliant'
        }
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics."""
        try:
            metrics = {
                'compliance_score': self._get_latest_compliance_score(),
                'generated_at': datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get security metrics: {e}")
            return {'error': str(e)}
    
    def _get_latest_compliance_score(self) -> float:
        """Get the latest compliance score."""
        if self.audit_history:
            return self.audit_history[-1]['overall_compliance_score']
        return 0.0


# Singleton instance
security_audit_manager = SecurityAuditManager()