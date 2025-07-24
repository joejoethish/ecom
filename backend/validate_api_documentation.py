"""
Script to validate API documentation.

This script runs tests to validate the API documentation setup,
including Swagger/OpenAPI documentation, documentation guides,
and API versioning documentation.
"""
import os
import sys
import django
import unittest
import json
import requests
from urllib.parse import urljoin

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.test.client import Client
from django.urls import reverse
from django.conf import settings


class APIDocumentationValidator:
    """
    Validator for API documentation.
    """
    
    def __init__(self):
        self.client = Client()
        self.base_url = 'http://localhost:8000'  # Adjust if needed
        self.errors = []
        self.warnings = []
        self.successes = []
    
    def validate_swagger_ui(self):
        """Validate Swagger UI endpoint."""
        print("Validating Swagger UI endpoint...")
        try:
            response = self.client.get(reverse('swagger-ui'))
            if response.status_code == 200 and 'text/html' in response['Content-Type']:
                self.successes.append("✅ Swagger UI endpoint is accessible")
            else:
                self.errors.append(f"❌ Swagger UI endpoint returned status {response.status_code}")
        except Exception as e:
            self.errors.append(f"❌ Error accessing Swagger UI endpoint: {str(e)}")
    
    def validate_redoc(self):
        """Validate ReDoc endpoint."""
        print("Validating ReDoc endpoint...")
        try:
            response = self.client.get(reverse('redoc'))
            if response.status_code == 200 and 'text/html' in response['Content-Type']:
                self.successes.append("✅ ReDoc endpoint is accessible")
            else:
                self.errors.append(f"❌ ReDoc endpoint returned status {response.status_code}")
        except Exception as e:
            self.errors.append(f"❌ Error accessing ReDoc endpoint: {str(e)}")
    
    def validate_schema(self):
        """Validate OpenAPI schema endpoint."""
        print("Validating OpenAPI schema endpoint...")
        try:
            response = self.client.get(reverse('schema'))
            if response.status_code == 200 and 'application/json' in response['Content-Type']:
                try:
                    schema = json.loads(response.content)
                    if 'openapi' in schema and 'paths' in schema and 'components' in schema:
                        self.successes.append("✅ OpenAPI schema is valid")
                        
                        # Check for API endpoints
                        paths = schema.get('paths', {})
                        if paths:
                            self.successes.append(f"✅ Schema contains {len(paths)} API endpoints")
                        else:
                            self.warnings.append("⚠️ Schema does not contain any API endpoints")
                        
                        # Check for components
                        components = schema.get('components', {})
                        schemas = components.get('schemas', {})
                        if schemas:
                            self.successes.append(f"✅ Schema contains {len(schemas)} component schemas")
                        else:
                            self.warnings.append("⚠️ Schema does not contain any component schemas")
                        
                        # Check for security schemes
                        security_schemes = components.get('securitySchemes', {})
                        if security_schemes:
                            self.successes.append(f"✅ Schema contains {len(security_schemes)} security schemes")
                        else:
                            self.warnings.append("⚠️ Schema does not contain any security schemes")
                    else:
                        self.errors.append("❌ OpenAPI schema is missing required fields")
                except json.JSONDecodeError:
                    self.errors.append("❌ OpenAPI schema is not valid JSON")
            else:
                self.errors.append(f"❌ OpenAPI schema endpoint returned status {response.status_code}")
        except Exception as e:
            self.errors.append(f"❌ Error accessing OpenAPI schema endpoint: {str(e)}")
    
    def validate_documentation_guides(self):
        """Validate API documentation guides."""
        print("Validating API documentation guides...")
        guides = [
            'authentication',
            'error-handling',
            'usage',
            'versioning',
        ]
        
        for guide in guides:
            try:
                response = self.client.get(f'/api/docs/guides/{guide}/')
                if response.status_code == 200 and 'text/html' in response['Content-Type']:
                    self.successes.append(f"✅ {guide.capitalize()} guide is accessible")
                else:
                    self.errors.append(f"❌ {guide.capitalize()} guide returned status {response.status_code}")
            except Exception as e:
                self.errors.append(f"❌ Error accessing {guide} guide: {str(e)}")
    
    def validate_api_versioning(self):
        """Validate API versioning documentation."""
        print("Validating API versioning documentation...")
        try:
            # Check versioning guide
            response = self.client.get('/api/docs/guides/versioning/')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                if 'v1' in content and 'v2' in content:
                    self.successes.append("✅ Versioning guide mentions API versions")
                else:
                    self.warnings.append("⚠️ Versioning guide does not mention API versions")
            
            # Check API version headers
            response = self.client.get('/api/v1/products/')
            if 'X-API-Version' in response and 'X-API-Supported-Versions' in response:
                self.successes.append("✅ API responses include version headers")
            else:
                self.warnings.append("⚠️ API responses do not include version headers")
            
            # Check deprecated version warning
            if 'X-API-Deprecation-Warning' in response:
                self.successes.append("✅ Deprecated API versions include warning headers")
            else:
                self.warnings.append("⚠️ Deprecated API versions do not include warning headers")
        except Exception as e:
            self.errors.append(f"❌ Error validating API versioning: {str(e)}")
    
    def validate_all(self):
        """Run all validation checks."""
        print("Starting API documentation validation...")
        
        self.validate_swagger_ui()
        self.validate_redoc()
        self.validate_schema()
        self.validate_documentation_guides()
        self.validate_api_versioning()
        
        print("\n=== Validation Results ===")
        
        if self.successes:
            print("\nSuccesses:")
            for success in self.successes:
                print(f"  {success}")
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  {error}")
        
        print("\n=== Summary ===")
        print(f"Successes: {len(self.successes)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Errors: {len(self.errors)}")
        
        return len(self.errors) == 0


if __name__ == '__main__':
    validator = APIDocumentationValidator()
    success = validator.validate_all()
    
    if success:
        print("\n✅ API documentation validation passed!")
        sys.exit(0)
    else:
        print("\n❌ API documentation validation failed!")
        sys.exit(1)