"""
Database Query Logging System
Provides detailed logging of database queries with execution time tracking
"""

import logging
import time
from typing import Dict, List, Any, Optional
from django.db import connection
from django.conf import settings
from django.core.management.color import no_style
from django.db.backends.utils import CursorWrapper
from threading import local

# Thread-local storage for correlation IDs
_thread_local = local()

logger = logging.getLogger('db_queries')

class QueryInfo:
    """Information about a database query"""
    
    def __init__(self, sql: str, params: tuple, start_time: float):
        self.sql = sql
        self.params = params
        self.start_time = start_time
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.correlation_id: Optional[str] = None
        
    def finish(self, end_time: float) -> None:
        """Mark query as finished and calculate duration"""
        self.end_time = end_time
        self.duration = end_time - self.start_time
        self.correlation_id = getattr(_thread_local, 'correlation_id', None)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'sql': self.sql,
            'params': self.params,
            'duration_ms': round(self.duration * 1000, 2) if self.duration else None,
            'correlation_id': self.correlation_id,
            'timestamp': self.start_time
        }

class DatabaseQueryLogger:
    """Centralized database query logging"""
    
    def __init__(self):
        self.queries: List[QueryInfo] = []
        self.slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD', 0.1)  # 100ms
        
    def log_query(self, query_info: QueryInfo) -> None:
        """Log a completed query"""
        self.queries.append(query_info)
        
        # Log slow queries
        if query_info.duration and query_info.duration > self.slow_query_threshold:
            logger.warning(
                f"Slow query detected: {query_info.duration:.3f}s",
                extra={
                    'query_info': query_info.to_dict(),
                    'correlation_id': query_info.correlation_id
                }
            )
        
        # Log all queries in debug mode
        if settings.DEBUG:
            logger.debug(
                f"Query executed: {query_info.sql[:100]}...",
                extra={
                    'query_info': query_info.to_dict(),
                    'correlation_id': query_info.correlation_id
                }
            )
    
    def get_queries_for_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get all queries for a specific correlation ID"""
        return [
            query.to_dict() 
            for query in self.queries 
            if query.correlation_id == correlation_id
        ]
    
    def get_slow_queries(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get all slow queries above threshold"""
        threshold = threshold or self.slow_query_threshold
        return [
            query.to_dict()
            for query in self.queries
            if query.duration and query.duration > threshold
        ]
    
    def clear_queries(self) -> None:
        """Clear stored queries"""
        self.queries.clear()

# Global query logger instance
query_logger = DatabaseQueryLogger()

class LoggingCursorWrapper(CursorWrapper):
    """Cursor wrapper that logs all database queries"""
    
    def execute(self, sql, params=None):
        query_info = QueryInfo(sql, params or (), time.time())
        
        try:
            result = super().execute(sql, params)
            query_info.finish(time.time())
            query_logger.log_query(query_info)
            return result
        except Exception as e:
            query_info.finish(time.time())
            query_info.error = str(e)
            query_logger.log_query(query_info)
            raise
    
    def executemany(self, sql, param_list):
        query_info = QueryInfo(sql, f"BATCH({len(param_list)} items)", time.time())
        
        try:
            result = super().executemany(sql, param_list)
            query_info.finish(time.time())
            query_logger.log_query(query_info)
            return result
        except Exception as e:
            query_info.finish(time.time())
            query_info.error = str(e)
            query_logger.log_query(query_info)
            raise

def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current thread"""
    _thread_local.correlation_id = correlation_id

def get_correlation_id() -> Optional[str]:
    """Get correlation ID for current thread"""
    return getattr(_thread_local, 'correlation_id', None)

def clear_correlation_id() -> None:
    """Clear correlation ID for current thread"""
    if hasattr(_thread_local, 'correlation_id'):
        delattr(_thread_local, 'correlation_id')

class DatabaseLoggingMiddleware:
    """Middleware to enable database query logging with correlation IDs"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Set correlation ID from request
        correlation_id = getattr(request, 'correlation_id', None)
        if correlation_id:
            set_correlation_id(correlation_id)
        
        # Patch database cursor for this request
        original_cursor = connection.cursor
        connection.cursor = lambda: LoggingCursorWrapper(original_cursor().cursor, connection)
        
        try:
            response = self.get_response(request)
            
            # Add query count to response headers in debug mode
            if settings.DEBUG:
                query_count = len(connection.queries)
                response['X-DB-Query-Count'] = str(query_count)
                
                # Log summary
                total_time = sum(float(q['time']) for q in connection.queries)
                logger.info(
                    f"Request completed: {query_count} queries, {total_time:.3f}s total",
                    extra={
                        'correlation_id': correlation_id,
                        'query_count': query_count,
                        'total_query_time': total_time
                    }
                )
            
            return response
        finally:
            # Restore original cursor
            connection.cursor = original_cursor
            clear_correlation_id()

# Query analysis utilities
class QueryAnalyzer:
    """Analyze database queries for performance issues"""
    
    @staticmethod
    def detect_n_plus_one(queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect potential N+1 query problems"""
        n_plus_one_patterns = []
        
        # Group similar queries
        query_groups = {}
        for query in queries:
            # Normalize SQL by removing specific IDs
            normalized_sql = query['sql']
            # Simple normalization - replace numbers with placeholder
            import re
            normalized_sql = re.sub(r'\b\d+\b', '?', normalized_sql)
            
            if normalized_sql not in query_groups:
                query_groups[normalized_sql] = []
            query_groups[normalized_sql].append(query)
        
        # Find groups with many similar queries
        for sql, group_queries in query_groups.items():
            if len(group_queries) > 5:  # Threshold for N+1 detection
                n_plus_one_patterns.append({
                    'pattern': sql,
                    'count': len(group_queries),
                    'total_time': sum(q.get('duration_ms', 0) for q in group_queries),
                    'queries': group_queries
                })
        
        return n_plus_one_patterns
    
    @staticmethod
    def get_slow_query_summary(queries: List[Dict[str, Any]], threshold: float = 100) -> Dict[str, Any]:
        """Get summary of slow queries"""
        slow_queries = [q for q in queries if q.get('duration_ms', 0) > threshold]
        
        return {
            'total_queries': len(queries),
            'slow_queries': len(slow_queries),
            'slowest_query': max(slow_queries, key=lambda q: q.get('duration_ms', 0)) if slow_queries else None,
            'total_slow_time': sum(q.get('duration_ms', 0) for q in slow_queries),
            'slow_query_details': slow_queries
        }