import json
import time
import hashlib
import secrets
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db.models import Avg, Count, Q, Sum
from django.core.cache import cache
from django.conf import settings
from .models import (
    APIVersion, APIKey, APIEndpoint, APIUsageLog, APIRateLimit,
    APIWebhook, APIWebhookDelivery, APIMockService, APIDocumentation,
    APIPerformanceMetric
)


class APIKeyService:
    """Service for API key management"""
    
    @staticmethod
    def generate_api_key() -> tuple:
        """Generate API key and secret"""
        key = secrets.token_urlsafe(32)
        secret = secrets.token_urlsafe(64)
        return key, secret
    
    @staticmethod
    def validate_api_key(key: str, secret: str = None) -> Optional[APIKey]:
        """Validate API key and secret"""
        try:
            api_key = APIKey.objects.get(key=key, status='active')
            
            # Check expiration
            if api_key.expires_at and api_key.expires_at < timezone.now():
                api_key.status = 'expired'
                api_key.save()
                return None
            
            # Update last used
            api_key.last_used_at = timezone.now()
            api_key.save(update_fields=['last_used_at'])
            
            return api_key
        except APIKey.DoesNotExist:
            return None
    
    @staticmethod
    def check_rate_limit(api_key: APIKey, endpoint: APIEndpoint = None) -> bool:
        """Check if API key has exceeded rate limits"""
        now = timezone.now()
        
        # Get or create rate limit record
        rate_limit, created = APIRateLimit.objects.get_or_create(
            api_key=api_key,
            endpoint=endpoint,
            defaults={
                'minute_reset': now + timedelta(minutes=1),
                'hour_reset': now + timedelta(hours=1),
                'day_reset': now + timedelta(days=1),
            }
        )
        
        # Reset counters if needed
        if now >= rate_limit.minute_reset:
            rate_limit.requests_per_minute = 0
            rate_limit.minute_reset = now + timedelta(minutes=1)
        
        if now >= rate_limit.hour_reset:
            rate_limit.requests_per_hour = 0
            rate_limit.hour_reset = now + timedelta(hours=1)
        
        if now >= rate_limit.day_reset:
            rate_limit.requests_per_day = 0
            rate_limit.day_reset = now + timedelta(days=1)
        
        # Check limits
        if rate_limit.requests_per_minute >= api_key.rate_limit_per_minute:
            return False
        if rate_limit.requests_per_hour >= api_key.rate_limit_per_hour:
            return False
        if rate_limit.requests_per_day >= api_key.rate_limit_per_day:
            return False
        
        # Increment counters
        rate_limit.requests_per_minute += 1
        rate_limit.requests_per_hour += 1
        rate_limit.requests_per_day += 1
        rate_limit.save()
        
        return True


