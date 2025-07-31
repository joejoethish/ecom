#!/usr/bin/env python3
"""
Environment-specific configuration management for MySQL database integration.
This script manages configuration deployment across different environments.
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages environment-specific configurations for MySQL deployment."""
    
    def __init__(self, environment: str):
        self.environment = environment
        self.base_dir = Path(__file__).parent
        self.env_dir = self.base_dir / "environments"
        self.templates_dir = self.base_dir / "templates"
        self.output_dir = self.base_dir / "generated"
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
    def load_environment_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        env_file = self.env_dir / f"{self.environment}.env"
        
        if not env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {env_file}")
        
        config = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        logger.info(f"Loaded configuration for environment: {self.environment}")
        return config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate required configuration parameters."""
        required_params = [
            'DB_NAME', 'DB_USER', 'DB_HOST', 'DB_PORT',
            'BACKUP_STORAGE_PATH', 'MONITORING_ALERT_EMAIL'
        ]
        
        missing_params = []
        for param in required_params:
            if not config.get(param):
                missing_params.append(param)
        
        if missing_params:
            logger.error(f"Missing required parameters: {missing_params}")
            return False
        
        # Validate sensitive parameters are not empty
        sensitive_params = ['DB_PASSWORD', 'SECRET_KEY']
        for param in sensitive_params:
            if param in config and not config[param]:
                logger.warning(f"Sensitive parameter {param} is empty")
        
        logger.info("Configuration validation passed")
        return True
    
    def generate_mysql_config(self, config: Dict[str, Any]) -> str:
        """Generate MySQL configuration file."""
        template = f"""[mysqld]
# Basic Settings
user = mysql
pid-file = /var/run/mysqld/mysqld.pid
socket = /var/run/mysqld/mysqld.sock
port = {config.get('DB_PORT', '3306')}
basedir = /usr
datadir = /var/lib/mysql
tmpdir = /tmp
lc-messages-dir = /usr/share/mysql
skip-external-locking

# Performance Settings
innodb_buffer_pool_size = {config.get('INNODB_BUFFER_POOL_SIZE', '2G')}
innodb_log_file_size = {config.get('INNODB_LOG_FILE_SIZE', '256M')}
innodb_flush_log_at_trx_commit = {config.get('INNODB_FLUSH_LOG_AT_TRX_COMMIT', '2')}
innodb_flush_method = {config.get('INNODB_FLUSH_METHOD', 'O_DIRECT')}
innodb_file_per_table = 1
innodb_open_files = 400

# Connection Settings
max_connections = {config.get('DB_MAX_CONNECTIONS', '500')}
max_connect_errors = 1000
connect_timeout = 60
wait_timeout = 28800
interactive_timeout = 28800

# Query Cache
query_cache_type = 0
query_cache_size = 0

# Logging
general_log = {1 if config.get('LOG_GENERAL_QUERIES', 'false').lower() == 'true' else 0}
slow_query_log = {1 if config.get('LOG_SLOW_QUERIES', 'true').lower() == 'true' else 0}
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = {config.get('ALERT_SLOW_QUERY_THRESHOLD', '2')}
log_queries_not_using_indexes = 1

# Security Settings
local_infile = 0
skip_show_database
"""

        if config.get('SECURITY_SSL_REQUIRED', 'false').lower() == 'true':
            template += f"""
# SSL Configuration
ssl-ca = {config.get('DB_SSL_CA', '/etc/mysql/ssl/ca-cert.pem')}
ssl-cert = {config.get('DB_SSL_CERT', '/etc/mysql/ssl/server-cert.pem')}
ssl-key = {config.get('DB_SSL_KEY', '/etc/mysql/ssl/server-key.pem')}
require_secure_transport = ON
"""

        if config.get('REPLICATION_ENABLED', 'false').lower() == 'true':
            template += f"""
# Binary Logging for Replication
server-id = {config.get('REPLICATION_SERVER_ID', '1')}
log-bin = mysql-bin
binlog_format = {config.get('REPLICATION_BINLOG_FORMAT', 'ROW')}
expire_logs_days = {config.get('REPLICATION_EXPIRE_LOGS_DAYS', '7')}
max_binlog_size = 100M
"""

        template += """
# Character Set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4

[client]
default-character-set = utf8mb4
"""
        
        return template
    
    def generate_django_settings(self, config: Dict[str, Any]) -> str:
        """Generate Django database settings."""
        settings = f"""
