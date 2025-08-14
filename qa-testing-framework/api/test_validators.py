"""
Unit tests for API Validators

Tests the validation utilities for API responses including
schema validation, security validation, and performance validation.
"""

import pytest
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.validators import (
    ValidationResult, SchemaValidator, ResponseValidator, 
    SecurityValidator, PerformanceValidator, APIValidator
)
from api.client import APIResponse


class TestValidationResult:
    """Test ValidationResult class"""
    
    def test_validation_result_creation(self):
        """Test ValidationResult object creation"""
        result = ValidationResult(True, [], [], [])
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.info) == 0
    
    def test_add_error(self):
        """Test adding error messages"""
        result = ValidationResult(True, [], [], [])
        
        result.add_error("Test error")
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"
    
    def test_add_warning(self):
        """Test adding warning messages"""
        result = ValidationResult(True, [], [], [])
        
        result.add_warning("Test warning")
        
        assert result.is_valid  # Warnings don't affect validity
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"
    
    def test_add_info(self):
        """Test adding info messages"""
        result = ValidationResult(True, [], [], [])
        
        result.add_info("Test info")
        
        assert result.is_valid
        assert len(result.info) == 1
        assert result.info[0] == "Test info"
    
    def test_merge_results(self):
        """Test merging validation results"""
        result1 = ValidationResult(True, [], [], [])
        result1.add_warning("Warning 1")
        
        result2 = ValidationResult(False, ["Error 1"], ["Warning 2"], ["Info 1"])
        
        result1.merge(result2)
        
        assert not result1.is_valid
        assert len(result1.errors) == 1
        assert len(result1.warnings) == 2
        assert len(result1.info) == 1


