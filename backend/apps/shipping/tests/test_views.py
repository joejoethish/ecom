from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import time, timedelta
from decimal import Decimal
import json

from ..models import (
    ShippingPartner, 
    ServiceableArea, 
    DeliverySlot, 
    Shipment, 
    ShipmentTracking,
    ShippingRate
)

User = get_user_model()


class ShippingPartnerViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpassword'
        )
        
        self.shipping_partner = ShippingPartner.objects.create(
            name='Test Shipper',
            code='TEST',
            partner_type='SHIPROCKET',
            api_key='test_api_key',
            api_secret='test_api_secret',
            base_url='https://api.testshipper.com',
            is_active=True
        )
        
        self.list_url = reverse('shippingpartner-list')
        self.detail_url = reverse('shippingpartner-detail', args=[self.shipping_partner.id])
    
    def test_list_shipping_partners_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_list_shipping_partners_regular_user(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_shipping_partner_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'New Shipper',
            'code': 'NEW',
            'partner_type': 'DELHIVERY',
            'api_key': 'new_api_key',
            'api_secret': 'new_api_secret',
            'base_url': 'https://api.newshipper.com',
            'is_active': True
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ShippingPartner.objects.count(), 2)
    
    def test_update_shipping_partner_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Updated Shipper'}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shipping_partner.refresh_from_db()
        self.assertEqual(self.shipping_partner.name, 'Updated Shipper')


class DeliverySlotViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpassword'
        )
        
        self.delivery_slot = DeliverySlot.objects.create(
            name='Morning Slot',
            start_time=time(9, 0),
            end_time=time(12, 0),
            day_of_week=0,  # Monday
            additional_fee=Decimal('10.00'),
            max_orders=50,
            is_active=True
        )
        
        self.shipping_partner = ShippingPartner.objects.create(
            name='Test Shipper',
            code='TEST',
            partner_type='SHIPROCKET',
            api_key='test_api_key',
            api_secret='test_api_secret',
            base_url='https://api.testshipper.com',
            is_active=True
        )
        
        self.serviceable_area = ServiceableArea.objects.create(
            shipping_partner=self.shipping_partner,
            pin_code='110001',
            city='New Delhi',
            state='Delhi',
            country='India',
            min_delivery_days=1,
            max_delivery_days=3,
            is_active=True
        )
        
        self.list_url = reverse('deliveryslot-list')
        self.detail_url = reverse('deliveryslot-detail', args=[self.delivery_slot.id])
        self.available_slots_url = reverse('deliveryslot-available-slots')
    
    def test_list_delivery_slots_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_available_slots(self):
        # Calculate a date that matches the day of week of our slot (Monday)
        today = timezone.now().date()
        days_ahead = (0 - today.weekday()) % 7  # 0 = Monday
        next_monday = today + timedelta(days=days_ahead)
        
        data = {
            'delivery_date': next_monday.isoformat(),
            'pin_code': '110001'
        }
        
        response = self.client.post(self.available_slots_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Morning Slot')
        self.assertEqual(response.data[0]['available_capacity'], 50)
    
    def test_available_slots_invalid_pin_code(self):
        today = timezone.now().date()
        days_ahead = (0 - today.weekday()) % 7
        next_monday = today + timedelta(days=days_ahead)
        
        data = {
            'delivery_date': next_monday.isoformat(),
            'pin_code': '999999'  # Invalid pin code
        }
        
        response = self.client.post(self.available_slots_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ShippingRateViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        self.shipping_partner = ShippingPartner.objects.create(
            name='Test Shipper',
            code='TEST',
            partner_type='SHIPROCKET',
            api_key='test_api_key',
            api_secret='test_api_secret',
            base_url='https://api.testshipper.com',
            is_active=True
        )
        
        self.serviceable_area = ServiceableArea.objects.create(
            shipping_partner=self.shipping_partner,
            pin_code='400001',
            city='Mumbai',
            state='Maharashtra',
            country='India',
            min_delivery_days=1,
            max_delivery_days=3,
            is_active=True
        )
        
        self.shipping_rate = ShippingRate.objects.create(
            shipping_partner=self.shipping_partner,
            min_weight=Decimal('0.00'),
            max_weight=Decimal('5.00'),
            base_rate=Decimal('100.00'),
            per_kg_rate=Decimal('20.00')
        )
        
        self.calculate_url = reverse('shippingrate-calculate')
    
    def test_calculate_shipping_rate(self):
        data = {
            'source_pin_code': '110001',
            'destination_pin_code': '400001',
            'weight': '2.5'
        }
        
        response = self.client.post(self.calculate_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if the rate calculation is correct
        # Base rate (100) + per_kg_rate (20) * weight (2.5) = 150
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['rate'], '150.00')
        self.assertEqual(response.data[0]['shipping_partner']['name'], 'Test Shipper')
    
    def test_calculate_shipping_rate_invalid_destination(self):
        data = {
            'source_pin_code': '110001',
            'destination_pin_code': '999999',  # Invalid pin code
            'weight': '2.5'
        }
        
        response = self.client.post(self.calculate_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ShipmentWebhookTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a mock order (using a dictionary since we don't want to import Order)
        self.mock_order = {'id': 1, 'user': self.user}
        
        self.shipping_partner = ShippingPartner.objects.create(
            name='Test Shipper',
            code='TEST',
            partner_type='SHIPROCKET',
            api_key='test_api_key',
            api_secret='test_api_secret',
            base_url='https://api.testshipper.com',
            is_active=True
        )
        
        # Create a shipment with a known tracking number
        self.shipment = Shipment.objects.create(
            order_id=1,  # Mock order ID
            shipping_partner=self.shipping_partner,
            tracking_number='TRACK123456',
            status='PENDING',
            shipping_address={'address': '123 Test St', 'city': 'Test City'},
            shipping_cost=Decimal('150.00')
        )
        
        self.webhook_url = reverse('shipment-webhook')
    
    def test_webhook_update(self):
        current_time = timezone.now()
        
        data = {
            'tracking_number': 'TRACK123456',
            'status': 'DELIVERED',
            'description': 'Package delivered at doorstep',
            'location': 'Mumbai',
            'timestamp': current_time.isoformat(),
            'partner_data': {'delivery_person': 'John Doe', 'signature': 'received'}
        }
        
        response = self.client.post(
            self.webhook_url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if shipment status was updated
        self.shipment.refresh_from_db()
        self.assertEqual(self.shipment.status, 'DELIVERED')
        
        # Check if tracking update was created
        tracking_update = ShipmentTracking.objects.filter(shipment=self.shipment).first()
        self.assertIsNotNone(tracking_update)
        self.assertEqual(tracking_update.status, 'DELIVERED')
        self.assertEqual(tracking_update.description, 'Package delivered at doorstep')
    
    def test_webhook_status_mapping(self):
        """Test that partner-specific statuses are mapped correctly"""
        current_time = timezone.now()
        
        # Test Shiprocket specific status
        data = {
            'tracking_number': 'TRACK123456',
            'status': 'PICKUP COMPLETE',
            'description': 'Package picked up from seller',
            'location': 'Delhi',
            'timestamp': current_time.isoformat()
        }
        
        response = self.client.post(
            self.webhook_url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.shipment.refresh_from_db()
        self.assertEqual(self.shipment.status, 'SHIPPED')
    
    def test_webhook_duplicate_prevention(self):
        """Test that duplicate tracking updates are prevented"""
        current_time = timezone.now()
        
        data = {
            'tracking_number': 'TRACK123456',
            'status': 'IN_TRANSIT',
            'description': 'Package in transit',
            'location': 'Mumbai',
            'timestamp': current_time.isoformat()
        }
        
        # Send the same webhook twice
        response1 = self.client.post(
            self.webhook_url, 
            json.dumps(data), 
            content_type='application/json'
        )
        response2 = self.client.post(
            self.webhook_url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Should only have one tracking update
        tracking_count = ShipmentTracking.objects.filter(
            shipment=self.shipment,
            status='IN_TRANSIT',
            timestamp=current_time
        ).count()
        self.assertEqual(tracking_count, 1)
    
    def test_webhook_invalid_tracking_number(self):
        current_time = timezone.now()
        
        data = {
            'tracking_number': 'INVALID123',
            'status': 'DELIVERED',
            'description': 'Package delivered',
            'location': 'Mumbai',
            'timestamp': current_time.isoformat()
        }
        
        response = self.client.post(
            self.webhook_url, 
            json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ShipmentBulkOperationsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        self.shipping_partner = ShippingPartner.objects.create(
            name='Test Shipper',
            code='TEST',
            partner_type='SHIPROCKET',
            api_key='test_api_key',
            api_secret='test_api_secret',
            base_url='https://api.testshipper.com',
            is_active=True
        )
        
        # Create multiple shipments
        self.shipments = []
        for i in range(3):
            shipment = Shipment.objects.create(
                order_id=i + 1,
                shipping_partner=self.shipping_partner,
                tracking_number=f'TRACK{i+1}',
                status='PENDING',
                shipping_address={'address': f'{i+1} Test St', 'city': 'Test City'},
                shipping_cost=Decimal('150.00')
            )
            self.shipments.append(shipment)
        
        self.bulk_update_url = reverse('shipment-bulk-update-status')
    
    def test_bulk_update_status(self):
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'shipment_ids': [s.id for s in self.shipments],
            'status': 'SHIPPED',
            'description': 'Bulk shipped',
            'location': 'Warehouse'
        }
        
        response = self.client.post(self.bulk_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_count'], 3)
        
        # Check if all shipments were updated
        for shipment in self.shipments:
            shipment.refresh_from_db()
            self.assertEqual(shipment.status, 'SHIPPED')
            
            # Check if tracking updates were created
            tracking_update = ShipmentTracking.objects.filter(
                shipment=shipment,
                status='SHIPPED'
            ).first()
            self.assertIsNotNone(tracking_update)
    
    def test_bulk_update_invalid_shipment_ids(self):
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'shipment_ids': [999, 1000],  # Non-existent IDs
            'status': 'SHIPPED'
        }
        
        response = self.client.post(self.bulk_update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ShipmentAnalyticsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        self.shipping_partner = ShippingPartner.objects.create(
            name='Test Shipper',
            code='TEST',
            partner_type='SHIPROCKET',
            api_key='test_api_key',
            api_secret='test_api_secret',
            base_url='https://api.testshipper.com',
            is_active=True
        )
        
        # Create shipments with different statuses
        base_time = timezone.now()
        self.shipments = []
        
        statuses = ['PENDING', 'SHIPPED', 'DELIVERED', 'DELIVERED']
        for i, status in enumerate(statuses):
            shipment = Shipment.objects.create(
                order_id=i + 1,
                shipping_partner=self.shipping_partner,
                tracking_number=f'TRACK{i+1}',
                status=status,
                shipping_address={'address': f'{i+1} Test St', 'city': 'Test City'},
                shipping_cost=Decimal('150.00'),
                created_at=base_time - timedelta(days=i)
            )
            
            if status in ['SHIPPED', 'DELIVERED']:
                shipment.shipped_at = base_time - timedelta(days=i, hours=1)
            if status == 'DELIVERED':
                shipment.delivered_at = base_time - timedelta(days=i-1)
            
            shipment.save()
            self.shipments.append(shipment)
        
        self.analytics_url = reverse('shipment-analytics')
    
    def test_analytics_basic(self):
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'date_from': (timezone.now() - timedelta(days=10)).date(),
            'date_to': timezone.now().date()
        }
        
        response = self.client.post(self.analytics_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check basic analytics
        self.assertEqual(response.data['total_shipments'], 4)
        self.assertEqual(response.data['delivered_shipments'], 2)
        self.assertEqual(response.data['pending_shipments'], 1)
        
        # Check status breakdown
        status_breakdown = response.data['status_breakdown']
        self.assertEqual(status_breakdown['PENDING']['count'], 1)
        self.assertEqual(status_breakdown['SHIPPED']['count'], 1)
        self.assertEqual(status_breakdown['DELIVERED']['count'], 2)
    
    def test_analytics_with_filters(self):
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'date_from': (timezone.now() - timedelta(days=10)).date(),
            'date_to': timezone.now().date(),
            'shipping_partner_id': self.shipping_partner.id,
            'status': 'DELIVERED'
        }
        
        response = self.client.post(self.analytics_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_shipments'], 2)


class ShippingRateBulkOperationsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        self.shipping_partner = ShippingPartner.objects.create(
            name='Test Shipper',
            code='TEST',
            partner_type='SHIPROCKET',
            api_key='test_api_key',
            api_secret='test_api_secret',
            base_url='https://api.testshipper.com',
            is_active=True
        )
        
        self.bulk_create_url = reverse('shippingrate-bulk-create')
    
    def test_bulk_create_rates(self):
        self.client.force_authenticate(user=self.admin_user)
        
        data = [
            {
                'shipping_partner': self.shipping_partner.id,
                'min_weight': '0.0',
                'max_weight': '1.0',
                'base_rate': '50.00',
                'per_kg_rate': '10.00'
            },
            {
                'shipping_partner': self.shipping_partner.id,
                'min_weight': '1.0',
                'max_weight': '5.0',
                'base_rate': '100.00',
                'per_kg_rate': '20.00'
            }
        ]
        
        response = self.client.post(self.bulk_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 2)
        
        # Check if rates were created
        self.assertEqual(ShippingRate.objects.count(), 2)
    
    def test_bulk_create_invalid_data(self):
        self.client.force_authenticate(user=self.admin_user)
        
        # Send non-list data
        data = {
            'shipping_partner': self.shipping_partner.id,
            'min_weight': '0.0',
            'max_weight': '1.0',
            'base_rate': '50.00'
        }
        
        response = self.client.post(self.bulk_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)