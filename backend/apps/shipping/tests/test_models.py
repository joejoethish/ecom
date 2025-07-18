from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import time

from apps.shipping.models import (
    ShippingPartner,
    ServiceableArea,
    DeliverySlot,
    Shipment,
    ShipmentTracking,
    ShippingRate
)

class ShippingPartnerModelTest(TestCase):
    """Tests for the ShippingPartner model"""
    
    def setUp(self):
        self.shipping_partner = ShippingPartner.objects.create(
            name="Test Shipping Partner",
            code="TEST",
            partner_type="SHIPROCKET",
            api_key="test_api_key",
            api_secret="test_api_secret",
            base_url="https://api.test.com",
            is_active=True,
            supports_cod=True,
            supports_prepaid=True,
            supports_international=False,
            supports_return=True,
            contact_person="Test Contact",
            contact_email="test@example.com",
            contact_phone="1234567890"
        )
    
    def test_shipping_partner_creation(self):
        """Test that a shipping partner can be created"""
        self.assertEqual(self.shipping_partner.name, "Test Shipping Partner")
        self.assertEqual(self.shipping_partner.code, "TEST")
        self.assertEqual(self.shipping_partner.partner_type, "SHIPROCKET")
        self.assertTrue(self.shipping_partner.is_active)
        self.assertTrue(self.shipping_partner.supports_cod)
        self.assertFalse(self.shipping_partner.supports_international)
    
    def test_shipping_partner_str(self):
        """Test the string representation of a shipping partner"""
        self.assertEqual(
            str(self.shipping_partner),
            "Test Shipping Partner (Shiprocket)"
        )


class ServiceableAreaModelTest(TestCase):
    """Tests for the ServiceableArea model"""
    
    def setUp(self):
        self.shipping_partner = ShippingPartner.objects.create(
            name="Test Shipping Partner",
            code="TEST",
            partner_type="SHIPROCKET",
            api_key="test_api_key",
            base_url="https://api.test.com"
        )
        
        self.serviceable_area = ServiceableArea.objects.create(
            shipping_partner=self.shipping_partner,
            pin_code="123456",
            city="Test City",
            state="Test State",
            country="India",
            min_delivery_days=1,
            max_delivery_days=3,
            is_active=True
        )
    
    def test_serviceable_area_creation(self):
        """Test that a serviceable area can be created"""
        self.assertEqual(self.serviceable_area.pin_code, "123456")
        self.assertEqual(self.serviceable_area.city, "Test City")
        self.assertEqual(self.serviceable_area.state, "Test State")
        self.assertEqual(self.serviceable_area.min_delivery_days, 1)
        self.assertEqual(self.serviceable_area.max_delivery_days, 3)
        self.assertTrue(self.serviceable_area.is_active)
    
    def test_serviceable_area_str(self):
        """Test the string representation of a serviceable area"""
        self.assertEqual(
            str(self.serviceable_area),
            "123456 - Test City, Test State"
        )
    
    def test_pin_code_validation(self):
        """Test that pin code validation works"""
        # Invalid pin code (too short)
        with self.assertRaises(ValidationError):
            area = ServiceableArea(
                shipping_partner=self.shipping_partner,
                pin_code="12345",  # 5 digits instead of 6
                city="Test City",
                state="Test State"
            )
            area.full_clean()
        
        # Invalid pin code (non-numeric)
        with self.assertRaises(ValidationError):
            area = ServiceableArea(
                shipping_partner=self.shipping_partner,
                pin_code="12345A",  # Contains a letter
                city="Test City",
                state="Test State"
            )
            area.full_clean()


class DeliverySlotModelTest(TestCase):
    """Tests for the DeliverySlot model"""
    
    def setUp(self):
        self.delivery_slot = DeliverySlot.objects.create(
            name="Morning Delivery",
            start_time=time(9, 0),  # 9:00 AM
            end_time=time(12, 0),   # 12:00 PM
            day_of_week=0,          # Monday
            additional_fee=50.00,
            max_orders=20,
            is_active=True
        )
    
    def test_delivery_slot_creation(self):
        """Test that a delivery slot can be created"""
        self.assertEqual(self.delivery_slot.name, "Morning Delivery")
        self.assertEqual(self.delivery_slot.start_time, time(9, 0))
        self.assertEqual(self.delivery_slot.end_time, time(12, 0))
        self.assertEqual(self.delivery_slot.day_of_week, 0)
        self.assertEqual(self.delivery_slot.additional_fee, 50.00)
        self.assertEqual(self.delivery_slot.max_orders, 20)
        self.assertTrue(self.delivery_slot.is_active)
    
    def test_delivery_slot_str(self):
        """Test the string representation of a delivery slot"""
        self.assertEqual(
            str(self.delivery_slot),
            "Monday 09:00 AM - 12:00 PM"
        )


