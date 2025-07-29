"""
Simple tests for API versioning functionality.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status


class SimpleAPIVersioningTestCase(TestCase):
    """Simple test case for API versioning functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_api_version_headers(self):
        """Test API version headers are present in responses."""
        # Test v1 endpoint
        response_v1 = self.client.get('/api/v1/products/')
        self.assertEqual(response_v1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v1['X-API-Version'], 'v1')
        self.assertIn('X-API-Supported-Versions', response_v1)
        
        # Test v2 endpoint
        response_v2 = self.client.get('/api/v2/products/')
        self.assertEqual(response_v2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_v2['X-API-Version'], 'v2')
        self.assertIn('X-API-Supported-Versions', response_v2)

    def test_api_version_urls(self):
        """Test API version URLs are properly configured."""
        # Test that both v1 and v2 endpoints exist
        endpoints = [
            '/api/v1/products/',
            '/api/v2/products/',
            '/api/v1/auth/login/',
            '/api/v2/auth/login/',
            '/api/v1/orders/',
            '/api/v2/orders/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])
            
    def test_version_specific_endpoints(self):
        """Test version-specific endpoints."""
        # Test v2-only endpoint (trending products)
        response_v2 = self.client.get('/api/v2/products/trending/')
        self.assertNotEqual(response_v2.status_code, status.HTTP_404_NOT_FOUND)
        
        # Same endpoint should not exist in v1
        response_v1 = self.client.get('/api/v1/products/trending/')
        self.assertEqual(response_v1.status_code, status.HTTP_404_NOT_FOUND)