# Global pytest configuration and fixtures
import pytest
import os
import django
from django.conf import settings
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import Mock, patch
import factory
from faker import Faker

# Configure Django settings for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.test')
django.setup()

fake = Faker()

@pytest.fixture(scope='session')
def django_db_setup():
    """Configure test database"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        }
    }

@pytest.fixture
def api_client():
    """Provide API client for testing"""
    return APIClient()

@pytest.fixture
def admin_user():
    """Create admin user for testing"""
    User = get_user_model()
    return User.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True
    )

@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Provide authenticated API client"""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client

@pytest.fixture
def mock_redis():
    """Mock Redis for testing"""
    with patch('django_redis.get_redis_connection') as mock:
        mock_connection = Mock()
        mock.return_value = mock_connection
        yield mock_connection

@pytest.fixture
def mock_celery():
    """Mock Celery for testing"""
    with patch('celery.current_app.send_task') as mock:
        yield mock

@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        'name': fake.word(),
        'description': fake.text(),
        'price': fake.pydecimal(left_digits=3, right_digits=2, positive=True),
        'sku': fake.uuid4(),
        'stock_quantity': fake.random_int(min=0, max=100)
    }

@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        'order_number': fake.uuid4(),
        'total_amount': fake.pydecimal(left_digits=4, right_digits=2, positive=True),
        'status': 'pending',
        'payment_status': 'pending'
    }

# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time
    start_time = time.time()
    yield
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.4f} seconds")

# Database fixtures
@pytest.fixture
def db_with_sample_data(db):
    """Database with sample data for testing"""
    # Create sample data here
    pass

# Security testing fixtures
@pytest.fixture
def security_headers():
    """Expected security headers"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'"
    }

# Test data factories
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True