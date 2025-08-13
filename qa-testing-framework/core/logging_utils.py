"""
Logging Utilities for QA Testing Framework

Provides centralized logging configuration and utilities for test execution,
error tracking, and debugging across all testing modules.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from .config import get_value
from .interfaces import TestModule, Severity


class TestLogger:
    """Enhanced logger for test execution with structured logging"""
    
    def __init__(self, name: str, module: TestModule, log_dir: str = "logs"):
        self.name = name
        self.module = module
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"qa_framework.{module.value}.{name}")
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup logger with appropriate handlers and formatters"""
        if self.logger.handlers:
            return  # Already configured
        
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for detailed logs
        log_file = self.log_dir / f"{self.module.value}_{self.name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # JSON handler for structured logs
        json_log_file = self.log_dir / f"{self.module.value}_{self.name}_structured.log"
        json_handler = logging.FileHandler(json_log_file)
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(json_handler)
    
    def test_start(self, test_case_id: str, test_name: str, **kwargs) -> None:
        """Log test case start"""
        self.logger.info(
            "Test started",
            extra={
                'event_type': 'test_start',
                'test_case_id': test_case_id,
                'test_name': test_name,
                'module': self.module.value,
                **kwargs
            }
        )
    
    def test_end(self, test_case_id: str, status: str, duration: float, **kwargs) -> None:
        """Log test case end"""
        self.logger.info(
            f"Test completed with status: {status}",
            extra={
                'event_type': 'test_end',
                'test_case_id': test_case_id,
                'status': status,
                'duration': duration,
                'module': self.module.value,
                **kwargs
            }
        )
    
    def test_step(self, test_case_id: str, step: str, action: str, **kwargs) -> None:
        """Log test step execution"""
        self.logger.debug(
            f"Test step: {step} - {action}",
            extra={
                'event_type': 'test_step',
                'test_case_id': test_case_id,
                'step': step,
                'action': action,
                'module': self.module.value,
                **kwargs
            }
        )
    
    def error(self, test_case_id: str, error: Exception, severity: Severity, **kwargs) -> None:
        """Log test error with severity"""
        self.logger.error(
            f"Test error: {str(error)}",
            extra={
                'event_type': 'test_error',
                'test_case_id': test_case_id,
                'error_message': str(error),
                'error_type': type(error).__name__,
                'severity': severity.value,
                'module': self.module.value,
                **kwargs
            },
            exc_info=True
        )
    
    def defect(self, test_case_id: str, defect_id: str, severity: Severity, description: str, **kwargs) -> None:
        """Log defect information"""
        self.logger.warning(
            f"Defect logged: {defect_id}",
            extra={
                'event_type': 'defect',
                'test_case_id': test_case_id,
                'defect_id': defect_id,
                'severity': severity.value,
                'description': description,
                'module': self.module.value,
                **kwargs
            }
        )
    
    def performance(self, test_case_id: str, metric_name: str, value: float, unit: str, **kwargs) -> None:
        """Log performance metrics"""
        self.logger.info(
            f"Performance metric: {metric_name} = {value} {unit}",
            extra={
                'event_type': 'performance',
                'test_case_id': test_case_id,
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                'module': self.module.value,
                **kwargs
            }
        )


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': getattr(record, 'module', 'unknown'),
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class LogManager:
    """Manages loggers for different test modules"""
    
    def __init__(self):
        self._loggers: Dict[str, TestLogger] = {}
        self._setup_root_logger()
    
    def _setup_root_logger(self) -> None:
        """Setup root logger configuration"""
        logging.basicConfig(
            level=logging.WARNING,  # Only show warnings and errors from other libraries
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Suppress noisy third-party loggers
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
    def get_logger(self, name: str, module: TestModule) -> TestLogger:
        """Get or create logger for specific test component"""
        logger_key = f"{module.value}.{name}"
        
        if logger_key not in self._loggers:
            self._loggers[logger_key] = TestLogger(name, module)
        
        return self._loggers[logger_key]
    
    def get_execution_logger(self, test_run_id: str) -> TestLogger:
        """Get logger for test execution tracking"""
        return self.get_logger(f"execution_{test_run_id}", TestModule.INTEGRATION)
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """Clean up old log files"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                except OSError:
                    pass  # File might be in use


# Global log manager instance
log_manager = LogManager()


def get_logger(name: str, module: TestModule) -> TestLogger:
    """Convenience function to get a logger"""
    return log_manager.get_logger(name, module)