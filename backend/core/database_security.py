"""
Database Security Manager for MySQL Database Integration

This module implements comprehensive database security measures including:
- Role-based access control with minimal privileges
- Field-level encryption for sensitive data
- Comprehensive audit logging and monitoring
- SSL/TLS encryption configuration
- Database user management
- Security threat detection

Requirements: 4.1, 4.2, 4.4, 4.5, 4.6
"""

import os
import logging
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import mysql.connector
from mysql.connector import Error as MySQLError
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import connection
from django.contrib.auth.models import User
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different types of data and operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(Enum):
    """Types of audit events to track."""
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"
    CONFIGURATION_CHANGE = "configuration_change"
    BACKUP_ACCESS = "backup_access"


@dataclass
class DatabaseUser:
    """Database user configuration with role-based permissions."""
    username: str
    password: str
    host: str
    privileges: List[str]
    databases: List[str]
    tables: Dict[str, List[str]]  # table_name: [permissions]
    max_connections: int
    ssl_required: bool
    password_expire_days: int
    account_locked: bool = False
    created_at: datetime = None
    last_login: datetime = None


@dataclass
class AuditLogEntry:
    """Audit log entry structure."""
    timestamp: datetime
    event_type: AuditEventType
    user: str
    source_ip: str
    database: str
    table: str
    operation: str
    affected_rows: int
    query_hash: str
    success: bool
    error_message: str = None
    additional_data: Dict[str, Any] = None


class FieldEncryption:
    """Field-level encryption for sensitive data."""
    
    def __init__(self, encryption_key: str = None):
        """Initialize field encryption with key."""
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            self.key = settings.SECRET_KEY.encode()
        
        # Derive encryption key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ecommerce_salt',  # In production, use random salt per field
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.key))
        self.cipher = Fernet(key)
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt a field value."""
        if not value:
            return value
        
        try:
            encrypted_value = self.cipher.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted_value).decode()
        except Exception as e:
            logger.error(f"Field encryption failed: {e}")
            raise
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a field value."""
        if not encrypted_value:
            return encrypted_value
        
        try:
            decoded_value = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted_value = self.cipher.decrypt(decoded_value)
            return decrypted_value.decode()
        except Exception as e:
            logger.error(f"Field decryption failed: {e}")
            raise
    
    def is_encrypted(self, value: str) -> bool:
        """Check if a value is encrypted."""
        try:
            if not value:
                return False
            decoded = base64.urlsafe_b64decode(value.encode())
            self.cipher.decrypt(decoded)
            return True
        except:
            return False


