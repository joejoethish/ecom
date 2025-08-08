"""
Management command to test the Supplier Management System
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta

from apps.admin_panel.models import AdminUser
from apps.admin_panel.supplier_models import (
    SupplierCategory, SupplierProfile, SupplierContact, SupplierDocument,
    PurchaseOrder, PurchaseOrderItem, SupplierPerformanceMetric,
    SupplierCommunication, SupplierContract, SupplierAudit,
    SupplierRiskAssessment, SupplierQualification, SupplierPayment
)


class Command(BaseCommand):
    help = 'Test the Supplier Management System functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test data after running tests',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing Supplier Management System'))
        self.stdout.write('=' * 60)
        
        test_results = []
        
        try:
            with transaction.atomic():
                # Test 1: Create admin user
                admin_user, created = AdminUser.objects.get_or_create(
                    username='supplier_test_admin',
                    defaults={
                        'email': 'supplier_admin@test.com',
                        'role': 'admin',
                        'is_admin_active': True
                    }
                )
                if created:
                    admin_user.set_password('testpass123')
                    admin_user.save()
                
                test_results.append(('Admin User Creation', True, f'Created/retrieved admin user: {admin_user.username}'))
                
                # Test 2: Create supplier category
                category = SupplierCategory.objects.create(
                    name='Test Electronics Category',
                    description='Electronic components and devices for testing'
                )
                test_results.append(('Supplier Category Creation', True, f'Created category: {category.name}'))
                
                # Test 3: Create supplier
                supplier = SupplierProfile.objects.create(
                    supplier_code='TEST-SUP-001',
                    name='Test Electronics Supplier Ltd',
                    supplier_type='manufacturer',
                    category=category,
                    primary_contact_name='John Doe',
                    primary_contact_email='john@testelectronics.com',
                    primary_contact_phone='+1234567890',
                    address_line1='123 Electronics Street',
                    city='Tech City',
                    state_province='Tech State',
                    postal_code='12345',
                    country='Tech Country',
                    status='active',
                    created_by=admin_user
                )
                test_results.append(('Supplier Creation', True, f'Created supplier: {supplier.name}'))
                
                # Test 4: Create supplier contact
                contact = SupplierContact.objects.create(
                    supplier=supplier,
                    contact_type='sales',
                    name='Jane Smith',
                    email='jane@testelectronics.com',
                    phone='+1234567891',
                    title='Sales Manager'
                )
                test_results.append(('Supplier Contact Creation', True, f'Created contact: {contact.name}'))
                
                # Test 5: Create purchase order
                po = PurchaseOrder.objects.create(
                    po_number='TEST-PO-001',
                    supplier=supplier,
                    order_date=date.today(),
                    required_date=date.today() + timedelta(days=30),
                    total_amount=Decimal('2500.00'),
                    payment_terms='Net 30',
                    created_by=admin_user
                )
                test_results.append(('Purchase Order Creation', True, f'Created PO: {po.po_number}'))
                
                # Test 6: Create purchase order item
                po_item = PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    line_number=1,
                    product_code='ELEC-001',
                    product_name='Electronic Component A',
                    quantity_ordered=Decimal('50.000'),
                    unit_price=Decimal('50.00'),
                    total_price=Decimal('2500.00')
                )
                test_results.append(('Purchase Order Item Creation', True, f'Created PO item: {po_item.product_name}'))
                
                # Test 7: Create performance metric
                metric = SupplierPerformanceMetric.objects.create(
                    supplier=supplier,
                    metric_type='delivery_time',
                    value=Decimal('95.5'),
                    target_value=Decimal('95.0'),
                    measured_by=admin_user
                )
                test_results.append(('Performance Metric Creation', True, f'Created metric: {metric.metric_type}'))
                
                # Test 8: Create supplier communication
                communication = SupplierCommunication.objects.create(
                    supplier=supplier,
                    communication_type='email',
                    direction='outbound',
                    subject='Welcome to Our Supplier Network',
                    content='Thank you for partnering with us.',
                    admin_user=admin_user
                )
                test_results.append(('Supplier Communication Creation', True, f'Created communication: {communication.subject}'))
                
                # Test 9: Create supplier contract
                contract = SupplierContract.objects.create(
                    supplier=supplier,
                    contract_type='supply_agreement',
                    contract_number='TEST-SC-001',
                    title='Master Supply Agreement',
                    start_date=date.today(),
                    end_date=date.today() + timedelta(days=365),
                    payment_terms='Net 30',
                    created_by=admin_user
                )
                test_results.append(('Supplier Contract Creation', True, f'Created contract: {contract.title}'))
                
                # Test 10: Create supplier audit
                audit = SupplierAudit.objects.create(
                    supplier=supplier,
                    audit_type='quality',
                    audit_number='TEST-SA-001',
                    title='Quality Audit 2025',
                    planned_date=date.today() + timedelta(days=30),
                    lead_auditor=admin_user
                )
                test_results.append(('Supplier Audit Creation', True, f'Created audit: {audit.title}'))
                
                # Test 11: Create risk assessment
                risk_assessment = SupplierRiskAssessment.objects.create(
                    supplier=supplier,
                    overall_risk_level='low',
                    overall_risk_score=Decimal('25.50'),
                    financial_risk_score=Decimal('20.00'),
                    operational_risk_score=Decimal('30.00'),
                    compliance_risk_score=Decimal('25.00'),
                    quality_risk_score=Decimal('20.00'),
                    delivery_risk_score=Decimal('30.00'),
                    assessed_by=admin_user
                )
                test_results.append(('Risk Assessment Creation', True, f'Created risk assessment with score: {risk_assessment.overall_risk_score}'))
                
                # Test 12: Create supplier qualification
                qualification = SupplierQualification.objects.create(
                    supplier=supplier,
                    qualification_type='initial',
                    qualification_number='TEST-SQ-001',
                    status='qualified',
                    overall_score=Decimal('85.50'),
                    assessor=admin_user
                )
                test_results.append(('Supplier Qualification Creation', True, f'Created qualification: {qualification.qualification_number}'))
                
                # Test 13: Create supplier payment
                payment = SupplierPayment.objects.create(
                    supplier=supplier,
                    payment_number='TEST-SP-001',
                    invoice_amount=Decimal('2500.00'),
                    net_amount=Decimal('2500.00'),
                    payment_terms='Net 30',
                    due_date=date.today() + timedelta(days=30)
                )
                test_results.append(('Supplier Payment Creation', True, f'Created payment: {payment.payment_number}'))
                
                # Test 14: Test relationships and properties
                assert supplier.contacts.count() == 1
                assert supplier.purchase_orders.count() == 1
                assert supplier.performance_metrics.count() == 1
                assert supplier.communications.count() == 1
                assert supplier.contracts.count() == 1
                assert supplier.audits.count() == 1
                assert supplier.risk_assessments.count() == 1
                assert supplier.qualifications.count() == 1
                assert supplier.payments.count() == 1
                
                test_results.append(('Model Relationships', True, 'All relationships working correctly'))
                
                # Test 15: Test model properties
                assert str(supplier) == f"{supplier.supplier_code} - {supplier.name}"
                assert supplier.total_orders == 1
                assert supplier.total_spent == Decimal('2500.00')
                assert po_item.quantity_pending == Decimal('50.000')
                
                test_results.append(('Model Properties', True, 'All properties working correctly'))
                
                # Test 16: Test model methods
                assert not contract.is_expiring_soon  # Contract expires in 365 days
                assert not payment.is_overdue  # Payment due in 30 days
                
                test_results.append(('Model Methods', True, 'All methods working correctly'))
                
                # Print results
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write(self.style.SUCCESS('📊 TEST RESULTS'))
                self.stdout.write('=' * 60)
                
                total_tests = len(test_results)
                passed_tests = sum(1 for result in test_results if result[1])
                
                for test_name, success, message in test_results:
                    status = self.style.SUCCESS('✓ PASS') if success else self.style.ERROR('✗ FAIL')
                    self.stdout.write(f"{status}: {test_name}")
                    if message:
                        self.stdout.write(f"   {message}")
                
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write(f"Total Tests: {total_tests}")
                self.stdout.write(self.style.SUCCESS(f"✓ Passed: {passed_tests}"))
                self.stdout.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
                
                if options['cleanup']:
                    # Clean up test data
                    SupplierCategory.objects.filter(name__startswith='Test').delete()
                    AdminUser.objects.filter(username='supplier_test_admin').delete()
                    self.stdout.write(self.style.WARNING('\n🧹 Test data cleaned up'))
                
                self.stdout.write(self.style.SUCCESS('\n🎉 Supplier Management System verification complete!'))
                
                if passed_tests == total_tests:
                    self.stdout.write(self.style.SUCCESS('✅ All tests passed! System is working correctly.'))
                else:
                    self.stdout.write(self.style.ERROR('❌ Some tests failed. Please check the implementation.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Test failed with error: {str(e)}'))
            import traceback
            traceback.print_exc()