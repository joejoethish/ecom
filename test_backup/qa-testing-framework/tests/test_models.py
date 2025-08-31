"""
Unit tests for core data models

Tests validation methods, serialization/deserialization utilities,
and data integrity for TestCase, TestExecution, and Defect models.
"""

import unittest
import json
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import (
    TestCase, TestExecution, Defect, TestStep, BrowserInfo, DeviceInfo, DefectStatus,
    TestUser, TestProduct, ProductVariant, Address, PaymentMethod
)
from core.interfaces import (
    TestModule, Priority, UserRole, ExecutionStatus, Severity, Environment
)


class TestTestStep(unittest.TestCase):
    """Test TestStep model validation"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_step = TestStep(
            step_number=1,
            description="Click login button",
            action="Click on the login button",
            expected_result="Login form should appear"
        )
    
    def test_valid_step(self):
        """Test valid test step"""
        self.assertTrue(self.valid_step.is_valid())
        self.assertEqual(len(self.valid_step.validate()), 0)
    
    def test_missing_description(self):
        """Test validation with missing description"""
        step = TestStep(
            step_number=1,
            description="",
            action="Click button",
            expected_result="Form appears"
        )
        errors = step.validate()
        self.assertFalse(step.is_valid())
        self.assertIn("Step description is required", errors)
    
    def test_missing_action(self):
        """Test validation with missing action"""
        step = TestStep(
            step_number=1,
            description="Test step",
            action="",
            expected_result="Form appears"
        )
        errors = step.validate()
        self.assertFalse(step.is_valid())
        self.assertIn("Step action is required", errors)
    
    def test_missing_expected_result(self):
        """Test validation with missing expected result"""
        step = TestStep(
            step_number=1,
            description="Test step",
            action="Click button",
            expected_result=""
        )
        errors = step.validate()
        self.assertFalse(step.is_valid())
        self.assertIn("Step expected result is required", errors)
    
    def test_invalid_step_number(self):
        """Test validation with invalid step number"""
        step = TestStep(
            step_number=0,
            description="Test step",
            action="Click button",
            expected_result="Form appears"
        )
        errors = step.validate()
        self.assertFalse(step.is_valid())
        self.assertIn("Step number must be positive", errors)
    
    def test_negative_duration(self):
        """Test validation with negative duration"""
        step = TestStep(
            step_number=1,
            description="Test step",
            action="Click button",
            expected_result="Form appears",
            duration=-5.0
        )
        errors = step.validate()
        self.assertFalse(step.is_valid())
        self.assertIn("Step duration cannot be negative", errors)


class TestTestCase(unittest.TestCase):
    """Test TestCase model validation and serialization"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_steps = [
            TestStep(1, "Navigate to login", "Go to login page", "Login page loads"),
            TestStep(2, "Enter credentials", "Type username and password", "Credentials entered")
        ]
        
        self.valid_test_case = TestCase(
            id="TC001",
            name="User Login Test",
            description="Test user login functionality",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.REGISTERED,
            test_steps=self.valid_steps,
            expected_result="User successfully logs in",
            requirements=["REQ-1.1", "REQ-1.2"]
        )
    
    def test_valid_test_case(self):
        """Test valid test case"""
        self.assertTrue(self.valid_test_case.is_valid())
        self.assertEqual(len(self.valid_test_case.validate()), 0)
    
    def test_missing_id(self):
        """Test validation with missing ID"""
        test_case = TestCase(
            id="",
            name="Test",
            description="Test description",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.REGISTERED,
            test_steps=self.valid_steps,
            expected_result="Success"
        )
        errors = test_case.validate()
        self.assertFalse(test_case.is_valid())
        self.assertIn("Test case ID is required", errors)
    
    def test_invalid_id_format(self):
        """Test validation with invalid ID format"""
        test_case = TestCase(
            id="TC@001",
            name="Test",
            description="Test description",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.REGISTERED,
            test_steps=self.valid_steps,
            expected_result="Success"
        )
        errors = test_case.validate()
        self.assertFalse(test_case.is_valid())
        self.assertIn("Test case ID must contain only alphanumeric characters, underscores, and hyphens", errors)
    
    def test_missing_name(self):
        """Test validation with missing name"""
        test_case = TestCase(
            id="TC001",
            name="",
            description="Test description",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.REGISTERED,
            test_steps=self.valid_steps,
            expected_result="Success"
        )
        errors = test_case.validate()
        self.assertFalse(test_case.is_valid())
        self.assertIn("Test case name is required", errors)
    
    def test_missing_test_steps(self):
        """Test validation with missing test steps"""
        test_case = TestCase(
            id="TC001",
            name="Test",
            description="Test description",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.REGISTERED,
            test_steps=[],
            expected_result="Success"
        )
        errors = test_case.validate()
        self.assertFalse(test_case.is_valid())
        self.assertIn("At least one test step is required", errors)
    
    def test_invalid_test_steps(self):
        """Test validation with invalid test steps"""
        invalid_step = TestStep(0, "", "", "")
        test_case = TestCase(
            id="TC001",
            name="Test",
            description="Test description",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.REGISTERED,
            test_steps=[invalid_step],
            expected_result="Success"
        )
        errors = test_case.validate()
        self.assertFalse(test_case.is_valid())
        self.assertTrue(any("Step 1:" in error for error in errors))
    
    def test_negative_duration(self):
        """Test validation with negative estimated duration"""
        test_case = TestCase(
            id="TC001",
            name="Test",
            description="Test description",
            module=TestModule.WEB,
            priority=Priority.HIGH,
            user_role=UserRole.REGISTERED,
            test_steps=self.valid_steps,
            expected_result="Success",
            estimated_duration=-10
        )
        errors = test_case.validate()
        self.assertFalse(test_case.is_valid())
        self.assertIn("Estimated duration cannot be negative", errors)
    
    def test_serialization_to_dict(self):
        """Test serialization to dictionary"""
        data = self.valid_test_case.to_dict()
        
        self.assertEqual(data['id'], "TC001")
        self.assertEqual(data['name'], "User Login Test")
        self.assertEqual(data['module'], "web")
        self.assertEqual(data['priority'], "high")
        self.assertEqual(data['user_role'], "registered")
        self.assertIsInstance(data['created_date'], str)
        self.assertIsInstance(data['updated_date'], str)
    
    def test_deserialization_from_dict(self):
        """Test deserialization from dictionary"""
        data = self.valid_test_case.to_dict()
        restored_case = TestCase.from_dict(data)
        
        self.assertEqual(restored_case.id, self.valid_test_case.id)
        self.assertEqual(restored_case.name, self.valid_test_case.name)
        self.assertEqual(restored_case.module, self.valid_test_case.module)
        self.assertEqual(restored_case.priority, self.valid_test_case.priority)
        self.assertEqual(restored_case.user_role, self.valid_test_case.user_role)
        self.assertEqual(len(restored_case.test_steps), len(self.valid_test_case.test_steps))
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization"""
        json_str = self.valid_test_case.to_json()
        self.assertIsInstance(json_str, str)
        
        # Verify it's valid JSON
        data = json.loads(json_str)
        self.assertEqual(data['id'], "TC001")
        
        # Test round-trip
        restored_case = TestCase.from_json(json_str)
        self.assertEqual(restored_case.id, self.valid_test_case.id)
        self.assertEqual(restored_case.name, self.valid_test_case.name)


class TestBrowserInfo(unittest.TestCase):
    """Test BrowserInfo model validation"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_browser_info = BrowserInfo(
            name="Chrome",
            version="91.0.4472.124",
            platform="Windows 10",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport_size={"width": 1920, "height": 1080}
        )
    
    def test_valid_browser_info(self):
        """Test valid browser info"""
        self.assertTrue(self.valid_browser_info.is_valid())
        self.assertEqual(len(self.valid_browser_info.validate()), 0)
    
    def test_missing_name(self):
        """Test validation with missing name"""
        browser_info = BrowserInfo(
            name="",
            version="91.0",
            platform="Windows",
            user_agent="Mozilla/5.0"
        )
        errors = browser_info.validate()
        self.assertFalse(browser_info.is_valid())
        self.assertIn("Browser name is required", errors)
    
    def test_invalid_viewport_size(self):
        """Test validation with invalid viewport size"""
        browser_info = BrowserInfo(
            name="Chrome",
            version="91.0",
            platform="Windows",
            user_agent="Mozilla/5.0",
            viewport_size={"width": -100, "height": 1080}
        )
        errors = browser_info.validate()
        self.assertFalse(browser_info.is_valid())
        self.assertIn("Viewport width and height must be positive", errors)


