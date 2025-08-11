# Performance Automation and Self-Healing
import asyncio
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.management import call_command
from django.conf import settings
import json

from .models import PerformanceMetric, PerformanceAlert, PerformanceIncident
from .utils import AlertManager, PerformanceAnalyzer

logger = logging.getLogger(__name__)

class PerformanceAutomation:
    """Automated performance management and self-healing"""
    
    def __init__(self):
        self.automation_rules = {
            'auto_scaling': {
                'cpu_threshold': 80,
                'memory_threshold': 85,
                'scale_up_cooldown': 300,  # 5 minutes
                'scale_down_cooldown': 600  # 10 minutes
            },
            'cache_management': {
                'hit_rate_threshold': 85,
                'memory_threshold': 90,
                'auto_clear_enabled': True
            },
            'database_optimization': {
                'slow_query_threshold': 1000,  # ms
                'connection_threshold': 80,
                'auto_index_enabled': True
            },
            'alert_suppression': {
                'duplicate_window': 300,  # 5 minutes
                'escalation_threshold': 3
            }
        }
    
    async def run_automation_cycle(self):
        """Run complete automation cycle"""
        logger.info("Starting performance automation cycle")
        
        try:
            # Check for performance issues
            issues = await self._detect_performance_issues()
            
            # Apply automated fixes
            for issue in issues:
                await self._apply_automated_fix(issue)
            
            # Perform preventive maintenance
            await self._perform_preventive_maintenance()
            
            # Update automation metrics
            await self._update_automation_metrics()
            
            logger.info("Performance automation cycle completed successfully")
            
        except Exception as e:
            logger.error(f"Error in automation cycle: {str(e)}")
            await self._handle_automation_error(e)
    
    async def _detect_performance_issues(self):
        """Detect performance issues that can be automatically resolved"""
        issues = []
        
        # Check CPU usage
        cpu_issue = await self._check_cpu_usage()
        if cpu_issue:
            issues.append(cpu_issue)
        
        # Check memory usage
        memory_issue = await self._check_memory_usage()
        if memory_issue:
            issues.append(memory_issue)
        
        # Check database performance
        db_issue = await self._check_database_performance()
        if db_issue:
            issues.append(db_issue)
        
        # Check cache performance
        cache_issue = await self._check_cache_performance()
        if cache_issue:
            issues.append(cache_issue)
        
        return issues
    
    async def _check_cpu_usage(self):
        """Check CPU usage and detect scaling needs"""
        recent_cpu_metrics = PerformanceMetric.objects.filter(
            metric_type='cpu_usage',
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).order_by('-timestamp')[:10]
        
        if not recent_cpu_metrics:
            return None
        
        avg_cpu = sum(metric.value for metric in recent_cpu_metrics) / len(recent_cpu_metrics)
        
        if avg_cpu > self.automation_rules['auto_scaling']['cpu_threshold']:
            return {
                'type': 'high_cpu_usage',
                'severity': 'high' if avg_cpu > 90 else 'medium',
                'current_value': avg_cpu,
                'threshold': self.automation_rules['auto_scaling']['cpu_threshold'],
                'action': 'scale_up',
                'automated': True
            }
        
        return None
    
    async def _check_memory_usage(self):
        """Check memory usage and detect scaling needs"""
        recent_memory_metrics = PerformanceMetric.objects.filter(
            metric_type='memory_usage',
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).order_by('-timestamp')[:10]
        
        if not recent_memory_metrics:
            return None
        
        avg_memory = sum(metric.value for metric in recent_memory_metrics) / len(recent_memory_metrics)
        
        if avg_memory > self.automation_rules['auto_scaling']['memory_threshold']:
            return {
                'type': 'high_memory_usage',
                'severity': 'high' if avg_memory > 95 else 'medium',
                'current_value': avg_memory,
                'threshold': self.automation_rules['auto_scaling']['memory_threshold'],
                'action': 'scale_up',
                'automated': True
            }
        
        return None
    
    async def _check_database_performance(self):
        """Check database performance issues"""
        from .models import DatabasePerformanceLog
        
        recent_slow_queries = DatabasePerformanceLog.objects.filter(
            is_slow_query=True,
            timestamp__gte=timezone.now() - timedelta(minutes=10)
        ).count()
        
        if recent_slow_queries > 5:  # More than 5 slow queries in 10 minutes
            return {
                'type': 'database_performance',
                'severity': 'medium',
                'slow_query_count': recent_slow_queries,
                'action': 'optimize_database',
                'automated': True
            }
        
        return None
    
    async def _check_cache_performance(self):
        """Check cache performance issues"""
        # Mock cache hit rate check
        cache_hit_rate = 82  # This would come from actual cache metrics
        
        if cache_hit_rate < self.automation_rules['cache_management']['hit_rate_threshold']:
            return {
                'type': 'low_cache_hit_rate',
                'severity': 'medium',
                'current_value': cache_hit_rate,
                'threshold': self.automation_rules['cache_management']['hit_rate_threshold'],
                'action': 'optimize_cache',
                'automated': True
            }
        
        return None
    
    async def _apply_automated_fix(self, issue):
        """Apply automated fix for detected issue"""
        logger.info(f"Applying automated fix for issue: {issue['type']}")
        
        try:
            if issue['action'] == 'scale_up':
                await self._auto_scale_up(issue)
            elif issue['action'] == 'optimize_database':
                await self._auto_optimize_database(issue)
            elif issue['action'] == 'optimize_cache':
                await self._auto_optimize_cache(issue)
            
            # Log the automated action
            await self._log_automated_action(issue, 'success')
            
        except Exception as e:
            logger.error(f"Failed to apply automated fix: {str(e)}")
            await self._log_automated_action(issue, 'failed', str(e))
    
    async def _auto_scale_up(self, issue):
        """Automatically scale up resources"""
        # This would integrate with cloud provider APIs
        logger.info(f"Auto-scaling triggered for {issue['type']}")
        
        # Mock scaling action
        scaling_result = {
            'action': 'scale_up',
            'resource_type': issue['type'].replace('high_', '').replace('_usage', ''),
            'previous_capacity': 2,
            'new_capacity': 3,
            'timestamp': timezone.now()
        }
        
        # Create performance metric to track scaling
        PerformanceMetric.objects.create(
            metric_type='auto_scaling',
            name=f"Auto Scale Up - {issue['type']}",
            value=scaling_result['new_capacity'],
            unit='instances',
            source='automation',
            metadata={
                'scaling_result': scaling_result,
                'trigger_issue': issue
            }
        )
        
        return scaling_result
    
    async def _auto_optimize_database(self, issue):
        """Automatically optimize database performance"""
        logger.info("Auto-optimizing database performance")
        
        # Run database optimization commands
        optimization_actions = []
        
        # Update table statistics
        try:
            # This would run actual database optimization commands
            optimization_actions.append({
                'action': 'update_statistics',
                'status': 'completed',
                'timestamp': timezone.now()
            })
        except Exception as e:
            optimization_actions.append({
                'action': 'update_statistics',
                'status': 'failed',
                'error': str(e),
                'timestamp': timezone.now()
            })
        
        # Clear query cache
        try:
            optimization_actions.append({
                'action': 'clear_query_cache',
                'status': 'completed',
                'timestamp': timezone.now()
            })
        except Exception as e:
            optimization_actions.append({
                'action': 'clear_query_cache',
                'status': 'failed',
                'error': str(e),
                'timestamp': timezone.now()
            })
        
        # Log optimization actions
        PerformanceMetric.objects.create(
            metric_type='database_optimization',
            name='Auto Database Optimization',
            value=len([a for a in optimization_actions if a['status'] == 'completed']),
            unit='actions',
            source='automation',
            metadata={
                'optimization_actions': optimization_actions,
                'trigger_issue': issue
            }
        )
        
        return optimization_actions
    
    async def _auto_optimize_cache(self, issue):
        """Automatically optimize cache performance"""
        logger.info("Auto-optimizing cache performance")
        
        cache_actions = []
        
        # Clear expired cache entries
        try:
            # This would integrate with actual cache system
            cache_actions.append({
                'action': 'clear_expired_entries',
                'status': 'completed',
                'entries_cleared': 1250,
                'timestamp': timezone.now()
            })
        except Exception as e:
            cache_actions.append({
                'action': 'clear_expired_entries',
                'status': 'failed',
                'error': str(e),
                'timestamp': timezone.now()
            })
        
        # Warm up frequently accessed data
        try:
            cache_actions.append({
                'action': 'warm_up_cache',
                'status': 'completed',
                'entries_warmed': 500,
                'timestamp': timezone.now()
            })
        except Exception as e:
            cache_actions.append({
                'action': 'warm_up_cache',
                'status': 'failed',
                'error': str(e),
                'timestamp': timezone.now()
            })
        
        # Log cache optimization
        PerformanceMetric.objects.create(
            metric_type='cache_optimization',
            name='Auto Cache Optimization',
            value=sum(a.get('entries_cleared', 0) + a.get('entries_warmed', 0) for a in cache_actions),
            unit='entries',
            source='automation',
            metadata={
                'cache_actions': cache_actions,
                'trigger_issue': issue
            }
        )
        
        return cache_actions
    
    async def _perform_preventive_maintenance(self):
        """Perform preventive maintenance tasks"""
        logger.info("Performing preventive maintenance")
        
        maintenance_tasks = []
        
        # Clean up old performance data
        try:
            call_command('cleanup_performance_data')
            maintenance_tasks.append({
                'task': 'cleanup_performance_data',
                'status': 'completed',
                'timestamp': timezone.now()
            })
        except Exception as e:
            maintenance_tasks.append({
                'task': 'cleanup_performance_data',
                'status': 'failed',
                'error': str(e),
                'timestamp': timezone.now()
            })
        
        # Collect system metrics
        try:
            call_command('collect_system_metrics')
            maintenance_tasks.append({
                'task': 'collect_system_metrics',
                'status': 'completed',
                'timestamp': timezone.now()
            })
        except Exception as e:
            maintenance_tasks.append({
                'task': 'collect_system_metrics',
                'status': 'failed',
                'error': str(e),
                'timestamp': timezone.now()
            })
        
        # Check performance alerts
        try:
            call_command('check_performance_alerts')
            maintenance_tasks.append({
                'task': 'check_performance_alerts',
                'status': 'completed',
                'timestamp': timezone.now()
            })
        except Exception as e:
            maintenance_tasks.append({
                'task': 'check_performance_alerts',
                'status': 'failed',
                'error': str(e),
                'timestamp': timezone.now()
            })
        
        # Log maintenance completion
        PerformanceMetric.objects.create(
            metric_type='preventive_maintenance',
            name='Automated Preventive Maintenance',
            value=len([t for t in maintenance_tasks if t['status'] == 'completed']),
            unit='tasks',
            source='automation',
            metadata={'maintenance_tasks': maintenance_tasks}
        )
        
        return maintenance_tasks
    
    async def _update_automation_metrics(self):
        """Update automation performance metrics"""
        # Calculate automation effectiveness
        recent_incidents = PerformanceIncident.objects.filter(
            started_at__gte=timezone.now() - timedelta(days=1)
        )
        
        auto_resolved = recent_incidents.filter(
            resolution__icontains='automated'
        ).count()
        
        total_incidents = recent_incidents.count()
        
        automation_effectiveness = (auto_resolved / total_incidents * 100) if total_incidents > 0 else 0
        
        PerformanceMetric.objects.create(
            metric_type='automation_effectiveness',
            name='Automation Effectiveness',
            value=automation_effectiveness,
            unit='percentage',
            source='automation',
            metadata={
                'auto_resolved_incidents': auto_resolved,
                'total_incidents': total_incidents,
                'period': '24_hours'
            }
        )
    
    async def _log_automated_action(self, issue, status, error_message=None):
        """Log automated action for audit trail"""
        log_data = {
            'timestamp': timezone.now(),
            'issue': issue,
            'status': status,
            'error_message': error_message
        }
        
        PerformanceMetric.objects.create(
            metric_type='automated_action',
            name=f"Automated Action - {issue['type']}",
            value=1 if status == 'success' else 0,
            unit='action',
            source='automation',
            metadata=log_data
        )
    
    async def _handle_automation_error(self, error):
        """Handle automation system errors"""
        logger.error(f"Automation system error: {str(error)}")
        
        # Create incident for automation failure
        PerformanceIncident.objects.create(
            incident_id=f"AUTO-{int(timezone.now().timestamp())}",
            title="Performance Automation System Error",
            description=f"Automation system encountered an error: {str(error)}",
            incident_type='error_spike',
            severity='high',
            affected_services=['automation'],
            timeline=[{
                'timestamp': timezone.now().isoformat(),
                'action': 'automation_error',
                'error': str(error),
                'user': 'system'
            }]
        )


