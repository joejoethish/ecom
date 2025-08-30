"""
Database integration and monitoring for the E2E Workflow Debugging System.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from django.db import connections, connection
from django.db.utils import DatabaseError
from django.core.management.color import no_style
from django.core.management.sql import sql_flush
from django.conf import settings
from .models import PerformanceSnapshot, ErrorLog
from .config import config, FeatureFlags
from .utils import PerformanceMonitor, ErrorLogger


logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """Monitor database connections and performance"""
    
    def __init__(self):
        self.connection_pools = {}
        self.query_cache = {}
        
    def check_database_health(self, database_alias: str = 'default') -> Dict[str, Any]:
        """Check database connection health"""
        try:
            db_connection = connections[database_alias]
            
            # Test connection
            start_time = time.time()
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            connection_time = (time.time() - start_time) * 1000
            
            # Get connection info
            connection_info = {
                'status': 'healthy',
                'connection_time_ms': connection_time,
                'database_name': db_connection.settings_dict.get('NAME'),
                'host': db_connection.settings_dict.get('HOST'),
                'port': db_connection.settings_dict.get('PORT'),
                'engine': db_connection.settings_dict.get('ENGINE'),
                'conn_max_age': db_connection.settings_dict.get('CONN_MAX_AGE'),
                'queries_executed': len(connection.queries) if settings.DEBUG else 'N/A',
            }
            
            # Check connection pool status if available
            if hasattr(db_connection, 'pool'):
                pool_info = self._get_connection_pool_info(db_connection)
                connection_info.update(pool_info)
            
            # Record performance metric
            if FeatureFlags.is_performance_monitoring_enabled():
                PerformanceMonitor.record_metric(
                    layer='database',
                    component='connection_health',
                    metric_name='connection_time',
                    metric_value=connection_time,
                    metadata=connection_info
                )
            
            return connection_info
            
        except DatabaseError as e:
            error_info = {
                'status': 'unhealthy',
                'error': str(e),
                'database_alias': database_alias
            }
            
            # Log error
            if FeatureFlags.is_error_tracking_enabled():
                ErrorLogger.log_error(
                    layer='database',
                    component='connection_health',
                    error_type='DatabaseConnectionError',
                    error_message=str(e),
                    severity='critical',
                    metadata=error_info
                )
            
            return error_info
    
    def _get_connection_pool_info(self, db_connection) -> Dict[str, Any]:
        """Get connection pool information"""
        try:
            pool = db_connection.pool
            return {
                'pool_size': getattr(pool, 'size', 'N/A'),
                'pool_checked_in': getattr(pool, 'checkedin', 'N/A'),
                'pool_checked_out': getattr(pool, 'checkedout', 'N/A'),
                'pool_overflow': getattr(pool, 'overflow', 'N/A'),
            }
        except AttributeError:
            return {'pool_info': 'Not available'}
    
    def analyze_slow_queries(self, threshold_ms: int = 100) -> List[Dict[str, Any]]:
        """Analyze slow queries from Django's query log"""
        if not settings.DEBUG:
            return []
        
        slow_queries = []
        for query_info in connection.queries:
            query_time = float(query_info.get('time', 0)) * 1000  # Convert to ms
            
            if query_time > threshold_ms:
                slow_query = {
                    'sql': query_info['sql'],
                    'time_ms': query_time,
                    'analysis': self._analyze_query(query_info['sql']),
                }
                slow_queries.append(slow_query)
                
                # Record performance metric
                if FeatureFlags.is_performance_monitoring_enabled():
                    PerformanceMonitor.record_metric(
                        layer='database',
                        component='query_performance',
                        metric_name='query_time',
                        metric_value=query_time,
                        metadata={
                            'sql': query_info['sql'][:200],  # Truncate for storage
                            'threshold_exceeded': True
                        }
                    )
        
        return slow_queries
    
    def _analyze_query(self, sql: str) -> Dict[str, Any]:
        """Analyze SQL query for potential issues"""
        analysis = {
            'issues': [],
            'recommendations': [],
            'complexity': 'low'
        }
        
        sql_lower = sql.lower()
        
        # Check for common performance issues
        if 'select *' in sql_lower:
            analysis['issues'].append('Using SELECT *')
            analysis['recommendations'].append('Select only needed columns')
        
        if sql_lower.count('join') > 3:
            analysis['issues'].append('Multiple JOINs detected')
            analysis['recommendations'].append('Consider query optimization or denormalization')
            analysis['complexity'] = 'high'
        
        if 'where' not in sql_lower and ('select' in sql_lower and 'from' in sql_lower):
            analysis['issues'].append('Query without WHERE clause')
            analysis['recommendations'].append('Add appropriate WHERE conditions')
        
        if 'order by' in sql_lower and 'limit' not in sql_lower:
            analysis['issues'].append('ORDER BY without LIMIT')
            analysis['recommendations'].append('Consider adding LIMIT clause')
        
        if sql_lower.count('subquery') > 0 or sql_lower.count('(select') > 0:
            analysis['complexity'] = 'medium'
            analysis['recommendations'].append('Consider optimizing subqueries')
        
        return analysis
    
    def check_migration_status(self) -> Dict[str, Any]:
        """Check Django migration status"""
        try:
            from django.db.migrations.executor import MigrationExecutor
            
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            migration_status = {
                'status': 'up_to_date' if not plan else 'pending_migrations',
                'pending_migrations': len(plan),
                'migration_details': []
            }
            
            if plan:
                for migration, backwards in plan:
                    migration_status['migration_details'].append({
                        'app': migration.app_label,
                        'name': migration.name,
                        'backwards': backwards
                    })
            
            return migration_status
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate_database_integrity(self) -> Dict[str, Any]:
        """Validate database integrity"""
        integrity_results = {
            'status': 'healthy',
            'issues': [],
            'foreign_key_violations': [],
            'constraint_violations': []
        }
        
        try:
            # Check foreign key constraints
            with connection.cursor() as cursor:
                # MySQL-specific foreign key check
                if 'mysql' in connection.settings_dict['ENGINE']:
                    cursor.execute("SET foreign_key_checks = 1")
                    
                    # Get all tables with foreign keys
                    cursor.execute("""
                        SELECT TABLE_NAME, CONSTRAINT_NAME, COLUMN_NAME, 
                               REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                        FROM information_schema.KEY_COLUMN_USAGE 
                        WHERE REFERENCED_TABLE_NAME IS NOT NULL 
                        AND TABLE_SCHEMA = %s
                    """, [connection.settings_dict['NAME']])
                    
                    foreign_keys = cursor.fetchall()
                    
                    for fk in foreign_keys:
                        table, constraint, column, ref_table, ref_column = fk
                        
                        # Check for orphaned records
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM {table} t1 
                            LEFT JOIN {ref_table} t2 ON t1.{column} = t2.{ref_column}
                            WHERE t1.{column} IS NOT NULL AND t2.{ref_column} IS NULL
                        """)
                        
                        orphaned_count = cursor.fetchone()[0]
                        if orphaned_count > 0:
                            integrity_results['foreign_key_violations'].append({
                                'table': table,
                                'constraint': constraint,
                                'orphaned_records': orphaned_count
                            })
                            integrity_results['status'] = 'issues_found'
            
        except Exception as e:
            integrity_results['status'] = 'error'
            integrity_results['error'] = str(e)
            
            # Log error
            if FeatureFlags.is_error_tracking_enabled():
                ErrorLogger.log_error(
                    layer='database',
                    component='integrity_check',
                    error_type='IntegrityCheckError',
                    error_message=str(e),
                    severity='warning',
                    metadata={'check_type': 'foreign_key_validation'}
                )
        
        return integrity_results
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics and metrics"""
        stats = {
            'connection_info': {},
            'table_statistics': [],
            'performance_metrics': {}
        }
        
        try:
            with connection.cursor() as cursor:
                # Get database size and table information
                if 'mysql' in connection.settings_dict['ENGINE']:
                    # Database size
                    cursor.execute("""
                        SELECT 
                            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS db_size_mb,
                            COUNT(*) as table_count
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, [connection.settings_dict['NAME']])
                    
                    db_info = cursor.fetchone()
                    stats['connection_info'] = {
                        'database_size_mb': db_info[0],
                        'table_count': db_info[1]
                    }
                    
                    # Table statistics
                    cursor.execute("""
                        SELECT 
                            table_name,
                            table_rows,
                            ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
                            ROUND(data_length / 1024 / 1024, 2) AS data_mb,
                            ROUND(index_length / 1024 / 1024, 2) AS index_mb
                        FROM information_schema.tables 
                        WHERE table_schema = %s 
                        ORDER BY (data_length + index_length) DESC 
                        LIMIT 20
                    """, [connection.settings_dict['NAME']])
                    
                    for row in cursor.fetchall():
                        stats['table_statistics'].append({
                            'table_name': row[0],
                            'row_count': row[1],
                            'total_size_mb': row[2],
                            'data_size_mb': row[3],
                            'index_size_mb': row[4]
                        })
        
        except Exception as e:
            stats['error'] = str(e)
            logger.error(f"Failed to get database statistics: {e}")
        
        return stats
    
    def optimize_database_performance(self) -> Dict[str, Any]:
        """Analyze and suggest database performance optimizations"""
        optimizations = {
            'recommendations': [],
            'analysis': {},
            'priority': 'low'
        }
        
        try:
            # Analyze slow queries
            slow_queries = self.analyze_slow_queries()
            if slow_queries:
                optimizations['recommendations'].append({
                    'type': 'query_optimization',
                    'description': f'Found {len(slow_queries)} slow queries',
                    'action': 'Review and optimize slow queries',
                    'priority': 'high' if len(slow_queries) > 10 else 'medium'
                })
            
            # Check database statistics
            stats = self.get_database_statistics()
            
            # Analyze table sizes
            large_tables = [
                table for table in stats.get('table_statistics', [])
                if table.get('total_size_mb', 0) > 100  # Tables larger than 100MB
            ]
            
            if large_tables:
                optimizations['recommendations'].append({
                    'type': 'table_optimization',
                    'description': f'Found {len(large_tables)} large tables',
                    'action': 'Consider partitioning or archiving old data',
                    'priority': 'medium'
                })
            
            # Check for missing indexes (simplified check)
            integrity_results = self.validate_database_integrity()
            if integrity_results.get('foreign_key_violations'):
                optimizations['recommendations'].append({
                    'type': 'data_integrity',
                    'description': 'Found foreign key violations',
                    'action': 'Clean up orphaned records',
                    'priority': 'high'
                })
            
            # Set overall priority
            priorities = [rec.get('priority', 'low') for rec in optimizations['recommendations']]
            if 'high' in priorities:
                optimizations['priority'] = 'high'
            elif 'medium' in priorities:
                optimizations['priority'] = 'medium'
            
            optimizations['analysis'] = {
                'slow_queries_count': len(slow_queries),
                'large_tables_count': len(large_tables),
                'integrity_issues': len(integrity_results.get('foreign_key_violations', [])),
                'total_recommendations': len(optimizations['recommendations'])
            }
        
        except Exception as e:
            optimizations['error'] = str(e)
            logger.error(f"Failed to analyze database performance: {e}")
        
        return optimizations


# Global database monitor instance
database_monitor = DatabaseMonitor()


class DatabaseMiddleware:
    """Middleware to monitor database queries and performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if not FeatureFlags.is_database_monitoring_enabled():
            return self.get_response(request)
        
        # Record initial query count
        initial_queries = len(connection.queries) if settings.DEBUG else 0
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Record database metrics
        end_time = time.time()
        final_queries = len(connection.queries) if settings.DEBUG else 0
        query_count = final_queries - initial_queries
        
        if query_count > 0:
            correlation_id = getattr(request, 'correlation_id', None)
            
            # Record query count metric
            PerformanceMonitor.record_metric(
                layer='database',
                component='middleware',
                metric_name='query_count',
                metric_value=query_count,
                correlation_id=correlation_id,
                metadata={
                    'path': request.path,
                    'method': request.method,
                    'total_time_ms': (end_time - start_time) * 1000
                }
            )
            
            # Check for N+1 query problems
            if query_count > 10:  # Threshold for potential N+1 problem
                ErrorLogger.log_error(
                    layer='database',
                    component='middleware',
                    error_type='PotentialN+1Query',
                    error_message=f'High query count detected: {query_count} queries',
                    correlation_id=correlation_id,
                    severity='warning',
                    metadata={
                        'path': request.path,
                        'method': request.method,
                        'query_count': query_count
                    }
                )
        
        return response