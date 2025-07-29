#!/usr/bin/env python
"""
System Integration Validation Script

This script validates that all components of the e-commerce platform are properly
integrated and working together. It checks database connections, Redis, Elasticsearch,
Celery, and other critical services.
"""

import os
import sys
import django
import time
import json
import socket
import requests
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.db import connections
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from elasticsearch import Elasticsearch
from redis import Redis
import celery.app.control

User = get_user_model()


class SystemValidator:
    """Validates system integration and component health"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'overall_status': 'UNKNOWN'
        }
    
    def validate_database(self):
        """Validate database connection"""
        print("Validating database connection...")
        try:
            # Check if database is accessible
            connections['default'].cursor()
            
            # Try a simple query
            user_count = User.objects.count()
            
            self.results['components']['database'] = {
                'status': 'OK',
                'message': f'Database connection successful. User count: {user_count}'
            }
            print("✓ Database connection successful")
            return True
        except Exception as e:
            self.results['components']['database'] = {
                'status': 'ERROR',
                'message': f'Database connection failed: {str(e)}'
            }
            print(f"✗ Database connection failed: {str(e)}")
            return False
    
    def validate_redis(self):
        """Validate Redis connection"""
        print("Validating Redis connection...")
        try:
            # Get Redis configuration
            redis_host = settings.REDIS_HOST
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_db = getattr(settings, 'REDIS_DB', 0)
            redis_password = getattr(settings, 'REDIS_PASSWORD', None)
            
            # Connect to Redis
            redis_client = Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                socket_timeout=5
            )
            
            # Test Redis connection
            redis_client.ping()
            
            # Test Django cache (which should use Redis)
            cache_key = 'system_validator_test'
            cache_value = 'test_value'
            cache.set(cache_key, cache_value, 60)
            retrieved_value = cache.get(cache_key)
            
            if retrieved_value != cache_value:
                raise Exception("Cache value mismatch")
            
            self.results['components']['redis'] = {
                'status': 'OK',
                'message': 'Redis connection successful'
            }
            print("✓ Redis connection successful")
            return True
        except Exception as e:
            self.results['components']['redis'] = {
                'status': 'ERROR',
                'message': f'Redis connection failed: {str(e)}'
            }
            print(f"✗ Redis connection failed: {str(e)}")
            return False
    
    def validate_elasticsearch(self):
        """Validate Elasticsearch connection"""
        print("Validating Elasticsearch connection...")
        try:
            # Get Elasticsearch configuration
            es_hosts = getattr(settings, 'ELASTICSEARCH_HOSTS', ['http://localhost:9200'])
            es_username = getattr(settings, 'ELASTICSEARCH_USERNAME', None)
            es_password = getattr(settings, 'ELASTICSEARCH_PASSWORD', None)
            
            # Connect to Elasticsearch
            es_client = Elasticsearch(
                es_hosts,
                basic_auth=(es_username, es_password) if es_username and es_password else None,
                verify_certs=False
            )
            
            # Check if Elasticsearch is running
            es_info = es_client.info()
            
            self.results['components']['elasticsearch'] = {
                'status': 'OK',
                'message': f'Elasticsearch connection successful. Version: {es_info["version"]["number"]}'
            }
            print(f"✓ Elasticsearch connection successful. Version: {es_info['version']['number']}")
            return True
        except Exception as e:
            self.results['components']['elasticsearch'] = {
                'status': 'ERROR',
                'message': f'Elasticsearch connection failed: {str(e)}'
            }
            print(f"✗ Elasticsearch connection failed: {str(e)}")
            return False
    
    def validate_celery(self):
        """Validate Celery connection"""
        print("Validating Celery connection...")
        try:
            # Import Celery app
            from ecommerce_project.celery import app
            
            # Check if Celery workers are running
            inspector = app.control.inspect()
            active_workers = inspector.active()
            
            if not active_workers:
                raise Exception("No active Celery workers found")
            
            self.results['components']['celery'] = {
                'status': 'OK',
                'message': f'Celery connection successful. Active workers: {list(active_workers.keys())}'
            }
            print(f"✓ Celery connection successful. Active workers: {list(active_workers.keys())}")
            return True
        except Exception as e:
            self.results['components']['celery'] = {
                'status': 'ERROR',
                'message': f'Celery connection failed: {str(e)}'
            }
            print(f"✗ Celery connection failed: {str(e)}")
            return False
    
    def validate_api(self):
        """Validate API endpoints"""
        print("Validating API endpoints...")
        try:
            # Get API base URL
            api_base_url = 'http://localhost:8000/api/v1'
            
            # Test endpoints
            endpoints = [
                '/products/',
                '/categories/',
                '/health/'
            ]
            
            results = {}
            all_successful = True
            
            for endpoint in endpoints:
                try:
                    url = f"{api_base_url}{endpoint}"
                    response = requests.get(url, timeout=5)
                    response.raise_for_status()
                    results[endpoint] = {
                        'status': response.status_code,
                        'success': True
                    }
                except Exception as e:
                    results[endpoint] = {
                        'status': getattr(response, 'status_code', None),
                        'success': False,
                        'error': str(e)
                    }
                    all_successful = False
            
            status = 'OK' if all_successful else 'WARNING'
            
            self.results['components']['api'] = {
                'status': status,
                'message': 'API endpoints validation completed',
                'details': results
            }
            
            if all_successful:
                print("✓ API endpoints validation successful")
            else:
                print("⚠ Some API endpoints failed validation")
            
            return all_successful
        except Exception as e:
            self.results['components']['api'] = {
                'status': 'ERROR',
                'message': f'API validation failed: {str(e)}'
            }
            print(f"✗ API validation failed: {str(e)}")
            return False
    
    def validate_websockets(self):
        """Validate WebSocket connections"""
        print("Validating WebSocket connections...")
        try:
            # Check if Channels is properly configured
            if not hasattr(settings, 'CHANNEL_LAYERS'):
                raise Exception("CHANNEL_LAYERS not configured in settings")
            
            # Check if Redis channel layer is configured
            channel_layers = settings.CHANNEL_LAYERS
            if channel_layers['default']['BACKEND'] != 'channels_redis.core.RedisChannelLayer':
                raise Exception("Redis channel layer not configured")
            
            # We can't easily test WebSocket connections here, so we just check configuration
            self.results['components']['websockets'] = {
                'status': 'OK',
                'message': 'WebSocket configuration validated'
            }
            print("✓ WebSocket configuration validated")
            return True
        except Exception as e:
            self.results['components']['websockets'] = {
                'status': 'ERROR',
                'message': f'WebSocket validation failed: {str(e)}'
            }
            print(f"✗ WebSocket validation failed: {str(e)}")
            return False
    
    def validate_all(self):
        """Validate all components"""
        print("\n=== Starting System Validation ===\n")
        
        # Validate all components
        db_status = self.validate_database()
        redis_status = self.validate_redis()
        es_status = self.validate_elasticsearch()
        celery_status = self.validate_celery()
        api_status = self.validate_api()
        ws_status = self.validate_websockets()
        
        # Determine overall status
        if all([db_status, redis_status, es_status, celery_status, api_status, ws_status]):
            self.results['overall_status'] = 'OK'
        elif any([not db_status, not redis_status, not celery_status]):
            self.results['overall_status'] = 'ERROR'
        else:
            self.results['overall_status'] = 'WARNING'
        
        print("\n=== System Validation Complete ===\n")
        print(f"Overall Status: {self.results['overall_status']}")
        
        # Save results to file
        with open('system_validation_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Results saved to system_validation_results.json")
        
        return self.results['overall_status'] == 'OK'


if __name__ == '__main__':
    validator = SystemValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)