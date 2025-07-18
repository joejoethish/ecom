import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import ShippingPartner, ServiceableArea, Shipment, ShipmentTracking

logger = logging.getLogger(__name__)

class ShippingException(Exception):
    """Base exception for shipping-related errors"""
    pass


class ShippingPartnerService:
    """Base service class for shipping partner integrations"""
    
    def __init__(self, shipping_partner: ShippingPartner):
        self.shipping_partner = shipping_partner
        self.base_url = shipping_partner.base_url
        self.api_key = shipping_partner.api_key
        self.api_secret = shipping_partner.api_secret
        self.configuration = shipping_partner.configuration
        
    def check_serviceability(self, pin_code: str) -> Dict[str, Any]:
        """
        Check if a pin code is serviceable
        
        Args:
            pin_code: The pin code to check
            
        Returns:
            Dict with serviceability information
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a shipping order with the partner
        
        Args:
            order_data: Order information
            
        Returns:
            Dict with created order information
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def generate_label(self, shipment_id: str) -> str:
        """
        Generate a shipping label
        
        Args:
            shipment_id: The shipment ID
            
        Returns:
            URL to the shipping label
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """
        Track a shipment
        
        Args:
            tracking_number: The tracking number
            
        Returns:
            Dict with tracking information
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def calculate_shipping_rate(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate shipping rate
        
        Args:
            package_data: Package information including weight, dimensions, source, destination
            
        Returns:
            Dict with rate information
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def cancel_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """
        Cancel a shipment
        
        Args:
            shipment_id: The shipment ID
            
        Returns:
            Dict with cancellation information
        """
        raise NotImplementedError("Subclasses must implement this method")

class ShiprocketService(ShippingPartnerService):
    """Service for Shiprocket integration"""
    
    def __init__(self, shipping_partner: ShippingPartner):
        super().__init__(shipping_partner)
        self.token = None
        self.token_expiry = None
    
    def _get_auth_token(self) -> str:
        """
        Get authentication token from Shiprocket
        
        Returns:
            Authentication token
        """
        # Check if we have a valid token
        if self.token and self.token_expiry and self.token_expiry > timezone.now():
            return self.token
        
        # Get new token
        url = f"{self.base_url}/auth/login"
        payload = {
            "email": self.configuration.get("email"),
            "password": self.api_secret
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Store token and expiry
            self.token = data.get("token")
            # Token typically expires in 24 hours
            self.token_expiry = timezone.now() + timedelta(hours=23)
            
            return self.token
        except requests.exceptions.RequestException as e:
            logger.error(f"Shiprocket authentication error: {str(e)}")
            raise ShippingException(f"Failed to authenticate with Shiprocket: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Shiprocket API requests
        
        Returns:
            Dict with headers
        """
        token = self._get_auth_token()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    def check_serviceability(self, pin_code: str) -> Dict[str, Any]:
        """
        Check if a pin code is serviceable by Shiprocket
        
        Args:
            pin_code: The pin code to check
            
        Returns:
            Dict with serviceability information
        """
        url = f"{self.base_url}/courier/serviceability"
        params = {
            "pickup_postcode": self.configuration.get("pickup_postcode", ""),
            "delivery_postcode": pin_code,
            "weight": 1,  # Default weight in kg
            "cod": 0  # Default to prepaid
        }
        
        try:
            headers = self._get_headers()
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process and return serviceability data
            return {
                "serviceable": len(data.get("data", {}).get("available_courier_companies", [])) > 0,
                "couriers": data.get("data", {}).get("available_courier_companies", []),
                "delivery_days": data.get("data", {}).get("delivery_days", None),
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Shiprocket serviceability check error: {str(e)}")
            raise ShippingException(f"Failed to check serviceability with Shiprocket: {str(e)}")
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a shipping order with Shiprocket
        
        Args:
            order_data: Order information
            
        Returns:
            Dict with created order information
        """
        url = f"{self.base_url}/orders/create/adhoc"
        
        # Transform order_data to Shiprocket format
        shiprocket_order = {
            "order_id": order_data.get("order_number"),
            "order_date": order_data.get("order_date").strftime("%Y-%m-%d %H:%M"),
            "pickup_location": self.configuration.get("pickup_location", "Primary"),
            "channel_id": self.configuration.get("channel_id"),
            "comment": order_data.get("notes", ""),
            "billing_customer_name": order_data.get("billing_address", {}).get("name", ""),
            "billing_last_name": "",
            "billing_address": order_data.get("billing_address", {}).get("address_line_1", ""),
            "billing_address_2": order_data.get("billing_address", {}).get("address_line_2", ""),
            "billing_city": order_data.get("billing_address", {}).get("city", ""),
            "billing_pincode": order_data.get("billing_address", {}).get("postal_code", ""),
            "billing_state": order_data.get("billing_address", {}).get("state", ""),
            "billing_country": order_data.get("billing_address", {}).get("country", "India"),
            "billing_email": order_data.get("billing_address", {}).get("email", ""),
            "billing_phone": order_data.get("billing_address", {}).get("phone", ""),
            "shipping_is_billing": order_data.get("shipping_is_billing", False),
            "shipping_customer_name": order_data.get("shipping_address", {}).get("name", ""),
            "shipping_last_name": "",
            "shipping_address": order_data.get("shipping_address", {}).get("address_line_1", ""),
            "shipping_address_2": order_data.get("shipping_address", {}).get("address_line_2", ""),
            "shipping_city": order_data.get("shipping_address", {}).get("city", ""),
            "shipping_pincode": order_data.get("shipping_address", {}).get("postal_code", ""),
            "shipping_state": order_data.get("shipping_address", {}).get("state", ""),
            "shipping_country": order_data.get("shipping_address", {}).get("country", "India"),
            "shipping_email": order_data.get("shipping_address", {}).get("email", ""),
            "shipping_phone": order_data.get("shipping_address", {}).get("phone", ""),
            "order_items": [],
            "payment_method": "Prepaid" if order_data.get("payment_method") != "COD" else "COD",
            "sub_total": float(order_data.get("total_amount", 0)),
            "length": order_data.get("package_dimensions", {}).get("length", 10),
            "breadth": order_data.get("package_dimensions", {}).get("breadth", 10),
            "height": order_data.get("package_dimensions", {}).get("height", 10),
            "weight": order_data.get("package_dimensions", {}).get("weight", 0.5),
        }
        
        # Add order items
        for item in order_data.get("items", []):
            shiprocket_order["order_items"].append({
                "name": item.get("product_name", ""),
                "sku": item.get("sku", ""),
                "units": item.get("quantity", 1),
                "selling_price": float(item.get("unit_price", 0)),
                "discount": float(item.get("discount", 0)),
                "tax": float(item.get("tax", 0)),
                "hsn": item.get("hsn", "")
            })
        
        try:
            headers = self._get_headers()
            response = requests.post(url, headers=headers, json=shiprocket_order)
            response.raise_for_status()
            data = response.json()
            
            # Process and return order data
            return {
                "partner_order_id": data.get("order_id"),
                "shipment_id": data.get("shipment_id"),
                "status": "PROCESSING",
                "tracking_number": data.get("awb_code"),
                "estimated_delivery_date": data.get("expected_delivery_date"),
                "shipping_cost": data.get("shipping_cost"),
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Shiprocket order creation error: {str(e)}")
            raise ShippingException(f"Failed to create order with Shiprocket: {str(e)}")
    
    def generate_label(self, shipment_id: str) -> str:
        """
        Generate a shipping label with Shiprocket
        
        Args:
            shipment_id: The shipment ID
            
        Returns:
            URL to the shipping label
        """
        url = f"{self.base_url}/courier/generate/label"
        payload = {
            "shipment_id": [shipment_id]
        }
        
        try:
            headers = self._get_headers()
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Return label URL
            return data.get("label_url", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"Shiprocket label generation error: {str(e)}")
            raise ShippingException(f"Failed to generate label with Shiprocket: {str(e)}")
    
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """
        Track a shipment with Shiprocket
        
        Args:
            tracking_number: The tracking number (AWB code)
            
        Returns:
            Dict with tracking information
        """
        url = f"{self.base_url}/courier/track"
        params = {
            "awb": tracking_number
        }
        
        try:
            headers = self._get_headers()
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process tracking data
            tracking_data = data.get("tracking_data", {})
            shipment_track = tracking_data.get("shipment_track", [])
            
            # Map Shiprocket status to our status
            status_mapping = {
                "PICKUP SCHEDULED": "PROCESSING",
                "PICKUP GENERATED": "PROCESSING",
                "AWB ASSIGNED": "PROCESSING",
                "LABEL GENERATED": "PROCESSING",
                "PICKUP COMPLETE": "SHIPPED",
                "IN TRANSIT": "IN_TRANSIT",
                "OUT FOR DELIVERY": "OUT_FOR_DELIVERY",
                "DELIVERED": "DELIVERED",
                "CANCELLED": "CANCELLED",
                "RTO INITIATED": "RETURNED",
                "RTO DELIVERED": "RETURNED",
                "FAILED DELIVERY": "FAILED_DELIVERY"
            }
            
            current_status = "PENDING"
            if tracking_data.get("current_status"):
                current_status = status_mapping.get(
                    tracking_data.get("current_status").upper(), 
                    "IN_TRANSIT"
                )
            
            # Extract tracking history
            tracking_history = []
            for track in shipment_track:
                status = status_mapping.get(track.get("status", "").upper(), "IN_TRANSIT")
                tracking_history.append({
                    "status": status,
                    "description": track.get("status", ""),
                    "location": track.get("location", ""),
                    "timestamp": track.get("date", ""),
                    "raw_response": track
                })
            
            return {
                "status": current_status,
                "estimated_delivery_date": tracking_data.get("etd"),
                "tracking_history": tracking_history,
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Shiprocket tracking error: {str(e)}")
            raise ShippingException(f"Failed to track shipment with Shiprocket: {str(e)}")
    
    def calculate_shipping_rate(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate shipping rate with Shiprocket
        
        Args:
            package_data: Package information including weight, dimensions, source, destination
            
        Returns:
            Dict with rate information
        """
        url = f"{self.base_url}/courier/serviceability"
        params = {
            "pickup_postcode": package_data.get("source_pin_code", self.configuration.get("pickup_postcode", "")),
            "delivery_postcode": package_data.get("destination_pin_code", ""),
            "weight": package_data.get("weight", 0.5),
            "cod": 1 if package_data.get("payment_method") == "COD" else 0
        }
        
        # Add dimensions if available
        if package_data.get("length") and package_data.get("breadth") and package_data.get("height"):
            params["length"] = package_data.get("length")
            params["breadth"] = package_data.get("breadth")
            params["height"] = package_data.get("height")
        
        try:
            headers = self._get_headers()
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process and return rate data
            available_couriers = data.get("data", {}).get("available_courier_companies", [])
            rates = []
            
            for courier in available_couriers:
                rates.append({
                    "courier_name": courier.get("courier_name"),
                    "courier_id": courier.get("courier_company_id"),
                    "rate": courier.get("rate"),
                    "delivery_days": courier.get("estimated_delivery_days"),
                    "is_cod_available": courier.get("is_cod_available") == 1
                })
            
            return {
                "rates": rates,
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Shiprocket rate calculation error: {str(e)}")
            raise ShippingException(f"Failed to calculate shipping rate with Shiprocket: {str(e)}")
    
    def cancel_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """
        Cancel a shipment with Shiprocket
        
        Args:
            shipment_id: The shipment ID
            
        Returns:
            Dict with cancellation information
        """
        url = f"{self.base_url}/orders/cancel"
        payload = {
            "ids": [int(shipment_id)]
        }
        
        try:
            headers = self._get_headers()
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": data.get("status") == 200,
                "message": data.get("message", ""),
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Shiprocket cancellation error: {str(e)}")
            raise ShippingException(f"Failed to cancel shipment with Shiprocket: {str(e)}")


class DelhiveryService(ShippingPartnerService):
    """Service for Delhivery integration"""
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Delhivery API requests
        
        Returns:
            Dict with headers
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
    
    def check_serviceability(self, pin_code: str) -> Dict[str, Any]:
        """
        Check if a pin code is serviceable by Delhivery
        
        Args:
            pin_code: The pin code to check
            
        Returns:
            Dict with serviceability information
        """
        url = f"{self.base_url}/c/api/pin-codes/json/"
        params = {
            "token": self.api_key,
            "filter_codes": pin_code
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process and return serviceability data
            delivery_codes = data.get("delivery_codes", [])
            serviceable = False
            
            if delivery_codes:
                for code in delivery_codes:
                    if code.get("postal_code") == pin_code and code.get("status") == "serviceable":
                        serviceable = True
                        break
            
            return {
                "serviceable": serviceable,
                "delivery_days": None,  # Delhivery doesn't provide this in the serviceability API
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Delhivery serviceability check error: {str(e)}")
            raise ShippingException(f"Failed to check serviceability with Delhivery: {str(e)}")
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a shipping order with Delhivery
        
        Args:
            order_data: Order information
            
        Returns:
            Dict with created order information
        """
        url = f"{self.base_url}/api/cmu/create.json"
        
        # Format address
        shipping_address = order_data.get("shipping_address", {})
        address = f"{shipping_address.get('address_line_1', '')}"
        if shipping_address.get('address_line_2'):
            address += f", {shipping_address.get('address_line_2')}"
        
        # Transform order_data to Delhivery format
        shipment = {
            "format": "json",
            "data": {
                "shipments": [
                    {
                        "name": shipping_address.get("name", ""),
                        "add": address,
                        "pin": shipping_address.get("postal_code", ""),
                        "city": shipping_address.get("city", ""),
                        "state": shipping_address.get("state", ""),
                        "country": shipping_address.get("country", "India"),
                        "phone": shipping_address.get("phone", ""),
                        "order": order_data.get("order_number", ""),
                        "payment_mode": "COD" if order_data.get("payment_method") == "COD" else "Prepaid",
                        "cod_amount": str(order_data.get("total_amount", "0")) if order_data.get("payment_method") == "COD" else "0",
                        "total_amount": str(order_data.get("total_amount", "0")),
                        "weight": str(order_data.get("package_dimensions", {}).get("weight", "0.5")),
                        "shipment_length": str(order_data.get("package_dimensions", {}).get("length", "10")),
                        "shipment_width": str(order_data.get("package_dimensions", {}).get("breadth", "10")),
                        "shipment_height": str(order_data.get("package_dimensions", {}).get("height", "10")),
                        "product_to_be_shipped": ", ".join([item.get("product_name", "") for item in order_data.get("items", [])])
                    }
                ]
            }
        }
        
        # Add pickup location
        pickup_location = self.configuration.get("pickup_location")
        if pickup_location:
            shipment["pickup_location"] = pickup_location
        
        # Add return address if available
        return_address = self.configuration.get("return_address")
        if return_address:
            shipment["data"]["shipments"][0]["return_add"] = return_address.get("address", "")
            shipment["data"]["shipments"][0]["return_pin"] = return_address.get("pin", "")
            shipment["data"]["shipments"][0]["return_city"] = return_address.get("city", "")
            shipment["data"]["shipments"][0]["return_state"] = return_address.get("state", "")
            shipment["data"]["shipments"][0]["return_country"] = return_address.get("country", "India")
            shipment["data"]["shipments"][0]["return_phone"] = return_address.get("phone", "")
            shipment["data"]["shipments"][0]["return_name"] = return_address.get("name", "")
        
        try:
            headers = self._get_headers()
            response = requests.post(url, headers=headers, json=shipment)
            response.raise_for_status()
            data = response.json()
            
            # Check for errors in response
            if data.get("packages", []) and data["packages"][0].get("status") == "Success":
                package = data["packages"][0]
                return {
                    "partner_order_id": package.get("ref_id"),
                    "shipment_id": package.get("waybill"),
                    "status": "PROCESSING",
                    "tracking_number": package.get("waybill"),
                    "estimated_delivery_date": None,  # Delhivery doesn't provide this in the creation API
                    "raw_response": data
                }
            else:
                error_msg = data.get("error", "Unknown error")
                logger.error(f"Delhivery order creation error: {error_msg}")
                raise ShippingException(f"Failed to create order with Delhivery: {error_msg}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Delhivery order creation error: {str(e)}")
            raise ShippingException(f"Failed to create order with Delhivery: {str(e)}")
    
    def generate_label(self, shipment_id: str) -> str:
        """
        Generate a shipping label with Delhivery
        
        Args:
            shipment_id: The shipment ID (waybill)
            
        Returns:
            URL to the shipping label
        """
        # Delhivery provides direct URL for label generation
        return f"{self.base_url}/api/p/printwaybill/?wbns={shipment_id}&token={self.api_key}"
    
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """
        Track a shipment with Delhivery
        
        Args:
            tracking_number: The tracking number (waybill)
            
        Returns:
            Dict with tracking information
        """
        url = f"{self.base_url}/api/v1/packages/json/"
        params = {
            "token": self.api_key,
            "waybill": tracking_number
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process tracking data
            shipment_data = data.get("ShipmentData", [])
            if not shipment_data:
                raise ShippingException(f"No tracking data found for {tracking_number}")
            
            shipment = shipment_data[0]
            scans = shipment.get("Scans", [])
            
            # Map Delhivery status to our status
            status_mapping = {
                "Pickup Scheduled": "PROCESSING",
                "Pickup Generated": "PROCESSING",
                "Pickup Assigned": "PROCESSING",
                "Pickup Complete": "SHIPPED",
                "In Transit": "IN_TRANSIT",
                "Out for Delivery": "OUT_FOR_DELIVERY",
                "Delivered": "DELIVERED",
                "Cancelled": "CANCELLED",
                "RTO Initiated": "RETURNED",
                "RTO Delivered": "RETURNED",
                "Failed Delivery": "FAILED_DELIVERY"
            }
            
            # Get current status
            current_status = "PENDING"
            if shipment.get("Status"):
                current_status = status_mapping.get(shipment.get("Status"), "IN_TRANSIT")
            
            # Extract tracking history
            tracking_history = []
            for scan in scans:
                status = status_mapping.get(scan.get("ScanDetail", {}).get("Scan", ""), "IN_TRANSIT")
                scan_time = scan.get("ScanDetail", {}).get("ScanDateTime", "")
                
                tracking_history.append({
                    "status": status,
                    "description": scan.get("ScanDetail", {}).get("Instructions", ""),
                    "location": scan.get("ScanDetail", {}).get("ScannedLocation", ""),
                    "timestamp": scan_time,
                    "raw_response": scan
                })
            
            return {
                "status": current_status,
                "estimated_delivery_date": shipment.get("ExpectedDeliveryDate"),
                "tracking_history": tracking_history,
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Delhivery tracking error: {str(e)}")
            raise ShippingException(f"Failed to track shipment with Delhivery: {str(e)}")
    
    def calculate_shipping_rate(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate shipping rate with Delhivery
        
        Args:
            package_data: Package information including weight, dimensions, source, destination
            
        Returns:
            Dict with rate information
        """
        url = f"{self.base_url}/api/kinko/v1/invoice/charges/.json"
        
        payload = {
            "pickup_pincode": package_data.get("source_pin_code", self.configuration.get("pickup_postcode", "")),
            "delivery_pincode": package_data.get("destination_pin_code", ""),
            "cod": package_data.get("payment_method") == "COD",
            "weight": package_data.get("weight", 0.5)
        }
        
        # Add dimensions if available
        if package_data.get("length") and package_data.get("breadth") and package_data.get("height"):
            payload["md"] = "S"  # Surface
            payload["d"] = f"{package_data.get('length')}x{package_data.get('breadth')}x{package_data.get('height')}"
        
        try:
            headers = self._get_headers()
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Process and return rate data
            if data.get("success"):
                return {
                    "rates": [{
                        "courier_name": "Delhivery",
                        "rate": data.get("total_amount"),
                        "delivery_days": data.get("expected_delivery_days"),
                        "is_cod_available": True
                    }],
                    "raw_response": data
                }
            else:
                error_msg = data.get("error", "Unknown error")
                logger.error(f"Delhivery rate calculation error: {error_msg}")
                raise ShippingException(f"Failed to calculate shipping rate with Delhivery: {error_msg}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Delhivery rate calculation error: {str(e)}")
            raise ShippingException(f"Failed to calculate shipping rate with Delhivery: {str(e)}")
    
    def cancel_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """
        Cancel a shipment with Delhivery
        
        Args:
            shipment_id: The shipment ID (waybill)
            
        Returns:
            Dict with cancellation information
        """
        url = f"{self.base_url}/api/p/edit"
        params = {
            "token": self.api_key,
            "waybill": shipment_id,
            "cancellation": "true"
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": data.get("success", False),
                "message": data.get("message", ""),
                "raw_response": data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Delhivery cancellation error: {str(e)}")
            raise ShippingException(f"Failed to cancel shipment with Delhivery: {str(e)}")


class ShippingService:
    """Main service for shipping operations"""
    
    def get_shipping_partner_service(self, shipping_partner: ShippingPartner) -> ShippingPartnerService:
        """
        Get the appropriate shipping partner service based on partner type
        
        Args:
            shipping_partner: The shipping partner
            
        Returns:
            ShippingPartnerService instance
        """
        if shipping_partner.partner_type == "SHIPROCKET":
            return ShiprocketService(shipping_partner)
        elif shipping_partner.partner_type == "DELHIVERY":
            return DelhiveryService(shipping_partner)
        else:
            raise ShippingException(f"Unsupported shipping partner type: {shipping_partner.partner_type}")
    
    def check_serviceability(self, pin_code: str, shipping_partner: ShippingPartner = None) -> Dict[str, Any]:
        """
        Check if a pin code is serviceable
        
        Args:
            pin_code: The pin code to check
            shipping_partner: Optional specific shipping partner to check with
            
        Returns:
            Dict with serviceability information
        """
        if shipping_partner:
            # Check with specific partner
            service = self.get_shipping_partner_service(shipping_partner)
            return service.check_serviceability(pin_code)
        else:
            # Check with all active partners
            partners = ShippingPartner.objects.filter(is_active=True)
            results = {}
            
            for partner in partners:
                try:
                    service = self.get_shipping_partner_service(partner)
                    results[partner.code] = service.check_serviceability(pin_code)
                except Exception as e:
                    logger.error(f"Error checking serviceability with {partner.name}: {str(e)}")
                    results[partner.code] = {"serviceable": False, "error": str(e)}
            
            # Check if pin code is in our database
            serviceable_areas = ServiceableArea.objects.filter(
                pin_code=pin_code,
                is_active=True
            )
            
            # Determine overall serviceability
            serviceable = len(serviceable_areas) > 0 or any(r.get("serviceable", False) for r in results.values())
            
            return {
                "serviceable": serviceable,
                "partner_results": results,
                "delivery_days": min([
                    area.max_delivery_days for area in serviceable_areas
                ]) if serviceable_areas else None
            }
    
    def create_shipment(self, order, shipping_partner: ShippingPartner, order_data: Dict[str, Any]) -> Shipment:
        """
        Create a shipment for an order
        
        Args:
            order: The order object
            shipping_partner: The shipping partner to use
            order_data: Order information
            
        Returns:
            Created Shipment object
        """
        service = self.get_shipping_partner_service(shipping_partner)
        
        # Create shipment with partner
        result = service.create_order(order_data)
        
        # Create shipment record
        shipment = Shipment.objects.create(
            order=order,
            shipping_partner=shipping_partner,
            tracking_number=result.get("tracking_number"),
            shipping_label_url=result.get("shipping_label_url", ""),
            partner_order_id=result.get("partner_order_id"),
            partner_shipment_id=result.get("shipment_id"),
            status=result.get("status"),
            estimated_delivery_date=result.get("estimated_delivery_date"),
            shipping_address=order_data.get("shipping_address"),
            weight=order_data.get("package_dimensions", {}).get("weight"),
            dimensions=order_data.get("package_dimensions", {}),
            shipping_cost=result.get("shipping_cost", 0.00)
        )
        
        return shipment
    
    def track_shipment(self, shipment: Shipment) -> Shipment:
        """
        Track a shipment and update its status
        
        Args:
            shipment: The shipment to track
            
        Returns:
            Updated Shipment object
        """
        service = self.get_shipping_partner_service(shipment.shipping_partner)
        
        # Get tracking information
        result = service.track_shipment(shipment.tracking_number)
        
        # Update shipment status
        if result.get("status") != shipment.status:
            shipment.status = result.get("status")
            
            # Update timestamps based on status
            if shipment.status == "SHIPPED" and not shipment.shipped_at:
                shipment.shipped_at = timezone.now()
            elif shipment.status == "DELIVERED" and not shipment.delivered_at:
                shipment.delivered_at = timezone.now()
                
            shipment.save()
        
        # Create tracking entries
        for track in result.get("tracking_history", []):
            # Parse timestamp
            timestamp = parse_datetime(track.get("timestamp"))
            if not timestamp:
                timestamp = timezone.now()
            
            # Check if this tracking entry already exists
            existing = ShipmentTracking.objects.filter(
                shipment=shipment,
                status=track.get("status"),
                description=track.get("description"),
                location=track.get("location")
            ).exists()
            
            if not existing:
                ShipmentTracking.objects.create(
                    shipment=shipment,
                    status=track.get("status"),
                    description=track.get("description"),
                    location=track.get("location"),
                    timestamp=timestamp,
                    raw_response=track.get("raw_response", {})
                )
        
        return shipment
    
    def calculate_shipping_rate(self, shipping_partner: ShippingPartner, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate shipping rate
        
        Args:
            shipping_partner: The shipping partner to use
            package_data: Package information
            
        Returns:
            Dict with rate information
        """
        service = self.get_shipping_partner_service(shipping_partner)
        return service.calculate_shipping_rate(package_data)
    
    def cancel_shipment(self, shipment: Shipment) -> Dict[str, Any]:
        """
        Cancel a shipment
        
        Args:
            shipment: The shipment to cancel
            
        Returns:
            Dict with cancellation information
        """
        service = self.get_shipping_partner_service(shipment.shipping_partner)
        
        # Cancel with partner
        result = service.cancel_shipment(shipment.partner_shipment_id)
        
        if result.get("success"):
            # Update shipment status
            shipment.status = "CANCELLED"
            shipment.save()
            
            # Create tracking entry
            ShipmentTracking.objects.create(
                shipment=shipment,
                status="CANCELLED",
                description="Shipment cancelled",
                location="",
                timestamp=timezone.now(),
                raw_response=result.get("raw_response", {})
            )
        
        return result