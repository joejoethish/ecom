from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import datetime

from apps.shipping.models import (
    ShippingPartner,
    ServiceableArea,
    Shipment,
    ShipmentTracking
)
from apps.shipping.services import (
    ShippingService,
    ShiprocketService,
    DelhiveryService,
    ShippingException
)

class ShippingServiceTest(TestCase):
    """Tests for the ShippingService class"""
    
    def setUp(self):
        self.shipping_partner = ShippingPartner.objects.create(
            name="Test Shipping Partner",
            code="TEST",
            partner_type="SHIPROCKET",
            api_key="test_api_key",
            api_secret="test_api_secret",
            base_url="https://api.test.com",
            configuration={"pickup_postcode": "123456"}
        )
        
        self.service = ShippingService()
    
    def test_get_shipping_partner_service(self):
        """Test getting the appropriate shipping partner service"""
        # Test Shiprocket service
        shiprocket_partner = ShippingPartner.objects.create(
            name="Shiprocket",
            code="SHIPROCKET",
            partner_type="SHIPROCKET",
            api_key="test_key",
            base_url="https://api.shiprocket.com"
        )
        
        service = self.service.get_shipping_partner_service(shiprocket_partner)
        self.assertIsInstance(service, ShiprocketService)
        
        # Test Delhivery service
        delhivery_partner = ShippingPartner.objects.create(
            name="Delhivery",
            code="DELHIVERY",
            partner_type="DELHIVERY",
            api_key="test_key",
            base_url="https://api.delhivery.com"
        )
        
        service = self.service.get_shipping_partner_service(delhivery_partner)
        self.assertIsInstance(service, DelhiveryService)
        
        # Test unsupported partner
        other_partner = ShippingPartner.objects.create(
            name="Other",
            code="OTHER",
            partner_type="OTHER",
            api_key="test_key",
            base_url="https://api.other.com"
        )
        
        with self.assertRaises(ShippingException):
            self.service.get_shipping_partner_service(other_partner)
    
    def test_check_serviceability(self):
        """Test checking serviceability for a pin code"""
        with patch.object(ShippingService, 'get_shipping_partner_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.check_serviceability.return_value = {
                "serviceable": True,
                "delivery_days": 3
            }
            mock_get_service.return_value = mock_service
            
            result = self.service.check_serviceability("123456")
            
            self.assertTrue(result["serviceable"])
            self.assertEqual(result["delivery_days"], 3)
            mock_service.check_serviceability.assert_called_once_with("123456")
    
    def test_create_shipment(self):
        """Test creating a shipment"""
        order_data = {
            "order_number": "ORD123",
            "shipping_address": {
                "name": "Test Customer",
                "address_line_1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "123456",
                "country": "India",
                "phone": "1234567890"
            },
            "items": [
                {
                    "product_name": "Test Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ],
            "total_amount": 100.00
        }
        
        with patch.object(ShippingService, 'get_shipping_partner_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_order.return_value = {
                "partner_order_id": "PARTNER123",
                "shipment_id": "SHIPMENT123",
                "status": "PROCESSING",
                "tracking_number": "TRACK123",
                "estimated_delivery_date": "2025-07-25",
                "shipping_cost": 50.00
            }
            mock_get_service.return_value = mock_service
            
            # Mock the Order model
            mock_order = MagicMock()
            mock_order.order_number = "ORD123"
            
            shipment = self.service.create_shipment(mock_order, self.shipping_partner, order_data)
            
            self.assertEqual(shipment.tracking_number, "TRACK123")
            self.assertEqual(shipment.partner_order_id, "PARTNER123")
            self.assertEqual(shipment.partner_shipment_id, "SHIPMENT123")
            self.assertEqual(shipment.status, "PROCESSING")
            self.assertEqual(shipment.shipping_cost, 50.00)
            mock_service.create_order.assert_called_once_with(order_data)
    
    def test_track_shipment(self):
        """Test tracking a shipment"""
        # Create a mock shipment
        mock_order = MagicMock()
        mock_order.order_number = "ORD123"
        
        shipment = Shipment.objects.create(
            order=mock_order,
            shipping_partner=self.shipping_partner,
            tracking_number="TRACK123",
            status="PROCESSING",
            shipping_address={"name": "Test Customer"}
        )
        
        with patch.object(ShippingService, 'get_shipping_partner_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.track_shipment.return_value = {
                "status": "IN_TRANSIT",
                "estimated_delivery_date": "2025-07-25",
                "tracking_history": [
                    {
                        "status": "PROCESSING",
                        "description": "Shipment created",
                        "location": "Warehouse",
                        "timestamp": "2025-07-20T10:00:00Z"
                    },
                    {
                        "status": "IN_TRANSIT",
                        "description": "Shipment in transit",
                        "location": "Transit Hub",
                        "timestamp": "2025-07-21T10:00:00Z"
                    }
                ]
            }
            mock_get_service.return_value = mock_service
            
            updated_shipment = self.service.track_shipment(shipment)
            
            self.assertEqual(updated_shipment.status, "IN_TRANSIT")
            self.assertEqual(ShipmentTracking.objects.filter(shipment=shipment).count(), 2)
            mock_service.track_shipment.assert_called_once_with("TRACK123")
    
    def test_calculate_shipping_rate(self):
        """Test calculating shipping rate"""
        package_data = {
            "source_pin_code": "123456",
            "destination_pin_code": "654321",
            "weight": 1.5,
            "payment_method": "PREPAID"
        }
        
        with patch.object(ShippingService, 'get_shipping_partner_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.calculate_shipping_rate.return_value = {
                "rates": [
                    {
                        "courier_name": "Test Courier",
                        "rate": 100.00,
                        "delivery_days": 3
                    }
                ]
            }
            mock_get_service.return_value = mock_service
            
            rates = self.service.calculate_shipping_rate(self.shipping_partner, package_data)
            
            self.assertEqual(len(rates["rates"]), 1)
            self.assertEqual(rates["rates"][0]["rate"], 100.00)
            mock_service.calculate_shipping_rate.assert_called_once_with(package_data)


class ShiprocketServiceTest(TestCase):
    """Tests for the ShiprocketService class"""
    
    def setUp(self):
        self.shipping_partner = ShippingPartner.objects.create(
            name="Shiprocket",
            code="SHIPROCKET",
            partner_type="SHIPROCKET",
            api_key="test_api_key",
            api_secret="test_api_secret",
            base_url="https://api.shiprocket.com",
            configuration={
                "email": "test@example.com",
                "pickup_postcode": "123456",
                "pickup_location": "Primary",
                "channel_id": "12345"
            }
        )
        
        self.service = ShiprocketService(self.shipping_partner)
    
    @patch('requests.post')
    def test_get_auth_token(self, mock_post):
        """Test getting authentication token"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "test_token"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        token = self.service._get_auth_token()
        
        self.assertEqual(token, "test_token")
        mock_post.assert_called_once()
        
        # Test token caching
        token = self.service._get_auth_token()
        self.assertEqual(token, "test_token")
        # Should still be called only once (cached)
        mock_post.assert_called_once()
    
    @patch('requests.get')
    def test_check_serviceability(self, mock_get):
        """Test checking serviceability"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "available_courier_companies": [
                    {"courier_name": "Test Courier", "estimated_delivery_days": 3}
                ],
                "delivery_days": 3
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Mock auth token
        self.service.token = "test_token"
        self.service.token_expiry = timezone.now() + timezone.timedelta(hours=1)
        
        result = self.service.check_serviceability("123456")
        
        self.assertTrue(result["serviceable"])
        self.assertEqual(result["delivery_days"], 3)
        mock_get.assert_called_once()
    
    @patch('requests.post')
    def test_create_order(self, mock_post):
        """Test creating an order"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "order_id": "PARTNER123",
            "shipment_id": "SHIPMENT123",
            "awb_code": "TRACK123",
            "expected_delivery_date": "2025-07-25",
            "shipping_cost": 50.00
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Mock auth token
        self.service.token = "test_token"
        self.service.token_expiry = timezone.now() + timezone.timedelta(hours=1)
        
        order_data = {
            "order_number": "ORD123",
            "order_date": datetime.now(),
            "shipping_address": {
                "name": "Test Customer",
                "address_line_1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "123456",
                "country": "India",
                "phone": "1234567890"
            },
            "billing_address": {
                "name": "Test Customer",
                "address_line_1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "123456",
                "country": "India",
                "phone": "1234567890"
            },
            "items": [
                {
                    "product_name": "Test Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ],
            "total_amount": 100.00,
            "payment_method": "PREPAID"
        }
        
        result = self.service.create_order(order_data)
        
        self.assertEqual(result["partner_order_id"], "PARTNER123")
        self.assertEqual(result["shipment_id"], "SHIPMENT123")
        self.assertEqual(result["tracking_number"], "TRACK123")
        self.assertEqual(result["shipping_cost"], 50.00)
        mock_post.assert_called_once()


class DelhiveryServiceTest(TestCase):
    """Tests for the DelhiveryService class"""
    
    def setUp(self):
        self.shipping_partner = ShippingPartner.objects.create(
            name="Delhivery",
            code="DELHIVERY",
            partner_type="DELHIVERY",
            api_key="test_api_key",
            base_url="https://api.delhivery.com",
            configuration={
                "pickup_location": "Primary",
                "pickup_postcode": "123456",
                "return_address": {
                    "name": "Test Store",
                    "address": "123 Store St",
                    "pin": "123456",
                    "city": "Test City",
                    "state": "Test State",
                    "country": "India",
                    "phone": "1234567890"
                }
            }
        )
        
        self.service = DelhiveryService(self.shipping_partner)
    
    @patch('requests.get')
    def test_check_serviceability(self, mock_get):
        """Test checking serviceability"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "delivery_codes": [
                {
                    "postal_code": "123456",
                    "status": "serviceable"
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = self.service.check_serviceability("123456")
        
        self.assertTrue(result["serviceable"])
        mock_get.assert_called_once()
    
    @patch('requests.post')
    def test_create_order(self, mock_post):
        """Test creating an order"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "packages": [
                {
                    "status": "Success",
                    "ref_id": "PARTNER123",
                    "waybill": "TRACK123"
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        order_data = {
            "order_number": "ORD123",
            "shipping_address": {
                "name": "Test Customer",
                "address_line_1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "123456",
                "country": "India",
                "phone": "1234567890"
            },
            "items": [
                {
                    "product_name": "Test Product",
                    "quantity": 1,
                    "unit_price": 100.00
                }
            ],
            "total_amount": 100.00,
            "payment_method": "PREPAID",
            "package_dimensions": {
                "weight": 1.5,
                "length": 10,
                "breadth": 10,
                "height": 5
            }
        }
        
        result = self.service.create_order(order_data)
        
        self.assertEqual(result["partner_order_id"], "PARTNER123")
        self.assertEqual(result["tracking_number"], "TRACK123")
        self.assertEqual(result["status"], "PROCESSING")
        mock_post.assert_called_once()
    
    def test_generate_label(self):
        """Test generating a shipping label"""
        label_url = self.service.generate_label("TRACK123")
        expected_url = f"{self.shipping_partner.base_url}/api/p/printwaybill/?wbns=TRACK123&token={self.shipping_partner.api_key}"
        self.assertEqual(label_url, expected_url)
    
    @patch('requests.get')
    def test_track_shipment(self, mock_get):
        """Test tracking a shipment"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ShipmentData": [
                {
                    "Status": "In Transit",
                    "ExpectedDeliveryDate": "2025-07-25",
                    "Scans": [
                        {
                            "ScanDetail": {
                                "Scan": "Pickup Complete",
                                "Instructions": "Shipment picked up",
                                "ScannedLocation": "Warehouse",
                                "ScanDateTime": "2025-07-20T10:00:00"
                            }
                        },
                        {
                            "ScanDetail": {
                                "Scan": "In Transit",
                                "Instructions": "Shipment in transit",
                                "ScannedLocation": "Transit Hub",
                                "ScanDateTime": "2025-07-21T10:00:00"
                            }
                        }
                    ]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = self.service.track_shipment("TRACK123")
        
        self.assertEqual(result["status"], "IN_TRANSIT")
        self.assertEqual(result["estimated_delivery_date"], "2025-07-25")
        self.assertEqual(len(result["tracking_history"]), 2)
        mock_get.assert_called_once()