class TestDeviceInfo(unittest.TestCase):
    """Test DeviceInfo model validation"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_device_info = DeviceInfo(
            platform="iOS",
            device_name="iPhone 12",
            os_version="14.6",
            app_version="1.0.0",
            screen_resolution={"width": 390, "height": 844}
        )
    
    def test_valid_device_info(self):
        """Test valid device info"""
        self.assertTrue(self.valid_device_info.is_valid())
        self.assertEqual(len(self.valid_device_info.validate()), 0)
    
    def test_invalid_platform(self):
        """Test validation with invalid platform"""
        device_info = DeviceInfo(
            platform="Windows",
            device_name="Surface",
            os_version="10",
            app_version="1.0.0"
        )
        errors = device_info.validate()
        self.assertFalse(device_info.is_valid())
        self.assertIn("Platform must be 'iOS' or 'Android'", errors)
    
    def test_missing_device_name(self):
        """Test validation with missing device name"""
        device_info = DeviceInfo(
            platform="iOS",
            device_name="",
            os_version="14.6",
            app_version="1.0.0"
        )
        errors = device_info.validate()
        self.assertFalse(device_info.is_valid())
        self.assertIn("Device name is required", errors)


class TestTestExecution(unittest.TestCase):
    """Test TestExecution model validation and serialization"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_execution = TestExecution(
            id="EXE001",
            test_case_id="TC001",
            environment=Environment.STAGING,
            status=ExecutionStatus.PASSED,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=5),
            actual_result="User logged in successfully"
        )
    
    def test_valid_execution(self):
        """Test valid test execution"""
        self.assertTrue(self.valid_execution.is_valid())
        self.assertEqual(len(self.valid_execution.validate()), 0)
    
    def test_duration_calculation(self):
        """Test duration calculation"""
        start = datetime.now()
        end = start + timedelta(minutes=5)
        execution = TestExecution(
            id="EXE001",
            test_case_id="TC001",
            environment=Environment.STAGING,
            status=ExecutionStatus.PASSED,
            start_time=start,
            end_time=end
        )
        self.assertEqual(execution.duration, 300.0)  # 5 minutes = 300 seconds
    
    def test_missing_id(self):
        """Test validation with missing ID"""
        execution = TestExecution(
            id="",
            test_case_id="TC001",
            environment=Environment.STAGING,
            status=ExecutionStatus.PASSED,
            start_time=datetime.now()
        )
        errors = execution.validate()
        self.assertFalse(execution.is_valid())
        self.assertIn("Execution ID is required", errors)
    
    def test_invalid_time_logic(self):
        """Test validation with invalid time logic"""
        start = datetime.now()
        end = start - timedelta(minutes=5)  # End before start
        execution = TestExecution(
            id="EXE001",
            test_case_id="TC001",
            environment=Environment.STAGING,
            status=ExecutionStatus.PASSED,
            start_time=start,
            end_time=end
        )
        errors = execution.validate()
        self.assertFalse(execution.is_valid())
        self.assertIn("End time cannot be before start time", errors)
    
    def test_serialization_to_dict(self):
        """Test serialization to dictionary"""
        data = self.valid_execution.to_dict()
        
        self.assertEqual(data['id'], "EXE001")
        self.assertEqual(data['test_case_id'], "TC001")
        self.assertEqual(data['environment'], "staging")
        self.assertEqual(data['status'], "passed")
        self.assertIsInstance(data['start_time'], str)
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization"""
        json_str = self.valid_execution.to_json()
        self.assertIsInstance(json_str, str)
        
        # Test round-trip
        restored_execution = TestExecution.from_json(json_str)
        self.assertEqual(restored_execution.id, self.valid_execution.id)
        self.assertEqual(restored_execution.environment, self.valid_execution.environment)


class TestDefect(unittest.TestCase):
    """Test Defect model validation and serialization"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_defect = Defect(
            id="DEF001",
            test_case_id="TC001",
            test_execution_id="EXE001",
            severity=Severity.MAJOR,
            title="Login button not working",
            description="The login button does not respond to clicks",
            reproduction_steps=[
                "Navigate to login page",
                "Click login button",
                "Observe no response"
            ],
            environment=Environment.STAGING
        )
    
    def test_valid_defect(self):
        """Test valid defect"""
        self.assertTrue(self.valid_defect.is_valid())
        self.assertEqual(len(self.valid_defect.validate()), 0)
    
    def test_missing_title(self):
        """Test validation with missing title"""
        defect = Defect(
            id="DEF001",
            test_case_id="TC001",
            test_execution_id="EXE001",
            severity=Severity.MAJOR,
            title="",
            description="Description",
            reproduction_steps=["Step 1"]
        )
        errors = defect.validate()
        self.assertFalse(defect.is_valid())
        self.assertIn("Defect title is required", errors)
    
    def test_missing_reproduction_steps(self):
        """Test validation with missing reproduction steps"""
        defect = Defect(
            id="DEF001",
            test_case_id="TC001",
            test_execution_id="EXE001",
            severity=Severity.MAJOR,
            title="Bug title",
            description="Description",
            reproduction_steps=[]
        )
        errors = defect.validate()
        self.assertFalse(defect.is_valid())
        self.assertIn("At least one reproduction step is required", errors)
    
    def test_invalid_status(self):
        """Test validation with invalid status"""
        defect = Defect(
            id="DEF001",
            test_case_id="TC001",
            test_execution_id="EXE001",
            severity=Severity.MAJOR,
            title="Bug title",
            description="Description",
            reproduction_steps=["Step 1"],
            status="invalid_status"
        )
        errors = defect.validate()
        self.assertFalse(defect.is_valid())
        self.assertIn("Invalid defect status", errors)
    
    def test_invalid_time_logic(self):
        """Test validation with invalid time logic"""
        created = datetime.now()
        resolved = created - timedelta(hours=1)  # Resolved before created
        defect = Defect(
            id="DEF001",
            test_case_id="TC001",
            test_execution_id="EXE001",
            severity=Severity.MAJOR,
            title="Bug title",
            description="Description",
            reproduction_steps=["Step 1"],
            created_date=created,
            resolved_date=resolved
        )
        errors = defect.validate()
        self.assertFalse(defect.is_valid())
        self.assertIn("Resolved date cannot be before created date", errors)
    
    def test_serialization_to_dict(self):
        """Test serialization to dictionary"""
        data = self.valid_defect.to_dict()
        
        self.assertEqual(data['id'], "DEF001")
        self.assertEqual(data['severity'], "major")
        self.assertEqual(data['environment'], "staging")
        self.assertIsInstance(data['created_date'], str)
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization"""
        json_str = self.valid_defect.to_json()
        self.assertIsInstance(json_str, str)
        
        # Test round-trip
        restored_defect = Defect.from_json(json_str)
        self.assertEqual(restored_defect.id, self.valid_defect.id)
        self.assertEqual(restored_defect.severity, self.valid_defect.severity)
        self.assertEqual(restored_defect.title, self.valid_defect.title)


class TestAddress(unittest.TestCase):
    """Test Address model validation"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA",
            address_type="shipping"
        )
    
    def test_valid_address(self):
        """Test valid address"""
        self.assertTrue(self.valid_address.is_valid())
        self.assertEqual(len(self.valid_address.validate()), 0)
    
    def test_missing_street(self):
        """Test validation with missing street"""
        address = Address(
            street="",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA"
        )
        errors = address.validate()
        self.assertFalse(address.is_valid())
        self.assertIn("Street address is required", errors)
    
    def test_invalid_address_type(self):
        """Test validation with invalid address type"""
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA",
            address_type="invalid"
        )
        errors = address.validate()
        self.assertFalse(address.is_valid())
        self.assertIn("Address type must be 'shipping' or 'billing'", errors)


