"""
Core Data Models for QA Testing Framework

Defines the data structures used throughout the testing framework
for test cases, executions, defects, and test data.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import re
from .interfaces import (
    TestModule, Priority, UserRole, ExecutionStatus, 
    Severity, Environment
)


@dataclass
class TestStep:
    """Individual test step within a test case"""
    step_number: int
    description: str
    action: str
    expected_result: str
    actual_result: Optional[str] = None
    status: Optional[ExecutionStatus] = None
    screenshot_path: Optional[str] = None
    duration: Optional[float] = None
    
    def validate(self) -> List[str]:
        """Validate test step data integrity"""
        errors = []
        
        # Validate required fields
        if not self.description or not self.description.strip():
            errors.append("Step description is required")
        
        if not self.action or not self.action.strip():
            errors.append("Step action is required")
        
        if not self.expected_result or not self.expected_result.strip():
            errors.append("Step expected result is required")
        
        # Validate step number
        if self.step_number <= 0:
            errors.append("Step number must be positive")
        
        # Validate duration if provided
        if self.duration is not None and self.duration < 0:
            errors.append("Step duration cannot be negative")
        
        # Validate status if provided
        if self.status is not None and not isinstance(self.status, ExecutionStatus):
            errors.append("Invalid execution status")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if test step is valid"""
        return len(self.validate()) == 0


@dataclass
class TestCase:
    """Test case definition"""
    id: str
    name: str
    description: str
    module: TestModule
    priority: Priority
    user_role: UserRole
    test_steps: List[TestStep]
    expected_result: str
    prerequisites: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    estimated_duration: int = 0  # in minutes
    requirements: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    created_by: str = "qa_framework"
    
    def validate(self) -> List[str]:
        """Validate test case data integrity"""
        errors = []
        
        # Validate required fields
        if not self.id or not self.id.strip():
            errors.append("Test case ID is required")
        
        if not self.name or not self.name.strip():
            errors.append("Test case name is required")
        
        if not self.description or not self.description.strip():
            errors.append("Test case description is required")
        
        if not self.expected_result or not self.expected_result.strip():
            errors.append("Expected result is required")
        
        # Validate ID format (alphanumeric with underscores/hyphens)
        if self.id and not re.match(r'^[a-zA-Z0-9_-]+$', self.id):
            errors.append("Test case ID must contain only alphanumeric characters, underscores, and hyphens")
        
        # Validate test steps
        if not self.test_steps:
            errors.append("At least one test step is required")
        else:
            for i, step in enumerate(self.test_steps):
                step_errors = step.validate()
                for error in step_errors:
                    errors.append(f"Step {i+1}: {error}")
        
        # Validate estimated duration
        if self.estimated_duration < 0:
            errors.append("Estimated duration cannot be negative")
        
        # Validate enum values
        if not isinstance(self.module, TestModule):
            errors.append("Invalid test module")
        
        if not isinstance(self.priority, Priority):
            errors.append("Invalid priority")
        
        if not isinstance(self.user_role, UserRole):
            errors.append("Invalid user role")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if test case is valid"""
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to string values
        data['module'] = self.module.value
        data['priority'] = self.priority.value
        data['user_role'] = self.user_role.value
        # Convert datetime to ISO format
        data['created_date'] = self.created_date.isoformat()
        data['updated_date'] = self.updated_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCase':
        """Create TestCase from dictionary"""
        # Convert string values back to enums
        data['module'] = TestModule(data['module'])
        data['priority'] = Priority(data['priority'])
        data['user_role'] = UserRole(data['user_role'])
        # Convert ISO format back to datetime
        data['created_date'] = datetime.fromisoformat(data['created_date'])
        data['updated_date'] = datetime.fromisoformat(data['updated_date'])
        # Convert test steps
        data['test_steps'] = [TestStep(**step) for step in data['test_steps']]
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestCase':
        """Create TestCase from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class BrowserInfo:
    """Browser information for web tests"""
    name: str
    version: str
    platform: str
    user_agent: str
    viewport_size: Optional[Dict[str, int]] = None
    
    def validate(self) -> List[str]:
        """Validate browser information"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Browser name is required")
        
        if not self.version or not self.version.strip():
            errors.append("Browser version is required")
        
        if not self.platform or not self.platform.strip():
            errors.append("Platform is required")
        
        if not self.user_agent or not self.user_agent.strip():
            errors.append("User agent is required")
        
        # Validate viewport size if provided
        if self.viewport_size:
            if not isinstance(self.viewport_size, dict):
                errors.append("Viewport size must be a dictionary")
            elif 'width' not in self.viewport_size or 'height' not in self.viewport_size:
                errors.append("Viewport size must contain width and height")
            elif (not isinstance(self.viewport_size.get('width'), int) or 
                  not isinstance(self.viewport_size.get('height'), int)):
                errors.append("Viewport width and height must be integers")
            elif (self.viewport_size.get('width', 0) <= 0 or 
                  self.viewport_size.get('height', 0) <= 0):
                errors.append("Viewport width and height must be positive")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if browser info is valid"""
        return len(self.validate()) == 0


