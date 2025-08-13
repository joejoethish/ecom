"""
Unit Tests for TestDataManager

Tests the test data management functionality including user creation,
product generation, and data cleanup operations.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from core.data_manager import TestDataManager
from core.interfaces import UserRole, Environment
from core.models import TestUser, TestProduct


class TestDataManagerTests(unittest.TestCase):
    """Test cases for TestDataManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.data_manager = TestDataManager()
        self.test_environment = Environment.DEVELOPMENT
    
    def test_initialization(self):
        """Test TestDataManager initialization"""
        self.assertIsInstance(self.data_manager, TestDataManager)
        self.assertEqual(self.data_manager.current_environment, Environment.DEVELOPMENT)
        self.assertIsInstance(self.data_manager.created_users, dict)
        self.assertIsInstance(self.data_manager.created_products, dict)
        self.assertIsInstance(self.data_manager.categories, dict)
        self.assertGreater(len(self.data_manager.categories), 0)
    
    def test_create_test_user_registered(self):
        """Test creating a registered test user"""
        user_data = self.data_manager.create_test_user(UserRole.REGISTERED)
        
        self.assertIsInstance(user_data, dict)
        self.assertIn("id", user_data)
        self.assertIn("email", user_data)
        self.assertIn("password", user_data)
        self.assertEqual(user_data["user_type"], UserRole.REGISTERED.value)
        self.assertTrue(user_data["email"].endswith("@testdomain.com"))
        self.assertGreaterEqual(len(user_data["password"]), 6)
    
    def test_create_test_user_premium(self):
        """Test creating a premium test user"""
        user_data = self.data_manager.create_test_user(UserRole.PREMIUM)
        
        self.assertEqual(user_data["user_type"], UserRole.PREMIUM.value)
        self.assertIn("profile_data", user_data)
        self.assertIn("loyalty_points", user_data["profile_data"])
        self.assertIn("membership_tier", user_data["profile_data"])
    
    def test_create_test_user_seller(self):
        """Test creating a seller test user"""
        user_data = self.data_manager.create_test_user(UserRole.SELLER)
        
        self.assertEqual(user_data["user_type"], UserRole.SELLER.value)
        self.assertIn("profile_data", user_data)
        self.assertIn("store_name", user_data["profile_data"])
        self.assertIn("business_type", user_data["profile_data"])
    
    def test_create_test_user_admin(self):
        """Test creating an admin test user"""
        user_data = self.data_manager.create_test_user(UserRole.ADMIN)
        
        self.assertEqual(user_data["user_type"], UserRole.ADMIN.value)
        self.assertIn("profile_data", user_data)
        self.assertIn("admin_permissions", user_data["profile_data"])
        self.assertIn("department", user_data["profile_data"])
    
    def test_create_test_user_guest(self):
        """Test creating a guest test user"""
        user_data = self.data_manager.create_test_user(UserRole.GUEST)
        
        self.assertEqual(user_data["user_type"], UserRole.GUEST.value)
        self.assertEqual(len(user_data["addresses"]), 0)  # Guests have no saved addresses
        self.assertEqual(len(user_data["payment_methods"]), 0)  # Guests have no saved payment methods
    
    def test_generate_test_products_electronics(self):
        """Test generating electronics products"""
        products = self.data_manager.generate_test_products("Electronics", 5)
        
        self.assertEqual(len(products), 5)
        for product in products:
            self.assertIsInstance(product, dict)
            self.assertEqual(product["category"], "Electronics")
            self.assertIn("id", product)
            self.assertIn("name", product)
            self.assertIn("price", product)
            self.assertGreater(product["price"], 0)
    
    def test_generate_test_products_clothing(self):
        """Test generating clothing products"""
        products = self.data_manager.generate_test_products("Clothing", 3)
        
        self.assertEqual(len(products), 3)
        for product in products:
            self.assertEqual(product["category"], "Clothing")
            self.assertIn("variants", product)
            # Clothing should have variants with size/color
            if product["variants"]:
                variant = product["variants"][0]
                self.assertIn("attributes", variant)
    
    def test_generate_test_products_invalid_category(self):
        """Test generating products with invalid category"""
        products = self.data_manager.generate_test_products("InvalidCategory", 2)
        
        self.assertEqual(len(products), 2)
        for product in products:
            self.assertEqual(product["category"], "InvalidCategory")
    
    def test_setup_test_data_success(self):
        """Test successful test data setup"""
        with patch('core.data_manager.get_config') as mock_config:
            mock_config.return_value = {
                "users_count": 10,
                "products_count": 20,
                "categories_count": 5
            }
            
            result = self.data_manager.setup_test_data(self.test_environment)
            
            self.assertTrue(result)
            self.assertIn(self.test_environment, self.data_manager.created_users)
            self.assertIn(self.test_environment, self.data_manager.created_products)
    
    def test_cleanup_test_data_success(self):
        """Test successful test data cleanup"""
        # Setup some test data first
        self.data_manager.created_users[self.test_environment] = []
        self.data_manager.created_products[self.test_environment] = []
        
        result = self.data_manager.cleanup_test_data(self.test_environment.value)
        
        self.assertTrue(result)
        self.assertNotIn(self.test_environment, self.data_manager.created_users)
        self.assertNotIn(self.test_environment, self.data_manager.created_products)
    
    def test_get_test_users_by_role(self):
        """Test getting test users by role"""
        # Create some test users
        self.data_manager.create_test_user(UserRole.REGISTERED)
        self.data_manager.create_test_user(UserRole.PREMIUM)
        self.data_manager.create_test_user(UserRole.REGISTERED)
        
        registered_users = self.data_manager.get_test_users_by_role(UserRole.REGISTERED)
        premium_users = self.data_manager.get_test_users_by_role(UserRole.PREMIUM)
        
        self.assertEqual(len(registered_users), 2)
        self.assertEqual(len(premium_users), 1)
        
        for user in registered_users:
            self.assertEqual(user["user_type"], UserRole.REGISTERED.value)
    
    def test_get_test_products_by_category(self):
        """Test getting test products by category"""
        # Create some test products
        self.data_manager.generate_test_products("Electronics", 3)
        self.data_manager.generate_test_products("Clothing", 2)
        
        electronics_products = self.data_manager.get_test_products_by_category("Electronics")
        clothing_products = self.data_manager.get_test_products_by_category("Clothing")
        
        self.assertEqual(len(electronics_products), 3)
        self.assertEqual(len(clothing_products), 2)
        
        for product in electronics_products:
            self.assertEqual(product["category"], "Electronics")
    
    def test_create_isolated_test_data(self):
        """Test creating isolated test data for specific test case"""
        requirements = {
            "users": [
                {"role": "registered", "count": 2},
                {"role": "premium", "count": 1}
            ],
            "products": [
                {"category": "Electronics", "count": 3},
                {"category": "Clothing", "count": 2}
            ]
        }
        
        isolated_data = self.data_manager.create_isolated_test_data("test_case_123", requirements)
        
        self.assertIsInstance(isolated_data, dict)
        self.assertEqual(isolated_data["test_case_id"], "test_case_123")
        self.assertEqual(len(isolated_data["users"]), 3)  # 2 registered + 1 premium
        self.assertEqual(len(isolated_data["products"]), 5)  # 3 electronics + 2 clothing
        self.assertIn("created_at", isolated_data)
    
    def test_password_generation(self):
        """Test password generation requirements"""
        password = self.data_manager._generate_password()
        
        self.assertGreaterEqual(len(password), 8)
        self.assertLessEqual(len(password), 12)
        self.assertTrue(any(c.isdigit() for c in password))  # Has digit
        self.assertTrue(any(c in "!@#$%" for c in password))  # Has special char
    
    def test_product_price_generation(self):
        """Test product price generation by category"""
        electronics_price = self.data_manager._generate_product_price("Electronics")
        clothing_price = self.data_manager._generate_product_price("Clothing")
        books_price = self.data_manager._generate_product_price("Books")
        
        # Electronics should be more expensive than books
        self.assertGreaterEqual(electronics_price, 50)
        self.assertLessEqual(electronics_price, 2000)
        
        self.assertGreaterEqual(clothing_price, 20)
        self.assertLessEqual(clothing_price, 300)
        
        self.assertGreaterEqual(books_price, 10)
        self.assertLessEqual(books_price, 50)
    
    def test_address_generation_for_different_roles(self):
        """Test address generation for different user roles"""
        # Guest users should have no addresses
        guest_addresses = self.data_manager._generate_addresses(UserRole.GUEST)
        self.assertEqual(len(guest_addresses), 0)
        
        # Registered users should have 1-3 addresses
        registered_addresses = self.data_manager._generate_addresses(UserRole.REGISTERED)
        self.assertGreaterEqual(len(registered_addresses), 1)
        self.assertLessEqual(len(registered_addresses), 3)
        
        # Check address validity
        if registered_addresses:
            address = registered_addresses[0]
            self.assertTrue(address.is_valid())
    
    def test_payment_method_generation_for_different_roles(self):
        """Test payment method generation for different user roles"""
        # Guest users should have no payment methods
        guest_methods = self.data_manager._generate_payment_methods(UserRole.GUEST)
        self.assertEqual(len(guest_methods), 0)
        
        # Premium users should have 2-4 payment methods
        premium_methods = self.data_manager._generate_payment_methods(UserRole.PREMIUM)
        self.assertGreaterEqual(len(premium_methods), 2)
        self.assertLessEqual(len(premium_methods), 4)
        
        # Check payment method validity
        if premium_methods:
            method = premium_methods[0]
            self.assertTrue(method.is_valid())
            self.assertTrue(method.is_default)  # First method should be default
    
    def test_product_variant_generation(self):
        """Test product variant generation for different categories"""
        # Clothing should have size/color variants
        clothing_variants = self.data_manager._generate_product_variants("Clothing", "Men's Wear")
        if clothing_variants:
            variant = clothing_variants[0]
            self.assertIn("size", variant.attributes)
            self.assertIn("color", variant.attributes)
        
        # Electronics should have storage/color variants for phones
        electronics_variants = self.data_manager._generate_product_variants("Electronics", "Smartphones")
        if electronics_variants:
            variant = electronics_variants[0]
            self.assertTrue("storage" in variant.attributes or "color" in variant.attributes)
    
    def test_product_attributes_generation(self):
        """Test product attributes generation for different categories"""
        electronics_attrs = self.data_manager._generate_product_attributes("Electronics", "Smartphones")
        clothing_attrs = self.data_manager._generate_product_attributes("Clothing", "Men's Wear")
        books_attrs = self.data_manager._generate_product_attributes("Books", "Fiction")
        
        # All should have common attributes
        for attrs in [electronics_attrs, clothing_attrs, books_attrs]:
            self.assertIn("weight", attrs)
            self.assertIn("dimensions", attrs)
            self.assertIn("warranty", attrs)
        
        # Category-specific attributes
        self.assertIn("brand", electronics_attrs)
        self.assertIn("energy_rating", electronics_attrs)
        
        self.assertIn("material", clothing_attrs)
        self.assertIn("care_instructions", clothing_attrs)
        
        self.assertIn("author", books_attrs)
        self.assertIn("publisher", books_attrs)
        self.assertIn("pages", books_attrs)
    
    def test_user_tracking_across_environments(self):
        """Test user tracking across different environments"""
        # Create users in development environment
        dev_user = self.data_manager.create_test_user(UserRole.REGISTERED)
        
        # Switch to staging environment
        self.data_manager.current_environment = Environment.STAGING
        staging_user = self.data_manager.create_test_user(UserRole.REGISTERED)
        
        # Check that users are tracked separately
        dev_users = self.data_manager.get_test_users_by_role(UserRole.REGISTERED, Environment.DEVELOPMENT)
        staging_users = self.data_manager.get_test_users_by_role(UserRole.REGISTERED, Environment.STAGING)
        
        self.assertEqual(len(dev_users), 1)
        self.assertEqual(len(staging_users), 1)
        self.assertNotEqual(dev_users[0]["id"], staging_users[0]["id"])


if __name__ == '__main__':
    unittest.main()