class DatabaseSecurityManager:
    """Comprehensive database security management."""
    
    def __init__(self):
        """Initialize the database security manager."""
        self.connection_config = self._get_connection_config()
        self.field_encryption = FieldEncryption()
        self.audit_enabled = getattr(settings, 'DB_AUDIT_ENABLED', True)
        self.threat_detection_enabled = getattr(settings, 'DB_THREAT_DETECTION_ENABLED', True)
        self.max_failed_attempts = getattr(settings, 'DB_MAX_FAILED_ATTEMPTS', 5)
        self.lockout_duration = getattr(settings, 'DB_LOCKOUT_DURATION', 3600)  # 1 hour
        
        # Initialize security monitoring
        self._init_security_monitoring()
    
    def _get_connection_config(self) -> Dict[str, Any]:
        """Get database connection configuration."""
        db_config = settings.DATABASES['default']
        return {
            'host': db_config['HOST'],
            'port': int(db_config['PORT']),
            'database': db_config['NAME'],
            'user': db_config['USER'],
            'password': db_config['PASSWORD'],
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True,
            'ssl_disabled': False,
            'ssl_verify_cert': True,
            'ssl_verify_identity': True,
        }
    
    def _init_security_monitoring(self):
        """Initialize security monitoring components."""
        try:
            # Create audit log table if it doesn't exist
            self._create_audit_tables()
            
            # Set up threat detection rules
            self._setup_threat_detection()
            
            logger.info("Database security monitoring initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize security monitoring: {e}")
    
    def _create_audit_tables(self):
        """Create audit logging tables."""
        create_audit_table_sql = """
        CREATE TABLE IF NOT EXISTS db_audit_log (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME(6) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            user VARCHAR(100) NOT NULL,
            source_ip VARCHAR(45),
            database_name VARCHAR(100),
            table_name VARCHAR(100),
            operation VARCHAR(50),
            affected_rows INT DEFAULT 0,
            query_hash VARCHAR(64),
            success BOOLEAN NOT NULL,
            error_message TEXT,
            additional_data JSON,
            INDEX idx_audit_timestamp (timestamp),
            INDEX idx_audit_user (user),
            INDEX idx_audit_event_type (event_type),
            INDEX idx_audit_source_ip (source_ip)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        create_security_events_table_sql = """
        CREATE TABLE IF NOT EXISTS db_security_events (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME(6) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            user VARCHAR(100),
            source_ip VARCHAR(45),
            description TEXT NOT NULL,
            details JSON,
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at DATETIME(6),
            resolved_by VARCHAR(100),
            INDEX idx_security_timestamp (timestamp),
            INDEX idx_security_severity (severity),
            INDEX idx_security_resolved (resolved)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(create_audit_table_sql)
                cursor.execute(create_security_events_table_sql)
            logger.info("Audit tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create audit tables: {e}")
    
    def _setup_threat_detection(self):
        """Set up threat detection rules and monitoring."""
        self.threat_rules = {
            'sql_injection_patterns': [
                r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
                r"(--|#|/\*|\*/)",
                r"(\b(or|and)\s+\d+\s*=\s*\d+)",
                r"(\b(or|and)\s+['\"].*['\"])",
            ],
            'suspicious_queries': [
                r"(information_schema|mysql\.user|mysql\.db)",
                r"(show\s+(databases|tables|columns|grants))",
                r"(load_file|into\s+outfile|into\s+dumpfile)",
            ],
            'privilege_escalation': [
                r"(grant|revoke)\s+",
                r"(create\s+user|drop\s+user|alter\s+user)",
                r"(set\s+password|change\s+master)",
            ]
        }
    
    def setup_ssl_encryption(self) -> bool:
        """Configure SSL encryption for database connections."""
        try:
            ssl_config = {
                'ssl_ca': getattr(settings, 'DB_SSL_CA', '/etc/mysql/ssl/ca-cert.pem'),
                'ssl_cert': getattr(settings, 'DB_SSL_CERT', '/etc/mysql/ssl/client-cert.pem'),
                'ssl_key': getattr(settings, 'DB_SSL_KEY', '/etc/mysql/ssl/client-key.pem'),
                'ssl_verify_cert': True,
                'ssl_verify_identity': True,
            }
            
            # Test SSL connection
            test_config = self.connection_config.copy()
            test_config.update(ssl_config)
            
            conn = mysql.connector.connect(**test_config)
            cursor = conn.cursor()
            cursor.execute("SHOW STATUS LIKE 'Ssl_cipher'")
            result = cursor.fetchone()
            
            if result and result[1]:
                logger.info(f"SSL encryption enabled with cipher: {result[1]}")
                cursor.close()
                conn.close()
                return True
            else:
                logger.warning("SSL connection established but no cipher detected")
                cursor.close()
                conn.close()
                return False
                
        except MySQLError as e:
            logger.error(f"Failed to configure SSL encryption: {e}")
            return False
    
    def create_database_users(self) -> Dict[str, bool]:
        """Create role-based database users with minimal privileges."""
        users_config = {
            'ecommerce_read': DatabaseUser(
                username='ecommerce_read',
                password=self._generate_secure_password(),
                host='%',
                privileges=['SELECT'],
                databases=['ecommerce_db'],
                tables={
                    'products_product': ['SELECT'],
                    'products_category': ['SELECT'],
                    'orders_order': ['SELECT'],
                    'auth_user': ['SELECT'],
                    'customers_customer': ['SELECT'],
                },
                max_connections=50,
                ssl_required=True,
                password_expire_days=90
            ),
            'ecommerce_write': DatabaseUser(
                username='ecommerce_write',
                password=self._generate_secure_password(),
                host='%',
                privileges=['SELECT', 'INSERT', 'UPDATE'],
                databases=['ecommerce_db'],
                tables={
                    'products_product': ['SELECT', 'INSERT', 'UPDATE'],
                    'orders_order': ['SELECT', 'INSERT', 'UPDATE'],
                    'cart_cartitem': ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
                    'inventory_inventory': ['SELECT', 'UPDATE'],
                },
                max_connections=30,
                ssl_required=True,
                password_expire_days=60
            ),
            'ecommerce_admin': DatabaseUser(
                username='ecommerce_admin',
                password=self._generate_secure_password(),
                host='localhost',
                privileges=['ALL PRIVILEGES'],
                databases=['ecommerce_db'],
                tables={},
                max_connections=5,
                ssl_required=True,
                password_expire_days=30
            ),
            'ecommerce_backup': DatabaseUser(
                username='ecommerce_backup',
                password=self._generate_secure_password(),
                host='localhost',
                privileges=['SELECT', 'LOCK TABLES', 'SHOW VIEW', 'EVENT', 'TRIGGER'],
                databases=['ecommerce_db'],
                tables={},
                max_connections=2,
                ssl_required=True,
                password_expire_days=180
            ),
            'ecommerce_monitor': DatabaseUser(
                username='ecommerce_monitor',
                password=self._generate_secure_password(),
                host='%',
                privileges=['SELECT', 'PROCESS', 'REPLICATION CLIENT'],
                databases=['information_schema', 'performance_schema'],
                tables={},
                max_connections=10,
                ssl_required=True,
                password_expire_days=120
            )
        }
        
        results = {}
        
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            for username, user_config in users_config.items():
                try:
                    # Create user
                    create_user_sql = f"""
                    CREATE USER IF NOT EXISTS '{user_config.username}'@'{user_config.host}' 
                    IDENTIFIED BY '{user_config.password}'
                    REQUIRE SSL
                    WITH MAX_CONNECTIONS_PER_HOUR {user_config.max_connections}
                    PASSWORD EXPIRE INTERVAL {user_config.password_expire_days} DAY
                    """
                    cursor.execute(create_user_sql)
                    
                    # Grant database-level privileges
                    for db in user_config.databases:
                        if user_config.privileges:
                            privileges = ', '.join(user_config.privileges)
                            grant_sql = f"GRANT {privileges} ON {db}.* TO '{user_config.username}'@'{user_config.host}'"
                            cursor.execute(grant_sql)
                    
                    # Grant table-level privileges
                    for table, table_privileges in user_config.tables.items():
                        if table_privileges:
                            privileges = ', '.join(table_privileges)
                            grant_sql = f"GRANT {privileges} ON ecommerce_db.{table} TO '{user_config.username}'@'{user_config.host}'"
                            cursor.execute(grant_sql)
                    
                    cursor.execute("FLUSH PRIVILEGES")
                    results[username] = True
                    
                    # Log user creation
                    self.log_audit_event(
                        event_type=AuditEventType.CONFIGURATION_CHANGE,
                        user='system',
                        source_ip='localhost',
                        database='mysql',
                        table='user',
                        operation='CREATE_USER',
                        affected_rows=1,
                        query_hash=hashlib.sha256(create_user_sql.encode()).hexdigest()[:16],
                        success=True,
                        additional_data={'username': user_config.username, 'privileges': user_config.privileges}
                    )
                    
                    logger.info(f"Database user '{username}' created successfully")
                    
                except MySQLError as e:
                    logger.error(f"Failed to create user '{username}': {e}")
                    results[username] = False
            
            cursor.close()
            conn.close()
            
        except MySQLError as e:
            logger.error(f"Failed to connect to database for user creation: {e}")
            return {username: False for username in users_config.keys()}
        
        return results
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure random password."""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def setup_audit_logging(self) -> bool:
        """Set up comprehensive audit logging."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            # Enable general query log for audit purposes
            audit_config_sql = [
                "SET GLOBAL general_log = 'ON'",
                "SET GLOBAL log_output = 'TABLE'",
                "SET GLOBAL slow_query_log = 'ON'",
                "SET GLOBAL long_query_time = 2",
                "SET GLOBAL log_queries_not_using_indexes = 'ON'",
            ]
            
            for sql in audit_config_sql:
                try:
                    cursor.execute(sql)
                    logger.info(f"Executed audit configuration: {sql}")
                except MySQLError as e:
                    logger.warning(f"Failed to execute audit config '{sql}': {e}")
            
            # Create audit triggers for sensitive tables
            self._create_audit_triggers(cursor)
            
            cursor.close()
            conn.close()
            
            logger.info("Audit logging configured successfully")
            return True
            
        except MySQLError as e:
            logger.error(f"Failed to setup audit logging: {e}")
            return False
    
    def _create_audit_triggers(self, cursor):
        """Create audit triggers for sensitive tables."""
        sensitive_tables = [
            'auth_user',
            'customers_customer',
            'orders_order',
            'payments_payment',
            'products_product'
        ]
        
        for table in sensitive_tables:
            # Create INSERT trigger
            insert_trigger_sql = f"""
            CREATE TRIGGER IF NOT EXISTS {table}_audit_insert
            AFTER INSERT ON {table}
            FOR EACH ROW
            BEGIN
                INSERT INTO db_audit_log (
                    timestamp, event_type, user, database_name, table_name, 
                    operation, affected_rows, success
                ) VALUES (
                    NOW(6), 'DATA_MODIFICATION', USER(), DATABASE(), '{table}', 
                    'INSERT', 1, TRUE
                );
            END
            """
            
            # Create UPDATE trigger
            update_trigger_sql = f"""
            CREATE TRIGGER IF NOT EXISTS {table}_audit_update
            AFTER UPDATE ON {table}
            FOR EACH ROW
            BEGIN
                INSERT INTO db_audit_log (
                    timestamp, event_type, user, database_name, table_name, 
                    operation, affected_rows, success
                ) VALUES (
                    NOW(6), 'DATA_MODIFICATION', USER(), DATABASE(), '{table}', 
                    'UPDATE', 1, TRUE
                );
            END
            """
            
            # Create DELETE trigger
            delete_trigger_sql = f"""
            CREATE TRIGGER IF NOT EXISTS {table}_audit_delete
            AFTER DELETE ON {table}
            FOR EACH ROW
            BEGIN
                INSERT INTO db_audit_log (
                    timestamp, event_type, user, database_name, table_name, 
                    operation, affected_rows, success
                ) VALUES (
                    NOW(6), 'DATA_MODIFICATION', USER(), DATABASE(), '{table}', 
                    'DELETE', 1, TRUE
                );
            END
            """
            
            try:
                cursor.execute(insert_trigger_sql)
                cursor.execute(update_trigger_sql)
                cursor.execute(delete_trigger_sql)
                logger.info(f"Audit triggers created for table: {table}")
            except MySQLError as e:
                logger.error(f"Failed to create audit triggers for {table}: {e}")
    
    def encrypt_sensitive_data(self, table_name: str, sensitive_fields: List[str]) -> bool:
        """Implement field-level encryption for sensitive data."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            # Get current data
            select_sql = f"SELECT id, {', '.join(sensitive_fields)} FROM {table_name}"
            cursor.execute(select_sql)
            rows = cursor.fetchall()
            
            # Encrypt and update data
            for row in rows:
                record_id = row[0]
                encrypted_values = []
                
                for i, field_value in enumerate(row[1:], 1):
                    if field_value and not self.field_encryption.is_encrypted(str(field_value)):
                        encrypted_value = self.field_encryption.encrypt_field(str(field_value))
                        encrypted_values.append((sensitive_fields[i-1], encrypted_value))
                
                if encrypted_values:
                    update_parts = [f"{field} = %s" for field, _ in encrypted_values]
                    update_sql = f"UPDATE {table_name} SET {', '.join(update_parts)} WHERE id = %s"
                    values = [value for _, value in encrypted_values] + [record_id]
                    cursor.execute(update_sql, values)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Log encryption activity
            self.log_audit_event(
                event_type=AuditEventType.CONFIGURATION_CHANGE,
                user='system',
                source_ip='localhost',
                database='ecommerce_db',
                table=table_name,
                operation='ENCRYPT_FIELDS',
                affected_rows=len(rows),
                query_hash=hashlib.sha256(f"encrypt_{table_name}".encode()).hexdigest()[:16],
                success=True,
                additional_data={'encrypted_fields': sensitive_fields}
            )
            
            logger.info(f"Encrypted sensitive fields in {table_name}: {sensitive_fields}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to encrypt sensitive data in {table_name}: {e}")
            return False
    
    def log_audit_event(self, event_type: AuditEventType, user: str, source_ip: str,
                       database: str, table: str, operation: str, affected_rows: int,
                       query_hash: str, success: bool, error_message: str = None,
                       additional_data: Dict[str, Any] = None):
        """Log an audit event."""
        if not self.audit_enabled:
            return
        
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            insert_sql = """
            INSERT INTO db_audit_log (
                timestamp, event_type, user, source_ip, database_name, table_name,
                operation, affected_rows, query_hash, success, error_message, additional_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                datetime.now(),
                event_type.value,
                user,
                source_ip,
                database,
                table,
                operation,
                affected_rows,
                query_hash,
                success,
                error_message,
                json.dumps(additional_data) if additional_data else None
            )
            
            cursor.execute(insert_sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def detect_threats(self, query: str, user: str, source_ip: str) -> Tuple[bool, List[str]]:
        """Detect potential security threats in database queries."""
        if not self.threat_detection_enabled:
            return False, []
        
        threats_detected = []
        query_lower = query.lower()
        
        # Check for SQL injection patterns
        import re
        for pattern in self.threat_rules['sql_injection_patterns']:
            if re.search(pattern, query_lower, re.IGNORECASE):
                threats_detected.append(f"SQL injection pattern detected: {pattern}")
        
        # Check for suspicious queries
        for pattern in self.threat_rules['suspicious_queries']:
            if re.search(pattern, query_lower, re.IGNORECASE):
                threats_detected.append(f"Suspicious query pattern detected: {pattern}")
        
        # Check for privilege escalation attempts
        for pattern in self.threat_rules['privilege_escalation']:
            if re.search(pattern, query_lower, re.IGNORECASE):
                threats_detected.append(f"Privilege escalation attempt detected: {pattern}")
        
        # Check for unusual access patterns
        if self._is_unusual_access_pattern(user, source_ip):
            threats_detected.append("Unusual access pattern detected")
        
        if threats_detected:
            # Log security event
            self._log_security_event(
                event_type="THREAT_DETECTED",
                severity="HIGH",
                user=user,
                source_ip=source_ip,
                description=f"Security threats detected in query: {'; '.join(threats_detected)}",
                details={
                    'query_hash': hashlib.sha256(query.encode()).hexdigest()[:16],
                    'threats': threats_detected,
                    'query_length': len(query)
                }
            )
            
            return True, threats_detected
        
        return False, []
    
    def _is_unusual_access_pattern(self, user: str, source_ip: str) -> bool:
        """Check for unusual access patterns."""
        cache_key = f"db_access_{user}_{source_ip}"
        access_history = cache.get(cache_key, [])
        
        current_time = timezone.now()
        
        # Remove old entries (older than 1 hour)
        access_history = [
            timestamp for timestamp in access_history
            if current_time - timestamp < timedelta(hours=1)
        ]
        
        # Add current access
        access_history.append(current_time)
        cache.set(cache_key, access_history, 3600)  # Cache for 1 hour
        
        # Check for unusual patterns
        if len(access_history) > 100:  # More than 100 queries per hour
            return True
        
        # Check for rapid successive queries (more than 10 per minute)
        recent_queries = [
            timestamp for timestamp in access_history
            if current_time - timestamp < timedelta(minutes=1)
        ]
        
        if len(recent_queries) > 10:
            return True
        
        return False
    
    def _log_security_event(self, event_type: str, severity: str, user: str,
                           source_ip: str, description: str, details: Dict[str, Any]):
        """Log a security event."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            insert_sql = """
            INSERT INTO db_security_events (
                timestamp, event_type, severity, user, source_ip, description, details
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                datetime.now(),
                event_type,
                severity,
                user,
                source_ip,
                description,
                json.dumps(details)
            )
            
            cursor.execute(insert_sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            
            # Send alert for high severity events
            if severity in ['HIGH', 'CRITICAL']:
                self._send_security_alert(event_type, severity, user, source_ip, description)
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _send_security_alert(self, event_type: str, severity: str, user: str,
                            source_ip: str, description: str):
        """Send security alert notifications."""
        try:
            subject = f"Database Security Alert - {severity}"
            message = f"""
            Security Event Detected:
            
            Event Type: {event_type}
            Severity: {severity}
            User: {user}
            Source IP: {source_ip}
            Description: {description}
            Timestamp: {datetime.now()}
            
            Please investigate immediately.
            """
            
            # Get alert recipients from settings
            recipients = getattr(settings, 'DB_SECURITY_ALERT_RECIPIENTS', [])
            if recipients:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipients,
                    fail_silently=False
                )
                logger.info(f"Security alert sent for {event_type}")
            
        except Exception as e:
            logger.error(f"Failed to send security alert: {e}")
    
    def monitor_failed_login_attempts(self, user: str, source_ip: str, success: bool):
        """Monitor and handle failed login attempts."""
        cache_key = f"db_login_attempts_{user}_{source_ip}"
        attempts = cache.get(cache_key, 0)
        
        if success:
            # Reset failed attempts on successful login
            cache.delete(cache_key)
            
            # Log successful login
            self.log_audit_event(
                event_type=AuditEventType.LOGIN_SUCCESS,
                user=user,
                source_ip=source_ip,
                database='ecommerce_db',
                table='auth_user',
                operation='LOGIN',
                affected_rows=1,
                query_hash=hashlib.sha256(f"login_{user}".encode()).hexdigest()[:16],
                success=True
            )
        else:
            # Increment failed attempts
            attempts += 1
            cache.set(cache_key, attempts, self.lockout_duration)
            
            # Log failed login
            self.log_audit_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                user=user,
                source_ip=source_ip,
                database='ecommerce_db',
                table='auth_user',
                operation='LOGIN',
                affected_rows=0,
                query_hash=hashlib.sha256(f"login_{user}".encode()).hexdigest()[:16],
                success=False,
                error_message="Authentication failed"
            )
            
            # Check if account should be locked
            if attempts >= self.max_failed_attempts:
                self._lock_account(user, source_ip)
    
    def _lock_account(self, user: str, source_ip: str):
        """Lock account after too many failed attempts."""
        lock_key = f"db_account_locked_{user}"
        cache.set(lock_key, True, self.lockout_duration)
        
        # Log security event
        self._log_security_event(
            event_type="ACCOUNT_LOCKED",
            severity="MEDIUM",
            user=user,
            source_ip=source_ip,
            description=f"Account locked due to {self.max_failed_attempts} failed login attempts",
            details={'lockout_duration': self.lockout_duration}
        )
        
        logger.warning(f"Account {user} locked due to failed login attempts from {source_ip}")
    
    def is_account_locked(self, user: str) -> bool:
        """Check if an account is locked."""
        lock_key = f"db_account_locked_{user}"
        return cache.get(lock_key, False)
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and statistics."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            # Get audit log statistics
            cursor.execute("""
                SELECT 
                    event_type,
                    COUNT(*) as count,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
                FROM db_audit_log 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY event_type
            """)
            audit_stats = cursor.fetchall()
            
            # Get security events statistics
            cursor.execute("""
                SELECT 
                    severity,
                    COUNT(*) as count,
                    SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved
                FROM db_security_events 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY severity
            """)
            security_stats = cursor.fetchall()
            
            # Get top users by activity
            cursor.execute("""
                SELECT user, COUNT(*) as activity_count
                FROM db_audit_log 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY user
                ORDER BY activity_count DESC
                LIMIT 10
            """)
            top_users = cursor.fetchall()
            
            # Get top source IPs
            cursor.execute("""
                SELECT source_ip, COUNT(*) as request_count
                FROM db_audit_log 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                AND source_ip IS NOT NULL
                GROUP BY source_ip
                ORDER BY request_count DESC
                LIMIT 10
            """)
            top_ips = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'audit_statistics': [
                    {
                        'event_type': row[0],
                        'total_count': row[1],
                        'successful': row[2],
                        'failed': row[3]
                    } for row in audit_stats
                ],
                'security_events': [
                    {
                        'severity': row[0],
                        'total_count': row[1],
                        'resolved': row[2]
                    } for row in security_stats
                ],
                'top_users': [
                    {'user': row[0], 'activity_count': row[1]} for row in top_users
                ],
                'top_source_ips': [
                    {'source_ip': row[0], 'request_count': row[1]} for row in top_ips
                ],
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get security metrics: {e}")
            return {}
    
    def cleanup_old_audit_logs(self, retention_days: int = 90):
        """Clean up old audit logs based on retention policy."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            # Delete old audit logs
            delete_sql = """
            DELETE FROM db_audit_log 
            WHERE timestamp < DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            cursor.execute(delete_sql, (retention_days,))
            deleted_audit_rows = cursor.rowcount
            
            # Delete old security events (keep resolved ones longer)
            delete_security_sql = """
            DELETE FROM db_security_events 
            WHERE timestamp < DATE_SUB(NOW(), INTERVAL %s DAY)
            AND resolved = 1
            """
            cursor.execute(delete_security_sql, (retention_days * 2,))  # Keep resolved events twice as long
            deleted_security_rows = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_audit_rows} audit log entries and {deleted_security_rows} security events")
            
            return {
                'deleted_audit_logs': deleted_audit_rows,
                'deleted_security_events': deleted_security_rows
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {e}")
            return {'error': str(e)}


# Singleton instance
database_security_manager = DatabaseSecurityManager()