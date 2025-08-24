"""
Tests for Route Discovery Service
"""

import os
import tempfile
import shutil
from unittest.mock import patch, mock_open
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    FrontendRoute, APICallDiscovery, RouteDiscoverySession, 
    RouteDependency, WorkflowSession
)
from .route_discovery import (
    NextJSRouteScanner, APICallExtractor, DependencyMapper, 
    RouteDiscoveryService
)

User = get_user_model()


class NextJSRouteScannerTest(TestCase):
    """Test the Next.js route scanner"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = NextJSRouteScanner(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, path, content="export default function Component() { return <div>Test</div>; }"):
        """Helper to create test files"""
        full_path = os.path.join(self.temp_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
    
    def test_scan_basic_page_routes(self):
        """Test scanning basic page routes"""
        # Create test app structure
        self.create_test_file('src/app/page.tsx')
        self.create_test_file('src/app/about/page.tsx')
        self.create_test_file('src/app/products/page.tsx')
        
        routes = self.scanner.scan_routes()
        
        self.assertEqual(len(routes), 3)
        
        # Check root page
        root_route = next((r for r in routes if r['path'] == '/'), None)
        self.assertIsNotNone(root_route)
        self.assertEqual(root_route['route_type'], 'page')
        self.assertFalse(root_route['is_dynamic'])
        
        # Check about page
        about_route = next((r for r in routes if r['path'] == '/about'), None)
        self.assertIsNotNone(about_route)
        self.assertEqual(about_route['route_type'], 'page')
    
    def test_scan_dynamic_routes(self):
        """Test scanning dynamic routes"""
        self.create_test_file('src/app/products/[id]/page.tsx')
        self.create_test_file('src/app/users/[...slug]/page.tsx')
        
        routes = self.scanner.scan_routes()
        
        self.assertEqual(len(routes), 2)
        
        # Check dynamic route
        dynamic_route = next((r for r in routes if r['path'] == '/products/[id]'), None)
        self.assertIsNotNone(dynamic_route)
        self.assertTrue(dynamic_route['is_dynamic'])
        self.assertIn('id', dynamic_route['dynamic_segments'])
        
        # Check catch-all route
        catchall_route = next((r for r in routes if r['path'] == '/users/[...slug]'), None)
        self.assertIsNotNone(catchall_route)
        self.assertTrue(catchall_route['is_dynamic'])
        self.assertIn('...slug', catchall_route['dynamic_segments'])
    
    def test_scan_api_routes(self):
        """Test scanning API routes"""
        self.create_test_file('src/app/api/users/route.ts', 'export async function GET() { return Response.json({}); }')
        self.create_test_file('src/app/api/products/[id]/route.ts')
        
        routes = self.scanner.scan_routes()
        
        self.assertEqual(len(routes), 2)
        
        # Check API route
        api_route = next((r for r in routes if r['path'] == '/api/users'), None)
        self.assertIsNotNone(api_route)
        self.assertEqual(api_route['route_type'], 'api')
    
    def test_scan_route_groups(self):
        """Test scanning route groups (folders in parentheses)"""
        self.create_test_file('src/app/(auth)/login/page.tsx')
        self.create_test_file('src/app/(auth)/register/page.tsx')
        
        routes = self.scanner.scan_routes()
        
        self.assertEqual(len(routes), 2)
        
        # Route groups should not affect the URL path
        login_route = next((r for r in routes if r['path'] == '/login'), None)
        self.assertIsNotNone(login_route)
        
        register_route = next((r for r in routes if r['path'] == '/register'), None)
        self.assertIsNotNone(register_route)
    
    def test_scan_layout_and_special_files(self):
        """Test scanning layout and special files"""
        self.create_test_file('src/app/layout.tsx')
        self.create_test_file('src/app/loading.tsx')
        self.create_test_file('src/app/error.tsx')
        self.create_test_file('src/app/not-found.tsx')
        
        routes = self.scanner.scan_routes()
        
        self.assertEqual(len(routes), 4)
        
        # Check layout
        layout_route = next((r for r in routes if r['route_type'] == 'layout'), None)
        self.assertIsNotNone(layout_route)
        
        # Check loading
        loading_route = next((r for r in routes if r['route_type'] == 'loading'), None)
        self.assertIsNotNone(loading_route)
    
    def test_extract_component_name(self):
        """Test extracting component names from files"""
        # Test default export function
        content = "export default function HomePage() { return <div>Home</div>; }"
        self.create_test_file('src/app/page.tsx', content)
        
        component_name = self.scanner._extract_component_name(os.path.join(self.temp_dir, 'src/app/page.tsx'))
        self.assertEqual(component_name, 'HomePage')
    
    def test_nonexistent_directory(self):
        """Test handling of nonexistent app directory"""
        scanner = NextJSRouteScanner('/nonexistent/path')
        routes = scanner.scan_routes()
        
        self.assertEqual(len(routes), 0)
        self.assertIn('App directory not found', scanner.errors[0])


class APICallExtractorTest(TestCase):
    """Test the API call extractor"""
    
    def setUp(self):
        self.extractor = APICallExtractor()
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.tsx', delete=False)
    
    def tearDown(self):
        os.unlink(self.temp_file.name)
    
    def write_component(self, content):
        """Helper to write component content to temp file"""
        self.temp_file.write(content)
        self.temp_file.flush()
    
    def test_extract_fetch_calls(self):
        """Test extracting fetch API calls"""
        content = '''
        export default function Component() {
            useEffect(() => {
                fetch('/api/products', {
                    method: 'GET',
                    headers: {
                        'Authorization': 'Bearer token',
                        'Content-Type': 'application/json'
                    }
                });
            }, []);
            
            const handleSubmit = () => {
                fetch('/api/orders', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            };
            
            return <div>Component</div>;
        }
        '''
        self.write_component(content)
        
        api_calls = self.extractor.extract_api_calls(self.temp_file.name)
        
        self.assertEqual(len(api_calls), 2)
        
        # Check GET call
        get_call = next((call for call in api_calls if call['method'] == 'GET'), None)
        self.assertIsNotNone(get_call)
        self.assertEqual(get_call['endpoint'], '/api/products')
        self.assertTrue(get_call['requires_authentication'])
        self.assertIn('Authorization', get_call['headers'])
        
        # Check POST call
        post_call = next((call for call in api_calls if call['method'] == 'POST'), None)
        self.assertIsNotNone(post_call)
        self.assertEqual(post_call['endpoint'], '/api/orders')
    
    def test_extract_axios_calls(self):
        """Test extracting axios API calls"""
        content = '''
        import axios from 'axios';
        
        export default function Component() {
            const fetchData = async () => {
                await axios.get('/api/users');
                await axios.post('/api/users', userData);
                await axios({
                    url: '/api/products',
                    method: 'PUT'
                });
            };
            
            return <div>Component</div>;
        }
        '''
        self.write_component(content)
        
        api_calls = self.extractor.extract_api_calls(self.temp_file.name)
        
        self.assertEqual(len(api_calls), 3)
        
        # Check different axios call patterns
        methods = [call['method'] for call in api_calls]
        self.assertIn('GET', methods)
        self.assertIn('POST', methods)
        self.assertIn('PUT', methods)
    
    def test_extract_service_calls(self):
        """Test extracting custom service calls"""
        content = '''
        import { getProducts, createOrder } from '@/services/api';
        
        export default function Component() {
            useEffect(() => {
                getProducts();
            }, []);
            
            const handleOrder = () => {
                createOrder(orderData);
            };
            
            return <div>Component</div>;
        }
        '''
        self.write_component(content)
        
        api_calls = self.extractor.extract_api_calls(self.temp_file.name)
        
        self.assertEqual(len(api_calls), 2)
        
        # Check service calls
        service_calls = [call for call in api_calls if call['call_type'] == 'service']
        self.assertEqual(len(service_calls), 2)
        
        get_call = next((call for call in service_calls if call['service_function'] == 'getProducts'), None)
        self.assertIsNotNone(get_call)
        self.assertEqual(get_call['service_name'], 'api')
    
    def test_find_containing_function(self):
        """Test finding the containing function for API calls"""
        content = '''
        export default function Component() {
            const fetchData = async () => {
                fetch('/api/data');
            };
            
            useEffect(() => {
                fetch('/api/initial');
            }, []);
            
            return <div>Component</div>;
        }
        '''
        self.write_component(content)
        
        api_calls = self.extractor.extract_api_calls(self.temp_file.name)
        
        self.assertEqual(len(api_calls), 2)
        
        # Check function names are detected
        function_names = [call['function_name'] for call in api_calls if call['function_name']]
        self.assertTrue(len(function_names) > 0)


class RouteDiscoveryServiceTest(TestCase):
    """Test the complete route discovery service"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.service = RouteDiscoveryService()
        self.service.scanner = NextJSRouteScanner(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, path, content="export default function Component() { return <div>Test</div>; }"):
        """Helper to create test files"""
        full_path = os.path.join(self.temp_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
    
    def test_run_discovery_success(self):
        """Test successful route discovery"""
        # Create test files
        self.create_test_file('src/app/page.tsx', '''
            export default function HomePage() {
                useEffect(() => {
                    fetch('/api/products');
                }, []);
                return <div>Home</div>;
            }
        ''')
        self.create_test_file('src/app/products/page.tsx')
        
        session = self.service.run_discovery()
        
        self.assertEqual(session.status, 'completed')
        self.assertGreater(session.routes_discovered, 0)
        self.assertIsNotNone(session.end_time)
        self.assertIsNotNone(session.scan_duration_ms)
        
        # Check that routes were saved to database
        routes = FrontendRoute.objects.all()
        self.assertGreater(routes.count(), 0)
    
    def test_run_discovery_failure(self):
        """Test route discovery failure handling"""
        # Mock scanner to raise an exception
        with patch.object(self.service.scanner, 'scan_routes', side_effect=Exception('Test error')):
            session = self.service.run_discovery()
            
            self.assertEqual(session.status, 'failed')
            self.assertIsNotNone(session.error_log)
            self.assertIn('Test error', session.error_log)
    
    def test_get_discovery_results(self):
        """Test getting discovery results"""
        # Create a completed session
        session = RouteDiscoverySession.objects.create(
            status='completed',
            routes_discovered=2,
            api_calls_discovered=3,
            scan_duration_ms=1500
        )
        
        # Create test routes
        route1 = FrontendRoute.objects.create(
            path='/',
            route_type='page',
            component_path='/test/page.tsx',
            component_name='HomePage',
            discovered_at=session.start_time
        )
        
        route2 = FrontendRoute.objects.create(
            path='/products',
            route_type='page',
            component_path='/test/products/page.tsx',
            component_name='ProductsPage',
            discovered_at=session.start_time
        )
        
        # Create API calls
        APICallDiscovery.objects.create(
            frontend_route=route1,
            method='GET',
            endpoint='/api/products',
            component_file='/test/page.tsx'
        )
        
        results = self.service.get_discovery_results()
        
        self.assertEqual(results['totalRoutes'], 2)
        self.assertEqual(results['apiCallsCount'], 1)
        self.assertEqual(results['scanDuration'], 1500)
        self.assertIsNotNone(results['lastScanned'])
    
    def test_validate_discovery_accuracy(self):
        """Test route discovery validation"""
        # Create test routes with valid and invalid paths
        valid_route = FrontendRoute.objects.create(
            path='/',
            route_type='page',
            component_path=__file__,  # Use this test file as valid path
            component_name='TestComponent'
        )
        
        invalid_route = FrontendRoute.objects.create(
            path='/invalid',
            route_type='page',
            component_path='/nonexistent/file.tsx',
            component_name='InvalidComponent'
        )
        
        results = self.service.validate_discovery_accuracy()
        
        self.assertEqual(results['totalRoutes'], 2)
        self.assertEqual(results['validRoutes'], 1)
        self.assertEqual(results['invalidRoutes'], 1)
        self.assertGreater(len(results['errors']), 0)
        
        # Check that validation status was updated
        valid_route.refresh_from_db()
        invalid_route.refresh_from_db()
        
        self.assertTrue(valid_route.is_valid)
        self.assertFalse(invalid_route.is_valid)


class RouteDiscoveryAPITest(APITestCase):
    """Test the route discovery API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_trigger_scan_endpoint(self):
        """Test the scan trigger endpoint"""
        with patch('apps.debugging.views.RouteDiscoveryService') as mock_service:
            mock_session = RouteDiscoverySession(
                status='completed',
                routes_discovered=5,
                api_calls_discovered=10,
                scan_duration_ms=2000
            )
            mock_service.return_value.run_discovery.return_value = mock_session
            
            response = self.client.post('/api/debugging/route-discovery/scan/')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['status'], 'completed')
            self.assertEqual(response.data['routes_discovered'], 5)
    
    def test_get_results_endpoint(self):
        """Test the results endpoint"""
        with patch('apps.debugging.views.RouteDiscoveryService') as mock_service:
            mock_results = {
                'routes': [],
                'totalRoutes': 0,
                'apiCallsCount': 0,
                'lastScanned': '2024-01-01T00:00:00Z',
                'scanDuration': 0
            }
            mock_service.return_value.get_discovery_results.return_value = mock_results
            
            response = self.client.get('/api/debugging/route-discovery/results/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['totalRoutes'], 0)
    
    def test_get_dependencies_endpoint(self):
        """Test the dependencies endpoint"""
        # Create test data
        route = FrontendRoute.objects.create(
            path='/',
            route_type='page',
            component_path='/test/page.tsx',
            component_name='HomePage'
        )
        
        api_call = APICallDiscovery.objects.create(
            frontend_route=route,
            method='GET',
            endpoint='/api/products',
            component_file='/test/page.tsx'
        )
        
        response = self.client.get('/api/debugging/route-discovery/dependencies/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('frontend_routes', response.data)
        self.assertIn('api_endpoints', response.data)
        self.assertIn('dependencies', response.data)
        
        # Check dependency mapping
        dependencies = response.data['dependencies']
        self.assertEqual(len(dependencies), 1)
        self.assertEqual(dependencies[0]['frontend_route'], '/')
        self.assertEqual(dependencies[0]['api_endpoint'], '/api/products')
    
    def test_get_routes_by_type_endpoint(self):
        """Test the routes by type endpoint"""
        # Create test routes
        FrontendRoute.objects.create(
            path='/',
            route_type='page',
            component_path='/test/page.tsx',
            component_name='HomePage'
        )
        
        FrontendRoute.objects.create(
            path='/api/users',
            route_type='api',
            component_path='/test/api/users/route.ts',
            component_name='UsersAPI'
        )
        
        # Test filtering by page type
        response = self.client.get('/api/debugging/route-discovery/routes/?type=page')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['route_type'], 'page')
        
        # Test filtering by API type
        response = self.client.get('/api/debugging/route-discovery/routes/?type=api')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['route_type'], 'api')
    
    def test_validate_endpoint(self):
        """Test the validation endpoint"""
        with patch('apps.debugging.views.RouteDiscoveryService') as mock_service:
            mock_results = {
                'totalRoutes': 10,
                'validRoutes': 8,
                'invalidRoutes': 2,
                'errors': ['Component file not found: /missing.tsx']
            }
            mock_service.return_value.validate_discovery_accuracy.return_value = mock_results
            
            response = self.client.post('/api/debugging/route-discovery/validate/')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['totalRoutes'], 10)
            self.assertEqual(response.data['validRoutes'], 8)
            self.assertEqual(response.data['invalidRoutes'], 2)
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication"""
        self.client.credentials()  # Remove authentication
        
        response = self.client.post('/api/debugging/route-discovery/scan/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.get('/api/debugging/route-discovery/results/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DependencyMapperTest(TestCase):
    """Test the dependency mapper"""
    
    def setUp(self):
        self.mapper = DependencyMapper()
    
    def test_create_dependency_map(self):
        """Test creating dependency map"""
        # Create test route with API calls
        route = FrontendRoute.objects.create(
            path='/',
            route_type='page',
            component_path='/test/page.tsx',
            component_name='HomePage'
        )
        
        # Create API calls
        APICallDiscovery.objects.create(
            frontend_route=route,
            method='GET',
            endpoint='/api/products',
            component_file='/test/page.tsx',
            function_name='useEffect'
        )
        
        APICallDiscovery.objects.create(
            frontend_route=route,
            method='POST',
            endpoint='/api/orders',
            component_file='/test/page.tsx',
            function_name='handleSubmit'
        )
        
        dependencies = self.mapper.create_dependency_map([route])
        
        self.assertEqual(len(dependencies), 2)
        
        # Check dependency types
        get_dep = next((d for d in dependencies if d['method'] == 'GET'), None)
        self.assertIsNotNone(get_dep)
        self.assertEqual(get_dep['dependency_type'], 'direct')
        self.assertTrue(get_dep['is_critical'])
        
        post_dep = next((d for d in dependencies if d['method'] == 'POST'), None)
        self.assertIsNotNone(post_dep)
        self.assertFalse(post_dep['is_critical'])  # POST requests are usually conditional
    
    def test_determine_dependency_type(self):
        """Test dependency type determination"""
        # Create API calls with different function contexts
        route = FrontendRoute.objects.create(
            path='/',
            route_type='page',
            component_path='/test/page.tsx',
            component_name='HomePage'
        )
        
        # Direct dependency (useEffect)
        direct_call = APICallDiscovery.objects.create(
            frontend_route=route,
            method='GET',
            endpoint='/api/data',
            function_name='useEffect'
        )
        
        # Conditional dependency (onClick)
        conditional_call = APICallDiscovery.objects.create(
            frontend_route=route,
            method='POST',
            endpoint='/api/action',
            function_name='onClick'
        )
        
        # Lazy dependency
        lazy_call = APICallDiscovery.objects.create(
            frontend_route=route,
            method='GET',
            endpoint='/api/lazy',
            function_name='lazyLoad'
        )
        
        # Test dependency type determination
        self.assertEqual(self.mapper._determine_dependency_type(direct_call), 'direct')
        self.assertEqual(self.mapper._determine_dependency_type(conditional_call), 'conditional')
        self.assertEqual(self.mapper._determine_dependency_type(lazy_call), 'lazy')
    
    def test_is_critical_dependency(self):
        """Test critical dependency determination"""
        route = FrontendRoute.objects.create(
            path='/',
            route_type='page',
            component_path='/test/page.tsx',
            component_name='HomePage'
        )
        
        # Critical: GET request
        get_call = APICallDiscovery.objects.create(
            frontend_route=route,
            method='GET',
            endpoint='/api/products'
        )
        
        # Critical: Auth endpoint
        auth_call = APICallDiscovery.objects.create(
            frontend_route=route,
            method='POST',
            endpoint='/api/auth/login'
        )
        
        # Non-critical: Other POST
        post_call = APICallDiscovery.objects.create(
            frontend_route=route,
            method='POST',
            endpoint='/api/feedback'
        )
        
        self.assertTrue(self.mapper._is_critical_dependency(get_call))
        self.assertTrue(self.mapper._is_critical_dependency(auth_call))
        self.assertFalse(self.mapper._is_critical_dependency(post_call))