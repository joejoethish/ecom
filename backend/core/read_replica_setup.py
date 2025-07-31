"""
MySQL Read Replica Setup and Configuration

This module provides utilities for setting up and managing MySQL read replicas
for load distribution and high availability.
"""
import os
import logging
import subprocess
import time
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.db import connections
from django.core.management.base import BaseCommand
from django.core.cache import cache
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


class ReadReplicaManager:
    """
    Manages MySQL read replica setup, configuration, and monitoring
    """
    
    def __init__(self):
        self.master_config = self._get_master_config()
        self.replica_configs = self._get_replica_configs()
        self.replication_user = 'replication_user'
        self.replication_password = 'replication_password_123'
        
    def _get_master_config(self) -> Dict:
        """Get master database configuration"""
        return {
            'host': settings.DATABASES['default']['HOST'],
            'port': int(settings.DATABASES['default']['PORT']),
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'database': settings.DATABASES['default']['NAME'],
        }
    
    def _get_replica_configs(self) -> List[Dict]:
        """Get read replica configurations from environment"""
        replicas = []
        
        # Support multiple replicas via environment variables
        for i in range(1, 4):  # Support up to 3 replicas
            replica_host = os.getenv(f'DB_REPLICA_{i}_HOST')
            if replica_host:
                replicas.append({
                    'alias': f'read_replica_{i}',
                    'host': replica_host,
                    'port': int(os.getenv(f'DB_REPLICA_{i}_PORT', '3306')),
                    'user': os.getenv(f'DB_REPLICA_{i}_USER', 'replica_user'),
                    'password': os.getenv(f'DB_REPLICA_{i}_PASSWORD', 'replica_password'),
                    'database': os.getenv(f'DB_REPLICA_{i}_NAME', self.master_config['database']),
                })
        
        # Default single replica configuration
        if not replicas:
            replicas.append({
                'alias': 'read_replica',
                'host': os.getenv('DB_READ_HOST', 'localhost'),
                'port': int(os.getenv('DB_READ_PORT', '3308')),
                'user': os.getenv('DB_READ_USER', 'replica_user'),
                'password': os.getenv('DB_READ_PASSWORD', 'replica_password'),
                'database': os.getenv('DB_READ_NAME', self.master_config['database']),
            })
        
        return replicas
    
    def setup_master_for_replication(self) -> bool:
        """
        Configure master database for replication
        """
        try:
            connection = mysql.connector.connect(**self.master_config)
            cursor = connection.cursor()
            
            logger.info("Configuring master database for replication...")
            
            # Create replication user
            cursor.execute(f"""
                CREATE USER IF NOT EXISTS '{self.replication_user}'@'%' 
                IDENTIFIED BY '{self.replication_password}'
            """)
            
            # Grant replication privileges
            cursor.execute(f"""
                GRANT REPLICATION SLAVE ON *.* TO '{self.replication_user}'@'%'
            """)
            
            # Flush privileges
            cursor.execute("FLUSH PRIVILEGES")
            
            # Enable binary logging (requires server restart if not already enabled)
            cursor.execute("SHOW VARIABLES LIKE 'log_bin'")
            log_bin_status = cursor.fetchone()
            
            if log_bin_status and log_bin_status[1] != 'ON':
                logger.warning("Binary logging is not enabled. Please add the following to my.cnf and restart MySQL:")
                logger.warning("log-bin=mysql-bin")
                logger.warning("server-id=1")
                logger.warning("binlog-format=ROW")
                return False
            
            # Get master status
            cursor.execute("SHOW MASTER STATUS")
            master_status = cursor.fetchone()
            
            if master_status:
                logger.info(f"Master status: File={master_status[0]}, Position={master_status[1]}")
                # Cache master status for replica setup
                cache.set('master_log_file', master_status[0], 3600)
                cache.set('master_log_pos', master_status[1], 3600)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            logger.info("Master database configured for replication successfully")
            return True
            
        except Error as e:
            logger.error(f"Error configuring master for replication: {e}")
            return False
    
    def setup_replica(self, replica_config: Dict) -> bool:
        """
        Set up a single read replica
        """
        try:
            # Connect to replica (remove alias from connection config)
            conn_config = {k: v for k, v in replica_config.items() if k != 'alias'}
            connection = mysql.connector.connect(**conn_config)
            cursor = connection.cursor()
            
            logger.info(f"Setting up replica: {replica_config['alias']}")
            
            # Stop any existing replication
            cursor.execute("STOP SLAVE")
            
            # Reset slave configuration
            cursor.execute("RESET SLAVE ALL")
            
            # Get master status from cache
            master_log_file = cache.get('master_log_file')
            master_log_pos = cache.get('master_log_pos')
            
            if not master_log_file or not master_log_pos:
                logger.error("Master status not available. Please run setup_master_for_replication first.")
                return False
            
            # Configure slave
            change_master_sql = f"""
                CHANGE MASTER TO
                MASTER_HOST='{self.master_config['host']}',
                MASTER_PORT={self.master_config['port']},
                MASTER_USER='{self.replication_user}',
                MASTER_PASSWORD='{self.replication_password}',
                MASTER_LOG_FILE='{master_log_file}',
                MASTER_LOG_POS={master_log_pos}
            """
            
            cursor.execute(change_master_sql)
            
            # Start replication
            cursor.execute("START SLAVE")
            
            # Check slave status
            cursor.execute("SHOW SLAVE STATUS")
            slave_status = cursor.fetchone()
            
            if slave_status:
                io_running = slave_status[10]  # Slave_IO_Running
                sql_running = slave_status[11]  # Slave_SQL_Running
                
                if io_running == 'Yes' and sql_running == 'Yes':
                    logger.info(f"Replica {replica_config['alias']} started successfully")
                    return True
                else:
                    logger.error(f"Replica {replica_config['alias']} failed to start: IO={io_running}, SQL={sql_running}")
                    if slave_status[19]:  # Last_Error
                        logger.error(f"Last error: {slave_status[19]}")
            
            cursor.close()
            connection.close()
            return False
            
        except Error as e:
            logger.error(f"Error setting up replica {replica_config['alias']}: {e}")
            return False
    
    def setup_all_replicas(self) -> bool:
        """
        Set up all configured read replicas
        """
        logger.info("Starting read replica setup...")
        
        # First, configure master
        if not self.setup_master_for_replication():
            logger.error("Failed to configure master for replication")
            return False
        
        # Set up each replica
        success_count = 0
        for replica_config in self.replica_configs:
            if self.setup_replica(replica_config):
                success_count += 1
            else:
                logger.error(f"Failed to set up replica: {replica_config['alias']}")
        
        logger.info(f"Successfully set up {success_count}/{len(self.replica_configs)} replicas")
        return success_count > 0
    
    def check_replication_status(self) -> Dict[str, Dict]:
        """
        Check the status of all read replicas
        """
        status = {}
        
        for replica_config in self.replica_configs:
            try:
                # Remove alias from connection config
                conn_config = {k: v for k, v in replica_config.items() if k != 'alias'}
                connection = mysql.connector.connect(**conn_config)
                cursor = connection.cursor()
                
                cursor.execute("SHOW SLAVE STATUS")
                slave_status = cursor.fetchone()
                
                if slave_status:
                    status[replica_config['alias']] = {
                        'io_running': slave_status[10],
                        'sql_running': slave_status[11],
                        'seconds_behind_master': slave_status[32],
                        'last_error': slave_status[19],
                        'master_host': slave_status[1],
                        'master_port': slave_status[3],
                        'healthy': slave_status[10] == 'Yes' and slave_status[11] == 'Yes'
                    }
                else:
                    status[replica_config['alias']] = {
                        'healthy': False,
                        'error': 'No slave status available'
                    }
                
                cursor.close()
                connection.close()
                
            except Error as e:
                status[replica_config['alias']] = {
                    'healthy': False,
                    'error': str(e)
                }
        
        return status
    
    def monitor_replication_lag(self) -> Dict[str, int]:
        """
        Monitor replication lag for all replicas
        """
        lag_status = {}
        
        for replica_config in self.replica_configs:
            try:
                # Remove alias from connection config
                conn_config = {k: v for k, v in replica_config.items() if k != 'alias'}
                connection = mysql.connector.connect(**conn_config)
                cursor = connection.cursor()
                
                cursor.execute("SHOW SLAVE STATUS")
                slave_status = cursor.fetchone()
                
                if slave_status and slave_status[32] is not None:
                    lag_status[replica_config['alias']] = slave_status[32]
                else:
                    lag_status[replica_config['alias']] = -1  # Unknown
                
                cursor.close()
                connection.close()
                
            except Error as e:
                logger.error(f"Error checking lag for {replica_config['alias']}: {e}")
                lag_status[replica_config['alias']] = -1
        
        return lag_status
    
    def failover_replica(self, failed_replica: str) -> bool:
        """
        Handle failover when a replica fails
        """
        logger.warning(f"Initiating failover for failed replica: {failed_replica}")
        
        # Mark replica as unhealthy in cache
        cache.set(f"db_health_{failed_replica}", {'healthy': False}, 300)
        
        # Check if we have other healthy replicas
        status = self.check_replication_status()
        healthy_replicas = [alias for alias, info in status.items() 
                          if info.get('healthy', False) and alias != failed_replica]
        
        if healthy_replicas:
            logger.info(f"Failover successful. Healthy replicas available: {healthy_replicas}")
            return True
        else:
            logger.critical("No healthy replicas available! All reads will be routed to master.")
            return False
    
    def get_replica_django_config(self) -> Dict[str, Dict]:
        """
        Generate Django database configuration for read replicas
        """
        django_config = {}
        
        for replica_config in self.replica_configs:
            django_config[replica_config['alias']] = {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': replica_config['database'],
                'USER': replica_config['user'],
                'PASSWORD': replica_config['password'],
                'HOST': replica_config['host'],
                'PORT': str(replica_config['port']),
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                    'charset': 'utf8mb4',
                    'use_unicode': True,
                    'autocommit': True,
                    'sql_mode': 'STRICT_TRANS_TABLES',
                    'isolation_level': 'read committed',
                    'connect_timeout': 10,
                    'read_timeout': 30,
                    'write_timeout': 30,
                },
                'CONN_MAX_AGE': 3600,
                'CONN_HEALTH_CHECKS': True,
                'READ_REPLICA': True,
            }
        
        return django_config


