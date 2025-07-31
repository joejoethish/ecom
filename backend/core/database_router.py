"""
Database router for read/write splitting and connection optimization
"""
import logging
import random
from typing import Optional, List, Dict, Any
from django.conf import settings
from django.db import models
from django.core.cache import cache

logger = logging.getLogger(__name__)


class DatabaseRouter:
    """
    Advanced database router that handles read/write splitting,
    load balancing, and connection optimization
    """
    
    def __init__(self):
        self.read_databases = self._get_read_databases()
        self.write_database = 'default'
        self.read_only_apps = getattr(settings, 'READ_ONLY_APPS', [
            'analytics', 'reports', 'search'
        ])
        self.write_only_apps = getattr(settings, 'WRITE_ONLY_APPS', [
            'admin', 'auth', 'contenttypes', 'sessions'
        ])
        self.read_only_models = getattr(settings, 'READ_ONLY_MODELS', [])
        self.replica_lag_threshold = getattr(settings, 'REPLICA_LAG_THRESHOLD', 5)  # seconds
        
    def _get_read_databases(self) -> List[str]:
        """Get list of available read replica databases"""
        read_dbs = []
        for db_alias, db_config in settings.DATABASES.items():
            if db_alias != 'default' and db_config.get('READ_REPLICA', False):
                read_dbs.append(db_alias)
        
        # If no read replicas configured, fall back to default
        return read_dbs if read_dbs else ['default']
    
    def db_for_read(self, model, **hints) -> Optional[str]:
        """
        Suggest the database to read from based on model and hints
        """
        # Check if this is a read-only app
        if model._meta.app_label in self.read_only_apps:
            return self._select_read_database()
        
        # Check if this is a read-only model
        model_name = f"{model._meta.app_label}.{model._meta.model_name}"
        if model_name in self.read_only_models:
            return self._select_read_database()
        
        # Check for explicit read hint
        if hints.get('read_only', False):
            return self._select_read_database()
        
        # Check for instance-based hints
        instance = hints.get('instance')
        if instance and hasattr(instance, '_state'):
            # If the instance was just created, read from write database
            # to avoid read-after-write consistency issues
            if instance._state.adding:
                return self.write_database
        
        # For analytics and reporting queries, prefer read replicas
        if self._is_analytics_query(model, hints):
            return self._select_read_database()
        
        # Default to read replica for most read operations
        return self._select_read_database()
    
    def db_for_write(self, model, **hints) -> Optional[str]:
        """
        Suggest the database to write to
        """
        # All writes go to the primary database
        return self.write_database
    
    def allow_relation(self, obj1, obj2, **hints) -> Optional[bool]:
        """
        Allow relations if models are in the same database
        """
        db_set = {'default'}
        db_set.update(self.read_databases)
        
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints) -> Optional[bool]:
        """
        Ensure that migrations only run on the primary database
        """
        return db == 'default'
    
    def _select_read_database(self) -> str:
        """
        Select the best read database based on health and load balancing
        """
        if not self.read_databases or self.read_databases == ['default']:
            return 'default'
        
        # Get healthy read databases
        healthy_dbs = self._get_healthy_read_databases()
        
        if not healthy_dbs:
            logger.warning("No healthy read replicas available, falling back to primary")
            return 'default'
        
        # Use weighted random selection based on replica health
        return self._weighted_random_selection(healthy_dbs)
    
    def _get_healthy_read_databases(self) -> List[str]:
        """
        Get list of healthy read databases based on replication lag and connectivity
        """
        healthy_dbs = []
        
        for db_alias in self.read_databases:
            if db_alias == 'default':
                healthy_dbs.append(db_alias)
                continue
                
            # Check database health from cache
            health_key = f"db_health_{db_alias}"
            health_status = cache.get(health_key)
            
            if health_status is None:
                # Check database health
                health_status = self._check_database_health(db_alias)
                # Cache health status for 30 seconds
                cache.set(health_key, health_status, 30)
            
            if health_status.get('healthy', False):
                # Check replication lag
                lag = health_status.get('replication_lag', 0)
                if lag <= self.replica_lag_threshold:
                    healthy_dbs.append(db_alias)
                else:
                    logger.warning(f"Database {db_alias} has high replication lag: {lag}s")
        
        return healthy_dbs
    
    def _check_database_health(self, db_alias: str) -> Dict[str, Any]:
        """
        Check the health of a specific database
        """
        from django.db import connections
        from django.db.utils import OperationalError
        
        try:
            connection = connections[db_alias]
            
            with connection.cursor() as cursor:
                # Basic connectivity test
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if not result or result[0] != 1:
                    return {'healthy': False, 'error': 'Invalid response to health check'}
                
                # Check replication lag (MySQL specific)
                replication_lag = 0
                if 'mysql' in connection.settings_dict.get('ENGINE', ''):
                    try:
                        cursor.execute("SHOW SLAVE STATUS")
                        slave_status = cursor.fetchone()
                        if slave_status:
                            # Seconds_Behind_Master is typically at index 32
                            # This may vary based on MySQL version
                            replication_lag = slave_status[32] if len(slave_status) > 32 else 0
                            replication_lag = replication_lag or 0
                    except Exception as e:
                        logger.debug(f"Could not check replication lag for {db_alias}: {e}")
                
                return {
                    'healthy': True,
                    'replication_lag': replication_lag,
                    'response_time': 0  # Could be measured if needed
                }
                
        except OperationalError as e:
            logger.error(f"Database {db_alias} health check failed: {e}")
            return {'healthy': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error checking {db_alias} health: {e}")
            return {'healthy': False, 'error': str(e)}
    
    def _weighted_random_selection(self, databases: List[str]) -> str:
        """
        Select database using weighted random selection based on health metrics
        """
        if len(databases) == 1:
            return databases[0]
        
        # For now, use simple random selection
        # In the future, this could be weighted based on:
        # - Connection pool availability
        # - Response times
        # - Current load
        return random.choice(databases)
    
    def _is_analytics_query(self, model, hints: Dict[str, Any]) -> bool:
        """
        Determine if this is an analytics/reporting query that should prefer read replicas
        """
        # Check for aggregation hints
        if hints.get('aggregation', False):
            return True
        
        # Check for large dataset queries
        if hints.get('large_dataset', False):
            return True
        
        # Check model patterns that typically indicate analytics
        model_name = model._meta.model_name.lower()
        analytics_patterns = ['log', 'metric', 'stat', 'report', 'analytics']
        
        return any(pattern in model_name for pattern in analytics_patterns)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about database routing decisions
        """
        stats = {
            'read_databases': self.read_databases,
            'write_database': self.write_database,
            'read_only_apps': self.read_only_apps,
            'write_only_apps': self.write_only_apps,
            'replica_lag_threshold': self.replica_lag_threshold,
        }
        
        # Get health status for all databases
        health_status = {}
        for db_alias in ['default'] + self.read_databases:
            if db_alias not in health_status:
                health_status[db_alias] = self._check_database_health(db_alias)
        
        stats['database_health'] = health_status
        return stats
    
    def force_write_database(self, model_class=None, app_label=None):
        """
        Context manager to force queries to use write database
        """
        return ForceWriteDatabase(self, model_class, app_label)


class ForceWriteDatabase:
    """
    Context manager to force specific queries to use the write database
    """
    
    def __init__(self, router, model_class=None, app_label=None):
        self.router = router
        self.model_class = model_class
        self.app_label = app_label
        self.original_read_method = None
    
    def __enter__(self):
        # Store original method
        self.original_read_method = self.router.db_for_read
        
        # Replace with method that always returns write database
        def force_write_db(model, **hints):
            if self.model_class and model != self.model_class:
                return self.original_read_method(model, **hints)
            if self.app_label and model._meta.app_label != self.app_label:
                return self.original_read_method(model, **hints)
            return self.router.write_database
        
        self.router.db_for_read = force_write_db
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original method
        if self.original_read_method:
            self.router.db_for_read = self.original_read_method


class ReadOnlyDatabaseRouter(DatabaseRouter):
    """
    Simplified router that sends all reads to read replicas
    """
    
    def db_for_read(self, model, **hints) -> Optional[str]:
        """Always use read database for reads"""
        return self._select_read_database()


class WriteOnlyDatabaseRouter(DatabaseRouter):
    """
    Router that sends all operations to the write database
    """
    
    def db_for_read(self, model, **hints) -> Optional[str]:
        """Use write database for reads to ensure consistency"""
        return self.write_database


# Utility functions for manual database selection
def using_read_database():
    """Context manager to force queries to use read database"""
    from django.db import transaction
    router = DatabaseRouter()
    read_db = router._select_read_database()
    return transaction.using(read_db)


def using_write_database():
    """Context manager to force queries to use write database"""
    from django.db import transaction
    return transaction.using('default')


def get_router_stats() -> Dict[str, Any]:
    """Get statistics about database routing"""
    router = DatabaseRouter()
    return router.get_database_stats()