from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.documentation.models import (
    DocumentationCategory, DocumentationTemplate, Documentation
)
import os
import ast
import inspect

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate documentation from code automatically'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Django app to generate docs for',
        )
        parser.add_argument(
            '--output-category',
            type=str,
            default='API Documentation',
            help='Category to create docs in',
        )

    def handle(self, *args, **options):
        app_name = options.get('app')
        category_name = options.get('output_category')

        # Get or create category
        category, created = DocumentationCategory.objects.get_or_create(
            name=category_name,
            defaults={
                'description': f'Auto-generated documentation for {app_name or "the application"}',
                'icon': 'code',
                'color': '#10B981'
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created category: {category_name}')
            )

        # Get admin user for authoring
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('No admin user found. Please create an admin user first.')
            )
            return

        if app_name:
            self.generate_app_docs(app_name, category, admin_user)
        else:
            self.generate_general_docs(category, admin_user)

    def generate_app_docs(self, app_name, category, author):
        """Generate documentation for a specific Django app"""
        try:
            # Import the app
            app_module = __import__(f'apps.{app_name}', fromlist=[''])
            
            # Generate model documentation
            self.generate_model_docs(app_name, category, author)
            
            # Generate view documentation
            self.generate_view_docs(app_name, category, author)
            
            # Generate API documentation
            self.generate_api_docs(app_name, category, author)
            
            self.stdout.write(
                self.style.SUCCESS(f'Generated documentation for app: {app_name}')
            )
            
        except ImportError:
            self.stdout.write(
                self.style.ERROR(f'Could not import app: {app_name}')
            )

    def generate_model_docs(self, app_name, category, author):
        """Generate documentation for Django models"""
        try:
            models_module = __import__(f'apps.{app_name}.models', fromlist=[''])
            
            # Get all model classes
            model_classes = []
            for name in dir(models_module):
                obj = getattr(models_module, name)
                if (inspect.isclass(obj) and 
                    hasattr(obj, '_meta') and 
                    hasattr(obj._meta, 'app_label')):
                    model_classes.append(obj)

            if model_classes:
                content = self.generate_models_content(model_classes)
                
                Documentation.objects.update_or_create(
                    title=f'{app_name.title()} Models',
                    category=category,
                    defaults={
                        'content': content,
                        'excerpt': f'Data models for the {app_name} application',
                        'author': author,
                        'status': 'published',
                        'visibility': 'internal'
                    }
                )
                
        except ImportError:
            pass

    def generate_models_content(self, model_classes):
        """Generate markdown content for models"""
        content = f"# Models Documentation\n\n"
        content += "This document describes the data models used in this application.\n\n"
        
        for model_class in model_classes:
            content += f"## {model_class.__name__}\n\n"
            
            # Add model docstring if available
            if model_class.__doc__:
                content += f"{model_class.__doc__}\n\n"
            
            # Add fields
            content += "### Fields\n\n"
            content += "| Field | Type | Description |\n"
            content += "|-------|------|-------------|\n"
            
            for field in model_class._meta.fields:
                field_type = field.__class__.__name__
                help_text = getattr(field, 'help_text', '') or ''
                content += f"| {field.name} | {field_type} | {help_text} |\n"
            
            content += "\n"
            
            # Add methods
            methods = [method for method in dir(model_class) 
                      if not method.startswith('_') and 
                      callable(getattr(model_class, method))]
            
            if methods:
                content += "### Methods\n\n"
                for method in methods[:10]:  # Limit to first 10 methods
                    try:
                        method_obj = getattr(model_class, method)
                        if hasattr(method_obj, '__doc__') and method_obj.__doc__:
                            content += f"- **{method}()**: {method_obj.__doc__.strip()}\n"
                        else:
                            content += f"- **{method}()**\n"
                    except:
                        content += f"- **{method}()**\n"
                content += "\n"
        
        return content

    def generate_view_docs(self, app_name, category, author):
        """Generate documentation for views"""
        try:
            views_module = __import__(f'apps.{app_name}.views', fromlist=[''])
            
            # Get view classes and functions
            views = []
            for name in dir(views_module):
                obj = getattr(views_module, name)
                if (inspect.isclass(obj) or inspect.isfunction(obj)) and not name.startswith('_'):
                    views.append((name, obj))

            if views:
                content = self.generate_views_content(views)
                
                Documentation.objects.update_or_create(
                    title=f'{app_name.title()} Views',
                    category=category,
                    defaults={
                        'content': content,
                        'excerpt': f'View functions and classes for the {app_name} application',
                        'author': author,
                        'status': 'published',
                        'visibility': 'internal'
                    }
                )
                
        except ImportError:
            pass

    def generate_views_content(self, views):
        """Generate markdown content for views"""
        content = f"# Views Documentation\n\n"
        content += "This document describes the views used in this application.\n\n"
        
        for name, view_obj in views:
            content += f"## {name}\n\n"
            
            # Add docstring if available
            if hasattr(view_obj, '__doc__') and view_obj.__doc__:
                content += f"{view_obj.__doc__}\n\n"
            
            # Add type information
            if inspect.isclass(view_obj):
                content += f"**Type**: Class-based view\n\n"
                
                # Add methods for class-based views
                methods = [method for method in dir(view_obj) 
                          if not method.startswith('_') and 
                          callable(getattr(view_obj, method))]
                
                if methods:
                    content += "### Methods\n\n"
                    for method in methods[:5]:  # Limit to first 5 methods
                        content += f"- {method}\n"
                    content += "\n"
                    
            else:
                content += f"**Type**: Function-based view\n\n"
                
                # Add function signature
                try:
                    sig = inspect.signature(view_obj)
                    content += f"**Signature**: `{name}{sig}`\n\n"
                except:
                    pass
        
        return content

    def generate_api_docs(self, app_name, category, author):
        """Generate API documentation"""
        try:
            # Try to import serializers
            serializers_module = __import__(f'apps.{app_name}.serializers', fromlist=[''])
            
            # Get serializer classes
            serializers = []
            for name in dir(serializers_module):
                obj = getattr(serializers_module, name)
                if (inspect.isclass(obj) and 
                    name.endswith('Serializer') and 
                    not name.startswith('_')):
                    serializers.append((name, obj))

            if serializers:
                content = self.generate_api_content(serializers)
                
                Documentation.objects.update_or_create(
                    title=f'{app_name.title()} API',
                    category=category,
                    defaults={
                        'content': content,
                        'excerpt': f'API endpoints and serializers for the {app_name} application',
                        'author': author,
                        'status': 'published',
                        'visibility': 'internal'
                    }
                )
                
        except ImportError:
            pass

    def generate_api_content(self, serializers):
        """Generate markdown content for API"""
        content = f"# API Documentation\n\n"
        content += "This document describes the API endpoints and data structures.\n\n"
        
        content += "## Serializers\n\n"
        
        for name, serializer_class in serializers:
            content += f"### {name}\n\n"
            
            # Add docstring if available
            if serializer_class.__doc__:
                content += f"{serializer_class.__doc__}\n\n"
            
            # Add fields if available
            try:
                if hasattr(serializer_class, '_declared_fields'):
                    fields = serializer_class._declared_fields
                    if fields:
                        content += "#### Fields\n\n"
                        content += "| Field | Type | Required |\n"
                        content += "|-------|------|----------|\n"
                        
                        for field_name, field_obj in fields.items():
                            field_type = field_obj.__class__.__name__
                            required = not getattr(field_obj, 'allow_null', True)
                            content += f"| {field_name} | {field_type} | {required} |\n"
                        
                        content += "\n"
            except:
                pass
        
        return content

    def generate_general_docs(self, category, author):
        """Generate general documentation"""
        
        # Create overview documentation
        overview_content = """# System Overview

This documentation provides an overview of the system architecture and components.

## Architecture

The system follows a modular architecture with the following components:

- **Frontend**: React/Next.js application
- **Backend**: Django REST API
- **Database**: PostgreSQL with Redis caching
- **Authentication**: JWT-based authentication

## Key Features

- Comprehensive admin panel
- Role-based access control
- Real-time analytics
- Advanced search capabilities
- Multi-language support

## Getting Started

1. Set up the development environment
2. Install dependencies
3. Run database migrations
4. Start the development server

## API Endpoints

The API follows RESTful conventions and provides endpoints for:

- Authentication and user management
- Data management (CRUD operations)
- Analytics and reporting
- System configuration

## Security

The system implements multiple security measures:

- JWT token authentication
- Role-based permissions
- Input validation and sanitization
- HTTPS enforcement
- Rate limiting
"""

        Documentation.objects.update_or_create(
            title='System Overview',
            category=category,
            defaults={
                'content': overview_content,
                'excerpt': 'High-level overview of the system architecture and features',
                'author': author,
                'status': 'published',
                'visibility': 'internal'
            }
        )

        self.stdout.write(
            self.style.SUCCESS('Generated general documentation')
        )