@dataclass
class DeviceInfo:
    """Device information for mobile tests"""
    platform: str  # iOS, Android
    device_name: str
    os_version: str
    app_version: str
    screen_resolution: Optional[Dict[str, int]] = None
    
    def validate(self) -> List[str]:
        """Validate device information"""
        errors = []
        
        if not self.platform or not self.platform.strip():
            errors.append("Platform is required")
        
        if not self.device_name or not self.device_name.strip():
            errors.append("Device name is required")
        
        if not self.os_version or not self.os_version.strip():
            errors.append("OS version is required")
        
        if not self.app_version or not self.app_version.strip():
            errors.append("App version is required")
        
        # Validate platform values
        if self.platform and self.platform.lower() not in ['ios', 'android']:
            errors.append("Platform must be 'iOS' or 'Android'")
        
        # Validate screen resolution if provided
        if self.screen_resolution:
            if not isinstance(self.screen_resolution, dict):
                errors.append("Screen resolution must be a dictionary")
            elif 'width' not in self.screen_resolution or 'height' not in self.screen_resolution:
                errors.append("Screen resolution must contain width and height")
            elif (not isinstance(self.screen_resolution.get('width'), int) or 
                  not isinstance(self.screen_resolution.get('height'), int)):
                errors.append("Screen resolution width and height must be integers")
            elif (self.screen_resolution.get('width', 0) <= 0 or 
                  self.screen_resolution.get('height', 0) <= 0):
                errors.append("Screen resolution width and height must be positive")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if device info is valid"""
        return len(self.validate()) == 0


@dataclass
class TestExecution:
    """Test execution record"""
    id: str
    test_case_id: str
    environment: Environment
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    actual_result: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    defects: List[str] = field(default_factory=list)  # defect IDs
    browser_info: Optional[BrowserInfo] = None
    device_info: Optional[DeviceInfo] = None
    executed_by: str = "qa_framework"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate execution duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def validate(self) -> List[str]:
        """Validate test execution data integrity"""
        errors = []
        
        # Validate required fields
        if not self.id or not self.id.strip():
            errors.append("Execution ID is required")
        
        if not self.test_case_id or not self.test_case_id.strip():
            errors.append("Test case ID is required")
        
        if not self.executed_by or not self.executed_by.strip():
            errors.append("Executed by is required")
        
        # Validate ID format
        if self.id and not re.match(r'^[a-zA-Z0-9_-]+$', self.id):
            errors.append("Execution ID must contain only alphanumeric characters, underscores, and hyphens")
        
        # Validate enum values
        if not isinstance(self.environment, Environment):
            errors.append("Invalid environment")
        
        if not isinstance(self.status, ExecutionStatus):
            errors.append("Invalid execution status")
        
        # Validate time logic
        if self.end_time and self.start_time and self.end_time < self.start_time:
            errors.append("End time cannot be before start time")
        
        # Validate browser info if provided
        if self.browser_info:
            browser_errors = self.browser_info.validate()
            for error in browser_errors:
                errors.append(f"Browser info: {error}")
        
        # Validate device info if provided
        if self.device_info:
            device_errors = self.device_info.validate()
            for error in device_errors:
                errors.append(f"Device info: {error}")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if test execution is valid"""
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to string values
        data['environment'] = self.environment.value
        data['status'] = self.status.value
        # Convert datetime to ISO format
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestExecution':
        """Create TestExecution from dictionary"""
        # Convert string values back to enums
        data['environment'] = Environment(data['environment'])
        data['status'] = ExecutionStatus(data['status'])
        # Convert ISO format back to datetime
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        # Convert nested objects
        if data.get('browser_info'):
            data['browser_info'] = BrowserInfo(**data['browser_info'])
        if data.get('device_info'):
            data['device_info'] = DeviceInfo(**data['device_info'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestExecution':
        """Create TestExecution from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class DefectStatus:
    """Defect status enumeration"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


@dataclass
class Defect:
    """Defect/bug record"""
    id: str
    test_case_id: str
    test_execution_id: str
    severity: Severity
    status: str = DefectStatus.OPEN
    title: str = ""
    description: str = ""
    reproduction_steps: List[str] = field(default_factory=list)
    environment: Optional[Environment] = None
    browser_info: Optional[BrowserInfo] = None
    device_info: Optional[DeviceInfo] = None
    screenshots: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    resolved_date: Optional[datetime] = None
    created_by: str = "qa_framework"
    tags: List[str] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate defect data integrity"""
        errors = []
        
        # Validate required fields
        if not self.id or not self.id.strip():
            errors.append("Defect ID is required")
        
        if not self.test_case_id or not self.test_case_id.strip():
            errors.append("Test case ID is required")
        
        if not self.test_execution_id or not self.test_execution_id.strip():
            errors.append("Test execution ID is required")
        
        if not self.title or not self.title.strip():
            errors.append("Defect title is required")
        
        if not self.description or not self.description.strip():
            errors.append("Defect description is required")
        
        if not self.created_by or not self.created_by.strip():
            errors.append("Created by is required")
        
        # Validate ID format
        if self.id and not re.match(r'^[a-zA-Z0-9_-]+$', self.id):
            errors.append("Defect ID must contain only alphanumeric characters, underscores, and hyphens")
        
        # Validate enum values
        if not isinstance(self.severity, Severity):
            errors.append("Invalid severity")
        
        # Validate status
        valid_statuses = [DefectStatus.OPEN, DefectStatus.IN_PROGRESS, 
                         DefectStatus.RESOLVED, DefectStatus.CLOSED, DefectStatus.REOPENED]
        if self.status not in valid_statuses:
            errors.append("Invalid defect status")
        
        # Validate environment if provided
        if self.environment and not isinstance(self.environment, Environment):
            errors.append("Invalid environment")
        
        # Validate time logic
        if self.resolved_date and self.created_date and self.resolved_date < self.created_date:
            errors.append("Resolved date cannot be before created date")
        
        # Validate browser info if provided
        if self.browser_info:
            browser_errors = self.browser_info.validate()
            for error in browser_errors:
                errors.append(f"Browser info: {error}")
        
        # Validate device info if provided
        if self.device_info:
            device_errors = self.device_info.validate()
            for error in device_errors:
                errors.append(f"Device info: {error}")
        
        # Validate reproduction steps
        if not self.reproduction_steps:
            errors.append("At least one reproduction step is required")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if defect is valid"""
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to string values
        data['severity'] = self.severity.value
        if self.environment:
            data['environment'] = self.environment.value
        # Convert datetime to ISO format
        data['created_date'] = self.created_date.isoformat()
        if self.resolved_date:
            data['resolved_date'] = self.resolved_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Defect':
        """Create Defect from dictionary"""
        # Convert string values back to enums
        data['severity'] = Severity(data['severity'])
        if data.get('environment'):
            data['environment'] = Environment(data['environment'])
        # Convert ISO format back to datetime
        data['created_date'] = datetime.fromisoformat(data['created_date'])
        if data.get('resolved_date'):
            data['resolved_date'] = datetime.fromisoformat(data['resolved_date'])
        # Convert nested objects
        if data.get('browser_info'):
            data['browser_info'] = BrowserInfo(**data['browser_info'])
        if data.get('device_info'):
            data['device_info'] = DeviceInfo(**data['device_info'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Defect':
        """Create Defect from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class Address:
    """Address data for testing"""
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    address_type: str = "shipping"  # shipping, billing
    
    def validate(self) -> List[str]:
        """Validate address data integrity"""
        errors = []
        
        # Validate required fields
        if not self.street or not self.street.strip():
            errors.append("Street address is required")
        
        if not self.city or not self.city.strip():
            errors.append("City is required")
        
        if not self.state or not self.state.strip():
            errors.append("State is required")
        
        if not self.postal_code or not self.postal_code.strip():
            errors.append("Postal code is required")
        
        if not self.country or not self.country.strip():
            errors.append("Country is required")
        
        # Validate address type
        valid_types = ["shipping", "billing"]
        if self.address_type not in valid_types:
            errors.append("Address type must be 'shipping' or 'billing'")
        
        # Validate postal code format (basic validation)
        if self.postal_code and not re.match(r'^[a-zA-Z0-9\s-]{3,10}$', self.postal_code):
            errors.append("Invalid postal code format")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if address is valid"""
        return len(self.validate()) == 0


@dataclass
class PaymentMethod:
    """Payment method data for testing"""
    type: str  # credit_card, debit_card, paypal, upi, cod
    details: Dict[str, Any] = field(default_factory=dict)
    is_default: bool = False
    
    def validate(self) -> List[str]:
        """Validate payment method data integrity"""
        errors = []
        
        # Validate required fields
        if not self.type or not self.type.strip():
            errors.append("Payment method type is required")
        
        # Validate payment method type
        valid_types = ["credit_card", "debit_card", "paypal", "upi", "cod", "wallet"]
        if self.type not in valid_types:
            errors.append(f"Invalid payment method type. Must be one of: {', '.join(valid_types)}")
        
        # Validate details based on payment type
        if self.type in ["credit_card", "debit_card"]:
            if not self.details.get("card_number"):
                errors.append("Card number is required for card payments")
            elif not re.match(r'^\d{13,19}$', str(self.details["card_number"]).replace(' ', '')):
                errors.append("Invalid card number format")
            
            if not self.details.get("expiry_month") or not self.details.get("expiry_year"):
                errors.append("Expiry month and year are required for card payments")
            
            if not self.details.get("cvv"):
                errors.append("CVV is required for card payments")
            elif not re.match(r'^\d{3,4}$', str(self.details["cvv"])):
                errors.append("Invalid CVV format")
        
        elif self.type == "upi":
            if not self.details.get("upi_id"):
                errors.append("UPI ID is required for UPI payments")
            elif not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+$', self.details["upi_id"]):
                errors.append("Invalid UPI ID format")
        
        elif self.type == "paypal":
            if not self.details.get("email"):
                errors.append("Email is required for PayPal payments")
            elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.details["email"]):
                errors.append("Invalid email format for PayPal")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if payment method is valid"""
        return len(self.validate()) == 0


@dataclass
class TestUser:
    """Test user data model"""
    id: str
    user_type: UserRole
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    profile_data: Dict[str, Any] = field(default_factory=dict)
    addresses: List[Address] = field(default_factory=list)
    payment_methods: List[PaymentMethod] = field(default_factory=list)
    is_active: bool = True
    created_date: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> List[str]:
        """Validate test user data integrity"""
        errors = []
        
        # Validate required fields
        if not self.id or not self.id.strip():
            errors.append("User ID is required")
        
        if not self.email or not self.email.strip():
            errors.append("Email is required")
        
        if not self.password or not self.password.strip():
            errors.append("Password is required")
        
        # Validate ID format
        if self.id and not re.match(r'^[a-zA-Z0-9_-]+$', self.id):
            errors.append("User ID must contain only alphanumeric characters, underscores, and hyphens")
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if self.email and not re.match(email_pattern, self.email):
            errors.append("Invalid email format")
        
        # Validate password strength (basic requirements)
        if self.password:
            if len(self.password) < 6:
                errors.append("Password must be at least 6 characters long")
        
        # Validate phone format if provided
        if self.phone and self.phone.strip():
            phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
            if not re.match(phone_pattern, self.phone.replace(' ', '').replace('-', '')):
                errors.append("Invalid phone number format")
        
        # Validate user role
        if not isinstance(self.user_type, UserRole):
            errors.append("Invalid user role")
        
        # Validate addresses
        for i, address in enumerate(self.addresses):
            address_errors = address.validate()
            for error in address_errors:
                errors.append(f"Address {i+1}: {error}")
        
        # Validate payment methods
        for i, payment_method in enumerate(self.payment_methods):
            payment_errors = payment_method.validate()
            for error in payment_errors:
                errors.append(f"Payment method {i+1}: {error}")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if test user is valid"""
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to string values
        data['user_type'] = self.user_type.value
        # Convert datetime to ISO format
        data['created_date'] = self.created_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestUser':
        """Create TestUser from dictionary"""
        # Convert string values back to enums
        data['user_type'] = UserRole(data['user_type'])
        # Convert ISO format back to datetime
        data['created_date'] = datetime.fromisoformat(data['created_date'])
        # Convert nested objects
        data['addresses'] = [Address(**addr) for addr in data.get('addresses', [])]
        data['payment_methods'] = [PaymentMethod(**pm) for pm in data.get('payment_methods', [])]
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestUser':
        """Create TestUser from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class ProductVariant:
    """Product variant for testing"""
    id: str
    name: str
    sku: str
    price: float
    attributes: Dict[str, Any] = field(default_factory=dict)  # size, color, etc.
    stock_quantity: int = 0
    
    def validate(self) -> List[str]:
        """Validate product variant data integrity"""
        errors = []
        
        # Validate required fields
        if not self.id or not self.id.strip():
            errors.append("Variant ID is required")
        
        if not self.name or not self.name.strip():
            errors.append("Variant name is required")
        
        if not self.sku or not self.sku.strip():
            errors.append("Variant SKU is required")
        
        # Validate ID format
        if self.id and not re.match(r'^[a-zA-Z0-9_-]+$', self.id):
            errors.append("Variant ID must contain only alphanumeric characters, underscores, and hyphens")
        
        # Validate SKU format
        if self.sku and not re.match(r'^[a-zA-Z0-9_-]+$', self.sku):
            errors.append("SKU must contain only alphanumeric characters, underscores, and hyphens")
        
        # Validate price
        if self.price < 0:
            errors.append("Variant price cannot be negative")
        
        # Validate stock quantity
        if self.stock_quantity < 0:
            errors.append("Variant stock quantity cannot be negative")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if product variant is valid"""
        return len(self.validate()) == 0


@dataclass
class TestProduct:
    """Test product data model"""
    id: str
    name: str
    description: str
    category: str
    price: float
    stock_quantity: int
    subcategory: str = ""
    seller_id: str = ""
    status: str = "active"  # active, inactive, out_of_stock
    variants: List[ProductVariant] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_date: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> List[str]:
        """Validate test product data integrity"""
        errors = []
        
        # Validate required fields
        if not self.id or not self.id.strip():
            errors.append("Product ID is required")
        
        if not self.name or not self.name.strip():
            errors.append("Product name is required")
        
        if not self.description or not self.description.strip():
            errors.append("Product description is required")
        
        if not self.category or not self.category.strip():
            errors.append("Product category is required")
        
        # Validate ID format
        if self.id and not re.match(r'^[a-zA-Z0-9_-]+$', self.id):
            errors.append("Product ID must contain only alphanumeric characters, underscores, and hyphens")
        
        # Validate price
        if self.price < 0:
            errors.append("Product price cannot be negative")
        
        # Validate stock quantity
        if self.stock_quantity < 0:
            errors.append("Stock quantity cannot be negative")
        
        # Validate status
        valid_statuses = ["active", "inactive", "out_of_stock", "discontinued"]
        if self.status not in valid_statuses:
            errors.append(f"Invalid product status. Must be one of: {', '.join(valid_statuses)}")
        
        # Validate variants
        for i, variant in enumerate(self.variants):
            variant_errors = variant.validate()
            for error in variant_errors:
                errors.append(f"Variant {i+1}: {error}")
        
        # Validate category format
        if self.category and not re.match(r'^[a-zA-Z0-9\s_-]+$', self.category):
            errors.append("Category must contain only alphanumeric characters, spaces, underscores, and hyphens")
        
        # Validate subcategory format if provided
        if self.subcategory and not re.match(r'^[a-zA-Z0-9\s_-]+$', self.subcategory):
            errors.append("Subcategory must contain only alphanumeric characters, spaces, underscores, and hyphens")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if test product is valid"""
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime to ISO format
        data['created_date'] = self.created_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestProduct':
        """Create TestProduct from dictionary"""
        # Convert ISO format back to datetime
        data['created_date'] = datetime.fromisoformat(data['created_date'])
        # Convert nested objects
        data['variants'] = [ProductVariant(**variant) for variant in data.get('variants', [])]
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestProduct':
        """Create TestProduct from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class OrderItem:
    """Order item for testing"""
    product_id: str
    variant_id: Optional[str] = None
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0


@dataclass
class TestOrder:
    """Test order data model"""
    id: str
    user_id: str
    items: List[OrderItem]
    status: str = "pending"  # pending, confirmed, shipped, delivered, cancelled
    shipping_address: Optional[Address] = None
    billing_address: Optional[Address] = None
    payment_method: Optional[PaymentMethod] = None
    subtotal: float = 0.0
    tax_amount: float = 0.0
    shipping_cost: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)


@dataclass
class TestDataSet:
    """Complete test data set for isolated testing"""
    users: List[TestUser] = field(default_factory=list)
    products: List[TestProduct] = field(default_factory=list)
    orders: List[TestOrder] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    
    def get_user_by_type(self, user_type: UserRole) -> Optional[TestUser]:
        """Get first user of specified type"""
        for user in self.users:
            if user.user_type == user_type:
                return user
        return None
    
    def get_users_by_type(self, user_type: UserRole) -> List[TestUser]:
        """Get all users of specified type"""
        return [user for user in self.users if user.user_type == user_type]
    
    def get_products_by_category(self, category: str) -> List[TestProduct]:
        """Get products in specified category"""
        return [product for product in self.products if product.category == category]
    
    def get_active_products(self) -> List[TestProduct]:
        """Get all active products"""
        return [product for product in self.products if product.status == "active"]


@dataclass
class TestSuite:
    """Test suite containing multiple test cases"""
    id: str
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    environment: Optional[Environment] = None
    parallel_execution: bool = False
    tags: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    
    def get_test_cases_by_module(self, module: TestModule) -> List[TestCase]:
        """Get test cases for specific module"""
        return [tc for tc in self.test_cases if tc.module == module]
    
    def get_test_cases_by_priority(self, priority: Priority) -> List[TestCase]:
        """Get test cases by priority"""
        return [tc for tc in self.test_cases if tc.priority == priority]
    
    def get_critical_tests(self) -> List[TestCase]:
        """Get critical priority test cases"""
        return self.get_test_cases_by_priority(Priority.CRITICAL)


@dataclass
class TestRun:
    """Test run execution record"""
    id: str
    test_suite_id: str
    environment: Environment
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    executions: List[TestExecution] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    executed_by: str = "qa_framework"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate total run duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage"""
        if not self.executions:
            return 0.0
        
        passed = len([e for e in self.executions if e.status == ExecutionStatus.PASSED])
        return (passed / len(self.executions)) * 100
    
    def get_failed_executions(self) -> List[TestExecution]:
        """Get failed test executions"""
        return [e for e in self.executions if e.status == ExecutionStatus.FAILED]
    
    def get_executions_by_module(self, module: TestModule) -> List[TestExecution]:
        """Get executions for specific module"""
        # This would require looking up test cases by execution ID
        # Implementation would depend on data access layer
        return []