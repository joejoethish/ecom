"""
Advanced Threat Detection System for MySQL Database Integration

This module implements comprehensive database threat detection and monitoring:
- Advanced SQL injection detection
- Behavioral anomaly detection
- Real-time threat monitoring
- Automated threat response
- Machine learning-based pattern recognition

Requirements: 4.4, 4.5
"""

import os
import logging
import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
import mysql.connector
from mysql.connector import Error as MySQLError
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from core.database_security import database_security_manager, AuditEventType


logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatCategory(Enum):
    """Categories of security threats."""
    SQL_INJECTION = "sql_injection"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    BRUTE_FORCE = "brute_force"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_QUERY = "suspicious_query"
    MASS_DATA_ACCESS = "mass_data_access"


@dataclass
class ThreatSignature:
    """Threat detection signature."""
    signature_id: str
    category: ThreatCategory
    pattern: str
    description: str
    severity: ThreatLevel
    is_regex: bool
    is_active: bool
    false_positive_rate: float
    created_at: datetime
    last_updated: datetime


@dataclass
class ThreatDetection:
    """Detected threat information."""
    detection_id: str
    timestamp: datetime
    threat_category: ThreatCategory
    severity: ThreatLevel
    user: str
    source_ip: str
    query_hash: str
    description: str
    confidence_score: float
    raw_query: str
    matched_signatures: List[str]
    context_data: Dict[str, Any]
    is_blocked: bool
    response_action: str


@dataclass
class UserBehaviorProfile:
    """User behavior profile for anomaly detection."""
    user: str
    typical_query_patterns: Set[str]
    typical_access_times: List[int]  # Hours of day
    typical_source_ips: Set[str]
    typical_tables_accessed: Set[str]
    average_queries_per_hour: float
    average_query_complexity: float
    last_updated: datetime


