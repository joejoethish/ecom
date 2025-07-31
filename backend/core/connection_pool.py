"""
MySQL Connection Pool Manager for optimized database connections
"""
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


@dataclass
class PoolMetrics:
    """Connection pool metrics tracking"""
    pool_name: str
    pool_size: int
    active_connections: int = 0
    idle_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    peak_connections: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


class ConnectionPoolManager:
    """
    Advanced MySQL connection pool manager with health monitoring,
    automatic recovery, and performance optimization
    """
    
    def __init__(self, pool_config: Optional[Dict[str, Any]] = None):
        self.pool_config = pool_config or self._get_default_config()
        self.pools: Dict[str, mysql.connector.pooling.MySQLConnectionPool] = {}
        self.metrics: Dict[str, PoolMetrics] = {}
        self.health_check_interval = 30  # seconds
        self.last_health_check = {}
        self._lock = threading.RLock()
        self._monitoring_enabled = True
        
        # Initialize pools
        self._initialize_pools()
        
        # Start background health monitoring
        self._start_health_monitoring()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default pool configuration from Django settings"""
        db_config = settings.DATABASES.get('default', {})
        
        return {
            'default': {
                'pool_name': 'ecommerce_pool',
                'pool_size': 20,
                'pool_reset_session': True,
                'pool_pre_ping': True,
                'max_overflow': 30,
                'pool_recycle': 3600,
                'host': db_config.get('HOST', 'localhost'),
                'port': int(db_config.get('PORT', 3306)),
                'database': db_config.get('NAME', 'ecommerce_db'),
                'user': db_config.get('USER', 'root'),
                'password': db_config.get('PASSWORD', ''),
                'charset': 'utf8mb4',
                'use_unicode': True,
                'autocommit': True,
                'sql_mode': 'STRICT_TRANS_TABLES',
                'connect_timeout': 10,
                'read_timeout': 30,
                'write_timeout': 30,
            }
        }
    
    def _initialize_pools(self):
        """Initialize connection pools for each configured database"""
        for pool_name, config in self.pool_config.items():
            try:
                # Create connection pool
                pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name=config['pool_name'],
                    pool_size=config['pool_size'],
                    pool_reset_session=config.get('pool_reset_session', True),
                    host=config['host'],
                    port=config['port'],
                    database=config['database'],
                    user=config['user'],
                    password=config['password'],
                    charset=config.get('charset', 'utf8mb4'),
                    use_unicode=config.get('use_unicode', True),
                    autocommit=config.get('autocommit', True),
                    sql_mode=config.get('sql_mode', 'STRICT_TRANS_TABLES'),
                    connect_timeout=config.get('connect_timeout', 10),
                    read_timeout=config.get('read_timeout', 30),
                    write_timeout=config.get('write_timeout', 30),
                )
                
                self.pools[pool_name] = pool
                self.metrics[pool_name] = PoolMetrics(
                    pool_name=config['pool_name'],
                    pool_size=config['pool_size']
                )
                
                logger.info(f"Initialized connection pool '{pool_name}' with {config['pool_size']} connections")
                
            except MySQLError as e:
                logger.error(f"Failed to initialize pool '{pool_name}': {e}")
                raise
    
    @contextmanager
    def get_connection(self, pool_name: str = 'default', read_only: bool = False):
        """
        Get a connection from the pool with automatic cleanup
        
        Args:
            pool_name: Name of the pool to get connection from
            read_only: Whether this is a read-only connection (for future routing)
        """
        connection = None
        start_time = time.time()
        
        try:
            with self._lock:
                if pool_name not in self.pools:
                    raise ValueError(f"Pool '{pool_name}' not found")
                
                pool = self.pools[pool_name]
                metrics = self.metrics[pool_name]
                
                # Get connection from pool
                connection = pool.get_connection()
                
                # Update metrics
                metrics.active_connections += 1
                metrics.total_requests += 1
                metrics.peak_connections = max(
                    metrics.peak_connections, 
                    metrics.active_connections
                )
                metrics.last_updated = datetime.now()
                
                # Perform health check if needed
                if self._should_health_check(pool_name):
                    self._perform_health_check(connection, pool_name)
            
            yield connection
            
        except MySQLError as e:
            with self._lock:
                if pool_name in self.metrics:
                    self.metrics[pool_name].failed_requests += 1
            
            logger.error(f"Failed to get connection from pool '{pool_name}': {e}")
            
            # Attempt recovery
            self._attempt_recovery(pool_name)
            raise
            
        finally:
            # Clean up and update metrics
            if connection and connection.is_connected():
                try:
                    connection.close()
                except:
                    pass
            
            with self._lock:
                if pool_name in self.metrics:
                    metrics = self.metrics[pool_name]
                    metrics.active_connections = max(0, metrics.active_connections - 1)
                    
                    # Update average response time
                    response_time = time.time() - start_time
                    if metrics.total_requests > 0:
                        metrics.average_response_time = (
                            (metrics.average_response_time * (metrics.total_requests - 1) + response_time) 
                            / metrics.total_requests
                        )
    
    def _should_health_check(self, pool_name: str) -> bool:
        """Check if health check is needed for the pool"""
        last_check = self.last_health_check.get(pool_name, datetime.min)
        return datetime.now() - last_check > timedelta(seconds=self.health_check_interval)
    
    def _perform_health_check(self, connection, pool_name: str):
        """Perform health check on connection"""
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0] == 1:
                self.last_health_check[pool_name] = datetime.now()
                logger.debug(f"Health check passed for pool '{pool_name}'")
            else:
                logger.warning(f"Health check failed for pool '{pool_name}': Invalid result")
                
        except MySQLError as e:
            logger.error(f"Health check failed for pool '{pool_name}': {e}")
            self._attempt_recovery(pool_name)
    
    def _attempt_recovery(self, pool_name: str):
        """Attempt to recover a failed connection pool"""
        try:
            logger.info(f"Attempting recovery for pool '{pool_name}'")
            
            # Get pool configuration
            if pool_name not in self.pool_config:
                logger.error(f"No configuration found for pool '{pool_name}'")
                return
            
            config = self.pool_config[pool_name]
            
            # Recreate the pool
            new_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=f"{config['pool_name']}_recovery_{int(time.time())}",
                pool_size=config['pool_size'],
                pool_reset_session=config.get('pool_reset_session', True),
                host=config['host'],
                port=config['port'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                charset=config.get('charset', 'utf8mb4'),
                use_unicode=config.get('use_unicode', True),
                autocommit=config.get('autocommit', True),
                sql_mode=config.get('sql_mode', 'STRICT_TRANS_TABLES'),
                connect_timeout=config.get('connect_timeout', 10),
                read_timeout=config.get('read_timeout', 30),
                write_timeout=config.get('write_timeout', 30),
            )
            
            # Replace the old pool
            with self._lock:
                old_pool = self.pools.get(pool_name)
                self.pools[pool_name] = new_pool
                
                # Reset metrics
                if pool_name in self.metrics:
                    self.metrics[pool_name].failed_requests = 0
                    self.metrics[pool_name].last_updated = datetime.now()
            
            logger.info(f"Successfully recovered pool '{pool_name}'")
            
        except Exception as e:
            logger.error(f"Failed to recover pool '{pool_name}': {e}")
    
    def _start_health_monitoring(self):
        """Start background health monitoring thread"""
        def monitor():
            while self._monitoring_enabled:
                try:
                    self._monitor_all_pools()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    time.sleep(5)  # Short delay before retry
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logger.info("Started connection pool health monitoring")
    
    def _monitor_all_pools(self):
        """Monitor health of all connection pools"""
        for pool_name in list(self.pools.keys()):
            try:
                with self.get_connection(pool_name) as conn:
                    # Connection test is performed in get_connection
                    pass
            except Exception as e:
                logger.warning(f"Pool '{pool_name}' health check failed: {e}")
    
    def get_pool_metrics(self, pool_name: str = None) -> Dict[str, PoolMetrics]:
        """Get metrics for specified pool or all pools"""
        with self._lock:
            if pool_name:
                return {pool_name: self.metrics.get(pool_name)}
            return self.metrics.copy()
    
    def get_pool_status(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed status of all connection pools"""
        status = {}
        
        with self._lock:
            for pool_name, pool in self.pools.items():
                metrics = self.metrics.get(pool_name)
                
                try:
                    # Try to get a connection to test pool health
                    test_conn = pool.get_connection()
                    test_conn.close()
                    pool_healthy = True
                except:
                    pool_healthy = False
                
                status[pool_name] = {
                    'healthy': pool_healthy,
                    'pool_size': metrics.pool_size if metrics else 0,
                    'active_connections': metrics.active_connections if metrics else 0,
                    'total_requests': metrics.total_requests if metrics else 0,
                    'failed_requests': metrics.failed_requests if metrics else 0,
                    'average_response_time': metrics.average_response_time if metrics else 0,
                    'peak_connections': metrics.peak_connections if metrics else 0,
                    'last_updated': metrics.last_updated.isoformat() if metrics else None,
                }
        
        return status
    
    def optimize_pool_size(self, pool_name: str, target_utilization: float = 0.8):
        """
        Optimize pool size based on usage patterns
        
        Args:
            pool_name: Name of the pool to optimize
            target_utilization: Target utilization percentage (0.0 to 1.0)
        """
        with self._lock:
            if pool_name not in self.metrics:
                logger.warning(f"No metrics found for pool '{pool_name}'")
                return
            
            metrics = self.metrics[pool_name]
            current_utilization = metrics.peak_connections / metrics.pool_size
            
            if current_utilization > target_utilization:
                # Increase pool size
                new_size = int(metrics.peak_connections / target_utilization) + 2
                logger.info(f"Recommending pool size increase for '{pool_name}': {metrics.pool_size} -> {new_size}")
            elif current_utilization < target_utilization * 0.5:
                # Decrease pool size
                new_size = max(5, int(metrics.peak_connections / target_utilization))
                logger.info(f"Recommending pool size decrease for '{pool_name}': {metrics.pool_size} -> {new_size}")
            else:
                logger.info(f"Pool '{pool_name}' size is optimal")
    
    def close_all_pools(self):
        """Close all connection pools"""
        self._monitoring_enabled = False
        
        with self._lock:
            for pool_name, pool in self.pools.items():
                try:
                    # Note: mysql.connector pools don't have a direct close method
                    # Connections will be closed when they go out of scope
                    logger.info(f"Closed pool '{pool_name}'")
                except Exception as e:
                    logger.error(f"Error closing pool '{pool_name}': {e}")
            
            self.pools.clear()
            self.metrics.clear()


# Global connection pool manager instance
_pool_manager = None


def get_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager instance"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()
    return _pool_manager


def initialize_connection_pools(pool_config: Optional[Dict[str, Any]] = None):
    """Initialize connection pools with custom configuration"""
    global _pool_manager
    _pool_manager = ConnectionPoolManager(pool_config)
    return _pool_manager