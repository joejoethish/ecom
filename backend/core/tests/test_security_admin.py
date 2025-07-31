"""
Tests for the database security admin interface.

This module tests:
- Security admin interface functionality
- Audit log viewing and management
- Security event monitoring
- Admin permissions and access control

Requirements: 4.1, 4.2, 4.4, 4.5, 4.6
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta


User = get_user_model()


class SecurityAdminTestCase(TestCase):
    """Test case for security admin interface."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
        
        # Create security tables for testing
        self._create_test_tables()
        self._create_test_data()
    
    def _create_test_tables(self):
        """Create test security tables."""
        with connection.cursor() as cursor:
            # Create audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS db_audit_log (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME(6) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    user VARCHAR(100) NOT NULL,
                    source_ip VARCHAR(45),
                    database_name VARCHAR(100),
                    table_name VARCHAR(100),
                    operation VARCHAR(50),
                    affected_rows INT DEFAULT 0,
                    query_hash VARCHAR(64),
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    additional_data JSON
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # Create security events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS db_security_events (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME(6) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    user VARCHAR(100),
                    source_ip VARCHAR(45),
                    description TEXT NOT NULL,
                    details JSON,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at DATETIME(6),
                    resolved_by VARCHAR(100)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
    
    def _create_test_data(self):
        """Create test audit and security data."""
        with connection.cursor() as cursor:
            # Insert test audit log entries
            cursor.execute("""
                INSERT INTO db_audit_log (
                    timestamp, event_type, user, source_ip, database_name,
                    table_name, operation, affected_rows, query_hash, success
                ) VALUES 
                (%s, 'LOGIN_SUCCESS', 'testuser', '192.168.1.100', 'ecommerce_db', 
                 'auth_user', 'SELECT', 1, 'abc123', TRUE),
                (%s, 'LOGIN_FAILURE', 'hacker', '10.0.0.1', 'ecommerce_db',
                 'auth_user', 'SELECT', 0, 'def456', FALSE)
            """, [datetime.now(), datetime.now()])
            
            # Insert test security events
            cursor.execute("""
                INSERT INTO db_security_events (
                    timestamp, event_type, severity, user, source_ip, description, resolved
                ) VALUES 
                (%s, 'SUSPICIOUS_ACTIVITY', 'HIGH', 'testuser', '192.168.1.100', 
                 'Multiple failed login attempts detected', FALSE),
                (%s, 'THREAT_DETECTED', 'CRITICAL', 'hacker', '10.0.0.1',
                 'SQL injection attempt detected', FALSE)
            """, [datetime.now(), datetime.now()])
    
    def test_security_admin_access_superuser(self):
        """Test that superusers can access security admin."""
        self.client.login(username='admin', password='testpass123')
        
        # Test security dashboard access
        response = self.client.get('/security-admin/')
        self.assertEqual(response.status_code, 200)
    
    def test_security_admin_access_staff(self):
        """Test that staff users can access security admin with proper permissions."""
        self.client.login(username='staff', password='testpass123')
        
        # Test security dashboard access
        response = self.client.get('/security-admin/')
        self.assertEqual(response.status_code, 200)
    
    def test_security_admin_access_denied_regular_user(self):
        """Test that regular users cannot access security admin."""
        self.client.login(username='user', password='testpass123')
        
        # Test security dashboard access denied
        response = self.client.get('/security-admin/')
        self.assertIn(response.status_code, [302, 403])  # Redirect to login or forbidden
    
    def test_audit_log_list_view(self):
        """Test audit log list view."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/security-admin/core/auditlogproxy/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'LOGIN_SUCCESS')
    
    def test_security_events_list_view(self):
        """Test security events list view."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/security-admin/core/securityeventproxy/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SUSPICIOUS_ACTIVITY')
        self.assertContains(response, 'HIGH')
    
    def test_security_dashboard_view(self):
        """Test security dashboard view."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/security-admin/security-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Security Dashboard')
    
    @patch('core.admin.security_admin.database_security_manager')
    def test_resolve_security_event(self, mock_security_manager):
        """Test resolving a security event."""
        self.client.login(username='admin', password='testpass123')
        
        # Mock the security manager
        mock_security_manager.log_audit_event = MagicMock()
        
        response = self.client.post(
            '/security-admin/resolve-security-event/',
            data=json.dumps({'event_id': 1}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))
    
    def test_export_audit_logs(self):
        """Test exporting audit logs to CSV."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/security-admin/export-audit-logs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_security_summary_report(self):
        """Test security summary report generation."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/security-admin/security-report/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('summary', data)
        self.assertIn('event_breakdown', data)
    
    @patch('core.admin.security_admin.database_security_manager')
    def test_run_security_scan(self, mock_security_manager):
        """Test running a security scan."""
        self.client.login(username='admin', password='testpass123')
        
        # Mock the security manager
        mock_security_manager.log_audit_event = MagicMock()
        
        response = self.client.post('/security-admin/run-security-scan/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))
        self.assertIn('results', data)
    
    @patch('core.admin.security_admin.database_security_manager')
    def test_test_database_security(self, mock_security_manager):
        """Test database security configuration test."""
        self.client.login(username='admin', password='testpass123')
        
        # Mock the security manager
        mock_security_manager.setup_ssl_encryption = MagicMock(return_value=True)
        mock_security_manager.log_audit_event = MagicMock()
        
        response = self.client.post('/security-admin/test-database-security/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))
        self.assertIn('results', data)
    
    def test_audit_log_detail_view(self):
        """Test audit log detail view."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/security-admin/audit-log-detail/1/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Audit Log Detail')
    
    def tearDown(self):
        """Clean up test data."""
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS db_audit_log")
            cursor.execute("DROP TABLE IF EXISTS db_security_events")


class SecurityAdminPermissionsTestCase(TestCase):
    """Test case for security admin permissions."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user without admin permissions
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access security admin."""
        response = self.client.get('/security-admin/')
        self.assertIn(response.status_code, [302, 403])
    
    def test_insufficient_permissions_denied(self):
        """Test that users without proper permissions cannot access security admin."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get('/security-admin/')
        self.assertIn(response.status_code, [302, 403])
    
    def test_post_requests_require_authentication(self):
        """Test that POST requests require authentication."""
        response = self.client.post('/security-admin/run-security-scan/')
        self.assertIn(response.status_code, [302, 403])
        
        response = self.client.post('/security-admin/resolve-security-event/')
        self.assertIn(response.status_code, [302, 403])