from django.test import TestCase
from django.utils import timezone
from datetime import time, datetime
from decimal import Decimal
from ..models import (
    ShippingPartner, 
    ServiceableArea, 
    DeliverySlot, 
    Shipment, 
    ShipmentTracking,
    ShippingRate
)
from ..serializers import (
    ShippingPartnerSerializer,
    ServiceableAreaSerializer,
    DeliverySlotSerializer,
    ShipmentSerializer,
    ShipmentTrackingSerializer,
    ShippingRateSerializer,
    ShippingRateCalculationSerializer,
    DeliverySlotAvailabilitySerializer,
    TrackingWebhookSerializer
)


class ShippingPartnerSerializerTest(TestCase):
    def setUp(self):
        self.shipping_partner_data = {
            'name': 'Test Shipper',
            'code': 'TEST',
            'partner_type': 'SHIPROCKET',
            'api_key': 'test_api_key',
            'api_secret': 'test_api_secret',
            'base_url': 'https://api.testshipper.com',
            'is_active': True,
            'supports_cod': True,
            'supports_prepaid': True,
            'supports_international': False,
            'supports_return': True,
            'contact_person': 'Test Contact',
            'contact_email': 'contact@testshipper.com',
            'contact_phone': '1234567890'
        }
        self.shipping_partner = ShippingPartner.objects.create(**self.shipping_partner_data)
        self.serializer = ShippingPartnerSerializer(instance=self.shipping_partner)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        expected_fields = [
            'id', 'name', 'code', 'partner_type', 'base_url',
            'is_active', 'supports_cod', 'supports_prepaid',
            'supports_international', 'supports_return',
            'contact_person', 'contact_email', 'contact_phone',
            'created_at', 'updated_at'
        ]
        self.assertEqual(set(data.keys()), set(expected_fields))
        
    def test_name_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['name'], self.shipping_partner_data['name'])


class DeliverySlotSerializerTest(TestCase):
    def setUp(self):
        self.delivery_slot_data = {
            'name': 'Morning Slot',
            'start_time': time(9, 0),
            'end_time': time(12, 0),
            'day_of_week': 0,  # Monday
            'additional_fee': Decimal('10.00'),
            'max_orders': 50,
            'is_active': True
        }
        self.delivery_slot = DeliverySlot.objects.create(**self.delivery_slot_data)
        self.serializer = DeliverySlotSerializer(instance=self.delivery_slot)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        expected_fields = [
            'id', 'name', 'start_time', 'end_time', 'day_of_week',
            'day_of_week_display', 'additional_fee', 'max_orders',
            'is_active', 'created_at', 'updated_at'
        ]
        self.assertEqual(set(data.keys()), set(expected_fields))
        
    def test_day_of_week_display_field(self):
        data = self.serializer.data
        self.assertEqual(data['day_of_week_display'], 'Monday')


class ShippingRateCalculationSerializerTest(TestCase):
    def test_valid_data(self):
        data = {
            'source_pin_code': '110001',
            'destination_pin_code': '400001',
            'weight': '5.5',
            'dimensions': {'length': 10, 'width': 10, 'height': 10}
        }
        serializer = ShippingRateCalculationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
    def test_invalid_data(self):
        data = {
            'source_pin_code': '110001',
            'destination_pin_code': '400001',
            'weight': 'invalid'  # Invalid weight
        }
        serializer = ShippingRateCalculationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('weight', serializer.errors)


class TrackingWebhookSerializerTest(TestCase):
    def test_valid_data(self):
        data = {
            'tracking_number': 'TRACK123456',
            'status': 'DELIVERED',
            'description': 'Package delivered',
            'location': 'Mumbai',
            'timestamp': timezone.now().isoformat(),
            'partner_data': {'partner_id': 'XYZ123'}
        }
        serializer = TrackingWebhookSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
    def test_invalid_data(self):
        data = {
            'tracking_number': 'TRACK123456',
            'status': 'DELIVERED',
            # Missing required timestamp field
        }
        serializer = TrackingWebhookSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('timestamp', serializer.errors)