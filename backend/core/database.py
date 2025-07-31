"""
Database utilities and health checks for MySQL integration
"""
import logging
from django.db import connection, connections
from django.core.management.color import no_style
from django.db.utils import OperationalError
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DatabaseHealthChecker:
    """Database health monitoring and connection management"""
    
    @staticmethod
    def check_connection(database_alias: str = 'default') -> Dict[str, Any]:
        """
        Check database connection health
        """
        try:
            db_conn = connections[database_alias]
            
            # Test basic connection
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            # Get connection info
            connection_info = {
                'status': 'healthy',
                'database': db_conn.settings_dict.get('NAME'),
                'host': db_conn.settings_dict.get('HOST'),
                'port': db_conn.settings_dict.get('PORT'),
                'engine': db_conn.settings_dict.get('ENGINE'),
                'test_query_result': result[0] if result else None,
                'connection_alive': True
            }
            
            # Get MySQL specific info
            if 'mysql' in db_conn.settings_dict.get('ENGINE', ''):
                with db_conn.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()
                    connection_info['mysql_version'] = version[0] if version else None
                    
                    cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                    threads = cursor.fetchone()
                    connection_info['active_connections'] = int(threads[1]) if threads else None
            
            return connection_info
            
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connection_alive': False
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'connection_alive': False
            }
    
    @staticmethod
    def get_database_stats(database_alias: str = 'default') -> Dict[str, Any]:
        """
        Get database statistics and performance metrics
        """
        try:
            db_conn = connections[database_alias]
            stats = {}
            
            if 'mysql' in db_conn.settings_dict.get('ENGINE', ''):
                with db_conn.cursor() as cursor:
                    # Get database size
                    cursor.execute("""
                        SELECT 
                            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size in MB'
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, [db_conn.settings_dict.get('NAME')])
                    size_result = cursor.fetchone()
                    stats['database_size_mb'] = size_result[0] if size_result else 0
                    
                    # Get table count
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, [db_conn.settings_dict.get('NAME')])
                    table_count = cursor.fetchone()
                    stats['table_count'] = table_count[0] if table_count else 0
                    
                    # Get connection stats
                    cursor.execute("SHOW STATUS LIKE 'Connections'")
                    connections_result = cursor.fetchone()
                    stats['total_connections'] = int(connections_result[1]) if connections_result else 0
                    
                    cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                    active_connections = cursor.fetchone()
                    stats['active_connections'] = int(active_connections[1]) if active_connections else 0
                    
                    # Get uptime
                    cursor.execute("SHOW STATUS LIKE 'Uptime'")
                    uptime_result = cursor.fetchone()
                    stats['uptime_seconds'] = int(uptime_result[1]) if uptime_result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def optimize_tables(database_alias: str = 'default') -> List[str]:
        """
        Optimize database tables for better performance
        """
        try:
            db_conn = connections[database_alias]
            optimized_tables = []
            
            if 'mysql' in db_conn.settings_dict.get('ENGINE', ''):
                with db_conn.cursor() as cursor:
                    # Get all tables
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, [db_conn.settings_dict.get('NAME')])
                    
                    tables = cursor.fetchall()
                    
                    for table in tables:
                        table_name = table[0]
                        try:
                            cursor.execute(f"OPTIMIZE TABLE `{table_name}`")
                            optimized_tables.append(table_name)
                            logger.info(f"Optimized table: {table_name}")
                        except Exception as e:
                            logger.warning(f"Failed to optimize table {table_name}: {e}")
            
            return optimized_tables
            
        except Exception as e:
            logger.error(f"Failed to optimize tables: {e}")
            return []

class DatabaseConnectionManager:
    """Manage database connections and pooling"""
    
    @staticmethod
    def close_old_connections():
        """Close old database connections"""
        try:
            for conn in connections.all():
                conn.close_if_unusable_or_obsolete()
            logger.info("Closed old database connections")
        except Exception as e:
            logger.error(f"Failed to close old connections: {e}")
    
    @staticmethod
    def reset_queries():
        """Reset query log to prevent memory leaks"""
        try:
            from django.db import reset_queries
            reset_queries()
            logger.debug("Reset database queries log")
        except Exception as e:
            logger.error(f"Failed to reset queries: {e}")
    
    @staticmethod
    def get_connection_info() -> Dict[str, Any]:
        """Get information about all database connections"""
        info = {}
        
        for alias in connections:
            try:
                conn = connections[alias]
                info[alias] = {
                    'vendor': conn.vendor,
                    'display_name': conn.display_name,
                    'settings': {
                        'ENGINE': conn.settings_dict.get('ENGINE'),
                        'NAME': conn.settings_dict.get('NAME'),
                        'HOST': conn.settings_dict.get('HOST'),
                        'PORT': conn.settings_dict.get('PORT'),
                    },
                    'is_usable': conn.is_usable(),
                    'queries_logged': len(conn.queries) if hasattr(conn, 'queries') else 0
                }
            except Exception as e:
                info[alias] = {'error': str(e)}
        
        return info

# Utility functions
def ensure_connection():
    """Ensure database connection is active"""
    try:
        connection.ensure_connection()
        return True
    except Exception as e:
        logger.error(f"Failed to ensure database connection: {e}")
        return False

def execute_raw_sql(sql: str, params: List[Any] = None) -> List[Dict[str, Any]]:
    """Execute raw SQL and return results as dictionaries"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or [])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Failed to execute raw SQL: {e}")
        raise