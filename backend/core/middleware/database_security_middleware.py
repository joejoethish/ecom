"""
Database Security Middleware

This middleware integrates database security monitoring with Django requests:
- Monitors database queries for security threats
- Logs database access attempts
- Handles failed authentication attempts
- Provides security context for requests

Requirements: 4.1, 4.2, 4.4, 4.5, 4.6
"""

import logging
import hashlib
from typing import Callable, Optional
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.conf import settings
from core.database_security import database_security_manager, AuditEventType
import time


logger = logging.getLogger(__name__)
User = get_user_model()


class DatabaseSecurityMiddleware(MiddlewareMixin):
    """Middleware for database security monitoring and threat detection."""
    
    def __init__(self, get_response: Callable):
        """Initialize the middleware."""
        self.get_response = get_response
        self.enabled = getattr(settings, 'DB_SECURITY_MIDDLEWARE_ENABLED', True)
        self.log_all_queries = getattr(settings, 'DB_SECURITY_LOG_ALL_QUERIES', False)
        self.threat_detection_enabled = getattr(settings, 'DB_THREAT_DETECTION_ENABLED', True)
        super().__init__(get_response)
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request through security middleware."""
        if not self.enabled:
            return self.get_response(request)
        
        # Add security context to request
        request.db_security_context = {
            'start_time': time.time(),
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'source_ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'path': request.path,
            'method': request.method,
            'queries_executed': [],
            'threats_detected': []
        }
        
        # Check if user account is locked
        if hasattr(request, 'user') and request.user.is_authenticated:
            if database_security_manager.is_account_locked(str(request.user)):
                return JsonResponse(
                    {'error': 'Account temporarily locked due to security concerns'},
                    status=423  # Locked
                )
        
        # Monitor database queries during request processing
        if self.threat_detection_enabled:
            self._start_query_monitoring(request)
        
        response = self.get_response(request)
        
        # Log request completion and any security events
        self._log_request_completion(request, response)
        
        return response
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _start_query_monitoring(self, request: HttpRequest):
        """Start monitoring database queries for the request."""
        # Store original execute method
        original_execute = connection.cursor().execute
        
        def monitored_execute(cursor, sql, params=None):
            """Monitor database query execution."""
            query_start_time = time.time()
            
            try:
                # Execute the query
                result = original_execute(sql, params)
                query_success = True
                error_message = None
            except Exception as e:
                query_success = False
                error_message = str(e)
                raise
            finally:
                query_end_time = time.time()
                query_duration = query_end_time - query_start_time
                
                # Analyze query for security threats
                if self.threat_detection_enabled:
                    threats_detected, threat_details = database_security_manager.detect_threats(
                        sql, 
                        request.db_security_context['user'],
                        request.db_security_context['source_ip']
                    )
                    
                    if threats_detected:
                        request.db_security_context['threats_detected'].extend(threat_details)
                        logger.warning(
                            f"Security threats detected in query from {request.db_security_context['user']} "
                            f"at {request.db_security_context['source_ip']}: {threat_details}"
                        )
                
                # Log query execution
                query_info = {
                    'sql_hash': hashlib.sha256(sql.encode()).hexdigest()[:16],
                    'duration': query_duration,
                    'success': query_success,
                    'error': error_message,
                    'threats': threat_details if threats_detected else []
                }
                request.db_security_context['queries_executed'].append(query_info)
                
                # Log to audit system if configured
                if self.log_all_queries or not query_success or threats_detected:
                    database_security_manager.log_audit_event(
                        event_type=AuditEventType.DATA_ACCESS,
                        user=request.db_security_context['user'],
                        source_ip=request.db_security_context['source_ip'],
                        database=connection.settings_dict['NAME'],
                        table='multiple',  # Could be parsed from SQL
                        operation='QUERY',
                        affected_rows=cursor.rowcount if hasattr(cursor, 'rowcount') else 0,
                        query_hash=query_info['sql_hash'],
                        success=query_success,
                        error_message=error_message,
                        additional_data={
                            'duration': query_duration,
                            'path': request.path,
                            'method': request.method,
                            'user_agent': request.db_security_context['user_agent'][:200],
                            'threats': threat_details if threats_detected else None
                        }
                    )
            
            return result
        
        # Replace cursor execute method temporarily
        connection.cursor().execute = monitored_execute
    
    def _log_request_completion(self, request: HttpRequest, response: HttpResponse):
        """Log request completion and security summary."""
        if not hasattr(request, 'db_security_context'):
            return
        
        context = request.db_security_context
        request_duration = time.time() - context['start_time']
        
        # Count queries and threats
        total_queries = len(context['queries_executed'])
        failed_queries = sum(1 for q in context['queries_executed'] if not q['success'])
        total_threats = len(context['threats_detected'])
        
        # Log request summary
        logger.info(
            f"Request completed: {context['method']} {context['path']} "
            f"by {context['user']} from {context['source_ip']} "
            f"in {request_duration:.3f}s with {total_queries} queries "
            f"({failed_queries} failed, {total_threats} threats detected)"
        )
        
        # Log security events if threats were detected
        if total_threats > 0:
            database_security_manager.log_audit_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                user=context['user'],
                source_ip=context['source_ip'],
                database=connection.settings_dict['NAME'],
                table='request',
                operation='HTTP_REQUEST',
                affected_rows=0,
                query_hash=hashlib.sha256(f"{context['method']}_{context['path']}".encode()).hexdigest()[:16],
                success=response.status_code < 400,
                additional_data={
                    'request_duration': request_duration,
                    'total_queries': total_queries,
                    'failed_queries': failed_queries,
                    'threats_detected': context['threats_detected'],
                    'response_status': response.status_code,
                    'user_agent': context['user_agent'][:200]
                }
            )
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """Handle exceptions and log security-related errors."""
        if not hasattr(request, 'db_security_context'):
            return None
        
        context = request.db_security_context
        
        # Log exception with security context
        logger.error(
            f"Request exception: {context['method']} {context['path']} "
            f"by {context['user']} from {context['source_ip']}: {exception}"
        )
        
        # Check if exception might be security-related
        security_related_exceptions = [
            'PermissionDenied',
            'SuspiciousOperation',
            'ValidationError',
            'IntegrityError',
            'OperationalError'
        ]
        
        if any(exc_type in str(type(exception)) for exc_type in security_related_exceptions):
            database_security_manager.log_audit_event(
                event_type=AuditEventType.SECURITY_VIOLATION,
                user=context['user'],
                source_ip=context['source_ip'],
                database=connection.settings_dict['NAME'],
                table='request',
                operation='EXCEPTION',
                affected_rows=0,
                query_hash=hashlib.sha256(f"exception_{context['path']}".encode()).hexdigest()[:16],
                success=False,
                error_message=str(exception),
                additional_data={
                    'exception_type': str(type(exception)),
                    'path': context['path'],
                    'method': context['method'],
                    'user_agent': context['user_agent'][:200]
                }
            )
        
        return None


class AuthenticationSecurityMiddleware(MiddlewareMixin):
    """Middleware for monitoring authentication attempts and security."""
    
    def __init__(self, get_response: Callable):
        """Initialize the authentication security middleware."""
        self.get_response = get_response
        self.enabled = getattr(settings, 'AUTH_SECURITY_MIDDLEWARE_ENABLED', True)
        super().__init__(get_response)
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process authentication security."""
        if not self.enabled:
            return self.get_response(request)
        
        # Monitor authentication endpoints
        auth_endpoints = ['/api/auth/login/', '/api/auth/token/', '/admin/login/']
        
        if any(request.path.startswith(endpoint) for endpoint in auth_endpoints):
            return self._handle_auth_request(request)
        
        return self.get_response(request)
    
    def _handle_auth_request(self, request: HttpRequest) -> HttpResponse:
        """Handle authentication requests with security monitoring."""
        user_identifier = None
        source_ip = self._get_client_ip(request)
        
        # Extract user identifier from request
        if request.method == 'POST':
            if hasattr(request, 'data'):
                user_identifier = request.data.get('username') or request.data.get('email')
            elif request.POST:
                user_identifier = request.POST.get('username') or request.POST.get('email')
        
        # Check if account is locked before processing
        if user_identifier and database_security_manager.is_account_locked(user_identifier):
            logger.warning(f"Login attempt for locked account: {user_identifier} from {source_ip}")
            return JsonResponse(
                {'error': 'Account temporarily locked due to security concerns'},
                status=423
            )
        
        # Process the request
        response = self.get_response(request)
        
        # Monitor authentication result
        if user_identifier:
            auth_success = response.status_code in [200, 201]
            
            # Update failed login attempts tracking
            database_security_manager.monitor_failed_login_attempts(
                user_identifier, source_ip, auth_success
            )
            
            # Log authentication attempt
            if auth_success:
                logger.info(f"Successful authentication: {user_identifier} from {source_ip}")
            else:
                logger.warning(f"Failed authentication: {user_identifier} from {source_ip}")
        
        return response
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip