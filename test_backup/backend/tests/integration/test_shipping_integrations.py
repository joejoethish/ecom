#!/usr/bin/env python
"""
Shipping Partner Integration Tests

This module contains integration tests for shipping partner integrations,
testing the interaction between the e-commerce platform and shipping providers.
"""

import os
import sys
import django
import json
import uuid
from decimal import Decimal
from unittest import mock
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem
from apps.shipping.models import ShippingPartner, Shipment, ShipmentTracking, ServiceableArea
from apps.products.models import Product, Category
from apps.customers.models import Address

User = get_user_model()


class MockShiprocketClient:
    """Mock Shiprocket client for testing"""
    
    def __init__(self, *args, **kwargs):
        self.token = 'mock_shiprocket_token'
    
    def generate_token(self):
        return {
            'token': self.token,
            'expires_at': (datetime.now() + timedelta(days=1)).isoformat()
        }
    
    def check_serviceability(self, pickup_postcode, delivery_postcode, weight, cod=0):
        return {
            'status': 200,
            'data': {
                'available_courier_companies': [
                    {
                        'id': 1,
                        'name': 'Delhivery',
                        'rate': 100.0,
                        'etd': '2-3 days',
                        'is_cod_available': True
                    },
                    {
                        'id': 2,
                        'name': 'DTDC',
                        'rate': 120.0,
                        'etd': '3-4 days',
                        'is_cod_available': True
                    }
                ]
            }
        }
    
    def create_order(self, order_data):
        return {
            'status': 200,
            'data': {
                'order_id': 123456,
                'shipment_id': 7890123,
                'status': 'NEW',
                'status_code': 1,
                'courier_company_id': 1,
                'courier_name': 'Delhivery',
                'awb_code': f'SR{uuid.uuid4().hex[:10].upper()}',
                'pickup_scheduled_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'pickup_token_number': f'PT{uuid.uuid4().hex[:8].upper()}',
                'label_url': f'https://shiprocket.co/label/{uuid.uuid4().hex}',
                'manifest_url': f'https://shiprocket.co/manifest/{uuid.uuid4().hex}'
            }
        }
    
    def track_shipment(self, shipment_id=None, awb_code=None):
        current_status = 'Pickup Scheduled'
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'status': 200,
            'tracking_data': {
                'shipment_id': shipment_id or 7890123,
                'awb_code': awb_code or f'SR{uuid.uuid4().hex[:10].upper()}',
                'current_status': current_status,
                'current_timestamp': current_timestamp,
                'delivered_to': 'Self',
                'destination': 'Mumbai',
                'etd': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                'courier_name': 'Delhivery',
                'tracking_history': [
                    {
                        'status': 'Order Placed',
                        'location': 'Delhi',
                        'timestamp': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                    },
                    {
                        'status': current_status,
                        'location': 'Delhi',
                        'timestamp': current_timestamp
                    }
                ]
            }
        }
    
    def cancel_shipment(self, shipment_id):
        return {
            'status': 200,
            'message': 'Shipment cancelled successfully'
        }


class MockDelhiveryClient:
    """Mock Delhivery client for testing"""
    
    def __init__(self, *args, **kwargs):
        self.token = 'mock_delhivery_token'
    
    def check_serviceability(self, pin_code):
        return {
            'delivery_codes': [
                {
                    'postal_code': pin_code,
                    'status': 'serviceable',
                    'district': 'Mumbai',
                    'state': 'Maharashtra',
                    'pre_paid': True,
                    'cash': True,
                    'pickup': True,
                    'delivery_codes': 'ALL'
                }
            ]
        }
    
    def create_waybill(self, count=1):
        return {
            'success': True,
            'waybills': [f'DL{uuid.uuid4().hex[:10].upper()}' for _ in range(count)]
        }
    
    def create_package(self, package_data):
        return {
            'success': True,
            'package_id': f'PKG{uuid.uuid4().hex[:8].upper()}',
            'waybill': package_data.get('waybill') or f'DL{uuid.uuid4().hex[:10].upper()}',
            'status': 'Manifested',
            'client_reference_number': package_data.get('client_reference_number')
        }
    
    def track_package(self, waybill):
        current_status = 'Manifested'
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'success': True,
            'ShipmentData': [
                {
                    'Shipment': {
                        'AWB': waybill,
                        'Status': current_status,
                        'StatusDateTime': current_timestamp,
                        'DestinationCity': 'Mumbai',
                        'ExpectedDeliveryDate': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
                    },
                    'Scans': [
                        {
                            'ScanDetail': {
                                'Scan': 'Manifested',
                                'ScanDateTime': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                                'ScannedLocation': 'Delhi'
                            }
                        },
                        {
                            'ScanDetail': {
                                'Scan': current_status,
                                'ScanDateTime': current_timestamp,
                                'ScannedLocation': 'Delhi'
                            }
                        }
                    ]
                }
            ]
        }
    
    def cancel_package(self, waybill):
        return {
            'success': True,
            'message': 'Shipment cancelled successfully'
        }