class APILoggingService:
    """Service for API usage logging"""
    
    @staticmethod
    def log_request(
        api_key: APIKey,
        endpoint: APIEndpoint,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> APIUsageLog:
        """Log API request and response"""
        
        # Determine status
        status_code = response_data.get('status_code', 500)
        if status_code < 400:
            status = 'success'
        elif status_code == 429:
            status = 'rate_limited'
        elif status_code == 401:
            status = 'unauthorized'
        elif status_code == 403:
            status = 'forbidden'
        elif status_code >= 500:
            status = 'error'
        else:
            status = 'error'
        
        # Create log entry
        log_entry = APIUsageLog.objects.create(
            api_key=api_key,
            endpoint=endpoint,
            request_id=request_data.get('request_id', ''),
            ip_address=request_data.get('ip_address', ''),
            user_agent=request_data.get('user_agent', ''),
            request_headers=request_data.get('headers', {}),
            request_body=request_data.get('body', ''),
            status_code=status_code,
            status=status,
            response_time=response_data.get('response_time', 0),
            response_size=response_data.get('response_size', 0),
            error_message=response_data.get('error_message', ''),
        )
        
        # Update performance metrics asynchronously
        APIMetricsService.update_metrics(endpoint, log_entry)
        
        return log_entry


class APIMetricsService:
    """Service for API performance metrics"""
    
    @staticmethod
    def update_metrics(endpoint: APIEndpoint, log_entry: APIUsageLog):
        """Update performance metrics for an endpoint"""
        date = log_entry.timestamp.date()
        hour = log_entry.timestamp.hour
        
        # Update hourly metrics
        metric, created = APIPerformanceMetric.objects.get_or_create(
            endpoint=endpoint,
            date=date,
            hour=hour,
            defaults={
                'request_count': 0,
                'avg_response_time': 0.0,
                'min_response_time': float('inf'),
                'max_response_time': 0.0,
                'error_count': 0,
                'error_rate': 0.0,
            }
        )
        
        # Update counters
        metric.request_count += 1
        
        # Update response time stats
        if created:
            metric.avg_response_time = log_entry.response_time
            metric.min_response_time = log_entry.response_time
            metric.max_response_time = log_entry.response_time
        else:
            # Calculate new average
            total_time = metric.avg_response_time * (metric.request_count - 1)
            metric.avg_response_time = (total_time + log_entry.response_time) / metric.request_count
            
            # Update min/max
            metric.min_response_time = min(metric.min_response_time, log_entry.response_time)
            metric.max_response_time = max(metric.max_response_time, log_entry.response_time)
        
        # Update error stats
        if log_entry.status == 'error':
            metric.error_count += 1
        
        metric.error_rate = (metric.error_count / metric.request_count) * 100
        
        # Update status code counters
        status_code = log_entry.status_code
        if 200 <= status_code < 300:
            metric.status_2xx += 1
        elif 300 <= status_code < 400:
            metric.status_3xx += 1
        elif 400 <= status_code < 500:
            metric.status_4xx += 1
        elif 500 <= status_code < 600:
            metric.status_5xx += 1
        
        metric.save()
        
        # Also update daily metrics (hour=None)
        daily_metric, created = APIPerformanceMetric.objects.get_or_create(
            endpoint=endpoint,
            date=date,
            hour=None,
            defaults={
                'request_count': 0,
                'avg_response_time': 0.0,
                'min_response_time': float('inf'),
                'max_response_time': 0.0,
                'error_count': 0,
                'error_rate': 0.0,
            }
        )
        
        # Update daily metrics similar to hourly
        daily_metric.request_count += 1
        
        if created:
            daily_metric.avg_response_time = log_entry.response_time
            daily_metric.min_response_time = log_entry.response_time
            daily_metric.max_response_time = log_entry.response_time
        else:
            total_time = daily_metric.avg_response_time * (daily_metric.request_count - 1)
            daily_metric.avg_response_time = (total_time + log_entry.response_time) / daily_metric.request_count
            daily_metric.min_response_time = min(daily_metric.min_response_time, log_entry.response_time)
            daily_metric.max_response_time = max(daily_metric.max_response_time, log_entry.response_time)
        
        if log_entry.status == 'error':
            daily_metric.error_count += 1
        
        daily_metric.error_rate = (daily_metric.error_count / daily_metric.request_count) * 100
        
        if 200 <= status_code < 300:
            daily_metric.status_2xx += 1
        elif 300 <= status_code < 400:
            daily_metric.status_3xx += 1
        elif 400 <= status_code < 500:
            daily_metric.status_4xx += 1
        elif 500 <= status_code < 600:
            daily_metric.status_5xx += 1
        
        daily_metric.save()
    
    @staticmethod
    def get_analytics_data(days: int = 7) -> Dict[str, Any]:
        """Get comprehensive analytics data"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get usage logs for the period
        logs = APIUsageLog.objects.filter(
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        )
        
        total_requests = logs.count()
        total_errors = logs.filter(status='error').count()
        avg_response_time = logs.aggregate(avg=Avg('response_time'))['avg'] or 0
        error_rate = (total_errors / max(total_requests, 1)) * 100
        
        # Top endpoints
        top_endpoints = (
            logs.values('endpoint__path', 'endpoint__method')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Top API keys
        top_api_keys = (
            logs.filter(api_key__isnull=False)
            .values('api_key__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Hourly stats for last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)
        hourly_logs = logs.filter(timestamp__gte=last_24h)
        
        hourly_stats = []
        for hour in range(24):
            hour_start = last_24h + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            hour_logs = hourly_logs.filter(
                timestamp__gte=hour_start,
                timestamp__lt=hour_end
            )
            
            hourly_stats.append({
                'hour': hour_start.strftime('%H:00'),
                'requests': hour_logs.count(),
                'errors': hour_logs.filter(status='error').count(),
                'avg_response_time': hour_logs.aggregate(avg=Avg('response_time'))['avg'] or 0,
            })
        
        # Daily stats
        daily_stats = []
        for day in range(days):
            day_date = start_date + timedelta(days=day)
            day_logs = logs.filter(timestamp__date=day_date)
            
            daily_stats.append({
                'date': day_date.isoformat(),
                'requests': day_logs.count(),
                'errors': day_logs.filter(status='error').count(),
                'avg_response_time': day_logs.aggregate(avg=Avg('response_time'))['avg'] or 0,
            })
        
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'avg_response_time': avg_response_time,
            'error_rate': error_rate,
            'top_endpoints': list(top_endpoints),
            'top_api_keys': list(top_api_keys),
            'hourly_stats': hourly_stats,
            'daily_stats': daily_stats,
        }


class APIWebhookService:
    """Service for webhook management"""
    
    @staticmethod
    def trigger_webhook(event_type: str, payload: Dict[str, Any]):
        """Trigger webhooks for a specific event"""
        webhooks = APIWebhook.objects.filter(
            is_active=True,
            events__contains=[event_type]
        )
        
        for webhook in webhooks:
            APIWebhookService.deliver_webhook(webhook, event_type, payload)
    
    @staticmethod
    def deliver_webhook(webhook: APIWebhook, event_type: str, payload: Dict[str, Any]):
        """Deliver a webhook"""
        delivery = APIWebhookDelivery.objects.create(
            webhook=webhook,
            event_type=event_type,
            payload=payload,
            status='pending'
        )
        
        try:
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'API-Management-Webhook/1.0',
            }
            
            # Add signature if secret is configured
            if webhook.secret:
                signature = APIWebhookService.generate_signature(
                    webhook.secret,
                    json.dumps(payload)
                )
                headers['X-Webhook-Signature'] = signature
            
            # Make request
            response = requests.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=webhook.timeout
            )
            
            # Update delivery record
            delivery.status = 'success' if response.status_code < 400 else 'failed'
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limit size
            delivery.attempts += 1
            delivery.delivered_at = timezone.now()
            
        except Exception as e:
            delivery.status = 'failed'
            delivery.error_message = str(e)
            delivery.attempts += 1
            
            # Schedule retry if attempts < retry_count
            if delivery.attempts < webhook.retry_count:
                delivery.status = 'retrying'
                delivery.next_retry = timezone.now() + timedelta(
                    minutes=2 ** delivery.attempts  # Exponential backoff
                )
        
        delivery.save()
        
        # Update webhook last triggered
        webhook.last_triggered = timezone.now()
        webhook.save(update_fields=['last_triggered'])
    
    @staticmethod
    def generate_signature(secret: str, payload: str) -> str:
        """Generate webhook signature"""
        return hashlib.sha256(
            (secret + payload).encode('utf-8')
        ).hexdigest()


class APIMockService:
    """Service for API mocking"""
    
    @staticmethod
    def get_mock_response(endpoint: APIEndpoint, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get mock response for an endpoint"""
        mocks = APIMockService.objects.filter(
            endpoint=endpoint,
            is_active=True
        )
        
        for mock in mocks:
            if APIMockService.matches_conditions(mock, request_data):
                # Add delay if configured
                if mock.delay > 0:
                    time.sleep(mock.delay / 1000)  # Convert to seconds
                
                return {
                    'status_code': mock.response_code,
                    'body': mock.response_body,
                    'headers': mock.response_headers,
                }
        
        return None
    
    @staticmethod
    def matches_conditions(mock: APIMockService, request_data: Dict[str, Any]) -> bool:
        """Check if request matches mock conditions"""
        if not mock.conditions:
            return True
        
        # Check query parameters
        if 'query_params' in mock.conditions:
            request_params = request_data.get('query_params', {})
            for key, value in mock.conditions['query_params'].items():
                if request_params.get(key) != value:
                    return False
        
        # Check headers
        if 'headers' in mock.conditions:
            request_headers = request_data.get('headers', {})
            for key, value in mock.conditions['headers'].items():
                if request_headers.get(key) != value:
                    return False
        
        # Check body content
        if 'body_contains' in mock.conditions:
            request_body = request_data.get('body', '')
            if mock.conditions['body_contains'] not in request_body:
                return False
        
        return True


class APIVersioningService:
    """Service for API versioning"""
    
    @staticmethod
    def get_version_from_request(request) -> str:
        """Extract API version from request"""
        # Check header
        version = request.META.get('HTTP_API_VERSION')
        if version:
            return version
        
        # Check query parameter
        version = request.GET.get('version')
        if version:
            return version
        
        # Check URL path
        path_parts = request.path.split('/')
        for part in path_parts:
            if part.startswith('v') and part[1:].isdigit():
                return part[1:]
        
        # Default to latest
        latest_version = APIVersion.objects.filter(is_active=True).first()
        return latest_version.version if latest_version else '1.0'
    
    @staticmethod
    def is_version_supported(version: str) -> bool:
        """Check if API version is supported"""
        return APIVersion.objects.filter(
            version=version,
            is_active=True
        ).exists()
    
    @staticmethod
    def get_deprecated_versions() -> List[str]:
        """Get list of deprecated versions"""
        return list(
            APIVersion.objects.filter(is_deprecated=True)
            .values_list('version', flat=True)
        )


class APISecurityService:
    """Service for API security"""
    
    @staticmethod
    def validate_ip_whitelist(api_key: APIKey, ip_address: str) -> bool:
        """Validate IP address against whitelist"""
        if not api_key.ip_whitelist:
            return True
        
        return ip_address in api_key.ip_whitelist
    
    @staticmethod
    def detect_suspicious_activity(api_key: APIKey) -> bool:
        """Detect suspicious API activity"""
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        
        # Get recent requests
        recent_requests = APIUsageLog.objects.filter(
            api_key=api_key,
            timestamp__gte=last_hour
        )
        
        # Check for unusual patterns
        request_count = recent_requests.count()
        error_count = recent_requests.filter(status='error').count()
        
        # High request volume
        if request_count > api_key.rate_limit_per_hour * 0.8:
            return True
        
        # High error rate
        if request_count > 0 and (error_count / request_count) > 0.5:
            return True
        
        # Multiple IP addresses
        ip_count = recent_requests.values('ip_address').distinct().count()
        if ip_count > 10:
            return True
        
        return False
    
    @staticmethod
    def generate_api_token(api_key: APIKey, expires_in: int = 3600) -> str:
        """Generate temporary API token"""
        import jwt
        
        payload = {
            'api_key_id': str(api_key.id),
            'exp': timezone.now().timestamp() + expires_in,
            'iat': timezone.now().timestamp(),
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    @staticmethod
    def validate_api_token(token: str) -> Optional[APIKey]:
        """Validate API token"""
        import jwt
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            api_key_id = payload.get('api_key_id')
            
            return APIKey.objects.get(id=api_key_id, status='active')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, APIKey.DoesNotExist):
            return None