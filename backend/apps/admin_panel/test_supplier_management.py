"""
Comprehensive tests for Supplier and Vendor Management System
"""
import json
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import AdminUser, AdminPermission
from .supplier_models import (
    SupplierCategory, SupplierProfile, SupplierContact, SupplierDocument,
    PurchaseOrder, PurchaseOrderItem, SupplierPerformanceMetric,
    SupplierCommunication, SupplierContract, SupplierAudit,
    SupplierRiskAssessment, SupplierQualification, SupplierPayment
)
from .supplier_services import (
    SupplierOnboardingService, SupplierPerformanceService,
    SupplierRiskService, SupplierAnalyticsService
)


class SupplierModelTests(TestCase):
    """Test cases for supplier models."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.category = SupplierCategory.objects.create(
            name='Electronics',
            description='Electronic components and devices'
        )
        
        self.supplier = SupplierProfile.objects.create(
            supplier_code='SUP001',
            name='Test Supplier Ltd',
            supplier_type='manufacturer',
            category=self.category,
            primary_contact_name='John Doe',
            primary_contact_email='john@testsupplier.com',
            primary_contact_phone='+1234567890',
            address_line1='123 Test Street',
            city='Test City',
            state_province='Test State',
            postal_code='12345',
            country='Test Country',
            status='active',
            created_by=self.admin_user
        )
    
    def test_supplier_creation(self):
        """Test supplier model creation."""
        self.assertEqual(self.supplier.name, 'Test Supplier Ltd')
        self.assertEqual(self.supplier.supplier_code, 'SUP001')
        self.assertEqual(self.supplier.status, 'active')
        self.assertEqual(self.supplier.category, self.category)
        self.assertEqual(self.supplier.created_by, self.admin_user)
    
    def test_supplier_str_representation(self):
        """Test supplier string representation."""
        expected = f"{self.supplier.supplier_code} - {self.supplier.name}"
        self.assertEqual(str(self.supplier), expected)
    
    def test_supplier_total_orders_property(self):
        """Test supplier total_orders property."""
        # Create purchase orders
        po1 = PurchaseOrder.objects.create(
            po_number='PO001',
            supplier=self.supplier,
            order_date=date.today(),
            required_date=date.today() + timedelta(days=30),
            total_amount=Decimal('1000.00'),
            created_by=self.admin_user
        )
        po2 = PurchaseOrder.objects.create(
            po_number='PO002',
            supplier=self.supplier,
            order_date=date.today(),
            required_date=date.today() + timedelta(days=30),
            total_amount=Decimal('2000.00'),
            created_by=self.admin_user
        )
        
        self.assertEqual(self.supplier.total_orders, 2)
    
    def test_supplier_total_spent_property(self):
        """Test supplier total_spent property."""
        po1 = PurchaseOrder.objects.create(
            po_number='PO001',
            supplier=self.supplier,
            order_date=date.today(),
            required_date=date.today() + timedelta(days=30),
            total_amount=Decimal('1000.00'),
            created_by=self.admin_user
        )
        po2 = PurchaseOrder.objects.create(
            po_number='PO002',
            supplier=self.supplier,
            order_date=date.today(),
            required_date=date.today() + timedelta(days=30),
            total_amount=Decimal('2000.00'),
            created_by=self.admin_user
        )
        
        self.assertEqual(self.supplier.total_spent, Decimal('3000.00'))
    
    def test_supplier_contact_creation(self):
        """Test supplier contact creation."""
        contact = SupplierContact.objects.create(
            supplier=self.supplier,
            contact_type='sales',
            name='Jane Smith',
            email='jane@testsupplier.com',
            phone='+1234567891'
        )
        
        self.assertEqual(contact.supplier, self.supplier)
        self.assertEqual(contact.name, 'Jane Smith')
        self.assertEqual(contact.contact_type, 'sales')
    
    def test_purchase_order_creation(self):
        """Test purchase order creation."""
        po = PurchaseOrder.objects.create(
            po_number='PO001',
            supplier=self.supplier,
            order_date=date.today(),
            required_date=date.today() + timedelta(days=30),
            total_amount=Decimal('1000.00'),
            created_by=self.admin_user
        )
        
        self.assertEqual(po.supplier, self.supplier)
        self.assertEqual(po.po_number, 'PO001')
        self.assertEqual(po.status, 'draft')
        self.assertEqual(po.total_amount, Decimal('1000.00'))
    
    def test_purchase_order_item_quantity_pending(self):
        """Test purchase order item quantity_pending property."""
        po = PurchaseOrder.objects.create(
            po_number='PO001',
            supplier=self.supplier,
            order_date=date.today(),
            required_date=date.today() + timedelta(days=30),
            total_amount=Decimal('1000.00'),
            created_by=self.admin_user
        )
        
        item = PurchaseOrderItem.objects.create(
            purchase_order=po,
            line_number=1,
            product_code='PROD001',
            product_name='Test Product',
            quantity_ordered=Decimal('10.000'),
            quantity_received=Decimal('3.000'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('1000.00')
        )
        
        self.assertEqual(item.quantity_pending, Decimal('7.000'))
    
    def test_supplier_contract_expiry_properties(self):
        """Test supplier contract expiry properties."""
        contract = SupplierContract.objects.create(
            supplier=self.supplier,
            contract_type='supply_agreement',
            contract_number='SC001',
            title='Test Contract',
            start_date=date.today() - timedelta(days=365),
            end_date=date.today() + timedelta(days=15),
            payment_terms='Net 30',
            created_by=self.admin_user
        )
        
        self.assertTrue(contract.is_expiring_soon)
        self.assertEqual(contract.days_until_expiry, 15)
    
    def test_supplier_payment_overdue_properties(self):
        """Test supplier payment overdue properties."""
        payment = SupplierPayment.objects.create(
            supplier=self.supplier,
            payment_number='SP001',
            invoice_amount=Decimal('1000.00'),
            net_amount=Decimal('1000.00'),
            payment_terms='Net 30',
            due_date=date.today() - timedelta(days=5)
        )
        
        self.assertTrue(payment.is_overdue)
        self.assertEqual(payment.days_overdue, 5)
        self.assertEqual(payment.outstanding_amount, Decimal('1000.00'))


class SupplierAPITests(APITestCase):
    """Test cases for supplier API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        # Create permissions
        self.view_permission = AdminPermission.objects.create(
            codename='suppliers.view',
            name='View Suppliers',
            module='suppliers',
            action='view'
        )
        self.edit_permission = AdminPermission.objects.create(
            codename='suppliers.edit',
            name='Edit Suppliers',
            module='suppliers',
            action='edit'
        )
        
        self.admin_user.permissions.add(self.view_permission, self.edit_permission)
        
        self.category = SupplierCategory.objects.create(
            name='Electronics',
            description='Electronic components'
        )
        
        self.supplier = Supplier.objects.create(
            supplier_code='SUP001',
            name='Test Supplier Ltd',
            supplier_type='manufacturer',
            category=self.category,
            primary_contact_name='John Doe',
            primary_contact_email='john@testsupplier.com',
            primary_contact_phone='+1234567890',
            address_line1='123 Test Street',
            city='Test City',
            state_province='Test State',
            postal_code='12345',
            country='Test Country',
            status='active',
            created_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_supplier_list_api(self):
        """Test supplier list API endpoint."""
        url = reverse('admin_panel:admin-suppliers-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Supplier Ltd')
    
    def test_supplier_detail_api(self):
        """Test supplier detail API endpoint."""
        url = reverse('admin_panel:admin-suppliers-detail', kwargs={'pk': self.supplier.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Supplier Ltd')
        self.assertEqual(response.data['supplier_code'], 'SUP001')
    
    def test_supplier_create_api(self):
        """Test supplier creation API endpoint."""
        url = reverse('admin_panel:admin-suppliers-list')
        data = {
            'supplier_code': 'SUP002',
            'name': 'New Supplier Ltd',
            'supplier_type': 'distributor',
            'category': self.category.id,
            'primary_contact_name': 'Jane Smith',
            'primary_contact_email': 'jane@newsupplier.com',
            'primary_contact_phone': '+1234567891',
            'address_line1': '456 New Street',
            'city': 'New City',
            'state_province': 'New State',
            'postal_code': '54321',
            'country': 'New Country',
            'status': 'pending'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Supplier Ltd')
        self.assertEqual(response.data['supplier_code'], 'SUP002')
        
        # Verify supplier was created in database
        supplier = Supplier.objects.get(supplier_code='SUP002')
        self.assertEqual(supplier.name, 'New Supplier Ltd')
        self.assertEqual(supplier.created_by, self.admin_user)
    
    def test_supplier_update_api(self):
        """Test supplier update API endpoint."""
        url = reverse('admin_panel:admin-suppliers-detail', kwargs={'pk': self.supplier.id})
        data = {
            'name': 'Updated Supplier Ltd',
            'status': 'inactive'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Supplier Ltd')
        self.assertEqual(response.data['status'], 'inactive')
        
        # Verify supplier was updated in database
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.name, 'Updated Supplier Ltd')
        self.assertEqual(self.supplier.last_modified_by, self.admin_user)
    
    def test_supplier_analytics_api(self):
        """Test supplier analytics API endpoint."""
        url = reverse('admin_panel:admin-suppliers-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_suppliers', response.data)
        self.assertIn('active_suppliers', response.data)
        self.assertEqual(response.data['total_suppliers'], 1)
    
    def test_supplier_dashboard_api(self):
        """Test supplier dashboard API endpoint."""
        url = reverse('admin_panel:admin-suppliers-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('key_metrics', response.data)
        self.assertIn('alerts', response.data)
        self.assertEqual(response.data['key_metrics']['total_suppliers'], 1)
    
    def test_supplier_change_status_api(self):
        """Test supplier change status API endpoint."""
        url = reverse('admin_panel:admin-suppliers-change-status', kwargs={'pk': self.supplier.id})
        data = {
            'status': 'suspended',
            'reason': 'Quality issues'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'suspended')
        
        # Verify status change was logged
        communication = SupplierCommunication.objects.filter(
            supplier=self.supplier,
            subject__contains='Status changed'
        ).first()
        self.assertIsNotNone(communication)
    
    def test_purchase_order_create_api(self):
        """Test purchase order creation API endpoint."""
        url = reverse('admin_panel:admin-purchase-orders-list')
        data = {
            'supplier': self.supplier.id,
            'required_date': (date.today() + timedelta(days=30)).isoformat(),
            'total_amount': '1500.00',
            'payment_terms': 'Net 30'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['supplier'], self.supplier.id)
        self.assertIn('PO-', response.data['po_number'])
    
    def test_purchase_order_approve_api(self):
        """Test purchase order approval API endpoint."""
        po = PurchaseOrder.objects.create(
            po_number='PO001',
            supplier=self.supplier,
            status='pending_approval',
            order_date=date.today(),
            required_date=date.today() + timedelta(days=30),
            total_amount=Decimal('1000.00'),
            created_by=self.admin_user
        )
        
        url = reverse('admin_panel:admin-purchase-orders-approve', kwargs={'pk': po.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        
        # Verify approval in database
        po.refresh_from_db()
        self.assertEqual(po.status, 'approved')
        self.assertEqual(po.approved_by, self.admin_user)
        self.assertIsNotNone(po.approved_at)


class SupplierServiceTests(TestCase):
    """Test cases for supplier services."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.category = SupplierCategory.objects.create(
            name='Electronics',
            description='Electronic components'
        )
        
        self.supplier = Supplier.objects.create(
            supplier_code='SUP001',
            name='Test Supplier Ltd',
            supplier_type='manufacturer',
            category=self.category,
            primary_contact_name='John Doe',
            primary_contact_email='john@testsupplier.com',
            primary_contact_phone='+1234567890',
            address_line1='123 Test Street',
            city='Test City',
            state_province='Test State',
            postal_code='12345',
            country='Test Country',
            status='active',
            created_by=self.admin_user
        )
    
    def test_supplier_onboarding_initiation(self):
        """Test supplier onboarding initiation."""
        supplier_data = {
            'supplier_code': 'SUP002',
            'name': 'New Supplier Ltd',
            'supplier_type': 'distributor',
            'category': self.category,
            'primary_contact_name': 'Jane Smith',
            'primary_contact_email': 'jane@newsupplier.com',
            'primary_contact_phone': '+1234567891',
            'address_line1': '456 New Street',
            'city': 'New City',
            'state_province': 'New State',
            'postal_code': '54321',
            'country': 'New Country'
        }
        
        supplier = SupplierOnboardingService.initiate_onboarding(
            supplier_data, self.admin_user
        )
        
        self.assertEqual(supplier.status, 'pending')
        self.assertEqual(supplier.created_by, self.admin_user)
        
        # Check if communication record was created
        communication = SupplierCommunication.objects.filter(
            supplier=supplier,
            subject='Welcome to Our Supplier Network'
        ).first()
        self.assertIsNotNone(communication)
        
        # Check if risk assessment was created
        risk_assessment = SupplierRiskAssessment.objects.filter(
            supplier=supplier
        ).first()
        self.assertIsNotNone(risk_assessment)
    
    def test_required_documents_by_type(self):
        """Test getting required documents by supplier type."""
        manufacturer_docs = SupplierOnboardingService.get_required_documents('manufacturer')
        distributor_docs = SupplierOnboardingService.get_required_documents('distributor')
        
        self.assertIn('business_license', manufacturer_docs)
        self.assertIn('quality_certificate', manufacturer_docs)
        self.assertIn('iso_certificate', manufacturer_docs)
        
        self.assertIn('business_license', distributor_docs)
        self.assertIn('distribution_agreement', distributor_docs)
    
    def test_onboarding_completion_check(self):
        """Test onboarding completion check."""
        # Create required documents
        SupplierDocument.objects.create(
            supplier=self.supplier,
            document_type='business_license',
            title='Business License',
            file='test_file.pdf',
            status='approved',
            uploaded_by=self.admin_user
        )
        
        # Create contacts
        SupplierContact.objects.create(
            supplier=self.supplier,
            contact_type='primary',
            name='John Doe',
            email='john@testsupplier.com'
        )
        SupplierContact.objects.create(
            supplier=self.supplier,
            contact_type='billing',
            name='Jane Doe',
            email='billing@testsupplier.com'
        )
        
        completion_status = SupplierOnboardingService.check_onboarding_completion(
            self.supplier
        )
        
        self.assertFalse(completion_status['is_complete'])  # Missing other required docs
        self.assertTrue(completion_status['has_primary_contact'])
        self.assertTrue(completion_status['has_billing_contact'])
    
    def test_delivery_performance_calculation(self):
        """Test delivery performance calculation."""
        # Create completed purchase orders
        po1 = PurchaseOrder.objects.create(
            po_number='PO001',
            supplier=self.supplier,
            status='completed',
            order_date=date.today() - timedelta(days=60),
            required_date=date.today() - timedelta(days=30),
            delivered_date=date.today() - timedelta(days=28),  # 2 days early
            total_amount=Decimal('1000.00'),
            created_by=self.admin_user
        )
        
        po2 = PurchaseOrder.objects.create(
            po_number='PO002',
            supplier=self.supplier,
            status='completed',
            order_date=date.today() - timedelta(days=40),
            required_date=date.today() - timedelta(days=10),
            delivered_date=date.today() - timedelta(days=5),  # 5 days late
            total_amount=Decimal('2000.00'),
            created_by=self.admin_user
        )
        
        performance = SupplierPerformanceService.calculate_delivery_performance(
            self.supplier, period_days=90
        )
        
        self.assertEqual(performance['total_orders'], 2)
        self.assertEqual(performance['on_time_deliveries'], 1)
        self.assertEqual(performance['on_time_percentage'], 50.0)
        self.assertEqual(performance['early_deliveries'], 1)
        self.assertEqual(performance['average_delay_days'], 5.0)
    
    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        # Set up supplier with some risk factors
        self.supplier.current_balance = Decimal('8000.00')
        self.supplier.credit_limit = Decimal('10000.00')  # 80% utilization
        self.supplier.quality_rating = Decimal('2.5')  # Below average
        self.supplier.delivery_rating = Decimal('3.0')
        self.supplier.save()
        
        risk_data = SupplierRiskService.calculate_risk_score(self.supplier)
        
        self.assertIn('overall_score', risk_data)
        self.assertIn('risk_level', risk_data)
        self.assertIn('risk_factors', risk_data)
        self.assertIn('mitigation_strategies', risk_data)
        
        # Risk score should be > 0 due to quality rating and credit utilization
        self.assertGreater(risk_data['overall_score'], 0)
    
    def test_supplier_analytics_dashboard_data(self):
        """Test supplier analytics dashboard data generation."""
        # Create additional test data
        Supplier.objects.create(
            supplier_code='SUP002',
            name='High Risk Supplier',
            supplier_type='distributor',
            risk_level='high',
            primary_contact_name='Jane Smith',
            primary_contact_email='jane@highrisk.com',
            primary_contact_phone='+1234567891',
            address_line1='789 Risk Street',
            city='Risk City',
            state_province='Risk State',
            postal_code='99999',
            country='Risk Country',
            status='active',
            created_by=self.admin_user
        )
        
        dashboard_data = SupplierAnalyticsService.generate_supplier_dashboard_data()
        
        self.assertIn('key_metrics', dashboard_data)
        self.assertIn('risk_distribution', dashboard_data)
        self.assertIn('recent_activities', dashboard_data)
        self.assertIn('alerts', dashboard_data)
        
        self.assertEqual(dashboard_data['key_metrics']['total_suppliers'], 2)
        self.assertEqual(dashboard_data['key_metrics']['active_suppliers'], 2)
        
        # Should have alert for high risk supplier
        high_risk_alert = next(
            (alert for alert in dashboard_data['alerts'] 
             if 'high/critical risk' in alert['message']), 
            None
        )
        self.assertIsNotNone(high_risk_alert)
    
    def test_supplier_data_export(self):
        """Test supplier data export functionality."""
        csv_data = SupplierAnalyticsService.export_supplier_data(
            supplier_ids=[self.supplier.id], 
            format='csv'
        )
        
        self.assertIn('Supplier Code', csv_data)
        self.assertIn('SUP001', csv_data)
        self.assertIn('Test Supplier Ltd', csv_data)
        
        # Test invalid format
        with self.assertRaises(ValueError):
            SupplierAnalyticsService.export_supplier_data(format='invalid')


class SupplierIntegrationTests(APITestCase):
    """Integration tests for supplier management system."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = AdminUser.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        # Create all necessary permissions
        permissions = [
            ('suppliers.view', 'View Suppliers', 'suppliers', 'view'),
            ('suppliers.create', 'Create Suppliers', 'suppliers', 'create'),
            ('suppliers.edit', 'Edit Suppliers', 'suppliers', 'edit'),
            ('suppliers.delete', 'Delete Suppliers', 'suppliers', 'delete'),
            ('suppliers.approve', 'Approve Suppliers', 'suppliers', 'approve'),
            ('purchase_orders.view', 'View Purchase Orders', 'purchase_orders', 'view'),
            ('purchase_orders.create', 'Create Purchase Orders', 'purchase_orders', 'create'),
            ('purchase_orders.edit', 'Edit Purchase Orders', 'purchase_orders', 'edit'),
            ('purchase_orders.approve', 'Approve Purchase Orders', 'purchase_orders', 'approve'),
        ]
        
        for codename, name, module, action in permissions:
            permission = AdminPermission.objects.create(
                codename=codename,
                name=name,
                module=module,
                action=action
            )
            self.admin_user.permissions.add(permission)
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_complete_supplier_workflow(self):
        """Test complete supplier management workflow."""
        # 1. Create supplier category
        category_url = reverse('admin_panel:admin-supplier-categories-list')
        category_data = {
            'name': 'Electronics',
            'description': 'Electronic components and devices'
        }
        category_response = self.client.post(category_url, category_data, format='json')
        self.assertEqual(category_response.status_code, status.HTTP_201_CREATED)
        category_id = category_response.data['id']
        
        # 2. Create supplier
        supplier_url = reverse('admin_panel:admin-suppliers-list')
        supplier_data = {
            'supplier_code': 'SUP001',
            'name': 'Test Electronics Ltd',
            'supplier_type': 'manufacturer',
            'category': category_id,
            'primary_contact_name': 'John Doe',
            'primary_contact_email': 'john@testelectronics.com',
            'primary_contact_phone': '+1234567890',
            'address_line1': '123 Electronics Street',
            'city': 'Tech City',
            'state_province': 'Tech State',
            'postal_code': '12345',
            'country': 'Tech Country',
            'status': 'pending'
        }
        supplier_response = self.client.post(supplier_url, supplier_data, format='json')
        self.assertEqual(supplier_response.status_code, status.HTTP_201_CREATED)
        supplier_id = supplier_response.data['id']
        
        # 3. Add supplier contact
        contact_url = reverse('admin_panel:admin-supplier-contacts-list')
        contact_data = {
            'supplier': supplier_id,
            'contact_type': 'sales',
            'name': 'Jane Smith',
            'email': 'jane@testelectronics.com',
            'phone': '+1234567891'
        }
        contact_response = self.client.post(contact_url, contact_data, format='json')
        self.assertEqual(contact_response.status_code, status.HTTP_201_CREATED)
        
        # 4. Change supplier status to active
        status_url = reverse('admin_panel:admin-suppliers-change-status', kwargs={'pk': supplier_id})
        status_data = {
            'status': 'active',
            'reason': 'Completed onboarding process'
        }
        status_response = self.client.post(status_url, status_data, format='json')
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(status_response.data['status'], 'active')
        
        # 5. Create purchase order
        po_url = reverse('admin_panel:admin-purchase-orders-list')
        po_data = {
            'supplier': supplier_id,
            'required_date': (date.today() + timedelta(days=30)).isoformat(),
            'total_amount': '2500.00',
            'payment_terms': 'Net 30',
            'status': 'pending_approval'
        }
        po_response = self.client.post(po_url, po_data, format='json')
        self.assertEqual(po_response.status_code, status.HTTP_201_CREATED)
        po_id = po_response.data['id']
        
        # 6. Approve purchase order
        approve_url = reverse('admin_panel:admin-purchase-orders-approve', kwargs={'pk': po_id})
        approve_response = self.client.post(approve_url)
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(approve_response.data['status'], 'approved')
        
        # 7. Send purchase order to supplier
        send_url = reverse('admin_panel:admin-purchase-orders-send-to-supplier', kwargs={'pk': po_id})
        send_response = self.client.post(send_url)
        self.assertEqual(send_response.status_code, status.HTTP_200_OK)
        self.assertEqual(send_response.data['status'], 'sent')
        
        # 8. Create performance metric
        metric_url = reverse('admin_panel:admin-supplier-performance-list')
        metric_data = {
            'supplier': supplier_id,
            'metric_type': 'delivery_time',
            'value': '95.5',
            'target_value': '95.0',
            'measurement_date': date.today().isoformat()
        }
        metric_response = self.client.post(metric_url, metric_data, format='json')
        self.assertEqual(metric_response.status_code, status.HTTP_201_CREATED)
        
        # 9. Create risk assessment
        risk_url = reverse('admin_panel:admin-supplier-risk-assessments-list')
        risk_data = {
            'supplier': supplier_id,
            'overall_risk_level': 'low',
            'overall_risk_score': '25.50',
            'financial_risk_score': '20.00',
            'operational_risk_score': '30.00',
            'compliance_risk_score': '25.00',
            'quality_risk_score': '20.00',
            'delivery_risk_score': '30.00'
        }
        risk_response = self.client.post(risk_url, risk_data, format='json')
        self.assertEqual(risk_response.status_code, status.HTTP_201_CREATED)
        
        # 10. Verify supplier analytics
        analytics_url = reverse('admin_panel:admin-suppliers-analytics')
        analytics_response = self.client.get(analytics_url)
        self.assertEqual(analytics_response.status_code, status.HTTP_200_OK)
        self.assertEqual(analytics_response.data['total_suppliers'], 1)
        self.assertEqual(analytics_response.data['active_suppliers'], 1)
        
        # 11. Verify dashboard data
        dashboard_url = reverse('admin_panel:admin-suppliers-dashboard')
        dashboard_response = self.client.get(dashboard_url)
        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertEqual(dashboard_response.data['key_metrics']['total_suppliers'], 1)
        self.assertEqual(dashboard_response.data['active_purchase_orders'], 1)
    
    def test_supplier_performance_tracking(self):
        """Test supplier performance tracking workflow."""
        # Create supplier
        supplier = Supplier.objects.create(
            supplier_code='SUP001',
            name='Performance Test Supplier',
            supplier_type='manufacturer',
            primary_contact_name='John Doe',
            primary_contact_email='john@perftest.com',
            primary_contact_phone='+1234567890',
            address_line1='123 Test Street',
            city='Test City',
            state_province='Test State',
            postal_code='12345',
            country='Test Country',
            status='active',
            created_by=self.admin_user
        )
        
        # Create multiple purchase orders with different delivery performance
        orders_data = [
            {
                'po_number': 'PO001',
                'required_date': date.today() - timedelta(days=30),
                'delivered_date': date.today() - timedelta(days=28),  # 2 days early
                'status': 'completed'
            },
            {
                'po_number': 'PO002',
                'required_date': date.today() - timedelta(days=20),
                'delivered_date': date.today() - timedelta(days=15),  # 5 days late
                'status': 'completed'
            },
            {
                'po_number': 'PO003',
                'required_date': date.today() - timedelta(days=10),
                'delivered_date': date.today() - timedelta(days=10),  # On time
                'status': 'completed'
            }
        ]
        
        for order_data in orders_data:
            PurchaseOrder.objects.create(
                po_number=order_data['po_number'],
                supplier=supplier,
                order_date=date.today() - timedelta(days=60),
                required_date=order_data['required_date'],
                delivered_date=order_data['delivered_date'],
                status=order_data['status'],
                total_amount=Decimal('1000.00'),
                created_by=self.admin_user
            )
        
        # Test performance calculation
        performance = SupplierPerformanceService.calculate_delivery_performance(supplier)
        
        self.assertEqual(performance['total_orders'], 3)
        self.assertEqual(performance['on_time_deliveries'], 2)  # Early + on time
        self.assertAlmostEqual(performance['on_time_percentage'], 66.67, places=1)
        self.assertEqual(performance['early_deliveries'], 1)
        
        # Update performance ratings
        SupplierPerformanceService.update_performance_ratings(supplier)
        
        # Verify ratings were updated
        supplier.refresh_from_db()
        self.assertGreater(supplier.delivery_rating, Decimal('0.00'))
        self.assertGreater(supplier.overall_rating, Decimal('0.00'))
        
        # Verify performance metrics were created
        metrics = SupplierPerformanceMetric.objects.filter(supplier=supplier)
        self.assertGreater(metrics.count(), 0)
    
    def test_supplier_contract_management(self):
        """Test supplier contract management workflow."""
        # Create supplier
        supplier = Supplier.objects.create(
            supplier_code='SUP001',
            name='Contract Test Supplier',
            supplier_type='manufacturer',
            primary_contact_name='John Doe',
            primary_contact_email='john@contracttest.com',
            primary_contact_phone='+1234567890',
            address_line1='123 Test Street',
            city='Test City',
            state_province='Test State',
            postal_code='12345',
            country='Test Country',
            status='active',
            created_by=self.admin_user
        )
        
        # Create contract
        contract_url = reverse('admin_panel:admin-supplier-contracts-list')
        contract_data = {
            'supplier': supplier.id,
            'contract_type': 'supply_agreement',
            'title': 'Master Supply Agreement',
            'description': 'Main supply contract for electronic components',
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=365)).isoformat(),
            'contract_value': '100000.00',
            'payment_terms': 'Net 30',
            'currency': 'USD'
        }
        
        contract_response = self.client.post(contract_url, contract_data, format='json')
        self.assertEqual(contract_response.status_code, status.HTTP_201_CREATED)
        contract_id = contract_response.data['id']
        
        # Approve contract
        approve_url = reverse('admin_panel:admin-supplier-contracts-approve', kwargs={'pk': contract_id})
        approve_response = self.client.post(approve_url)
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(approve_response.data['status'], 'approved')
        
        # Test expiring contracts endpoint
        # Create an expiring contract
        expiring_contract = SupplierContract.objects.create(
            supplier=supplier,
            contract_type='service_agreement',
            contract_number='SC-EXPIRE-001',
            title='Expiring Contract',
            start_date=date.today() - timedelta(days=300),
            end_date=date.today() + timedelta(days=15),  # Expires in 15 days
            payment_terms='Net 30',
            status='active',
            created_by=self.admin_user
        )
        
        expiring_url = reverse('admin_panel:admin-supplier-contracts-expiring')
        expiring_response = self.client.get(expiring_url)
        self.assertEqual(expiring_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(expiring_response.data), 1)
        self.assertEqual(expiring_response.data[0]['id'], expiring_contract.id)