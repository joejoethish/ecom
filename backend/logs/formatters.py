"""
Custom log formatters for the ecommerce platform.
"""
import logging
import json
from datetime import datetime
from django.utils import timezone


class VerboseFormatter(logging.Formatter):
    """
    Detailed formatter with timestamp, level, module, process, thread, and message.
    """
    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        return super().format(record)


class SimpleFormatter(logging.Formatter):
    """
    Simple formatter with just level and message.
    """
    def format(self, record):
        return super().format(record)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Formatter that adds colors to console output based on log level.
    """
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',   # Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',  # Red
        'CRITICAL': '\033[1;91m', # Bold Red
        'RESET': '\033[0m'    # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS:
            return f"{self.COLORS[record.levelname]}{log_message}{self.COLORS['RESET']}"
        return log_message


class StructuredFormatter(logging.Formatter):
    """
    Formatter that outputs structured log entries with consistent fields.
    """
    def format(self, record):
        # Basic log structure
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add source location
        log_data.update({
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        })
        
        # Add process and thread info
        log_data.update({
            'process': record.process,
            'process_name': record.processName,
            'thread': record.thread,
            'thread_name': record.threadName,
        })
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info),
            }
        
        # Add any extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_') and key not in [
                'args', 'exc_info', 'exc_text', 'stack_info', 'created', 
                'msecs', 'relativeCreated', 'levelno', 'pathname', 'filename'
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)


class SecurityFormatter(logging.Formatter):
    """
    Formatter specifically for security events with additional context.
    """
    def format(self, record):
        # Start with basic log structure
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'level': record.levelname,
            'event_type': getattr(record, 'event_type', 'security_event'),
            'message': record.getMessage(),
        }
        
        # Add security-specific fields
        security_fields = [
            'user_id', 'username', 'ip_address', 'request_path', 
            'request_method', 'status_code', 'user_agent'
        ]
        
        for field in security_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add any additional context
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class BusinessMetricsFormatter(logging.Formatter):
    """
    Formatter for business metrics with timestamp and metric values.
    """
    def format(self, record):
        # Basic metric structure
        metric_data = {
            'timestamp': timezone.now().isoformat(),
            'metric_name': getattr(record, 'metric_name', 'unknown_metric'),
            'metric_value': getattr(record, 'metric_value', 0),
        }
        
        # Add dimensions for the metric
        if hasattr(record, 'dimensions') and isinstance(record.dimensions, dict):
            metric_data['dimensions'] = record.dimensions
        
        # Add any additional context
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            metric_data.update(record.extra_data)
        
        return json.dumps(metric_data)