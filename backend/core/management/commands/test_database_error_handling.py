"""
Management command for testing database error handling and recovery system
"""

import time
import threading
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.db.utils import OperationalError, DatabaseError

from core.database_error_handler import get_error_handler, database_error_handler, retry_on_database_error


class Command(BaseCommand):
    help = 'Test database error handling and recovery system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['connection', 'deadlock', 'timeout', 'circuit-breaker', 'all'],
            default='all',
            help='Type of error handling test to run'
        )
        
        parser.add_argument(
            '--database',
            type=str,
            default='default',
            help='Database alias to test'
        )
        
        parser.add_argument(
            '--concurrent-threads',
            type=int,
            default=5,
            help='Number of concurrent threads for deadlock testing'
        )
        
        parser.add_argument(
            '--reset-degradation',
            action='store_true',
            help='Reset degradation mode'
        )
        
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='Show error handling statistics'
        )
    
    def handle(self, *args, **options):
        error_handler = get_error_handler()
        
        if options['reset_degradation']:
            error_handler.reset_degradation_mode(options['database'])
            self.stdout.write(
                self.style.SUCCESS(f"Degradation mode reset for {options['database']}")
            )
            return
        
        if options['show_stats']:
            self._show_statistics(error_handler, options['database'])
            return
        
        test_type = options['test_type']
        database = options['database']
        
        self.stdout.write(f"Testing database error handling for {database}")
        self.stdout.write(f"Test type: {test_type}")
        
        if test_type == 'all':
            self._test_connection_errors(database)
            self._test_deadlock_handling(database, options['concurrent_threads'])
            self._test_timeout_handling(database)
            self._test_circuit_breaker(database)
        elif test_type == 'connection':
            self._test_connection_errors(database)
        elif test_type == 'deadlock':
            self._test_deadlock_handling(database, options['concurrent_threads'])
        elif test_type == 'timeout':
            self._test_timeout_handling(database)
        elif test_type == 'circuit-breaker':
            self._test_circuit_breaker(database)
        
        self.stdout.write(self.style.SUCCESS("Error handling tests completed"))
    
    def _test_connection_errors(self, database_alias: str):
        """Test connection error handling"""
        self.stdout.write("Testing connection error handling...")
        
        error_handler = get_error_handler()
        
        @database_error_handler(database_alias, 'connection_test')
        def test_connection():
            # Simulate connection error by closing connection
            connection = connections[database_alias]
            connection.close()
            
            # Try to execute query on closed connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        
        try:
            test_connection()
            self.stdout.write(self.style.SUCCESS("✓ Connection error handled successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Connection error test failed: {e}"))
    
    def _test_deadlock_handling(self, database_alias: str, num_threads: int):
        """Test deadlock detection and handling"""
        self.stdout.write(f"Testing deadlock handling with {num_threads} threads...")
        
        # Create test tables if they don't exist
        self._create_test_tables(database_alias)
        
        results = []
        threads = []
        
        def deadlock_transaction(thread_id: int):
            """Create a transaction that can cause deadlocks"""
            try:
                with transaction.atomic(using=database_alias):
                    connection = connections[database_alias]
                    with connection.cursor() as cursor:
                        # Lock rows in different order to create deadlock potential
                        if thread_id % 2 == 0:
                            cursor.execute("SELECT * FROM test_table_1 WHERE id = 1 FOR UPDATE")
                            time.sleep(0.1)
                            cursor.execute("SELECT * FROM test_table_2 WHERE id = 1 FOR UPDATE")
                        else:
                            cursor.execute("SELECT * FROM test_table_2 WHERE id = 1 FOR UPDATE")
                            time.sleep(0.1)
                            cursor.execute("SELECT * FROM test_table_1 WHERE id = 1 FOR UPDATE")
                        
                        # Update the rows
                        cursor.execute("UPDATE test_table_1 SET value = %s WHERE id = 1", [f"thread_{thread_id}"])
                        cursor.execute("UPDATE test_table_2 SET value = %s WHERE id = 1", [f"thread_{thread_id}"])
                
                results.append(f"Thread {thread_id}: Success")
                
            except Exception as e:
                error_handler = get_error_handler()
                if error_handler.deadlock_detector.detect_deadlock(e):
                    results.append(f"Thread {thread_id}: Deadlock detected and handled")
                else:
                    results.append(f"Thread {thread_id}: Error - {e}")
        
        # Start threads
        for i in range(num_threads):
            thread = threading.Thread(target=deadlock_transaction, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Show results
        for result in results:
            if "Success" in result or "handled" in result:
                self.stdout.write(self.style.SUCCESS(f"✓ {result}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠ {result}"))
    
    def _test_timeout_handling(self, database_alias: str):
        """Test timeout error handling"""
        self.stdout.write("Testing timeout handling...")
        
        @retry_on_database_error(max_attempts=3, delay=0.5)
        def test_timeout():
            connection = connections[database_alias]
            with connection.cursor() as cursor:
                # Simulate a long-running query that might timeout
                cursor.execute("SELECT SLEEP(0.1)")  # MySQL specific
        
        try:
            test_timeout()
            self.stdout.write(self.style.SUCCESS("✓ Timeout handling test completed"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠ Timeout test result: {e}"))
    
    def _test_circuit_breaker(self, database_alias: str):
        """Test circuit breaker functionality"""
        self.stdout.write("Testing circuit breaker...")
        
        error_handler = get_error_handler()
        
        # Generate multiple errors to trigger circuit breaker
        for i in range(6):  # Exceed threshold
            try:
                with error_handler.handle_database_errors(database_alias, f'circuit_test_{i}'):
                    # Simulate database error
                    raise OperationalError("Simulated database error")
            except:
                pass
        
        # Check if circuit breaker is activated
        if error_handler.is_degraded(database_alias):
            self.stdout.write(self.style.SUCCESS("✓ Circuit breaker activated successfully"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Circuit breaker not activated"))
        
        # Reset for next tests
        error_handler.reset_degradation_mode(database_alias)
    
    def _create_test_tables(self, database_alias: str):
        """Create test tables for deadlock testing"""
        connection = connections[database_alias]
        
        with connection.cursor() as cursor:
            # Create test tables if they don't exist
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_table_1 (
                        id INT PRIMARY KEY,
                        value VARCHAR(100)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_table_2 (
                        id INT PRIMARY KEY,
                        value VARCHAR(100)
                    )
                """)
                
                # Insert test data
                cursor.execute("INSERT IGNORE INTO test_table_1 (id, value) VALUES (1, 'initial')")
                cursor.execute("INSERT IGNORE INTO test_table_2 (id, value) VALUES (1, 'initial')")
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not create test tables: {e}"))
    
    def _show_statistics(self, error_handler, database_alias: str):
        """Show error handling statistics"""
        stats = error_handler.get_error_statistics(database_alias)
        
        self.stdout.write(self.style.SUCCESS("Database Error Handling Statistics"))
        self.stdout.write("=" * 50)
        
        self.stdout.write(f"Total errors: {stats['total_errors']}")
        self.stdout.write(f"Recent errors (24h): {stats['recent_errors_24h']}")
        self.stdout.write(f"Degradation mode: {stats['degradation_mode']}")
        
        if stats['degradation_start_time']:
            self.stdout.write(f"Degradation started: {stats['degradation_start_time']}")
        
        self.stdout.write("\nError types:")
        for error_type, count in stats['error_types'].items():
            self.stdout.write(f"  {error_type}: {count}")
        
        self.stdout.write("\nSeverity distribution:")
        for severity, count in stats['severity_counts'].items():
            self.stdout.write(f"  {severity}: {count}")
        
        deadlock_stats = stats['deadlock_statistics']
        self.stdout.write(f"\nDeadlock statistics:")
        self.stdout.write(f"  Total deadlocks: {deadlock_stats['total_deadlocks']}")
        self.stdout.write(f"  Recent deadlocks (24h): {deadlock_stats['recent_deadlocks_24h']}")
        
        if deadlock_stats['most_common_pattern']:
            pattern, count = deadlock_stats['most_common_pattern']
            self.stdout.write(f"  Most common pattern: {pattern} ({count} times)")