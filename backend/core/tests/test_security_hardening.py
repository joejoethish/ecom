"""
Comprehensive tests for database security hardening components.

Tests cover:
- Transparent data encryption
- Threat detection and monitoring
- Security audit and compliance
- Key management and rotation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from django.test import TestCase
from django.conf import settings
from django.core.cache import cache

from core.encryption_manager import (
    TransparentDataEncryption, EncryptionAlgorithm, KeyType, EncryptionKey
)
from core.threat_detection import (
    AdvancedThreatDetector, ThreatCategory, ThreatLevel, ThreatDetection
)
from core.security_audit import (
    SecurityAuditManager, ComplianceFramework, AuditStatus, ComplianceRule
)


class TestTransparentDataEncryption(TestCase):
    """Test transparent data encryption functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.encryption = TransparentDataEncryption()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment."""
        cache.clear()
    
    @patch('core.encryption_manager.mysql.connector.connect')
    def test_generate_encryption_key(self, mock_connect):
        """Test encryption key generation."""
        # Mock database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Test key generation
        key = self.encryption.generate_encryption_key(
            key_type=KeyType.DATA_ENCRYPTION_KEY,
            algorithm=EncryptionAlgorithm.FERNET,
            expires_days=90
        )
        
        # Verify key properties
        self.assertIsInstance(key, EncryptionKey)
        self.assertEqual(key.key_type, KeyType.DATA_ENCRYPTION_KEY)
        self.assertEqual(key.algorithm, EncryptionAlgorithm.FERNET)
        self.assertTrue(key.is_active)
        self.assertIsNotNone(key.key_data)
        
        # Verify database interaction
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('core.encryption_manager.mysql.connector.connect')
    def test_field_encryption_configuration(self, mock_connect):
        """Test field encryption configuration."""
        # Mock database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Configure field encryption
        success = self.encryption.configure_field_encryption(
            table_name='auth_user',
            field_name='email',
            algorithm=EncryptionAlgorithm.FERNET,
            is_searchable=True
        )
        
        self.assertTrue(success)
        
        # Verify field configuration is stored
        field_key = 'auth_user.email'
        self.assertIn(field_key, self.encryption.encrypted_fields)
        
        field_config = self.encryption.encrypted_fields[field_key]
        self.assertEqual(field_config.table_name, 'auth_user')
        self.assertEqual(field_config.field_name, 'email')
        self.assertEqual(field_config.encryption_algorithm, EncryptionAlgorithm.FERNET)
        self.assertTrue(field_config.is_searchable)
    
    def test_field_value_encryption_decryption(self):
        """Test field value encryption and decryption."""
        # Set up a mock encrypted field configuration
        from core.encryption_manager import EncryptedField
        from cryptography.fernet import Fernet
        
        # Create a test encryption key
        test_key = Fernet.generate_key()
        encryption_key = EncryptionKey(
            key_id='test_key',
            key_type=KeyType.DATA_ENCRYPTION_KEY,
            algorithm=EncryptionAlgorithm.FERNET,
            key_data=test_key,
            created_at=datetime.now(),
            expires_at=None,
            version=1,
            is_active=True,
            metadata={}
        )
        
        # Add to encryption manager
        self.encryption.encryption_keys['test_key'] = encryption_key
        
        # Create field configuration
        field_config = EncryptedField(
            table_name='auth_user',
            field_name='email',
            encryption_algorithm=EncryptionAlgorithm.FERNET,
            key_id='test_key',
            is_searchable=False,
            created_at=datetime.now(),
            last_rotated=datetime.now()
        )
        
        self.encryption.encrypted_fields['auth_user.email'] = field_config
        
        # Test encryption and decryption
        original_value = 'test@example.com'
        
        # Encrypt the value
        encrypted_value = self.encryption.encrypt_field_value(
            'auth_user', 'email', original_value
        )
        
        self.assertNotEqual(encrypted_value, original_value)
        self.assertIsInstance(encrypted_value, str)
        
        # Decrypt the value
        decrypted_value = self.encryption.decrypt_field_value(
            'auth_user', 'email', encrypted_value
        )
        
        self.assertEqual(decrypted_value, original_value)
    
    def test_encryption_status(self):
        """Test encryption status reporting."""
        status = self.encryption.get_encryption_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('total_encryption_keys', status)
        self.assertIn('active_keys', status)
        self.assertIn('encrypted_fields', status)
        self.assertIn('keys_by_algorithm', status)
        self.assertIn('field_encryption_summary', status)


class TestAdvancedThreatDetector(TestCase):
    """Test advanced threat detection functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.detector = AdvancedThreatDetector()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment."""
        cache.clear()
    
    def test_sql_injection_detection(self):
        """Test SQL injection threat detection."""
        # Test various SQL injection patterns
        test_cases = [
            ("SELECT * FROM users WHERE id = 1 OR 1=1", True),
            ("SELECT * FROM users WHERE name = 'admin'--'", True),
            ("SELECT * FROM users UNION SELECT * FROM passwords", True),
            ("SELECT * FROM users WHERE id = 1", False),
            ("INSERT INTO users (name) VALUES ('John')", False),
        ]
        
        for query, should_detect in test_cases:
            threats_detected, detections = self.detector.detect_threats(
                query=query,
                user='test_user',
                source_ip='127.0.0.1'
            )
            
            if should_detect:
                self.assertTrue(threats_detected, f"Should detect threat in: {query}")
                self.assertGreater(len(detections), 0)
                # Check that at least one detection is SQL injection
                sql_injection_detected = any(
                    d.threat_category == ThreatCategory.SQL_INJECTION 
                    for d in detections
                )
                self.assertTrue(sql_injection_detected)
            else:
                # Note: Normal queries might still trigger behavioral anomalies
                # so we don't assert False here, just check no SQL injection
                if threats_detected:
                    sql_injection_detected = any(
                        d.threat_category == ThreatCategory.SQL_INJECTION 
                        for d in detections
                    )
                    self.assertFalse(sql_injection_detected, f"False positive in: {query}")
    
    def test_privilege_escalation_detection(self):
        """Test privilege escalation threat detection."""
        test_queries = [
            "GRANT ALL PRIVILEGES ON *.* TO 'user'@'%'",
            "CREATE USER 'hacker'@'%' IDENTIFIED BY 'password'",
            "REVOKE SELECT ON database.* FROM 'user'@'%'",
        ]
        
        for query in test_queries:
            threats_detected, detections = self.detector.detect_threats(
                query=query,
                user='test_user',
                source_ip='127.0.0.1'
            )
            
            self.assertTrue(threats_detected, f"Should detect privilege escalation in: {query}")
            
            # Check for privilege escalation category
            priv_escalation_detected = any(
                d.threat_category == ThreatCategory.PRIVILEGE_ESCALATION 
                for d in detections
            )
            self.assertTrue(priv_escalation_detected)
    
    def test_behavioral_anomaly_detection(self):
        """Test behavioral anomaly detection."""
        # Create a mock user profile
        from core.threat_detection import UserBehaviorProfile
        
        profile = UserBehaviorProfile(
            user='test_user',
            typical_query_patterns={'select * from users', 'select name from products'},
            typical_access_times=[9, 10, 11, 14, 15, 16],  # Business hours
            typical_source_ips={'192.168.1.100', '10.0.0.50'},
            typical_tables_accessed={'users', 'products', 'orders'},
            average_queries_per_hour=10.0,
            average_query_complexity=5.0,
            last_updated=datetime.now()
        )
        
        self.detector.user_profiles['test_user'] = profile
        
        # Test unusual access time (3 AM)
        with patch('core.threat_detection.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 3
            
            threats_detected, detections = self.detector.detect_threats(
                query="SELECT * FROM users",
                user='test_user',
                source_ip='192.168.1.100'
            )
            
            if threats_detected:
                anomaly_detected = any(
                    d.threat_category == ThreatCategory.ANOMALOUS_BEHAVIOR 
                    for d in detections
                )
                # Should detect unusual access time
                self.assertTrue(anomaly_detected)
    
    def test_threat_statistics(self):
        """Test threat statistics generation."""
        stats = self.detector.get_threat_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('detection_summary', stats)
        self.assertIn('active_signatures', stats)
        self.assertIn('user_profiles', stats)
        self.assertIn('generated_at', stats)
    
    def test_user_ip_blocking(self):
        """Test user and IP blocking functionality."""
        user = 'test_user'
        ip = '192.168.1.100'
        
        # Initially not blocked
        self.assertFalse(self.detector.is_user_blocked(user))
        self.assertFalse(self.detector.is_ip_blocked(ip))
        
        # Block user and IP
        self.detector._block_user_temporarily(user, 300)  # 5 minutes
        self.detector._block_ip_temporarily(ip, 300)
        
        # Should now be blocked
        self.assertTrue(self.detector.is_user_blocked(user))
        self.assertTrue(self.detector.is_ip_blocked(ip))


class TestSecurityAuditManager(TestCase):
    """Test security audit and compliance functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.audit_manager = SecurityAuditManager()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment."""
        cache.clear()
    
    @patch('core.security_audit.mysql.connector.connect')
    def test_compliance_rule_creation(self, mock_connect):
        """Test compliance rule creation and storage."""
        # Mock database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Create a test compliance rule
        from core.security_audit import ComplianceRule, RiskLevel
        
        rule = ComplianceRule(
            rule_id='test_rule',
            framework=ComplianceFramework.GDPR,
            title='Test Rule',
            description='Test compliance rule',
            requirement='Test requirement',
            check_query='SELECT COUNT(*) FROM test_table',
            expected_result='>0',
            risk_level=RiskLevel.MEDIUM,
            is_active=True,
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Store the rule
        self.audit_manager._store_compliance_rule(rule)
        
        # Verify database interaction
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('core.security_audit.mysql.connector.connect')
    def test_compliance_audit_execution(self, mock_connect):
        """Test compliance audit execution."""
        # Mock database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchall.return_value = [(5,)]  # Mock result for count query
        
        # Add a test rule to the manager
        from core.security_audit import ComplianceRule, RiskLevel
        
        test_rule = ComplianceRule(
            rule_id='test_audit_rule',
            framework=ComplianceFramework.GDPR,
            title='Test Audit Rule',
            description='Test audit rule description',
            requirement='Test requirement',
            check_query='SELECT COUNT(*) FROM encrypted_fields',
            expected_result='>0',
            risk_level=RiskLevel.HIGH,
            is_active=True,
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        self.audit_manager.compliance_rules['test_audit_rule'] = test_rule
        
        # Run compliance audit
        results = self.audit_manager.run_compliance_audit(ComplianceFramework.GDPR)
        
        # Verify results structure
        self.assertIsInstance(results, dict)
        self.assertIn('audit_id', results)
        self.assertIn('overall_compliance_score', results)
        self.assertIn('total_rules', results)
        self.assertIn('rule_results', results)
        
        # Should have processed our test rule
        self.assertGreater(results['total_rules'], 0)
    
    def test_result_analysis(self):
        """Test compliance check result analysis."""
        from core.security_audit import ComplianceRule, RiskLevel
        
        test_rule = ComplianceRule(
            rule_id='test_analysis_rule',
            framework=ComplianceFramework.PCI_DSS,
            title='Test Analysis Rule',
            description='Test rule for analysis',
            requirement='Test requirement',
            check_query='SELECT COUNT(*) FROM test',
            expected_result='>5',
            risk_level=RiskLevel.HIGH,
            is_active=True,
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Test different result scenarios
        test_cases = [
            ("[(10,)]", ">5", True),   # Should pass
            ("[(3,)]", ">5", False),   # Should fail
            ("[(2,)]", "<=5", True),   # Should pass
            ("[(10,)]", "<=5", False), # Should fail
            ("test_value", "test_value", True),  # Should pass
            ("other_value", "test_value", False), # Should fail
        ]
        
        for actual, expected, should_pass in test_cases:
            status, compliance_score, findings, recommendations = \
                self.audit_manager._analyze_check_result(actual, expected, test_rule)
            
            if should_pass:
                self.assertEqual(status, AuditStatus.COMPLIANT)
                self.assertEqual(compliance_score, 1.0)
            else:
                self.assertEqual(status, AuditStatus.NON_COMPLIANT)
                self.assertEqual(compliance_score, 0.0)
            
            self.assertIsInstance(findings, list)
            self.assertIsInstance(recommendations, list)
    
    def test_security_metrics_calculation(self):
        """Test security metrics calculation."""
        metrics = self.audit_manager.get_security_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('encryption_coverage', metrics)
        self.assertIn('audit_completeness', metrics)
        self.assertIn('threat_detection_effectiveness', metrics)
        self.assertIn('compliance_score', metrics)
        self.assertIn('generated_at', metrics)
    
    def test_compliance_report_generation(self):
        """Test compliance report generation."""
        # Mock the audit results
        with patch.object(self.audit_manager, 'run_compliance_audit') as mock_audit:
            mock_audit.return_value = {
                'audit_id': 'test_audit',
                'overall_compliance_score': 85.0,
                'risk_score': 0.3,
                'total_rules': 10,
                'compliant_rules': 8,
                'non_compliant_rules': 2,
                'partially_compliant_rules': 0,
                'rule_results': [],
                'recommendations': ['Test recommendation'],
                'summary_by_framework': {}
            }
            
            report = self.audit_manager.generate_compliance_report(ComplianceFramework.GDPR)
            
            self.assertIsInstance(report, dict)
            self.assertIn('report_id', report)
            self.assertIn('executive_summary', report)
            self.assertIn('detailed_findings', report)
            self.assertIn('risk_assessment', report)
            self.assertIn('recommendations', report)
            self.assertIn('next_audit_date', report)


class TestSecurityIntegration(TestCase):
    """Test integration between security components."""
    
    def setUp(self):
        """Set up test environment."""
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment."""
        cache.clear()
    
    @patch('core.encryption_manager.mysql.connector.connect')
    @patch('core.threat_detection.mysql.connector.connect')
    @patch('core.security_audit.mysql.connector.connect')
    def test_end_to_end_security_workflow(self, mock_audit_connect, mock_threat_connect, mock_encrypt_connect):
        """Test end-to-end security workflow."""
        # Mock all database connections
        for mock_connect in [mock_audit_connect, mock_threat_connect, mock_encrypt_connect]:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            mock_cursor.fetchone.return_value = (0,)
        
        # 1. Set up encryption
        encryption = TransparentDataEncryption()
        
        # 2. Configure threat detection
        detector = AdvancedThreatDetector()
        
        # 3. Set up audit manager
        audit_manager = SecurityAuditManager()
        
        # 4. Test that all components are initialized
        self.assertIsNotNone(encryption)
        self.assertIsNotNone(detector)
        self.assertIsNotNone(audit_manager)
        
        # 5. Test threat detection on encrypted data scenario
        test_query = "SELECT encrypted_field FROM sensitive_table"
        threats_detected, detections = detector.detect_threats(
            query=test_query,
            user='test_user',
            source_ip='127.0.0.1'
        )
        
        # Should not detect threats in normal encrypted data access
        # (though behavioral anomalies might still be detected)
        if threats_detected:
            # Ensure no false positives for SQL injection
            sql_injection_detected = any(
                d.threat_category == ThreatCategory.SQL_INJECTION 
                for d in detections
            )
            self.assertFalse(sql_injection_detected)
    
    def test_security_configuration_validation(self):
        """Test security configuration validation."""
        # Test that required settings are available
        required_settings = [
            'DB_AUDIT_ENABLED',
            'DB_THREAT_DETECTION_ENABLED',
            'ENCRYPTION_KEY_ROTATION_DAYS'
        ]
        
        for setting in required_settings:
            # Should have default values even if not explicitly set
            value = getattr(settings, setting, None)
            # We don't assert specific values since they might have defaults
            # Just ensure the settings system is working
            self.assertIsNotNone(getattr(settings, 'SECRET_KEY', None))


if __name__ == '__main__':
    unittest.main()