"""
Authentication Test Data Factory

Provides test data generation for authentication and user management API tests.
Includes user accounts, test scenarios, and validation data.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random
import string

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.interfaces import UserRole, Environment
from core.models import TestUser, Address, PaymentMethod


class AuthTestDataFactory:
    """Factory for generating authentication test data"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.base_domain = self._get_base_domain()
    
    def _get_base_domain(self) -> str:
        """Get base domain for test environment"""
        domain_map = {
            Environment.DEVELOPMENT: 'localhost:8000',
            Environment.STAGING: 'staging-api.example.com',
            Environment.PRODUCTION: 'api.example.com'
        }
        return domain_map.get(self.environment, 'localhost:8000')
    
    def generate_test_users(self) -> Dict[str, TestUser]:
        """Generate comprehensive set of test users for all roles"""
        users = {}
        
        # Guest users (for registration testing)
        for i in range(5):
            user_id = f"guest_user_{i+1}"
            users[user_id] = TestUser(
                id=user_id,
                user_type=UserRole.GUEST,
                email=f"guest{i+1}@testdomain.com",
                password="guestpass123",
                first_name=f"Guest{i+1}",
                last_name="User",
                phone=f"+1555000{100+i}",
                is_active=False  # Guests typically need email verification
            )
        
        # Regular customers
        for i in range(10):
            user_id = f"customer_user_{i+1}"
            addresses = [
                Address(
                    street=f"{100+i*10} Test Street",
                    city="Test City",
                    state="TS",
                    postal_code=f"{10000+i}",
                    country="US",
                    address_type="shipping"
                ),
                Address(
                    street=f"{200+i*10} Billing Ave",
                    city="Billing City",
                    state="BC",
                    postal_code=f"{20000+i}",
                    country="US",
                    address_type="billing"
                )
            ]
            
            payment_methods = [
                PaymentMethod(
                    type="credit_card",
                    details={
                        "card_number": f"4111111111111{111+i}",
                        "expiry_month": "12",
                        "expiry_year": "2025",
                        "cvv": "123",
                        "cardholder_name": f"Customer {i+1}"
                    },
                    is_default=True
                )
            ]
            
            users[user_id] = TestUser(
                id=user_id,
                user_type=UserRole.CUSTOMER,
                email=f"customer{i+1}@testdomain.com",
                password="customerpass123",
                first_name=f"Customer{i+1}",
                last_name="User",
                phone=f"+1555001{100+i}",
                addresses=addresses,
                payment_methods=payment_methods,
                is_active=True,
                profile_data={
                    "preferences": {
                        "newsletter": True,
                        "sms_notifications": False,
                        "language": "en",
                        "currency": "USD"
                    },
                    "loyalty_points": random.randint(0, 1000)
                }
            )
        
        # Premium customers
        for i in range(5):
            user_id = f"premium_user_{i+1}"
            addresses = [
                Address(
                    street=f"{300+i*10} Premium Street",
                    city="Premium City",
                    state="PC",
                    postal_code=f"{30000+i}",
                    country="US",
                    address_type="shipping"
                )
            ]
            
            payment_methods = [
                PaymentMethod(
                    type="credit_card",
                    details={
                        "card_number": f"5555555555554{444+i}",
                        "expiry_month": "06",
                        "expiry_year": "2026",
                        "cvv": "456",
                        "cardholder_name": f"Premium {i+1}"
                    },
                    is_default=True
                ),
                PaymentMethod(
                    type="paypal",
                    details={
                        "email": f"premium{i+1}@paypal.com"
                    }
                )
            ]
            
            users[user_id] = TestUser(
                id=user_id,
                user_type=UserRole.PREMIUM_CUSTOMER,
                email=f"premium{i+1}@testdomain.com",
                password="premiumpass123",
                first_name=f"Premium{i+1}",
                last_name="Customer",
                phone=f"+1555002{100+i}",
                addresses=addresses,
                payment_methods=payment_methods,
                is_active=True,
                profile_data={
                    "membership_level": "gold",
                    "membership_since": "2023-01-01",
                    "loyalty_points": random.randint(1000, 5000),
                    "preferences": {
                        "newsletter": True,
                        "sms_notifications": True,
                        "language": "en",
                        "currency": "USD"
                    }
                }
            )
        
        # Sellers/Vendors
        for i in range(8):
            user_id = f"seller_user_{i+1}"
            addresses = [
                Address(
                    street=f"{400+i*10} Business Blvd",
                    city="Commerce City",
                    state="CC",
                    postal_code=f"{40000+i}",
                    country="US",
                    address_type="business"
                )
            ]
            
            users[user_id] = TestUser(
                id=user_id,
                user_type=UserRole.SELLER,
                email=f"seller{i+1}@testdomain.com",
                password="sellerpass123",
                first_name=f"Seller{i+1}",
                last_name="Business",
                phone=f"+1555003{100+i}",
                addresses=addresses,
                is_active=True,
                profile_data={
                    "business_name": f"Test Business {i+1}",
                    "business_type": "retail",
                    "tax_id": f"TAX{1000+i}",
                    "verification_status": "verified",
                    "commission_rate": 0.15,
                    "total_sales": random.randint(10000, 100000)
                }
            )
        
        # Admin users
        for i in range(3):
            user_id = f"admin_user_{i+1}"
            users[user_id] = TestUser(
                id=user_id,
                user_type=UserRole.ADMIN,
                email=f"admin{i+1}@testdomain.com",
                password="adminpass123",
                first_name=f"Admin{i+1}",
                last_name="User",
                phone=f"+1555004{100+i}",
                is_active=True,
                profile_data={
                    "department": "operations",
                    "access_level": "standard_admin",
                    "last_login": datetime.now().isoformat()
                }
            )
        
        # Super Admin users
        for i in range(2):
            user_id = f"super_admin_user_{i+1}"
            users[user_id] = TestUser(
                id=user_id,
                user_type=UserRole.SUPER_ADMIN,
                email=f"superadmin{i+1}@testdomain.com",
                password="superadminpass123",
                first_name=f"SuperAdmin{i+1}",
                last_name="User",
                phone=f"+1555005{100+i}",
                is_active=True,
                profile_data={
                    "department": "system_administration",
                    "access_level": "super_admin",
                    "security_clearance": "level_5",
                    "last_login": datetime.now().isoformat()
                }
            )
        
        return users
    
    def get_registration_test_data(self) -> List[Dict[str, Any]]:
        """Get test data for user registration scenarios"""
        return [
            # Valid registration data
            {
                "scenario": "valid_registration",
                "data": {
                    "email": "newuser@testdomain.com",
                    "password": "securepass123",
                    "password_confirm": "securepass123",
                    "first_name": "New",
                    "last_name": "User",
                    "phone": "+1555999001",
                    "terms_accepted": True
                },
                "expected_status": 201,
                "expected_fields": ["id", "email", "first_name", "last_name", "is_active"]
            },
            # Missing required fields
            {
                "scenario": "missing_email",
                "data": {
                    "password": "securepass123",
                    "password_confirm": "securepass123",
                    "first_name": "Test",
                    "last_name": "User"
                },
                "expected_status": 400,
                "expected_errors": ["email"]
            },
            # Invalid email format
            {
                "scenario": "invalid_email",
                "data": {
                    "email": "invalid-email",
                    "password": "securepass123",
                    "password_confirm": "securepass123",
                    "first_name": "Test",
                    "last_name": "User"
                },
                "expected_status": 400,
                "expected_errors": ["email"]
            },
            # Weak password
            {
                "scenario": "weak_password",
                "data": {
                    "email": "weakpass@testdomain.com",
                    "password": "123",
                    "password_confirm": "123",
                    "first_name": "Weak",
                    "last_name": "Password"
                },
                "expected_status": 400,
                "expected_errors": ["password"]
            },
            # Password mismatch
            {
                "scenario": "password_mismatch",
                "data": {
                    "email": "mismatch@testdomain.com",
                    "password": "password123",
                    "password_confirm": "different123",
                    "first_name": "Password",
                    "last_name": "Mismatch"
                },
                "expected_status": 400,
                "expected_errors": ["password_confirm"]
            },
            # Duplicate email
            {
                "scenario": "duplicate_email",
                "data": {
                    "email": "customer1@testdomain.com",  # Already exists
                    "password": "newpass123",
                    "password_confirm": "newpass123",
                    "first_name": "Duplicate",
                    "last_name": "Email"
                },
                "expected_status": 400,
                "expected_errors": ["email"]
            }
        ]
    
    def get_login_test_data(self) -> List[Dict[str, Any]]:
        """Get test data for user login scenarios"""
        return [
            # Valid login
            {
                "scenario": "valid_login",
                "data": {
                    "username": "customer1@testdomain.com",
                    "password": "customerpass123"
                },
                "expected_status": 200,
                "expected_fields": ["access", "refresh", "user"]
            },
            # Invalid email
            {
                "scenario": "invalid_email",
                "data": {
                    "username": "nonexistent@testdomain.com",
                    "password": "anypassword"
                },
                "expected_status": 401,
                "expected_errors": ["detail"]
            },
            # Invalid password
            {
                "scenario": "invalid_password",
                "data": {
                    "username": "customer1@testdomain.com",
                    "password": "wrongpassword"
                },
                "expected_status": 401,
                "expected_errors": ["detail"]
            },
            # Inactive account
            {
                "scenario": "inactive_account",
                "data": {
                    "username": "guest1@testdomain.com",  # Inactive account
                    "password": "guestpass123"
                },
                "expected_status": 401,
                "expected_errors": ["detail"]
            },
            # Empty credentials
            {
                "scenario": "empty_credentials",
                "data": {
                    "username": "",
                    "password": ""
                },
                "expected_status": 400,
                "expected_errors": ["username", "password"]
            }
        ]
    
    def get_role_permission_test_data(self) -> Dict[str, Dict[str, List[str]]]:
        """Get role-based permission test data"""
        return {
            "guest": {
                "allowed_endpoints": [
                    "/api/v1/auth/register/",
                    "/api/v1/auth/login/",
                    "/api/v1/products/",
                    "/api/v1/categories/"
                ],
                "forbidden_endpoints": [
                    "/api/v1/auth/profile/",
                    "/api/v1/users/",
                    "/api/v1/orders/",
                    "/api/v1/admin/",
                    "/api/v1/sellers/"
                ]
            },
            "customer": {
                "allowed_endpoints": [
                    "/api/v1/auth/profile/",
                    "/api/v1/products/",
                    "/api/v1/orders/",
                    "/api/v1/cart/",
                    "/api/v1/reviews/"
                ],
                "forbidden_endpoints": [
                    "/api/v1/users/",
                    "/api/v1/admin/",
                    "/api/v1/sellers/management/"
                ]
            },
            "premium_customer": {
                "allowed_endpoints": [
                    "/api/v1/auth/profile/",
                    "/api/v1/products/",
                    "/api/v1/orders/",
                    "/api/v1/cart/",
                    "/api/v1/reviews/",
                    "/api/v1/premium/"
                ],
                "forbidden_endpoints": [
                    "/api/v1/users/",
                    "/api/v1/admin/",
                    "/api/v1/sellers/management/"
                ]
            },
            "seller": {
                "allowed_endpoints": [
                    "/api/v1/auth/profile/",
                    "/api/v1/products/",
                    "/api/v1/orders/",
                    "/api/v1/sellers/",
                    "/api/v1/analytics/seller/"
                ],
                "forbidden_endpoints": [
                    "/api/v1/users/",
                    "/api/v1/admin/",
                    "/api/v1/analytics/admin/"
                ]
            },
            "admin": {
                "allowed_endpoints": [
                    "/api/v1/auth/profile/",
                    "/api/v1/users/",
                    "/api/v1/products/",
                    "/api/v1/orders/",
                    "/api/v1/admin/",
                    "/api/v1/analytics/",
                    "/api/v1/sellers/"
                ],
                "forbidden_endpoints": [
                    "/api/v1/system/critical/"
                ]
            },
            "super_admin": {
                "allowed_endpoints": [
                    "/api/v1/auth/profile/",
                    "/api/v1/users/",
                    "/api/v1/products/",
                    "/api/v1/orders/",
                    "/api/v1/admin/",
                    "/api/v1/analytics/",
                    "/api/v1/sellers/",
                    "/api/v1/system/"
                ],
                "forbidden_endpoints": []
            }
        }
    
    def get_security_test_data(self) -> List[Dict[str, Any]]:
        """Get security validation test data"""
        return [
            # SQL Injection attempts
            {
                "scenario": "sql_injection_login",
                "endpoint": "/api/v1/auth/login/",
                "data": {
                    "username": "'; DROP TABLE users; --",
                    "password": "password"
                },
                "expected_status": 400,
                "description": "SQL injection attempt in username field"
            },
            # XSS attempts
            {
                "scenario": "xss_profile_update",
                "endpoint": "/api/v1/auth/profile/",
                "data": {
                    "first_name": "<script>alert('xss')</script>",
                    "last_name": "User"
                },
                "expected_status": 400,
                "description": "XSS attempt in profile fields"
            },
            # CSRF attempts
            {
                "scenario": "csrf_missing_token",
                "endpoint": "/api/v1/auth/profile/",
                "data": {
                    "first_name": "Updated"
                },
                "headers": {},  # Missing CSRF token
                "expected_status": 403,
                "description": "CSRF protection validation"
            },
            # Rate limiting tests
            {
                "scenario": "brute_force_login",
                "endpoint": "/api/v1/auth/login/",
                "data": {
                    "username": "customer1@testdomain.com",
                    "password": "wrongpassword"
                },
                "repeat_count": 10,
                "expected_status": 429,
                "description": "Brute force login attempt"
            }
        ]
    
    def get_password_test_data(self) -> List[Dict[str, Any]]:
        """Get password management test data"""
        return [
            # Valid password change
            {
                "scenario": "valid_password_change",
                "data": {
                    "old_password": "customerpass123",
                    "new_password": "newpassword123",
                    "new_password_confirm": "newpassword123"
                },
                "expected_status": 200
            },
            # Wrong old password
            {
                "scenario": "wrong_old_password",
                "data": {
                    "old_password": "wrongpassword",
                    "new_password": "newpassword123",
                    "new_password_confirm": "newpassword123"
                },
                "expected_status": 400,
                "expected_errors": ["old_password"]
            },
            # Weak new password
            {
                "scenario": "weak_new_password",
                "data": {
                    "old_password": "customerpass123",
                    "new_password": "123",
                    "new_password_confirm": "123"
                },
                "expected_status": 400,
                "expected_errors": ["new_password"]
            },
            # Password confirmation mismatch
            {
                "scenario": "password_mismatch",
                "data": {
                    "old_password": "customerpass123",
                    "new_password": "newpassword123",
                    "new_password_confirm": "differentpassword123"
                },
                "expected_status": 400,
                "expected_errors": ["new_password_confirm"]
            }
        ]
    
    def generate_random_user_data(self) -> Dict[str, Any]:
        """Generate random user data for testing"""
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        return {
            "email": f"random_{random_id}@testdomain.com",
            "password": "randompass123",
            "password_confirm": "randompass123",
            "first_name": f"Random{random_id[:4].title()}",
            "last_name": "User",
            "phone": f"+1555{random.randint(1000000, 9999999)}"
        }
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Get all API endpoints for testing"""
        base_url = f"http://{self.base_domain}"
        
        return {
            # Authentication endpoints
            "register": f"{base_url}/api/v1/auth/register/",
            "login": f"{base_url}/api/v1/auth/login/",
            "logout": f"{base_url}/api/v1/auth/logout/",
            "refresh": f"{base_url}/api/v1/auth/refresh/",
            "profile": f"{base_url}/api/v1/auth/profile/",
            "change_password": f"{base_url}/api/v1/auth/change-password/",
            "reset_password": f"{base_url}/api/v1/auth/reset-password/",
            "verify_email": f"{base_url}/api/v1/auth/verify-email/",
            
            # User management endpoints
            "users": f"{base_url}/api/v1/users/",
            "user_detail": f"{base_url}/api/v1/users/{{id}}/",
            
            # Other endpoints for permission testing
            "products": f"{base_url}/api/v1/products/",
            "orders": f"{base_url}/api/v1/orders/",
            "cart": f"{base_url}/api/v1/cart/",
            "admin": f"{base_url}/api/v1/admin/",
            "sellers": f"{base_url}/api/v1/sellers/",
            "analytics": f"{base_url}/api/v1/analytics/"
        }


# Convenience functions for easy access
def get_test_users(environment: Environment = Environment.DEVELOPMENT) -> Dict[str, TestUser]:
    """Get all test users for the specified environment"""
    factory = AuthTestDataFactory(environment)
    return factory.generate_test_users()


def get_user_by_role(role: UserRole, environment: Environment = Environment.DEVELOPMENT) -> Optional[TestUser]:
    """Get first test user with specified role"""
    users = get_test_users(environment)
    for user in users.values():
        if user.user_type == role:
            return user
    return None


def get_users_by_role(role: UserRole, environment: Environment = Environment.DEVELOPMENT) -> List[TestUser]:
    """Get all test users with specified role"""
    users = get_test_users(environment)
    return [user for user in users.values() if user.user_type == role]


if __name__ == '__main__':
    # Example usage
    factory = AuthTestDataFactory()
    users = factory.generate_test_users()
    
    print(f"Generated {len(users)} test users:")
    for user_id, user in users.items():
        print(f"  {user_id}: {user.email} ({user.user_type.value})")