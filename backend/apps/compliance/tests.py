from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta
import json

from .models import (
    ComplianceFramework, CompliancePolicy, ComplianceControl,
    ComplianceAssessment, ComplianceIncident, ComplianceTraining,
    ComplianceTrainingRecord, ComplianceAuditTrail, ComplianceRiskAssessment,
    ComplianceVendor, ComplianceReport
)
from .utils import ComplianceCalculator, ComplianceValidator

User = get_user_model()


class ComplianceModelTests(TestCase):
    """Test compliance models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.framework = ComplianceFramework.objects.create(
            name='Test Framework',
            framework_type='custom',
            description='Test framework description',
            version='1.0',
            effective_date=date.today(),
            status='active',
            created_by=self.user
        )
    
    def test_framework_creation(self):
        """Test compliance framework creation"""
        self.assertEqual(self.framework.name, 'Test Framework')
        self.assertEqual(self.framework.framework_type, 'custom')
        self.assertEqual(self.framework.status, 'active')
        self.assertEqual(str(self.framework), 'Test Framework (1.0)')
    
    def test_policy_creation(self):
        """Test compliance policy creation"""
        policy = CompliancePolicy.objects.create(
            framework=self.framework,
            title='Test Policy',
            policy_type='data_protection',
            description='Test policy description',
            content='Test policy content',
            version='1.0',
            effective_date=date.today(),
            review_date=date.today() + timedelta(days=365),
            owner=self.user
        )
        
        self.assertEqual(policy.title, 'Test Policy')
        self.assertEqual(policy.framework, self.framework)
        self.assertEqual(policy.owner, self.user)
        self.assertEqual(str(policy), 'Test Policy (v1.0)')
    
    def test_control_creation(self):
        """Test compliance control creation"""
        control = ComplianceControl.objects.create(
            framework=self.framework,
            control_id='TEST-001',
            title='Test Control',
            description='Test control description',
            control_type='preventive',
            implementation_status='implemented',
            risk_level=3,
            owner=self.user,
            frequency='monthly'
        )
        
        self.assertEqual(control.control_id, 'TEST-001')
        self.assertEqual(control.framework, self.framework)
        self.assertEqual(control.risk_level, 3)
        self.assertEqual(str(control), 'TEST-001: Test Control')
    
    def test_incident_creation(self):
        """Test compliance incident creation"""
        incident = ComplianceIncident.objects.create(
            incident_id='INC-001',
            framework=self.framework,
            title='Test Incident',
            incident_type='data_breach',
            description='Test incident description',
            severity='high',
            reported_by=self.user,
            occurred_at=timezone.now()
        )
        
        self.assertEqual(incident.incident_id, 'INC-001')
        self.assertEqual(incident.severity, 'high')
        self.assertEqual(incident.reported_by, self.user)
        self.assertEqual(str(incident), 'INC-001: Test Incident')
    
    def test_risk_assessment_creation(self):
        """Test risk assessment creation"""
        risk = ComplianceRiskAssessment.objects.create(
            framework=self.framework,
            title='Test Risk',
            description='Test risk description',
            risk_category='operational',
            likelihood='medium',
            impact='high',
            inherent_risk_score=12,
            residual_risk_score=8,
            risk_owner=self.user,
            review_date=date.today() + timedelta(days=90)
        )
        
        self.assertEqual(risk.title, 'Test Risk')
        self.assertEqual(risk.inherent_risk_score, 12)
        self.assertEqual(risk.residual_risk_score, 8)
        self.assertTrue(risk.residual_risk_score <= risk.inherent_risk_score)


class ComplianceAPITests(APITestCase):
    """Test compliance API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.framework = ComplianceFramework.objects.create(
            name='Test Framework',
            framework_type='custom',
            description='Test framework description',
            version='1.0',
            effective_date=date.today(),
            status='active',
            created_by=self.user
        )
    
    def test_framework_list_api(self):
        """Test framework list API"""
        url = reverse('compliance:framework-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Framework')
    
    def test_framework_create_api(self):
        """Test framework creation API"""
        url = reverse('compliance:framework-list')
        data = {
            'name': 'New Framework',
            'framework_type': 'gdpr',
            'description': 'New framework description',
            'version': '1.0',
            'effective_date': date.today().isoformat(),
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Framework')
        self.assertEqual(response.data['created_by']['id'], self.user.id)
    
    def test_policy_create_api(self):
        """Test policy creation API"""
        url = reverse('compliance:policy-list')
        data = {
            'framework_id': str(self.framework.id),
            'title': 'Test Policy',
            'policy_type': 'data_protection',
            'description': 'Test policy description',
            'content': 'Test policy content',
            'version': '1.0',
            'effective_date': date.today().isoformat(),
            'review_date': (date.today() + timedelta(days=365)).isoformat(),
            'owner_id': self.user.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Policy')
    
    def test_incident_create_api(self):
        """Test incident creation API"""
        url = reverse('compliance:incident-list')
        data = {
            'framework_id': str(self.framework.id),
            'title': 'Test Incident',
            'incident_type': 'data_breach',
            'description': 'Test incident description',
            'severity': 'high',
            'occurred_at': timezone.now().isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Incident')
        self.assertEqual(response.data['reported_by']['id'], self.user.id)
        self.assertTrue(response.data['incident_id'].startswith('INC-'))
    
    def test_dashboard_overview_api(self):
        """Test dashboard overview API"""
        url = reverse('compliance:dashboard-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_frameworks', response.data)
        self.assertIn('active_frameworks', response.data)
        self.assertEqual(response.data['total_frameworks'], 1)
        self.assertEqual(response.data['active_frameworks'], 1)


class ComplianceUtilsTests(TestCase):
    """Test compliance utility functions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.framework = ComplianceFramework.objects.create(
            name='Test Framework',
            framework_type='custom',
            description='Test framework description',
            version='1.0',
            effective_date=date.today(),
            status='active',
            created_by=self.user
        )
    
    def test_risk_score_calculation(self):
        """Test risk score calculation"""
        score = ComplianceCalculator.calculate_risk_score('high', 'major')
        self.assertEqual(score, 16)  # 4 * 4
        
        score = ComplianceCalculator.calculate_risk_score('low', 'minor')
        self.assertEqual(score, 4)  # 2 * 2
        
        score = ComplianceCalculator.calculate_risk_score('very_high', 'catastrophic')
        self.assertEqual(score, 25)  # 5 * 5
    
    def test_compliance_score_calculation(self):
        """Test compliance score calculation"""
        # Create some controls
        ComplianceControl.objects.create(
            framework=self.framework,
            control_id='TEST-001',
            title='Test Control 1',
            description='Test control description',
            control_type='preventive',
            implementation_status='implemented',
            risk_level=3,
            owner=self.user,
            frequency='monthly'
        )
        
        ComplianceControl.objects.create(
            framework=self.framework,
            control_id='TEST-002',
            title='Test Control 2',
            description='Test control description',
            control_type='detective',
            implementation_status='in_progress',
            risk_level=2,
            owner=self.user,
            frequency='quarterly'
        )
        
        score = ComplianceCalculator.calculate_compliance_score(self.framework)
        self.assertEqual(score, 50.0)  # 1 out of 2 controls implemented
    
    def test_policy_validation(self):
        """Test policy validation"""
        policy = CompliancePolicy(
            framework=self.framework,
            title='Test Policy',
            policy_type='data_protection',
            description='Test policy description',
            content='Test policy content',
            version='1.0',
            status='active',  # Active without approval
            effective_date=date.today(),
            review_date=date.today() - timedelta(days=1),  # Review date before effective date
            owner=self.user
        )
        
        errors = ComplianceValidator.validate_policy_approval_workflow(policy)
        
        self.assertIn("Policy cannot be active without approval", errors)
        self.assertIn("Review date must be after effective date", errors)
    
    def test_risk_validation(self):
        """Test risk assessment validation"""
        risk = ComplianceRiskAssessment(
            framework=self.framework,
            title='Test Risk',
            description='Test risk description',
            risk_category='operational',
            likelihood='medium',
            impact='high',
            inherent_risk_score=8,
            residual_risk_score=12,  # Higher than inherent
            status='mitigated',
            mitigation_strategies=[],  # Empty strategies
            risk_owner=self.user,
            review_date=date.today() + timedelta(days=90)
        )
        
        errors = ComplianceValidator.validate_risk_assessment(risk)
        
        self.assertIn("Residual risk score cannot be higher than inherent risk score", errors)
        self.assertIn("Mitigated risks must have mitigation strategies", errors)


class ComplianceWorkflowTests(TestCase):
    """Test compliance workflows"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123'
        )
        
        self.framework = ComplianceFramework.objects.create(
            name='Test Framework',
            framework_type='custom',
            description='Test framework description',
            version='1.0',
            effective_date=date.today(),
            status='active',
            created_by=self.user
        )
    
    def test_policy_approval_workflow(self):
        """Test policy approval workflow"""
        policy = CompliancePolicy.objects.create(
            framework=self.framework,
            title='Test Policy',
            policy_type='data_protection',
            description='Test policy description',
            content='Test policy content',
            version='1.0',
            status='draft',
            effective_date=date.today(),
            review_date=date.today() + timedelta(days=365),
            owner=self.user
        )
        
        # Test approval
        policy.status = 'approved'
        policy.approver = self.manager
        policy.approved_at = timezone.now()
        policy.save()
        
        self.assertEqual(policy.status, 'approved')
        self.assertEqual(policy.approver, self.manager)
        self.assertIsNotNone(policy.approved_at)
        
        # Test activation
        policy.status = 'active'
        policy.save()
        
        self.assertEqual(policy.status, 'active')
    
    def test_incident_lifecycle(self):
        """Test incident lifecycle"""
        incident = ComplianceIncident.objects.create(
            incident_id='INC-001',
            framework=self.framework,
            title='Test Incident',
            incident_type='data_breach',
            description='Test incident description',
            severity='high',
            status='reported',
            reported_by=self.user,
            occurred_at=timezone.now()
        )
        
        # Assign incident
        incident.assigned_to = self.manager
        incident.status = 'investigating'
        incident.save()
        
        self.assertEqual(incident.status, 'investigating')
        self.assertEqual(incident.assigned_to, self.manager)
        
        # Resolve incident
        incident.status = 'resolved'
        incident.resolved_at = timezone.now()
        incident.root_cause = 'Test root cause'
        incident.save()
        
        self.assertEqual(incident.status, 'resolved')
        self.assertIsNotNone(incident.resolved_at)
        self.assertEqual(incident.root_cause, 'Test root cause')
    
    def test_training_assignment_workflow(self):
        """Test training assignment workflow"""
        training = ComplianceTraining.objects.create(
            framework=self.framework,
            title='Test Training',
            training_type='general_awareness',
            description='Test training description',
            content='Test training content',
            duration_hours=2.0,
            status='active',
            mandatory=True,
            created_by=self.user
        )
        
        # Assign training
        record = ComplianceTrainingRecord.objects.create(
            training=training,
            user=self.manager,
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='not_started'
        )
        
        self.assertEqual(record.status, 'not_started')
        self.assertEqual(record.training, training)
        self.assertEqual(record.user, self.manager)
        
        # Complete training
        record.status = 'completed'
        record.completed_date = date.today()
        record.score = 85
        record.save()
        
        self.assertEqual(record.status, 'completed')
        self.assertEqual(record.score, 85)
        self.assertIsNotNone(record.completed_date)


class ComplianceIntegrationTests(APITestCase):
    """Test compliance system integration"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.framework = ComplianceFramework.objects.create(
            name='GDPR Framework',
            framework_type='gdpr',
            description='GDPR compliance framework',
            version='1.0',
            effective_date=date.today(),
            status='active',
            created_by=self.user
        )
    
    def test_end_to_end_compliance_workflow(self):
        """Test complete compliance workflow"""
        # 1. Create a policy
        policy_data = {
            'framework_id': str(self.framework.id),
            'title': 'Data Protection Policy',
            'policy_type': 'data_protection',
            'description': 'GDPR data protection policy',
            'content': 'Policy content here...',
            'version': '1.0',
            'effective_date': date.today().isoformat(),
            'review_date': (date.today() + timedelta(days=365)).isoformat(),
            'owner_id': self.user.id
        }
        
        policy_response = self.client.post(
            reverse('compliance:policy-list'),
            policy_data,
            format='json'
        )
        self.assertEqual(policy_response.status_code, status.HTTP_201_CREATED)
        policy_id = policy_response.data['id']
        
        # 2. Approve the policy
        approve_response = self.client.post(
            reverse('compliance:policy-approve', kwargs={'pk': policy_id})
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        
        # 3. Create a control for the policy
        control_data = {
            'framework_id': str(self.framework.id),
            'policy_id': policy_id,
            'control_id': 'GDPR-001',
            'title': 'Data Access Control',
            'description': 'Control for data access',
            'control_type': 'preventive',
            'implementation_status': 'implemented',
            'risk_level': 3,
            'owner_id': self.user.id,
            'frequency': 'monthly'
        }
        
        control_response = self.client.post(
            reverse('compliance:control-list'),
            control_data,
            format='json'
        )
        self.assertEqual(control_response.status_code, status.HTTP_201_CREATED)
        
        # 4. Create a risk assessment
        risk_data = {
            'framework_id': str(self.framework.id),
            'title': 'Data Breach Risk',
            'description': 'Risk of data breach',
            'risk_category': 'operational',
            'likelihood': 'medium',
            'impact': 'high',
            'inherent_risk_score': 12,
            'residual_risk_score': 6,
            'risk_owner_id': self.user.id,
            'review_date': (date.today() + timedelta(days=90)).isoformat(),
            'status': 'assessed'
        }
        
        risk_response = self.client.post(
            reverse('compliance:risk-assessment-list'),
            risk_data,
            format='json'
        )
        self.assertEqual(risk_response.status_code, status.HTTP_201_CREATED)
        
        # 5. Check dashboard reflects all changes
        dashboard_response = self.client.get(
            reverse('compliance:dashboard-overview')
        )
        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        
        dashboard_data = dashboard_response.data
        self.assertEqual(dashboard_data['total_frameworks'], 1)
        self.assertEqual(dashboard_data['total_policies'], 1)
        self.assertEqual(dashboard_data['total_controls'], 1)
        
        # 6. Generate a report
        report_data = {
            'title': 'GDPR Compliance Report',
            'report_type': 'dashboard',
            'framework_id': str(self.framework.id),
            'description': 'Monthly GDPR compliance report'
        }
        
        report_response = self.client.post(
            reverse('compliance:report-list'),
            report_data,
            format='json'
        )
        self.assertEqual(report_response.status_code, status.HTTP_201_CREATED)
        
        # This demonstrates a complete compliance workflow from policy creation
        # through risk assessment to reporting