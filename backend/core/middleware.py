"""
Custom middleware for the ecommerce platform.
"""
import logging
import time
import uuid
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests and responses.
    """
    
    def process_request(self, request):
        """
        Process incoming request and add request ID for tracking.
        """
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())
        
        logger.info(
            f"Request started - ID: {request.request_id}, "
            f"Method: {request.method}, Path: {request.path}, "
            f"User: {getattr(request.user, 'id', 'Anonymous')}"
        )
        
    def process_response(self, request, response):
        """
        Process response and log request completion.
        """
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            logger.info(
                f"Request completed - ID: {getattr(request, 'request_id', 'Unknown')}, "
                f"Status: {response.status_code}, Duration: {duration:.3f}s"
            )
            
        return response