# Database Configuration for {self.environment.upper()}
DATABASES = {{
    'default': {{
        'ENGINE': '{config.get('DB_ENGINE', 'django.db.backends.mysql')}',
        'NAME': '{config.get('DB_NAME')}',
        'USER': '{config.get('DB_USER')}',
        'PASSWORD': '{config.get('DB_PASSWORD', '')}',
        'HOST': '{config.get('DB_HOST')}',
        'PORT': '{config.get('DB_PORT', '3306')}',
        'OPTIONS': {{
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
"""

        if config.get('SECURITY_SSL_REQUIRED', 'false').lower() == 'true':
            settings += f"""            'ssl': {{
                'ca': '{config.get('DB_SSL_CA')}',
                'cert': '{config.get('DB_SSL_CERT')}',
                'key': '{config.get('DB_SSL_KEY')}',
            }},
"""

        settings += f"""        }},
        'CONN_MAX_AGE': {config.get('DB_CONN_MAX_AGE', '3600')},
        'CONN_HEALTH_CHECKS': {config.get('DB_CONN_HEALTH_CHECKS', 'True')},
    }}
}}
"""

        if config.get('DB_READ_HOST'):
            settings += f"""
# Read Replica Configuration
DATABASES['read_replica'] = {{
    'ENGINE': '{config.get('DB_ENGINE', 'django.db.backends.mysql')}',
    'NAME': '{config.get('DB_NAME')}',
    'USER': '{config.get('DB_READ_USER')}',
    'PASSWORD': '{config.get('DB_READ_PASSWORD', '')}',
    'HOST': '{config.get('DB_READ_HOST')}',
    'PORT': '{config.get('DB_PORT', '3306')}',
    'OPTIONS': {{
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'charset': 'utf8mb4',
    }},
}}

