"""
Django management command to start the ongoing maintenance coordinator
"""

import logging
import signal
import sys
from django.core.management.base import BaseCommand
from django.conf import settings

from core.ongoing_maintenance_coordinator import start_maintenance_coordinator, stop_maintenance_coordinator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start the ongoing database maintenance coordinator'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as daemon process',
        )
        parser.add_argument(
            '--pidfile',
            type=str,
            help='Path to PID file for daemon mode',
            default='/tmp/maintenance_coordinator.pid'
        )
    
    def handle(self, *args, **options):
        """Start the maintenance coordinator"""
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            self.stdout.write(
                self.style.WARNING('Received shutdown signal, stopping maintenance coordinator...')
            )
            stop_maintenance_coordinator()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            self.stdout.write(
                self.style.SUCCESS('Starting ongoing maintenance coordinator...')
            )
            
            # Start the coordinator
            start_maintenance_coordinator()
            
            self.stdout.write(
                self.style.SUCCESS('Maintenance coordinator started successfully')
            )
            
            if options['daemon']:
                self._run_as_daemon(options['pidfile'])
            else:
                self._run_foreground()
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Interrupted by user, stopping...')
            )
            stop_maintenance_coordinator()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to start maintenance coordinator: {e}')
            )
            logger.error(f'Maintenance coordinator startup failed: {e}')
            sys.exit(1)
    
    def _run_foreground(self):
        """Run in foreground mode"""
        self.stdout.write('Maintenance coordinator running in foreground mode...')
        self.stdout.write('Press Ctrl+C to stop')
        
        try:
            # Keep the process alive
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    def _run_as_daemon(self, pidfile):
        """Run as daemon process"""
        import os
        import atexit
        
        try:
            # Fork first child
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError as e:
            self.stdout.write(
                self.style.ERROR(f'Fork #1 failed: {e}')
            )
            sys.exit(1)
        
        # Decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)
        
        try:
            # Fork second child
            pid = os.fork()
            if pid > 0:
                # Exit second parent
                sys.exit(0)
        except OSError as e:
            self.stdout.write(
                self.style.ERROR(f'Fork #2 failed: {e}')
            )
            sys.exit(1)
        
        # Write PID file
        with open(pidfile, 'w') as f:
            f.write(str(os.getpid()))
        
        # Register cleanup function
        atexit.register(lambda: os.remove(pidfile) if os.path.exists(pidfile) else None)
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Keep daemon alive
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass