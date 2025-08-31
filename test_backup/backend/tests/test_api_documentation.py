"""
Tests for API documentation endpoints.

This module contains comprehensive tests for API documentation endpoints,
including schema validation, guide rendering, and documentation completeness.
"""
import json
import re
import yaml
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class APIDocumentationTests(APITestCase):
    """Test suite for API documentation endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
    
    def test_swagger_ui_endpoint(self):
        """Test that Swagger UI endpoint is accessible."""
        url = reverse('swagger-ui')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/html', response['Content-Type'])
        
        # Check for key Swagger UI elements in the HTML
        content = response.content.decode('utf-8')
        self.assertIn('swagger-ui', content)
        self.assertIn('E-Commerce Platform API', content)
    
    def test_redoc_endpoint(self):
        """Test that ReDoc endpoint is accessible."""
        url = reverse('redoc')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/html', response['Content-Type'])
        
        # Check for key ReDoc elements in the HTML
        content = response.content.decode('utf-8')
        self.assertIn('redoc', content)
        self.assertIn('E-Commerce Platform API', content)
    
    def test_schema_endpoint(self):
        """Test that OpenAPI schema endpoint is accessible and returns valid JSON."""
        url = reverse('schema')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/json', response['Content-Type'])
        
        # Validate that the response is valid JSON
        try:
            schema = json.loads(response.content)
            self.assertIn('openapi', schema)
            self.assertIn('info', schema)
            self.assertIn('paths', schema)
            self.assertIn('components', schema)
            
            # Check OpenAPI version
            self.assertEqual(schema['openapi'], '3.0.3')
            
            # Check API info
            self.assertEqual(schema['info']['title'], 'E-Commerce Platform API')
            self.assertIn('version', schema['info'])
            self.assertIn('description', schema['info'])
        except json.JSONDecodeError:
            self.fail("Schema endpoint did not return valid JSON")
    
    def test_schema_yaml_endpoint(self):
        """Test that OpenAPI schema YAML endpoint is accessible."""
        url = reverse('schema-yaml')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/yaml', response['Content-Type'])
        
        # Validate that the response is valid YAML
        try:
            schema = yaml.safe_load(response.content)
            self.assertIn('openapi', schema)
            self.assertIn('info', schema)
            self.assertIn('paths', schema)
            self.assertIn('components', schema)
        except yaml.YAMLError:
            self.fail("Schema endpoint did not return valid YAML")
    
    def test_schema_contains_product_endpoints(self):
        """Test that schema contains product endpoints."""
        url = reverse('schema')
        response = self.client.get(url)
        schema = json.loads(response.content)
        
        # Check for product endpoints
        paths = schema.get('paths', {})
        self.assertTrue(any('/products/' in path for path in paths))
        
        # Check for product tags
        tags = schema.get('tags', [])
        self.assertTrue(any(tag.get('name') == 'Products' for tag in tags))
        
        # Check for specific product operations
        product_paths = [path for path in paths.keys() if '/products/' in path]
        self.assertTrue(len(product_paths) > 0)
        
        # Check for CRUD operations on products
        product_list_path = next((path for path in paths.keys() if path.endswith('/products/')), None)
        if product_list_path:
            self.assertIn('get', paths[product_list_path])  # List products
            self.assertIn('post', paths[product_list_path])  # Create product
    
    def test_schema_contains_authentication_endpoints(self):
        """Test that schema contains authentication endpoints."""
        url = reverse('schema')
        response = self.client.get(url)
        schema = json.loads(response.content)
        
        # Check for authentication endpoints
        paths = schema.get('paths', {})
        self.assertTrue(any('/auth/' in path for path in paths))
        
        # Check for authentication tags
        tags = schema.get('tags', [])
        self.assertTrue(any(tag.get('name') == 'Authentication' for tag in tags))
        
        # Check for specific authentication operations
        auth_paths = [path for path in paths.keys() if '/auth/' in path]
        self.assertTrue(len(auth_paths) > 0)
        
        # Check for login and register endpoints
        self.assertTrue(any('login' in path for path in auth_paths))
        self.assertTrue(any('register' in path for path in auth_paths))
    
    def test_schema_contains_security_definitions(self):
        """Test that schema contains security definitions."""
        url = reverse('schema')
        response = self.client.get(url)
        schema = json.loads(response.content)
        
        # Check for security schemes
        components = schema.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        self.assertIn('Bearer', security_schemes)
        
        # Check Bearer auth scheme
        bearer_scheme = security_schemes.get('Bearer', {})
        self.assertEqual(bearer_scheme.get('type'), 'http')
        self.assertEqual(bearer_scheme.get('scheme'), 'bearer')
        
        # Check that security is applied to protected endpoints
        paths = schema.get('paths', {})
        protected_paths = [
            path for path in paths.keys() 
            if not (path.endswith('/login/') or path.endswith('/register/'))
        ]
        
        if protected_paths:
            sample_path = protected_paths[0]
            for method in paths[sample_path].values():
                if 'security' in method:
                    # At least one endpoint should have security
                    self.assertTrue(any('Bearer' in sec for sec in method['security']))
                    break
            else:
                self.fail("No security requirements found in protected endpoints")
    
    def test_schema_contains_all_api_modules(self):
        """Test that schema contains all API modules."""
        url = reverse('schema')
        response = self.client.get(url)
        schema = json.loads(response.content)
        
        # Get all app modules from settings
        local_apps = [app for app in settings.LOCAL_APPS if app.startswith('apps.')]
        app_names = [app.split('.')[-1] for app in local_apps]
        
        # Check for endpoints for each app
        paths = schema.get('paths', {})
        path_strings = ' '.join(paths.keys())
        
        for app_name in app_names:
            # Skip apps that might not have API endpoints
            if app_name in ['chat']:  # WebSocket endpoints might not be in REST API schema
                continue
                
            # Check if app name appears in paths
            self.assertTrue(
                any(f'/{app_name}/' in path for path in paths) or  # Direct path
                re.search(rf'\b{app_name}\b', path_strings, re.IGNORECASE),  # Name in path
                f"API schema is missing endpoints for {app_name}"
            )
    
    def test_schema_contains_examples(self):
        """Test that schema contains examples for requests and responses."""
        url = reverse('schema')
        response = self.client.get(url)
        schema = json.loads(response.content)
        
        # Check for examples in components
        components = schema.get('components', {})
        schemas = components.get('schemas', {})
        
        # At least some schemas should have examples
        schemas_with_examples = [
            schema_name for schema_name, schema_def in schemas.items()
            if 'example' in schema_def
        ]
        
        self.assertTrue(
            len(schemas_with_examples) > 0,
            "API schema does not contain any examples in component schemas"
        )
        
        # Check for examples in responses
        paths = schema.get('paths', {})
        examples_in_responses = False
        
        for path_item in paths.values():
            for operation in path_item.values():
                responses = operation.get('responses', {})
                for response in responses.values():
                    if 'content' in response:
                        for content_type in response['content'].values():
                            if 'examples' in content_type:
                                examples_in_responses = True
                                break
        
        self.assertTrue(
            examples_in_responses,
            "API schema does not contain any examples in responses"
        )
    
    def test_schema_contains_error_responses(self):
        """Test that schema contains error response definitions."""
        url = reverse('schema')
        response = self.client.get(url)
        schema = json.loads(response.content)
        
        # Check paths for error responses
        paths = schema.get('paths', {})
        
        # Count paths with error responses
        paths_with_errors = 0
        
        for path_item in paths.values():
            for operation in path_item.values():
                responses = operation.get('responses', {})
                # Check for error status codes (4xx, 5xx)
                error_responses = [
                    status_code for status_code in responses.keys()
                    if status_code.startswith('4') or status_code.startswith('5')
                ]
                
                if error_responses:
                    paths_with_errors += 1
        
        # At least some paths should have error responses
        self.assertTrue(
            paths_with_errors > 0,
            "API schema does not contain any error responses"
        )
        
        # Check for common error status codes
        common_error_codes = ['400', '401', '403', '404', '429']
        error_codes_found = set()
        
        for path_item in paths.values():
            for operation in path_item.values():
                responses = operation.get('responses', {})
                for code in common_error_codes:
                    if code in responses:
                        error_codes_found.add(code)
        
        # Should have at least some common error codes
        self.assertTrue(
            len(error_codes_found) > 0,
            "API schema does not contain common error status codes"
        )
    
    def test_api_documentation_guides_exist(self):
        """Test that API documentation guides exist."""
        # Test authentication guide
        response = self.client.get('/api/docs/guides/authentication/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test error handling guide
        response = self.client.get('/api/docs/guides/error-handling/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test usage guide
        response = self.client.get('/api/docs/guides/usage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test versioning guide
        response = self.client.get('/api/docs/guides/versioning/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test guides list endpoint
        response = self.client.get('/api/docs/guides.json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/json', response['Content-Type'])
        
        guides_data = json.loads(response.content)
        self.assertIn('guides', guides_data)
        self.assertTrue(len(guides_data['guides']) >= 4)
    
    def test_api_documentation_markdown_rendering(self):
        """Test that API documentation markdown renders correctly."""
        # Test markdown rendering for guides
        response = self.client.get('/api/docs/guides/authentication/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/html', response['Content-Type'])
        
        # Check for HTML content that indicates markdown was rendered
        content = response.content.decode('utf-8')
        self.assertIn('<h1', content)  # Should have rendered headings
        self.assertIn('<code>', content)  # Should have rendered code blocks
        self.assertIn('<table>', content)  # Should have rendered tables
        
        # Check for navigation links to other guides
        self.assertIn('href="/api/docs/guides/usage/"', content)
        self.assertIn('href="/api/docs/guides/error-handling/"', content)
        self.assertIn('href="/api/docs/guides/versioning/"', content)
    
    def test_api_endpoints_list(self):
        """Test that API endpoints list is accessible."""
        response = self.client.get('/api/docs/endpoints.json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/json', response['Content-Type'])
        
        endpoints_data = json.loads(response.content)
        self.assertIn('endpoints', endpoints_data)
        
        # Should have at least some endpoints grouped by tag
        self.assertTrue(len(endpoints_data['endpoints']) > 0)
        
        # Check structure of endpoints data
        for tag, endpoints in endpoints_data['endpoints'].items():
            self.assertTrue(len(endpoints) > 0)
            endpoint = endpoints[0]
            self.assertIn('path', endpoint)
            self.assertIn('method', endpoint)
            self.assertIn('summary', endpoint)
            
    def test_api_versioning_in_documentation(self):
        """Test that API versioning is properly documented."""
        url = reverse('schema')
        response = self.client.get(url)
        schema = json.loads(response.content)
        
        # Check for v1 and v2 endpoints
        paths = schema.get('paths', {})
        v1_paths = [path for path in paths.keys() if '/v1/' in path]
        v2_paths = [path for path in paths.keys() if '/v2/' in path]
        
        # Should have both v1 and v2 endpoints
        self.assertTrue(len(v1_paths) > 0, "No v1 API endpoints found in documentation")
        self.assertTrue(len(v2_paths) > 0, "No v2 API endpoints found in documentation")
        
        # Check versioning guide for version information
        response = self.client.get('/api/docs/guides/versioning/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        
        # Should mention both v1 and v2
        self.assertIn('v1', content)
        self.assertIn('v2', content)
        
        # Should mention versioning strategy
        self.assertIn('URL-based versioning', content)