DATABASE_ROUTERS = ['core.routers.DatabaseRouter']
"""

        return settings
    
    def generate_monitoring_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate monitoring configuration."""
        monitoring_config = {
            'enabled': config.get('MONITORING_ENABLED', 'true').lower() == 'true',
            'interval': int(config.get('MONITORING_INTERVAL', '60')),
            'alert_email': config.get('MONITORING_ALERT_EMAIL'),
            'slack_webhook': config.get('MONITORING_SLACK_WEBHOOK'),
            'thresholds': {
                'cpu': int(config.get('ALERT_CPU_THRESHOLD', '80')),
                'memory': int(config.get('ALERT_MEMORY_THRESHOLD', '85')),
                'disk': int(config.get('ALERT_DISK_THRESHOLD', '90')),
                'connections': int(config.get('ALERT_CONNECTION_THRESHOLD', '80')),
                'slow_queries': int(config.get('ALERT_SLOW_QUERY_THRESHOLD', '5')),
                'replication_lag': int(config.get('ALERT_REPLICATION_LAG_THRESHOLD', '300'))
            },
            'database': {
                'host': config.get('DB_HOST'),
                'port': int(config.get('DB_PORT', '3306')),
                'user': 'monitor',
                'password': 'monitor_password'
            }
        }
        
        return monitoring_config
    
    def generate_backup_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate backup configuration."""
        backup_config = {
            'enabled': config.get('BACKUP_ENABLED', 'true').lower() == 'true',
            'schedules': {
                'full': config.get('BACKUP_SCHEDULE_FULL', '0 2 * * *'),
                'incremental': config.get('BACKUP_SCHEDULE_INCREMENTAL', '0 */4 * * *')
            },
            'retention_days': int(config.get('BACKUP_RETENTION_DAYS', '30')),
            'storage_path': config.get('BACKUP_STORAGE_PATH', '/var/backups/mysql'),
            'encryption_key': config.get('BACKUP_ENCRYPTION_KEY'),
            's3': {
                'bucket': config.get('BACKUP_S3_BUCKET'),
                'region': config.get('BACKUP_S3_REGION', 'us-east-1')
            },
            'database': {
                'host': config.get('DB_HOST'),
                'port': int(config.get('DB_PORT', '3306')),
                'name': config.get('DB_NAME'),
                'user': config.get('DB_USER'),
                'password': config.get('DB_PASSWORD')
            }
        }
        
        return backup_config
    
    def deploy_configuration(self) -> bool:
        """Deploy configuration files for the specified environment."""
        try:
            # Load environment configuration
            config = self.load_environment_config()
            
            # Validate configuration
            if not self.validate_config(config):
                return False
            
            # Generate MySQL configuration
            mysql_config = self.generate_mysql_config(config)
            mysql_config_file = self.output_dir / f"mysql-{self.environment}.cnf"
            with open(mysql_config_file, 'w') as f:
                f.write(mysql_config)
            logger.info(f"Generated MySQL config: {mysql_config_file}")
            
            # Generate Django settings
            django_settings = self.generate_django_settings(config)
            django_settings_file = self.output_dir / f"django-db-{self.environment}.py"
            with open(django_settings_file, 'w') as f:
                f.write(django_settings)
            logger.info(f"Generated Django settings: {django_settings_file}")
            
            # Generate monitoring configuration
            monitoring_config = self.generate_monitoring_config(config)
            monitoring_config_file = self.output_dir / f"monitoring-{self.environment}.json"
            with open(monitoring_config_file, 'w') as f:
                json.dump(monitoring_config, f, indent=2)
            logger.info(f"Generated monitoring config: {monitoring_config_file}")
            
            # Generate backup configuration
            backup_config = self.generate_backup_config(config)
            backup_config_file = self.output_dir / f"backup-{self.environment}.json"
            with open(backup_config_file, 'w') as f:
                json.dump(backup_config, f, indent=2)
            logger.info(f"Generated backup config: {backup_config_file}")
            
            logger.info(f"Configuration deployment completed for environment: {self.environment}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration deployment failed: {str(e)}")
            return False
    
    def list_environments(self) -> list:
        """List available environments."""
        env_files = list(self.env_dir.glob("*.env"))
        environments = [f.stem for f in env_files]
        return sorted(environments)
    
    def compare_environments(self, env1: str, env2: str) -> Dict[str, Any]:
        """Compare configurations between two environments."""
        config1 = ConfigManager(env1).load_environment_config()
        config2 = ConfigManager(env2).load_environment_config()
        
        all_keys = set(config1.keys()) | set(config2.keys())
        differences = {}
        
        for key in all_keys:
            val1 = config1.get(key, '<missing>')
            val2 = config2.get(key, '<missing>')
            
            if val1 != val2:
                differences[key] = {
                    env1: val1,
                    env2: val2
                }
        
        return differences

def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Environment-specific configuration management for MySQL deployment"
    )
    
    parser.add_argument(
        'command',
        choices=['deploy', 'list', 'compare', 'validate'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--environment', '-e',
        help='Environment name (required for deploy and validate)'
    )
    
    parser.add_argument(
        '--compare-with',
        help='Second environment for comparison (used with compare command)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'list':
        manager = ConfigManager('production')  # Dummy environment for listing
        environments = manager.list_environments()
        print("Available environments:")
        for env in environments:
            print(f"  - {env}")
    
    elif args.command == 'deploy':
        if not args.environment:
            print("Error: --environment is required for deploy command")
            sys.exit(1)
        
        manager = ConfigManager(args.environment)
        success = manager.deploy_configuration()
        sys.exit(0 if success else 1)
    
    elif args.command == 'validate':
        if not args.environment:
            print("Error: --environment is required for validate command")
            sys.exit(1)
        
        manager = ConfigManager(args.environment)
        try:
            config = manager.load_environment_config()
            valid = manager.validate_config(config)
            print(f"Configuration validation: {'PASSED' if valid else 'FAILED'}")
            sys.exit(0 if valid else 1)
        except Exception as e:
            print(f"Validation error: {str(e)}")
            sys.exit(1)
    
    elif args.command == 'compare':
        if not args.environment or not args.compare_with:
            print("Error: --environment and --compare-with are required for compare command")
            sys.exit(1)
        
        manager = ConfigManager(args.environment)
        try:
            differences = manager.compare_environments(args.environment, args.compare_with)
            
            if not differences:
                print(f"No differences found between {args.environment} and {args.compare_with}")
            else:
                print(f"Differences between {args.environment} and {args.compare_with}:")
                for key, values in differences.items():
                    print(f"  {key}:")
                    print(f"    {args.environment}: {values[args.environment]}")
                    print(f"    {args.compare_with}: {values[args.compare_with]}")
        except Exception as e:
            print(f"Comparison error: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main()