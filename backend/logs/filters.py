"""
Custom log filters for the ecommerce platform.
"""
import logging
import re
from django.conf import settings


class RequireDebugTrue(logging.Filter):
    """
    Filter that only allows records when DEBUG=True.
    """
    def filter(self, record):
        return settings.DEBUG


class RequireDebugFalse(logging.Filter):
    """
    Filter that only allows records when DEBUG=False.
    """
    def filter(self, record):
        return not settings.DEBUG


class IgnoreHealthChecks(logging.Filter):
    """
    Filter that ignores health check endpoints to reduce log noise.
    """
    def filter(self, record):
        if hasattr(record, 'request_path'):
            return not record.request_path.startswith('/api/health')
        return True


class SensitiveDataFilter(logging.Filter):
    """
    Filter that masks sensitive data in log messages.
    """
    SENSITIVE_FIELDS = [
        'password', 'token', 'secret', 'credit_card', 'card_number', 
        'cvv', 'cvc', 'expiry', 'ssn', 'social_security', 'auth',
        'authorization', 'api_key', 'apikey', 'access_key', 'secret_key'
    ]
    
    def __init__(self, name=''):
        super().__init__(name)
        self.patterns = [
            (re.compile(fr'({field}[\'"]\s*:\s*[\'"])[^\'"]+([\'"]\s*)', re.IGNORECASE), r'\1*****\2')
            for field in self.SENSITIVE_FIELDS
        ]
        
        # Add patterns for common sensitive data formats
        # Credit card pattern
        self.patterns.append(
            (re.compile(r'\b(\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?)\d{4}\b'), r'\1****')
        )
        # JWT pattern
        self.patterns.append(
            (re.compile(r'(eyJ[a-zA-Z0-9_-]{5,})\.[a-zA-Z0-9_-]{5,}\.[a-zA-Z0-9_-]{5,}'), r'\1.******.******')
        )
    
    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern, replacement in self.patterns:
                record.msg = pattern.sub(replacement, record.msg)
        
        # Also check for sensitive data in extra attributes
        for attr in dir(record):
            if attr.startswith('__') or attr in ('msg', 'args', 'exc_info', 'exc_text'):
                continue
            
            value = getattr(record, attr)
            if isinstance(value, str):
                for pattern, replacement in self.patterns:
                    setattr(record, attr, pattern.sub(replacement, value))
        
        return True


class RateLimitFilter(logging.Filter):
    """
    Filter that rate limits log messages to prevent log flooding.
    """
    def __init__(self, name='', rate=100, per=60, burst=200):
        super().__init__(name)
        self.rate = rate  # Max logs per time period
        self.per = per    # Time period in seconds
        self.burst = burst  # Max burst of logs
        self.allowance = rate  # Current allowance
        self.last_check = 0  # Last check timestamp
        self.dropped_count = 0  # Count of dropped messages
    
    def filter(self, record):
        import time
        current = time.time()
        
        # Calculate time passed
        time_passed = current - self.last_check
        self.last_check = current
        
        # Update allowance
        self.allowance += time_passed * (self.rate / self.per)
        
        # Cap allowance at burst limit
        if self.allowance > self.burst:
            self.allowance = self.burst
        
        # Check if we should allow this message
        if self.allowance < 1.0:
            self.dropped_count += 1
            return False
        
        # Consume allowance
        self.allowance -= 1.0
        
        # If we've dropped messages, add a note about it
        if self.dropped_count > 0:
            record.dropped_messages = self.dropped_count
            self.dropped_count = 0
        
        return True


class EnvironmentFilter(logging.Filter):
    """
    Filter that adds environment information to log records.
    """
    def __init__(self, name='', environment=None):
        super().__init__(name)
        self.environment = environment or getattr(settings, 'ENVIRONMENT', 'development')
    
    def filter(self, record):
        record.environment = self.environment
        return True


class UserFilter(logging.Filter):
    """
    Filter that adds user information to log records from request.
    """
    def filter(self, record):
        if hasattr(record, 'request'):
            request = record.request
            if hasattr(request, 'user') and request.user.is_authenticated:
                record.user_id = request.user.id
                record.username = request.user.username
            else:
                record.user_id = None
                record.username = 'anonymous'
        return True