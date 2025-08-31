"""
Core Interfaces for QA Testing Framework

Defines base interfaces for test managers, data managers, and report generators
to ensure consistent implementation across all testing modules.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class TestModule(Enum):
    """Test module types"""
    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    DATABASE = "database"
    INTEGRATION = "integration"


class Priority(Enum):
    """Test case priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UserRole(Enum):
    """User roles for testing"""
    GUEST = "guest"
    REGISTERED = "registered"
    PREMIUM = "premium"
    SELLER = "seller"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class ExecutionStatus(Enum):
    """Test execution status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class Severity(Enum):
    """Defect severity levels"""
    CRITICAL = "critical"  # System crashes, security issues
    MAJOR = "major"        # Feature not working
    MINOR = "minor"        # UI/cosmetic issues


class Environment(Enum):
    """Test environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ITestManager(ABC):
    """Interface for test execution management"""
    
    @abstractmethod
    def execute_test_suite(self, suite_name: str, environment: Environment) -> Dict[str, Any]:
        """Execute a complete test suite in specified environment"""
        pass
    
    @abstractmethod
    def schedule_tests(self, schedule_config: Dict[str, Any]) -> bool:
        """Schedule automated test execution"""
        pass
    
    @abstractmethod
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Retrieve test execution results"""
        pass
    
    @abstractmethod
    def generate_report(self, report_type: str, filters: Dict[str, Any]) -> str:
        """Generate test execution report"""
        pass


class IDataManager(ABC):
    """Interface for test data management"""
    
    @abstractmethod
    def setup_test_data(self, environment: Environment) -> bool:
        """Setup test data for specified environment"""
        pass
    
    @abstractmethod
    def cleanup_test_data(self, test_id: str) -> bool:
        """Clean up test data after execution"""
        pass
    
    @abstractmethod
    def create_test_user(self, user_type: UserRole) -> Dict[str, Any]:
        """Create test user account"""
        pass
    
    @abstractmethod
    def generate_test_products(self, category: str, count: int) -> List[Dict[str, Any]]:
        """Generate test product data"""
        pass


class IReportGenerator(ABC):
    """Interface for test report generation"""
    
    @abstractmethod
    def generate_execution_report(self, test_run_id: str) -> str:
        """Generate detailed test execution report"""
        pass
    
    @abstractmethod
    def create_coverage_report(self, module_filter: Optional[TestModule] = None) -> str:
        """Generate test coverage report"""
        pass
    
    @abstractmethod
    def export_report(self, report_data: Dict[str, Any], format_type: str, destination: str) -> bool:
        """Export report in specified format"""
        pass
    
    @abstractmethod
    def schedule_reporting(self, schedule_config: Dict[str, Any]) -> bool:
        """Schedule automated report generation"""
        pass


class IEnvironmentManager(ABC):
    """Interface for environment management"""
    
    @abstractmethod
    def switch_environment(self, env_name: Environment) -> bool:
        """Switch to specified test environment"""
        pass
    
    @abstractmethod
    def validate_environment(self, env_config: Dict[str, Any]) -> bool:
        """Validate environment configuration"""
        pass
    
    @abstractmethod
    def setup_payment_sandbox(self, gateway_type: str) -> bool:
        """Setup payment gateway sandbox environment"""
        pass
    
    @abstractmethod
    def configure_notification_services(self) -> bool:
        """Configure notification services for testing"""
        pass


class IBugTracker(ABC):
    """Interface for bug tracking and defect management"""
    
    @abstractmethod
    def log_defect(self, test_case: str, severity: Severity, details: Dict[str, Any]) -> str:
        """Log a new defect"""
        pass
    
    @abstractmethod
    def update_defect_status(self, defect_id: str, status: str) -> bool:
        """Update defect status"""
        pass
    
    @abstractmethod
    def categorize_issue(self, defect_details: Dict[str, Any]) -> str:
        """Categorize defect based on details"""
        pass
    
    @abstractmethod
    def generate_defect_summary(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate defect summary report"""
        pass


class IErrorHandler(ABC):
    """Interface for error handling"""
    
    @abstractmethod
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle test execution errors"""
        pass
    
    @abstractmethod
    def capture_screenshot(self, context: Dict[str, Any]) -> str:
        """Capture screenshot for UI test failures"""
        pass
    
    @abstractmethod
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error details"""
        pass
    
    @abstractmethod
    def determine_continuation_strategy(self, error: Exception) -> str:
        """Determine whether to continue or halt test execution"""
        pass