"""
Simple tests for Route Discovery Service functionality
"""

import os
import tempfile
import shutil
from django.test import TestCase

from .route_discovery import NextJSRouteScanner, APICallExtractor


class SimpleRouteScannerTest(TestCase):
    """Simple test for the Next.js route scanner"""
    
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
        
        routes = self.scanner.scan_routes()
        
        self.assertEqual(len(routes), 2)
        
        # Check root page
        root_route = next((r for r in routes if r['path'] == '/'), None)
        self.assertIsNotNone(root_route)
        self.assertEqual(root_route['route_type'], 'page')
        self.assertFalse(root_route['is_dynamic'])
    
    def test_scan_dynamic_routes(self):
        """Test scanning dynamic routes"""
        self.create_test_file('src/app/products/[id]/page.tsx')
        
        routes = self.scanner.scan_routes()
        
        self.assertEqual(len(routes), 1)
        
        # Check dynamic route
        dynamic_route = routes[0]
        self.assertEqual(dynamic_route['path'], '/products/[id]')
        self.assertTrue(dynamic_route['is_dynamic'])
        self.assertIn('id', dynamic_route['dynamic_segments'])
    
    def test_nonexistent_directory(self):
        """Test handling of nonexistent app directory"""
        scanner = NextJSRouteScanner('/nonexistent/path')
        routes = scanner.scan_routes()
        
        self.assertEqual(len(routes), 0)
        self.assertGreater(len(scanner.errors), 0)


class SimpleAPICallExtractorTest(TestCase):
    """Simple test for the API call extractor"""
    
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
                        'Authorization': 'Bearer token'
                    }
                });
            }, []);
            
            return <div>Component</div>;
        }
        '''
        self.write_component(content)
        
        api_calls = self.extractor.extract_api_calls(self.temp_file.name)
        
        self.assertEqual(len(api_calls), 1)
        
        # Check GET call
        get_call = api_calls[0]
        self.assertEqual(get_call['method'], 'GET')
        self.assertEqual(get_call['endpoint'], '/api/products')
        self.assertTrue(get_call['requires_authentication'])
    
    def test_extract_axios_calls(self):
        """Test extracting axios API calls"""
        content = '''
        import axios from 'axios';
        
        export default function Component() {
            const fetchData = async () => {
                await axios.get('/api/users');
                await axios.post('/api/users', userData);
            };
            
            return <div>Component</div>;
        }
        '''
        self.write_component(content)
        
        api_calls = self.extractor.extract_api_calls(self.temp_file.name)
        
        self.assertEqual(len(api_calls), 2)
        
        # Check different axios call patterns
        methods = [call['method'] for call in api_calls]
        self.assertIn('GET', methods)
        self.assertIn('POST', methods)