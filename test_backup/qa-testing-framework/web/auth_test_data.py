"""
Authentication Test Data Generator

Provides test data generation utilities specifically for authentication
and user management testing scenarios.
"""

import random
import string
from typing import Dict, List, Any
from datetime import datetime, timedelta

from ..core.interfaces import UserRole, Environment
from ..core.models import TestUser, Address, PaymentMethod


class AuthTestDataGenerator:
    """Generates test data for authentication tests"""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.domain_suffix = self._get_domain_suffix()
        
        # Test data pools
        self.first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
            "William", "Jennifer", "James", "Mary", "Christopher", "Patricia", "Daniel",
            "Linda", "Matthew", "Elizabeth", "Anthony", "Barbara", "Mark", "Susan"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson"
        ]
        
        self.street_names = [
            "Main St", "Oak Ave", "Pine Rd", "Maple Dr", "Cedar Ln", "Elm St", "Park Ave",
            "First St", "Second St", "Third St", "Washington St", "Lincoln Ave", "Jefferson Rd"
        ]
        
        self.cities = [
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
            "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville"
        ]
        
        self.states = [
            "NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "NC", "GA", "MI", "NJ"
        ]
    
    def _get_domain_suffix(self) -> str:
        """Get email domain suffix based on environment"""
        domain_map = {
            Environment.DEVELOPMENT: "testdev.com",
            Environment.STAGING: "teststaging.com",
            Environment.PRODUCTION: "testprod.com"
        }
        return domain_map.get(self.environment, "testdomain.com")
    
    def generate_random_string(self, length: int = 8, include_numbers: bool = True) -> str:
        """Generate random string"""
        chars = string.ascii_lowercase
        if include_numbers:
            chars += string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def generate_email(self, prefix: str = None) -> str:
        """Generate test email address"""
        if prefix is None:
            prefix = f"testuser_{self.generate_random_string(6)}"
        
        timestamp = int(datetime.now().timestamp())
        return f"{prefix}_{timestamp}@{self.domain_suffix}"
    
    def generate_password(self, strength: str = "strong") -> str:
        """Generate password based on strength requirement"""
        if strength == "weak":
            return "123"
        elif strength == "medium":
            return "password123"
        elif strength == "strong":
            # Strong password with uppercase, lowercase, numbers, and special chars
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choice(chars) for _ in range(12))
            # Ensure it has required character types
            password = "Test123!" + password[:4]
            return password
        else:
            return "defaultpass123"
    
    def generate_phone_number(self) -> str:
        """Generate valid phone number"""
        area_code = random.randint(200, 999)
        exchange = random.randint(200, 999)
        number = random.randint(1000, 9999)
        return f"+1{area_code}{exchange}{number}"
    
    def generate_address(self) -> Address:
        """Generate test address"""
        return Address(
            street=f"{random.randint(100, 9999)} {random.choice(self.street_names)}",
            city=random.choice(self.cities),
            state=random.choice(self.states),
            postal_code=f"{random.randint(10000, 99999)}",
            country="US",
            address_type=random.choice(["shipping", "billing"])
        )
    
    def generate_payment_method(self, method_type: str = "credit_card") -> PaymentMethod:
        """Generate test payment method"""
        if method_type == "credit_card":
            return PaymentMethod(
                type="credit_card",
                details={
                    "card_number": "4111111111111111",  # Test Visa number
                    "expiry_month": random.randint(1, 12),
                    "expiry_year": random.randint(2024, 2030),
                    "cvv": f"{random.randint(100, 999)}",
                    "cardholder_name": f"{random.choice(self.first_names)} {random.choice(self.last_names)}"
                }
            )
        elif method_type == "paypal":
            return PaymentMethod(
                type="paypal",
                details={
                    "email": self.generate_email("paypal_user")
                }
            )
        elif method_type == "upi":
            return PaymentMethod(
                type="upi",
                details={
                    "upi_id": f"testuser{random.randint(1000, 9999)}@paytm"
                }
            )
        else:
            return PaymentMethod(type="cod")
    
    def create_basic_user_data(self, user_role: UserRole = UserRole.REGISTERED) -> Dict[str, Any]:
        """Create basic user data for registration"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": self.generate_email(f"{first_name.lower()}.{last_name.lower()}"),
            "password": self.generate_password("strong"),
            "phone": self.generate_phone_number(),
            "user_role": user_role
        }
    
    def create_complete_user_data(self, user_role: UserRole = UserRole.REGISTERED) -> Dict[str, Any]:
        """Create complete user data with addresses and payment methods"""
        basic_data = self.create_basic_user_data(user_role)
        
        # Add addresses
        addresses = [self.generate_address() for _ in range(random.randint(1, 3))]
        
        # Add payment methods
        payment_methods = []
        if user_role in [UserRole.REGISTERED, UserRole.PREMIUM]:
            payment_methods.append(self.generate_payment_method("credit_card"))
            if random.choice([True, False]):
                payment_methods.append(self.generate_payment_method("paypal"))
        
        basic_data.update({
            "addresses": addresses,
            "payment_methods": payment_methods,
            "profile_data": {
                "date_of_birth": (datetime.now() - timedelta(days=random.randint(6570, 25550))).strftime("%Y-%m-%d"),
                "gender": random.choice(["male", "female", "other"]),
                "newsletter_subscription": random.choice([True, False]),
                "marketing_emails": random.choice([True, False])
            }
        })
        
        return basic_data
    
    def create_test_user_model(self, user_role: UserRole = UserRole.REGISTERED) -> TestUser:
        """Create TestUser model instance"""
        user_data = self.create_complete_user_data(user_role)
        
        return TestUser(
            id=f"USER_{self.generate_random_string(8).upper()}",
            user_type=user_role,
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            phone=user_data["phone"],
            profile_data=user_data["profile_data"],
            addresses=user_data["addresses"],
            payment_methods=user_data["payment_methods"]
        )
    
    def create_invalid_user_data_scenarios(self) -> List[Dict[str, Any]]:
        """Create various invalid user data scenarios for negative testing"""
        base_data = self.create_basic_user_data()
        
        scenarios = [
            # Empty email
            {**base_data, "email": "", "scenario": "empty_email"},
            
            # Invalid email formats
            {**base_data, "email": "invalid-email", "scenario": "invalid_email_format"},
            {**base_data, "email": "@domain.com", "scenario": "missing_username"},
            {**base_data, "email": "user@", "scenario": "missing_domain"},
            {**base_data, "email": "user@domain", "scenario": "missing_tld"},
            
            # Weak passwords
            {**base_data, "password": "", "scenario": "empty_password"},
            {**base_data, "password": "123", "scenario": "too_short_password"},
            {**base_data, "password": "password", "scenario": "weak_password"},
            {**base_data, "password": "12345678", "scenario": "numeric_only_password"},
            
            # Missing required fields
            {**base_data, "first_name": "", "scenario": "empty_first_name"},
            {**base_data, "last_name": "", "scenario": "empty_last_name"},
            
            # Invalid phone numbers
            {**base_data, "phone": "123", "scenario": "too_short_phone"},
            {**base_data, "phone": "invalid-phone", "scenario": "invalid_phone_format"},
            {**base_data, "phone": "1234567890123456789", "scenario": "too_long_phone"},
            
            # Special characters in names
            {**base_data, "first_name": "John<script>", "scenario": "xss_in_first_name"},
            {**base_data, "last_name": "'; DROP TABLE users; --", "scenario": "sql_injection_in_last_name"},
        ]
        
        return scenarios
    
    def create_login_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create login test scenarios"""
        valid_user = self.create_basic_user_data()
        
        scenarios = [
            # Valid login
            {
                "email": valid_user["email"],
                "password": valid_user["password"],
                "remember_me": False,
                "scenario": "valid_login",
                "expected_result": "success"
            },
            
            # Valid login with remember me
            {
                "email": valid_user["email"],
                "password": valid_user["password"],
                "remember_me": True,
                "scenario": "valid_login_remember_me",
                "expected_result": "success"
            },
            
            # Invalid email
            {
                "email": "nonexistent@email.com",
                "password": "password123",
                "remember_me": False,
                "scenario": "invalid_email",
                "expected_result": "failure"
            },
            
            # Invalid password
            {
                "email": valid_user["email"],
                "password": "wrongpassword",
                "remember_me": False,
                "scenario": "invalid_password",
                "expected_result": "failure"
            },
            
            # Empty credentials
            {
                "email": "",
                "password": "",
                "remember_me": False,
                "scenario": "empty_credentials",
                "expected_result": "failure"
            },
            
            # SQL injection attempts
            {
                "email": "admin'; DROP TABLE users; --",
                "password": "password",
                "remember_me": False,
                "scenario": "sql_injection_email",
                "expected_result": "failure"
            },
            
            {
                "email": "admin@test.com",
                "password": "' OR '1'='1",
                "remember_me": False,
                "scenario": "sql_injection_password",
                "expected_result": "failure"
            },
            
            # XSS attempts
            {
                "email": "<script>alert('xss')</script>@test.com",
                "password": "password",
                "remember_me": False,
                "scenario": "xss_email",
                "expected_result": "failure"
            }
        ]
        
        return scenarios
    
    def create_password_reset_scenarios(self) -> List[Dict[str, Any]]:
        """Create password reset test scenarios"""
        valid_user = self.create_basic_user_data()
        
        scenarios = [
            # Valid email
            {
                "email": valid_user["email"],
                "scenario": "valid_email",
                "expected_result": "success"
            },
            
            # Non-existent email
            {
                "email": "nonexistent@email.com",
                "scenario": "nonexistent_email",
                "expected_result": "handled_gracefully"
            },
            
            # Invalid email format
            {
                "email": "invalid-email",
                "scenario": "invalid_email_format",
                "expected_result": "validation_error"
            },
            
            # Empty email
            {
                "email": "",
                "scenario": "empty_email",
                "expected_result": "validation_error"
            },
            
            # SQL injection attempt
            {
                "email": "admin'; DROP TABLE users; --",
                "scenario": "sql_injection",
                "expected_result": "handled_gracefully"
            }
        ]
        
        return scenarios
    
    def create_profile_update_scenarios(self) -> List[Dict[str, Any]]:
        """Create profile update test scenarios"""
        scenarios = [
            # Valid updates
            {
                "first_name": "Updated",
                "last_name": "Name",
                "phone": "+1234567890",
                "scenario": "valid_update",
                "expected_result": "success"
            },
            
            # Empty name fields
            {
                "first_name": "",
                "last_name": "Name",
                "phone": "+1234567890",
                "scenario": "empty_first_name",
                "expected_result": "validation_error"
            },
            
            # Invalid phone
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "invalid-phone",
                "scenario": "invalid_phone",
                "expected_result": "validation_error"
            },
            
            # XSS attempts
            {
                "first_name": "<script>alert('xss')</script>",
                "last_name": "Doe",
                "phone": "+1234567890",
                "scenario": "xss_first_name",
                "expected_result": "sanitized_or_rejected"
            }
        ]
        
        return scenarios
    
    def create_password_change_scenarios(self) -> List[Dict[str, Any]]:
        """Create password change test scenarios"""
        current_password = self.generate_password("strong")
        
        scenarios = [
            # Valid password change
            {
                "current_password": current_password,
                "new_password": self.generate_password("strong"),
                "confirm_password": None,  # Will be set to new_password
                "scenario": "valid_change",
                "expected_result": "success"
            },
            
            # Wrong current password
            {
                "current_password": "wrongpassword",
                "new_password": self.generate_password("strong"),
                "confirm_password": None,
                "scenario": "wrong_current_password",
                "expected_result": "failure"
            },
            
            # Weak new password
            {
                "current_password": current_password,
                "new_password": "123",
                "confirm_password": "123",
                "scenario": "weak_new_password",
                "expected_result": "validation_error"
            },
            
            # Password mismatch
            {
                "current_password": current_password,
                "new_password": self.generate_password("strong"),
                "confirm_password": "different_password",
                "scenario": "password_mismatch",
                "expected_result": "validation_error"
            },
            
            # Same as current password
            {
                "current_password": current_password,
                "new_password": current_password,
                "confirm_password": current_password,
                "scenario": "same_as_current",
                "expected_result": "validation_error"
            }
        ]
        
        return scenarios
    
    def create_role_based_access_scenarios(self) -> List[Dict[str, Any]]:
        """Create role-based access control test scenarios"""
        scenarios = [
            # Guest user access
            {
                "user_role": None,  # Not logged in
                "protected_urls": [
                    "/dashboard",
                    "/profile",
                    "/orders",
                    "/settings"
                ],
                "scenario": "guest_access",
                "expected_result": "redirect_to_login"
            },
            
            # Registered user access
            {
                "user_role": UserRole.REGISTERED,
                "allowed_urls": [
                    "/dashboard",
                    "/profile",
                    "/orders"
                ],
                "restricted_urls": [
                    "/admin",
                    "/admin/users",
                    "/admin/products"
                ],
                "scenario": "registered_user_access",
                "expected_result": "appropriate_access"
            },
            
            # Premium user access
            {
                "user_role": UserRole.PREMIUM,
                "allowed_urls": [
                    "/dashboard",
                    "/profile",
                    "/orders",
                    "/premium-features"
                ],
                "restricted_urls": [
                    "/admin",
                    "/admin/users"
                ],
                "scenario": "premium_user_access",
                "expected_result": "appropriate_access"
            },
            
            # Admin user access
            {
                "user_role": UserRole.ADMIN,
                "allowed_urls": [
                    "/dashboard",
                    "/profile",
                    "/admin",
                    "/admin/users",
                    "/admin/products"
                ],
                "restricted_urls": [
                    "/admin/system-settings"
                ],
                "scenario": "admin_user_access",
                "expected_result": "appropriate_access"
            }
        ]
        
        return scenarios
    
    def get_test_users_by_role(self, count: int = 5) -> Dict[UserRole, List[TestUser]]:
        """Generate test users for each role"""
        users_by_role = {}
        
        for role in UserRole:
            users_by_role[role] = []
            for _ in range(count):
                user = self.create_test_user_model(role)
                users_by_role[role].append(user)
        
        return users_by_role