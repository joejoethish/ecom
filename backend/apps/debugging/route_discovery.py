"""
Frontend Route Discovery Service
Analyzes Next.js app directory structure and discovers routes and API calls
"""

import os
import re
import ast
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from django.conf import settings
from django.utils import timezone

from .models import (
    FrontendRoute, APICallDiscovery, RouteDiscoverySession, 
    RouteDependency, ErrorLog
)


class NextJSRouteScanner:
    """Scans Next.js app directory structure to discover routes"""
    
    def __init__(self, frontend_path: str = None):
        self.frontend_path = frontend_path or self._get_frontend_path()
        self.app_dir = os.path.join(self.frontend_path, 'src', 'app')
        self.routes_discovered = []
        self.errors = []
    
    def _get_frontend_path(self) -> str:
        """Get the frontend directory path"""
        base_dir = getattr(settings, 'BASE_DIR', os.getcwd())
        # Go up one level from backend to find frontend
        project_root = os.path.dirname(base_dir)
        return os.path.join(project_root, 'frontend')
    
    def scan_routes(self) -> List[Dict[str, Any]]:
        """Scan the Next.js app directory for routes"""
        if not os.path.exists(self.app_dir):
            self.errors.append(f"App directory not found: {self.app_dir}")
            return []
        
        self.routes_discovered = []
        self._scan_directory(self.app_dir, '')
        return self.routes_discovered
    
    def _scan_directory(self, directory: str, route_path: str):
        """Recursively scan directory for route files"""
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                if os.path.isdir(item_path):
                    # Handle route groups (folders in parentheses)
                    if item.startswith('(') and item.endswith(')'):
                        # Route groups don't affect the URL path
                        self._scan_directory(item_path, route_path)
                    else:
                        # Regular directory becomes part of the route
                        new_route_path = f"{route_path}/{item}" if route_path else f"/{item}"
                        self._scan_directory(item_path, new_route_path)
                
                elif os.path.isfile(item_path) and item.endswith(('.tsx', '.ts', '.jsx', '.js')):
                    self._process_route_file(item_path, route_path, item)
        
        except Exception as e:
            self.errors.append(f"Error scanning directory {directory}: {str(e)}")
    
    def _process_route_file(self, file_path: str, route_path: str, filename: str):
        """Process individual route files"""
        try:
            # Determine route type based on filename
            route_type = self._get_route_type(filename)
            
            # Skip non-route files
            if route_type is None:
                return
            
            # Handle dynamic routes
            is_dynamic = '[' in route_path or filename.startswith('[')
            dynamic_segments = self._extract_dynamic_segments(route_path, filename)
            
            # Determine final route path
            final_route_path = self._get_final_route_path(route_path, filename, route_type)
            
            # Get component name
            component_name = self._extract_component_name(file_path)
            
            route_info = {
                'path': final_route_path,
                'route_type': route_type,
                'component_path': file_path,
                'component_name': component_name,
                'is_dynamic': is_dynamic,
                'dynamic_segments': dynamic_segments,
                'metadata': {
                    'filename': filename,
                    'directory': os.path.dirname(file_path),
                    'relative_path': os.path.relpath(file_path, self.frontend_path)
                }
            }
            
            self.routes_discovered.append(route_info)
        
        except Exception as e:
            self.errors.append(f"Error processing file {file_path}: {str(e)}")
    
    def _get_route_type(self, filename: str) -> Optional[str]:
        """Determine route type based on filename"""
        if filename == 'page.tsx' or filename == 'page.js':
            return 'page'
        elif filename == 'route.tsx' or filename == 'route.js' or filename == 'route.ts':
            return 'api'
        elif filename == 'layout.tsx' or filename == 'layout.js':
            return 'layout'
        elif filename == 'loading.tsx' or filename == 'loading.js':
            return 'loading'
        elif filename == 'error.tsx' or filename == 'error.js':
            return 'error'
        elif filename == 'not-found.tsx' or filename == 'not-found.js':
            return 'not_found'
        else:
            return None
    
    def _extract_dynamic_segments(self, route_path: str, filename: str) -> List[str]:
        """Extract dynamic segments from route path"""
        segments = []
        
        # Extract from route path
        path_segments = re.findall(r'\[([^\]]+)\]', route_path)
        segments.extend(path_segments)
        
        # Extract from filename
        file_segments = re.findall(r'\[([^\]]+)\]', filename)
        segments.extend(file_segments)
        
        return list(set(segments))  # Remove duplicates
    
    def _get_final_route_path(self, route_path: str, filename: str, route_type: str) -> str:
        """Get the final route path for the URL"""
        if route_type == 'api':
            # API routes use the directory path
            return f"/api{route_path}" if route_path else "/api"
        elif route_type == 'page':
            # Page routes use the directory path
            return route_path if route_path else "/"
        else:
            # Other types (layout, loading, error) don't create routes
            return route_path if route_path else "/"
    
    def _extract_component_name(self, file_path: str) -> str:
        """Extract component name from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for default export function/component
            patterns = [
                r'export\s+default\s+function\s+(\w+)',
                r'export\s+default\s+(\w+)',
                r'const\s+(\w+)\s*=.*export\s+default\s+\1',
                r'function\s+(\w+).*export\s+default\s+\1'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
            
            # Fallback to filename
            return os.path.splitext(os.path.basename(file_path))[0]
        
        except Exception:
            return os.path.splitext(os.path.basename(file_path))[0]


class APICallExtractor:
    """Extracts API calls from React components"""
    
    def __init__(self):
        self.api_calls = []
        self.errors = []
    
    def extract_api_calls(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract API calls from a component file"""
        self.api_calls = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract fetch calls
            self._extract_fetch_calls(content, file_path)
            
            # Extract axios calls
            self._extract_axios_calls(content, file_path)
            
            # Extract custom API service calls
            self._extract_service_calls(content, file_path)
            
        except Exception as e:
            self.errors.append(f"Error extracting API calls from {file_path}: {str(e)}")
        
        return self.api_calls
    
    def _extract_fetch_calls(self, content: str, file_path: str):
        """Extract fetch() API calls"""
        # Pattern to match fetch calls
        fetch_pattern = r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*(?:,\s*\{([^}]+)\})?\s*\)'
        
        for match in re.finditer(fetch_pattern, content, re.MULTILINE | re.DOTALL):
            url = match.group(1)
            options_str = match.group(2) if match.group(2) else ''
            
            # Extract method from options
            method = 'GET'  # default
            method_match = re.search(r'method\s*:\s*[\'"`](\w+)[\'"`]', options_str)
            if method_match:
                method = method_match.group(1).upper()
            
            # Extract headers
            headers = {}
            headers_match = re.search(r'headers\s*:\s*\{([^}]+)\}', options_str)
            if headers_match:
                headers_str = headers_match.group(1)
                # Simple header extraction
                header_pairs = re.findall(r'[\'"`]([^\'"`]+)[\'"`]\s*:\s*[\'"`]([^\'"`]+)[\'"`]', headers_str)
                headers = dict(header_pairs)
            
            # Check for authentication
            requires_auth = 'Authorization' in headers or 'Bearer' in options_str
            
            api_call = {
                'method': method,
                'endpoint': url,
                'component_file': file_path,
                'line_number': content[:match.start()].count('\n') + 1,
                'function_name': self._find_containing_function(content, match.start()),
                'requires_authentication': requires_auth,
                'headers': headers,
                'call_type': 'fetch'
            }
            
            self.api_calls.append(api_call)
    
    def _extract_axios_calls(self, content: str, file_path: str):
        """Extract axios API calls"""
        # Patterns for different axios call styles
        patterns = [
            r'axios\.(\w+)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',  # axios.get('/api/...')
            r'axios\s*\(\s*\{[^}]*url\s*:\s*[\'"`]([^\'"`]+)[\'"`][^}]*method\s*:\s*[\'"`](\w+)[\'"`]',  # axios({url: '...', method: '...'})
            r'axios\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*\{[^}]*method\s*:\s*[\'"`](\w+)[\'"`]'  # axios('/api/...', {method: '...'})
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                if 'url' in pattern:
                    url = match.group(1)
                    method = match.group(2).upper()
                else:
                    method = match.group(1).upper()
                    url = match.group(2)
                
                api_call = {
                    'method': method,
                    'endpoint': url,
                    'component_file': file_path,
                    'line_number': content[:match.start()].count('\n') + 1,
                    'function_name': self._find_containing_function(content, match.start()),
                    'requires_authentication': 'Authorization' in match.group(0) or 'Bearer' in match.group(0),
                    'headers': {},
                    'call_type': 'axios'
                }
                
                self.api_calls.append(api_call)
    
    def _extract_service_calls(self, content: str, file_path: str):
        """Extract calls to custom API service functions"""
        # Look for imports from services
        service_imports = re.findall(r'import\s+\{([^}]+)\}\s+from\s+[\'"`]@/services/(\w+)[\'"`]', content)
        
        for imports, service_name in service_imports:
            functions = [f.strip() for f in imports.split(',')]
            
            for func in functions:
                # Find calls to this function
                func_calls = re.finditer(rf'{func}\s*\(', content)
                
                for call_match in func_calls:
                    api_call = {
                        'method': 'UNKNOWN',  # Would need to analyze service file
                        'endpoint': f'/api/{service_name}/*',  # Placeholder
                        'component_file': file_path,
                        'line_number': content[:call_match.start()].count('\n') + 1,
                        'function_name': self._find_containing_function(content, call_match.start()),
                        'requires_authentication': True,  # Assume services require auth
                        'headers': {},
                        'call_type': 'service',
                        'service_name': service_name,
                        'service_function': func
                    }
                    
                    self.api_calls.append(api_call)
    
    def _find_containing_function(self, content: str, position: int) -> Optional[str]:
        """Find the function that contains the given position"""
        # Look backwards for function declaration
        before_content = content[:position]
        
        # Patterns for function declarations
        patterns = [
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{[^}]*$',
            r'(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*$',
            r'(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{[^}]*$'
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, before_content, re.MULTILINE | re.DOTALL))
            if matches:
                return matches[-1].group(1)
        
        return None


