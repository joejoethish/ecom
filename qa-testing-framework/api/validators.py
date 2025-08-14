"""
API Request/Response Validation Utilities

Provides comprehensive validation utilities for API testing including
schema validation, data type validation, and business logic validation.
"""

import re
import json
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APIResponse


class ValidationSeverity(Enum):
    """Validation error severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    
    def add_error(self, message: str):
        """Add error message"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add warning message"""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add info message"""
        self.info.append(message)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result"""
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)


class SchemaValidator:
    """JSON Schema validator for API responses"""
    
    @staticmethod
    def validate_user_schema(data: Dict[str, Any]) -> ValidationResult:
        """Validate user object schema"""
        result = ValidationResult(True, [], [], [])
        
        # Required fields
        required_fields = ['id', 'email', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        # Field type validation
        if 'id' in data and not isinstance(data['id'], (int, str)):
            result.add_error("Field 'id' must be integer or string")
        
        if 'email' in data:
            if not isinstance(data['email'], str):
                result.add_error("Field 'email' must be string")
            elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
                result.add_error("Field 'email' has invalid format")
        
        if 'first_name' in data and not isinstance(data['first_name'], str):
            result.add_error("Field 'first_name' must be string")
        
        if 'last_name' in data and not isinstance(data['last_name'], str):
            result.add_error("Field 'last_name' must be string")
        
        # Optional fields validation
        if 'phone' in data and data['phone'] is not None:
            if not isinstance(data['phone'], str):
                result.add_error("Field 'phone' must be string")
            elif not re.match(r'^[\+]?[1-9][\d]{0,15}$', data['phone'].replace(' ', '').replace('-', '')):
                result.add_warning("Field 'phone' has unusual format")
        
        if 'is_active' in data and not isinstance(data['is_active'], bool):
            result.add_error("Field 'is_active' must be boolean")
        
        if 'date_joined' in data and data['date_joined'] is not None:
            if not isinstance(data['date_joined'], str):
                result.add_error("Field 'date_joined' must be string")
            else:
                try:
                    datetime.fromisoformat(data['date_joined'].replace('Z', '+00:00'))
                except ValueError:
                    result.add_error("Field 'date_joined' has invalid datetime format")
        
        return result
    
    @staticmethod
    def validate_product_schema(data: Dict[str, Any]) -> ValidationResult:
        """Validate product object schema"""
        result = ValidationResult(True, [], [], [])
        
        # Required fields
        required_fields = ['id', 'name', 'price', 'category']
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        # Field type validation
        if 'id' in data and not isinstance(data['id'], (int, str)):
            result.add_error("Field 'id' must be integer or string")
        
        if 'name' in data and not isinstance(data['name'], str):
            result.add_error("Field 'name' must be string")
        
        if 'price' in data:
            if not isinstance(data['price'], (int, float, str)):
                result.add_error("Field 'price' must be number or string")
            else:
                try:
                    price = float(data['price'])
                    if price < 0:
                        result.add_error("Field 'price' cannot be negative")
                except (ValueError, TypeError):
                    result.add_error("Field 'price' has invalid numeric format")
        
        if 'category' in data and not isinstance(data['category'], str):
            result.add_error("Field 'category' must be string")
        
        # Optional fields validation
        if 'description' in data and data['description'] is not None:
            if not isinstance(data['description'], str):
                result.add_error("Field 'description' must be string")
        
        if 'stock_quantity' in data:
            if not isinstance(data['stock_quantity'], int):
                result.add_error("Field 'stock_quantity' must be integer")
            elif data['stock_quantity'] < 0:
                result.add_error("Field 'stock_quantity' cannot be negative")
        
        if 'is_active' in data and not isinstance(data['is_active'], bool):
            result.add_error("Field 'is_active' must be boolean")
        
        if 'images' in data:
            if not isinstance(data['images'], list):
                result.add_error("Field 'images' must be array")
            else:
                for i, image in enumerate(data['images']):
                    if not isinstance(image, str):
                        result.add_error(f"Image {i} must be string URL")
                    elif not re.match(r'^https?://', image):
                        result.add_warning(f"Image {i} should be a valid URL")
        
        return result
    
    @staticmethod
    def validate_order_schema(data: Dict[str, Any]) -> ValidationResult:
        """Validate order object schema"""
        result = ValidationResult(True, [], [], [])
        
        # Required fields
        required_fields = ['id', 'user', 'items', 'total_amount', 'status']
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        # Field type validation
        if 'id' in data and not isinstance(data['id'], (int, str)):
            result.add_error("Field 'id' must be integer or string")
        
        if 'user' in data and not isinstance(data['user'], (int, str, dict)):
            result.add_error("Field 'user' must be integer, string, or object")
        
        if 'items' in data:
            if not isinstance(data['items'], list):
                result.add_error("Field 'items' must be array")
            elif len(data['items']) == 0:
                result.add_error("Field 'items' cannot be empty")
            else:
                for i, item in enumerate(data['items']):
                    if not isinstance(item, dict):
                        result.add_error(f"Item {i} must be object")
                    else:
                        item_result = SchemaValidator.validate_order_item_schema(item)
                        if not item_result.is_valid:
                            for error in item_result.errors:
                                result.add_error(f"Item {i}: {error}")
        
        if 'total_amount' in data:
            if not isinstance(data['total_amount'], (int, float, str)):
                result.add_error("Field 'total_amount' must be number or string")
            else:
                try:
                    amount = float(data['total_amount'])
                    if amount < 0:
                        result.add_error("Field 'total_amount' cannot be negative")
                except (ValueError, TypeError):
                    result.add_error("Field 'total_amount' has invalid numeric format")
        
        if 'status' in data:
            valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned']
            if data['status'] not in valid_statuses:
                result.add_error(f"Field 'status' must be one of: {', '.join(valid_statuses)}")
        
        return result
    
    @staticmethod
    def validate_order_item_schema(data: Dict[str, Any]) -> ValidationResult:
        """Validate order item object schema"""
        result = ValidationResult(True, [], [], [])
        
        # Required fields
        required_fields = ['product', 'quantity', 'price']
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        # Field type validation
        if 'product' in data and not isinstance(data['product'], (int, str, dict)):
            result.add_error("Field 'product' must be integer, string, or object")
        
        if 'quantity' in data:
            if not isinstance(data['quantity'], int):
                result.add_error("Field 'quantity' must be integer")
            elif data['quantity'] <= 0:
                result.add_error("Field 'quantity' must be positive")
        
        if 'price' in data:
            if not isinstance(data['price'], (int, float, str)):
                result.add_error("Field 'price' must be number or string")
            else:
                try:
                    price = float(data['price'])
                    if price < 0:
                        result.add_error("Field 'price' cannot be negative")
                except (ValueError, TypeError):
                    result.add_error("Field 'price' has invalid numeric format")
        
        return result
    
    @staticmethod
    def validate_pagination_schema(data: Dict[str, Any]) -> ValidationResult:
        """Validate pagination object schema"""
        result = ValidationResult(True, [], [], [])
        
        # Check for pagination fields
        pagination_fields = ['count', 'next', 'previous', 'results']
        has_pagination = any(field in data for field in pagination_fields)
        
        if has_pagination:
            if 'count' in data and not isinstance(data['count'], int):
                result.add_error("Pagination field 'count' must be integer")
            
            if 'next' in data and data['next'] is not None and not isinstance(data['next'], str):
                result.add_error("Pagination field 'next' must be string URL or null")
            
            if 'previous' in data and data['previous'] is not None and not isinstance(data['previous'], str):
                result.add_error("Pagination field 'previous' must be string URL or null")
            
            if 'results' in data and not isinstance(data['results'], list):
                result.add_error("Pagination field 'results' must be array")
        
        return result


class ResponseValidator:
    """Comprehensive response validator"""
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
    
    def validate_response_structure(self, response: APIResponse) -> ValidationResult:
        """Validate basic response structure"""
        result = ValidationResult(True, [], [], [])
        
        # Check status code
        if response.status_code < 100 or response.status_code >= 600:
            result.add_error(f"Invalid HTTP status code: {response.status_code}")
        
        # Check content type for JSON responses
        content_type = response.headers.get('content-type', '')
        if isinstance(response.content, dict) or isinstance(response.content, list):
            if not content_type.startswith('application/json'):
                result.add_warning("Response contains JSON but Content-Type is not application/json")
        
        # Check response time
        if response.response_time > 5.0:
            result.add_warning(f"Slow response time: {response.response_time:.2f}s")
        elif response.response_time > 10.0:
            result.add_error(f"Extremely slow response time: {response.response_time:.2f}s")
        
        return result
    
    def validate_error_response(self, response: APIResponse) -> ValidationResult:
        """Validate error response format"""
        result = ValidationResult(True, [], [], [])
        
        if not response.is_success:
            if isinstance(response.content, dict):
                # Check for common error fields
                error_fields = ['error', 'message', 'detail', 'errors']
                has_error_field = any(field in response.content for field in error_fields)
                
                if not has_error_field:
                    result.add_warning("Error response should contain error information")
                
                # Validate error message format
                if 'message' in response.content and not isinstance(response.content['message'], str):
                    result.add_error("Error message must be string")
                
                if 'errors' in response.content and not isinstance(response.content['errors'], (list, dict)):
                    result.add_error("Errors field must be array or object")
            
            elif isinstance(response.content, str):
                if not response.content.strip():
                    result.add_warning("Error response has empty content")
        
        return result
    
    def validate_success_response(self, response: APIResponse, expected_schema: str = None) -> ValidationResult:
        """Validate successful response format"""
        result = ValidationResult(True, [], [], [])
        
        if response.is_success:
            if isinstance(response.content, dict):
                # Validate based on expected schema
                if expected_schema == 'user':
                    schema_result = self.schema_validator.validate_user_schema(response.content)
                    result.merge(schema_result)
                elif expected_schema == 'product':
                    schema_result = self.schema_validator.validate_product_schema(response.content)
                    result.merge(schema_result)
                elif expected_schema == 'order':
                    schema_result = self.schema_validator.validate_order_schema(response.content)
                    result.merge(schema_result)
                elif expected_schema == 'list':
                    # Validate list response with pagination
                    pagination_result = self.schema_validator.validate_pagination_schema(response.content)
                    result.merge(pagination_result)
            
            elif isinstance(response.content, list):
                if expected_schema:
                    for i, item in enumerate(response.content):
                        if expected_schema == 'user':
                            item_result = self.schema_validator.validate_user_schema(item)
                        elif expected_schema == 'product':
                            item_result = self.schema_validator.validate_product_schema(item)
                        elif expected_schema == 'order':
                            item_result = self.schema_validator.validate_order_schema(item)
                        else:
                            continue
                        
                        if not item_result.is_valid:
                            for error in item_result.errors:
                                result.add_error(f"Item {i}: {error}")
        
        return result
    
    def validate_authentication_response(self, response: APIResponse) -> ValidationResult:
        """Validate authentication response"""
        result = ValidationResult(True, [], [], [])
        
        if response.is_success and isinstance(response.content, dict):
            # Check for token fields
            token_fields = ['access', 'token', 'access_token', 'refresh', 'refresh_token']
            has_token = any(field in response.content for field in token_fields)
            
            if not has_token:
                result.add_warning("Authentication response should contain token")
            
            # Validate token format (basic JWT check)
            for field in token_fields:
                if field in response.content:
                    token = response.content[field]
                    if isinstance(token, str) and token.count('.') == 2:
                        result.add_info(f"Valid JWT token format in field '{field}'")
                    elif isinstance(token, str):
                        result.add_warning(f"Token in field '{field}' may not be JWT format")
        
        return result
    
    def validate_crud_response(self, response: APIResponse, operation: str) -> ValidationResult:
        """Validate CRUD operation response"""
        result = ValidationResult(True, [], [], [])
        
        if operation.upper() == 'CREATE':
            if response.status_code != 201:
                result.add_warning(f"CREATE operation returned {response.status_code}, expected 201")
            
            if isinstance(response.content, dict) and 'id' not in response.content:
                result.add_warning("CREATE response should contain 'id' field")
        
        elif operation.upper() == 'READ':
            if response.status_code != 200:
                result.add_error(f"READ operation returned {response.status_code}, expected 200")
        
        elif operation.upper() == 'UPDATE':
            if response.status_code not in [200, 204]:
                result.add_warning(f"UPDATE operation returned {response.status_code}, expected 200 or 204")
        
        elif operation.upper() == 'DELETE':
            if response.status_code not in [200, 204, 404]:
                result.add_warning(f"DELETE operation returned {response.status_code}, expected 200, 204, or 404")
        
        return result


class SecurityValidator:
    """Security-focused response validator"""
    
    @staticmethod
    def validate_security_headers(response: APIResponse) -> ValidationResult:
        """Validate security-related headers"""
        result = ValidationResult(True, [], [], [])
        
        # Check for security headers
        security_headers = {
            'x-content-type-options': 'nosniff',
            'x-frame-options': ['DENY', 'SAMEORIGIN'],
            'x-xss-protection': '1; mode=block',
            'strict-transport-security': None,  # Should exist for HTTPS
            'content-security-policy': None,
        }
        
        for header, expected_value in security_headers.items():
            if header not in response.headers:
                result.add_warning(f"Missing security header: {header}")
            elif expected_value:
                actual_value = response.headers[header].lower()
                if isinstance(expected_value, list):
                    if actual_value not in [v.lower() for v in expected_value]:
                        result.add_warning(f"Security header {header} has unexpected value: {actual_value}")
                elif actual_value != expected_value.lower():
                    result.add_warning(f"Security header {header} has unexpected value: {actual_value}")
        
        return result
    
    @staticmethod
    def validate_sensitive_data_exposure(response: APIResponse) -> ValidationResult:
        """Check for potential sensitive data exposure"""
        result = ValidationResult(True, [], [], [])
        
        if isinstance(response.content, (dict, list)):
            content_str = json.dumps(response.content).lower()
            
            # Check for potentially sensitive fields
            sensitive_patterns = [
                r'password',
                r'secret',
                r'private_key',
                r'api_key',
                r'token.*[a-f0-9]{20,}',  # Long hex strings that might be tokens
                r'ssn',
                r'social_security',
                r'credit_card',
                r'cvv',
            ]
            
            for pattern in sensitive_patterns:
                if re.search(pattern, content_str):
                    result.add_warning(f"Response may contain sensitive data matching pattern: {pattern}")
        
        return result


class PerformanceValidator:
    """Performance-focused validator"""
    
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or {
            'response_time_warning': 2.0,
            'response_time_critical': 5.0,
            'payload_size_warning': 1024 * 1024,  # 1MB
            'payload_size_critical': 5 * 1024 * 1024,  # 5MB
        }
    
    def validate_performance(self, response: APIResponse) -> ValidationResult:
        """Validate response performance metrics"""
        result = ValidationResult(True, [], [], [])
        
        # Response time validation
        if response.response_time > self.thresholds['response_time_critical']:
            result.add_error(f"Critical response time: {response.response_time:.2f}s")
        elif response.response_time > self.thresholds['response_time_warning']:
            result.add_warning(f"Slow response time: {response.response_time:.2f}s")
        
        # Payload size validation
        content_length = response.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > self.thresholds['payload_size_critical']:
                    result.add_error(f"Critical payload size: {size} bytes")
                elif size > self.thresholds['payload_size_warning']:
                    result.add_warning(f"Large payload size: {size} bytes")
            except ValueError:
                pass
        
        return result


class APIValidator:
    """Main API validator that combines all validation types"""
    
    def __init__(self, performance_thresholds: Optional[Dict[str, float]] = None):
        self.response_validator = ResponseValidator()
        self.security_validator = SecurityValidator()
        self.performance_validator = PerformanceValidator(performance_thresholds)
    
    def validate_full_response(self, response: APIResponse, expected_schema: str = None,
                             operation: str = None, check_security: bool = True,
                             check_performance: bool = True) -> ValidationResult:
        """Perform comprehensive response validation"""
        result = ValidationResult(True, [], [], [])
        
        # Basic structure validation
        structure_result = self.response_validator.validate_response_structure(response)
        result.merge(structure_result)
        
        # Success/error response validation
        if response.is_success:
            success_result = self.response_validator.validate_success_response(response, expected_schema)
            result.merge(success_result)
        else:
            error_result = self.response_validator.validate_error_response(response)
            result.merge(error_result)
        
        # CRUD operation validation
        if operation:
            crud_result = self.response_validator.validate_crud_response(response, operation)
            result.merge(crud_result)
        
        # Security validation
        if check_security:
            security_result = self.security_validator.validate_security_headers(response)
            result.merge(security_result)
            
            sensitive_data_result = self.security_validator.validate_sensitive_data_exposure(response)
            result.merge(sensitive_data_result)
        
        # Performance validation
        if check_performance:
            performance_result = self.performance_validator.validate_performance(response)
            result.merge(performance_result)
        
        return result