#!/usr/bin/env python
"""
Demo script for setting up read replicas

This script demonstrates how to set up and configure MySQL read replicas
for the ecommerce platform.
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

from core.read_replica_setup import ReadReplicaManager
from core.replica_health_monitor import ReplicaHealthMonitor
from django.conf import settings


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_section(title):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")


def demo_configuration():
    """Demonstrate replica configuration"""
    print_header("READ REPLICA CONFIGURATION DEMO")
    
    manager = ReadReplicaManager()
    
    print_section("Current Configuration")
    print(f"Master Config: {manager.master_config}")
    print(f"Replica Configs: {manager.replica_configs}")
    
    print_section("Django Database Configuration")
    django_config = manager.get_replica_django_config()
    
    print("Add the following to your DATABASES setting:")
    print("-" * 40)
    
    for alias, config in django_config.items():
        print(f"\n'{alias}': {{")
        for key, value in config.items():
            if isinstance(value, dict):
                print(f"    '{key}': {{")
                for sub_key, sub_value in value.items():
                    print(f"        '{sub_key}': {repr(sub_value)},")
                print("    },")
            else:
                print(f"    '{key}': {repr(value)},")
        print("},")
    
    print_section("Environment Variables")
    print("Set these environment variables for replica configuration:")
    print("-" * 50)
    
    for i, replica in enumerate(manager.replica_configs, 1):
        if len(manager.replica_configs) > 1:
            print(f"\n# Replica {i}")
            print(f"DB_REPLICA_{i}_HOST={replica['host']}")
            print(f"DB_REPLICA_{i}_PORT={replica['port']}")
            print(f"DB_REPLICA_{i}_USER={replica['user']}")
            print(f"DB_REPLICA_{i}_PASSWORD={replica['password']}")
        else:
            print(f"DB_READ_HOST={replica['host']}")
            print(f"DB_READ_PORT={replica['port']}")
            print(f"DB_READ_USER={replica['user']}")
            print(f"DB_READ_PASSWORD={replica['password']}")


def demo_setup_process():
    """Demonstrate the setup process"""
    print_header("READ REPLICA SETUP PROCESS")
    
    print_section("Step 1: Master Configuration")
    print("""
To configure the master database for replication:

1. Add the following to your MySQL configuration (my.cnf):
   [mysqld]
   log-bin=mysql-bin
   server-id=1
   binlog-format=ROW
   
2. Restart MySQL server

3. Run the setup command:
   python manage.py setup_read_replicas --setup
    """)
    
    print_section("Step 2: Replica Server Setup")
    print("""
For each replica server:

1. Install MySQL and configure with unique server-id:
   [mysqld]
   server-id=2  # Use different ID for each replica
   read-only=1
   
2. Create initial data copy:
   mysqldump --master-data=2 --single-transaction --all-databases > master_backup.sql
   mysql < master_backup.sql
   
3. The setup command will configure replication automatically
    """)
    
    print_section("Step 3: Django Configuration")
    print("""
1. Update your Django settings to include read replica databases
2. Ensure DATABASE_ROUTERS includes 'core.database_router.DatabaseRouter'
3. Configure replica monitoring settings
4. Restart your Django application
    """)


def demo_monitoring():
    """Demonstrate monitoring capabilities"""
    print_header("READ REPLICA MONITORING DEMO")
    
    monitor = ReplicaHealthMonitor()
    
    print_section("Monitoring Configuration")
    status = monitor.get_monitoring_status()
    
    print(f"Monitoring Enabled: {status['monitoring_enabled']}")
    print(f"Check Interval: {status['check_interval']}s")
    print(f"Lag Threshold: {status['lag_threshold']}s")
    print(f"Max Failures: {status['max_failures']}")
    print(f"Failure Window: {status['failure_window']}s")
    
    print_section("Available Commands")
    print("""
Monitor replica health:
  python manage.py monitor_replicas --status
  python manage.py monitor_replicas --start
  python manage.py monitor_replicas --metrics
  
