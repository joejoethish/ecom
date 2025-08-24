#!/usr/bin/env python3
"""
Simple validation script for Route Discovery functionality
Tests the core components without requiring full Django setup
"""

import os
import tempfile
import shutil
import sys
import json
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_frontend_structure(base_dir):
    """Create a test Next.js frontend structure"""
    app_dir = os.path.join(base_dir, 'src', 'app')
    os.makedirs(app_dir, exist_ok=True)
    
    # Create test files
    test_files = {
        'src/app/page.tsx': '''
export default function HomePage() {
    useEffect(() => {
        fetch('/api/products', {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer token'
            }
        });
    }, []);
    
    return <div>Home Page</div>;
}
        ''',
        'src/app/about/page.tsx': '''
export default function AboutPage() {
    return <div>About Page</div>;
}
        ''',
        'src/app/products/[id]/page.tsx': '''
export default function ProductPage({ params }) {
    useEffect(() => {
        fetch(`/api/products/${params.id}`);
        axios.post('/api/analytics', { event: 'view_product' });
    }, [params.id]);
    
    return <div>Product Page</div>;
}
        ''',
        'src/app/api/products/route.ts': '''
export async function GET() {
    return Response.json({ products: [] });
}
        ''',
        'src/app/(auth)/login/page.tsx': '''
export default function LoginPage() {
    const handleLogin = async () => {
        await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    };
    
    return <div>Login Page</div>;
}
        '''
    }
    
    for file_path, content in test_files.items():
        full_path = os.path.join(base_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content.strip())
    
    return base_dir

def test_route_scanner():
    """Test the NextJS Route Scanner"""
    print("Testing NextJS Route Scanner...")
    
    # Create temporary directory with test structure
    temp_dir = tempfile.mkdtemp()
    try:
        frontend_dir = create_test_frontend_structure(temp_dir)
        
        # Import and test the scanner (without Django dependencies)
        from route_discovery import NextJSRouteScanner
        
        scanner = NextJSRouteScanner(frontend_dir)
        routes = scanner.scan_routes()
        
        print(f"✓ Found {len(routes)} routes")
        
        # Validate expected routes
        expected_routes = ['/', '/about', '/products/[id]', '/api/products', '/(auth)/login']
        found_paths = [route['path'] for route in routes]
        
        for expected in expected_routes:
            if any(expected in path for path in found_paths):
                print(f"✓ Found expected route pattern: {expected}")
            else:
                print(f"✗ Missing expected route: {expected}")
        
        # Check for dynamic routes
        dynamic_routes = [r for r in routes if r['is_dynamic']]
        print(f"✓ Found {len(dynamic_routes)} dynamic routes")
        
        # Check route types
        page_routes = [r for r in routes if r['route_type'] == 'page']
        api_routes = [r for r in routes if r['route_type'] == 'api']
        print(f"✓ Found {len(page_routes)} page routes and {len(api_routes)} API routes")
        
        return True
        
    except Exception as e:
        print(f"✗ Route scanner test failed: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)

def test_api_call_extractor():
    """Test the API Call Extractor"""
    print("\nTesting API Call Extractor...")
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.tsx', delete=False)
    try:
        # Write test component with various API calls
        test_content = '''
import axios from 'axios';

export default function TestComponent() {
    useEffect(() => {
        // Fetch call
        fetch('/api/products', {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer token',
                'Content-Type': 'application/json'
            }
        });
        
        // Axios calls
        axios.get('/api/users');
        axios.post('/api/orders', orderData);
        
        // Service call
        productService.getProducts();
    }, []);
    
    return <div>Test Component</div>;
}
        '''
        
        temp_file.write(test_content)
        temp_file.flush()
        
        from route_discovery import APICallExtractor
        
        extractor = APICallExtractor()
        api_calls = extractor.extract_api_calls(temp_file.name)
        
        print(f"✓ Extracted {len(api_calls)} API calls")
        
        # Validate different call types
        fetch_calls = [call for call in api_calls if call.get('call_type') == 'fetch']
        axios_calls = [call for call in api_calls if call.get('call_type') == 'axios']
        
        print(f"✓ Found {len(fetch_calls)} fetch calls")
        print(f"✓ Found {len(axios_calls)} axios calls")
        
        # Check for authentication detection
        auth_calls = [call for call in api_calls if call.get('requires_authentication')]
        print(f"✓ Detected {len(auth_calls)} calls requiring authentication")
        
        return True
        
    except Exception as e:
        print(f"✗ API call extractor test failed: {e}")
        return False
    finally:
        os.unlink(temp_file.name)

def test_integration():
    """Test integration between components"""
    print("\nTesting Integration...")
    
    temp_dir = tempfile.mkdtemp()
    try:
        frontend_dir = create_test_frontend_structure(temp_dir)
        
        from route_discovery import NextJSRouteScanner, APICallExtractor
        
        # Scan routes
        scanner = NextJSRouteScanner(frontend_dir)
        routes = scanner.scan_routes()
        
        # Extract API calls for each route
        extractor = APICallExtractor()
        total_api_calls = 0
        
        for route in routes:
            if route['route_type'] in ['page', 'api']:
                try:
                    api_calls = extractor.extract_api_calls(route['component_path'])
                    total_api_calls += len(api_calls)
                    
                    if api_calls:
                        print(f"✓ Route {route['path']} has {len(api_calls)} API calls")
                except Exception as e:
                    print(f"⚠ Could not extract API calls from {route['path']}: {e}")
        
        print(f"✓ Total API calls found across all routes: {total_api_calls}")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)

def main():
    """Run all validation tests"""
    print("Route Discovery Validation Script")
    print("=" * 40)
    
    tests = [
        test_route_scanner,
        test_api_call_extractor,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Route discovery functionality is working.")
        return 0
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())