class AdvancedThreatDetector:
    """Advanced threat detection system with machine learning capabilities."""
    
    def __init__(self):
        """Initialize the threat detection system."""
        self.connection_config = self._get_connection_config()
        self.threat_signatures = {}
        self.user_profiles = {}
        self.detection_history = deque(maxlen=10000)  # Keep last 10k detections
        self.blocked_ips = set()
        self.blocked_users = set()
        
        # Configuration
        self.enable_behavioral_analysis = getattr(settings, 'THREAT_BEHAVIORAL_ANALYSIS', True)
        self.enable_ml_detection = getattr(settings, 'THREAT_ML_DETECTION', True)
        self.auto_block_threshold = getattr(settings, 'THREAT_AUTO_BLOCK_THRESHOLD', 0.8)
        self.profile_learning_period = getattr(settings, 'THREAT_PROFILE_LEARNING_DAYS', 30)
        
        # Initialize system
        self._initialize_threat_detection()
    
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
    
    def _initialize_threat_detection(self):
        """Initialize threat detection system."""
        try:
            # Create threat detection tables
            self._create_threat_tables()
            
            # Load threat signatures
            self._load_threat_signatures()
            
            # Load user behavior profiles
            self._load_user_profiles()
            
            # Initialize default signatures
            self._initialize_default_signatures()
            
            logger.info("Advanced threat detection system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize threat detection system: {e}")
    
    def _create_threat_tables(self):
        """Create tables for threat detection data."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            # Threat signatures table
            create_signatures_table = """
            CREATE TABLE IF NOT EXISTS threat_signatures (
                signature_id VARCHAR(64) PRIMARY KEY,
                category VARCHAR(32) NOT NULL,
                pattern TEXT NOT NULL,
                description TEXT NOT NULL,
                severity VARCHAR(16) NOT NULL,
                is_regex BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                false_positive_rate DECIMAL(5,4) DEFAULT 0.0000,
                created_at DATETIME(6) NOT NULL,
                last_updated DATETIME(6) NOT NULL,
                INDEX idx_category (category),
                INDEX idx_severity (severity),
                INDEX idx_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            # Threat detections table
            create_detections_table = """
            CREATE TABLE IF NOT EXISTS threat_detections (
                detection_id VARCHAR(64) PRIMARY KEY,
                timestamp DATETIME(6) NOT NULL,
                threat_category VARCHAR(32) NOT NULL,
                severity VARCHAR(16) NOT NULL,
                user VARCHAR(100) NOT NULL,
                source_ip VARCHAR(45),
                query_hash VARCHAR(64),
                description TEXT NOT NULL,
                confidence_score DECIMAL(5,4) NOT NULL,
                raw_query TEXT,
                matched_signatures JSON,
                context_data JSON,
                is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
                response_action VARCHAR(100),
                INDEX idx_timestamp (timestamp),
                INDEX idx_category (threat_category),
                INDEX idx_severity (severity),
                INDEX idx_user (user),
                INDEX idx_source_ip (source_ip),
                INDEX idx_blocked (is_blocked)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            # User behavior profiles table
            create_profiles_table = """
            CREATE TABLE IF NOT EXISTS user_behavior_profiles (
                user VARCHAR(100) PRIMARY KEY,
                typical_query_patterns JSON,
                typical_access_times JSON,
                typical_source_ips JSON,
                typical_tables_accessed JSON,
                average_queries_per_hour DECIMAL(8,2) DEFAULT 0.00,
                average_query_complexity DECIMAL(8,2) DEFAULT 0.00,
                last_updated DATETIME(6) NOT NULL,
                INDEX idx_last_updated (last_updated)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_signatures_table)
            cursor.execute(create_detections_table)
            cursor.execute(create_profiles_table)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Threat detection tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create threat detection tables: {e}")
            raise
    
    def _load_threat_signatures(self):
        """Load threat signatures from database."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT signature_id, category, pattern, description, severity, 
                       is_regex, is_active, false_positive_rate, created_at, last_updated
                FROM threat_signatures
                WHERE is_active = TRUE
            """)
            
            for row in cursor.fetchall():
                signature = ThreatSignature(
                    signature_id=row[0],
                    category=ThreatCategory(row[1]),
                    pattern=row[2],
                    description=row[3],
                    severity=ThreatLevel(row[4]),
                    is_regex=row[5],
                    is_active=row[6],
                    false_positive_rate=float(row[7]),
                    created_at=row[8],
                    last_updated=row[9]
                )
                self.threat_signatures[signature.signature_id] = signature
            
            cursor.close()
            conn.close()
            
            logger.info(f"Loaded {len(self.threat_signatures)} threat signatures")
            
        except Exception as e:
            logger.error(f"Failed to load threat signatures: {e}")
    
    def _load_user_profiles(self):
        """Load user behavior profiles from database."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user, typical_query_patterns, typical_access_times, 
                       typical_source_ips, typical_tables_accessed, 
                       average_queries_per_hour, average_query_complexity, last_updated
                FROM user_behavior_profiles
                WHERE last_updated >= %s
            """, [datetime.now() - timedelta(days=self.profile_learning_period)])
            
            for row in cursor.fetchall():
                profile = UserBehaviorProfile(
                    user=row[0],
                    typical_query_patterns=set(json.loads(row[1]) if row[1] else []),
                    typical_access_times=json.loads(row[2]) if row[2] else [],
                    typical_source_ips=set(json.loads(row[3]) if row[3] else []),
                    typical_tables_accessed=set(json.loads(row[4]) if row[4] else []),
                    average_queries_per_hour=float(row[5]),
                    average_query_complexity=float(row[6]),
                    last_updated=row[7]
                )
                self.user_profiles[profile.user] = profile
            
            cursor.close()
            conn.close()
            
            logger.info(f"Loaded {len(self.user_profiles)} user behavior profiles")
            
        except Exception as e:
            logger.error(f"Failed to load user behavior profiles: {e}")
    
    def _initialize_default_signatures(self):
        """Initialize default threat detection signatures."""
        default_signatures = [
            # SQL Injection signatures
            {
                'signature_id': 'sqli_union_select',
                'category': ThreatCategory.SQL_INJECTION,
                'pattern': r'\b(union\s+select|union\s+all\s+select)\b',
                'description': 'UNION-based SQL injection attempt',
                'severity': ThreatLevel.HIGH,
                'is_regex': True
            },
            {
                'signature_id': 'sqli_comment_injection',
                'category': ThreatCategory.SQL_INJECTION,
                'pattern': r'(--|#|/\*|\*/)',
                'description': 'SQL comment injection attempt',
                'severity': ThreatLevel.MEDIUM,
                'is_regex': True
            },
            {
                'signature_id': 'sqli_boolean_blind',
                'category': ThreatCategory.SQL_INJECTION,
                'pattern': r'\b(or|and)\s+\d+\s*=\s*\d+',
                'description': 'Boolean-based blind SQL injection',
                'severity': ThreatLevel.HIGH,
                'is_regex': True
            },
            {
                'signature_id': 'sqli_string_injection',
                'category': ThreatCategory.SQL_INJECTION,
                'pattern': r"(\b(or|and)\s+['\"].*['\"]|['\"].*['\"].*=.*['\"])",
                'description': 'String-based SQL injection attempt',
                'severity': ThreatLevel.HIGH,
                'is_regex': True
            },
            
            # Privilege escalation signatures
            {
                'signature_id': 'priv_grant_revoke',
                'category': ThreatCategory.PRIVILEGE_ESCALATION,
                'pattern': r'\b(grant|revoke)\s+',
                'description': 'Privilege modification attempt',
                'severity': ThreatLevel.CRITICAL,
                'is_regex': True
            },
            {
                'signature_id': 'priv_user_management',
                'category': ThreatCategory.PRIVILEGE_ESCALATION,
                'pattern': r'\b(create\s+user|drop\s+user|alter\s+user)\b',
                'description': 'User management operation',
                'severity': ThreatLevel.CRITICAL,
                'is_regex': True
            },
            
            # Data exfiltration signatures
            {
                'signature_id': 'data_information_schema',
                'category': ThreatCategory.DATA_EXFILTRATION,
                'pattern': r'\binformation_schema\b',
                'description': 'Information schema access attempt',
                'severity': ThreatLevel.MEDIUM,
                'is_regex': True
            },
            {
                'signature_id': 'data_show_commands',
                'category': ThreatCategory.DATA_EXFILTRATION,
                'pattern': r'\bshow\s+(databases|tables|columns|grants)\b',
                'description': 'Database structure enumeration',
                'severity': ThreatLevel.MEDIUM,
                'is_regex': True
            },
            {
                'signature_id': 'data_file_operations',
                'category': ThreatCategory.DATA_EXFILTRATION,
                'pattern': r'\b(load_file|into\s+outfile|into\s+dumpfile)\b',
                'description': 'File system access attempt',
                'severity': ThreatLevel.HIGH,
                'is_regex': True
            },
            
            # Suspicious query patterns
            {
                'signature_id': 'suspicious_mysql_user',
                'category': ThreatCategory.SUSPICIOUS_QUERY,
                'pattern': r'\bmysql\.user\b',
                'description': 'MySQL user table access',
                'severity': ThreatLevel.HIGH,
                'is_regex': True
            },
            {
                'signature_id': 'suspicious_sleep',
                'category': ThreatCategory.SUSPICIOUS_QUERY,
                'pattern': r'\bsleep\s*\(',
                'description': 'Time-based attack pattern',
                'severity': ThreatLevel.MEDIUM,
                'is_regex': True
            }
        ]
        
        for sig_data in default_signatures:
            signature_id = sig_data['signature_id']
            if signature_id not in self.threat_signatures:
                signature = ThreatSignature(
                    signature_id=signature_id,
                    category=sig_data['category'],
                    pattern=sig_data['pattern'],
                    description=sig_data['description'],
                    severity=sig_data['severity'],
                    is_regex=sig_data['is_regex'],
                    is_active=True,
                    false_positive_rate=0.0,
                    created_at=datetime.now(),
                    last_updated=datetime.now()
                )
                
                self._store_threat_signature(signature)
                self.threat_signatures[signature_id] = signature
        
        logger.info(f"Initialized {len(default_signatures)} default threat signatures")
    
    def _store_threat_signature(self, signature: ThreatSignature):
        """Store threat signature in database."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            insert_sql = """
            INSERT INTO threat_signatures (
                signature_id, category, pattern, description, severity, 
                is_regex, is_active, false_positive_rate, created_at, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                pattern = VALUES(pattern),
                description = VALUES(description),
                severity = VALUES(severity),
                is_regex = VALUES(is_regex),
                is_active = VALUES(is_active),
                false_positive_rate = VALUES(false_positive_rate),
                last_updated = VALUES(last_updated)
            """
            
            values = (
                signature.signature_id,
                signature.category.value,
                signature.pattern,
                signature.description,
                signature.severity.value,
                signature.is_regex,
                signature.is_active,
                signature.false_positive_rate,
                signature.created_at,
                signature.last_updated
            )
            
            cursor.execute(insert_sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store threat signature {signature.signature_id}: {e}")
            raise
    
    def detect_threats(self, query: str, user: str, source_ip: str, 
                      context: Dict[str, Any] = None) -> Tuple[bool, List[ThreatDetection]]:
        """Comprehensive threat detection analysis."""
        detections = []
        
        try:
            # Signature-based detection
            signature_detections = self._signature_based_detection(query, user, source_ip, context)
            detections.extend(signature_detections)
            
            # Behavioral anomaly detection
            if self.enable_behavioral_analysis:
                behavioral_detections = self._behavioral_anomaly_detection(query, user, source_ip, context)
                detections.extend(behavioral_detections)
            
            # Statistical anomaly detection
            statistical_detections = self._statistical_anomaly_detection(query, user, source_ip, context)
            detections.extend(statistical_detections)
            
            # Store detections
            for detection in detections:
                self._store_threat_detection(detection)
                self.detection_history.append(detection)
            
            # Determine if any threats should trigger automatic blocking
            high_confidence_threats = [d for d in detections if d.confidence_score >= self.auto_block_threshold]
            
            if high_confidence_threats:
                self._handle_threat_response(high_confidence_threats, user, source_ip)
            
            return len(detections) > 0, detections
            
        except Exception as e:
            logger.error(f"Threat detection failed for user {user}: {e}")
            return False, []
    
    def _signature_based_detection(self, query: str, user: str, source_ip: str, 
                                 context: Dict[str, Any] = None) -> List[ThreatDetection]:
        """Detect threats using signature patterns."""
        detections = []
        query_lower = query.lower()
        
        for signature in self.threat_signatures.values():
            if not signature.is_active:
                continue
            
            try:
                match_found = False
                
                if signature.is_regex:
                    match = re.search(signature.pattern, query_lower, re.IGNORECASE | re.MULTILINE)
                    match_found = match is not None
                else:
                    match_found = signature.pattern.lower() in query_lower
                
                if match_found:
                    # Calculate confidence score based on signature reliability
                    confidence_score = max(0.1, 1.0 - signature.false_positive_rate)
                    
                    detection = ThreatDetection(
                        detection_id=f"sig_{signature.signature_id}_{hashlib.md5(f'{user}_{source_ip}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}",
                        timestamp=datetime.now(),
                        threat_category=signature.category,
                        severity=signature.severity,
                        user=user,
                        source_ip=source_ip,
                        query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
                        description=f"Signature match: {signature.description}",
                        confidence_score=confidence_score,
                        raw_query=query[:1000],  # Limit query length for storage
                        matched_signatures=[signature.signature_id],
                        context_data=context or {},
                        is_blocked=False,
                        response_action="logged"
                    )
                    
                    detections.append(detection)
                    
            except Exception as e:
                logger.error(f"Error processing signature {signature.signature_id}: {e}")
        
        return detections
    
    def _behavioral_anomaly_detection(self, query: str, user: str, source_ip: str, 
                                    context: Dict[str, Any] = None) -> List[ThreatDetection]:
        """Detect anomalies based on user behavior patterns."""
        detections = []
        
        if user not in self.user_profiles:
            # No profile exists, create one or skip behavioral analysis
            return detections
        
        profile = self.user_profiles[user]
        current_hour = datetime.now().hour
        
        try:
            # Check for unusual access time
            if current_hour not in profile.typical_access_times:
                if len(profile.typical_access_times) > 0:  # Only if we have historical data
                    detection = ThreatDetection(
                        detection_id=f"behav_time_{hashlib.md5(f'{user}_{source_ip}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}",
                        timestamp=datetime.now(),
                        threat_category=ThreatCategory.ANOMALOUS_BEHAVIOR,
                        severity=ThreatLevel.LOW,
                        user=user,
                        source_ip=source_ip,
                        query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
                        description=f"Unusual access time: {current_hour}:00 (typical: {profile.typical_access_times})",
                        confidence_score=0.3,
                        raw_query=query[:1000],
                        matched_signatures=[],
                        context_data=context or {},
                        is_blocked=False,
                        response_action="logged"
                    )
                    detections.append(detection)
            
            # Check for unusual source IP
            if source_ip not in profile.typical_source_ips:
                if len(profile.typical_source_ips) > 0:
                    detection = ThreatDetection(
                        detection_id=f"behav_ip_{hashlib.md5(f'{user}_{source_ip}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}",
                        timestamp=datetime.now(),
                        threat_category=ThreatCategory.ANOMALOUS_BEHAVIOR,
                        severity=ThreatLevel.MEDIUM,
                        user=user,
                        source_ip=source_ip,
                        query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
                        description=f"Unusual source IP: {source_ip}",
                        confidence_score=0.5,
                        raw_query=query[:1000],
                        matched_signatures=[],
                        context_data=context or {},
                        is_blocked=False,
                        response_action="logged"
                    )
                    detections.append(detection)
            
            # Check query pattern similarity
            query_pattern = self._extract_query_pattern(query)
            if query_pattern not in profile.typical_query_patterns:
                if len(profile.typical_query_patterns) > 5:  # Only if we have enough patterns
                    detection = ThreatDetection(
                        detection_id=f"behav_pattern_{hashlib.md5(f'{user}_{source_ip}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}",
                        timestamp=datetime.now(),
                        threat_category=ThreatCategory.ANOMALOUS_BEHAVIOR,
                        severity=ThreatLevel.LOW,
                        user=user,
                        source_ip=source_ip,
                        query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
                        description=f"Unusual query pattern detected",
                        confidence_score=0.4,
                        raw_query=query[:1000],
                        matched_signatures=[],
                        context_data=context or {},
                        is_blocked=False,
                        response_action="logged"
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"Behavioral anomaly detection failed for user {user}: {e}")
        
        return detections
    
    def _statistical_anomaly_detection(self, query: str, user: str, source_ip: str, 
                                     context: Dict[str, Any] = None) -> List[ThreatDetection]:
        """Detect statistical anomalies in query patterns."""
        detections = []
        
        try:
            # Check for mass data access patterns
            if self._is_mass_data_access(query):
                detection = ThreatDetection(
                    detection_id=f"stat_mass_{hashlib.md5(f'{user}_{source_ip}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}",
                    timestamp=datetime.now(),
                    threat_category=ThreatCategory.MASS_DATA_ACCESS,
                    severity=ThreatLevel.MEDIUM,
                    user=user,
                    source_ip=source_ip,
                    query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
                    description="Potential mass data access detected",
                    confidence_score=0.6,
                    raw_query=query[:1000],
                    matched_signatures=[],
                    context_data=context or {},
                    is_blocked=False,
                    response_action="logged"
                )
                detections.append(detection)
            
            # Check for unusual query complexity
            complexity_score = self._calculate_query_complexity(query)
            if user in self.user_profiles:
                profile = self.user_profiles[user]
                if complexity_score > profile.average_query_complexity * 3:  # 3x normal complexity
                    detection = ThreatDetection(
                        detection_id=f"stat_complex_{hashlib.md5(f'{user}_{source_ip}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}",
                        timestamp=datetime.now(),
                        threat_category=ThreatCategory.SUSPICIOUS_QUERY,
                        severity=ThreatLevel.LOW,
                        user=user,
                        source_ip=source_ip,
                        query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
                        description=f"Unusually complex query (score: {complexity_score:.2f}, avg: {profile.average_query_complexity:.2f})",
                        confidence_score=0.3,
                        raw_query=query[:1000],
                        matched_signatures=[],
                        context_data=context or {},
                        is_blocked=False,
                        response_action="logged"
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"Statistical anomaly detection failed for user {user}: {e}")
        
        return detections
    
    def _extract_query_pattern(self, query: str) -> str:
        """Extract a normalized pattern from a SQL query."""
        # Normalize query by removing literals and parameters
        pattern = re.sub(r"'[^']*'", "'?'", query.lower())
        pattern = re.sub(r'"[^"]*"', '"?"', pattern)
        pattern = re.sub(r'\b\d+\b', '?', pattern)
        pattern = re.sub(r'\s+', ' ', pattern).strip()
        return pattern
    
    def _is_mass_data_access(self, query: str) -> bool:
        """Check if query indicates potential mass data access."""
        query_lower = query.lower()
        
        # Look for patterns that might indicate mass data extraction
        mass_access_patterns = [
            r'select\s+\*\s+from\s+\w+\s*(?:;|$)',  # SELECT * without WHERE
            r'select\s+.+\s+from\s+\w+\s+limit\s+\d{4,}',  # Large LIMIT values
            r'union\s+select\s+.+\s+union\s+select',  # Multiple UNION statements
        ]
        
        for pattern in mass_access_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def _calculate_query_complexity(self, query: str) -> float:
        """Calculate a complexity score for a SQL query."""
        complexity = 0.0
        query_lower = query.lower()
        
        # Base complexity factors
        complexity += len(query) * 0.001  # Length factor
        complexity += query_lower.count('select') * 2
        complexity += query_lower.count('join') * 3
        complexity += query_lower.count('union') * 4
        complexity += query_lower.count('subquery') * 5
        complexity += query_lower.count('case') * 2
        complexity += query_lower.count('group by') * 2
        complexity += query_lower.count('order by') * 1
        complexity += query_lower.count('having') * 3
        
        return complexity
    
    def _store_threat_detection(self, detection: ThreatDetection):
        """Store threat detection in database."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            insert_sql = """
            INSERT INTO threat_detections (
                detection_id, timestamp, threat_category, severity, user, source_ip,
                query_hash, description, confidence_score, raw_query, matched_signatures,
                context_data, is_blocked, response_action
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                detection.detection_id,
                detection.timestamp,
                detection.threat_category.value,
                detection.severity.value,
                detection.user,
                detection.source_ip,
                detection.query_hash,
                detection.description,
                detection.confidence_score,
                detection.raw_query,
                json.dumps(detection.matched_signatures),
                json.dumps(detection.context_data),
                detection.is_blocked,
                detection.response_action
            )
            
            cursor.execute(insert_sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store threat detection {detection.detection_id}: {e}")
    
    def _handle_threat_response(self, threats: List[ThreatDetection], user: str, source_ip: str):
        """Handle automated threat response actions."""
        try:
            # Determine response action based on threat severity and confidence
            critical_threats = [t for t in threats if t.severity == ThreatLevel.CRITICAL]
            high_threats = [t for t in threats if t.severity == ThreatLevel.HIGH]
            
            if critical_threats:
                # Block user and IP for critical threats
                self._block_user_temporarily(user, 3600)  # 1 hour
                self._block_ip_temporarily(source_ip, 1800)  # 30 minutes
                
                # Send immediate alert
                self._send_critical_threat_alert(critical_threats, user, source_ip)
                
                logger.critical(f"Critical threats detected - blocked user {user} and IP {source_ip}")
                
            elif len(high_threats) >= 3:
                # Block IP for multiple high-severity threats
                self._block_ip_temporarily(source_ip, 900)  # 15 minutes
                
                logger.warning(f"Multiple high-severity threats detected - blocked IP {source_ip}")
            
            # Update threat detection statistics
            self._update_threat_statistics(threats)
            
        except Exception as e:
            logger.error(f"Threat response handling failed: {e}")
    
    def _block_user_temporarily(self, user: str, duration_seconds: int):
        """Temporarily block a user."""
        cache_key = f"threat_blocked_user_{user}"
        cache.set(cache_key, True, duration_seconds)
        self.blocked_users.add(user)
        
        # Log the blocking action
        database_security_manager.log_audit_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user='system',
            source_ip='localhost',
            database='ecommerce_db',
            table='threat_response',
            operation='BLOCK_USER',
            affected_rows=1,
            query_hash=f"block_user_{user}",
            success=True,
            additional_data={'blocked_user': user, 'duration': duration_seconds}
        )
    
    def _block_ip_temporarily(self, source_ip: str, duration_seconds: int):
        """Temporarily block an IP address."""
        cache_key = f"threat_blocked_ip_{source_ip}"
        cache.set(cache_key, True, duration_seconds)
        self.blocked_ips.add(source_ip)
        
        # Log the blocking action
        database_security_manager.log_audit_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user='system',
            source_ip='localhost',
            database='ecommerce_db',
            table='threat_response',
            operation='BLOCK_IP',
            affected_rows=1,
            query_hash=f"block_ip_{source_ip}",
            success=True,
            additional_data={'blocked_ip': source_ip, 'duration': duration_seconds}
        )
    
    def _send_critical_threat_alert(self, threats: List[ThreatDetection], user: str, source_ip: str):
        """Send alert for critical threats."""
        try:
            threat_descriptions = [t.description for t in threats]
            
            database_security_manager._send_security_alert(
                event_type="CRITICAL_THREAT_DETECTED",
                severity="CRITICAL",
                user=user,
                source_ip=source_ip,
                description=f"Critical threats detected: {'; '.join(threat_descriptions)}"
            )
            
        except Exception as e:
            logger.error(f"Failed to send critical threat alert: {e}")
    
    def _update_threat_statistics(self, threats: List[ThreatDetection]):
        """Update threat detection statistics."""
        try:
            stats_key = "threat_detection_stats"
            stats = cache.get(stats_key, {
                'total_detections': 0,
                'by_category': defaultdict(int),
                'by_severity': defaultdict(int),
                'last_updated': datetime.now().isoformat()
            })
            
            for threat in threats:
                stats['total_detections'] += 1
                stats['by_category'][threat.threat_category.value] += 1
                stats['by_severity'][threat.severity.value] += 1
            
            stats['last_updated'] = datetime.now().isoformat()
            cache.set(stats_key, stats, 3600)  # Cache for 1 hour
            
        except Exception as e:
            logger.error(f"Failed to update threat statistics: {e}")
    
    def is_user_blocked(self, user: str) -> bool:
        """Check if a user is currently blocked."""
        cache_key = f"threat_blocked_user_{user}"
        return cache.get(cache_key, False) or user in self.blocked_users
    
    def is_ip_blocked(self, source_ip: str) -> bool:
        """Check if an IP address is currently blocked."""
        cache_key = f"threat_blocked_ip_{source_ip}"
        return cache.get(cache_key, False) or source_ip in self.blocked_ips
    
    def get_threat_statistics(self) -> Dict[str, Any]:
        """Get comprehensive threat detection statistics."""
        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            
            # Get detection counts by category and severity
            cursor.execute("""
                SELECT threat_category, severity, COUNT(*) as count
                FROM threat_detections
                WHERE timestamp >= %s
                GROUP BY threat_category, severity
            """, [datetime.now() - timedelta(days=7)])
            
            detection_stats = cursor.fetchall()
            
            # Get top users with detections
            cursor.execute("""
                SELECT user, COUNT(*) as detection_count
                FROM threat_detections
                WHERE timestamp >= %s
                GROUP BY user
                ORDER BY detection_count DESC
                LIMIT 10
            """, [datetime.now() - timedelta(days=7)])
            
            top_users = cursor.fetchall()
            
            # Get top source IPs with detections
            cursor.execute("""
                SELECT source_ip, COUNT(*) as detection_count
                FROM threat_detections
                WHERE timestamp >= %s AND source_ip IS NOT NULL
                GROUP BY source_ip
                ORDER BY detection_count DESC
                LIMIT 10
            """, [datetime.now() - timedelta(days=7)])
            
            top_ips = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Format statistics
            stats = {
                'detection_summary': {
                    'by_category': defaultdict(int),
                    'by_severity': defaultdict(int)
                },
                'top_users': [{'user': row[0], 'detections': row[1]} for row in top_users],
                'top_source_ips': [{'ip': row[0], 'detections': row[1]} for row in top_ips],
                'active_signatures': len([s for s in self.threat_signatures.values() if s.is_active]),
                'user_profiles': len(self.user_profiles),
                'blocked_users': len(self.blocked_users),
                'blocked_ips': len(self.blocked_ips),
                'generated_at': datetime.now().isoformat()
            }
            
            for category, severity, count in detection_stats:
                stats['detection_summary']['by_category'][category] += count
                stats['detection_summary']['by_severity'][severity] += count
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get threat statistics: {e}")
            return {'error': str(e)}


# Singleton instance
advanced_threat_detector = AdvancedThreatDetector()