#!/usr/bin/env python
"""
Simple test script for Supplier Management System
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.db import transaction
from apps.admin_panel.models import AdminUser
from apps.admin_panel.supplier_models import (
    SupplierCategory, SupplierProfile, SupplierContact, PurchaseOrder
)

def test_supplier_system():
    """Test basic supplier system functionality."""
    print("🚀 Testing Supplier Management System")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # Create admin user
            admin_user, created = AdminUser.objects.get_or_create(
                username='test_admin',
                defaults={
                    'email': 'admin@test.com',
                    'role': 'admin'
                }
            )
            print("✓ Admin user created/retrieved")
            
            # Create supplier category
            category = SupplierCategory.objects.create(
                name='Test Electronics',
                description='Electronic components for testing'
            )
            print("✓ Supplier category created")
            
            # Create supplier
            supplier = SupplierProfile.objects.create(
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
                created_by=admin_user
            )
            print("✓ Supplier created")
            
            # Create supplier contact
            contact = SupplierContact.objects.create(
                supplier=supplier,
                contact_type='sales',
                name='Jane Smith',
                email='jane@testsupplier.com',
                phone='+1234567891'
            )
            print("✓ Supplier contact created")
            
            # Create purchase order
            po = PurchaseOrder.objects.create(
                po_number='TEST-PO-001',
                supplier=supplier,
                order_date='2025-01-01',
                required_date='2025-02-01',
                total_amount=1500.00,
                created_by=admin_user
            )
            print("✓ Purchase order created")
            
            # Test relationships
            assert supplier.contacts.count() == 1
            assert supplier.purchase_orders.count() == 1
            assert supplier.total_orders == 1
            print("✓ Relationships working correctly")
            
            # Test properties
            assert str(supplier) == f"{supplier.supplier_code} - {supplier.name}"
            assert contact.supplier == supplier
            assert po.supplier == supplier
            print("✓ Model properties working correctly")
            
            print("\n🎉 All tests passed! Supplier Management System is working correctly.")
            return True
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_supplier_system()
    sys.exit(0 if success else 1)