class SelfHealingSystem:
    """Self-healing performance management"""
    
    def __init__(self):
        self.healing_strategies = {
            'memory_leak': {
                'detection_threshold': 90,
                'action': 'restart_service',
                'cooldown': 1800  # 30 minutes
            },
            'connection_pool_exhaustion': {
                'detection_threshold': 95,
                'action': 'reset_connections',
                'cooldown': 300  # 5 minutes
            },
            'disk_space_low': {
                'detection_threshold': 90,
                'action': 'cleanup_logs',
                'cooldown': 3600  # 1 hour
            },
            'high_error_rate': {
                'detection_threshold': 5,  # 5% error rate
                'action': 'circuit_breaker',
                'cooldown': 600  # 10 minutes
            }
        }
        
        self.last_healing_actions = {}
    
    async def monitor_and_heal(self):
        """Monitor system health and apply healing actions"""
        logger.info("Starting self-healing monitoring")
        
        healing_actions = []
        
        for issue_type, strategy in self.healing_strategies.items():
            if await self._should_apply_healing(issue_type, strategy):
                action_result = await self._apply_healing_action(issue_type, strategy)
                healing_actions.append(action_result)
        
        # Log healing summary
        if healing_actions:
            PerformanceMetric.objects.create(
                metric_type='self_healing',
                name='Self-Healing Actions',
                value=len(healing_actions),
                unit='actions',
                source='self_healing',
                metadata={'healing_actions': healing_actions}
            )
        
        return healing_actions
    
    async def _should_apply_healing(self, issue_type, strategy):
        """Check if healing action should be applied"""
        # Check cooldown period
        last_action_time = self.last_healing_actions.get(issue_type)
        if last_action_time:
            time_since_last = (timezone.now() - last_action_time).total_seconds()
            if time_since_last < strategy['cooldown']:
                return False
        
        # Check if issue is present
        return await self._detect_issue(issue_type, strategy)
    
    async def _detect_issue(self, issue_type, strategy):
        """Detect if specific issue is present"""
        if issue_type == 'memory_leak':
            return await self._detect_memory_leak(strategy['detection_threshold'])
        elif issue_type == 'connection_pool_exhaustion':
            return await self._detect_connection_exhaustion(strategy['detection_threshold'])
        elif issue_type == 'disk_space_low':
            return await self._detect_low_disk_space(strategy['detection_threshold'])
        elif issue_type == 'high_error_rate':
            return await self._detect_high_error_rate(strategy['detection_threshold'])
        
        return False
    
    async def _detect_memory_leak(self, threshold):
        """Detect memory leak patterns"""
        # Get memory usage trend over last hour
        memory_metrics = PerformanceMetric.objects.filter(
            metric_type='memory_usage',
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).order_by('timestamp')
        
        if len(memory_metrics) < 10:
            return False
        
        # Check if memory usage is consistently increasing
        values = [m.value for m in memory_metrics]
        recent_avg = sum(values[-5:]) / 5
        
        return recent_avg > threshold
    
    async def _detect_connection_exhaustion(self, threshold):
        """Detect database connection pool exhaustion"""
        # Mock implementation - would check actual connection pool metrics
        return False
    
    async def _detect_low_disk_space(self, threshold):
        """Detect low disk space"""
        disk_metrics = PerformanceMetric.objects.filter(
            metric_type='disk_usage',
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).order_by('-timestamp')[:1]
        
        if not disk_metrics:
            return False
        
        return disk_metrics[0].value > threshold
    
    async def _detect_high_error_rate(self, threshold):
        """Detect high error rate"""
        recent_errors = PerformanceMetric.objects.filter(
            metric_type='error_rate',
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        recent_requests = PerformanceMetric.objects.filter(
            metric_type='response_time',
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        if recent_requests == 0:
            return False
        
        error_rate = (recent_errors / recent_requests) * 100
        return error_rate > threshold
    
    async def _apply_healing_action(self, issue_type, strategy):
        """Apply healing action for detected issue"""
        logger.info(f"Applying self-healing action for {issue_type}")
        
        action_result = {
            'issue_type': issue_type,
            'action': strategy['action'],
            'timestamp': timezone.now(),
            'status': 'attempted'
        }
        
        try:
            if strategy['action'] == 'restart_service':
                result = await self._restart_service()
            elif strategy['action'] == 'reset_connections':
                result = await self._reset_connections()
            elif strategy['action'] == 'cleanup_logs':
                result = await self._cleanup_logs()
            elif strategy['action'] == 'circuit_breaker':
                result = await self._activate_circuit_breaker()
            else:
                result = {'status': 'unknown_action'}
            
            action_result.update(result)
            action_result['status'] = 'completed'
            
            # Update last action time
            self.last_healing_actions[issue_type] = timezone.now()
            
        except Exception as e:
            action_result['status'] = 'failed'
            action_result['error'] = str(e)
            logger.error(f"Self-healing action failed: {str(e)}")
        
        return action_result
    
    async def _restart_service(self):
        """Restart service to resolve memory leaks"""
        # Mock implementation - would restart actual service
        logger.info("Restarting service for memory leak resolution")
        return {
            'action_details': 'Service restart initiated',
            'expected_downtime': '30 seconds'
        }
    
    async def _reset_connections(self):
        """Reset database connections"""
        # Mock implementation - would reset actual connection pool
        logger.info("Resetting database connections")
        return {
            'action_details': 'Database connections reset',
            'connections_reset': 25
        }
    
    async def _cleanup_logs(self):
        """Clean up log files to free disk space"""
        # Mock implementation - would clean actual log files
        logger.info("Cleaning up log files")
        return {
            'action_details': 'Log files cleaned',
            'space_freed': '2.5 GB'
        }
    
    async def _activate_circuit_breaker(self):
        """Activate circuit breaker for high error rates"""
        # Mock implementation - would activate actual circuit breaker
        logger.info("Activating circuit breaker")
        return {
            'action_details': 'Circuit breaker activated',
            'duration': '5 minutes'
        }