class DependencyMapper:
    """Maps dependencies between frontend routes and backend API endpoints"""
    
    def __init__(self):
        self.dependencies = []
        self.errors = []
    
    def create_dependency_map(self, routes: List[FrontendRoute]) -> List[Dict[str, Any]]:
        """Create dependency mapping for discovered routes"""
        self.dependencies = []
        
        for route in routes:
            try:
                self._analyze_route_dependencies(route)
            except Exception as e:
                self.errors.append(f"Error analyzing dependencies for {route.path}: {str(e)}")
        
        return self.dependencies
    
    def _analyze_route_dependencies(self, route: FrontendRoute):
        """Analyze dependencies for a specific route"""
        # Get API calls for this route
        api_calls = APICallDiscovery.objects.filter(frontend_route=route)
        
        for api_call in api_calls:
            dependency = {
                'frontend_route': route.path,
                'api_endpoint': api_call.endpoint,
                'method': api_call.method,
                'component': route.component_name,
                'dependency_type': self._determine_dependency_type(api_call),
                'is_critical': self._is_critical_dependency(api_call),
                'load_order': self._determine_load_order(api_call)
            }
            
            self.dependencies.append(dependency)
    
    def _determine_dependency_type(self, api_call: APICallDiscovery) -> str:
        """Determine the type of dependency"""
        # Analyze the context of the API call
        if 'useEffect' in api_call.function_name or 'componentDidMount' in api_call.function_name:
            return 'direct'
        elif 'onClick' in api_call.function_name or 'onSubmit' in api_call.function_name:
            return 'conditional'
        elif 'lazy' in api_call.function_name.lower() or 'dynamic' in api_call.function_name.lower():
            return 'lazy'
        else:
            return 'direct'
    
    def _is_critical_dependency(self, api_call: APICallDiscovery) -> bool:
        """Determine if this dependency is critical for route functionality"""
        # GET requests for data are usually critical
        if api_call.method == 'GET':
            return True
        
        # Authentication endpoints are critical
        if 'auth' in api_call.endpoint.lower() or 'login' in api_call.endpoint.lower():
            return True
        
        # Other methods are usually conditional
        return False
    
    def _determine_load_order(self, api_call: APICallDiscovery) -> int:
        """Determine the load order of this API call"""
        # Authentication calls should be first
        if 'auth' in api_call.endpoint.lower():
            return 1
        
        # Data fetching calls
        if api_call.method == 'GET':
            return 2
        
        # Other calls
        return 3


