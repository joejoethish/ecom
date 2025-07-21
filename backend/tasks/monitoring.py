"""
Task monitoring and retry logic for the e-commerce platform.
"""
import logging
from typing import Dict, Any, Optional, List
from celery import shared_task, current_task
from celery.exceptions import Retry
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.core.cache import cache
import json
import traceback

logger = logging.getLogger(__name__)


class TaskMonitor:
    """
    Task monitoring utility for tracking task execution and failures.
    """
    
    @staticmethod
    def log_task_start(task_name: str, task_id: str, args: tuple = None, kwargs: dict = None):
        """
        Log task start.
        
        Args:
            task_name: Name of the task
            task_id: Unique task ID
            args: Task arguments
            kwargs: Task keyword arguments
        """
        logger.info(f"Task {task_name} started with ID {task_id}")
        
        # Store task execution info in cache for monitoring
        task_info = {
            'task_name': task_name,
            'task_id': task_id,
            'started_at': timezone.now().isoformat(),
            'args': str(args) if args else None,
            'kwargs': str(kwargs) if kwargs else None,
            'status': 'STARTED'
        }
        
        cache.set(f"task_info:{task_id}", task_info, timeout=3600)  # 1 hour
        
        # Update task statistics
        TaskMonitor._update_task_stats(task_name, 'started')
    
    @staticmethod
    def log_task_success(task_name: str, task_id: str, result: Any = None):
        """
        Log task success.
        
        Args:
            task_name: Name of the task
            task_id: Unique task ID
            result: Task result
        """
        logger.info(f"Task {task_name} completed successfully with ID {task_id}")
        
        # Update task info in cache
        task_info = cache.get(f"task_info:{task_id}", {})
        task_info.update({
            'completed_at': timezone.now().isoformat(),
            'status': 'SUCCESS',
            'result': str(result) if result else None
        })
        cache.set(f"task_info:{task_id}", task_info, timeout=3600)
        
        # Update task statistics
        TaskMonitor._update_task_stats(task_name, 'success')
    
    @staticmethod
    def log_task_failure(task_name: str, task_id: str, error: Exception, retry_count: int = 0):
        """
        Log task failure.
        
        Args:
            task_name: Name of the task
            task_id: Unique task ID
            error: Exception that caused the failure
            retry_count: Current retry count
        """
        logger.error(f"Task {task_name} failed with ID {task_id}: {str(error)}")
        
        # Update task info in cache
        task_info = cache.get(f"task_info:{task_id}", {})
        task_info.update({
            'failed_at': timezone.now().isoformat(),
            'status': 'FAILURE',
            'error': str(error),
            'traceback': traceback.format_exc(),
            'retry_count': retry_count
        })
        cache.set(f"task_info:{task_id}", task_info, timeout=3600)
        
        # Update task statistics
        TaskMonitor._update_task_stats(task_name, 'failure')
    
    @staticmethod
    def log_task_retry(task_name: str, task_id: str, error: Exception, retry_count: int):
        """
        Log task retry.
        
        Args:
            task_name: Name of the task
            task_id: Unique task ID
            error: Exception that caused the retry
            retry_count: Current retry count
        """
        logger.warning(f"Task {task_name} retry #{retry_count} with ID {task_id}: {str(error)}")
        
        # Update task info in cache
        task_info = cache.get(f"task_info:{task_id}", {})
        task_info.update({
            'last_retry_at': timezone.now().isoformat(),
            'status': 'RETRY',
            'last_error': str(error),
            'retry_count': retry_count
        })
        cache.set(f"task_info:{task_id}", task_info, timeout=3600)
        
        # Update task statistics
        TaskMonitor._update_task_stats(task_name, 'retry')
    
    @staticmethod
    def _update_task_stats(task_name: str, event_type: str):
        """
        Update task statistics in cache.
        
        Args:
            task_name: Name of the task
            event_type: Type of event (started, success, failure, retry)
        """
        stats_key = f"task_stats:{task_name}"
        stats = cache.get(stats_key, {
            'started': 0,
            'success': 0,
            'failure': 0,
            'retry': 0,
            'last_updated': timezone.now().isoformat()
        })
        
        stats[event_type] = stats.get(event_type, 0) + 1
        stats['last_updated'] = timezone.now().isoformat()
        
        cache.set(stats_key, stats, timeout=86400)  # 24 hours
    
    @staticmethod
    def get_task_info(task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task information by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task information dictionary or None
        """
        return cache.get(f"task_info:{task_id}")
    
    @staticmethod
    def get_task_stats(task_name: str) -> Optional[Dict[str, Any]]:
        """
        Get task statistics by name.
        
        Args:
            task_name: Task name
            
        Returns:
            Task statistics dictionary or None
        """
        return cache.get(f"task_stats:{task_name}")
    
    @staticmethod
    def get_all_task_stats() -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all tasks.
        
        Returns:
            Dictionary of task statistics
        """
        # This would require scanning cache keys, simplified implementation
        # In production, consider using a proper monitoring solution
        return {}


class TaskRetryHandler:
    """
    Handles task retry logic with exponential backoff.
    """
    
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_COUNTDOWN = 60  # seconds
    DEFAULT_MAX_COUNTDOWN = 3600  # 1 hour
    
    @staticmethod
    def should_retry(exception: Exception, retry_count: int, max_retries: int = None) -> bool:
        """
        Determine if a task should be retried based on the exception and retry count.
        
        Args:
            exception: The exception that occurred
            retry_count: Current retry count
            max_retries: Maximum number of retries allowed
            
        Returns:
            True if task should be retried, False otherwise
        """
        if max_retries is None:
            max_retries = TaskRetryHandler.DEFAULT_MAX_RETRIES
        
        if retry_count >= max_retries:
            return False
        
        # Don't retry certain types of errors
        non_retryable_errors = (
            ValueError,  # Invalid data
            TypeError,   # Programming errors
            AttributeError,  # Programming errors
        )
        
        if isinstance(exception, non_retryable_errors):
            return False
        
        return True
    
    @staticmethod
    def calculate_countdown(retry_count: int, base_countdown: int = None) -> int:
        """
        Calculate countdown for next retry using exponential backoff.
        
        Args:
            retry_count: Current retry count
            base_countdown: Base countdown in seconds
            
        Returns:
            Countdown in seconds for next retry
        """
        if base_countdown is None:
            base_countdown = TaskRetryHandler.DEFAULT_COUNTDOWN
        
        # Exponential backoff: base * (2 ^ retry_count)
        countdown = base_countdown * (2 ** retry_count)
        
        # Cap at maximum countdown
        return min(countdown, TaskRetryHandler.DEFAULT_MAX_COUNTDOWN)
    
    @staticmethod
    def retry_task(task, exception: Exception, retry_count: int = None, max_retries: int = None, countdown: int = None):
        """
        Retry a task with proper logging and backoff.
        
        Args:
            task: Celery task instance
            exception: Exception that caused the retry
            retry_count: Current retry count
            max_retries: Maximum retries allowed
            countdown: Countdown for next retry
        """
        if retry_count is None:
            retry_count = task.request.retries
        
        if max_retries is None:
            max_retries = TaskRetryHandler.DEFAULT_MAX_RETRIES
        
        if not TaskRetryHandler.should_retry(exception, retry_count, max_retries):
            TaskMonitor.log_task_failure(
                task.name, 
                task.request.id, 
                exception, 
                retry_count
            )
            raise exception
        
        if countdown is None:
            countdown = TaskRetryHandler.calculate_countdown(retry_count)
        
        TaskMonitor.log_task_retry(
            task.name,
            task.request.id,
            exception,
            retry_count + 1
        )
        
        raise task.retry(
            exc=exception,
            countdown=countdown,
            max_retries=max_retries
        )


def task_monitor_decorator(func):
    """
    Decorator to add monitoring to Celery tasks.
    """
    def wrapper(*args, **kwargs):
        task_id = current_task.request.id if current_task else 'unknown'
        task_name = func.__name__
        
        TaskMonitor.log_task_start(task_name, task_id, args, kwargs)
        
        try:
            result = func(*args, **kwargs)
            TaskMonitor.log_task_success(task_name, task_id, result)
            return result
        except Exception as e:
            if isinstance(e, Retry):
                # This is a retry, don't log as failure
                raise
            
            TaskMonitor.log_task_failure(task_name, task_id, e)
            raise
    
    return wrapper


class TaskHealthChecker:
    """
    Monitors task health and provides alerts.
    """
    
    @staticmethod
    def check_task_health(task_name: str) -> Dict[str, Any]:
        """
        Check health of a specific task.
        
        Args:
            task_name: Name of the task to check
            
        Returns:
            Health status dictionary
        """
        stats = TaskMonitor.get_task_stats(task_name)
        
        if not stats:
            return {
                'status': 'unknown',
                'message': 'No statistics available'
            }
        
        total_executions = stats.get('started', 0)
        failures = stats.get('failure', 0)
        
        if total_executions == 0:
            return {
                'status': 'idle',
                'message': 'No recent executions'
            }
        
        failure_rate = failures / total_executions if total_executions > 0 else 0
        
        if failure_rate > 0.5:  # More than 50% failure rate
            return {
                'status': 'critical',
                'message': f'High failure rate: {failure_rate:.2%}',
                'failure_rate': failure_rate,
                'stats': stats
            }
        elif failure_rate > 0.2:  # More than 20% failure rate
            return {
                'status': 'warning',
                'message': f'Elevated failure rate: {failure_rate:.2%}',
                'failure_rate': failure_rate,
                'stats': stats
            }
        else:
            return {
                'status': 'healthy',
                'message': 'Task is performing well',
                'failure_rate': failure_rate,
                'stats': stats
            }
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """
        Get overall system health for all tasks.
        
        Returns:
            System health summary
        """
        # This would scan all task statistics
        # Simplified implementation for now
        return {
            'status': 'healthy',
            'message': 'System monitoring active',
            'timestamp': timezone.now().isoformat()
        }