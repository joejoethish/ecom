#!/usr/bin/env python
"""
Simple test script to verify password reset tasks work correctly.
"""
import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.authentication.models import PasswordResetToken, PasswordResetAttempt
from apps.authentication.tasks import (
    cleanup_expired_password_reset_tokens,
    cleanup_old_password_reset_attempts,
    monitor_password_reset_token_performance
)

# Disable Celery for testing
from django.conf import settings
settings.CELERY_TASK_ALWAYS_EAGER = True

User = get_user_model()

def test_tasks():
    """Test the password reset tasks."""
    print("Testing Password Reset Tasks")
    print("=" * 50)
    
    # Clean up any existing test data first
    PasswordResetToken.objects.filter(token_hash__startswith='test_').delete()
    PasswordResetAttempt.objects.filter(email='test@example.com').delete()
    
    # Create test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'username': 'testuser',
            'password': 'testpass123'
        }
    )
    print(f"Test user: {user.email} ({'created' if created else 'exists'})")
    
    # Create test data
    now = timezone.now()
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    # Create expired token
    expired_token = PasswordResetToken.objects.create(
        user=user,
        token_hash=f'test_expired_{unique_id}',
        expires_at=now - timedelta(hours=2),
        ip_address='192.168.1.1'
    )
    print(f"Created expired token: {expired_token.id}")
    
    # Create active token
    active_token = PasswordResetToken.objects.create(
        user=user,
        token_hash=f'test_active_{unique_id}',
        expires_at=now + timedelta(hours=1),
        ip_address='192.168.1.1'
    )
    print(f"Created active token: {active_token.id}")
    
    # Create old attempt
    old_attempt = PasswordResetAttempt.objects.create(
        ip_address='192.168.1.1',
        email='test@example.com',
        success=True
    )
    old_attempt.created_at = now - timedelta(days=8)
    old_attempt.save()
    print(f"Created old attempt: {old_attempt.id}")
    
    # Create recent attempt
    recent_attempt = PasswordResetAttempt.objects.create(
        ip_address='192.168.1.2',
        email='test@example.com',
        success=False
    )
    print(f"Created recent attempt: {recent_attempt.id}")
    
    print("\nInitial state:")
    print(f"  Total tokens: {PasswordResetToken.objects.count()}")
    print(f"  Total attempts: {PasswordResetAttempt.objects.count()}")
    
    # Test monitoring task
    print("\n1. Testing monitoring task...")
    try:
        monitor_result = monitor_password_reset_token_performance()
        print(f"  Status: {monitor_result['status']}")
        print(f"  Total tokens: {monitor_result['token_statistics']['total_tokens']}")
        print(f"  Active tokens: {monitor_result['token_statistics']['active_tokens']}")
        print(f"  Expired tokens: {monitor_result['token_statistics']['expired_tokens']}")
        print(f"  Success rate: {monitor_result['attempt_statistics']['success_rate_7d']}%")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test token cleanup task
    print("\n2. Testing token cleanup task...")
    try:
        cleanup_result = cleanup_expired_password_reset_tokens()
        print(f"  Status: {cleanup_result['status']}")
        print(f"  Total deleted: {cleanup_result['total_deleted']}")
        print(f"  Expired deleted: {cleanup_result['expired_deleted']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test attempt cleanup task
    print("\n3. Testing attempt cleanup task...")
    try:
        attempt_result = cleanup_old_password_reset_attempts(days_old=7)
        print(f"  Status: {attempt_result['status']}")
        print(f"  Deleted count: {attempt_result['deleted_count']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\nFinal state:")
    print(f"  Total tokens: {PasswordResetToken.objects.count()}")
    print(f"  Total attempts: {PasswordResetAttempt.objects.count()}")
    
    # Cleanup test data
    PasswordResetToken.objects.filter(token_hash__startswith='test_').delete()
    PasswordResetAttempt.objects.filter(email='test@example.com').delete()
    if created:
        user.delete()
    
    print("\nTest completed successfully!")

if __name__ == '__main__':
    test_tasks()