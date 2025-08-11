from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from datetime import timedelta
import logging

from .models import (
    CacheConfiguration, CacheMetrics, CacheInvalidation,
    CacheWarming, CacheAlert, CacheOptimization
)
from .serializers import (
    CacheConfigurationSerializer, CacheMetricsSerializer, CacheInvalidationSerializer,
    CacheWarmingSerializer, CacheAlertSerializer, CacheOptimizationSerializer,
    CacheStatsSerializer, CacheAnalysisSerializer, CacheBenchmarkSerializer,
    CDNAnalyticsSerializer, AssetOptimizationSerializer, ImageOptimizationSerializer,
    CacheInvalidationRequestSerializer, CacheWarmingRequestSerializer
)
from .cache_manager import cache_manager
from .optimization import cache_optimizer
from .cdn_integration import cdn_manager

logger = logging.getLogger(__name__)


class CacheConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for cache configuration management"""
    
    queryset = CacheConfiguration.objects.all()
    serializer_class = CacheConfigurationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by cache type
        cache_type = self.request.query_params.get('cache_type')
        if cache_type:
            queryset = queryset.filter(cache_type=cache_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('priority', 'name')
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test cache connection"""
        try:
            config = self.get_object()
            
            # Test basic operations
            test_key = f"test_connection_{config.name}_{timezone.now().timestamp()}"
            test_value = "connection_test"
            
            # Test set operation
            set_success = cache_manager.set(test_key, test_value, config.name)
            if not set_success:
                return Response({
                    'success': False,
                    'message': 'Failed to set test value'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Test get operation
            retrieved_value = cache_manager.get(test_key, config.name)
            if retrieved_value != test_value:
                return Response({
                    'success': False,
                    'message': 'Retrieved value does not match set value'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Test delete operation
            delete_success = cache_manager.delete(test_key, config.name)
            
            # Get cache stats
            stats = cache_manager.get_cache_stats(config.name)
            
            return Response({
                'success': True,
                'message': 'Cache connection test successful',
                'operations': {
                    'set': set_success,
                    'get': retrieved_value == test_value,
                    'delete': delete_success
                },
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Cache connection test failed: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get cache statistics"""
        try:
            config = self.get_object()
            stats = cache_manager.get_cache_stats(config.name)
            
            serializer = CacheStatsSerializer(stats)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CacheMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for cache metrics (read-only)"""
    
    queryset = CacheMetrics.objects.all()
    serializer_class = CacheMetricsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by cache name
        cache_name = self.request.query_params.get('cache_name')
        if cache_name:
            queryset = queryset.filter(cache_name=cache_name)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get metrics summary"""
        try:
            cache_name = request.query_params.get('cache_name')
            days = int(request.query_params.get('days', 7))
            
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            queryset = self.get_queryset().filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )
            
            if cache_name:
                queryset = queryset.filter(cache_name=cache_name)
            
            # Aggregate metrics
            summary = queryset.aggregate(
                avg_hit_ratio=Avg('hit_ratio'),
                avg_response_time=Avg('avg_response_time_ms'),
                avg_memory_usage=Avg('memory_usage_percent'),
                total_operations=Sum('get_operations') + Sum('set_operations'),
                total_errors=Sum('error_count'),
                total_metrics=Count('id')
            )
            
            # Calculate additional metrics
            if summary['total_operations']:
                summary['error_rate'] = (summary['total_errors'] or 0) / summary['total_operations']
            else:
                summary['error_rate'] = 0
            
            # Get cache names and their counts
            cache_breakdown = queryset.values('cache_name').annotate(
                count=Count('id'),
                avg_hit_ratio=Avg('hit_ratio'),
                avg_response_time=Avg('avg_response_time_ms')
            ).order_by('-count')
            
            return Response({
                'period': f'{days} days',
                'summary': summary,
                'cache_breakdown': list(cache_breakdown)
            })
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CacheInvalidationViewSet(viewsets.ModelViewSet):
    """ViewSet for cache invalidation management"""
    
    queryset = CacheInvalidation.objects.all()
    serializer_class = CacheInvalidationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by cache name
        cache_name = self.request.query_params.get('cache_name')
        if cache_name:
            queryset = queryset.filter(cache_name=cache_name)
        
        # Filter by invalidation type
        invalidation_type = self.request.query_params.get('invalidation_type')
        if invalidation_type:
            queryset = queryset.filter(invalidation_type=invalidation_type)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['post'])
    def invalidate_keys(self, request):
        """Invalidate specific cache keys"""
        try:
            serializer = CacheInvalidationRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            cache_name = serializer.validated_data['cache_name']
            keys = serializer.validated_data.get('keys', [])
            pattern = serializer.validated_data.get('pattern')
            reason = serializer.validated_data['reason']
            
            results = []
            
            if keys:
                # Invalidate specific keys
                for key in keys:
                    success = cache_manager.delete(key, cache_name)
                    
                    # Record invalidation
                    CacheInvalidation.objects.create(
                        cache_key=key,
                        cache_name=cache_name,
                        invalidation_type='manual',
                        reason=reason,
                        triggered_by=request.user,
                        success=success
                    )
                    
                    results.append({
                        'key': key,
                        'success': success
                    })
            
            if pattern:
                # Invalidate by pattern
                deleted_count = cache_manager.invalidate_pattern(pattern, cache_name)
                
                # Record invalidation
                CacheInvalidation.objects.create(
                    cache_key=pattern,
                    cache_name=cache_name,
                    invalidation_type='pattern',
                    reason=reason,
                    triggered_by=request.user,
                    success=deleted_count > 0
                )
                
                results.append({
                    'pattern': pattern,
                    'deleted_count': deleted_count,
                    'success': deleted_count > 0
                })
            
            return Response({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CacheWarmingViewSet(viewsets.ModelViewSet):
    """ViewSet for cache warming management"""
    
    queryset = CacheWarming.objects.all()
    serializer_class = CacheWarmingSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute cache warming"""
        try:
            warming_config = self.get_object()
            
            # This would typically load data based on the query pattern
            # For now, we'll simulate the warming process
            
            # Update last run time
            warming_config.last_run = timezone.now()
            
            # Simulate warming success/failure
            import random
            success = random.choice([True, True, True, False])  # 75% success rate
            
            if success:
                warming_config.success_count += 1
            else:
                warming_config.failure_count += 1
            
            warming_config.save()
            
            return Response({
                'success': success,
                'warming_config': self.get_serializer(warming_config).data,
                'message': 'Cache warming executed successfully' if success else 'Cache warming failed'
            })
            
        except Exception as e:
            logger.error(f"Cache warming execution failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def warm_keys(self, request):
        """Warm specific cache keys"""
        try:
            serializer = CacheWarmingRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            cache_name = serializer.validated_data['cache_name']
            keys = serializer.validated_data['keys']
            data_source = serializer.validated_data['data_source']
            
            # This would typically use a data loader function
            # For now, we'll simulate the warming process
            def mock_data_loader(key):
                return f"warmed_data_for_{key}"
            
            results = cache_manager.warm_cache(cache_name, mock_data_loader, keys)
            
            return Response({
                'success': True,
                'results': results,
                'total_keys': len(keys),
                'successful_keys': sum(1 for success in results.values() if success)
            })
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CacheAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for cache alert management"""
    
    queryset = CacheAlert.objects.all()
    serializer_class = CacheAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by cache name
        cache_name = self.request.query_params.get('cache_name')
        if cache_name:
            queryset = queryset.filter(cache_name=cache_name)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by resolution status
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        try:
            alert = self.get_object()
            
            if alert.is_resolved:
                return Response({
                    'success': False,
                    'message': 'Alert is already resolved'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            alert.is_resolved = True
            alert.resolved_at = timezone.now()
            alert.resolved_by = request.user
            alert.save()
            
            return Response({
                'success': True,
                'message': 'Alert resolved successfully',
                'alert': self.get_serializer(alert).data
            })
            
        except Exception as e:
            logger.error(f"Alert resolution failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def resolve_bulk(self, request):
        """Resolve multiple alerts"""
        try:
            alert_ids = request.data.get('alert_ids', [])
            
            if not alert_ids:
                return Response({
                    'success': False,
                    'message': 'No alert IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            alerts = CacheAlert.objects.filter(
                id__in=alert_ids,
                is_resolved=False
            )
            
            updated_count = alerts.update(
                is_resolved=True,
                resolved_at=timezone.now(),
                resolved_by=request.user
            )
            
            return Response({
                'success': True,
                'message': f'Resolved {updated_count} alerts',
                'resolved_count': updated_count
            })
            
        except Exception as e:
            logger.error(f"Bulk alert resolution failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CacheOptimizationViewSet(viewsets.ModelViewSet):
    """ViewSet for cache optimization management"""
    
    queryset = CacheOptimization.objects.all()
    serializer_class = CacheOptimizationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by cache name
        cache_name = self.request.query_params.get('cache_name')
        if cache_name:
            queryset = queryset.filter(cache_name=cache_name)
        
        # Filter by optimization type
        optimization_type = self.request.query_params.get('optimization_type')
        if optimization_type:
            queryset = queryset.filter(optimization_type=optimization_type)
        
        # Filter by application status
        is_applied = self.request.query_params.get('is_applied')
        if is_applied is not None:
            queryset = queryset.filter(is_applied=is_applied.lower() == 'true')
        
        return queryset.order_by('-impact_score', '-created_at')
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply an optimization"""
        try:
            optimization = self.get_object()
            result = cache_optimizer.apply_optimization(optimization.id, request.user)
            
            if 'error' in result:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': 'Optimization applied successfully',
                'result': result
            })
            
        except Exception as e:
            logger.error(f"Optimization application failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Analyze cache performance and generate optimizations"""
        try:
            cache_name = request.data.get('cache_name')
            days = request.data.get('days', 7)
            
            if not cache_name:
                return Response({
                    'success': False,
                    'message': 'cache_name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Perform analysis
            analysis = cache_optimizer.analyze_cache_performance(cache_name, days)
            
            if 'error' in analysis:
                return Response({
                    'success': False,
                    'error': analysis['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate optimizations
            optimizations = cache_optimizer.optimize_cache_configuration(cache_name)
            
            serializer = CacheAnalysisSerializer(analysis)
            
            return Response({
                'success': True,
                'analysis': serializer.data,
                'optimizations': optimizations
            })
            
        except Exception as e:
            logger.error(f"Cache analysis failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def benchmark(self, request):
        """Benchmark cache performance"""
        try:
            cache_name = request.data.get('cache_name')
            test_duration = request.data.get('test_duration', 60)
            
            if not cache_name:
                return Response({
                    'success': False,
                    'message': 'cache_name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Run benchmark
            results = cache_optimizer.benchmark_cache_performance(cache_name, test_duration)
            
            if 'error' in results:
                return Response({
                    'success': False,
                    'error': results['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = CacheBenchmarkSerializer(results)
            
            return Response({
                'success': True,
                'benchmark': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Cache benchmarking failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def health_check(self, request):
        """Check cache health"""
        try:
            cache_name = request.query_params.get('cache_name')
            
            if not cache_name:
                return Response({
                    'success': False,
                    'message': 'cache_name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            health = cache_optimizer.monitor_cache_health(cache_name)
            
            if 'error' in health:
                return Response({
                    'success': False,
                    'error': health['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'health': health
            })
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CDNManagementViewSet(viewsets.ViewSet):
    """ViewSet for CDN management"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def upload_assets(self, request):
        """Upload static assets to CDN"""
        try:
            assets = request.data.get('assets', [])
            
            if not assets:
                return Response({
                    'success': False,
                    'message': 'No assets provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            results = cdn_manager.upload_static_assets(assets)
            
            if 'error' in results:
                return Response({
                    'success': False,
                    'error': results['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = AssetOptimizationSerializer(results)
            
            return Response({
                'success': True,
                'results': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Asset upload failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def optimize_images(self, request):
        """Optimize images for web delivery"""
        try:
            image_paths = request.data.get('image_paths', [])
            formats = request.data.get('formats', ['webp', 'avif'])
            
            if not image_paths:
                return Response({
                    'success': False,
                    'message': 'No image paths provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            results = cdn_manager.optimize_images(image_paths, formats)
            
            if 'error' in results:
                return Response({
                    'success': False,
                    'error': results['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ImageOptimizationSerializer(results)
            
            return Response({
                'success': True,
                'results': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def invalidate_cdn(self, request):
        """Invalidate CDN cache"""
        try:
            paths = request.data.get('paths', [])
            distribution_id = request.data.get('distribution_id')
            
            if not paths:
                return Response({
                    'success': False,
                    'message': 'No paths provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            results = cdn_manager.invalidate_cache(paths, distribution_id)
            
            if 'error' in results:
                return Response({
                    'success': False,
                    'error': results['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"CDN invalidation failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get CDN analytics"""
        try:
            distribution_id = request.query_params.get('distribution_id')
            days = int(request.query_params.get('days', 7))
            
            analytics = cdn_manager.get_cdn_analytics(distribution_id, days)
            
            if 'error' in analytics:
                return Response({
                    'success': False,
                    'error': analytics['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = CDNAnalyticsSerializer(analytics)
            
            return Response({
                'success': True,
                'analytics': serializer.data
            })
            
        except Exception as e:
            logger.error(f"CDN analytics failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)