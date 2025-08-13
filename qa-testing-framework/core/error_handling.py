"""
Error Handling Utilities for QA Testing Framework

Provides comprehensive error handling, classification, and recovery mechanisms
for test execution across all testing modules.
"""

import traceback
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from .interfaces import IErrorHandler, Severity, TestModule
from .logging_utils import get_logger


class TestExecutionError(Exception):
    """Base exception for test execution errors"""
    
    def __init__(self, message: str, severity: Severity, context: Dict[str, Any] = None):
        super().__init__(message)
        self.severity = severity
        self.context = context or {}
        self.timestamp = datetime.now()


class CriticalTestError(TestExecutionError):
    """Critical error that should halt test execution"""
    
    def __init__(self, message: str, context: Dict[str, Any] = None):
        super().__init__(message, Severity.CRITICAL, context)


class MajorTestError(TestExecutionError):
    """Major error that affects functionality but allows continuation"""
    
    def __init__(self, message: str, context: Dict[str, Any] = None):
        super().__init__(message, Severity.MAJOR, context)


class MinorTestError(TestExecutionError):
    """Minor error that doesn't significantly impact testing"""
    
    def __init__(self, message: str, context: Dict[str, Any] = None):
        super().__init__(message, Severity.MINOR, context)


class ErrorHandler(IErrorHandler):
    """Comprehensive error handler for test execution"""
    
    def __init__(self, module: TestModule, screenshot_dir: str = "screenshots"):
        self.module = module
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("error_handler", module)
        self.retry_config = {
            'max_retries': 3,
            'retry_delay': 2,
            'exponential_backoff': True
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle test execution errors with appropriate response"""
        severity = self._classify_error(error, context)
        error_id = self._generate_error_id(context)
        
        # Log the error
        self.log_error(error, context)
        
        # Capture screenshot for UI-related errors
        screenshot_path = None
        if context.get('test_type') in ['web', 'mobile'] and context.get('driver'):
            screenshot_path = self.capture_screenshot(context)
        
        # Determine continuation strategy
        continuation_strategy = self.determine_continuation_strategy(error)
        
        # Create error report
        error_report = {
            'error_id': error_id,
            'severity': severity.value,
            'error_type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'screenshot_path': screenshot_path,
            'continuation_strategy': continuation_strategy,
            'stack_trace': traceback.format_exc()
        }
        
        # Handle based on severity
        if severity == Severity.CRITICAL:
            self._handle_critical_error(error, error_report)
        elif severity == Severity.MAJOR:
            self._handle_major_error(error, error_report)
        else:
            self._handle_minor_error(error, error_report)
        
        return error_report
    
    def capture_screenshot(self, context: Dict[str, Any]) -> str:
        """Capture screenshot for UI test failures"""
        try:
            driver = context.get('driver')
            if not driver:
                return ""
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_case_id = context.get('test_case_id', 'unknown')
            filename = f"{test_case_id}_{timestamp}.png"
            screenshot_path = self.screenshot_dir / filename
            
            driver.save_screenshot(str(screenshot_path))
            self.logger.test_step(
                test_case_id, 
                "screenshot_capture", 
                f"Screenshot saved: {screenshot_path}"
            )
            
            return str(screenshot_path)
            
        except Exception as e:
            self.logger.error(
                context.get('test_case_id', 'unknown'),
                e,
                Severity.MINOR,
                action="screenshot_capture"
            )
            return ""
    
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error details with context"""
        severity = self._classify_error(error, context)
        test_case_id = context.get('test_case_id', 'unknown')
        
        self.logger.error(
            test_case_id,
            error,
            severity,
            **context
        )
    
    def determine_continuation_strategy(self, error: Exception) -> str:
        """Determine whether to continue or halt test execution"""
        if isinstance(error, CriticalTestError):
            return "halt_execution"
        elif isinstance(error, MajorTestError):
            return "continue_with_logging"
        elif isinstance(error, MinorTestError):
            return "continue_normally"
        else:
            # Classify unknown errors
            severity = self._classify_error(error, {})
            if severity == Severity.CRITICAL:
                return "halt_execution"
            elif severity == Severity.MAJOR:
                return "continue_with_logging"
            else:
                return "continue_normally"
    
    def _classify_error(self, error: Exception, context: Dict[str, Any]) -> Severity:
        """Classify error severity based on type and context"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Critical errors
        critical_indicators = [
            'security', 'authentication', 'authorization', 'payment',
            'database connection', 'system crash', 'memory error',
            'permission denied', 'access denied'
        ]
        
        if any(indicator in error_message for indicator in critical_indicators):
            return Severity.CRITICAL
        
        if error_type in ['SystemExit', 'KeyboardInterrupt', 'MemoryError', 'OSError']:
            return Severity.CRITICAL
        
        # Major errors
        major_indicators = [
            'timeout', 'connection', 'not found', 'invalid response',
            'assertion', 'validation', 'element not found'
        ]
        
        if any(indicator in error_message for indicator in major_indicators):
            return Severity.MAJOR
        
        if error_type in ['TimeoutError', 'ConnectionError', 'AssertionError', 'ValueError']:
            return Severity.MAJOR
        
        # Default to minor for UI/cosmetic issues
        return Severity.MINOR
    
    def _generate_error_id(self, context: Dict[str, Any]) -> str:
        """Generate unique error ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        test_case_id = context.get('test_case_id', 'unknown')
        return f"ERR_{self.module.value}_{test_case_id}_{timestamp}"
    
    def _handle_critical_error(self, error: Exception, error_report: Dict[str, Any]) -> None:
        """Handle critical errors that require immediate attention"""
        self.logger.logger.critical(f"CRITICAL ERROR: {error_report['error_id']} - {str(error)}")
        # Could integrate with alerting systems here
    
    def _handle_major_error(self, error: Exception, error_report: Dict[str, Any]) -> None:
        """Handle major errors that affect functionality"""
        self.logger.logger.error(f"MAJOR ERROR: {error_report['error_id']} - {str(error)}")
    
    def _handle_minor_error(self, error: Exception, error_report: Dict[str, Any]) -> None:
        """Handle minor errors that don't significantly impact testing"""
        self.logger.logger.warning(f"MINOR ERROR: {error_report['error_id']} - {str(error)}")


class RetryHandler:
    """Handles retry logic for transient failures"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, exponential_backoff: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.exponential_backoff = exponential_backoff
    
    def retry_on_failure(self, func: Callable, *args, **kwargs) -> Any:
        """Retry function execution on failure"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
                else:
                    break
        
        # All retries failed
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        if self.exponential_backoff:
            return self.base_delay * (2 ** attempt)
        else:
            return self.base_delay


class ErrorRecovery:
    """Handles error recovery and state restoration"""
    
    def __init__(self, module: TestModule):
        self.module = module
        self.logger = get_logger("error_recovery", module)
        self.recovery_strategies = {
            'web': self._recover_web_test,
            'mobile': self._recover_mobile_test,
            'api': self._recover_api_test,
            'database': self._recover_database_test
        }
    
    def recover_from_error(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Attempt to recover from error and continue testing"""
        test_type = context.get('test_type', self.module.value)
        recovery_func = self.recovery_strategies.get(test_type)
        
        if recovery_func:
            try:
                return recovery_func(error, context)
            except Exception as recovery_error:
                self.logger.error(
                    context.get('test_case_id', 'unknown'),
                    recovery_error,
                    Severity.MAJOR,
                    action="error_recovery"
                )
                return False
        
        return False
    
    def _recover_web_test(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Recover from web test errors"""
        driver = context.get('driver')
        if not driver:
            return False
        
        try:
            # Refresh page and try to continue
            driver.refresh()
            time.sleep(2)
            return True
        except:
            return False
    
    def _recover_mobile_test(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Recover from mobile test errors"""
        driver = context.get('driver')
        if not driver:
            return False
        
        try:
            # Reset app state
            driver.reset()
            time.sleep(3)
            return True
        except:
            return False
    
    def _recover_api_test(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Recover from API test errors"""
        # For API tests, recovery might involve re-authentication
        try:
            # Could implement token refresh logic here
            return True
        except:
            return False
    
    def _recover_database_test(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Recover from database test errors"""
        try:
            # Could implement connection reset logic here
            return True
        except:
            return False


def handle_test_error(error: Exception, context: Dict[str, Any], module: TestModule) -> Dict[str, Any]:
    """Convenience function for error handling"""
    error_handler = ErrorHandler(module)
    return error_handler.handle_error(error, context)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying functions on failure"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry_handler = RetryHandler(max_retries, delay)
            return retry_handler.retry_on_failure(func, *args, **kwargs)
        return wrapper
    return decorator