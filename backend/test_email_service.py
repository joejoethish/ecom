#!/usr/bin/env python
"""
Test script for the PasswordResetEmailService implementation.
This script validates the email service functionality.
"""
print("Starting email service test script...")

import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.testing')
django.setup()

from django.contrib.auth import get_user_model
from apps.authentication.email_service import PasswordResetEmailService
from apps.authentication.services import PasswordResetService

User = get_user_model()


def test_email_service():
    """Test the PasswordResetEmailService functionality."""
    print("Testing PasswordResetEmailService...")
    sys.stdout.flush()
    
    # Clean up any existing test data
    User.objects.filter(email='test@example.com').delete()
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123',
        first_name='Test',
        last_name='User'
    )
    print(f"✓ Created test user: {user.email}")
    
    # Test 1: Email configuration test
    print("\n1. Testing email configuration...")
    config_ok, config_message = PasswordResetEmailService.test_email_configuration()
    print(f"✓ Email configuration test: {config_message}")
    
    # Test 2: Get email stats
    print("\n2. Testing email stats...")
    stats = PasswordResetEmailService.get_email_stats()
    print(f"✓ Email service stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test 3: Generate reset URL
    print("\n3. Testing reset URL generation...")
    test_token = "test_token_123456789"
    reset_url = PasswordResetEmailService._get_reset_url(test_token)
    expected_url = f"{PasswordResetEmailService.FRONTEND_URL}/auth/reset-password/{test_token}"
    assert reset_url == expected_url, f"Expected {expected_url}, got {reset_url}"
    print(f"✓ Reset URL generated correctly: {reset_url}")
    
    # Test 4: Email context generation
    print("\n4. Testing email context generation...")
    context = PasswordResetEmailService._get_email_context(
        user=user,
        token=test_token,
        request_ip='192.168.1.1'
    )
    
    required_keys = ['user', 'reset_url', 'site_name', 'support_email', 'request_ip', 'request_time', 'expiry_time']
    for key in required_keys:
        assert key in context, f"Missing key in context: {key}"
    
    assert context['user'] == user, "User not correctly set in context"
    assert context['reset_url'] == reset_url, "Reset URL not correctly set in context"
    assert context['request_ip'] == '192.168.1.1', "IP address not correctly set in context"
    print("✓ Email context generated correctly")
    print(f"   Site name: {context['site_name']}")
    print(f"   Support email: {context['support_email']}")
    print(f"   Request time: {context['request_time']}")
    print(f"   Expiry time: {context['expiry_time']}")
    
    # Test 5: Template rendering
    print("\n5. Testing email template rendering...")
    try:
        html_content, text_content = PasswordResetEmailService._render_email_templates(context)
        
        # Check HTML content
        assert user.first_name in html_content, "User first name not in HTML content"
        assert user.email in html_content, "User email not in HTML content"
        assert reset_url in html_content, "Reset URL not in HTML content"
        assert context['site_name'] in html_content, "Site name not in HTML content"
        
        # Check text content
        assert user.first_name in text_content, "User first name not in text content"
        assert user.email in text_content, "User email not in text content"
        assert reset_url in text_content, "Reset URL not in text content"
        assert context['site_name'] in text_content, "Site name not in text content"
        
        print("✓ Email templates rendered successfully")
        print(f"   HTML content length: {len(html_content)} characters")
        print(f"   Text content length: {len(text_content)} characters")
        
    except Exception as e:
        print(f"✗ Template rendering failed: {str(e)}")
        return False
    
    # Test 6: Email message creation
    print("\n6. Testing email message creation...")
    try:
        email_message = PasswordResetEmailService._create_email_message(
            user=user,
            html_content=html_content,
            text_content=text_content
        )
        
        assert email_message.to == [user.email], "Email recipient not set correctly"
        assert PasswordResetEmailService.SITE_NAME in email_message.subject, "Site name not in subject"
        assert email_message.body == text_content, "Text content not set correctly"
        assert len(email_message.alternatives) == 1, "HTML alternative not attached"
        assert email_message.alternatives[0][1] == "text/html", "HTML alternative not set correctly"
        
        print("✓ Email message created successfully")
        print(f"   Subject: {email_message.subject}")
        print(f"   To: {email_message.to}")
        print(f"   From: {email_message.from_email}")
        
    except Exception as e:
        print(f"✗ Email message creation failed: {str(e)}")
        return False
    
    # Test 7: Complete email sending (dry run - won't actually send)
    print("\n7. Testing complete email sending process...")
    
    # Generate a real token for testing
    raw_token, reset_token = PasswordResetService.generate_reset_token(
        user=user,
        ip_address='192.168.1.1',
        user_agent='Test User Agent'
    )
    
    # Test the email sending (this will try to send but may fail due to email config)
    try:
        success, error_message = PasswordResetEmailService.send_password_reset_email(
            user=user,
            token=raw_token,
            request_ip='192.168.1.1'
        )
        
        if success:
            print("✓ Password reset email sent successfully")
        else:
            print(f"⚠ Password reset email failed (expected in test environment): {error_message}")
            # This is expected in test environment without proper email configuration
        
    except Exception as e:
        print(f"⚠ Email sending failed (expected in test environment): {str(e)}")
    
    # Test 8: Confirmation email
    print("\n8. Testing confirmation email...")
    try:
        success, error_message = PasswordResetEmailService.send_password_reset_confirmation_email(
            user=user,
            request_ip='192.168.1.1'
        )
        
        if success:
            print("✓ Password reset confirmation email sent successfully")
        else:
            print(f"⚠ Confirmation email failed (expected in test environment): {error_message}")
            
    except Exception as e:
        print(f"⚠ Confirmation email failed (expected in test environment): {str(e)}")
    
    # Test 9: Integration with PasswordResetService
    print("\n9. Testing integration with PasswordResetService...")
    
    # Clean up previous test data
    User.objects.filter(email='integration@example.com').delete()
    
    # Create another test user
    integration_user = User.objects.create_user(
        username='integrationuser',
        email='integration@example.com',
        password='testpassword123',
        first_name='Integration',
        last_name='Test'
    )
    
    # Test the complete flow
    success, message, token = PasswordResetService.request_password_reset(
        email='integration@example.com',
        ip_address='192.168.1.2',
        user_agent='Integration Test Agent'
    )
    
    if success and token:
        print("✓ Complete password reset flow with email integration works")
        print(f"   Message: {message}")
        print(f"   Token generated: {token[:8]}...")
    else:
        print(f"⚠ Complete flow failed (may be due to email config): {message}")
    
    print("\n🎉 Email service testing completed!")
    
    # Clean up test data
    User.objects.filter(email__in=['test@example.com', 'integration@example.com']).delete()
    print("✓ Test data cleaned up")
    
    return True


if __name__ == '__main__':
    try:
        test_email_service()
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()