"""
Log Aggregation Service
Correlates log entries across frontend, backend, and database layers using correlation IDs
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.core.cache import cache
from django.conf import settings
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger('log_aggregation')

class LogLevel(Enum):
    DEBUG = 'debug'
    INFO = 'info'
    WARN = 'warn'
    ERROR = 'error'

class LogSource(Enum):
    FRONTEND = 'frontend'
    BACKEND = 'backend'
    DATABASE = 'database'
    MIDDLEWARE = 'middleware'

@dataclass
class AggregatedLogEntry:
    """Unified log entry structure"""
    timestamp: datetime
    level: LogLevel
    message: str
    source: LogSource
    correlation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    
    # Source-specific fields
    request_method: Optional[str] = None
    request_url: Optional[str] = None
    response_status: Optional[int] = None
    response_time: Optional[float] = None
    
    # Database-specific fields
    sql_query: Optional[str] = None
    query_params: Optional[Any] = None
    query_duration: Optional[float] = None
    
    # Frontend-specific fields
    user_action: Optional[str] = None
    component: Optional[str] = None
    page_url: Optional[str] = None
    user_agent: Optional[str] = None

class LogAggregationService:
    """Service for aggregating and correlating logs across all system layers"""
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'LOG_AGGREGATION_CACHE_TIMEOUT', 3600)  # 1 hour
        self.max_entries_per_correlation = getattr(settings, 'MAX_LOG_ENTRIES_PER_CORRELATION', 1000)
        
    def add_log_entry(self, entry: AggregatedLogEntry) -> None:
        """Add a log entry to the aggregation system"""
        cache_key = f"logs:{entry.correlation_id}"
        
        # Get existing entries
        existing_entries = cache.get(cache_key, [])
        
        # Add new entry
        entry_dict = asdict(entry)
        entry_dict['timestamp'] = entry.timestamp.isoformat()
        # Convert enums to their string values
        entry_dict['level'] = entry.level.value
        entry_dict['source'] = entry.source.value
        existing_entries.append(entry_dict)
        
        # Limit number of entries to prevent memory issues
        if len(existing_entries) > self.max_entries_per_correlation:
            existing_entries = existing_entries[-self.max_entries_per_correlation:]
        
        # Store back in cache
        cache.set(cache_key, existing_entries, self.cache_timeout)
        
        # Maintain an index of correlation IDs
        correlation_index = cache.get('correlation_index', set())
        correlation_index.add(entry.correlation_id)
        cache.set('correlation_index', correlation_index, self.cache_timeout)
        
        # Log the aggregated entry
        logger.info(
            f"Log aggregated: {entry.source.value} - {entry.message}",
            extra={
                'correlation_id': entry.correlation_id,
                'source': entry.source.value,
                'level': entry.level.value,
                'context': entry.context
            }
        )
    
    def get_logs_by_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific correlation ID"""
        cache_key = f"logs:{correlation_id}"
        entries = cache.get(cache_key, [])
        
        # Sort by timestamp
        entries.sort(key=lambda x: x['timestamp'])
        
        return entries
    
    def get_workflow_trace(self, correlation_id: str) -> Dict[str, Any]:
        """Get a complete workflow trace with timing and flow analysis"""
        entries = self.get_logs_by_correlation_id(correlation_id)
        
        if not entries:
            return {'correlation_id': correlation_id, 'entries': [], 'analysis': {}}
        
        # Analyze the workflow
        analysis = self._analyze_workflow(entries)
        
        return {
            'correlation_id': correlation_id,
            'entries': entries,
            'analysis': analysis,
            'total_entries': len(entries),
            'start_time': entries[0]['timestamp'] if entries else None,
            'end_time': entries[-1]['timestamp'] if entries else None
        }
    
    def _analyze_workflow(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze workflow entries for performance and error patterns"""
        analysis = {
            'total_duration': 0,
            'error_count': 0,
            'warning_count': 0,
            'database_queries': 0,
            'api_calls': 0,
            'user_interactions': 0,
            'performance_issues': [],
            'error_summary': [],
            'layer_breakdown': {}
        }
        
        start_time = None
        end_time = None
        
        for entry in entries:
            # Parse timestamp
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            
            if start_time is None:
                start_time = timestamp
            end_time = timestamp
            
            # Count by level
            level = entry.get('level', 'info')
            if level == 'error':
                analysis['error_count'] += 1
                analysis['error_summary'].append({
                    'message': entry['message'],
                    'timestamp': entry['timestamp'],
                    'source': entry['source']
                })
            elif level == 'warn':
                analysis['warning_count'] += 1
            
            # Count by source
            source = entry.get('source', 'unknown')
            if source not in analysis['layer_breakdown']:
                analysis['layer_breakdown'][source] = 0
            analysis['layer_breakdown'][source] += 1
            
            # Count specific types
            if entry.get('sql_query'):
                analysis['database_queries'] += 1
                
                # Check for slow queries
                query_duration = entry.get('query_duration', 0)
                if query_duration > 100:  # 100ms threshold
                    analysis['performance_issues'].append({
                        'type': 'slow_query',
                        'duration': query_duration,
                        'query': entry['sql_query'][:100] + '...',
                        'timestamp': entry['timestamp']
                    })
            
            if entry.get('request_method'):
                analysis['api_calls'] += 1
                
                # Check for slow API calls
                response_time = entry.get('response_time', 0)
                if response_time > 1000:  # 1 second threshold
                    analysis['performance_issues'].append({
                        'type': 'slow_api_call',
                        'duration': response_time,
                        'url': entry.get('request_url', 'unknown'),
                        'timestamp': entry['timestamp']
                    })
            
            if entry.get('user_action'):
                analysis['user_interactions'] += 1
        
        # Calculate total duration
        if start_time and end_time:
            analysis['total_duration'] = (end_time - start_time).total_seconds() * 1000  # in milliseconds
        
        return analysis
    
    def search_logs(
        self, 
        query: str, 
        level: Optional[LogLevel] = None,
        source: Optional[LogSource] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search logs across all correlation IDs"""
        # This is a simplified implementation
        # In production, you'd want to use a proper search engine like Elasticsearch
        
        results = []
        
        # Get correlation IDs from index
        correlation_index = cache.get('correlation_index', set())
        
        for correlation_id in correlation_index:
            cache_key = f"logs:{correlation_id}"
            entries = cache.get(cache_key, [])
            
            for entry in entries:
                # Apply filters
                if level and entry.get('level') != level:
                    continue
                
                if source and entry.get('source') != source:
                    continue
                
                if start_time:
                    entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    if entry_time < start_time:
                        continue
                
                if end_time:
                    entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    if entry_time > end_time:
                        continue
                
                # Search in message and context
                if query.lower() in entry.get('message', '').lower():
                    results.append(entry)
                elif entry.get('context') and query.lower() in str(entry['context']).lower():
                    results.append(entry)
                
                if len(results) >= limit:
                    break
            
            if len(results) >= limit:
                break
        
        return results[:limit]
    
    def get_error_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns across the system"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        errors = self.search_logs(
            query="",
            level='error',  # Use string instead of enum
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # Group errors by message pattern
        error_patterns = {}
        for error in errors:
            message = error.get('message', 'Unknown error')
            # Simple pattern matching - group similar error messages
            pattern_key = message[:50]  # First 50 characters as pattern
            
            if pattern_key not in error_patterns:
                error_patterns[pattern_key] = {
                    'count': 0,
                    'first_seen': error['timestamp'],
                    'last_seen': error['timestamp'],
                    'sources': set(),
                    'correlation_ids': set()
                }
            
            pattern = error_patterns[pattern_key]
            pattern['count'] += 1
            pattern['last_seen'] = error['timestamp']
            pattern['sources'].add(error.get('source', 'unknown'))
            pattern['correlation_ids'].add(error.get('correlation_id', 'unknown'))
        
        # Convert sets to lists for JSON serialization
        for pattern in error_patterns.values():
            pattern['sources'] = list(pattern['sources'])
            pattern['correlation_ids'] = list(pattern['correlation_ids'])
        
        return {
            'total_errors': len(errors),
            'unique_patterns': len(error_patterns),
            'patterns': error_patterns,
            'analysis_period': f"{hours} hours"
        }
    
    def cleanup_old_logs(self, hours: int = 24) -> int:
        """Clean up old log entries from cache"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cleaned_count = 0
        
        # Get correlation IDs from index
        correlation_index = cache.get('correlation_index', set())
        
        for correlation_id in correlation_index:
            cache_key = f"logs:{correlation_id}"
            entries = cache.get(cache_key, [])
            original_count = len(entries)
            
            # Filter out old entries
            filtered_entries = []
            for entry in entries:
                entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                if entry_time >= cutoff_time:
                    filtered_entries.append(entry)
            
            # Update cache
            if filtered_entries:
                cache.set(cache_key, filtered_entries, self.cache_timeout)
            else:
                cache.delete(cache_key)
            
            cleaned_count += original_count - len(filtered_entries)
        
        logger.info(f"Cleaned up {cleaned_count} old log entries")
        return cleaned_count

# Global aggregation service instance
log_aggregation_service = LogAggregationService()

# Helper functions for easy integration
def log_frontend_entry(
    correlation_id: str,
    level: str,
    message: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """Log a frontend entry"""
    entry = AggregatedLogEntry(
        timestamp=datetime.now(),
        level=LogLevel(level),
        message=message,
        source=LogSource.FRONTEND,
        correlation_id=correlation_id,
        user_id=user_id,
        session_id=session_id,
        context=context,
        user_action=kwargs.get('user_action'),
        component=kwargs.get('component'),
        page_url=kwargs.get('page_url'),
        user_agent=kwargs.get('user_agent')
    )
    log_aggregation_service.add_log_entry(entry)

def log_backend_entry(
    correlation_id: str,
    level: str,
    message: str,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """Log a backend entry"""
    entry = AggregatedLogEntry(
        timestamp=datetime.now(),
        level=LogLevel(level),
        message=message,
        source=LogSource.BACKEND,
        correlation_id=correlation_id,
        user_id=user_id,
        context=context,
        request_method=kwargs.get('request_method'),
        request_url=kwargs.get('request_url'),
        response_status=kwargs.get('response_status'),
        response_time=kwargs.get('response_time'),
        stack_trace=kwargs.get('stack_trace')
    )
    log_aggregation_service.add_log_entry(entry)

def log_database_entry(
    correlation_id: str,
    level: str,
    message: str,
    sql_query: Optional[str] = None,
    query_params: Optional[Any] = None,
    query_duration: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Log a database entry"""
    entry = AggregatedLogEntry(
        timestamp=datetime.now(),
        level=LogLevel(level),
        message=message,
        source=LogSource.DATABASE,
        correlation_id=correlation_id,
        context=context,
        sql_query=sql_query,
        query_params=query_params,
        query_duration=query_duration
    )
    log_aggregation_service.add_log_entry(entry)