class RouteDiscoveryService:
    """Main service for frontend route discovery"""
    
    def __init__(self):
        self.scanner = NextJSRouteScanner()
        self.extractor = APICallExtractor()
        self.mapper = DependencyMapper()
        self.session = None
    
    def run_discovery(self) -> RouteDiscoverySession:
        """Run complete route discovery process"""
        # Create discovery session
        self.session = RouteDiscoverySession.objects.create()
        
        try:
            start_time = time.time()
            
            # Step 1: Scan routes
            routes_data = self.scanner.scan_routes()
            
            # Step 2: Save routes to database
            routes = self._save_routes(routes_data)
            
            # Step 3: Extract API calls for each route
            self._extract_api_calls_for_routes(routes)
            
            # Step 4: Create dependency mapping
            self.mapper.create_dependency_map(routes)
            
            # Update session
            end_time = time.time()
            self.session.status = 'completed'
            self.session.end_time = timezone.now()
            self.session.routes_discovered = len(routes)
            self.session.api_calls_discovered = APICallDiscovery.objects.filter(
                frontend_route__in=routes
            ).count()
            self.session.scan_duration_ms = int((end_time - start_time) * 1000)
            self.session.save()
            
        except Exception as e:
            # Mark session as failed
            self.session.status = 'failed'
            self.session.end_time = timezone.now()
            self.session.error_log = str(e)
            self.session.save()
            
            # Log error
            ErrorLog.objects.create(
                layer='api',
                component='RouteDiscoveryService',
                error_type='DiscoveryError',
                error_message=str(e),
                metadata={'session_id': str(self.session.session_id)}
            )
            
            raise
        
        return self.session
    
    def _save_routes(self, routes_data: List[Dict[str, Any]]) -> List[FrontendRoute]:
        """Save discovered routes to database"""
        routes = []
        
        for route_data in routes_data:
            route, created = FrontendRoute.objects.update_or_create(
                path=route_data['path'],
                defaults={
                    'route_type': route_data['route_type'],
                    'component_path': route_data['component_path'],
                    'component_name': route_data['component_name'],
                    'is_dynamic': route_data['is_dynamic'],
                    'dynamic_segments': route_data['dynamic_segments'],
                    'metadata': route_data['metadata'],
                    'is_valid': True
                }
            )
            routes.append(route)
        
        return routes
    
    def _extract_api_calls_for_routes(self, routes: List[FrontendRoute]):
        """Extract API calls for all routes"""
        for route in routes:
            try:
                # Only extract API calls for page and API routes
                if route.route_type in ['page', 'api']:
                    api_calls_data = self.extractor.extract_api_calls(route.component_path)
                    
                    # Save API calls to database
                    for api_call_data in api_calls_data:
                        APICallDiscovery.objects.update_or_create(
                            frontend_route=route,
                            endpoint=api_call_data['endpoint'],
                            method=api_call_data['method'],
                            defaults={
                                'component_file': api_call_data['component_file'],
                                'line_number': api_call_data.get('line_number'),
                                'function_name': api_call_data.get('function_name'),
                                'requires_authentication': api_call_data.get('requires_authentication', False),
                                'headers': api_call_data.get('headers', {}),
                                'is_valid': True
                            }
                        )
            
            except Exception as e:
                # Log error but continue with other routes
                ErrorLog.objects.create(
                    layer='api',
                    component='RouteDiscoveryService',
                    error_type='APIExtractionError',
                    error_message=f"Failed to extract API calls for route {route.path}: {str(e)}",
                    metadata={'route_id': route.id, 'session_id': str(self.session.session_id)}
                )
    
    def get_discovery_results(self) -> Dict[str, Any]:
        """Get the latest discovery results"""
        latest_session = RouteDiscoverySession.objects.filter(
            status='completed'
        ).order_by('-start_time').first()
        
        if not latest_session:
            return {
                'routes': [],
                'totalRoutes': 0,
                'apiCallsCount': 0,
                'lastScanned': None,
                'scanDuration': 0
            }
        
        routes = FrontendRoute.objects.filter(
            discovered_at__gte=latest_session.start_time
        ).prefetch_related('api_calls')
        
        routes_data = []
        total_api_calls = 0
        
        for route in routes:
            api_calls = []
            for api_call in route.api_calls.all():
                api_calls.append({
                    'method': api_call.method,
                    'endpoint': api_call.endpoint,
                    'authentication': api_call.requires_authentication,
                    'component': api_call.component_file,
                    'lineNumber': api_call.line_number
                })
                total_api_calls += 1
            
            routes_data.append({
                'path': route.path,
                'type': route.route_type,
                'component': route.component_name,
                'apiCalls': api_calls,
                'dependencies': [],  # TODO: Add dependency data
                'metadata': route.metadata
            })
        
        return {
            'routes': routes_data,
            'totalRoutes': len(routes_data),
            'apiCallsCount': total_api_calls,
            'lastScanned': latest_session.start_time.isoformat(),
            'scanDuration': latest_session.scan_duration_ms or 0
        }
    
    def validate_discovery_accuracy(self) -> Dict[str, Any]:
        """Validate the accuracy of route discovery"""
        routes = FrontendRoute.objects.all()
        valid_routes = 0
        invalid_routes = 0
        errors = []
        
        for route in routes:
            try:
                # Check if component file exists
                if os.path.exists(route.component_path):
                    route.is_valid = True
                    route.last_validated = timezone.now()
                    valid_routes += 1
                else:
                    route.is_valid = False
                    invalid_routes += 1
                    errors.append(f"Component file not found: {route.component_path}")
                
                route.save()
                
            except Exception as e:
                invalid_routes += 1
                errors.append(f"Error validating route {route.path}: {str(e)}")
        
        return {
            'totalRoutes': routes.count(),
            'validRoutes': valid_routes,
            'invalidRoutes': invalid_routes,
            'errors': errors
        }