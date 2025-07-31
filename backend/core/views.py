"""
Core views including database connection monitoring endpoints
"""
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAdminUser])
@cache_page(30)  # Cache for 30 seconds
def connection_pool_status(request):
    """
    Get connection pool status and metrics
    """
    try:
        from core.connection_pool import get_pool_manager
        from core.connection_monitor import get_connection_monitor
        
        pool_manager = get_pool_manager()
        monitor = get_connection_monitor()
        
        # Get pool status
        pool_status = pool_manager.get_pool_status()
        
        # Get current metrics
        current_metrics = monitor.get_current_metrics()
        
        # Get health summary
        health_summary = monitor.get_health_summary()
        
        response_data = {
            'timestamp': datetime.now().isoformat(),
            'pool_status': pool_status,
            'current_metrics': current_metrics,
            'health_summary': health_summary,
            'status': 'success'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get connection pool status: {e}")
        return Response(
            {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def connection_metrics_history(request):
    """
    Get historical connection metrics
    """
    try:
        from core.connection_monitor import get_connection_monitor
        
        monitor = get_connection_monitor()
        
        # Get parameters
        db_alias = request.GET.get('database', 'default')
        hours = int(request.GET.get('hours', 24))
        
        # Get historical metrics
        history = monitor.get_metrics_history(db_alias, hours)
        
        response_data = {
            'database': db_alias,
            'hours': hours,
            'metrics_count': len(history),
            'metrics': history,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get metrics history: {e}")
        return Response(
            {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def database_router_stats(request):
    """
    Get database router statistics
    """
    try:
        from core.database_router import get_router_stats
        
        router_stats = get_router_stats()
        
        response_data = {
            'router_stats': router_stats,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get router stats: {e}")
        return Response(
            {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def database_alerts(request):
    """
    Get recent database alerts
    """
    try:
        # Get alerts from cache
        alerts = cache.get('db_alerts', [])
        
        # Filter by severity if requested
        severity = request.GET.get('severity')
        if severity:
            alerts = [alert for alert in alerts if alert.get('level') == severity]
        
        # Limit results
        limit = int(request.GET.get('limit', 50))
        alerts = alerts[-limit:]
        
        response_data = {
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get database alerts: {e}")
        return Response(
            {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def optimize_connection_pools(request):
    """
    Optimize connection pool sizes
    """
    try:
        from core.connection_pool import get_pool_manager
        
        pool_manager = get_pool_manager()
        
        # Get pool name from request
        pool_name = request.data.get('pool_name')
        target_utilization = float(request.data.get('target_utilization', 0.8))
        
        if pool_name:
            # Optimize specific pool
            pool_manager.optimize_pool_size(pool_name, target_utilization)
            message = f"Optimized pool: {pool_name}"
        else:
            # Optimize all pools
            pool_status = pool_manager.get_pool_status()
            for pool_name in pool_status.keys():
                pool_manager.optimize_pool_size(pool_name, target_utilization)
            message = "Optimized all connection pools"
        
        # Get updated status
        updated_status = pool_manager.get_pool_status()
        
        response_data = {
            'message': message,
            'updated_status': updated_status,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to optimize connection pools: {e}")
        return Response(
            {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def test_connection_pools(request):
    """
    Test connection pool performance
    """
    try:
        import threading
        import time
        import random
        from django.db import connections
        from django.conf import settings
        from core.connection_monitor import get_connection_monitor
        
        # Get test parameters
        duration = int(request.data.get('duration', 30))  # seconds
        threads = int(request.data.get('threads', 5))
        
        results = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_time': 0,
            'errors': []
        }
        
        def test_worker():
            """Worker function for testing connections"""
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    # Test random database
                    db_alias = random.choice(list(settings.DATABASES.keys()))
                    connection = connections[db_alias]
                    
                    query_start = time.time()
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                    
                    query_time = time.time() - query_start
                    
                    results['total_queries'] += 1
                    results['successful_queries'] += 1
                    results['total_time'] += query_time
                    
                    # Record query time in monitor
                    monitor = get_connection_monitor()
                    monitor.record_query_time(db_alias, query_time)
                    
                    time.sleep(0.1)  # Brief pause between queries
                    
                except Exception as e:
                    results['failed_queries'] += 1
                    results['errors'].append(str(e))
        
        # Start test threads
        test_threads = []
        for i in range(threads):
            thread = threading.Thread(target=test_worker)
            thread.start()
            test_threads.append(thread)
        
        # Wait for completion
        for thread in test_threads:
            thread.join()
        
        # Calculate results
        avg_time = 0
        qps = 0
        failure_rate = 0
        
        if results['successful_queries'] > 0:
            avg_time = results['total_time'] / results['successful_queries']
            qps = results['successful_queries'] / duration
        
        if results['total_queries'] > 0:
            failure_rate = (results['failed_queries'] / results['total_queries']) * 100
        
        response_data = {
            'test_duration': duration,
            'concurrent_threads': threads,
            'total_queries': results['total_queries'],
            'successful_queries': results['successful_queries'],
            'failed_queries': results['failed_queries'],
            'average_query_time': round(avg_time, 3),
            'queries_per_second': round(qps, 2),
            'failure_rate': round(failure_rate, 2),
            'unique_errors': list(set(results['errors'][:10])),  # First 10 unique errors
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to test connection pools: {e}")
        return Response(
            {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )