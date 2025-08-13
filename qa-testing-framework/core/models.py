"""
Core Data Models for QA Testing Framework

Defines the data structures used throughout the testing framework
for test cases, executions, defects, and test data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
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


@dataclass
class BrowserInfo:
    """Browser information for web tests"""
    name: str
    version: str
    platform: str
    user_agent: str
    viewport_size: Optional[Dict[str, int]] = None


@dataclass
class DeviceInfo:
    """Device information for mobile tests"""
    platform: str  # iOS, Android
    device_name: str
    os_version: str
    app_version: str
    screen_resolution: Optional[Dict[str, int]] = None


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


@dataclass
class Address:
    """Address data for testing"""
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    address_type: str = "shipping"  # shipping, billing


@dataclass
class PaymentMethod:
    """Payment method data for testing"""
    type: str  # credit_card, debit_card, paypal, upi, cod
    details: Dict[str, Any] = field(default_factory=dict)
    is_default: bool = False


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


@dataclass
class ProductVariant:
    """Product variant for testing"""
    id: str
    name: str
    sku: str
    price: float
    attributes: Dict[str, Any] = field(default_factory=dict)  # size, color, etc.
    stock_quantity: int = 0


@dataclass
class TestProduct:
    """Test product data model"""
    id: str
    name: str
    description: str
    category: str
    subcategory: str = ""
    price: float
    stock_quantity: int
    variants: List[ProductVariant] = field(default_factory=list)
    seller_id: str = ""
    status: str = "active"  # active, inactive, out_of_stock
    images: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_date: datetime = field(default_factory=datetime.now)


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