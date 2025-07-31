"""
Management command to set up MySQL read replicas
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.read_replica_setup import ReadReplicaManager, ReplicationHealthChecker

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up and configure MySQL read replicas for load distribution'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--setup',
            action='store_true',
            help='Set up read replicas from scratch',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Check status of existing replicas',
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Start continuous monitoring of replica health',
        )
        parser.add_argument(
            '--failover',
            type=str,
            help='Perform manual failover for specified replica',
        )
        parser.add_argument(
            '--config',
            action='store_true',
            help='Generate Django database configuration for replicas',
        )
    
    def handle(self, *args, **options):
        manager = ReadReplicaManager()
        
        if options['setup']:
            self.setup_replicas(manager)
        elif options['status']:
            self.check_status(manager)
        elif options['monitor']:
            self.start_monitoring()
        elif options['failover']:
            self.perform_failover(manager, options['failover'])
        elif options['config']:
            self.show_config(manager)
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify an action: --setup, --status, --monitor, --failover, or --config'
                )
            )
    
    def setup_replicas(self, manager):
        """Set up read replicas"""
        self.stdout.write("Setting up MySQL read replicas...")
        
        try:
            success = manager.setup_all_replicas()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('Read replicas set up successfully!')
                )
                
                # Show status after setup
                self.check_status(manager)
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to set up read replicas. Check logs for details.')
                )
                
        except Exception as e:
            raise CommandError(f'Error setting up replicas: {e}')
    
    def check_status(self, manager):
        """Check replica status"""
        self.stdout.write("Checking replica status...")
        
        try:
            status = manager.check_replication_status()
            lag_status = manager.monitor_replication_lag()
            
            if not status:
                self.stdout.write(
                    self.style.WARNING('No replicas configured.')
                )
                return
            
            self.stdout.write("\nReplica Status:")
            self.stdout.write("-" * 50)
            
            for replica_alias, replica_info in status.items():
                lag = lag_status.get(replica_alias, -1)
                
                if replica_info.get('healthy', False):
                    status_color = self.style.SUCCESS
                    status_text = "HEALTHY"
                else:
                    status_color = self.style.ERROR
                    status_text = "UNHEALTHY"
                
                self.stdout.write(f"\n{replica_alias}:")
                self.stdout.write(f"  Status: {status_color(status_text)}")
                self.stdout.write(f"  IO Running: {replica_info.get('io_running', 'Unknown')}")
                self.stdout.write(f"  SQL Running: {replica_info.get('sql_running', 'Unknown')}")
                self.stdout.write(f"  Replication Lag: {lag}s" if lag >= 0 else "  Replication Lag: Unknown")
                
                if replica_info.get('last_error'):
                    self.stdout.write(f"  Last Error: {replica_info['last_error']}")
                
                if 'error' in replica_info:
                    self.stdout.write(f"  Error: {replica_info['error']}")
            
            # Summary
            healthy_count = sum(1 for info in status.values() if info.get('healthy', False))
            total_count = len(status)
            
            self.stdout.write(f"\nSummary: {healthy_count}/{total_count} replicas healthy")
            
        except Exception as e:
            raise CommandError(f'Error checking replica status: {e}')
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.stdout.write("Starting continuous replica health monitoring...")
        self.stdout.write("Press Ctrl+C to stop monitoring")
        
        try:
            checker = ReplicationHealthChecker()
            checker.start_monitoring()
        except KeyboardInterrupt:
            self.stdout.write("\nMonitoring stopped.")
        except Exception as e:
            raise CommandError(f'Error in monitoring: {e}')
    
    def perform_failover(self, manager, replica_alias):
        """Perform manual failover"""
        self.stdout.write(f"Performing failover for replica: {replica_alias}")
        
        try:
            success = manager.failover_replica(replica_alias)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'Failover completed for {replica_alias}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failover failed for {replica_alias}')
                )
                
        except Exception as e:
            raise CommandError(f'Error performing failover: {e}')
    
    def show_config(self, manager):
        """Show Django database configuration"""
        self.stdout.write("Django database configuration for read replicas:")
        
        try:
            config = manager.get_replica_django_config()
            
            self.stdout.write("\nAdd the following to your DATABASES setting:")
            self.stdout.write("-" * 50)
            
            for alias, db_config in config.items():
                self.stdout.write(f"\n'{alias}': {{")
                for key, value in db_config.items():
                    if isinstance(value, dict):
                        self.stdout.write(f"    '{key}': {{")
                        for sub_key, sub_value in value.items():
                            self.stdout.write(f"        '{sub_key}': {repr(sub_value)},")
                        self.stdout.write("    },")
                    else:
                        self.stdout.write(f"    '{key}': {repr(value)},")
                self.stdout.write("},")
            
            self.stdout.write("\nEnvironment variables needed:")
            self.stdout.write("-" * 30)
            
            for i, replica_config in enumerate(manager.replica_configs, 1):
                if len(manager.replica_configs) > 1:
                    self.stdout.write(f"\n# Replica {i}")
                    self.stdout.write(f"DB_REPLICA_{i}_HOST={replica_config['host']}")
                    self.stdout.write(f"DB_REPLICA_{i}_PORT={replica_config['port']}")
                    self.stdout.write(f"DB_REPLICA_{i}_USER={replica_config['user']}")
                    self.stdout.write(f"DB_REPLICA_{i}_PASSWORD={replica_config['password']}")
                    self.stdout.write(f"DB_REPLICA_{i}_NAME={replica_config['database']}")
                else:
                    self.stdout.write(f"\nDB_READ_HOST={replica_config['host']}")
                    self.stdout.write(f"DB_READ_PORT={replica_config['port']}")
                    self.stdout.write(f"DB_READ_USER={replica_config['user']}")
                    self.stdout.write(f"DB_READ_PASSWORD={replica_config['password']}")
                    self.stdout.write(f"DB_READ_NAME={replica_config['database']}")
                    
        except Exception as e:
            raise CommandError(f'Error generating configuration: {e}')