"""
API views for error handling and recovery system
"""

import uuid
import json
from typing import Dict, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

from .models import ErrorLog, DebugConfiguration
from .error_handling import (
    ErrorRecoveryEngine, ErrorClassifier, ErrorContext, 
    error_recovery_engine, CircuitBreaker
)
# from .error_notifications import notification_manager
from .serializers import ErrorLogSerializer, DebugConfigurationSerializer


class ErrorRecoveryViewSet(viewsets.ViewSet):
    """ViewSet for error recovery operations"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def handle_error(self, request):
        """Handle an error with recovery strategies"""
        try:
            data = request.data
            
            # Extract error information
            exception_type = data.get('exception_type', 'Exception')
            error_message = data.get('error_message', '')
            layer = data.get('layer', 'unknown')
            component = data.get('component', 'unknown')
            operation = data.get('operation', 'unknown')
            
            # Create error context
            context = ErrorContext(
                correlation_id=uuid.UUID(data.get('correlation_id')) if data.get('correlation_id') else None,
                user=request.user,
                request_path=request.path,
                request_method=request.method,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata=data.get('metadata', {})
            )
            
            # Create exception object
            exception = Exception(error_message)
            exception.__class__.__name__ = exception_type
            
            # Handle error with recovery engine
            recovery_result = error_recovery_engine.handle_error(
                exception=exception,
                layer=layer,
                component=component,
                operation=operation,
                context=context
            )
            
            return Response({
                'success': True,
                'recovery_applied': recovery_result is not None,
                'recovery_result': str(recovery_result) if recovery_result else None,
                'message': 'Error handled successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def system_health(self, request):
        """Get system health based on error patterns"""
        try:
            health_data = error_recovery_engine.get_system_health()
            return Response(health_data)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def classify_error(self, request):
        """Classify an error and get recovery strategy"""
        try:
            data = request.data
            
            exception_type = data.get('exception_type', 'Exception')
            error_message = data.get('error_message', '')
            layer = data.get('layer', 'unknown')
            component = data.get('component', 'unknown')
            
            # Create exception object
            exception = Exception(error_message)
            exception.__class__.__name__ = exception_type
            
            # Classify error
            classifier = ErrorClassifier()
            classification = classifier.classify_error(exception, layer, component)
            
            return Response({
                'category': classification.category.value,
                'severity': classification.severity.value,
                'is_recoverable': classification.is_recoverable,
                'recovery_strategy': classification.recovery_strategy.value,
                'max_retries': classification.max_retries,
                'base_delay_seconds': classification.base_delay_seconds,
                'backoff_multiplier': classification.backoff_multiplier,
                'circuit_breaker_threshold': classification.circuit_breaker_threshold,
                'circuit_breaker_timeout': classification.circuit_breaker_timeout
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def recovery_statistics(self, request):
        """Get error recovery statistics"""
        try:
            # Get recent errors with recovery information
            hours = int(request.query_params.get('hours', 24))
            since = timezone.now() - timedelta(hours=hours)
            
            recent_errors = ErrorLog.objects.filter(timestamp__gte=since)
            
            # Calculate statistics
            total_errors = recent_errors.count()
            resolved_errors = recent_errors.filter(resolved=True).count()
            
            # Group by recovery strategy (from metadata)
            recovery_stats = {}
            for error in recent_errors:
                classification = error.metadata.get('classification', {})
                strategy = classification.get('recovery_strategy', 'unknown')
                
                if strategy not in recovery_stats:
                    recovery_stats[strategy] = {'count': 0, 'resolved': 0}
                
                recovery_stats[strategy]['count'] += 1
                if error.resolved:
                    recovery_stats[strategy]['resolved'] += 1
            
            # Calculate success rates
            for strategy, stats in recovery_stats.items():
                if stats['count'] > 0:
                    stats['success_rate'] = (stats['resolved'] / stats['count']) * 100
                else:
                    stats['success_rate'] = 0
            
            return Response({
                'period_hours': hours,
                'total_errors': total_errors,
                'resolved_errors': resolved_errors,
                'overall_resolution_rate': (resolved_errors / total_errors * 100) if total_errors > 0 else 0,
                'recovery_strategies': recovery_stats,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CircuitBreakerViewSet(viewsets.ViewSet):
    """ViewSet for circuit breaker management"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get status of all circuit breakers"""
        try:
            component = request.query_params.get('component')
            
            if component:
                # Get status for specific component
                circuit_breaker = CircuitBreaker(component)
                return Response({
                    'component': component,
                    'status': circuit_breaker.get_status()
                })
            else:
                # Get status for all circuit breakers from recovery engine
                circuit_breakers = error_recovery_engine.circuit_breakers
                statuses = {}
                
                for component_name, breaker in circuit_breakers.items():
                    statuses[component_name] = breaker.get_status()
                
                return Response({
                    'circuit_breakers': statuses,
                    'timestamp': timezone.now().isoformat()
                })
                
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def reset(self, request):
        """Reset a circuit breaker"""
        try:
            component = request.data.get('component')
            if not component:
                return Response({
                    'error': 'Component name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Reset circuit breaker by clearing cache
            cache_keys = [
                f"circuit_breaker:{component}:state",
                f"circuit_breaker:{component}:failures",
                f"circuit_breaker:{component}:open_time"
            ]
            
            for key in cache_keys:
                cache.delete(key)
            
            return Response({
                'success': True,
                'message': f'Circuit breaker for {component} has been reset'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def test_failure(self, request):
        """Simulate a failure for testing circuit breaker"""
        try:
            component = request.data.get('component')
            if not component:
                return Response({
                    'error': 'Component name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create circuit breaker
            if component not in error_recovery_engine.circuit_breakers:
                error_recovery_engine.circuit_breakers[component] = CircuitBreaker(component)
            
            circuit_breaker = error_recovery_engine.circuit_breakers[component]
            circuit_breaker.record_failure()
            
            return Response({
                'success': True,
                'message': f'Failure recorded for {component}',
                'status': circuit_breaker.get_status()
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationViewSet(viewsets.ViewSet):
    """ViewSet for notification management"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get notification history"""
        try:
            hours = int(request.query_params.get('hours', 24))
            from .error_notifications import notification_manager
            notifications = notification_manager.get_notification_history(hours)
            
            return Response({
                'notifications': notifications,
                'count': len(notifications),
                'period_hours': hours
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def test_notification(self, request):
        """Send a test notification"""
        try:
            data = request.data
            escalation_level = data.get('escalation_level', 'medium')
            
            # Create a test error log
            test_error = ErrorLog.objects.create(
                layer='api',
                component='test',
                severity='error',
                error_type='TestError',
                error_message='This is a test notification',
                user=request.user,
                metadata={'test': True}
            )
            
            # Create escalation data
            escalation_data = {
                'error_log': test_error,
                'classification': type('MockClassification', (), {
                    'category': type('MockCategory', (), {'value': 'system'})(),
                    'severity': type('MockSeverity', (), {'value': 'error'})(),
                    'is_recoverable': True,
                    'recovery_strategy': type('MockStrategy', (), {'value': 'retry'})()
                })(),
                'escalation_level': escalation_level,
                'timestamp': timezone.now()
            }
            
            # Send notifications
            from .error_notifications import notification_manager
            notification_manager.send_notifications(escalation_data)
            
            # Clean up test error
            test_error.delete()
            
            return Response({
                'success': True,
                'message': f'Test notification sent for {escalation_level} escalation level'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def configuration(self, request):
        """Get notification configuration"""
        try:
            escalation_level = request.query_params.get('level', 'default')
            
            # Get notification configurations
            configs = DebugConfiguration.objects.filter(
                name__icontains='notification',
                name__contains=escalation_level,
                enabled=True
            )
            
            config_data = {}
            for config in configs:
                config_data[config.name] = config.config_data
            
            return Response({
                'escalation_level': escalation_level,
                'configurations': config_data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def update_configuration(self, request):
        """Update notification configuration"""
        try:
            data = request.data
            config_name = data.get('config_name')
            config_data = data.get('config_data')
            
            if not config_name or not config_data:
                return Response({
                    'error': 'config_name and config_data are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update or create configuration
            config, created = DebugConfiguration.objects.update_or_create(
                name=config_name,
                defaults={
                    'config_type': 'alert_settings',
                    'enabled': True,
                    'config_data': config_data,
                    'description': f'Updated via API at {timezone.now()}'
                }
            )
            
            return Response({
                'success': True,
                'created': created,
                'message': f'Configuration {config_name} {"created" if created else "updated"} successfully'
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ErrorClassificationViewSet(viewsets.ViewSet):
    """ViewSet for error classification operations"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available error categories"""
        from .error_handling import ErrorCategory, ErrorSeverity, RecoveryStrategy
        
        return Response({
            'categories': [category.value for category in ErrorCategory],
            'severities': [severity.value for severity in ErrorSeverity],
            'recovery_strategies': [strategy.value for strategy in RecoveryStrategy]
        })
    
    @action(detail=False, methods=['post'])
    def classify_batch(self, request):
        """Classify multiple errors at once"""
        try:
            errors = request.data.get('errors', [])
            if not errors:
                return Response({
                    'error': 'errors list is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            classifier = ErrorClassifier()
            results = []
            
            for error_data in errors:
                try:
                    exception_type = error_data.get('exception_type', 'Exception')
                    error_message = error_data.get('error_message', '')
                    layer = error_data.get('layer', 'unknown')
                    component = error_data.get('component', 'unknown')
                    
                    # Create exception object
                    exception = Exception(error_message)
                    exception.__class__.__name__ = exception_type
                    
                    # Classify error
                    classification = classifier.classify_error(exception, layer, component)
                    
                    results.append({
                        'input': error_data,
                        'classification': {
                            'category': classification.category.value,
                            'severity': classification.severity.value,
                            'is_recoverable': classification.is_recoverable,
                            'recovery_strategy': classification.recovery_strategy.value,
                            'max_retries': classification.max_retries,
                            'base_delay_seconds': classification.base_delay_seconds
                        }
                    })
                    
                except Exception as e:
                    results.append({
                        'input': error_data,
                        'error': str(e)
                    })
            
            return Response({
                'results': results,
                'total_processed': len(results)
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get error classification statistics"""
        try:
            hours = int(request.query_params.get('hours', 24))
            since = timezone.now() - timedelta(hours=hours)
            
            recent_errors = ErrorLog.objects.filter(timestamp__gte=since)
            
            # Group by classification data
            category_stats = {}
            severity_stats = {}
            recovery_stats = {}
            
            for error in recent_errors:
                classification = error.metadata.get('classification', {})
                
                # Category statistics
                category = classification.get('category', 'unknown')
                category_stats[category] = category_stats.get(category, 0) + 1
                
                # Severity statistics
                severity = classification.get('severity', error.severity)
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
                
                # Recovery strategy statistics
                strategy = classification.get('recovery_strategy', 'unknown')
                recovery_stats[strategy] = recovery_stats.get(strategy, 0) + 1
            
            return Response({
                'period_hours': hours,
                'total_errors': recent_errors.count(),
                'category_distribution': category_stats,
                'severity_distribution': severity_stats,
                'recovery_strategy_distribution': recovery_stats,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SystemHealthViewSet(viewsets.ViewSet):
    """ViewSet for system health monitoring related to error handling"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get system health overview"""
        try:
            health_data = error_recovery_engine.get_system_health()
            
            # Add additional metrics
            hours = int(request.query_params.get('hours', 1))
            since = timezone.now() - timedelta(hours=hours)
            
            recent_errors = ErrorLog.objects.filter(timestamp__gte=since)
            
            # Calculate error trends
            error_trend = []
            for i in range(hours):
                hour_start = since + timedelta(hours=i)
                hour_end = hour_start + timedelta(hours=1)
                hour_errors = recent_errors.filter(
                    timestamp__gte=hour_start,
                    timestamp__lt=hour_end
                ).count()
                
                error_trend.append({
                    'hour': hour_start.isoformat(),
                    'error_count': hour_errors
                })
            
            health_data.update({
                'error_trend': error_trend,
                'monitoring_period_hours': hours
            })
            
            return Response(health_data)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def components(self, request):
        """Get health status of individual components"""
        try:
            # Get component health from circuit breakers
            circuit_breakers = error_recovery_engine.circuit_breakers
            component_health = {}
            
            for component_name, breaker in circuit_breakers.items():
                status_info = breaker.get_status()
                
                # Determine health status
                if status_info['state'] == 'open':
                    health_status = 'unhealthy'
                elif status_info['failures'] > 0:
                    health_status = 'degraded'
                else:
                    health_status = 'healthy'
                
                component_health[component_name] = {
                    'status': health_status,
                    'circuit_breaker': status_info
                }
            
            # Add error counts per component
            hours = int(request.query_params.get('hours', 24))
            since = timezone.now() - timedelta(hours=hours)
            
            from django.db import models
            
            error_counts = ErrorLog.objects.filter(
                timestamp__gte=since
            ).values('component').annotate(
                error_count=models.Count('id')
            )
            
            for error_count in error_counts:
                component = error_count['component']
                if component not in component_health:
                    component_health[component] = {'status': 'unknown'}
                
                component_health[component]['recent_errors'] = error_count['error_count']
            
            return Response({
                'components': component_health,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def reset_health(self, request):
        """Reset health status (clear circuit breakers, etc.)"""
        try:
            component = request.data.get('component')
            
            if component:
                # Reset specific component
                cache_keys = [
                    f"circuit_breaker:{component}:state",
                    f"circuit_breaker:{component}:failures",
                    f"circuit_breaker:{component}:open_time"
                ]
                
                for key in cache_keys:
                    cache.delete(key)
                
                message = f'Health status reset for component: {component}'
            else:
                # Reset all components
                circuit_breakers = error_recovery_engine.circuit_breakers
                for component_name in circuit_breakers.keys():
                    cache_keys = [
                        f"circuit_breaker:{component_name}:state",
                        f"circuit_breaker:{component_name}:failures",
                        f"circuit_breaker:{component_name}:open_time"
                    ]
                    
                    for key in cache_keys:
                        cache.delete(key)
                
                message = 'Health status reset for all components'
            
            return Response({
                'success': True,
                'message': message
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)