class TestPaymentMethod(unittest.TestCase):
    """Test PaymentMethod model validation"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_credit_card = PaymentMethod(
            type="credit_card",
            details={
                "card_number": "4111111111111111",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123",
                "holder_name": "John Doe"
            }
        )
        
        self.valid_upi = PaymentMethod(
            type="upi",
            details={
                "upi_id": "user@paytm"
            }
        )
    
    def test_valid_credit_card(self):
        """Test valid credit card payment method"""
        self.assertTrue(self.valid_credit_card.is_valid())
        self.assertEqual(len(self.valid_credit_card.validate()), 0)
    
    def test_valid_upi(self):
        """Test valid UPI payment method"""
        self.assertTrue(self.valid_upi.is_valid())
        self.assertEqual(len(self.valid_upi.validate()), 0)
    
    def test_missing_card_number(self):
        """Test validation with missing card number"""
        payment_method = PaymentMethod(
            type="credit_card",
            details={
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123"
            }
        )
        errors = payment_method.validate()
        self.assertFalse(payment_method.is_valid())
        self.assertIn("Card number is required for card payments", errors)
    
    def test_invalid_upi_id(self):
        """Test validation with invalid UPI ID"""
        payment_method = PaymentMethod(
            type="upi",
            details={
                "upi_id": "invalid_upi_id"
            }
        )
        errors = payment_method.validate()
        self.assertFalse(payment_method.is_valid())
        self.assertIn("Invalid UPI ID format", errors)


class TestProductVariant(unittest.TestCase):
    """Test ProductVariant model validation"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_variant = ProductVariant(
            id="VAR001",
            name="Red Large",
            sku="SHIRT-RED-L",
            price=29.99,
            attributes={"color": "red", "size": "large"},
            stock_quantity=50
        )
    
    def test_valid_variant(self):
        """Test valid product variant"""
        self.assertTrue(self.valid_variant.is_valid())
        self.assertEqual(len(self.valid_variant.validate()), 0)
    
    def test_missing_id(self):
        """Test validation with missing ID"""
        variant = ProductVariant(
            id="",
            name="Red Large",
            sku="SHIRT-RED-L",
            price=29.99
        )
        errors = variant.validate()
        self.assertFalse(variant.is_valid())
        self.assertIn("Variant ID is required", errors)
    
    def test_negative_price(self):
        """Test validation with negative price"""
        variant = ProductVariant(
            id="VAR001",
            name="Red Large",
            sku="SHIRT-RED-L",
            price=-10.0
        )
        errors = variant.validate()
        self.assertFalse(variant.is_valid())
        self.assertIn("Variant price cannot be negative", errors)


class TestTestUser(unittest.TestCase):
    """Test TestUser model validation and serialization"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA"
        )
        
        self.valid_payment_method = PaymentMethod(
            type="credit_card",
            details={
                "card_number": "4111111111111111",
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123"
            }
        )
        
        self.valid_user = TestUser(
            id="USER001",
            user_type=UserRole.REGISTERED,
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            addresses=[self.valid_address],
            payment_methods=[self.valid_payment_method]
        )
    
    def test_valid_user(self):
        """Test valid test user"""
        self.assertTrue(self.valid_user.is_valid())
        self.assertEqual(len(self.valid_user.validate()), 0)
    
    def test_missing_email(self):
        """Test validation with missing email"""
        user = TestUser(
            id="USER001",
            user_type=UserRole.REGISTERED,
            email="",
            password="password123"
        )
        errors = user.validate()
        self.assertFalse(user.is_valid())
        self.assertIn("Email is required", errors)
    
    def test_invalid_email_format(self):
        """Test validation with invalid email format"""
        user = TestUser(
            id="USER001",
            user_type=UserRole.REGISTERED,
            email="invalid-email",
            password="password123"
        )
        errors = user.validate()
        self.assertFalse(user.is_valid())
        self.assertIn("Invalid email format", errors)
    
    def test_weak_password(self):
        """Test validation with weak password"""
        user = TestUser(
            id="USER001",
            user_type=UserRole.REGISTERED,
            email="test@example.com",
            password="123"
        )
        errors = user.validate()
        self.assertFalse(user.is_valid())
        self.assertIn("Password must be at least 6 characters long", errors)
    
    def test_invalid_phone_format(self):
        """Test validation with invalid phone format"""
        user = TestUser(
            id="USER001",
            user_type=UserRole.REGISTERED,
            email="test@example.com",
            password="password123",
            phone="invalid-phone"
        )
        errors = user.validate()
        self.assertFalse(user.is_valid())
        self.assertIn("Invalid phone number format", errors)
    
    def test_serialization_to_dict(self):
        """Test serialization to dictionary"""
        data = self.valid_user.to_dict()
        
        self.assertEqual(data['id'], "USER001")
        self.assertEqual(data['user_type'], "registered")
        self.assertEqual(data['email'], "test@example.com")
        self.assertIsInstance(data['created_date'], str)
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization"""
        json_str = self.valid_user.to_json()
        self.assertIsInstance(json_str, str)
        
        # Test round-trip
        restored_user = TestUser.from_json(json_str)
        self.assertEqual(restored_user.id, self.valid_user.id)
        self.assertEqual(restored_user.user_type, self.valid_user.user_type)
        self.assertEqual(restored_user.email, self.valid_user.email)


