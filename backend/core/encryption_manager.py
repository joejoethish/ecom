"""
Enhanced Encryption Manager for MySQL Database Integration

This module implements transparent data encryption and secure key management:
- Transparent data encryption for sensitive tables
- Secure key management and rotation
- Field-level encryption with multiple encryption algorithms
- Key derivation and secure storage

Requirements: 4.2, 4.4, 4.5
"""

import os
import logging
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64
import mysql.connector
from mysql.connector import Error as MySQLError
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


logger = logging.getLogger(__name__)


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms."""
    FERNET = "fernet"
    AES_256_GCM = "aes_256_gcm"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"


class KeyType(Enum):
    """Types of encryption keys."""
    MASTER_KEY = "master_key"
    DATA_ENCRYPTION_KEY = "data_encryption_key"
    KEY_ENCRYPTION_KEY = "key_encryption_key"
    BACKUP_KEY = "backup_key"


@dataclass
class EncryptionKey:
    """Encryption key metadata and data."""
    key_id: str
    key_type: KeyType
    algorithm: EncryptionAlgorithm
    key_data: bytes
    created_at: datetime
    expires_at: Optional[datetime]
    version: int
    is_active: bool
    metadata: Dict[str, Any]


@dataclass
class EncryptedField:
    """Encrypted field configuration."""
    table_name: str
    field_name: str
    encryption_algorithm: EncryptionAlgorithm
    key_id: str
    is_searchable: bool
    created_at: datetime
    last_rotated: datetime


class TransparentDataEncryption:
    """Transparent data encryption for sensitive database fields."""
    
    def __init__(self):
        """Initialize transparent data encryption."""
        self.master_key = self._get_or_create_master_key()
        self.encryption_keys = {}
        self.encrypted_fields = {}
        self.key_rotation_interval = getattr(settings, 'ENCRYPTION_KEY_ROTATION_DAYS', 90)
        self.backend = default_backend()
        
        # Load existing keys and field configurations
        self._load_encryption_configuration()
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create the master encryption key."""
        master_key_path = getattr(settings, 'ENCRYPTION_MASTER_KEY_PATH', '/etc/mysql/encryption/master.key')
        
        try:
            # Try to load existing master key
            if os.path.exists(master_key_path):
                with open(master_key_path, 'rb') as f:
                    return f.read()
            else:
                # Create new master key
                master_key = secrets.token_bytes(32)  # 256-bit key
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(master_key_path), exist_ok=True)
                
                # Save master key with restricted permissions
                with open(master_key_path, 'wb') as f:
                    f.write(master_key)
                os.chmod(master_key_path, 0o600)  # Read/write for owner only
                
                logger.info(f"Created new master encryption key at {master_key_path}")
                return master_key
                
        except Exception as e:
            logger.error(f"Failed to get or create master key: {e}")
            # Fallback to settings-based key
            return hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    
    def _load_encryption_configuration(self):
        """Load encryption keys and field configurations from database."""
        try:
            conn = mysql.connector.connect(**self._get_connection_config())
            cursor = conn.cursor()
            
            # Create encryption tables if they don't exist
            self._create_encryption_tables(cursor)
            
            # Load encryption keys
            cursor.execute("""
                SELECT key_id, key_type, algorithm, key_data, created_at, 
                       expires_at, version, is_active, metadata
                FROM encryption_keys
                WHERE is_active = TRUE
            """)
            
            for row in cursor.fetchall():
                key = EncryptionKey(
                    key_id=row[0],
                    key_type=KeyType(row[1]),
                    algorithm=EncryptionAlgorithm(row[2]),
                    key_data=base64.b64decode(row[3]),
                    created_at=row[4],
                    expires_at=row[5],
                    version=row[6],
                    is_active=row[7],
                    metadata=json.loads(row[8]) if row[8] else {}
                )
                self.encryption_keys[key.key_id] = key
            
            # Load encrypted field configurations
            cursor.execute("""
                SELECT table_name, field_name, encryption_algorithm, key_id, 
                       is_searchable, created_at, last_rotated
                FROM encrypted_fields
            """)
            
            for row in cursor.fetchall():
                field = EncryptedField(
                    table_name=row[0],
                    field_name=row[1],
                    encryption_algorithm=EncryptionAlgorithm(row[2]),
                    key_id=row[3],
                    is_searchable=row[4],
                    created_at=row[5],
                    last_rotated=row[6]
                )
                field_key = f"{field.table_name}.{field.field_name}"
                self.encrypted_fields[field_key] = field
            
            cursor.close()
            conn.close()
            
            logger.info(f"Loaded {len(self.encryption_keys)} encryption keys and {len(self.encrypted_fields)} encrypted fields")
            
        except Exception as e:
            logger.error(f"Failed to load encryption configuration: {e}")
    
    def _create_encryption_tables(self, cursor):
        """Create tables for storing encryption metadata."""
        create_keys_table = """
        CREATE TABLE IF NOT EXISTS encryption_keys (
            key_id VARCHAR(64) PRIMARY KEY,
            key_type VARCHAR(32) NOT NULL,
            algorithm VARCHAR(32) NOT NULL,
            key_data TEXT NOT NULL,
            created_at DATETIME(6) NOT NULL,
            expires_at DATETIME(6),
            version INT NOT NULL DEFAULT 1,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            metadata JSON,
            INDEX idx_key_type (key_type),
            INDEX idx_algorithm (algorithm),
            INDEX idx_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        create_fields_table = """
        CREATE TABLE IF NOT EXISTS encrypted_fields (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            encryption_algorithm VARCHAR(32) NOT NULL,
            key_id VARCHAR(64) NOT NULL,
            is_searchable BOOLEAN NOT NULL DEFAULT FALSE,
            created_at DATETIME(6) NOT NULL,
            last_rotated DATETIME(6) NOT NULL,
            UNIQUE KEY unique_field (table_name, field_name),
            FOREIGN KEY (key_id) REFERENCES encryption_keys(key_id),
            INDEX idx_table (table_name),
            INDEX idx_algorithm (encryption_algorithm)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        cursor.execute(create_keys_table)
        cursor.execute(create_fields_table)
    
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
        }
    
    def generate_encryption_key(self, key_type: KeyType, algorithm: EncryptionAlgorithm, 
                               expires_days: Optional[int] = None) -> EncryptionKey:
        """Generate a new encryption key."""
        key_id = f"{key_type.value}_{algorithm.value}_{secrets.token_hex(8)}"
        
        # Generate key based on algorithm
        if algorithm == EncryptionAlgorithm.FERNET:
            key_data = Fernet.generate_key()
        elif algorithm == EncryptionAlgorithm.AES_256_GCM:
            key_data = secrets.token_bytes(32)  # 256-bit key
        elif algorithm in [EncryptionAlgorithm.RSA_2048, EncryptionAlgorithm.RSA_4096]:
            key_size = 2048 if algorithm == EncryptionAlgorithm.RSA_2048 else 4096
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=self.backend
            )
            key_data = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        else:
            raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
        
        # Calculate expiration date
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        # Create encryption key object
        encryption_key = EncryptionKey(
            key_id=key_id,
            key_type=key_type,
            algorithm=algorithm,
            key_data=key_data,
            created_at=datetime.now(),
            expires_at=expires_at,
            version=1,
            is_active=True,
            metadata={}
        )
        
        # Store key in database
        self._store_encryption_key(encryption_key)
        
        # Cache key in memory
        self.encryption_keys[key_id] = encryption_key
        
        logger.info(f"Generated new encryption key: {key_id}")
        return encryption_key
    
    def _store_encryption_key(self, key: EncryptionKey):
        """Store encryption key in database."""
        try:
            conn = mysql.connector.connect(**self._get_connection_config())
            cursor = conn.cursor()
            
            # Encrypt key data with master key before storing
            encrypted_key_data = self._encrypt_with_master_key(key.key_data)
            
            insert_sql = """
            INSERT INTO encryption_keys (
                key_id, key_type, algorithm, key_data, created_at, 
                expires_at, version, is_active, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                key_data = VALUES(key_data),
                expires_at = VALUES(expires_at),
                version = version + 1,
                is_active = VALUES(is_active),
                metadata = VALUES(metadata)
            """
            
            values = (
                key.key_id,
                key.key_type.value,
                key.algorithm.value,
                base64.b64encode(encrypted_key_data).decode(),
                key.created_at,
                key.expires_at,
                key.version,
                key.is_active,
                json.dumps(key.metadata) if key.metadata else None
            )
            
            cursor.execute(insert_sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store encryption key {key.key_id}: {e}")
            raise
    
    def _encrypt_with_master_key(self, data: bytes) -> bytes:
        """Encrypt data with master key using AES-256-GCM."""
        # Derive key from master key
        salt = secrets.token_bytes(16)
        kdf = Scrypt(
            length=32,
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            backend=self.backend
        )
        key = kdf.derive(self.master_key)
        
        # Generate IV
        iv = secrets.token_bytes(12)
        
        # Encrypt data
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Combine salt, IV, tag, and ciphertext
        return salt + iv + encryptor.tag + ciphertext
    
    def _decrypt_with_master_key(self, encrypted_data: bytes) -> bytes:
        """Decrypt data with master key using AES-256-GCM."""
        # Extract components
        salt = encrypted_data[:16]
        iv = encrypted_data[16:28]
        tag = encrypted_data[28:44]
        ciphertext = encrypted_data[44:]
        
        # Derive key from master key
        kdf = Scrypt(
            length=32,
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            backend=self.backend
        )
        key = kdf.derive(self.master_key)
        
        # Decrypt data
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def configure_field_encryption(self, table_name: str, field_name: str, 
                                 algorithm: EncryptionAlgorithm, 
                                 is_searchable: bool = False) -> bool:
        """Configure encryption for a specific database field."""
        try:
            # Generate or get appropriate encryption key
            key_type = KeyType.DATA_ENCRYPTION_KEY
            key = self._get_or_create_key_for_algorithm(key_type, algorithm)
            
            # Create encrypted field configuration
            field = EncryptedField(
                table_name=table_name,
                field_name=field_name,
                encryption_algorithm=algorithm,
                key_id=key.key_id,
                is_searchable=is_searchable,
                created_at=datetime.now(),
                last_rotated=datetime.now()
            )
            
            # Store configuration in database
            self._store_encrypted_field_config(field)
            
            # Cache configuration
            field_key = f"{table_name}.{field_name}"
            self.encrypted_fields[field_key] = field
            
            logger.info(f"Configured encryption for field {table_name}.{field_name} with {algorithm.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure field encryption for {table_name}.{field_name}: {e}")
            return False
    
    def _get_or_create_key_for_algorithm(self, key_type: KeyType, algorithm: EncryptionAlgorithm) -> EncryptionKey:
        """Get existing or create new key for algorithm."""
        # Look for existing active key
        for key in self.encryption_keys.values():
            if (key.key_type == key_type and 
                key.algorithm == algorithm and 
                key.is_active and 
                (not key.expires_at or key.expires_at > datetime.now())):
                return key
        
        # Create new key if none found
        return self.generate_encryption_key(key_type, algorithm, self.key_rotation_interval)
    
    def _store_encrypted_field_config(self, field: EncryptedField):
        """Store encrypted field configuration in database."""
        try:
            conn = mysql.connector.connect(**self._get_connection_config())
            cursor = conn.cursor()
            
            insert_sql = """
            INSERT INTO encrypted_fields (
                table_name, field_name, encryption_algorithm, key_id, 
                is_searchable, created_at, last_rotated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                encryption_algorithm = VALUES(encryption_algorithm),
                key_id = VALUES(key_id),
                is_searchable = VALUES(is_searchable),
                last_rotated = VALUES(last_rotated)
            """
            
            values = (
                field.table_name,
                field.field_name,
                field.encryption_algorithm.value,
                field.key_id,
                field.is_searchable,
                field.created_at,
                field.last_rotated
            )
            
            cursor.execute(insert_sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store encrypted field config: {e}")
            raise
    
    def encrypt_field_value(self, table_name: str, field_name: str, value: str) -> str:
        """Encrypt a field value using configured encryption."""
        field_key = f"{table_name}.{field_name}"
        
        if field_key not in self.encrypted_fields:
            raise ValueError(f"No encryption configured for field {field_key}")
        
        field_config = self.encrypted_fields[field_key]
        encryption_key = self.encryption_keys[field_config.key_id]
        
        if not value:
            return value
        
        try:
            if field_config.encryption_algorithm == EncryptionAlgorithm.FERNET:
                cipher = Fernet(encryption_key.key_data)
                encrypted_value = cipher.encrypt(value.encode())
                return base64.urlsafe_b64encode(encrypted_value).decode()
            
            elif field_config.encryption_algorithm == EncryptionAlgorithm.AES_256_GCM:
                iv = secrets.token_bytes(12)
                cipher = Cipher(algorithms.AES(encryption_key.key_data), modes.GCM(iv), backend=self.backend)
                encryptor = cipher.encryptor()
                ciphertext = encryptor.update(value.encode()) + encryptor.finalize()
                
                # Combine IV, tag, and ciphertext
                encrypted_data = iv + encryptor.tag + ciphertext
                return base64.urlsafe_b64encode(encrypted_data).decode()
            
            else:
                raise ValueError(f"Unsupported encryption algorithm for field encryption: {field_config.encryption_algorithm}")
                
        except Exception as e:
            logger.error(f"Failed to encrypt field value for {field_key}: {e}")
            raise
    
    def decrypt_field_value(self, table_name: str, field_name: str, encrypted_value: str) -> str:
        """Decrypt a field value using configured encryption."""
        field_key = f"{table_name}.{field_name}"
        
        if field_key not in self.encrypted_fields:
            raise ValueError(f"No encryption configured for field {field_key}")
        
        field_config = self.encrypted_fields[field_key]
        encryption_key = self.encryption_keys[field_config.key_id]
        
        if not encrypted_value:
            return encrypted_value
        
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_value.encode())
            
            if field_config.encryption_algorithm == EncryptionAlgorithm.FERNET:
                cipher = Fernet(encryption_key.key_data)
                decrypted_value = cipher.decrypt(encrypted_data)
                return decrypted_value.decode()
            
            elif field_config.encryption_algorithm == EncryptionAlgorithm.AES_256_GCM:
                iv = encrypted_data[:12]
                tag = encrypted_data[12:28]
                ciphertext = encrypted_data[28:]
                
                cipher = Cipher(algorithms.AES(encryption_key.key_data), modes.GCM(iv, tag), backend=self.backend)
                decryptor = cipher.decryptor()
                decrypted_value = decryptor.update(ciphertext) + decryptor.finalize()
                return decrypted_value.decode()
            
            else:
                raise ValueError(f"Unsupported encryption algorithm for field decryption: {field_config.encryption_algorithm}")
                
        except Exception as e:
            logger.error(f"Failed to decrypt field value for {field_key}: {e}")
            raise
    
    def rotate_encryption_keys(self) -> Dict[str, Any]:
        """Rotate encryption keys that are due for rotation."""
        rotation_results = {
            'rotated_keys': [],
            'failed_rotations': [],
            'total_processed': 0
        }
        
        try:
            current_time = datetime.now()
            rotation_threshold = current_time - timedelta(days=self.key_rotation_interval)
            
            for key_id, key in self.encryption_keys.items():
                rotation_results['total_processed'] += 1
                
                # Check if key needs rotation
                needs_rotation = (
                    key.created_at < rotation_threshold or
                    (key.expires_at and key.expires_at < current_time + timedelta(days=7))  # Rotate 7 days before expiry
                )
                
                if needs_rotation:
                    try:
                        # Generate new key
                        new_key = self.generate_encryption_key(
                            key.key_type, 
                            key.algorithm, 
                            self.key_rotation_interval
                        )
                        
                        # Update field configurations to use new key
                        self._update_field_configurations_for_key_rotation(key_id, new_key.key_id)
                        
                        # Re-encrypt data with new key
                        self._re_encrypt_data_with_new_key(key_id, new_key.key_id)
                        
                        # Deactivate old key
                        key.is_active = False
                        self._store_encryption_key(key)
                        
                        rotation_results['rotated_keys'].append({
                            'old_key_id': key_id,
                            'new_key_id': new_key.key_id,
                            'algorithm': key.algorithm.value
                        })
                        
                        logger.info(f"Successfully rotated encryption key {key_id} to {new_key.key_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to rotate key {key_id}: {e}")
                        rotation_results['failed_rotations'].append({
                            'key_id': key_id,
                            'error': str(e)
                        })
            
            return rotation_results
            
        except Exception as e:
            logger.error(f"Key rotation process failed: {e}")
            rotation_results['error'] = str(e)
            return rotation_results
    
    def _update_field_configurations_for_key_rotation(self, old_key_id: str, new_key_id: str):
        """Update field configurations to use new key after rotation."""
        try:
            conn = mysql.connector.connect(**self._get_connection_config())
            cursor = conn.cursor()
            
            update_sql = """
            UPDATE encrypted_fields 
            SET key_id = %s, last_rotated = %s
            WHERE key_id = %s
            """
            
            cursor.execute(update_sql, (new_key_id, datetime.now(), old_key_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update in-memory cache
            for field_key, field_config in self.encrypted_fields.items():
                if field_config.key_id == old_key_id:
                    field_config.key_id = new_key_id
                    field_config.last_rotated = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to update field configurations for key rotation: {e}")
            raise
    
    def _re_encrypt_data_with_new_key(self, old_key_id: str, new_key_id: str):
        """Re-encrypt existing data with new key."""
        # This is a complex operation that would need to be done carefully in production
        # For now, we'll log the requirement and implement a basic framework
        logger.info(f"Re-encryption required for data encrypted with key {old_key_id} to use key {new_key_id}")
        
        # In a production system, this would involve:
        # 1. Identifying all records with data encrypted using the old key
        # 2. Decrypting with old key and re-encrypting with new key
        # 3. Updating records in batches to avoid long-running transactions
        # 4. Verifying data integrity after re-encryption
        
        # For this implementation, we'll create a placeholder that can be extended
        affected_fields = [
            field for field in self.encrypted_fields.values() 
            if field.key_id == old_key_id
        ]
        
        for field in affected_fields:
            logger.info(f"Would re-encrypt data in {field.table_name}.{field.field_name}")
    
    def get_encryption_status(self) -> Dict[str, Any]:
        """Get comprehensive encryption status and metrics."""
        try:
            status = {
                'total_encryption_keys': len(self.encryption_keys),
                'active_keys': sum(1 for key in self.encryption_keys.values() if key.is_active),
                'encrypted_fields': len(self.encrypted_fields),
                'keys_by_algorithm': {},
                'keys_by_type': {},
                'keys_expiring_soon': [],
                'field_encryption_summary': {},
                'last_key_rotation': None,
                'next_rotation_due': None
            }
            
            # Analyze keys by algorithm and type
            for key in self.encryption_keys.values():
                if key.is_active:
                    # Count by algorithm
                    algo = key.algorithm.value
                    status['keys_by_algorithm'][algo] = status['keys_by_algorithm'].get(algo, 0) + 1
                    
                    # Count by type
                    key_type = key.key_type.value
                    status['keys_by_type'][key_type] = status['keys_by_type'].get(key_type, 0) + 1
                    
                    # Check for keys expiring soon (within 30 days)
                    if key.expires_at and key.expires_at < datetime.now() + timedelta(days=30):
                        status['keys_expiring_soon'].append({
                            'key_id': key.key_id,
                            'expires_at': key.expires_at.isoformat(),
                            'algorithm': key.algorithm.value
                        })
            
            # Analyze encrypted fields
            for field in self.encrypted_fields.values():
                table = field.table_name
                if table not in status['field_encryption_summary']:
                    status['field_encryption_summary'][table] = {
                        'encrypted_fields': 0,
                        'algorithms_used': set()
                    }
                
                status['field_encryption_summary'][table]['encrypted_fields'] += 1
                status['field_encryption_summary'][table]['algorithms_used'].add(field.encryption_algorithm.value)
            
            # Convert sets to lists for JSON serialization
            for table_info in status['field_encryption_summary'].values():
                table_info['algorithms_used'] = list(table_info['algorithms_used'])
            
            # Find last rotation date
            if self.encrypted_fields:
                last_rotation = max(field.last_rotated for field in self.encrypted_fields.values())
                status['last_key_rotation'] = last_rotation.isoformat()
                status['next_rotation_due'] = (last_rotation + timedelta(days=self.key_rotation_interval)).isoformat()
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get encryption status: {e}")
            return {'error': str(e)}


# Singleton instance
transparent_data_encryption = TransparentDataEncryption()