Setup replicas:
  python manage.py setup_read_replicas --setup
  python manage.py setup_read_replicas --status
  python manage.py setup_read_replicas --config
    """)
    
    print_section("Health Check Demo")
    try:
        health_results = monitor.force_health_check()
        
        if health_results:
            print("Current replica health status:")
            for replica, health in health_results.items():
                status_text = "HEALTHY" if health['healthy'] else "UNHEALTHY"
                print(f"  {replica}: {status_text} (lag: {health['replication_lag']}s)")
        else:
            print("No replicas configured or available")
            
    except Exception as e:
        print(f"Health check failed: {e}")
        print("This is expected if replicas are not yet configured")


def demo_usage_examples():
    """Show usage examples"""
    print_header("USAGE EXAMPLES")
    
    print_section("Reading from Replicas")
    print("""
# Automatic read/write splitting (recommended)
from apps.products.models import Product

# This will automatically use read replica
products = Product.objects.all()

# Force read from specific database
from django.db import transaction

with transaction.using('read_replica'):
    products = Product.objects.all()

# Force read from write database (for consistency)
with transaction.using('default'):
    products = Product.objects.all()
    """)
    
    print_section("Manual Database Selection")
    print("""
from core.database_router import using_read_database, using_write_database

# Force read database
with using_read_database():
    products = Product.objects.all()

# Force write database
with using_write_database():
    products = Product.objects.all()
    """)
    
    print_section("Health Monitoring")
    print("""
from core.replica_health_monitor import get_replica_health_status

# Get current health status
health_status = get_replica_health_status()
print(health_status)

# Check router statistics
from core.database_router import get_router_stats
stats = get_router_stats()
print(stats)
    """)


def demo_troubleshooting():
    """Show troubleshooting information"""
    print_header("TROUBLESHOOTING")
    
    print_section("Common Issues")
    print("""
1. Replica connection fails:
   - Check network connectivity between master and replica
   - Verify replica user credentials
   - Ensure firewall allows MySQL connections
   
2. High replication lag:
   - Check replica server resources (CPU, memory, disk I/O)
   - Verify network bandwidth between master and replica
   - Consider optimizing queries or adding more replicas
   
3. Replication stops:
   - Check MySQL error logs on both master and replica
   - Verify binary log files are not corrupted
   - Check for duplicate key errors or other data conflicts
   
4. Django routing issues:
   - Verify DATABASE_ROUTERS setting includes DatabaseRouter
   - Check that read replica databases are marked with READ_REPLICA=True
   - Ensure cache is working for health status caching
    """)
    
    print_section("Diagnostic Commands")
    print("""
# Check replica status
python manage.py setup_read_replicas --status

# Monitor replica health
python manage.py monitor_replicas --force-check

# Test replica functionality
python test_read_replicas.py

# Check Django database configuration
python manage.py shell
>>> from django.conf import settings
>>> print(settings.DATABASES)
    """)
    
    print_section("MySQL Commands")
    print("""
# On master - check binary log status
SHOW MASTER STATUS;

# On replica - check replication status
SHOW SLAVE STATUS\\G

# Check replication lag
SELECT TIMESTAMPDIFF(SECOND, NOW(), TIMESTAMP) as lag_seconds 
FROM information_schema.REPLICA_HOST_STATUS;
    """)


def main():
    """Main demo function"""
    print("MySQL Read Replica Setup and Configuration Demo")
    print("This demo shows how to set up and use read replicas")
    
    try:
        demo_configuration()
        demo_setup_process()
        demo_monitoring()
        demo_usage_examples()
        demo_troubleshooting()
        
        print_header("DEMO COMPLETE")
        print("""
Next steps:
1. Configure your replica servers
2. Run: python manage.py setup_read_replicas --setup
3. Start monitoring: python manage.py monitor_replicas --start
4. Test the setup: python test_read_replicas.py

For more information, check the documentation or run:
python manage.py help setup_read_replicas
python manage.py help monitor_replicas
        """)
        
    except Exception as e:
        print(f"Demo failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()