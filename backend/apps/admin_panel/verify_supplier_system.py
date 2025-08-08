#!/usr/bin/env python
"""
Verification script for Supplier and Vendor Management System
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from apps.admin_panel.models import AdminUser, AdminPermission
from apps.admin_panel.supplier_models import (
    SupplierCategory, SupplierProfile, SupplierContact, SupplierDocument,
    PurchaseOrder, PurchaseOrderItem, SupplierPerformanceMetric,
    SupplierCommunication, SupplierContract, SupplierAudit,
    SupplierRiskAssessment, SupplierQualification, SupplierPayment
)
from apps.admin_panel.supplier_services import (
    SupplierOnboardingService, SupplierPerformanceService,
    SupplierRiskService, SupplierAnalyticsService
)


class SupplierSystemVerifier:
    """Verification class for supplier management system."""
    
    def __init__(self):
        self.test_results = []
        self.admin_user = None
        self.setup_test_data()
    
    def setup_test_data(self):
        """Set up test data for verification."""
        print("Setting up test data...")
        
        # Create admin user
        self.admin_user, created = AdminUser.objects.get_or_create(
            username='supplier_test_admin',
            defaults={
                'email': 'supplier_admin@test.com',
                'role': 'admin',
                'is_admin_active': True
            }
        )
        if created:
            self.admin_user.set_password('testpass123')
            self.admin_user.save()
        
        # Create permissions
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
            permission, created = AdminPermission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': name,
                    'module': module,
                    'action': action
                }
            )
            self.admin_user.permissions.add(permission)
        
        print("✓ Test data setup completed")
    
    def log_test(self, test_name, success, message=""):
        """Log test result."""
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    def test_supplier_models(self):
        """Test supplier model creation and relationships."""
        print("\n=== Testing Supplier Models ===")
        
        try:
            # Test supplier category creation
            category = SupplierCategory.objects.create(
                name='Test Electronics',
                description='Electronic components and devices'
            )
            self.log_test("Supplier Category Creation", True, f"Created category: {category.name}")
            
            # Test supplier creation
            supplier = Supplier.objects.create(
                supplier_code='TEST001',
                name='Test Supplier Ltd',
                supplier_type='manufacturer',
                category=category,
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
            self.log_test("Supplier Creation", True, f"Created supplier: {supplier.name}")
            
            # Test supplier contact creation
            contact = SupplierContact.objects.create(
                supplier=supplier,
                contact_type='sales',
                name='Jane Smith',
                email='jane@testsupplier.com',
                phone='+1234567891'
            )
            self.log_test("Supplier Contact Creation", True, f"Created contact: {contact.name}")
            
            # Test purchase order creation
            po = PurchaseOrder.objects.create(
                po_number='TEST-PO-001',
                supplier=supplier,
                order_date=date.today(),
                required_date=date.today() + timedelta(days=30),
                total_amount=Decimal('1500.00'),
                created_by=self.admin_user
            )
            self.log_test("Purchase Order Creation", True, f"Created PO: {po.po_number}")
            
            # Test purchase order item creation
            po_item = PurchaseOrderItem.objects.create(
                purchase_order=po,
                line_number=1,
                product_code='PROD001',
                product_name='Test Product',
                quantity_ordered=Decimal('10.000'),
                unit_price=Decimal('150.00'),
                total_price=Decimal('1500.00')
            )
            self.log_test("Purchase Order Item Creation", True, f"Created PO item: {po_item.product_name}")
            
            # Test supplier properties
            total_orders = supplier.total_orders
            total_spent = supplier.total_spent
            self.log_test("Supplier Properties", True, f"Total orders: {total_orders}, Total spent: ${total_spent}")
            
            # Test performance metric creation
            metric = SupplierPerformanceMetric.objects.create(
                supplier=supplier,
                metric_type='delivery_time',
                value=Decimal('95.5'),
                target_value=Decimal('95.0'),
                measured_by=self.admin_user
            )
            self.log_test("Performance Metric Creation", True, f"Created metric: {metric.metric_type}")
            
            # Test supplier communication creation
            communication = SupplierCommunication.objects.create(
                supplier=supplier,
                communication_type='email',
                direction='outbound',
                subject='Test Communication',
                content='This is a test communication',
                admin_user=self.admin_user
            )
            self.log_test("Supplier Communication Creation", True, f"Created communication: {communication.subject}")
            
            # Test supplier contract creation
            contract = SupplierContract.objects.create(
                supplier=supplier,
                contract_type='supply_agreement',
                contract_number='TEST-SC-001',
                title='Test Supply Agreement',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=365),
                payment_terms='Net 30',
                created_by=self.admin_user
            )
            self.log_test("Supplier Contract Creation", True, f"Created contract: {contract.title}")
            
            # Test supplier audit creation
            audit = SupplierAudit.objects.create(
                supplier=supplier,
                audit_type='quality',
                audit_number='TEST-SA-001',
                title='Test Quality Audit',
                planned_date=date.today() + timedelta(days=30),
                lead_auditor=self.admin_user
            )
            self.log_test("Supplier Audit Creation", True, f"Created audit: {audit.title}")
            
            # Test supplier risk assessment creation
            risk_assessment = SupplierRiskAssessment.objects.create(
                supplier=supplier,
                overall_risk_level='low',
                overall_risk_score=Decimal('25.50'),
                financial_risk_score=Decimal('20.00'),
                operational_risk_score=Decimal('30.00'),
                compliance_risk_score=Decimal('25.00'),
                quality_risk_score=Decimal('20.00'),
                delivery_risk_score=Decimal('30.00'),
                assessed_by=self.admin_user
            )
            self.log_test("Risk Assessment Creation", True, f"Created risk assessment with score: {risk_assessment.overall_risk_score}")
            
            # Test supplier qualification creation
            qualification = SupplierQualification.objects.create(
                supplier=supplier,
                qualification_type='initial',
                qualification_number='TEST-SQ-001',
                status='qualified',
                overall_score=Decimal('85.50'),
                assessor=self.admin_user
            )
            self.log_test("Supplier Qualification Creation", True, f"Created qualification: {qualification.qualification_number}")
            
            # Test supplier payment creation
            payment = SupplierPayment.objects.create(
                supplier=supplier,
                payment_number='TEST-SP-001',
                invoice_amount=Decimal('1500.00'),
                net_amount=Decimal('1500.00'),
                payment_terms='Net 30',
                due_date=date.today() + timedelta(days=30)
            )
            self.log_test("Supplier Payment Creation", True, f"Created payment: {payment.payment_number}")
            
        except Exception as e:
            self.log_test("Supplier Models", False, f"Error: {str(e)}")
    
    def test_supplier_services(self):
        """Test supplier service functions."""
        print("\n=== Testing Supplier Services ===")
        
        try:
            # Test supplier onboarding service
            supplier_data = {
                'supplier_code': 'ONBOARD001',
                'name': 'Onboarding Test Supplier',
                'supplier_type': 'distributor',
                'primary_contact_name': 'Alice Johnson',
                'primary_contact_email': 'alice@onboardtest.com',
                'primary_contact_phone': '+1234567892',
                'address_line1': '456 Onboard Street',
                'city': 'Onboard City',
                'state_province': 'Onboard State',
                'postal_code': '54321',
                'country': 'Onboard Country'
            }
            
            supplier = SupplierOnboardingService.initiate_onboarding(supplier_data, self.admin_user)
            self.log_test("Supplier Onboarding Initiation", True, f"Initiated onboarding for: {supplier.name}")
            
            # Test required documents
            required_docs = SupplierOnboardingService.get_required_documents('manufacturer')
            self.log_test("Required Documents Retrieval", len(required_docs) > 0, f"Found {len(required_docs)} required documents")
            
            # Test onboarding completion check
            completion_status = SupplierOnboardingService.check_onboarding_completion(supplier)
            self.log_test("Onboarding Completion Check", True, f"Completion: {completion_status['completion_percentage']}%")
            
            # Test performance service
            test_supplier = Supplier.objects.filter(supplier_code='TEST001').first()
            if test_supplier:
                # Create test purchase orders for performance calculation
                po1 = PurchaseOrder.objects.create(
                    po_number='PERF-PO-001',
                    supplier=test_supplier,
                    status='completed',
                    order_date=date.today() - timedelta(days=60),
                    required_date=date.today() - timedelta(days=30),
                    delivered_date=date.today() - timedelta(days=28),
                    total_amount=Decimal('1000.00'),
                    created_by=self.admin_user
                )
                
                po2 = PurchaseOrder.objects.create(
                    po_number='PERF-PO-002',
                    supplier=test_supplier,
                    status='completed',
                    order_date=date.today() - timedelta(days=40),
                    required_date=date.today() - timedelta(days=10),
                    delivered_date=date.today() - timedelta(days=15),
                    total_amount=Decimal('2000.00'),
                    created_by=self.admin_user
                )
                
                # Test delivery performance calculation
                delivery_perf = SupplierPerformanceService.calculate_delivery_performance(test_supplier)
                self.log_test("Delivery Performance Calculation", True, 
                            f"On-time rate: {delivery_perf['on_time_percentage']:.1f}%")
                
                # Test performance rating update
                SupplierPerformanceService.update_performance_ratings(test_supplier)
                test_supplier.refresh_from_db()
                self.log_test("Performance Rating Update", test_supplier.overall_rating > 0, 
                            f"Updated rating: {test_supplier.overall_rating}")
                
                # Test performance report generation
                perf_report = SupplierPerformanceService.generate_performance_report(test_supplier)
                self.log_test("Performance Report Generation", 'delivery_performance' in perf_report, 
                            f"Generated report with {len(perf_report)} sections")
            
            # Test risk service
            if test_supplier:
                risk_data = SupplierRiskService.calculate_risk_score(test_supplier)
                self.log_test("Risk Score Calculation", 'overall_score' in risk_data, 
                            f"Risk score: {risk_data['overall_score']:.2f}")
            
            # Test analytics service
            dashboard_data = SupplierAnalyticsService.generate_supplier_dashboard_data()
            self.log_test("Dashboard Data Generation", 'key_metrics' in dashboard_data, 
                        f"Generated dashboard with {dashboard_data['key_metrics']['total_suppliers']} suppliers")
            
            # Test performance trends
            trends = SupplierAnalyticsService.generate_performance_trends(period_months=6)
            self.log_test("Performance Trends Generation", 'monthly_trends' in trends, 
                        f"Generated {len(trends['monthly_trends'])} months of trend data")
            
            # Test data export
            csv_data = SupplierAnalyticsService.export_supplier_data(format='csv')
            lines_count = len(csv_data.split('\n'))
            self.log_test("Data Export", len(csv_data) > 0, f"Exported {lines_count} lines of CSV data")
            
        except Exception as e:
            self.log_test("Supplier Services", False, f"Error: {str(e)}")
    
    def test_supplier_business_logic(self):
        """Test supplier business logic and workflows."""
        print("\n=== Testing Supplier Business Logic ===")
        
        try:
            # Get test supplier
            test_supplier = Supplier.objects.filter(supplier_code='TEST001').first()
            if not test_supplier:
                self.log_test("Business Logic Tests", False, "Test supplier not found")
                return
            
            # Test purchase order workflow
            po = PurchaseOrder.objects.create(
                po_number='WORKFLOW-PO-001',
                supplier=test_supplier,
                status='draft',
                order_date=date.today(),
                required_date=date.today() + timedelta(days=30),
                total_amount=Decimal('2500.00'),
                created_by=self.admin_user
            )
            
            # Test status transitions
            po.status = 'pending_approval'
            po.save()
            self.log_test("PO Status Transition to Pending", po.status == 'pending_approval', 
                        f"Status: {po.status}")
            
            po.status = 'approved'
            po.approved_by = self.admin_user
            po.approved_at = timezone.now()
            po.save()
            self.log_test("PO Approval", po.status == 'approved' and po.approved_by is not None, 
                        f"Approved by: {po.approved_by.username}")
            
            # Test contract expiry logic
            contract = SupplierContract.objects.create(
                supplier=test_supplier,
                contract_type='service_agreement',
                contract_number='EXPIRY-TEST-001',
                title='Expiry Test Contract',
                start_date=date.today() - timedelta(days=300),
                end_date=date.today() + timedelta(days=15),
                payment_terms='Net 30',
                status='active',
                created_by=self.admin_user
            )
            
            self.log_test("Contract Expiry Detection", contract.is_expiring_soon, 
                        f"Days until expiry: {contract.days_until_expiry}")
            
            # Test payment overdue logic
            payment = SupplierPayment.objects.create(
                supplier=test_supplier,
                payment_number='OVERDUE-TEST-001',
                invoice_amount=Decimal('1000.00'),
                net_amount=Decimal('1000.00'),
                payment_terms='Net 30',
                due_date=date.today() - timedelta(days=5),
                status='pending'
            )
            
            self.log_test("Payment Overdue Detection", payment.is_overdue, 
                        f"Days overdue: {payment.days_overdue}")
            
            # Test supplier rating calculations
            test_supplier.quality_rating = Decimal('4.5')
            test_supplier.delivery_rating = Decimal('4.2')
            test_supplier.service_rating = Decimal('4.8')
            test_supplier.overall_rating = (test_supplier.quality_rating + 
                                          test_supplier.delivery_rating + 
                                          test_supplier.service_rating) / 3
            test_supplier.save()
            
            self.log_test("Supplier Rating Calculation", test_supplier.overall_rating > 4.0, 
                        f"Overall rating: {test_supplier.overall_rating}")
            
            # Test qualification expiry
            qualification = SupplierQualification.objects.create(
                supplier=test_supplier,
                qualification_type='certification',
                qualification_number='QUAL-EXPIRY-001',
                status='qualified',
                expiry_date=date.today() - timedelta(days=1),
                assessor=self.admin_user
            )
            
            self.log_test("Qualification Expiry Detection", qualification.is_expired, 
                        "Qualification correctly detected as expired")
            
        except Exception as e:
            self.log_test("Supplier Business Logic", False, f"Error: {str(e)}")
    
    def test_supplier_data_integrity(self):
        """Test data integrity and constraints."""
        print("\n=== Testing Data Integrity ===")
        
        try:
            # Test unique constraints
            test_supplier = Supplier.objects.filter(supplier_code='TEST001').first()
            if test_supplier:
                # Test unique supplier code constraint
                try:
                    duplicate_supplier = Supplier(
                        supplier_code='TEST001',  # Duplicate code
                        name='Duplicate Supplier',
                        supplier_type='manufacturer',
                        primary_contact_name='Test User',
                        primary_contact_email='test@duplicate.com',
                        primary_contact_phone='+1234567890',
                        address_line1='123 Test Street',
                        city='Test City',
                        state_province='Test State',
                        postal_code='12345',
                        country='Test Country',
                        created_by=self.admin_user
                    )
                    duplicate_supplier.save()
                    self.log_test("Unique Supplier Code Constraint", False, "Duplicate supplier code was allowed")
                except Exception:
                    self.log_test("Unique Supplier Code Constraint", True, "Duplicate supplier code correctly rejected")
                
                # Test unique PO number constraint
                try:
                    duplicate_po = PurchaseOrder(
                        po_number='TEST-PO-001',  # Duplicate PO number
                        supplier=test_supplier,
                        order_date=date.today(),
                        required_date=date.today() + timedelta(days=30),
                        total_amount=Decimal('1000.00'),
                        created_by=self.admin_user
                    )
                    duplicate_po.save()
                    self.log_test("Unique PO Number Constraint", False, "Duplicate PO number was allowed")
                except Exception:
                    self.log_test("Unique PO Number Constraint", True, "Duplicate PO number correctly rejected")
                
                # Test foreign key constraints
                po_count_before = PurchaseOrder.objects.filter(supplier=test_supplier).count()
                
                # Test cascade delete protection (should not delete supplier with POs)
                try:
                    test_supplier.delete()
                    self.log_test("Cascade Delete Protection", False, "Supplier with POs was deleted")
                except Exception:
                    self.log_test("Cascade Delete Protection", True, "Supplier with POs correctly protected from deletion")
                
                # Test data validation
                invalid_supplier = Supplier(
                    supplier_code='INVALID',
                    name='Invalid Supplier',
                    supplier_type='invalid_type',  # Invalid choice
                    primary_contact_name='Test User',
                    primary_contact_email='invalid-email',  # Invalid email
                    primary_contact_phone='invalid-phone',  # Invalid phone
                    address_line1='123 Test Street',
                    city='Test City',
                    state_province='Test State',
                    postal_code='12345',
                    country='Test Country',
                    created_by=self.admin_user
                )
                
                try:
                    invalid_supplier.full_clean()
                    self.log_test("Data Validation", False, "Invalid data passed validation")
                except Exception:
                    self.log_test("Data Validation", True, "Invalid data correctly rejected by validation")
            
        except Exception as e:
            self.log_test("Data Integrity", False, f"Error: {str(e)}")
    
    def test_supplier_performance_optimization(self):
        """Test performance optimization features."""
        print("\n=== Testing Performance Optimization ===")
        
        try:
            # Test database indexes by checking query performance
            import time
            
            # Create multiple suppliers for testing
            suppliers = []
            for i in range(100):
                supplier = Supplier.objects.create(
                    supplier_code=f'PERF{i:03d}',
                    name=f'Performance Test Supplier {i}',
                    supplier_type='manufacturer',
                    primary_contact_name=f'Contact {i}',
                    primary_contact_email=f'contact{i}@perftest.com',
                    primary_contact_phone=f'+123456{i:04d}',
                    address_line1=f'{i} Performance Street',
                    city='Performance City',
                    state_province='Performance State',
                    postal_code=f'{i:05d}',
                    country='Performance Country',
                    status='active',
                    created_by=self.admin_user
                )
                suppliers.append(supplier)
            
            # Test indexed queries
            start_time = time.time()
            results = Supplier.objects.filter(status='active').count()
            query_time = time.time() - start_time
            
            self.log_test("Indexed Query Performance", query_time < 1.0, 
                        f"Query took {query_time:.3f}s for {results} records")
            
            # Test bulk operations
            start_time = time.time()
            Supplier.objects.filter(supplier_code__startswith='PERF').update(
                risk_level='low',
                last_modified_by=self.admin_user
            )
            bulk_time = time.time() - start_time
            
            self.log_test("Bulk Update Performance", bulk_time < 1.0, 
                        f"Bulk update took {bulk_time:.3f}s")
            
            # Test aggregation queries
            start_time = time.time()
            stats = Supplier.objects.aggregate(
                total_suppliers=Count('id'),
                avg_rating=Avg('overall_rating')
            )
            agg_time = time.time() - start_time
            
            self.log_test("Aggregation Query Performance", agg_time < 1.0, 
                        f"Aggregation took {agg_time:.3f}s")
            
            # Clean up test data
            Supplier.objects.filter(supplier_code__startswith='PERF').delete()
            
        except Exception as e:
            self.log_test("Performance Optimization", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all verification tests."""
        print("🚀 Starting Supplier Management System Verification")
        print("=" * 60)
        
        with transaction.atomic():
            self.test_supplier_models()
            self.test_supplier_services()
            self.test_supplier_business_logic()
            self.test_supplier_data_integrity()
            self.test_supplier_performance_optimization()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✓ Passed: {passed_tests}")
        print(f"✗ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n🎉 Supplier Management System Verification Complete!")
        
        return failed_tests == 0


def main():
    """Main function to run verification."""
    verifier = SupplierSystemVerifier()
    success = verifier.run_all_tests()
    
    if success:
        print("\n✅ All tests passed! Supplier Management System is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)


if __name__ == '__main__':
    main()