class ReplicationHealthChecker:
    """
    Monitors replication health and performs automatic failover
    """
    
    def __init__(self):
        self.replica_manager = ReadReplicaManager()
        self.health_check_interval = 30  # seconds
        self.max_lag_threshold = getattr(settings, 'REPLICA_LAG_THRESHOLD', 5)
        
    def run_health_checks(self) -> Dict[str, bool]:
        """
        Run health checks on all replicas
        """
        logger.info("Running replica health checks...")
        
        status = self.replica_manager.check_replication_status()
        lag_status = self.replica_manager.monitor_replication_lag()
        
        health_results = {}
        
        for replica_alias, replica_status in status.items():
            is_healthy = (
                replica_status.get('healthy', False) and
                lag_status.get(replica_alias, -1) <= self.max_lag_threshold
            )
            
            health_results[replica_alias] = is_healthy
            
            # Cache health status
            cache.set(f"db_health_{replica_alias}", {
                'healthy': is_healthy,
                'replication_lag': lag_status.get(replica_alias, -1),
                'last_check': time.time()
            }, 60)
            
            if not is_healthy:
                logger.warning(f"Replica {replica_alias} is unhealthy: {replica_status}")
                self.replica_manager.failover_replica(replica_alias)
        
        return health_results
    
    def start_monitoring(self):
        """
        Start continuous monitoring (for use in management commands)
        """
        logger.info("Starting replica health monitoring...")
        
        while True:
            try:
                self.run_health_checks()
                time.sleep(self.health_check_interval)
            except KeyboardInterrupt:
                logger.info("Stopping replica health monitoring...")
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                time.sleep(self.health_check_interval)


def setup_read_replicas():
    """
    Convenience function to set up read replicas
    """
    manager = ReadReplicaManager()
    return manager.setup_all_replicas()


def check_replica_health():
    """
    Convenience function to check replica health
    """
    checker = ReplicationHealthChecker()
    return checker.run_health_checks()


def get_replica_status():
    """
    Get detailed status of all replicas
    """
    manager = ReadReplicaManager()
    return manager.check_replication_status()