class TestSchemaValidator:
    """Test SchemaValidator class"""
    
    def test_validate_user_schema_valid(self):
        """Test valid user schema validation"""
        user_data = {
            'id': 1,
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'is_active': True,
            'date_joined': '2023-01-01T00:00:00Z'
        }
        
        result = SchemaValidator.validate_user_schema(user_data)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_user_schema_missing_fields(self):
        """Test user schema validation with missing required fields"""
        user_data = {
            'id': 1,
            'email': 'test@example.com'
            # Missing first_name and last_name
        }
        
        result = SchemaValidator.validate_user_schema(user_data)
        
        assert not result.is_valid
        assert len(result.errors) >= 2  # Missing first_name and last_name
    
    def test_validate_user_schema_invalid_email(self):
        """Test user schema validation with invalid email"""
        user_data = {
            'id': 1,
            'email': 'invalid-email',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        result = SchemaValidator.validate_user_schema(user_data)
        
        assert not result.is_valid
        assert any('email' in error for error in result.errors)
    
    def test_validate_product_schema_valid(self):
        """Test valid product schema validation"""
        product_data = {
            'id': 1,
            'name': 'Test Product',
            'price': 29.99,
            'category': 'Electronics',
            'description': 'A test product',
            'stock_quantity': 100,
            'is_active': True,
            'images': ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']
        }
        
        result = SchemaValidator.validate_product_schema(product_data)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_product_schema_negative_price(self):
        """Test product schema validation with negative price"""
        product_data = {
            'id': 1,
            'name': 'Test Product',
            'price': -10.0,
            'category': 'Electronics'
        }
        
        result = SchemaValidator.validate_product_schema(product_data)
        
        assert not result.is_valid
        assert any('price' in error and 'negative' in error for error in result.errors)
    
    def test_validate_order_schema_valid(self):
        """Test valid order schema validation"""
        order_data = {
            'id': 1,
            'user': 123,
            'items': [
                {
                    'product': 1,
                    'quantity': 2,
                    'price': 29.99
                }
            ],
            'total_amount': 59.98,
            'status': 'confirmed'
        }
        
        result = SchemaValidator.validate_order_schema(order_data)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_order_schema_empty_items(self):
        """Test order schema validation with empty items"""
        order_data = {
            'id': 1,
            'user': 123,
            'items': [],
            'total_amount': 0.0,
            'status': 'pending'
        }
        
        result = SchemaValidator.validate_order_schema(order_data)
        
        assert not result.is_valid
        assert any('items' in error and 'empty' in error for error in result.errors)
    
    def test_validate_pagination_schema(self):
        """Test pagination schema validation"""
        pagination_data = {
            'count': 100,
            'next': 'http://example.com/api/next',
            'previous': None,
            'results': []
        }
        
        result = SchemaValidator.validate_pagination_schema(pagination_data)
        
        assert result.is_valid
        assert len(result.errors) == 0


class TestResponseValidator:
    """Test ResponseValidator class"""
    
    def setup_method(self):
        """Setup test validator"""
        self.validator = ResponseValidator()
    
    def test_validate_response_structure_success(self):
        """Test successful response structure validation"""
        response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},
            content={'data': 'test'},
            response_time=0.5,
            request_url='http://test.com/api',
            request_method='GET',
            request_headers={}
        )
        
        result = self.validator.validate_response_structure(response)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_response_structure_slow_response(self):
        """Test response structure validation with slow response"""
        response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},
            content={'data': 'test'},
            response_time=6.0,  # Slow response
            request_url='http://test.com/api',
            request_method='GET',
            request_headers={}
        )
        
        result = self.validator.validate_response_structure(response)
        
        assert result.is_valid  # Still valid, just slow
        assert len(result.warnings) > 0
        assert any('slow' in warning.lower() for warning in result.warnings)
    
    def test_validate_error_response(self):
        """Test error response validation"""
        error_response = APIResponse(
            status_code=400,
            headers={'content-type': 'application/json'},
            content={'error': 'Bad request', 'message': 'Invalid data'},
            response_time=0.1,
            request_url='http://test.com/api',
            request_method='POST',
            request_headers={}
        )
        
        result = self.validator.validate_error_response(error_response)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_error_response_no_error_info(self):
        """Test error response validation without error information"""
        error_response = APIResponse(
            status_code=500,
            headers={'content-type': 'application/json'},
            content={'data': 'some data'},  # No error information
            response_time=0.1,
            request_url='http://test.com/api',
            request_method='POST',
            request_headers={}
        )
        
        result = self.validator.validate_error_response(error_response)
        
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any('error information' in warning for warning in result.warnings)
    
    def test_validate_success_response_with_schema(self):
        """Test success response validation with schema"""
        user_response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},
            content={
                'id': 1,
                'email': 'test@example.com',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            response_time=0.1,
            request_url='http://test.com/api/users/1',
            request_method='GET',
            request_headers={}
        )
        
        result = self.validator.validate_success_response(user_response, 'user')
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_authentication_response(self):
        """Test authentication response validation"""
        auth_response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},
            content={
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.signature',
                'refresh': 'refresh_token_here'
            },
            response_time=0.2,
            request_url='http://test.com/api/auth/login',
            request_method='POST',
            request_headers={}
        )
        
        result = self.validator.validate_authentication_response(auth_response)
        
        assert result.is_valid
        assert len(result.info) > 0  # Should have JWT format info
    
    def test_validate_crud_response_create(self):
        """Test CRUD response validation for CREATE operation"""
        create_response = APIResponse(
            status_code=201,
            headers={'content-type': 'application/json'},
            content={'id': 1, 'name': 'Created item'},
            response_time=0.1,
            request_url='http://test.com/api/items',
            request_method='POST',
            request_headers={}
        )
        
        result = self.validator.validate_crud_response(create_response, 'CREATE')
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_crud_response_delete(self):
        """Test CRUD response validation for DELETE operation"""
        delete_response = APIResponse(
            status_code=204,
            headers={},
            content='',
            response_time=0.1,
            request_url='http://test.com/api/items/1',
            request_method='DELETE',
            request_headers={}
        )
        
        result = self.validator.validate_crud_response(delete_response, 'DELETE')
        
        assert result.is_valid
        assert len(result.errors) == 0


class TestSecurityValidator:
    """Test SecurityValidator class"""
    
    def test_validate_security_headers_complete(self):
        """Test security headers validation with all headers present"""
        response = APIResponse(
            status_code=200,
            headers={
                'content-type': 'application/json',
                'x-content-type-options': 'nosniff',
                'x-frame-options': 'DENY',
                'x-xss-protection': '1; mode=block',
                'strict-transport-security': 'max-age=31536000',
                'content-security-policy': "default-src 'self'"
            },
            content={'data': 'test'},
            response_time=0.1,
            request_url='https://test.com/api',
            request_method='GET',
            request_headers={}
        )
        
        result = SecurityValidator.validate_security_headers(response)
        
        assert result.is_valid
        assert len(result.warnings) == 0
    
    def test_validate_security_headers_missing(self):
        """Test security headers validation with missing headers"""
        response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},
            content={'data': 'test'},
            response_time=0.1,
            request_url='http://test.com/api',
            request_method='GET',
            request_headers={}
        )
        
        result = SecurityValidator.validate_security_headers(response)
        
        assert result.is_valid  # Still valid, just warnings
        assert len(result.warnings) > 0
        assert any('Missing security header' in warning for warning in result.warnings)
    
    def test_validate_sensitive_data_exposure(self):
        """Test sensitive data exposure validation"""
        # Response with potentially sensitive data
        sensitive_response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},
            content={
                'user': {
                    'id': 1,
                    'email': 'test@example.com',
                    'password': 'secret123',  # Sensitive!
                    'api_key': 'sk_test_1234567890abcdef'  # Sensitive!
                }
            },
            response_time=0.1,
            request_url='http://test.com/api/user',
            request_method='GET',
            request_headers={}
        )
        
        result = SecurityValidator.validate_sensitive_data_exposure(sensitive_response)
        
        assert result.is_valid  # Still valid, just warnings
        assert len(result.warnings) > 0
        assert any('sensitive data' in warning.lower() for warning in result.warnings)
    
    def test_validate_no_sensitive_data(self):
        """Test validation with no sensitive data"""
        clean_response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},
            content={
                'user': {
                    'id': 1,
                    'email': 'test@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe'
                }
            },
            response_time=0.1,
            request_url='http://test.com/api/user',
            request_method='GET',
            request_headers={}
        )
        
        result = SecurityValidator.validate_sensitive_data_exposure(clean_response)
        
        assert result.is_valid
        assert len(result.warnings) == 0


