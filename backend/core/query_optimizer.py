"""
Query Optimization and Performance Tuning System for MySQL Integration

This module provides comprehensive query optimization capabilities including:
- Query analysis and optimization recommendations
- Slow query detection and monitoring
- Index usage analysis and recommendations
- Query performance benchmarking
- Caching strategies for frequently accessed data
"""

import logging
import hashlib
import time
import json
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
from contextlib import contextmanager

from django.db import connections, connection
from django.db.utils import OperationalError, DatabaseError
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.db.models import QuerySet
from django.db.models.sql import Query

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Query performance metrics data structure"""
    query_hash: str
    query_text: str
    execution_time: float
    rows_examined: int
    rows_sent: int
    database_alias: str
    timestamp: datetime
    
    # Analysis results
    optimization_suggestions: List[str] = field(default_factory=list)
    severity: str = 'low'  # low, medium, high, critical
    frequency: int = 1
    index_usage: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class IndexRecommendation:
    """Index recommendation data structure"""
    table_name: str
    columns: List[str]
    index_type: str  # btree, hash, fulltext
    reason: str
    estimated_benefit: str  # low, medium, high
    query_patterns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class CacheStrategy:
    """Cache strategy configuration"""
    cache_key_pattern: str
    cache_timeout: int
    cache_backend: str = 'default'
    invalidation_triggers: List[str] = field(default_factory=list)
    hit_rate_threshold: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class QueryAnalyzer:
    """Advanced query analysis and optimization recommendations"""
    
    def __init__(self):
        self.query_patterns = {}
        self.optimization_rules = self._load_optimization_rules()
        self.index_recommendations = {}
        self.performance_baselines = {}
        
    def _load_optimization_rules(self) -> Dict[str, List[str]]:
        """Load query optimization rules"""
        return {
            'missing_index': [
                "Consider adding an index on frequently queried columns",
                "Use EXPLAIN to analyze query execution plan",
                "Check for table scans in WHERE clauses",
                "Add composite indexes for multi-column WHERE conditions"
            ],
            'inefficient_join': [
                "Optimize JOIN conditions with proper indexing",
                "Consider using EXISTS instead of IN for subqueries",
                "Ensure JOIN columns have matching data types",
                "Use INNER JOIN instead of WHERE for better performance",
                "Consider denormalization for frequently joined tables"
            ],
            'large_result_set': [
                "Add LIMIT clause to reduce result set size",
                "Consider pagination for large datasets",
                "Use appropriate WHERE conditions to filter results",
                "Implement result set streaming for very large queries"
            ],
            'subquery_optimization': [
                "Convert correlated subqueries to JOINs where possible",
                "Use EXISTS instead of IN for better performance",
                "Consider using temporary tables for complex subqueries",
                "Cache subquery results when appropriate"
            ],
            'function_in_where': [
                "Avoid using functions in WHERE clauses",
                "Create functional indexes if functions are necessary",
                "Rewrite queries to use sargable predicates",
                "Pre-compute function results in separate columns"
            ],
            'order_by_optimization': [
                "Add indexes on ORDER BY columns",
                "Consider using covering indexes for ORDER BY queries",
                "Limit result sets before ordering when possible",
                "Use composite indexes for multi-column ORDER BY"
            ],
            'group_by_optimization': [
                "Add indexes on GROUP BY columns",
                "Consider using covering indexes for GROUP BY queries",
                "Use HAVING clause efficiently",
                "Pre-aggregate data in summary tables when appropriate"
            ],
            'like_optimization': [
                "Use full-text search for text searching",
                "Avoid leading wildcards in LIKE patterns",
                "Consider using specialized search engines for complex text queries",
                "Use prefix indexes for long text columns"
            ]
        }
    
    def analyze_query(self, query_text: str, execution_time: float, 
                     rows_examined: int, rows_sent: int, 
                     database_alias: str = 'default') -> QueryMetrics:
        """Analyze a query and provide optimization suggestions"""
        query_hash = self._generate_query_hash(query_text)
        suggestions = []
        severity = self._calculate_severity(execution_time, rows_examined, rows_sent)
        
        # Analyze query patterns
        query_upper = query_text.upper()
        
        if self._has_missing_index_pattern(query_text):
            suggestions.extend(self.optimization_rules['missing_index'])
        
        if self._has_inefficient_join_pattern(query_text):
            suggestions.extend(self.optimization_rules['inefficient_join'])
        
        if rows_examined > 10000:
            suggestions.extend(self.optimization_rules['large_result_set'])
        
        if self._has_subquery_pattern(query_text):
            suggestions.extend(self.optimization_rules['subquery_optimization'])
        
        if self._has_function_in_where_pattern(query_text):
            suggestions.extend(self.optimization_rules['function_in_where'])
        
        if 'ORDER BY' in query_upper and not 'LIMIT' in query_upper:
            suggestions.extend(self.optimization_rules['order_by_optimization'])
        
        if 'GROUP BY' in query_upper:
            suggestions.extend(self.optimization_rules['group_by_optimization'])
        
        if 'LIKE' in query_upper and '%' in query_text:
            suggestions.extend(self.optimization_rules['like_optimization'])
        
        # Track query frequency
        frequency = self.query_patterns.get(query_hash, 0) + 1
        self.query_patterns[query_hash] = frequency
        
        # Get index usage information
        index_usage = self._analyze_index_usage(query_text, database_alias)
        
        return QueryMetrics(
            query_hash=query_hash,
            query_text=query_text[:2000],  # Truncate for storage
            execution_time=execution_time,
            rows_examined=rows_examined,
            rows_sent=rows_sent,
            database_alias=database_alias,
            timestamp=datetime.now(),
            optimization_suggestions=list(set(suggestions)),  # Remove duplicates
            severity=severity,
            frequency=frequency,
            index_usage=index_usage
        )
    
    def _generate_query_hash(self, query_text: str) -> str:
        """Generate a hash for query pattern matching"""
        # Normalize query by removing literals and whitespace
        normalized = ' '.join(query_text.upper().split())
        # Remove string literals and numbers for pattern matching
        import re
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _calculate_severity(self, execution_time: float, rows_examined: int, rows_sent: int) -> str:
        """Calculate query severity based on metrics"""
        if execution_time > 10 or rows_examined > 100000:
            return 'critical'
        elif execution_time > 5 or rows_examined > 50000:
            return 'high'
        elif execution_time > 2 or rows_examined > 10000:
            return 'medium'
        else:
            return 'low'
    
    def _has_missing_index_pattern(self, query: str) -> bool:
        """Check if query might benefit from indexing"""
        query_upper = query.upper()
        return ('WHERE' in query_upper and 
                any(op in query_upper for op in ['LIKE', '=', '>', '<', 'IN', 'BETWEEN']))
    
    def _has_inefficient_join_pattern(self, query: str) -> bool:
        """Check for potentially inefficient JOIN patterns"""
        query_upper = query.upper()
        return ('JOIN' in query_upper and 
                ('ON' not in query_upper or query_upper.count('JOIN') > query_upper.count('ON')))
    
    def _has_subquery_pattern(self, query: str) -> bool:
        """Check for subquery patterns"""
        query_upper = query.upper()
        return ('IN (' in query_upper and 'SELECT' in query_upper) or 'EXISTS (' in query_upper
    
    def _has_function_in_where_pattern(self, query: str) -> bool:
        """Check for functions in WHERE clauses"""
        query_upper = query.upper()
        functions = ['UPPER(', 'LOWER(', 'SUBSTRING(', 'DATE(', 'YEAR(', 'MONTH(', 'DAY(']
        return 'WHERE' in query_upper and any(func in query_upper for func in functions)
    
    def _analyze_index_usage(self, query_text: str, database_alias: str) -> Dict[str, Any]:
        """Analyze index usage for the query"""
        try:
            db_connection = connections[database_alias]
            
            with db_connection.cursor() as cursor:
                # Use EXPLAIN to analyze query execution plan
                cursor.execute(f"EXPLAIN {query_text}")
                explain_result = cursor.fetchall()
                
                index_usage = {
                    'uses_index': False,
                    'index_names': [],
                    'table_scans': 0,
                    'rows_examined_per_table': {}
                }
                
                for row in explain_result:
                    # MySQL EXPLAIN output format varies by version
                    # This is a simplified analysis
                    if len(row) > 4:
                        table = row[0] if row[0] else 'unknown'
                        key = row[5] if len(row) > 5 and row[5] else None
                        rows = row[8] if len(row) > 8 and row[8] else 0
                        
                        if key:
                            index_usage['uses_index'] = True
                            index_usage['index_names'].append(key)
                        else:
                            index_usage['table_scans'] += 1
                        
                        index_usage['rows_examined_per_table'][table] = rows
                
                return index_usage
                
        except Exception as e:
            logger.debug(f"Could not analyze index usage: {e}")
            return {}
    
    def generate_index_recommendations(self, query_metrics: List[QueryMetrics]) -> List[IndexRecommendation]:
        """Generate index recommendations based on query analysis"""
        recommendations = []
        table_column_usage = defaultdict(lambda: defaultdict(int))
        
        # Analyze query patterns to identify frequently used columns
        for metric in query_metrics:
            if metric.severity in ['high', 'critical'] and not metric.index_usage.get('uses_index', False):
                # Extract table and column information from query
                tables_columns = self._extract_table_columns(metric.query_text)
                
                for table, columns in tables_columns.items():
                    for column in columns:
                        table_column_usage[table][column] += metric.frequency
        
        # Generate recommendations based on usage patterns
        for table, columns in table_column_usage.items():
            # Sort columns by usage frequency
            sorted_columns = sorted(columns.items(), key=lambda x: x[1], reverse=True)
            
            # Single column indexes
            for column, frequency in sorted_columns[:5]:  # Top 5 columns
                if frequency > 10:  # Threshold for recommendation
                    recommendations.append(IndexRecommendation(
                        table_name=table,
                        columns=[column],
                        index_type='btree',
                        reason=f"Frequently used in WHERE clauses ({frequency} times)",
                        estimated_benefit='high' if frequency > 50 else 'medium'
                    ))
            
            # Composite indexes for frequently used column combinations
            if len(sorted_columns) > 1:
                top_columns = [col for col, freq in sorted_columns[:3] if freq > 5]
                if len(top_columns) > 1:
                    recommendations.append(IndexRecommendation(
                        table_name=table,
                        columns=top_columns,
                        index_type='btree',
                        reason="Frequently used column combination",
                        estimated_benefit='medium'
                    ))
        
        return recommendations
    
    def _extract_table_columns(self, query_text: str) -> Dict[str, Set[str]]:
        """Extract table and column information from query text"""
        # This is a simplified extraction - in practice, you'd want a proper SQL parser
        import re
        
        tables_columns = defaultdict(set)
        query_upper = query_text.upper()
        
        # Extract table names from FROM and JOIN clauses
        from_match = re.search(r'FROM\s+(\w+)', query_upper)
        if from_match:
            table = from_match.group(1).lower()
            
            # Extract columns from WHERE clause
            where_match = re.search(r'WHERE\s+(.+?)(?:ORDER BY|GROUP BY|LIMIT|$)', query_upper)
            if where_match:
                where_clause = where_match.group(1)
                # Simple column extraction - look for word.word patterns
                column_matches = re.findall(r'(\w+)\.(\w+)', where_clause)
                for table_alias, column in column_matches:
                    tables_columns[table].add(column.lower())
                
                # Also look for standalone column names
                standalone_columns = re.findall(r'\b(\w+)\s*[=<>]', where_clause)
                for column in standalone_columns:
                    if column.lower() not in ['and', 'or', 'not', 'in', 'like']:
                        tables_columns[table].add(column.lower())
        
        return dict(tables_columns)


class QueryPerformanceMonitor:
    """Monitor and track query performance metrics"""
    
    def __init__(self, monitoring_interval: int = 60):
        self.monitoring_interval = monitoring_interval
        self.query_metrics: deque = deque(maxlen=10000)
        self.slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD', 2.0)
        self.analyzer = QueryAnalyzer()
        self.monitoring_enabled = True
        
        # Performance tracking
        self.query_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.baseline_metrics = {}
        
    @contextmanager
    def monitor_query(self, query_text: str = None, database_alias: str = 'default'):
        """Context manager to monitor query execution"""
        start_time = time.time()
        rows_examined = 0
        rows_sent = 0
        
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            
            if query_text and execution_time > self.slow_query_threshold:
                # Analyze the slow query
                metrics = self.analyzer.analyze_query(
                    query_text=query_text,
                    execution_time=execution_time,
                    rows_examined=rows_examined,
                    rows_sent=rows_sent,
                    database_alias=database_alias
                )
                
                self.query_metrics.append(metrics)
                
                # Cache metrics for external access
                cache.set(f"slow_query_{metrics.query_hash}", metrics.to_dict(), 3600)
                
                logger.warning(f"Slow query detected: {execution_time:.2f}s - {query_text[:100]}...")
    
    def get_slow_queries(self, limit: int = 50) -> List[QueryMetrics]:
        """Get recent slow queries"""
        return list(self.query_metrics)[-limit:]
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        if not self.query_metrics:
            return {}
        
        total_queries = len(self.query_metrics)
        avg_execution_time = sum(q.execution_time for q in self.query_metrics) / total_queries
        
        severity_counts = defaultdict(int)
        for query in self.query_metrics:
            severity_counts[query.severity] += 1
        
        return {
            'total_slow_queries': total_queries,
            'average_execution_time': avg_execution_time,
            'severity_distribution': dict(severity_counts),
            'most_frequent_queries': self._get_most_frequent_queries(),
            'slowest_queries': self._get_slowest_queries()
        }
    
    def _get_most_frequent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently occurring slow queries"""
        query_frequency = defaultdict(int)
        query_examples = {}
        
        for query in self.query_metrics:
            query_frequency[query.query_hash] += 1
            if query.query_hash not in query_examples:
                query_examples[query.query_hash] = query
        
        sorted_queries = sorted(query_frequency.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'query_hash': query_hash,
                'frequency': frequency,
                'example': query_examples[query_hash].to_dict()
            }
            for query_hash, frequency in sorted_queries[:limit]
        ]
    
    def _get_slowest_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest queries"""
        sorted_queries = sorted(self.query_metrics, key=lambda x: x.execution_time, reverse=True)
        return [query.to_dict() for query in sorted_queries[:limit]]
    
    def benchmark_query(self, query_text: str, iterations: int = 10, 
                       database_alias: str = 'default') -> Dict[str, Any]:
        """Benchmark a specific query"""
        execution_times = []
        
        try:
            db_connection = connections[database_alias]
            
            for _ in range(iterations):
                start_time = time.time()
                
                with db_connection.cursor() as cursor:
                    cursor.execute(query_text)
                    results = cursor.fetchall()
                
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
            
            return {
                'query_text': query_text,
                'iterations': iterations,
                'min_time': min(execution_times),
                'max_time': max(execution_times),
                'avg_time': sum(execution_times) / len(execution_times),
                'total_time': sum(execution_times),
                'result_count': len(results) if 'results' in locals() else 0
            }
            
        except Exception as e:
            logger.error(f"Query benchmark failed: {e}")
            return {'error': str(e)}


class CacheOptimizer:
    """Optimize caching strategies for frequently accessed data"""
    
    def __init__(self):
        self.cache_strategies = {}
        self.cache_hit_rates = defaultdict(lambda: deque(maxlen=1000))
        self.cache_access_patterns = defaultdict(int)
        
    def register_cache_strategy(self, key_pattern: str, strategy: CacheStrategy):
        """Register a caching strategy"""
        self.cache_strategies[key_pattern] = strategy
    
    def get_cache_recommendations(self) -> List[Dict[str, Any]]:
        """Get cache optimization recommendations"""
        recommendations = []
        
        # Analyze cache hit rates
        for key_pattern, hit_rates in self.cache_hit_rates.items():
            if hit_rates:
                avg_hit_rate = sum(hit_rates) / len(hit_rates)
                
                if avg_hit_rate < 0.5:
                    recommendations.append({
                        'type': 'low_hit_rate',
                        'key_pattern': key_pattern,
                        'current_hit_rate': avg_hit_rate,
                        'recommendation': 'Consider adjusting cache timeout or invalidation strategy'
                    })
                elif avg_hit_rate > 0.9:
                    recommendations.append({
                        'type': 'high_hit_rate',
                        'key_pattern': key_pattern,
                        'current_hit_rate': avg_hit_rate,
                        'recommendation': 'Consider increasing cache timeout for better performance'
                    })
        
        return recommendations
    
    def track_cache_access(self, cache_key: str, hit: bool):
        """Track cache access patterns"""
        self.cache_access_patterns[cache_key] += 1
        
        # Find matching strategy
        for pattern in self.cache_strategies:
            if pattern in cache_key:
                self.cache_hit_rates[pattern].append(1 if hit else 0)
                break
    
    @contextmanager
    def cached_query(self, cache_key: str, timeout: int = 300):
        """Context manager for cached query execution"""
        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            self.track_cache_access(cache_key, True)
            yield cached_result
            return
        
        # Cache miss - execute and cache result
        self.track_cache_access(cache_key, False)
        result = yield None
        
        if result is not None:
            cache.set(cache_key, result, timeout)


# Global instances
query_monitor = QueryPerformanceMonitor()
cache_optimizer = CacheOptimizer()


def monitor_query_performance(query_text: str = None, database_alias: str = 'default'):
    """Decorator/context manager for monitoring query performance"""
    return query_monitor.monitor_query(query_text, database_alias)


def get_query_optimization_report() -> Dict[str, Any]:
    """Get comprehensive query optimization report"""
    analyzer = QueryAnalyzer()
    slow_queries = query_monitor.get_slow_queries()
    
    return {
        'query_statistics': query_monitor.get_query_statistics(),
        'index_recommendations': [rec.to_dict() for rec in analyzer.generate_index_recommendations(slow_queries)],
        'cache_recommendations': cache_optimizer.get_cache_recommendations(),
        'slow_queries': [q.to_dict() for q in slow_queries[-20:]],  # Last 20 slow queries
        'generated_at': datetime.now().isoformat()
    }