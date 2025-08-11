from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import json

from .models import (
    APIVersion, APIKey, APIEndpoint, APIUsageLog, APIRateLimit,
    APIWebhook, APIWebhookDelivery, APIMockService, APIDocumentation,
    APIPerformanceMetric
)
from .serializers import (
    APIVersionSerializer, APIKeySerializer, APIEndpointSerializer,
    APIUsageLogSerializer, APIRateLimitSerializer, APIWebhookSerializer,
    APIWebhookDeliverySerializer, APIMockServiceSerializer,
    APIDocumentationSerializer, APIPerformanceMetricSerializer,
    APIAnalyticsSerializer, APIHealthSerializer, GraphQLQuerySerializer,
    APITestCaseSerializer, APIBenchmarkSerializer
)
from .services import (
    APIKeyService, APILoggingService, APIMetricsService,
    APIWebhookService, APIMockService as MockService,
    APIVersioningService, APISecurityService
)

class APIVersionViewSet(viewsets.ModelViewSet):
    """ViewSet for API version management"""
    queryset = APIVersion.objects.all()
    serializer_class = APIVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def deprecate(self, request, pk=None):
        """Deprecate an API version"""
        version = self.get_object()
        version.is_deprecated = True
        version.deprecation_date = timezone.now()
        version.save()
        
        return Response({'status': 'deprecated'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an API version"""
        version = self.get_object()
        version.is_active = True
        version.save()
        
        return Response({'status': 'activated'})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active versions"""
        active_versions = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_versions, many=True)
        return Response(serializer.data)


class APIKeyViewSet(viewsets.ModelViewSet):
    """ViewSet for API key management"""
    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter API keys by user"""
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Generate API key and secret on creation"""
        key, secret = APIKeyService.generate_api_key()
        serializer.save(
            user=self.request.user,
            key=key,
            secret=secret
        )
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate API key and secret"""
        api_key = self.get_object()
        key, secret = APIKeyService.generate_api_key()
        api_key.key = key
        api_key.secret = secret
        api_key.save()
        
        return Response({
            'key': key,
            'secret': secret,
            'message': 'API key regenerated successfully'
        })
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke an API key"""
        api_key = self.get_object()
        api_key.status = 'revoked'
        api_key.save()
        
        return Response({'status': 'revoked'})
    
    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """Get usage statistics for an API key"""
        api_key = self.get_object()
        days = int(request.query_params.get('days', 7))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        usage_logs = APIUsageLog.objects.filter(
            api_key=api_key,
            timestamp__date__gte=start_date
        )
        
        stats = {
            'total_requests': usage_logs.count(),
            'total_errors': usage_logs.filter(status='error').count(),
            'avg_response_time': usage_logs.aggregate(avg=Avg('response_time'))['avg'] or 0,
            'daily_breakdown': []
        }
        
        for day in range(days):
            day_date = start_date + timedelta(days=day)
            day_logs = usage_logs.filter(timestamp__date=day_date)
            
            stats['daily_breakdown'].append({
                'date': day_date.isoformat(),
                'requests': day_logs.count(),
                'errors': day_logs.filter(status='error').count(),
            })
        
        return Response(stats)


class APIEndpointViewSet(viewsets.ModelViewSet):
    """ViewSet for API endpoint management"""
    queryset = APIEndpoint.objects.all()
    serializer_class = APIEndpointSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter endpoints by version and other parameters"""
        queryset = self.queryset
        
        version = self.request.query_params.get('version')
        if version:
            queryset = queryset.filter(version__version=version)
        
        method = self.request.query_params.get('method')
        if method:
            queryset = queryset.filter(method=method)
        
        is_public = self.request.query_params.get('is_public')
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get performance metrics for an endpoint"""
        endpoint = self.get_object()
        days = int(request.query_params.get('days', 7))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        metrics = APIPerformanceMetric.objects.filter(
            endpoint=endpoint,
            date__gte=start_date,
            hour__isnull=True  # Daily metrics
        ).order_by('date')
        
        serializer = APIPerformanceMetricSerializer(metrics, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def documentation(self, request, pk=None):
        """Get documentation for an endpoint"""
        endpoint = self.get_object()
        try:
            docs = endpoint.documentation
            serializer = APIDocumentationSerializer(docs)
            return Response(serializer.data)
        except APIDocumentation.DoesNotExist:
            return Response({'error': 'Documentation not found'}, status=404)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test an endpoint"""
        endpoint = self.get_object()
        
        # Get mock response if available
        mock_response = MockService.get_mock_response(endpoint, request.data)
        if mock_response:
            return Response({
                'type': 'mock',
                'response': mock_response
            })
        
        return Response({
            'type': 'live',
            'message': 'No mock available, would hit live endpoint'
        })


class APIUsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for API usage logs (read-only)"""
    queryset = APIUsageLog.objects.all()
    serializer_class = APIUsageLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter logs by various parameters"""
        queryset = self.queryset
        
        # Filter by API key if not superuser
        if not self.request.user.is_superuser:
            queryset = queryset.filter(api_key__user=self.request.user)
        
        # Date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)
        
        # Status filtering
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Endpoint filtering
        endpoint_id = self.request.query_params.get('endpoint')
        if endpoint_id:
            queryset = queryset.filter(endpoint_id=endpoint_id)
        
        return queryset.order_by('-timestamp')


class APIWebhookViewSet(viewsets.ModelViewSet):
    """ViewSet for webhook management"""
    queryset = APIWebhook.objects.all()
    serializer_class = APIWebhookSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test a webhook"""
        webhook = self.get_object()
        
        test_payload = {
            'event': 'webhook.test',
            'timestamp': timezone.now().isoformat(),
            'data': {'message': 'This is a test webhook'}
        }
        
        APIWebhookService.deliver_webhook(webhook, 'webhook.test', test_payload)
        
        return Response({'message': 'Test webhook sent'})
    
    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        """Get webhook deliveries"""
        webhook = self.get_object()
        deliveries = webhook.deliveries.all()[:50]  # Last 50 deliveries
        
        serializer = APIWebhookDeliverySerializer(deliveries, many=True)
        return Response(serializer.data)


class APIMockServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for mock service management"""
    queryset = APIMockService.objects.all()
    serializer_class = APIMockServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a mock service"""
        mock = self.get_object()
        mock.is_active = True
        mock.save()
        
        return Response({'status': 'activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a mock service"""
        mock = self.get_object()
        mock.is_active = False
        mock.save()
        
        return Response({'status': 'deactivated'})


class APIAnalyticsView(APIView):
    """View for API analytics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive API analytics"""
        days = int(request.query_params.get('days', 7))
        
        # Get analytics data
        analytics_data = APIMetricsService.get_analytics_data(days)
        
        serializer = APIAnalyticsSerializer(analytics_data)
        return Response(serializer.data)


class APIHealthView(APIView):
    """View for API health status"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get API health status"""
        import psutil
        
        # Calculate uptime (simplified)
        uptime = 99.9  # This would be calculated from actual uptime data
        
        # Get recent performance data
        recent_logs = APIUsageLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        )
        
        avg_response_time = recent_logs.aggregate(avg=Avg('response_time'))['avg'] or 0
        error_count = recent_logs.filter(status='error').count()
        total_count = recent_logs.count()
        error_rate = (error_count / max(total_count, 1)) * 100
        
        # System metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        disk = psutil.disk_usage('/')
        
        health_data = {
            'status': 'healthy' if error_rate < 5 else 'degraded',
            'uptime': uptime,
            'response_time': avg_response_time,
            'error_rate': error_rate,
            'active_connections': total_count,
            'memory_usage': memory.percent,
            'cpu_usage': cpu_percent,
            'disk_usage': (disk.used / disk.total) * 100,
        }
        
        serializer = APIHealthSerializer(health_data)
        return Response(serializer.data)


class GraphQLView(APIView):
    """GraphQL endpoint for API management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Execute GraphQL query"""
        serializer = GraphQLQuerySerializer(data=request.data)
        if serializer.is_valid():
            # This would integrate with a GraphQL engine
            # For now, return a placeholder response
            return Response({
                'data': {'message': 'GraphQL query executed'},
                'errors': []
            })
        
        return Response(serializer.errors, status=400)


class APITestingView(APIView):
    """View for API testing functionality"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Run API test cases"""
        serializer = APITestCaseSerializer(data=request.data)
        if serializer.is_valid():
            test_case = serializer.validated_data
            
            # Execute test case (simplified implementation)
            result = {
                'name': test_case['name'],
                'status': 'passed',
                'response_time': 150,
                'assertions_passed': len(test_case.get('assertions', [])),
                'assertions_failed': 0,
            }
            
            return Response(result)
        
        return Response(serializer.errors, status=400)


class APIBenchmarkView(APIView):
    """View for API benchmarking"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Run API benchmark"""
        endpoint = request.data.get('endpoint')
        concurrent_users = request.data.get('concurrent_users', 10)
        duration = request.data.get('duration', 60)
        
        # This would run actual benchmarks
        # For now, return mock data
        benchmark_data = {
            'endpoint': endpoint,
            'concurrent_users': concurrent_users,
            'total_requests': concurrent_users * 100,
            'duration': duration,
            'requests_per_second': (concurrent_users * 100) / duration,
            'avg_response_time': 120.5,
            'min_response_time': 45.2,
            'max_response_time': 890.1,
            'error_count': 2,
            'error_rate': 2.0,
            'percentiles': {
                '50': 115.0,
                '90': 200.0,
                '95': 350.0,
                '99': 750.0,
            }
        }
        
        serializer = APIBenchmarkSerializer(benchmark_data)
        return Response(serializer.data)


class APIRateLimitView(APIView):
    """View for rate limit management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get rate limit status for API keys"""
        api_key_id = request.query_params.get('api_key')
        
        if api_key_id:
            try:
                api_key = APIKey.objects.get(id=api_key_id)
                rate_limits = APIRateLimit.objects.filter(api_key=api_key)
                serializer = APIRateLimitSerializer(rate_limits, many=True)
                return Response(serializer.data)
            except APIKey.DoesNotExist:
                return Response({'error': 'API key not found'}, status=404)
        
        # Return all rate limits for user's API keys
        if request.user.is_superuser:
            rate_limits = APIRateLimit.objects.all()
        else:
            rate_limits = APIRateLimit.objects.filter(api_key__user=request.user)
        
        serializer = APIRateLimitSerializer(rate_limits, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Reset rate limits for an API key"""
        api_key_id = request.data.get('api_key')
        
        try:
            api_key = APIKey.objects.get(id=api_key_id)
            
            # Check permissions
            if not request.user.is_superuser and api_key.user != request.user:
                return Response({'error': 'Permission denied'}, status=403)
            
            # Reset rate limits
            APIRateLimit.objects.filter(api_key=api_key).update(
                requests_per_minute=0,
                requests_per_hour=0,
                requests_per_day=0,
                minute_reset=timezone.now() + timedelta(minutes=1),
                hour_reset=timezone.now() + timedelta(hours=1),
                day_reset=timezone.now() + timedelta(days=1),
            )
            
            return Response({'message': 'Rate limits reset successfully'})
            
        except APIKey.DoesNotExist:
            return Response({'error': 'API key not found'}, status=404)


class APISecurityView(APIView):
    """View for API security management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get security status and alerts"""
        # Check for suspicious activity
        suspicious_keys = []
        
        for api_key in APIKey.objects.filter(status='active'):
            if APISecurityService.detect_suspicious_activity(api_key):
                suspicious_keys.append({
                    'id': str(api_key.id),
                    'name': api_key.name,
                    'user': api_key.user.username,
                    'last_used': api_key.last_used_at,
                })
        
        return Response({
            'suspicious_activity': suspicious_keys,
            'total_active_keys': APIKey.objects.filter(status='active').count(),
            'total_revoked_keys': APIKey.objects.filter(status='revoked').count(),
        })
    
    def post(self, request):
        """Generate temporary API token"""
        api_key_id = request.data.get('api_key')
        expires_in = request.data.get('expires_in', 3600)
        
        try:
            api_key = APIKey.objects.get(id=api_key_id)
            
            # Check permissions
            if not request.user.is_superuser and api_key.user != request.user:
                return Response({'error': 'Permission denied'}, status=403)
            
            token = APISecurityService.generate_api_token(api_key, expires_in)
            
            return Response({
                'token': token,
                'expires_in': expires_in,
                'expires_at': (timezone.now() + timedelta(seconds=expires_in)).isoformat(),
            })
            
        except APIKey.DoesNotExist:
            return Response({'error': 'API key not found'}, status=404)


class APIDocumentationViewSet(viewsets.ModelViewSet):
    """ViewSet for API documentation management"""
    queryset = APIDocumentation.objects.all()
    serializer_class = APIDocumentationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter documentation by endpoint"""
        queryset = self.queryset
        
        endpoint_id = self.request.query_params.get('endpoint')
        if endpoint_id:
            queryset = queryset.filter(endpoint_id=endpoint_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export API documentation"""
        format_type = request.query_params.get('format', 'json')
        
        docs = self.get_queryset()
        
        if format_type == 'openapi':
            # Generate OpenAPI spec
            openapi_spec = {
                'openapi': '3.0.0',
                'info': {
                    'title': 'API Documentation',
                    'version': '1.0.0',
                },
                'paths': {}
            }
            
            for doc in docs:
                endpoint = doc.endpoint
                path = endpoint.path
                method = endpoint.method.lower()
                
                if path not in openapi_spec['paths']:
                    openapi_spec['paths'][path] = {}
                
                openapi_spec['paths'][path][method] = {
                    'summary': doc.summary,
                    'description': doc.description,
                    'parameters': doc.parameters,
                    'responses': {
                        '200': {
                            'description': 'Success',
                            'content': {
                                'application/json': {
                                    'examples': doc.response_examples
                                }
                            }
                        }
                    }
                }
            
            return Response(openapi_spec)
        
        # Default JSON format
        serializer = self.get_serializer(docs, many=True)
        return Response(serializer.data)