class TestTestProduct(unittest.TestCase):
    """Test TestProduct model validation and serialization"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_variant = ProductVariant(
            id="VAR001",
            name="Red Large",
            sku="SHIRT-RED-L",
            price=29.99,
            stock_quantity=50
        )
        
        self.valid_product = TestProduct(
            id="PROD001",
            name="Cotton T-Shirt",
            description="Comfortable cotton t-shirt",
            category="Clothing",
            price=25.99,
            stock_quantity=100,
            subcategory="T-Shirts",
            seller_id="SELLER001",
            variants=[self.valid_variant],
            images=["image1.jpg", "image2.jpg"]
        )
    
    def test_valid_product(self):
        """Test valid test product"""
        self.assertTrue(self.valid_product.is_valid())
        self.assertEqual(len(self.valid_product.validate()), 0)
    
    def test_missing_name(self):
        """Test validation with missing name"""
        product = TestProduct(
            id="PROD001",
            name="",
            description="Description",
            category="Clothing",
            price=25.99,
            stock_quantity=100
        )
        errors = product.validate()
        self.assertFalse(product.is_valid())
        self.assertIn("Product name is required", errors)
    
    def test_negative_price(self):
        """Test validation with negative price"""
        product = TestProduct(
            id="PROD001",
            name="Product",
            description="Description",
            category="Clothing",
            price=-10.0,
            stock_quantity=100
        )
        errors = product.validate()
        self.assertFalse(product.is_valid())
        self.assertIn("Product price cannot be negative", errors)
    
    def test_negative_stock(self):
        """Test validation with negative stock"""
        product = TestProduct(
            id="PROD001",
            name="Product",
            description="Description",
            category="Clothing",
            price=25.99,
            stock_quantity=-10
        )
        errors = product.validate()
        self.assertFalse(product.is_valid())
        self.assertIn("Stock quantity cannot be negative", errors)
    
    def test_invalid_status(self):
        """Test validation with invalid status"""
        product = TestProduct(
            id="PROD001",
            name="Product",
            description="Description",
            category="Clothing",
            price=25.99,
            stock_quantity=100,
            status="invalid_status"
        )
        errors = product.validate()
        self.assertFalse(product.is_valid())
        self.assertTrue(any("Invalid product status" in error for error in errors))
    
    def test_serialization_to_dict(self):
        """Test serialization to dictionary"""
        data = self.valid_product.to_dict()
        
        self.assertEqual(data['id'], "PROD001")
        self.assertEqual(data['name'], "Cotton T-Shirt")
        self.assertEqual(data['category'], "Clothing")
        self.assertIsInstance(data['created_date'], str)
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization"""
        json_str = self.valid_product.to_json()
        self.assertIsInstance(json_str, str)
        
        # Test round-trip
        restored_product = TestProduct.from_json(json_str)
        self.assertEqual(restored_product.id, self.valid_product.id)
        self.assertEqual(restored_product.name, self.valid_product.name)
        self.assertEqual(restored_product.category, self.valid_product.category)


if __name__ == '__main__':
    unittest.main()