"""
Core views for the ecommerce platform.

This module provides views for rendering API documentation guides and other
core functionality for the ecommerce platform.
"""
import os
import markdown
import json
from django.conf import settings
from django.http import HttpResponse, Http404, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenApiJsonRenderer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


# Define all available guides with metadata
API_GUIDES = [
    {'name': 'authentication', 'title': 'Authentication Guide', 'file': 'api/authentication_guide.md'},
    {'name': 'error-handling', 'title': 'Error Handling Guide', 'file': 'api/error_handling.md'},
    {'name': 'usage', 'title': 'API Usage Guide', 'file': 'api/usage_guide.md'},
    {'name': 'versioning', 'title': 'API Versioning Guide', 'file': 'api/versioning_guide.md'},
]


@cache_page(60 * 15)  # Cache for 15 minutes
def api_documentation_guide(request, guide_name):
    """
    View to render API documentation guides from markdown files.
    
    Args:
        request: HTTP request
        guide_name: Name of the guide to render
    
    Returns:
        HTTP response with rendered guide
    """
    # Find the guide by name
    guide = next((g for g in API_GUIDES if g['name'] == guide_name), None)
    
    if not guide:
        raise Http404("Guide not found")
    
    file_path = os.path.join(settings.BASE_DIR, 'docs', guide['file'])
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Convert markdown to HTML
            html_content = markdown.markdown(
                content,
                extensions=[
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.tables',
                    'markdown.extensions.toc',
                    'markdown.extensions.codehilite',
                ]
            )
            
            # Render template with guide content
            context = {
                'title': guide['title'],
                'content': mark_safe(html_content),
                'guide_name': guide_name,
                'guides': API_GUIDES
            }
            
            return HttpResponse(render_to_string('docs/guide.html', context))
    except FileNotFoundError:
        raise Http404("Guide file not found")


@api_view(['GET'])
@permission_classes([AllowAny])
def api_guides_list(request):
    """
    View to list all available API guides.
    
    Args:
        request: HTTP request
    
    Returns:
        JSON response with list of guides
    """
    return JsonResponse({
        'guides': [
            {
                'name': guide['name'],
                'title': guide['title'],
                'url': request.build_absolute_uri(f'/api/docs/guides/{guide["name"]}/')
            }
            for guide in API_GUIDES
        ]
    })


@require_http_methods(["GET"])
def api_endpoints_list(request):
    """
    View to list all API endpoints with their documentation.
    
    Args:
        request: HTTP request
    
    Returns:
        JSON response with list of endpoints
    """
    # Generate schema
    generator = SchemaGenerator()
    schema = generator.get_schema(request=request, public=True)
    
    # Extract endpoints from schema
    paths = schema.get('paths', {})
    endpoints = []
    
    for path, methods in paths.items():
        for method, details in methods.items():
            endpoints.append({
                'path': path,
                'method': method.upper(),
                'summary': details.get('summary', ''),
                'description': details.get('description', ''),
                'tags': details.get('tags', []),
                'deprecated': details.get('deprecated', False),
            })
    
    # Group endpoints by tag
    grouped_endpoints = {}
    for endpoint in endpoints:
        for tag in endpoint.get('tags', ['Other']):
            if tag not in grouped_endpoints:
                grouped_endpoints[tag] = []
            grouped_endpoints[tag].append(endpoint)
    
    return JsonResponse({
        'endpoints': grouped_endpoints
    })