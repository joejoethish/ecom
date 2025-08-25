"""
Integration tests for API validation engine.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.debugging.api_validation import (
    APIDiscoveryService,
    APIValidationService,
    validate_all_apis,
    check_api_health
)

User = get_user_model()


class APIValidationIntegrationTest(TestCase):
    """Integration tests for API validation functionality."""
    
    def test_discovery_service_initialization(self):
        """Test that discovery service can be initialized."""
        service = APIDiscoveryService()
        self.assertIsNotNone(service)
        self.assertEqual(len(service.discovered_endpoints), 0)
    
    def test_validation_service_initialization(self):
        """Test that validation service can be initialized."""
        service = APIValidationService()
        self.assertIsNotNone(service)
        self.assertIsNone(service.test_user)
        self.assertIsNone(service.jwt_token)
    
    def test_validation_service_setup_user(self):
        """Test that validation service can set up test user."""
        service = APIValidationService()
        service.setup_test_user()
        
        self.assertIsNotNone(service.test_user)
        self.assertIsNotNone(service.jwt_token)
        self.assertEqual(service.test_user.username, 'api_test_user')
        
        # Verify user exists in database
        user_exists = User.objects.filter(username='api_test_user').exists()
        self.assertTrue(user_exists)
    
    def test_url_pattern_conversion(self):
        """Test URL pattern conversion to testable URLs."""
        service = APIValidationService()
        
        # Test various URL patterns
        test_cases = [
            ('/api/users/<int:user_id>/', '/api/users/1/'),
            ('/api/products/<str:category>/', '/api/products/test/'),
            ('/api/posts/<slug:slug>/', '/api/posts/test-slug/'),
            ('/api/simple/', '/api/simple/'),
        ]
        
        for input_url, expected_url in test_cases:
            result = service._prepare_test_url(input_url)
            self.assertEqual(result, expected_url)
    
    def test_payload_generation(self):
        """Test payload generation from schema."""
        service = APIValidationService()
        
        schema = {
            'name': {'type': 'string', 'required': True},
            'email': {'type': 'string', 'required': True},
            'age': {'type': 'integer', 'required': False},
            'is_active': {'type': 'boolean', 'required': True}
        }
        
        payload = service._generate_test_payload(schema)
        
        # Check required fields are present
        self.assertIn('name', payload)
        self.assertIn('email', payload)
        self.assertIn('is_active', payload)
        
        # Check optional fields are not present
        self.assertNotIn('age', payload)
        
        # Check data types
        self.assertIsInstance(payload['name'], str)
        self.assertIsInstance(payload['email'], str)
        self.assertIsInstance(payload['is_active'], bool)
    
    def test_health_check_function(self):
        """Test API health check functionality."""
        result = check_api_health()
        
        # Check result structure
        self.assertIn('timestamp', result)
        self.assertIn('results', result)
        self.assertIn('overall_health', result)
        
        # Check that results is a list
        self.assertIsInstance(result['results'], list)
        
        # Check that overall health is a valid status
        self.assertIn(result['overall_health'], ['healthy', 'degraded'])
    
    def test_field_type_mapping(self):
        """Test field type mapping functionality."""
        from rest_framework import serializers
        
        service = APIDiscoveryService()
        
        # Test various field types
        test_cases = [
            (serializers.CharField(), 'string'),
            (serializers.EmailField(), 'string'),
            (serializers.IntegerField(), 'integer'),
            (serializers.FloatField(), 'number'),
            (serializers.BooleanField(), 'boolean'),
            (serializers.DateField(), 'string'),
            (serializers.JSONField(), 'object'),
            (serializers.ListField(), 'array'),
        ]
        
        for field, expected_type in test_cases:
            result = service._get_field_type(field)
            self.assertEqual(result, expected_type)
    
    def test_schema_generation(self):
        """Test schema generation from serializer fields."""
        from rest_framework import serializers
        
        class TestSerializer(serializers.Serializer):
            name = serializers.CharField(max_length=100, required=True)
            email = serializers.EmailField(required=True)
            age = serializers.IntegerField(required=False)
            is_active = serializers.BooleanField(default=True)
        
        service = APIDiscoveryService()
        serializer = TestSerializer()
        schema = service._generate_schema_from_serializer(serializer)
        
        # Check all fields are present
        expected_fields = ['name', 'email', 'age', 'is_active']
        for field in expected_fields:
            self.assertIn(field, schema)
        
        # Check field properties
        self.assertEqual(schema['name']['type'], 'string')
        self.assertTrue(schema['name']['required'])
        self.assertEqual(schema['name']['max_length'], 100)
        
        self.assertEqual(schema['email']['type'], 'string')
        self.assertTrue(schema['email']['required'])
        
        self.assertEqual(schema['age']['type'], 'integer')
        self.assertFalse(schema['age']['required'])
        
        self.assertEqual(schema['is_active']['type'], 'boolean')
        self.assertFalse(schema['is_active']['required'])  # Default value makes it not required