class ShipmentModelTest(TestCase):
    """Tests for the Shipment model"""
    
    def setUp(self):
        # Create a mock Order class since we can't import it directly (circular import)
        from django.db import models
        
        class MockOrder(models.Model):
            order_number = models.CharField(max_length=20)
            
            class Meta:
                app_label = 'orders'
                
        # Create necessary objects
        self.shipping_partner = ShippingPartner.objects.create(
            name="Test Shipping Partner",
            code="TEST",
            partner_type="SHIPROCKET",
            api_key="test_api_key",
            base_url="https://api.test.com"
        )
        
        self.delivery_slot = DeliverySlot.objects.create(
            name="Morning Delivery",
            start_time=time(9, 0),
            end_time=time(12, 0),
            day_of_week=0
        )
        
        # This is a simplified test that doesn't actually create an Order
        # In a real test, you would use a proper mock or fixture
        self.shipment = Shipment(
            # order would be set to a real Order instance
            shipping_partner=self.shipping_partner,
            tracking_number="TRACK123456",
            shipping_label_url="https://example.com/label.pdf",
            partner_order_id="PARTNER123",
            partner_shipment_id="SHIPMENT123",
            status="PROCESSING",
            estimated_delivery_date=timezone.now().date(),
            delivery_slot=self.delivery_slot,
            shipping_address={
                "name": "Test Customer",
                "address_line_1": "123 Test Street",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "123456",
                "country": "India",
                "phone": "1234567890"
            },
            weight=1.5,
            dimensions={"length": 10, "width": 10, "height": 5},
            shipping_cost=100.00
        )
    
    def test_shipment_fields(self):
        """Test that a shipment has the correct fields"""
        self.assertEqual(self.shipment.tracking_number, "TRACK123456")
        self.assertEqual(self.shipment.shipping_label_url, "https://example.com/label.pdf")
        self.assertEqual(self.shipment.partner_order_id, "PARTNER123")
        self.assertEqual(self.shipment.partner_shipment_id, "SHIPMENT123")
        self.assertEqual(self.shipment.status, "PROCESSING")
        self.assertEqual(self.shipment.shipping_partner, self.shipping_partner)
        self.assertEqual(self.shipment.delivery_slot, self.delivery_slot)
        self.assertEqual(self.shipment.weight, 1.5)
        self.assertEqual(self.shipment.dimensions, {"length": 10, "width": 10, "height": 5})
        self.assertEqual(self.shipment.shipping_cost, 100.00)


class ShipmentTrackingModelTest(TestCase):
    """Tests for the ShipmentTracking model"""
    
    def setUp(self):
        # Create a mock Order class since we can't import it directly (circular import)
        from django.db import models
        
        class MockOrder(models.Model):
            order_number = models.CharField(max_length=20)
            
            class Meta:
                app_label = 'orders'
        
        # Create necessary objects
        self.shipping_partner = ShippingPartner.objects.create(
            name="Test Shipping Partner",
            code="TEST",
            partner_type="SHIPROCKET",
            api_key="test_api_key",
            base_url="https://api.test.com"
        )
        
        # This is a simplified test that doesn't actually create an Order
        self.shipment = Shipment(
            # order would be set to a real Order instance
            shipping_partner=self.shipping_partner,
            tracking_number="TRACK123456",
            status="PROCESSING"
        )
        
        self.tracking = ShipmentTracking(
            shipment=self.shipment,
            status="PROCESSING",
            description="Shipment created",
            location="Warehouse",
            timestamp=timezone.now(),
            raw_response={"status": "success"}
        )
    
    def test_shipment_tracking_fields(self):
        """Test that a shipment tracking has the correct fields"""
        self.assertEqual(self.tracking.shipment, self.shipment)
        self.assertEqual(self.tracking.status, "PROCESSING")
        self.assertEqual(self.tracking.description, "Shipment created")
        self.assertEqual(self.tracking.location, "Warehouse")
        self.assertEqual(self.tracking.raw_response, {"status": "success"})


class ShippingRateModelTest(TestCase):
    """Tests for the ShippingRate model"""
    
    def setUp(self):
        self.shipping_partner = ShippingPartner.objects.create(
            name="Test Shipping Partner",
            code="TEST",
            partner_type="SHIPROCKET",
            api_key="test_api_key",
            base_url="https://api.test.com"
        )
        
        self.shipping_rate = ShippingRate.objects.create(
            shipping_partner=self.shipping_partner,
            source_pin_code="123456",
            destination_pin_code="654321",
            min_weight=0.5,
            max_weight=1.0,
            min_distance=0,
            max_distance=100,
            base_rate=50.00,
            per_kg_rate=10.00,
            per_km_rate=0.50
        )
    
    def test_shipping_rate_creation(self):
        """Test that a shipping rate can be created"""
        self.assertEqual(self.shipping_rate.shipping_partner, self.shipping_partner)
        self.assertEqual(self.shipping_rate.source_pin_code, "123456")
        self.assertEqual(self.shipping_rate.destination_pin_code, "654321")
        self.assertEqual(self.shipping_rate.min_weight, 0.5)
        self.assertEqual(self.shipping_rate.max_weight, 1.0)
        self.assertEqual(self.shipping_rate.min_distance, 0)
        self.assertEqual(self.shipping_rate.max_distance, 100)
        self.assertEqual(self.shipping_rate.base_rate, 50.00)
        self.assertEqual(self.shipping_rate.per_kg_rate, 10.00)
        self.assertEqual(self.shipping_rate.per_km_rate, 0.50)
    
    def test_shipping_rate_str(self):
        """Test the string representation of a shipping rate"""
        self.assertEqual(
            str(self.shipping_rate),
            "Test Shipping Partner - 0.5kg to 1.0kg"
        )