class TestPerformanceValidator:
    """Test PerformanceValidator class"""
    
    def test_validate_performance_good(self):
        """Test performance validation with good metrics"""
        validator = PerformanceValidator()
        
        response = APIResponse(
            status_code=200,
            headers={
                'content-type': 'application/json',
                'content-length': '1024'  # 1KB
            },
            content={'data': 'test'},
            response_time=0.5,  # Fast response
            request_url='http://test.com/api',
            request_method='GET',
            request_headers={}
        )
        
        result = validator.validate_performance(response)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_validate_performance_slow_response(self):
        """Test performance validation with slow response"""
        validator = PerformanceValidator()
        
        response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},
            content={'data': 'test'},
            response_time=6.0,  # Very slow response
            request_url='http://test.com/api',
            request_method='GET',
            request_headers={}
        )
        
        result = validator.validate_performance(response)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any('Critical response time' in error for error in result.errors)
    
    def test_validate_performance_large_payload(self):
        """Test performance validation with large payload"""
        validator = PerformanceValidator()
        
        response = APIResponse(
            status_code=200,
            headers={
                'content-type': 'application/json',
                'content-length': str(6 * 1024 * 1024)  # 6MB
            },
            content={'data': 'test'},
            response_time=1.0,
            request_url='http://test.com/api',
            request_method='GET',
            request_headers={}
        )
        
        result = validator.validate_performance(response)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any('Critical payload size' in error for error in result.errors)


class TestAPIValidator:
    """Test APIValidator class (main validator)"""
    
    def setup_method(self):
        """Setup test validator"""
        self.validator = APIValidator()
    
    def test_validate_full_response_success(self):
        """Test full response validation for successful response"""
        response = APIResponse(
            status_code=200,
            headers={
                'content-type': 'application/json',
                'x-content-type-options': 'nosniff'
            },
            content={
                'id': 1,
                'email': 'test@example.com',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            response_time=0.5,
            request_url='https://test.com/api/users/1',
            request_method='GET',
            request_headers={}
        )
        
        result = self.validator.validate_full_response(
            response, 
            expected_schema='user',
            operation='READ',
            check_security=True,
            check_performance=True
        )
        
        assert result.is_valid
    
    def test_validate_full_response_with_issues(self):
        """Test full response validation with various issues"""
        response = APIResponse(
            status_code=200,
            headers={'content-type': 'application/json'},  # Missing security headers
            content={
                'id': 1,
                'email': 'invalid-email',  # Invalid email format
                'first_name': 'John'
                # Missing last_name
            },
            response_time=3.0,  # Slow response
            request_url='http://test.com/api/users/1',  # HTTP instead of HTTPS
            request_method='GET',
            request_headers={}
        )
        
        result = self.validator.validate_full_response(
            response,
            expected_schema='user',
            operation='READ',
            check_security=True,
            check_performance=True
        )
        
        # Should still be valid overall but have warnings/errors
        assert len(result.errors) > 0 or len(result.warnings) > 0
    
    def test_validate_full_response_error(self):
        """Test full response validation for error response"""
        response = APIResponse(
            status_code=404,
            headers={'content-type': 'application/json'},
            content={'error': 'Not found', 'message': 'User not found'},
            response_time=0.1,
            request_url='http://test.com/api/users/999',
            request_method='GET',
            request_headers={}
        )
        
        result = self.validator.validate_full_response(
            response,
            operation='READ',
            check_security=True,
            check_performance=True
        )
        
        # Error responses can still be valid if properly formatted
        assert result.is_valid or len(result.errors) == 0


if __name__ == '__main__':
    pytest.main([__file__])