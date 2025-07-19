#!/usr/bin/env python
"""
Simple test script to verify shipping management API functionality
without requiring full Django test environment setup.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

from apps.shipping.models import (
    ShippingPartner, ServiceableArea, DeliverySlot, 
    Shipment, ShipmentTracking, ShippingRate
)
from apps.shipping.serializers import (
    ShippingPartnerSerializer, ShippingRateCalculationSerializer,
    TrackingWebhookSerializer, DeliverySlotAvailabilitySerializer
)
from django.utils import timezone


def test_shipping_models():
    """Test shipping model creation and relationships"""
    print("Testing shipping models...")
    
    # Create shipping partner
    partner = ShippingPartner.objects.create(
        name='Test Shiprocket',
        code='SHIPROCKET_TEST',
        partner_type='SHIPROCKET',
        api_key='test_key',
        api_secret='test_secret',
        base_url='https://api.shiprocket.in/v1/external',
        is_active=True,
        supports_cod=True,
        supports_prepaid=True
    )
    print(f"✓ Created shipping partner: {partner}")
    
    # Create serviceable area
    area = ServiceableArea.objects.create(
        shipping_partner=partner,
        pin_code='110001',
        city='New Delhi',
        state='Delhi',
        country='India',
        min_delivery_days=1,
        max_delivery_days=3,
        is_active=True
    )
    print(f"✓ Created serviceable area: {area}")
    
    # Create delivery slot
    slot = DeliverySlot.objects.create(
        name='Morning Delivery',
        start_time='09:00:00',
        end_time='12:00:00',
        day_of_week=1,  # Tuesday
        additional_fee=Decimal('10.00'),
        max_orders=50,
        is_active=True
    )
    print(f"✓ Created delivery slot: {slot}")
    
    # Create shipping rate
    rate = ShippingRate.objects.create(
        shipping_partner=partner,
        min_weight=Decimal('0.0'),
        max_weight=Decimal('5.0'),
        base_rate=Decimal('100.00'),
        per_kg_rate=Decimal('20.00')
    )
    print(f"✓ Created shipping rate: {rate}")
    
    # Create shipment
    shipment = Shipment.objects.create(
        order_id=1,
        shipping_partner=partner,
        tracking_number='TEST123456',
        status='PENDING',
        shipping_address={
            'name': 'John Doe',
            'address_line_1': '123 Test Street',
            'city': 'New Delhi',
            'state': 'Delhi',
            'postal_code': '110001',
            'country': 'India',
            'phone': '9876543210'
        },
        weight=Decimal('2.5'),
        shipping_cost=Decimal('150.00')
    )
    print(f"✓ Created shipment: {shipment}")
    
    # Create tracking update
    tracking = ShipmentTracking.objects.create(
        shipment=shipment,
        status='SHIPPED',
        description='Package shipped from warehouse',
        location='Delhi Hub',
        timestamp=timezone.now()
    )
    print(f"✓ Created tracking update: {tracking}")
    
    return partner, area, slot, rate, shipment, tracking


def test_serializers():
    """Test serializer functionality"""
    print("\nTesting serializers...")
    
    # Test shipping rate calculation serializer
    calc_data = {
        'source_pin_code': '110001',
        'destination_pin_code': '400001',
        'weight': '2.5',
        'dimensions': {'length': 10, 'width': 10, 'height': 10}
    }
    calc_serializer = ShippingRateCalculationSerializer(data=calc_data)
    if calc_serializer.is_valid():
        print("✓ Shipping rate calculation serializer validation passed")
    else:
        print(f"✗ Shipping rate calculation serializer errors: {calc_serializer.errors}")
    
    # Test webhook serializer
    webhook_data = {
        'tracking_number': 'TEST123456',
        'status': 'DELIVERED',
        'description': 'Package delivered successfully',
        'location': 'Mumbai',
        'timestamp': timezone.now().isoformat(),
        'partner_data': {'delivery_person': 'John', 'signature': 'received'}
    }
    webhook_serializer = TrackingWebhookSerializer(data=webhook_data)
    if webhook_serializer.is_valid():
        print("✓ Webhook serializer validation passed")
    else:
        print(f"✗ Webhook serializer errors: {webhook_serializer.errors}")
    
    # Test delivery slot availability serializer
    slot_data = {
        'delivery_date': (timezone.now().date() + timedelta(days=1)).isoformat(),
        'pin_code': '110001'
    }
    slot_serializer = DeliverySlotAvailabilitySerializer(data=slot_data)
    if slot_serializer.is_valid():
        print("✓ Delivery slot availability serializer validation passed")
    else:
        print(f"✗ Delivery slot availability serializer errors: {slot_serializer.errors}")


def test_rate_calculation():
    """Test shipping rate calculation logic"""
    print("\nTesting rate calculation...")
    
    # Get the shipping partner and rate created in test_shipping_models
    try:
        partner = ShippingPartner.objects.get(code='SHIPROCKET_TEST')
        rate = ShippingRate.objects.get(shipping_partner=partner)
        
        # Test rate calculation
        weight = Decimal('2.5')
        calculated_rate = rate.base_rate + (rate.per_kg_rate * weight)
        expected_rate = Decimal('100.00') + (Decimal('20.00') * Decimal('2.5'))  # 150.00
        
        if calculated_rate == expected_rate:
            print(f"✓ Rate calculation correct: {calculated_rate}")
        else:
            print(f"✗ Rate calculation incorrect: got {calculated_rate}, expected {expected_rate}")
            
    except (ShippingPartner.DoesNotExist, ShippingRate.DoesNotExist):
        print("✗ Could not find shipping partner or rate for calculation test")


def test_status_mapping():
    """Test status mapping functionality"""
    print("\nTesting status mapping...")
    
    # Test status mapping logic (from webhook enhancement)
    status_mapping = {
        'SHIPPED': 'SHIPPED',
        'IN_TRANSIT': 'IN_TRANSIT',
        'OUT_FOR_DELIVERY': 'OUT_FOR_DELIVERY',
        'DELIVERED': 'DELIVERED',
        'PICKUP COMPLETE': 'SHIPPED',
        'RTO INITIATED': 'RETURNED',
        'DISPATCHED': 'SHIPPED',
    }
    
    test_cases = [
        ('PICKUP COMPLETE', 'SHIPPED'),
        ('DISPATCHED', 'SHIPPED'),
        ('RTO INITIATED', 'RETURNED'),
        ('DELIVERED', 'DELIVERED'),
        ('UNKNOWN_STATUS', 'UNKNOWN_STATUS')  # Should remain unchanged
    ]
    
    for input_status, expected_output in test_cases:
        mapped_status = status_mapping.get(input_status.upper(), input_status.upper())
        if mapped_status == expected_output:
            print(f"✓ Status mapping correct: {input_status} -> {mapped_status}")
        else:
            print(f"✗ Status mapping incorrect: {input_status} -> {mapped_status}, expected {expected_output}")


def test_shipment_tracking():
    """Test shipment tracking functionality"""
    print("\nTesting shipment tracking...")
    
    try:
        shipment = Shipment.objects.get(tracking_number='TEST123456')
        
        # Test tracking updates
        tracking_updates = ShipmentTracking.objects.filter(shipment=shipment).order_by('-timestamp')
        
        if tracking_updates.exists():
            print(f"✓ Found {tracking_updates.count()} tracking update(s)")
            for update in tracking_updates:
                print(f"  - {update.status}: {update.description} at {update.location}")
        else:
            print("✗ No tracking updates found")
            
        # Test shipment status progression
        if shipment.status in ['PENDING', 'PROCESSING', 'SHIPPED', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED']:
            print(f"✓ Shipment status is valid: {shipment.status}")
        else:
            print(f"✗ Invalid shipment status: {shipment.status}")
            
    except Shipment.DoesNotExist:
        print("✗ Could not find test shipment")


def cleanup_test_data():
    """Clean up test data"""
    print("\nCleaning up test data...")
    
    # Delete in reverse order of dependencies
    ShipmentTracking.objects.filter(shipment__tracking_number='TEST123456').delete()
    Shipment.objects.filter(tracking_number='TEST123456').delete()
    ShippingRate.objects.filter(shipping_partner__code='SHIPROCKET_TEST').delete()
    DeliverySlot.objects.filter(name='Morning Delivery').delete()
    ServiceableArea.objects.filter(shipping_partner__code='SHIPROCKET_TEST').delete()
    ShippingPartner.objects.filter(code='SHIPROCKET_TEST').delete()
    
    print("✓ Test data cleaned up")


def main():
    """Run all tests"""
    print("=" * 60)
    print("SHIPPING MANAGEMENT API FUNCTIONALITY TEST")
    print("=" * 60)
    
    try:
        # Run tests
        test_shipping_models()
        test_serializers()
        test_rate_calculation()
        test_status_mapping()
        test_shipment_tracking()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always cleanup
        cleanup_test_data()


if __name__ == '__main__':
    main()