class ShippingPartnerIntegrationTest(TestCase):
    """Test shipping partner integrations"""
    
    def setUp(self):
        """Set up test data for shipping integration tests"""
        # Create test user
        self.user = User.objects.create_user(
            username='shippinguser',
            email='shipping@example.com',
            password='testpass123',
            first_name='Shipping',
            last_name='User'
        )
        
        # Create API client
        self.client = APIClient()
        self.client.login(username='shippinguser', password='testpass123')
        
        # Create category and product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            is_active=True
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product description',
            short_description='Test product',
            category=self.category,
            brand='TestBrand',
            sku='TEST001',
            price=Decimal('100.00'),
            is_active=True
        )
        
        # Create address
        self.address = Address.objects.create(
            user=self.user,
            type='HOME',
            first_name='Shipping',
            last_name='User',
            address_line_1='123 Shipping Street',
            city='Mumbai',
            state='Maharashtra',
            postal_code='400001',
            country='India',
            phone='1234567890',
            is_default=True
        )
        
        # Create shipping partners
        self.shiprocket_partner = ShippingPartner.objects.create(
            name='Shiprocket',
            code='SHIPROCKET',
            partner_type='SHIPROCKET',
            api_key='test_shiprocket_key',
            api_secret='test_shiprocket_secret',
            base_url='https://apiv2.shiprocket.in/v1/external',
            is_active=True,
            supports_cod=True,
            supports_prepaid=True
        )
        
        self.delhivery_partner = ShippingPartner.objects.create(
            name='Delhivery',
            code='DELHIVERY',
            partner_type='DELHIVERY',
            api_key='test_delhivery_key',
            api_secret='test_delhivery_secret',
            base_url='https://track.delhivery.com/api',
            is_active=True,
            supports_cod=True,
            supports_prepaid=True
        )
        
        # Create serviceable areas
        self.shiprocket_area = ServiceableArea.objects.create(
            shipping_partner=self.shiprocket_partner,
            pin_code='400001',
            city='Mumbai',
            state='Maharashtra',
            country='India',
            min_delivery_days=2,
            max_delivery_days=4,
            is_active=True
        )
        
        self.delhivery_area = ServiceableArea.objects.create(
            shipping_partner=self.delhivery_partner,
            pin_code='400001',
            city='Mumbai',
            state='Maharashtra',
            country='India',
            min_delivery_days=1,
            max_delivery_days=3,
            is_active=True
        )
        
        # Create order
        self.order = Order.objects.create(
            user=self.user,
            order_number=f'ORD-{uuid.uuid4().hex[:8].upper()}',
            status='CONFIRMED',
            total_amount=Decimal('100.00'),
            shipping_amount=Decimal('10.00'),
            tax_amount=Decimal('5.00'),
            shipping_address={
                'first_name': 'Shipping',
                'last_name': 'User',
                'address_line_1': '123 Shipping Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India',
                'phone': '1234567890'
            },
            billing_address={
                'first_name': 'Shipping',
                'last_name': 'User',
                'address_line_1': '123 Shipping Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India',
                'phone': '1234567890'
            },
            payment_method='PREPAID',
            payment_status='PAID'
        )
        
        # Create order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )

    @mock.patch('apps.shipping.services.shiprocket.ShiprocketClient', MockShiprocketClient)
    def test_shiprocket_integration_flow(self):
        """Test complete Shiprocket integration flow"""
        print("\nTesting Shiprocket integration flow...")
        
        # Step 1: Check serviceability
        response = self.client.get('/api/v1/shipping/check-serviceability/', {
            'pickup_pin_code': '110001',  # Delhi
            'delivery_pin_code': '400001',  # Mumbai
            'weight': '0.5'
        })
        self.assertEqual(response.status_code, 200)
        serviceability_data = response.json()
        self.assertTrue(serviceability_data['is_serviceable'])
        self.assertGreater(len(serviceability_data['shipping_options']), 0)
        print("✓ Serviceability check successful")
        
        # Step 2: Create shipment
        response = self.client.post('/api/v1/shipping/create-shipment/', {
            'order_id': self.order.id,
            'shipping_partner_id': self.shiprocket_partner.id,
            'package_weight': '0.5',
            'package_dimensions': {
                'length': 10,
                'width': 10,
                'height': 5
            },
            'is_cod': False
        })
        self.assertEqual(response.status_code, 201)
        shipment_data = response.json()
        self.assertIn('tracking_number', shipment_data)
        self.assertIn('label_url', shipment_data)
        tracking_number = shipment_data['tracking_number']
        print(f"✓ Shipment created successfully with tracking number: {tracking_number}")
        
        # Step 3: Track shipment
        response = self.client.get('/api/v1/shipping/track-shipment/', {
            'tracking_number': tracking_number
        })
        self.assertEqual(response.status_code, 200)
        tracking_data = response.json()
        self.assertIn('current_status', tracking_data)
        self.assertIn('tracking_history', tracking_data)
        self.assertGreater(len(tracking_data['tracking_history']), 0)
        print(f"✓ Shipment tracking successful: {tracking_data['current_status']}")
        
        # Step 4: Update shipment status via webhook
        webhook_data = {
            'awb': tracking_number,
            'current_status': 'In Transit',
            'current_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'location': 'Delhi Hub',
            'additional_info': 'Package in transit to destination'
        }
        
        response = self.client.post('/api/v1/shipping/webhook/shiprocket/', webhook_data, format='json')
        self.assertEqual(response.status_code, 200)
        print("✓ Webhook status update successful")
        
        # Step 5: Verify shipment status update
        shipment = Shipment.objects.get(tracking_number=tracking_number)
        self.assertEqual(shipment.status, 'IN_TRANSIT')
        
        # Check tracking history
        tracking_updates = ShipmentTracking.objects.filter(shipment=shipment).order_by('-timestamp')
        self.assertGreater(tracking_updates.count(), 0)
        latest_update = tracking_updates.first()
        self.assertEqual(latest_update.status, 'IN_TRANSIT')
        self.assertEqual(latest_update.location, 'Delhi Hub')
        print("✓ Shipment status and tracking history updated correctly")
        
        # Step 6: Cancel shipment
        response = self.client.post(f'/api/v1/shipping/cancel-shipment/', {
            'tracking_number': tracking_number,
            'reason': 'Customer requested cancellation'
        })
        self.assertEqual(response.status_code, 200)
        cancel_data = response.json()
        self.assertEqual(cancel_data['status'], 'success')
        print("✓ Shipment cancellation successful")
        
        # Verify shipment status after cancellation
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, 'CANCELLED')
        print("✓ Shipment status updated to cancelled")
        
        print("✓ Shiprocket integration flow test passed!")

    @mock.patch('apps.shipping.services.delhivery.DelhiveryClient', MockDelhiveryClient)
    def test_delhivery_integration_flow(self):
        """Test complete Delhivery integration flow"""
        print("\nTesting Delhivery integration flow...")
        
        # Step 1: Check serviceability
        response = self.client.get('/api/v1/shipping/check-serviceability/', {
            'delivery_pin_code': '400001',  # Mumbai
            'shipping_partner': 'DELHIVERY'
        })
        self.assertEqual(response.status_code, 200)
        serviceability_data = response.json()
        self.assertTrue(serviceability_data['is_serviceable'])
        print("✓ Serviceability check successful")
        
        # Step 2: Create waybill
        response = self.client.post('/api/v1/shipping/delhivery/create-waybill/')
        self.assertEqual(response.status_code, 200)
        waybill_data = response.json()
        self.assertIn('waybills', waybill_data)
        self.assertGreater(len(waybill_data['waybills']), 0)
        waybill = waybill_data['waybills'][0]
        print(f"✓ Waybill created successfully: {waybill}")
        
        # Step 3: Create shipment
        response = self.client.post('/api/v1/shipping/create-shipment/', {
            'order_id': self.order.id,
            'shipping_partner_id': self.delhivery_partner.id,
            'package_weight': '0.5',
            'package_dimensions': {
                'length': 10,
                'width': 10,
                'height': 5
            },
            'is_cod': False,
            'waybill': waybill
        })
        self.assertEqual(response.status_code, 201)
        shipment_data = response.json()
        self.assertIn('tracking_number', shipment_data)
        tracking_number = shipment_data['tracking_number']
        print(f"✓ Shipment created successfully with tracking number: {tracking_number}")
        
        # Step 4: Track shipment
        response = self.client.get('/api/v1/shipping/track-shipment/', {
            'tracking_number': tracking_number
        })
        self.assertEqual(response.status_code, 200)
        tracking_data = response.json()
        self.assertIn('current_status', tracking_data)
        self.assertIn('tracking_history', tracking_data)
        self.assertGreater(len(tracking_data['tracking_history']), 0)
        print(f"✓ Shipment tracking successful: {tracking_data['current_status']}")
        
        # Step 5: Update shipment status via webhook
        webhook_data = {
            'waybill': tracking_number,
            'status': 'In Transit',
            'status_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'location': 'Mumbai Hub',
            'instructions': 'Package in transit to destination'
        }
        
        response = self.client.post('/api/v1/shipping/webhook/delhivery/', webhook_data, format='json')
        self.assertEqual(response.status_code, 200)
        print("✓ Webhook status update successful")
        
        # Step 6: Verify shipment status update
        shipment = Shipment.objects.get(tracking_number=tracking_number)
        self.assertEqual(shipment.status, 'IN_TRANSIT')
        
        # Check tracking history
        tracking_updates = ShipmentTracking.objects.filter(shipment=shipment).order_by('-timestamp')
        self.assertGreater(tracking_updates.count(), 0)
        latest_update = tracking_updates.first()
        self.assertEqual(latest_update.status, 'IN_TRANSIT')
        self.assertEqual(latest_update.location, 'Mumbai Hub')
        print("✓ Shipment status and tracking history updated correctly")
        
        # Step 7: Cancel shipment
        response = self.client.post(f'/api/v1/shipping/cancel-shipment/', {
            'tracking_number': tracking_number,
            'reason': 'Customer requested cancellation'
        })
        self.assertEqual(response.status_code, 200)
        cancel_data = response.json()
        self.assertEqual(cancel_data['status'], 'success')
        print("✓ Shipment cancellation successful")
        
        # Verify shipment status after cancellation
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, 'CANCELLED')
        print("✓ Shipment status updated to cancelled")
        
        print("✓ Delhivery integration flow test passed!")

    def test_delivery_slot_selection(self):
        """Test delivery slot selection functionality"""
        print("\nTesting delivery slot selection...")
        
        # Create delivery slots
        from apps.shipping.models import DeliverySlot
        
        morning_slot = DeliverySlot.objects.create(
            name='Morning Delivery',
            start_time='09:00:00',
            end_time='12:00:00',
            day_of_week=1,  # Monday
            additional_fee=Decimal('10.00'),
            max_orders=50,
            is_active=True
        )
        
        afternoon_slot = DeliverySlot.objects.create(
            name='Afternoon Delivery',
            start_time='13:00:00',
            end_time='17:00:00',
            day_of_week=1,  # Monday
            additional_fee=Decimal('5.00'),
            max_orders=50,
            is_active=True
        )
        
        # Step 1: Get available delivery slots
        # Calculate next Monday
        import datetime
        today = datetime.date.today()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + datetime.timedelta(days=days_ahead)
        
        response = self.client.get('/api/v1/shipping/delivery-slots/', {
            'delivery_date': next_monday.isoformat(),
            'pin_code': '400001'
        })
        self.assertEqual(response.status_code, 200)
        slots_data = response.json()
        self.assertEqual(len(slots_data), 2)
        print(f"✓ Retrieved {len(slots_data)} available delivery slots")
        
        # Step 2: Select a delivery slot for shipment
        response = self.client.post('/api/v1/shipping/create-shipment/', {
            'order_id': self.order.id,
            'shipping_partner_id': self.shiprocket_partner.id,
            'package_weight': '0.5',
            'package_dimensions': {
                'length': 10,
                'width': 10,
                'height': 5
            },
            'is_cod': False,
            'delivery_slot_id': morning_slot.id,
            'delivery_date': next_monday.isoformat()
        })
        self.assertEqual(response.status_code, 201)
        shipment_data = response.json()
        self.assertIn('tracking_number', shipment_data)
        self.assertIn('delivery_slot', shipment_data)
        self.assertEqual(shipment_data['delivery_slot']['name'], 'Morning Delivery')
        print("✓ Shipment created with delivery slot successfully")
        
        # Step 3: Verify additional fee was added
        shipment = Shipment.objects.get(id=shipment_data['id'])
        self.assertEqual(shipment.shipping_cost, Decimal('10.00') + shipment.base_shipping_cost)
        print("✓ Additional fee for delivery slot applied correctly")
        
        print("✓ Delivery slot selection test passed!")

    def test_multi_package_shipment(self):
        """Test creating a shipment with multiple packages"""
        print("\nTesting multi-package shipment...")
        
        # Create another product
        product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Another test product description',
            short_description='Another test product',
            category=self.category,
            brand='TestBrand',
            sku='TEST002',
            price=Decimal('150.00'),
            is_active=True
        )
        
        # Add another item to the order
        order_item2 = OrderItem.objects.create(
            order=self.order,
            product=product2,
            quantity=1,
            unit_price=Decimal('150.00'),
            total_price=Decimal('150.00')
        )
        
        # Update order total
        self.order.total_amount = Decimal('250.00')  # 100 + 150
        self.order.save()
        
        # Step 1: Create multi-package shipment
        response = self.client.post('/api/v1/shipping/create-multi-package-shipment/', {
            'order_id': self.order.id,
            'shipping_partner_id': self.shiprocket_partner.id,
            'packages': [
                {
                    'items': [{'order_item_id': self.order_item.id, 'quantity': 1}],
                    'weight': '0.5',
                    'dimensions': {'length': 10, 'width': 10, 'height': 5}
                },
                {
                    'items': [{'order_item_id': order_item2.id, 'quantity': 1}],
                    'weight': '0.8',
                    'dimensions': {'length': 15, 'width': 15, 'height': 10}
                }
            ],
            'is_cod': False
        })
        self.assertEqual(response.status_code, 201)
        shipments_data = response.json()
        self.assertEqual(len(shipments_data), 2)
        tracking_numbers = [s['tracking_number'] for s in shipments_data]
        print(f"✓ Created {len(shipments_data)} shipments with tracking numbers: {', '.join(tracking_numbers)}")
        
        # Step 2: Verify shipments in database
        shipments = Shipment.objects.filter(order_id=self.order.id)
        self.assertEqual(shipments.count(), 2)
        
        # Verify each shipment has correct items
        for shipment in shipments:
            self.assertEqual(shipment.items.count(), 1)
        
        print("✓ Multi-package shipment test passed!")


def main():
    """Run the shipping integration tests"""
    from django.test.runner import DiscoverRunner
    test_runner = DiscoverRunner(verbosity=2)
    failures = test_runner.run_tests(['tests.integration.test_shipping_integrations'])
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()